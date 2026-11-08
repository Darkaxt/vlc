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
        identity = output('otool', '-D', path).splitlines()[1:]
        return [dep for line in lines if (dep := line.strip().split(' (')[0]) not in identity]
    lines = output('ldd', path).splitlines()
    if any('not found' in line for line in lines):
        raise RuntimeError(f'Unresolved native dependency: {path}\n' + '\n'.join(lines))
    return [match.group(1) for line in lines if (match := re.search(r'=> (/[^ ]+)', line))]


def mac_runpath_bindings(origin):
    lines = output('otool', '-l', origin).splitlines()
    result = []
    for index, line in enumerate(lines):
        if line.strip() == 'cmd LC_RPATH':
            original = lines[index + 2].strip().removeprefix('path ').split(' (offset ')[0]
            value = original
            if value.startswith('@loader_path/'):
                value = str(origin.parent / value.removeprefix('@loader_path/'))
            if value == '@loader_path':
                value = str(origin.parent)
            result.append((original, value))
    return result


def mac_runpaths(origin):
    return [resolved for original, resolved in mac_runpath_bindings(origin)]


def stage_qml_modules(imports, destination):
    """Preserve the scanner's module graph without copying sibling modules.

    macdeployqt recursively copies a module's entire directory. In Homebrew's
    merged QML tree, QtQuick also contains unrelated Qt3D modules; QtQml contains
    StateMachine. Those are independent modules, not resources of their parent.
    Copy each scanned module and its assets, letting the scanner select child
    modules explicitly. The installed SDK is read-only input throughout.
    """
    destination.mkdir(parents=True, exist_ok=False)
    modules = {}
    for item in imports:
        name, origin = item.get('name', ''), item.get('path', '')
        if item.get('type') != 'module' or not origin or not name.startswith('Qt'):
            continue
        if not re.fullmatch(r'[A-Za-z0-9_]+(?:\.[A-Za-z0-9_]+)*', name):
            raise RuntimeError('Invalid Qt QML module URI: ' + name)
        origin = Path(origin).resolve(strict=True)
        if name in modules and modules[name] != origin:
            raise RuntimeError('Conflicting QML module sources: ' + name)
        modules[name] = origin
    if not modules:
        raise RuntimeError('Qt import scanner found no resolved Qt modules')
    records = []

    def copy_contents(origin, target, native_bindings, source_files):
        target.mkdir(parents=True, exist_ok=True)
        for child in sorted(origin.iterdir()):
            copied = target / child.name
            if child.is_dir():
                if not (child / 'qmldir').is_file():
                    copy_contents(child, copied, native_bindings, source_files)
            elif child.is_file():
                shutil.copy2(child, copied)
                source_files.append({'source': str(child.resolve(strict=True)),
                                     'sha256': sha(child)})
                if MAC and native(copied):
                    # Resolve LC_RPATH in the source location before Qt moves
                    # the plugin. Relative source paths otherwise point into
                    # the app after deployment and lose modular framework roots.
                    bindings = mac_runpath_bindings(child.resolve(strict=True))
                    copied.chmod(copied.stat().st_mode | stat.S_IWUSR)
                    for original, resolved in bindings:
                        if original != resolved:
                            run('install_name_tool', '-rpath', original, resolved, copied)
                    native_bindings.append({'file': str(copied.relative_to(destination)),
                        'source_sha256': sha(child), 'runpaths': bindings})

    for name, origin in sorted(modules.items(), key=lambda item: (item[0].count('.'), item[0])):
        bindings, source_files = [], []
        copy_contents(origin, destination.joinpath(*name.split('.')), bindings, source_files)
        records.append({'name': name, 'source': str(origin), 'native_bindings': bindings,
                        'source_files': source_files})
    return records


