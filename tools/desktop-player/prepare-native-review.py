#!/usr/bin/env python3
"""Build the existing test-only Qt hook into a separate native review payload.

Normal release objects and libraries are restored in finally, including their
timestamps. Recovery bytes live in the hosted runner's disposable temp area,
outside the retained build cache and all release packages.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('native_package', Path(__file__).with_name('package-native.py'))
package = importlib.util.module_from_spec(spec)
spec.loader.exec_module(package)

# These translation units contain the native diagnostic conditionals. Changing
# make's CPPFLAGS alone does not invalidate their existing normal objects.
REVIEW_SOURCES = (
    'qt.cpp', 'maininterface/mainui.cpp', 'menus/menus.cpp',
    'dialogs/help/help.cpp', 'dialogs/preferences/preferences.cpp',
    'player/player_controller.cpp', 'player/player_controller_mpv.cpp',
    'player/mpv_playback.cpp',
)
REVIEW_MOC = 'player/player_controller.moc.cpp'


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work', required=True, type=Path)
    parser.add_argument('--review-root', required=True, type=Path)
    args = parser.parse_args()
    work = args.work.resolve()
    review = args.review_root.resolve()
    review.mkdir(parents=True, exist_ok=False)
    qt = work / 'vlc-build/modules/gui/qt'
    recovery = review / 'normal-object-recovery'
    recovery.mkdir()
    paths = [qt / 'libqt_plugin.la', qt / REVIEW_MOC]
    for source in (*REVIEW_SOURCES, REVIEW_MOC):
        relative = Path(source)
        stem = 'libqt_plugin_la-' + relative.stem
        paths.extend(qt / relative.parent / member for member in
                     (stem + '.lo', '.libs/' + stem + '.o', '.deps/' + stem + '.Plo'))
    paths.extend(path for path in (qt / '.libs').glob('libqt_plugin*')
                 if path.is_file() and not path.is_symlink())
    if any(not path.is_file() for path in paths):
        raise RuntimeError('Normal Qt object/library recovery set is incomplete')
    rows = []
    for path in paths:
        relative = path.relative_to(qt)
        saved = recovery / relative
        saved.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, saved)
        rows.append({'path': relative.as_posix(), 'sha256': digest(path),
                     'mtime_ns': path.stat().st_mtime_ns})
    (review / 'normal-recovery.json').write_text(json.dumps(rows, indent=2) + '\n')
    mac = platform.system() == 'Darwin'
    output_record = json.loads((work / 'package-output.json').read_text())
    packages = Path(output_record['directory']).resolve()
    if not packages.is_relative_to(work / 'packages'):
        raise RuntimeError('Native package generation escaped its owned work directory')
    if mac:
        normal = packages / 'Modern VLC.app'
        payload = review / 'Modern VLC.app'
        plugin_relative = Path('Contents/Frameworks/plugins/gui/libqt_plugin.dylib')
        executable_relative = Path('Contents/MacOS/vlc')
    else:
        candidates = sorted(packages.glob('Modern-VLC-Fork-*-linux-*'))
        candidates = [path for path in candidates if path.is_dir()]
        if len(candidates) != 1:
            raise RuntimeError('Expected exactly one normal Linux payload')
        normal = candidates[0]
        payload = review / normal.name
        plugin_relative = Path('lib/vlc/plugins/gui/libqt_plugin.so')
        executable_relative = Path('modern-vlc')
    if mac:
        # Preserve Apple's extended signatures on compiled Lua code/data,
        # framework metadata and symlinks in the separately owned review app.
        package.run('ditto', '--rsrc', '--extattr', normal, payload)
    else:
        shutil.copytree(normal, payload, symlinks=True)
    packaged_plugin = payload / plugin_relative
    previous_dependencies = package.dependencies(packaged_plugin) if mac else []
    try:
        flags = ['PLAYER_MPV_CPPFLAGS=-DVLC_MPV_RUNTIME_IDENTITY',
                 'PLAYER_DIAGNOSTICS_CPPFLAGS=-DVLC_PLAYER_DIAGNOSTICS']
        # The existing generator uses this configured Qt SDK and selected flags.
        # Do not touch the widely included header and rebuild the whole frontend.
        subprocess.run(['make', '-j1', '-f', 'Makefile', '-f',
            str(ROOT / 'tools/windows-player/qt-objects.mk'),
            *flags, 'qt-regenerate-player-moc'], cwd=qt, check=True)
        forced = [argument for source in REVIEW_SOURCES
                  for argument in ('-W', str(ROOT / 'modules/gui/qt' / source))]
        forced.extend(('-W', str(qt / REVIEW_MOC)))
        subprocess.run(['make', '-j1', *forced, 'libqt_plugin.la', *flags], cwd=qt, check=True)
        source_plugin = qt / '.libs' / packaged_plugin.name
        packaged_plugin.chmod(packaged_plugin.stat().st_mode | 0o200)
        shutil.copy2(source_plugin, packaged_plugin)
        if mac:
            for dependency in package.dependencies(packaged_plugin):
                if package.external(dependency):
                    continue
                matches = [old for old in previous_dependencies
                           if Path(old).name == Path(dependency).name]
                if len(matches) != 1:
                    raise RuntimeError('Diagnostic plugin changed native dependency: ' + dependency)
                package.run('install_name_tool', '-change', dependency, matches[0], packaged_plugin)
            package.run('codesign', '--force', '--sign', '-', packaged_plugin)
            package.refresh_mac_plugin_cache(payload, review / 'cachegen-home')
            package.run('codesign', '--force', '--sign', '-', payload)
            package.run('codesign', '--verify', '--deep', '--strict', payload)
        else:
            relative = os.path.relpath(payload / 'lib', packaged_plugin.parent)
            package.run('patchelf', '--set-rpath', '$ORIGIN/' + relative + ':$ORIGIN/' + relative + '/native',
                        packaged_plugin)
    finally:
        for row in rows:
            path = qt / row['path']
            if path.exists():
                path.chmod(path.stat().st_mode | 0o200)
            shutil.copy2(recovery / row['path'], path)
            if digest(path) != row['sha256'] or path.stat().st_mtime_ns != row['mtime_ns']:
                raise RuntimeError('Normal Qt recovery failed: ' + row['path'])
        (review / 'normal-restored.json').write_text(json.dumps({'state': 'verified', 'members': rows}, indent=2) + '\n')
    (review / 'review-player.json').write_text(json.dumps({
        'source_commit': package.output('git', '-C', ROOT, 'rev-parse', 'HEAD'),
        'executable': str(payload / executable_relative), 'diagnostic_plugin_sha256': digest(packaged_plugin),
        'normal_plugin_sha256': digest(normal / plugin_relative),
        'normal_payload_unmodified': True}, indent=2) + '\n')
    subprocess.run(['python3', ROOT / 'tools/desktop-player/verify-native-player.py',
                    '--executable', payload / executable_relative, '--scratch', review / 'acceptance'], check=True)


if __name__ == '__main__':
    main()
