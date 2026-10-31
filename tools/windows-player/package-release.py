"""Create this fork's versioned normal portable release, without publication.

Run after the integrated gates and normal build. The fresh destination is an
intentional deliverable on D:, and every shipped file receives a byte identity.
Independent native verification and release readback remain separate gates.
"""
import argparse
import ctypes
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import zipfile


def sha256(path):
    with path.open('rb') as source:
        return hashlib.file_digest(source, 'sha256').hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime', type=Path, required=True)
    parser.add_argument('--dependency-notices', type=Path, required=True)
    parser.add_argument('--destination', type=Path, required=True)
    parser.add_argument('--source-commit', required=True)
    parser.add_argument('--version', required=True)
    parser.add_argument('--include-mpv', action='store_true')
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[2]
    runtime, destination = args.runtime.resolve(), args.destination.resolve()
    assert re.fullmatch(r'[0-9a-f]{40}', args.source_commit)
    assert re.fullmatch(r'\d+\.\d+\.\d+', args.version)
    assert destination.drive.upper() == 'D:' and destination.is_relative_to(Path('D:/VLC-Redesign'))
    assert not destination.exists() and args.dependency_notices.is_dir()
    assert (args.dependency_notices / 'manifest.json').is_file()
    dependency_inventory = json.loads((args.dependency_notices / 'manifest.json').read_text())
    assert len(dependency_inventory.get('embedded_carriers_reviewed', [])) == 4
    assert subprocess.check_output(['git', '-C', str(repo), 'rev-parse', 'HEAD'], text=True).strip() == args.source_commit
    changes = subprocess.check_output(['git', '-C', str(repo), 'diff', '--name-only', 'HEAD'], text=True).splitlines()
    assert not any(path.startswith(('modules/', 'src/', 'share/', 'contrib/', 'tools/')) for path in changes), changes
    untracked = subprocess.check_output(['git', '-C', str(repo), 'ls-files', '--others', '--exclude-standard',
        '--', 'modules', 'src', 'share', 'contrib', 'tools'], text=True).splitlines()
    assert not untracked, 'Required source/tool files are outside the recorded commit: ' + repr(untracked)
    assert not (runtime / 'portable').exists() or not any((runtime / 'portable').iterdir())
    plugin = runtime / 'plugins/gui/libqt_plugin.dll'
    normal = plugin.read_bytes()
    mpv = None
    if args.include_mpv:
        registry = json.loads(subprocess.check_output(['git', '-C', str(repo), 'show',
            args.source_commit + ':modules/gui/qt/player/mpv/source.json']))
        mpv = json.loads((runtime / 'MPV-BUILDINFO.json').read_text())
        assert mpv['schema'] == 'vlc_redesign.mpv_build.v1'
        assert [item['name'] for item in mpv['files']] == registry['runtime']['files']
        assert {item['archive']: item['sha256'] for item in dependency_inventory['mpv_sources']} == \
               {item['archive']: item['sha256'] for item in mpv['sources']}
        assert dependency_inventory['baseline_sdk_manifest_sha256'] == mpv['sdk_dependency_notices_manifest_sha256']
        assert mpv['build_script_sha256'] == sha256(repo / registry['runtime']['build_script'])
        assert mpv['install_helper_sha256'] == sha256(repo / 'tools/windows-player/install-ffmpeg-files.py')
        for item in mpv['files']:
            assert sha256(runtime / item['name']) == item['sha256']
            assert item['sha256'].encode('ascii') in normal, 'Player is not bound to its packaged MPV payload'
    else:
        assert not (runtime / 'libmpv-2.dll').exists(), 'Select --include-mpv for the S8 runtime'
    markers = ['VLC_PLAYER_DIAGNOSTICS_DIR', 'VLC_PLAYER_DIAGNOSTICS_TOKEN',
        'VLC_PLAYER_DIAGNOSTICS_OFFSCREEN', 'VLC_PLAYER_DIAGNOSTICS_PROXY_PORT',
        'redesignSeekRequests', 'offscreen_session_is_capture_only',
        'core_observation_listener_failed_action_not_undone', 'palette_highlight',
        'PlayerDiagnostics', 'optional_legacy_font', 'mpvHistoryReady', 'mpv_history_ready', 'mpv_video_ready']
    for marker in markers:
        assert all(marker.encode(encoding) not in normal for encoding in ('ascii', 'utf-16le')), marker
    core = (runtime / 'libvlccore.dll').read_bytes()
    for marker in ('S7_TRACE', 'S7_ARG', 'S7_INSERT', 'S7_PLAY', 'S7_SPAWN_FAIL'):
        assert marker.encode() not in core, 'Temporary startup trace in release core: ' + marker
    with os.add_dll_directory(str(runtime)):
        native = ctypes.CDLL(str(runtime / 'libvlc.dll'))
        identity = {}
        for name in ('version', 'compiler', 'changeset'):
            getter = getattr(native, 'libvlc_get_' + name)
            getter.restype = ctypes.c_char_p
            identity[name] = getter().decode('utf-8')
    revision_tokens = re.findall(r'[0-9a-f]{7,40}', identity['changeset'])
    assert any(args.source_commit.startswith(token) for token in revision_tokens), identity
    assert 'dirty' not in identity['changeset'].lower(), identity
    destination.mkdir(parents=True)
    name = 'Modern-VLC-Fork-' + args.version + '-win64-portable'
    package = destination / name
    package.mkdir()
    root_files = ['vlc.exe', 'vlc-cache-gen.exe', 'vlc-preparser.exe', 'libvlc.dll', 'libvlccore.dll',
        'vlc.ico', 'AUTHORS.txt', 'COPYING.txt', 'NEWS.txt', 'README.txt', 'THANKS.txt']
    if mpv:
        root_files += ['MPV-BUILDINFO.json', *[item['name'] for item in mpv['files']]]
    for filename in root_files:
        assert (runtime / filename).is_file(), filename
        shutil.copy2(runtime / filename, package / filename)
    for folder in ('plugins', 'lua', 'skins', 'hrtfs', 'locale'):
        assert (runtime / folder).is_dir(), folder
        # A machine/build-specific plugin cache is generated by the real native
        # verifier for its exact extracted directory, rather than copied stale.
        shutil.copytree(runtime / folder, package / folder, ignore=shutil.ignore_patterns('plugins.dat'))
    (package / 'portable').mkdir()
    assert (package / 'locale/el/LC_MESSAGES/vlc.mo').is_file(), 'Preserve the upstream language catalogs'
    notices = package / 'licenses'
    notices.mkdir()
    for source, target in [('COPYING', 'GPL-2.0.txt'), ('COPYING.LIB', 'LGPL-2.1.txt'),
            ('modules/gui/qt/fonts/redesign/LICENSE.txt', 'INTER-OFL-1.1.txt'),
            ('doc/redesign/resources/s7/FLUENT-ICONS-LICENSE.txt', 'FLUENT-ICONS-MIT.txt'),
            ('doc/redesign/resources/s7/THIRD-PARTY-NOTICES.md', 'THIRD-PARTY-NOTICES.md')]:
        blob = subprocess.check_output(['git', '-C', str(repo), 'show', args.source_commit + ':' + source])
        (notices / target).write_bytes(blob)
    shutil.copytree(args.dependency_notices, notices / 'dependencies')
    for version in ('GPL-3', 'LGPL-3'):
        source = args.dependency_notices / 'compiler-runtime/common-licenses' / version
        assert source.is_file()
        shutil.copy2(source, notices / (version + '.0.txt'))
    # The combined Qt 6 application is conveyed under GPLv3. Preserve VLC's
    # original GPLv2 text in licenses alongside the independently licensed parts.
    shutil.copy2(notices / 'GPL-3.0.txt', package / 'COPYING.txt')
    (package / 'README-MODERN-VLC.txt').write_text(
        'Modern VLC Fork ' + args.version + ' - Windows x64 portable\n\n'
        'Independent modified VLC 4 development build; not an official VideoLAN release.\n'
        'The combined application is distributed under GNU GPL version 3.\n'
        'Original component licenses and copyright notices remain in licenses/.\n'
        'Extract the whole folder and run vlc.exe. Keep the empty portable folder\n'
        'beside it: this release stores its settings there, independently of installed VLC.\n'
        'No installer, OS font installation or replacement of installed VLC is required.\n\n'
        'The redesigned interface includes Inter. First-run setup can download the\n'
        'optional original classic-skin font directly from its publisher; Use FreeSans\n'
        'keeps first launch usable offline. Downloaded font bytes are user profile data\n'
        'and are not included in this package or its corresponding-source archive.\n\n'
        'Source commit: ' + args.source_commit + '\n'
        'Source, build inputs, notices and recovery instructions accompany this release\n'
        'at https://github.com/Darkaxt/vlc/releases .\n', encoding='utf-8')
    if mpv:
        with (package / 'README-MODERN-VLC.txt').open('a', encoding='utf-8') as guide:
            guide.write('\nPlayback settings can switch the open item between VLC and MPV, with a\n'
                'brief interruption while the new engine restores its playback position.\n'
                'Preferences separately choose the startup engine; VLC is the default.\n'
                'MPV converts supported Dolby Vision video to BT.709/sRGB SDR. Native\n'
                'Dolby Vision display signaling and full Profile 7 FEL are not claimed.\n'
                'Keep both packaged MPV DLLs beside vlc.exe. MPV color conversion requires\n'
                'the Vulkan runtime supplied by a compatible graphics driver.\n')
    build = {'schema': 'vlc_redesign.release_identity.v1', 'product': 'Modern VLC Fork',
        'version': args.version, 'source_commit': args.source_commit,
        'upstream_revision': '392bc1d0abdb7396b6c97fef206efa1d23868e19',
        'source_repository': 'https://github.com/Darkaxt/vlc', 'native': identity,
        'qt': '6.8.3', 'qt_plugin_sha256': sha256(plugin),
        'dependency_notices_manifest_sha256': sha256(args.dependency_notices / 'manifest.json'),
        'normal_diagnostic_markers_absent': markers, 'profile': 'Empty portable directory beside vlc.exe',
        'signing': 'This helper performs no Authenticode signing step. Inspect delivered signatures independently; none is asserted here.'}
    if mpv:
        build['mpv'] = mpv
        build['mpv_manifest_sha256'] = sha256(runtime / 'MPV-BUILDINFO.json')
        with (package / 'README-MODERN-VLC.txt').open('a', encoding='utf-8') as stream:
            stream.write('\nPlayback settings offer VLC (default) and MPV. The live engine choice can reopen\n'
                         'the current item in the other engine, preserving position and play/pause state.\n'
                         'MPV converts supported Dolby Vision/HDR input to BT.709/sRGB SDR. Native Dolby\n'
                         'Vision signaling and full Profile 7 FEL reconstruction are not claimed.\n'
                         'Tools marked VLC remain available by switching back to VLC.\n')
    (package / 'BUILDINFO.json').write_text(json.dumps(build, indent=2) + '\n', encoding='utf-8')
    records = []
    for file in sorted(package.rglob('*')):
        assert not file.is_symlink(), file
        if file.is_file():
            assert file.suffix.lower() not in ('.otf', '.pyc'), file
            records.append({'path': file.relative_to(package).as_posix(), 'bytes': file.stat().st_size, 'sha256': sha256(file)})
    manifest = dict(build, files=records)
    (package / 'FILE-MANIFEST.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    archive = destination / (name + '.zip')
    with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as output:
        output.writestr(name + '/portable/', '')
        for file in sorted(package.rglob('*')):
            if file.is_file():
                info = zipfile.ZipInfo(name + '/' + file.relative_to(package).as_posix(), date_time=(2026, 10, 29, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                output.writestr(info, file.read_bytes())
    result = {'package': str(package), 'archive': str(archive), 'archive_sha256': sha256(archive),
        'archive_bytes': archive.stat().st_size, 'source_commit': args.source_commit, 'normal_marker_scan_passed': True,
        'delivery_verification': 'Pending independent extraction/native verification and published readback.'}
    (destination / 'package-result.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, indent=2), flush=True)


if __name__ == '__main__':
    main()