def prepare_mac_qml(work, qt, generation):
    qmake = qt / 'bin/qmake'
    qml = Path(output(qmake, '-query', 'QT_INSTALL_QML'))
    candidates = [Path(output(qmake, '-query', 'QT_HOST_LIBEXECS')) / 'qmlimportscanner',
                  qt / 'libexec/qmlimportscanner', qt / 'bin/qmlimportscanner']
    scanner = next((path for path in candidates if path.is_file()), None)
    if scanner is None:
        raise RuntimeError('Installed native Qt import scanner is missing: ' + str(candidates))
    imports = json.loads(output(scanner, '-rootPath', ROOT / 'modules/gui/qt', '-importPath', qml))
    directory = work / 'qml-deployment' / generation
    records = stage_qml_modules(imports, directory)
    (directory.parent / (generation + '.json')).write_text(json.dumps({
        'scanner': str(scanner), 'installed_qml': str(qml), 'modules': records}, indent=2) + '\n')
    return directory


def stage_mac_qt_plugins(qt, app):
    # Match the native GUI/network/image plugin categories needed by this Qt
    # interface. Qt's automatic copy loses each Homebrew module's source RPATH;
    # supply owned, rebased plugins as explicit deployment inputs instead.
    qmake = qt / 'bin/qmake'
    installed = Path(output(qmake, '-query', 'QT_INSTALL_PLUGINS'))
    copied = []
    records = []
    for category in ('platforms', 'printsupport', 'styles', 'tls', 'networkinformation',
                     'imageformats', 'iconengines', 'platforminputcontexts', 'virtualkeyboard'):
        origin = installed / category
        if not origin.is_dir():
            continue
        # iterdir follows a category symlink too; rglob's default would miss
        # categories provided solely by one separately installed Qt module.
        for plugin in sorted(origin.glob('*.dylib')):
            if '_debug.' in plugin.name or (category == 'platforms' and 'cocoa' not in plugin.name):
                continue
            target = app / 'Contents/PlugIns' / category / plugin.name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(plugin, target)
            target.chmod(target.stat().st_mode | stat.S_IWUSR)
            bindings = mac_runpath_bindings(plugin.resolve(strict=True))
            for original, resolved in bindings:
                if original != resolved:
                    run('install_name_tool', '-rpath', original, resolved, target)
            copied.append(target)
            records.append({'file': target.relative_to(app).as_posix(),
                'source': str(plugin.resolve()), 'source_sha256': sha(plugin), 'runpaths': bindings})
    if not any(path.parent.name == 'platforms' for path in copied):
        raise RuntimeError('The installed Qt Cocoa platform plugin is missing')
    (app / 'Contents/Resources/QT-PLUGINS.json').write_text(json.dumps(records, indent=2) + '\n')
    return copied


def resolve_mac_dependency(dep, origin, runpaths):
    if dep.startswith('@loader_path/'):
        return origin.parent / dep.removeprefix('@loader_path/')
    if dep.startswith('@rpath/'):
        suffix = dep.removeprefix('@rpath/')
        for directory in runpaths:
            candidate = Path(directory) / suffix
            if candidate.is_file():
                return candidate
        raise RuntimeError(f'Unresolved LC_RPATH dependency {dep} in {origin}; searched {runpaths}')
    if dep.startswith('@'):
        raise RuntimeError(f'Unsupported native dependency binding {dep} in {origin}')
    return Path(dep)


def external(dep):
    if MAC:
        return dep.startswith(('/System/', '/usr/lib/'))
    name = Path(dep).name
    # Never ship the host libc, loader, or graphics driver dispatch. Their ABI
    # and native driver belong to the destination OS, not this application.
    return bool(re.match(r'^(ld-linux|lib(c|m|dl|pthread|rt|resolv|util)\.so|lib(GL|EGL|OpenGL|GLX|GLdispatch|drm|gbm))', name))


def resolve_packaged_mac_dependency(dep, origin, executable, app, runpaths=None):
    def expand(value):
        if value == '@loader_path' or value.startswith('@loader_path/'):
            return origin.parent / value.removeprefix('@loader_path').lstrip('/')
        if value == '@executable_path' or value.startswith('@executable_path/'):
            return executable.parent / value.removeprefix('@executable_path').lstrip('/')
        if value.startswith('@') or not Path(value).is_absolute():
            raise RuntimeError('Unresolved packaged Mach-O path: ' + value)
        return Path(value)

    if dep.startswith('@rpath/'):
        if runpaths is None:
            runpaths = mac_runpaths(origin) + mac_runpaths(executable)
        candidates = [expand(directory) / dep.removeprefix('@rpath/') for directory in runpaths]
    else:
        candidates = [expand(dep)]
    for candidate in candidates:
        if not candidate.is_file():
            continue
        resolved = candidate.resolve()
        if not resolved.is_relative_to(app.resolve()):
            raise RuntimeError(f'Packaged dependency resolves outside the app: {origin}: {dep}: {resolved}')
        return resolved
    raise RuntimeError(f'Missing packaged dependency {dep} in {origin}; searched {candidates}')


