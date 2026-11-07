#!/usr/bin/env python3
"""Assemble relocatable native desktop packages, with exact runtime identities.

This does not declare a release qualified. The output manifest explicitly records
which package formats still need native installation/playback acceptance.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import plistlib
import re
import shutil
import stat
import subprocess
import tarfile
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[2]
MAC = platform.system() == 'Darwin'


def run(*args, **kwargs):
    print('+', ' '.join(map(str, args)), flush=True)
    subprocess.run(list(map(str, args)), check=True, **kwargs)


def output(*args):
    return subprocess.check_output(list(map(str, args)), text=True).strip()


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def native(path):
    if not path.is_file():
        return False
    with path.open('rb') as stream:
        return stream.read(4) in (b'\x7fELF', b'\xcf\xfa\xed\xfe', b'\xce\xfa\xed\xfe', b'\xca\xfe\xba\xbe')


def dependencies(path):
    if MAC:
        lines = output('otool', '-L', path).splitlines()[1:]
        return [line.strip().split(' (')[0] for line in lines]
    lines = output('ldd', path).splitlines()
    if any('not found' in line for line in lines):
        raise RuntimeError(f'Unresolved native dependency: {path}\n' + '\n'.join(lines))
    return [match.group(1) for line in lines if (match := re.search(r'=> (/[^ ]+)', line))]


def external(dep):
    if MAC:
        return dep.startswith(('/System/', '/usr/lib/'))
    name = Path(dep).name
    # Never ship the host libc, loader, or graphics driver dispatch. Their ABI
    # and native driver belong to the destination OS, not this application.
    return bool(re.match(r'^(ld-linux|lib(c|m|dl|pthread|rt|resolv|util)\.so|lib(GL|EGL|OpenGL|GLX|GLdispatch|drm|gbm))', name))


def copy_closure(initial, destination):
    destination.mkdir(parents=True, exist_ok=True)
    queue = list(map(Path, initial))
    origins = {}
    while queue:
        origin = queue.pop(0)
        real = origin.resolve(strict=True)
        name = origin.name
        if name in origins:
            if sha(origins[name]) != sha(real):
                raise RuntimeError('Conflicting native library basename: ' + name)
            continue
        origins[name] = real
        shutil.copy2(real, destination / name)
        for dep in dependencies(real):
            if external(dep):
                continue
            if dep.startswith('@rpath/'):
                # Homebrew libraries use absolute dependencies; Qt frameworks
                # are deployed separately by Qt's own macdeployqt.
                raise RuntimeError(f'Unresolved source rpath {dep} in {real}')
            if dep.startswith('@loader_path/'):
                dep = str(real.parent / dep.removeprefix('@loader_path/'))
            queue.append(Path(dep))
    for name, origin in origins.items():
        target = destination / name
        target.chmod(target.stat().st_mode | stat.S_IWUSR)
        if MAC:
            run('install_name_tool', '-id', '@loader_path/' + name, target)
            for dep in dependencies(origin):
                if not external(dep):
                    run('install_name_tool', '-change', dep, '@loader_path/' + Path(dep).name, target)
            run('strip', '-S', target)
            run('codesign', '--force', '--sign', '-', target)
        else:
            run('strip', '--strip-debug', target)
            run('patchelf', '--set-rpath', '$ORIGIN', target)
    return [{'name': name, 'source_path': str(path), 'source_sha256': sha(path),
             'sha256': sha(destination / name)} for name, path in origins.items()]


def stage_mpv(work, prefix):
    matches = sorted((prefix / 'lib').glob('libmpv.*.dylib' if MAC else 'libmpv.so.*'))
    if not matches:
        raise RuntimeError('Native libmpv was not installed')
    library = matches[0]
    directory = work / 'mpv-runtime'
    # Immutable runtime members are staged once per content-keyed build. A new
    # dependency build must get a new key instead of mixing old/new libraries.
    binding = directory / 'runtime.json'
    if binding.exists():
        rows = json.loads(binding.read_text())
        if rows[0]['source_sha256'] != sha(library.resolve()):
            raise RuntimeError('MPV source output changed; use a new runtime staging key')
        if any(sha(directory / row['name']) != row['sha256'] for row in rows):
            raise RuntimeError('Retained MPV payload was changed')
    else:
        rows = copy_closure([library], directory)
        binding.write_text(json.dumps(rows, indent=2) + '\n')
    relative = '../Frameworks/mpv/' if MAC else '../lib/mpv/'
    header = work / 'vlc-build/modules/gui/qt/mpv_runtime_identity.hpp'
    header.parent.mkdir(parents=True, exist_ok=True)
    text = ('// Generated from the staged, stripped native runtime.\n#pragma once\n'
            'namespace MpvRuntimeIdentity {\nstruct File { const char *name; const char *sha256; };\n'
            'inline constexpr File files[] = {\n')
    text += ''.join('    {"' + relative + row['name'] + '", "' + row['sha256'] + '"},\n' for row in rows)
    text += '};\n}\n'
    if not header.exists() or header.read_text() != text:
        header.write_text(text)


def write_executable(path, text):
    path.write_text(text)
    path.chmod(0o755)


def package_mac(work, installed, out, version, arch):
    app = out / 'Modern VLC.app'
    if app.exists():
        raise RuntimeError('Package directory already exists; preserve or retire its consumers before rebuilding')
    contents = app / 'Contents'
    binaries = contents / 'MacOS'; binaries.mkdir(parents=True)
    frameworks = contents / 'Frameworks'; frameworks.mkdir()
    resources = contents / 'Resources'; resources.mkdir()
    shutil.copy2(installed / 'bin/vlc-osx', binaries / 'vlc')
    for parent in (installed / 'libexec', installed / 'bin'):
        for path in parent.rglob('*') if parent.exists() else []:
            if path.is_file() and path.name in ('vlc-qt-check', 'vlc-preparser', 'vlc-cache-gen'):
                shutil.copy2(path, binaries / path.name)
    shutil.copytree(installed / 'lib/vlc/plugins', frameworks / 'plugins')
    shutil.copytree(installed / 'share/vlc', resources / 'share')
    shutil.copytree(work / 'mpv-runtime', frameworks / 'mpv')
    for path in (installed / 'lib').glob('libvlc*.dylib'):
        shutil.copy2(path.resolve(), frameworks / path.name)
    # Qt deploys its plugin/QML/framework graph using the actual app executable
    # and Qt interface module, rather than swapping in the upstream Cocoa UI.
    info = {'CFBundleIdentifier': 'io.github.darkaxt.modern-vlc', 'CFBundleName': 'Modern VLC',
            'CFBundleDisplayName': 'Modern VLC Fork', 'CFBundleExecutable': 'vlc',
            'CFBundlePackageType': 'APPL', 'CFBundleShortVersionString': version,
            'CFBundleVersion': version, 'LSMinimumSystemVersion': '13.0',
            'NSHighResolutionCapable': True, 'NSPrincipalClass': 'NSApplication'}
    (contents / 'Info.plist').write_bytes(plistlib.dumps(info))
    qt = Path(output('brew', '--prefix', 'qt'))
    run(qt / 'bin/macdeployqt', app, '-qmldir=' + str(ROOT / 'modules/gui/qt'), '-always-overwrite',
        '-executable=' + str(frameworks / 'plugins/gui/libqt_plugin.dylib'))
    run('codesign', '--force', '--sign', '-', app)
    run('codesign', '--verify', '--deep', '--strict', app)
    zip_path = out / f'Modern-VLC-Fork-{version}-macos-{arch}.zip'
    run('ditto', '-c', '-k', '--sequesterRsrc', '--keepParent', app, zip_path)
    run('hdiutil', 'create', '-volname', 'Modern VLC Fork', '-srcfolder', app,
        '-format', 'UDZO', out / f'Modern-VLC-Fork-{version}-macos-{arch}.dmg')


def package_linux(work, installed, out, version, arch):
    app = out / f'Modern-VLC-Fork-{version}-linux-{arch}'
    if app.exists():
        raise RuntimeError('Package directory already exists; finish consumers and retire old staging explicitly')
    shutil.copytree(installed, app, symlinks=True)
    shutil.copytree(work / 'mpv-runtime', app / 'lib/mpv')
    deps = app / 'lib/native'; deps.mkdir()
    binaries = [p for p in app.rglob('*') if native(p) and 'mpv' not in p.relative_to(app).parts]
    required = []
    for path in binaries:
        required.extend(Path(dep) for dep in dependencies(path) if not external(dep)
                        and not Path(dep).is_relative_to(installed))
    closure = copy_closure(required, deps)
    (app / 'NATIVE-DEPENDENCIES.json').write_text(json.dumps(closure, indent=2) + '\n')
    for path in binaries:
        run('strip', '--strip-debug', path)
        relative = os.path.relpath(app / 'lib', path.parent)
        run('patchelf', '--set-rpath', '$ORIGIN/' + relative + ':$ORIGIN/' + relative + '/native', path)
    write_executable(app / 'modern-vlc', '''#!/bin/sh
set -eu
root=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
export VLC_LIB_PATH="$root/lib/vlc" VLC_DATA_PATH="$root/share/vlc" VLC_LIBEXEC_PATH="$root/libexec/vlc"
export QT_QPA_PLATFORM=xcb
export XDG_CONFIG_HOME="${XDG_CONFIG_HOME:-$HOME/.config}/modern-vlc"
export XDG_DATA_HOME="${XDG_DATA_HOME:-$HOME/.local/share}/modern-vlc"
export XDG_CACHE_HOME="${XDG_CACHE_HOME:-$HOME/.cache}/modern-vlc"
exec "$root/bin/vlc" --intf=qt "$@"
''')
    write_executable(app / 'AppRun', '#!/bin/sh\nexec "$(dirname "$0")/modern-vlc" "$@"\n')
    desktop = '[Desktop Entry]\nType=Application\nName=Modern VLC Fork\nExec=modern-vlc %U\nIcon=modern-vlc\nCategories=AudioVideo;Player;\n'
    (app / 'modern-vlc.desktop').write_text(desktop)
    shutil.copy2(ROOT / 'share/icons/256x256/vlc.png', app / 'modern-vlc.png')
    with tarfile.open(out / (app.name + '.tar.xz'), 'w:xz') as archive:
        archive.add(app, arcname=app.name)
    deb = work / 'deb'
    target = deb / 'opt/modern-vlc'; target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(app, target)
    control = deb / 'DEBIAN'; control.mkdir()
    deb_arch = 'arm64' if arch == 'aarch64' else 'amd64'
    (control / 'control').write_text(f'Package: modern-vlc-fork\nVersion: {version}\nArchitecture: {deb_arch}\n'
        'Maintainer: Darkaxt\nDepends: libc6 (>= 2.38), libgl1, libegl1, libx11-6\n'
        'Description: Modern VLC Fork with the Qt redesign and VLC/MPV engines\n')
    run('dpkg-deb', '--build', '--root-owner-group', deb, out / f'{app.name}.deb')
    # Additional formats are generated from this same payload, never rebuilt
    # with a smaller plugin graph. Their installation is a later native check.
    runtime_pins = {'x86_64': '617aa77314d57c8b8e4fae9c3f0b35af7b30d5529cb69e98f64f92510ed98a46',
                    'aarch64': '9a72a744d221576c9347ec074243acc5c3c7568896b12714e0e82e9f0bf47900'}
    runtime = work / ('appimage-runtime-' + arch)
    if not runtime.exists():
        urllib.request.urlretrieve('https://github.com/AppImage/type2-runtime/releases/download/continuous/runtime-' + arch, runtime)
    if sha(runtime) != runtime_pins[arch]:
        raise RuntimeError('AppImage runtime no longer matches the pinned digest')
    squash = work / 'appimage.squashfs'
    run('mksquashfs', app, squash, '-noappend', '-comp', 'zstd', '-processors', '1', '-root-owned')
    image = out / (app.name + '.AppImage')
    with image.open('wb') as stream:
        for part in (runtime, squash):
            with part.open('rb') as source:
                shutil.copyfileobj(source, stream)
    image.chmod(0o755)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=('stage-mpv', 'packages'))
    parser.add_argument('--work', required=True, type=Path)
    parser.add_argument('--prefix', required=True, type=Path)
    args = parser.parse_args()
    if args.operation == 'stage-mpv':
        stage_mpv(args.work.resolve(), args.prefix.resolve())
        return
    version = re.search(r'"(\d+\.\d+\.\d+)"',
        (ROOT / 'modules/gui/qt/dialogs/help/fork_release.hpp').read_text()).group(1)
    out = args.work / 'packages'; out.mkdir(exist_ok=True)
    architecture = platform.machine()
    if MAC:
        package_mac(args.work, args.work / 'installed', out, version, architecture)
    else:
        package_linux(args.work, args.work / 'installed', out, version, architecture)
    (out / 'PACKAGE-STATUS.json').write_text(json.dumps({
        'version': version, 'source_commit': output('git', '-C', ROOT, 'rev-parse', 'HEAD'),
        'state': 'GENERATED; native release qualification not yet performed',
        'assets': [{'name': p.name, 'sha256': sha(p)} for p in out.iterdir() if p.is_file()]}, indent=2) + '\n')


if __name__ == '__main__':
    main()