def audit_package(app, executable, arch, receipt):
    """Check every shipped native module, including ones playback may not load.

    A runner's installed Qt/codec SDK must not mask an incomplete portable app.
    Signing follows this audit so its resource receipt is sealed in the bundle.
    """
    root = app.resolve()
    files = sorted({path.resolve() for path in app.rglob('*') if native(path)})
    records = []
    executable_runpaths = mac_runpaths(executable) if MAC else []
    errors = []
    for path in files:
        if not path.is_relative_to(root):
            raise RuntimeError('Packaged native symlink escaped the app: ' + str(path))
        if MAC:
            architectures = output('lipo', '-archs', path).split()
            if arch not in architectures:
                raise RuntimeError(f'Wrong packaged architecture {path}: {architectures}')
        else:
            machine = re.search(r'(?m)^\s*Machine:\s*(.+)$', output('readelf', '-h', path)).group(1)
            expected = {'x86_64': 'Advanced Micro Devices X86-64', 'aarch64': 'AArch64'}[arch]
            if machine != expected:
                raise RuntimeError(f'Wrong packaged architecture {path}: {machine}')
            architectures = [arch]
        linked = []
        deps = dependencies(path)
        runpaths = mac_runpaths(path) + executable_runpaths if MAC and any(
            dep.startswith('@rpath/') for dep in deps) else []
        for dep in deps:
            if external(dep):
                linked.append({'os_dependency': dep})
                continue
            try:
                resolved = resolve_packaged_mac_dependency(dep, path, executable, root, runpaths) if MAC else Path(dep).resolve()
                if not resolved.is_relative_to(root):
                    raise RuntimeError(f'Packaged dependency resolves outside the app: {path}: {dep}')
                linked.append({'packaged_dependency': resolved.relative_to(root).as_posix()})
            except RuntimeError as error:
                errors.append(str(error))
                linked.append({'unresolved_dependency': dep, 'error': str(error)})
        records.append({'file': path.relative_to(root).as_posix(),
                        'architectures': architectures, 'dependencies': linked})
    if not records:
        raise RuntimeError('Native package contains no native binaries')
    receipt.write_text(json.dumps({'state': 'FAILED' if errors else 'architecture and dependency closure verified',
        'architecture': arch, 'members': records, 'errors': errors}, indent=2) + '\n')
    if errors:
        raise RuntimeError('Native package dependency audit failed:\n' + '\n'.join(errors))


def copy_closure(initial, destination):
    destination.mkdir(parents=True, exist_ok=True)
    queue = [(Path(path), []) for path in initial]
    origins = {}
    while queue:
        origin, inherited_runpaths = queue.pop(0)
        real = origin.resolve(strict=True)
        name = origin.name
        if name in origins:
            if sha(origins[name]) != sha(real):
                raise RuntimeError('Conflicting native library basename: ' + name)
            continue
        origins[name] = real
        target = destination / name
        # Homebrew bottles carry read-only library modes. A partial closure
        # from an interrupted staging pass is still owned generated output;
        # restore its write permission before replacing its bytes.
        if target.exists():
            target.chmod(target.stat().st_mode | stat.S_IWUSR)
        shutil.copy2(real, target)
        runpaths = mac_runpaths(real) + inherited_runpaths if MAC else []
        for dep in dependencies(real):
            if external(dep):
                continue
            if MAC and '.framework/' in dep:
                continue  # Qt's macdeployqt owns framework/plugin deployment.
            resolved = resolve_mac_dependency(dep, real, runpaths) if MAC else Path(dep)
            queue.append((resolved, runpaths))
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


def split_symbols(path, relative, work):
    saved = work / 'symbols' / relative
    saved.parent.mkdir(parents=True, exist_ok=True)
    if MAC:
        # Keep the matching unstripped Mach-O when the release toolchain emits
        # no DWARF (-g0). Do not advertise a nonexistent dSYM.
        shutil.copy2(path, saved)
    else:
        run('objcopy', '--only-keep-debug', path, saved)


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


def verify_bundled_mpv(work, directory):
    rows = json.loads((work / 'mpv-runtime/runtime.json').read_text())
    for row in rows:
        if sha(directory / row['name']) != row['sha256']:
            raise RuntimeError('Packaging changed the compiled MPV runtime identity: ' + row['name'])


def mac_minimum_system(load_commands):
    """Read deployment targets, without confusing SDK versions with minOS."""
    versions = []
    for block in re.split(r'(?m)^Load command \d+\s*$', load_commands):
        if re.search(r'\bcmd LC_BUILD_VERSION\b', block):
            match = re.search(r'(?m)^\s*minos ([\d.]+)\s*$', block)
        elif re.search(r'\bcmd LC_VERSION_MIN_MACOSX\b', block):
            match = re.search(r'(?m)^\s*version ([\d.]+)\s*$', block)
        else:
            continue
        if match:
            versions.append(tuple(map(int, match.group(1).split('.'))))
    return max(versions, default=(0,))


def refresh_mac_plugin_cache(app, home):
    # VLC validates cached entries against plugin size and mtime. Both the
    # normal app and a review app with a replaced Qt plugin need a fresh index.
    contents = app / 'Contents'
    home.mkdir(parents=True, exist_ok=True)
    environment = os.environ.copy()
    environment.update(HOME=str(home), VLC_LIB_PATH=str(contents / 'Frameworks'),
        VLC_DATA_PATH=str(contents / 'Resources/share'), VLC_LIBEXEC_PATH=str(contents / 'MacOS'))
    plugins = contents / 'Frameworks/plugins'
    run(contents / 'MacOS/vlc-cache-gen', plugins, env=environment)
    run('codesign', '--force', '--sign', '-', plugins / 'plugins.dat')


def package_mac(work, installed, out, version, arch):
    app = out / 'Modern VLC.app'
    if app.exists():
        raise RuntimeError('Package directory already exists; preserve or retire its consumers before rebuilding')
    contents = app / 'Contents'
    binaries = contents / 'MacOS'; binaries.mkdir(parents=True)
    frameworks = contents / 'Frameworks'; frameworks.mkdir()
    resources = contents / 'Resources'; resources.mkdir()
    iconset = work / 'Modern-VLC.iconset'; iconset.mkdir(exist_ok=True)
    shutil.copy2(ROOT / 'modules/gui/qt/pixmaps/redesign/app.png', iconset / 'icon_256x256.png')
    run('iconutil', '-c', 'icns', iconset, '-o', resources / 'Modern-VLC.icns')
    # bin/Makefile.am's install-data-local renames vlc-osx to vlc.
    shutil.copy2(installed / 'bin/vlc', binaries / 'vlc')
    for parent in (installed / 'libexec', installed / 'bin'):
        for path in parent.rglob('*') if parent.exists() else []:
            if path.is_file() and path.name in ('vlc-qt-check', 'vlc-preparser', 'vlc-cache-gen'):
                shutil.copy2(path, binaries / path.name)
    # Prepare VLC's complete runtime plugin graph separately. macdeployqt
    # rewrites every discovered library for every Qt dependency; only the Qt
    # interface needs that pass. Adding the other VLC plugins afterwards avoids
    # thousands of unrelated install_name_tool operations without reducing VLC.
    plugins = work / 'plugin-deployment' / out.name
    shutil.copytree(installed / 'lib/vlc/plugins', plugins,
                    ignore=shutil.ignore_patterns('*.la', '*.a', 'plugins.dat'))
    # Match VLC's native macOS package route for the configured Blu-ray Java
    # companion. It is runtime code, not a host JDK or build tool.
    for jar in (work / 'native-contrib').glob('*/share/java/libbluray*.jar'):
        shutil.copy2(jar, plugins / jar.name)
    shutil.copytree(installed / 'share/vlc', resources / 'share')
    shutil.copytree(installed / 'libexec/vlc/lua', frameworks / 'lua')
    shutil.copytree(ROOT / 'share/hrtfs', resources / 'share/hrtfs')
    for path in (installed / 'lib').glob('libvlc*.dylib'):
        shutil.copy2(path.resolve(), frameworks / path.name)
    originals = [p for p in app.rglob('*') if native(p) and 'mpv' not in p.relative_to(app).parts]
    originals.extend(path for path in plugins.rglob('*') if native(path))
    required = []
    for path in originals:
        required.extend(Path(dep) for dep in dependencies(path)
                        if not external(dep) and not dep.startswith('@') and '.framework/' not in dep)
    closure = copy_closure(required, frameworks / 'native')
    (resources / 'NATIVE-DEPENDENCIES.json').write_text(json.dumps(closure, indent=2) + '\n')
    for path in originals:
        deployed = frameworks / 'plugins' / path.relative_to(plugins) if path.is_relative_to(plugins) else path
        split_symbols(path, deployed.relative_to(app), work)
        for dep in dependencies(path):
            if external(dep) or '.framework/' in dep:
                continue
            name = Path(dep).name
            own = frameworks / name
            replacement = own if own.exists() else frameworks / 'native' / name
            if not replacement.exists():
                raise RuntimeError(f'Unresolved package dependency {dep}: {path}')
            run('install_name_tool', '-change', dep,
                '@loader_path/' + os.path.relpath(replacement, deployed.parent), path)
        run('strip', '-S', path)
    # Qt deploys its plugin/QML/framework graph using the actual app executable
    # and Qt interface module, rather than swapping in the upstream Cocoa UI.
    info = {'CFBundleIdentifier': 'io.github.darkaxt.modern-vlc', 'CFBundleName': 'Modern VLC',
            'CFBundleDisplayName': 'Modern VLC Fork', 'CFBundleExecutable': 'vlc',
            'CFBundleIconFile': 'Modern-VLC.icns',
            'CFBundlePackageType': 'APPL', 'CFBundleShortVersionString': version,
            'CFBundleVersion': version, 'LSMinimumSystemVersion': '13.0',
            'NSHighResolutionCapable': True, 'NSPrincipalClass': 'NSApplication'}
    (contents / 'Info.plist').write_bytes(plistlib.dumps(info))
    gui = frameworks / 'plugins/gui'
    gui.mkdir(parents=True)
    shutil.copy2(plugins / 'gui/libqt_plugin.dylib', gui / 'libqt_plugin.dylib')
    qt = Path(output('brew', '--prefix', 'qt'))
    qml = prepare_mac_qml(work, qt, out.name)
    qt_plugins = stage_mac_qt_plugins(qt, app)
    # macdeployqt discovers dylibs, but its default executable root is only
    # vlc. The startup Qt probe is a separate linked executable, not a dylib.
    qt_executables = [path for path in binaries.iterdir() if path.name != 'vlc' and native(path)]
    # This bundle is a new source-bound generation. Qt must keep its normal
    # already-deployed dependency deduplication, rather than overwrite shared
    # frameworks again for every QML/plugin branch.
    run(qt / 'bin/macdeployqt', app, '-qmldir=' + str(ROOT / 'modules/gui/qt'),
        '-qmlimport=' + str(qml), '-verbose=2', '-no-codesign', '-no-plugins',
        *('-executable=' + str(path) for path in qt_plugins + qt_executables),
        '-executable=' + str(frameworks / 'plugins/gui/libqt_plugin.dylib'))
    shutil.copytree(plugins, frameworks / 'plugins', dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns('libqt_plugin.dylib'))
    # libmpv is loaded dynamically and has no Qt dependency. Install its already
    # signed immutable closure after Qt's deployment rewrites, not as input to
    # a second linker/signing pass over every library in the bundle.
    shutil.copytree(work / 'mpv-runtime', frameworks / 'mpv',
                    ignore=shutil.ignore_patterns('runtime.json'))
    shutil.copy2(work / 'mpv-runtime/runtime.json', resources / 'MPV-RUNTIME.json')
    minimums = {str(path.relative_to(app)): mac_minimum_system(output('otool', '-l', path))
                for path in app.rglob('*') if native(path)}
    minimum = max((13, 0), *minimums.values())
    info['LSMinimumSystemVersion'] = '.'.join(map(str, minimum))
    (contents / 'Info.plist').write_bytes(plistlib.dumps(info))
    (resources / 'MINIMUM-SYSTEM.json').write_text(json.dumps({
        'minimum_macos': info['LSMinimumSystemVersion'], 'native_members': minimums}, indent=2) + '\n')
    audit_package(app, binaries / 'vlc', arch, resources / 'NATIVE-PACKAGE.json')
    run('python3', ROOT / 'tools/desktop-player/collect-native-sources.py', '--work', work,
        '--app', app, '--out', out, '--generation', out.name)
    # Sign inner objects before the outer bundle. MPV payloads were signed
    # before their identities were compiled and must remain byte-identical.
    for path in sorted(app.rglob('*'), key=lambda p: len(p.parts), reverse=True):
        # Upstream macOS codesign.sh also signs every compiled Lua file as
        # code/data below Frameworks. It cannot be invoked unchanged here: its
        # fixed VLC.app/Sparkle/Cocoa layout differs from this Qt app bundle.
        runtime_data = path.is_file() and (path.is_relative_to(frameworks / 'lua') or
            (path.is_relative_to(frameworks / 'plugins') and path.suffix == '.jar'))
        if (native(path) or runtime_data) and path != binaries / 'vlc' and 'mpv' not in path.relative_to(app).parts:
            run('codesign', '--force', '--sign', '-', path)
    # Stripping, relocating and signing change plugin size/mtime. Generate the
    # cache from these final runtime bytes, not the install prefix's old index.
    refresh_mac_plugin_cache(app, work / 'package-cachegen' / out.name)
    run('codesign', '--force', '--sign', '-', app)
    run('codesign', '--verify', '--deep', '--strict', app)
    verify_bundled_mpv(work, frameworks / 'mpv')
    zip_path = out / f'Modern-VLC-Fork-{version}-macos-{arch}.zip'
    run('ditto', '-c', '-k', '--sequesterRsrc', '--keepParent', app, zip_path)
    run('hdiutil', 'create', '-volname', 'Modern VLC Fork', '-srcfolder', app,
        '-format', 'UDZO', out / f'Modern-VLC-Fork-{version}-macos-{arch}.dmg')


def stage_linux_system_payload(app, root):
    """Give installable packages the same player plus real desktop entry points."""
    shutil.copytree(app, root / 'opt/modern-vlc')
    launcher = root / 'usr/bin/modern-vlc'
    launcher.parent.mkdir(parents=True)
    write_executable(launcher, '#!/bin/sh\nexec /opt/modern-vlc/modern-vlc "$@"\n')
    desktop = root / 'usr/share/applications/modern-vlc.desktop'
    desktop.parent.mkdir(parents=True)
    shutil.copy2(app / 'modern-vlc.desktop', desktop)
    icon = root / 'usr/share/icons/hicolor/256x256/apps/modern-vlc.png'
    icon.parent.mkdir(parents=True)
    shutil.copy2(app / 'modern-vlc.png', icon)


def package_linux(work, installed, out, version, arch):
    app = out / f'Modern-VLC-Fork-{version}-linux-{arch}'
    if app.exists():
        raise RuntimeError('Package directory already exists; finish consumers and retire old staging explicitly')
    shutil.copytree(installed, app, symlinks=True, ignore=shutil.ignore_patterns('*.la', '*.a'))
    shutil.copytree(work / 'mpv-runtime', app / 'lib/mpv')
    qt_plugins = Path(output('qmake6', '-query', 'QT_INSTALL_PLUGINS'))
    qt_qml = Path(output('qmake6', '-query', 'QT_INSTALL_QML'))
    qt_sources = []
    for name in ('platforms', 'imageformats', 'iconengines', 'platformthemes', 'styles', 'tls', 'xcbglintegrations'):
        if (qt_plugins / name).exists():
            shutil.copytree(qt_plugins / name, app / 'lib/qt/plugins' / name, symlinks=True)
            qt_sources.extend(str(path.resolve()) for path in (qt_plugins / name).rglob('*') if path.is_file())
    shutil.copytree(qt_qml, app / 'lib/qt/qml', symlinks=True)
    qt_sources.extend(str(path.resolve()) for path in qt_qml.rglob('*') if path.is_file())
    (app / 'QT-SOURCES.json').write_text(json.dumps(sorted(set(qt_sources)), indent=2) + '\n')
    deps = app / 'lib/native'; deps.mkdir()
    binaries = [p for p in app.rglob('*') if native(p) and 'mpv' not in p.relative_to(app).parts]
    required = []
    for path in binaries:
        required.extend(Path(dep) for dep in dependencies(path) if not external(dep)
                        and not Path(dep).is_relative_to(installed))
    closure = copy_closure(required, deps)
    (app / 'NATIVE-DEPENDENCIES.json').write_text(json.dumps(closure, indent=2) + '\n')
    for path in binaries:
        split_symbols(path, path.relative_to(app), work)
        run('strip', '--strip-debug', path)
        relative = os.path.relpath(app / 'lib', path.parent)
        run('patchelf', '--set-rpath', '$ORIGIN/' + relative + ':$ORIGIN/' + relative + '/native', path)
    write_executable(app / 'modern-vlc', '''#!/bin/sh
set -eu
root=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
export VLC_LIB_PATH="$root/lib/vlc" VLC_DATA_PATH="$root/share/vlc" VLC_LIBEXEC_PATH="$root/libexec/vlc"
export QT_QPA_PLATFORM=xcb
export QT_PLUGIN_PATH="$root/lib/qt/plugins"
export QML_IMPORT_PATH="$root/lib/qt/qml" QML2_IMPORT_PATH="$root/lib/qt/qml"
export XDG_CONFIG_HOME="${XDG_CONFIG_HOME:-$HOME/.config}/modern-vlc"
export XDG_DATA_HOME="${XDG_DATA_HOME:-$HOME/.local/share}/modern-vlc"
export XDG_CACHE_HOME="${XDG_CACHE_HOME:-$HOME/.cache}/modern-vlc"
exec "$root/bin/vlc" --intf=qt "$@"
''')
    write_executable(app / 'AppRun', '#!/bin/sh\nexec "$(dirname "$0")/modern-vlc" "$@"\n')
    desktop = '[Desktop Entry]\nType=Application\nName=Modern VLC Fork\nExec=modern-vlc %U\nIcon=modern-vlc\nCategories=AudioVideo;Player;\n'
    (app / 'modern-vlc.desktop').write_text(desktop)
    shutil.copy2(ROOT / 'modules/gui/qt/pixmaps/redesign/app.png', app / 'modern-vlc.png')
    verify_bundled_mpv(work, app / 'lib/mpv')
    audit_package(app, app / 'bin/vlc', arch, app / 'NATIVE-PACKAGE.json')
    runtime_pins = json.loads((ROOT / 'tools/desktop-player/native-inputs.json').read_text())['appimage_runtime']
    runtime = work / ('appimage-runtime-' + arch)
    if not runtime.exists():
        urllib.request.urlretrieve('https://github.com/AppImage/type2-runtime/releases/download/continuous/runtime-' + arch, runtime)
    if sha(runtime) != runtime_pins[arch + '_sha256']:
        raise RuntimeError('AppImage runtime no longer matches the pinned digest')
    run('python3', ROOT / 'tools/desktop-player/collect-native-sources.py', '--work', work,
        '--app', app, '--out', out, '--generation', out.name)
    with tarfile.open(out / (app.name + '.tar.xz'), 'w:xz') as archive:
        archive.add(app, arcname=app.name)
    staging = work / 'linux-package-staging' / out.name
    staging.mkdir(parents=True, exist_ok=False)
    system_payload = staging / 'system'
    stage_linux_system_payload(app, system_payload)
    deb = staging / 'deb'
    shutil.copytree(system_payload, deb)
    control = deb / 'DEBIAN'; control.mkdir()
    deb_arch = 'arm64' if arch == 'aarch64' else 'amd64'
    (control / 'control').write_text(f'Package: modern-vlc-fork\nVersion: {version}\nArchitecture: {deb_arch}\n'
        'Maintainer: Darkaxt\nDepends: libc6 (>= 2.38), libgl1, libegl1, libx11-6\n'
        'Description: Modern VLC Fork with the Qt redesign and VLC/MPV engines\n')
    run('dpkg-deb', '--build', '--root-owner-group', deb, out / f'{app.name}.deb')
    rpm_root = staging / 'rpm'
    for name in ('BUILD', 'BUILDROOT', 'RPMS', 'SOURCES', 'SPECS', 'SRPMS'):
        (rpm_root / name).mkdir(parents=True, exist_ok=True)
    with tarfile.open(rpm_root / 'SOURCES/payload.tar.gz', 'w:gz') as archive:
        archive.add(system_payload, arcname='.')
    spec = rpm_root / 'SPECS/modern-vlc.spec'
    spec.write_text(f'''Name: modern-vlc-fork
Version: {version}
Release: 1
Summary: Modern VLC Fork Qt redesign with VLC and MPV
License: GPL-3.0-or-later
Source0: payload.tar.gz
AutoReqProv: no
Requires: glibc >= 2.38, libGL.so.1()(64bit), libEGL.so.1()(64bit)
%description
Modern VLC Fork with the Qt redesign and VLC/MPV engines.
%prep
%build
%install
mkdir -p %{{buildroot}}
tar -xzf %{{SOURCE0}} -C %{{buildroot}}
%files
%defattr(-,root,root,-)
/opt/modern-vlc
/usr/bin/modern-vlc
/usr/share/applications/modern-vlc.desktop
/usr/share/icons/hicolor/256x256/apps/modern-vlc.png
''')
    run('rpmbuild', '-bb', '--define', '_topdir ' + str(rpm_root), '--define', '__os_install_post %{nil}', spec)
    for artifact in (rpm_root / 'RPMS').rglob('*.rpm'):
        shutil.copy2(artifact, out / (app.name + '.rpm'))
    snap = staging / 'snap'; snap.mkdir()
    shutil.copytree(app, snap / 'player')
    meta = snap / 'meta'; meta.mkdir()
    (meta / 'snap.yaml').write_text(f'''name: modern-vlc-fork
version: '{version}'
summary: Modern VLC Fork with the Qt redesign
description: VLC and stock MPV playback using the redesigned Qt interface.
base: core24
grade: stable
confinement: strict
architectures: [{deb_arch}]
apps:
  modern-vlc:
    command: player/modern-vlc
    plugs: [desktop, desktop-legacy, x11, audio-playback, opengl, home, network, removable-media]
''')
    run('mksquashfs', snap, out / (app.name + '.snap'), '-noappend', '-comp', 'xz', '-processors', '1', '-root-owned')
    # Additional formats are generated from this same payload, never rebuilt
    # with a smaller plugin graph. Their installation is a later native check.
    squash = staging / 'appimage.squashfs'
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
    # A repaired packager gets a distinct owned output generation. Preserve
    # the failed generation and its diagnostic evidence, without discarding
    # compiler/dependency objects or overwriting a package still being read.
    commit = output('git', '-C', ROOT, 'rev-parse', 'HEAD')
    out = args.work / 'packages' / commit
    out.mkdir(parents=True, exist_ok=True)
    (args.work / 'package-output.json').write_text(json.dumps({
        'source_commit': commit, 'directory': str(out.resolve()),
        'qualification': 'PENDING'}, indent=2) + '\n')
    architecture = platform.machine()
    if MAC:
        package_mac(args.work, args.work / 'installed', out, version, architecture)
    else:
        package_linux(args.work, args.work / 'installed', out, version, architecture)
    symbols = out / f'Modern-VLC-Fork-{version}-{platform.system().lower()}-{architecture}-symbols.zip'
    with zipfile.ZipFile(symbols, 'w', zipfile.ZIP_DEFLATED) as archive:
        for path in (args.work / 'symbols').rglob('*'):
            if path.is_file():
                archive.write(path, path.relative_to(args.work / 'symbols'))
    (out / 'PACKAGE-STATUS.json').write_text(json.dumps({
        'version': version, 'source_commit': output('git', '-C', ROOT, 'rev-parse', 'HEAD'),
        'state': 'GENERATED; native release qualification not yet performed',
        'assets': [{'name': p.name, 'sha256': sha(p)} for p in out.iterdir() if p.is_file()]}, indent=2) + '\n')


if __name__ == '__main__':
    main()
