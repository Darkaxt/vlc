"""R65 whole-workflow native verification using the existing Qt event bridge.

Fresh portable copies, real publisher HTTPS, controlled cancel/retry peers and
the actual skins2 font consumer. No desktop input, activation or switching.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import uuid
import zipfile

sys.dont_write_bytecode = True
from isolated_desktop import IsolatedProcess

FONT_HASH = '3da2532e334eb31eabcf476e826b33b5f19ecde9dd110b3fd8699585c89d2b76'
ARCHIVE_HASH = 'fc25f631167471a1e33f57264a8eba1f3b27bffbdcdb0487bc6e0fbc584d6672'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime', type=Path, required=True)
    parser.add_argument('--scratch', type=Path, required=True)
    parser.add_argument('--fixture', type=Path, required=True)
    parser.add_argument('--skin-fixture', type=Path, required=True)
    parser.add_argument('--mode', choices=['download', 'fallback', 'cancel', 'retry', 'cached', 'corrupt'], required=True)
    parser.add_argument('--font-archive', type=Path)
    parser.add_argument('--theme', choices=['light', 'dark'], default='light')
    parser.add_argument('--scale', choices=['1', '1.5', '2'], default='1')
    parser.add_argument('--skip-skin', action='store_true')
    args = parser.parse_args()
    source, scratch = args.runtime.resolve(), args.scratch.resolve()
    assert scratch.drive.upper() == 'D:' and scratch.parent.name.startswith('vlc-s7-') and not scratch.exists()
    assert args.fixture.is_file() and args.skin_fixture.is_file()
    plugin = source / 'plugins/gui/libqt_plugin.dll'
    assert b'VLC_PLAYER_DIAGNOSTICS_DIR' in plugin.read_bytes()
    scratch.mkdir()
    runtime, evidence = scratch / 'runtime', scratch / 'evidence'
    shutil.copytree(source, runtime, ignore=lambda directory, names: ['sdk'] if Path(directory).resolve() == source else [])
    portable = runtime / 'portable'
    portable.mkdir(exist_ok=True)
    assert not any(portable.iterdir()), 'Preserve existing source-runtime preferences'
    qt_settings = portable / 'vlc/vlc-qt-interface.ini'
    qt_settings.parent.mkdir()
    qt_settings.write_text('[MainWindow]\ncolor-scheme-index=' + ('1' if args.theme == 'light' else '2') + '\n')
    expected_font = portable / 'redesign/fonts/Delicious_R_2021.otf'
    original_corrupt = b'R65 test-owned unrecognized font; preserve these bytes.'
    if args.mode in ('cached', 'corrupt'):
        expected_font.parent.mkdir(parents=True)
        if args.mode == 'cached':
            assert args.font_archive and hashlib.sha256(args.font_archive.read_bytes()).hexdigest() == ARCHIVE_HASH
            with zipfile.ZipFile(args.font_archive) as archive:
                blob = archive.read('DELICIOUS_21_OTF/Delicious_R_2021.otf')
            assert hashlib.sha256(blob).hexdigest() == FONT_HASH
            expected_font.write_bytes(blob)
        else:
            expected_font.write_bytes(original_corrupt)
    evidence.mkdir()
    (scratch / 'tmp').mkdir()
    (scratch / 'qml').mkdir()
    env = {k: v for k, v in os.environ.items() if not k.startswith('VLC_PLAYER_DIAGNOSTICS')}
    env.pop('VLC_PLUGIN_PATH', None)
    env.pop('QT_SCREEN_SCALE_FACTORS', None)
    env.update(TEMP=str(scratch / 'tmp'), TMP=str(scratch / 'tmp'), VLC_DATA_PATH=str(runtime),
        QML_DISK_CACHE_PATH=str(scratch / 'qml'), QT_DISABLE_SHADER_DISK_CACHE='1',
        QSG_RHI_DISABLE_SHADER_DISK_CACHE='1', QT_FORCE_STDERR_LOGGING='1',
        QT_ENABLE_HIGHDPI_SCALING='0', QT_FONT_DPI='96', QT_SCALE_FACTOR=args.scale)
    records = {'schema': 'vlc_redesign.first_run_font_workflow.v1', 'mode': args.mode,
        'theme': args.theme, 'scale': args.scale, 'steps': [],
        'qt_plugin_sha256': hashlib.sha256(plugin.read_bytes()).hexdigest()}
    peer, peer_error = None, None

    def start_peer():
        nonlocal peer, peer_error
        if args.mode not in ('cancel', 'retry', 'cached'):
            return
        peer_error = (evidence / 'peer.stderr').open('wb')
        script = Path(__file__).with_name('font-retry-peer.py' if args.mode == 'retry' else 'pending-connect-peer.py')
        command = [sys.executable, '-B', str(script)]
        if args.mode != 'retry':
            command += ['--directory', str(scratch / 'peer'), '--origin', 'www.exljbris.com:443']
        peer = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=peer_error,
            text=True, encoding='utf-8', creationflags=subprocess.CREATE_NO_WINDOW)
        first = peer.stdout.readline()
        records['peer_events'] = [first.strip()]
        ready = json.loads((scratch / 'peer/peer.json').read_text()) if args.mode != 'retry' else json.loads(first)
        env['VLC_PLAYER_DIAGNOSTICS_PROXY_PORT'] = str(ready['port'])
    current_session = None

    def inspect(label, operation, *options):
        completed = subprocess.run([sys.executable, '-B', str(Path(__file__).with_name('inspect-player.py')),
            '--session', str(current_session), operation, *map(str, options)], capture_output=True,
            text=True, encoding='utf-8', creationflags=subprocess.CREATE_NO_WINDOW)
        (current_session.parent / (label + '.client.log')).write_text(completed.stdout + completed.stderr, encoding='utf-8')
        assert completed.returncode == 0, (label, completed.stdout, completed.stderr)
        output = Path(re.search(r'^Response: (.+)$', completed.stdout, re.M).group(1).strip())
        snapshot = json.loads(output.read_text(encoding='utf-8'))
        assert not snapshot.get('qml_errors'), snapshot.get('qml_errors')
        assert '"before": false, "after": false' in completed.stdout
        records['steps'].append({'name': label, 'response': str(output.relative_to(scratch)),
            'font': snapshot.get('optional_legacy_font'), 'customization': snapshot.get('customization')})
        return snapshot

    def qt_run(name, setup):
        nonlocal current_session
        directory = evidence / name
        directory.mkdir()
        current_session = directory / 'session.json'
        token = uuid.uuid4().hex + uuid.uuid4().hex
        environment = dict(env, VLC_PLAYER_DIAGNOSTICS_DIR=str(directory), VLC_PLAYER_DIAGNOSTICS_TOKEN=token,
            VLC_PLAYER_DIAGNOSTICS_BUILD=records['qt_plugin_sha256'])
        command = [str(runtime / 'vlc.exe'), '--intf=qt', '--no-one-instance', '--no-media-library',
            '--no-plugins-cache', '--no-qt-updates-notif', '--no-metadata-network-access',
            '--restore-playback-pos=0', '--no-save-recentplay', '--no-qt-video-autoresize',
            '--no-video-title-show', '--aout=mmdevice', '--mmdevice-backend=wasapi',
            '--no-volume-save', '--mmdevice-volume=0', '--start-paused', '--file-logging',
            '--log-verbose=2', '--logfile=' + str(directory / 'native-ui.log')]
        if setup:
            command += ['--qt-privacy-ask']
        command.append(str(args.fixture.resolve()))
        with (directory / 'stdout').open('wb') as out, (directory / 'stderr').open('wb') as err:
            player = IsolatedProcess(command, cwd=runtime, env=environment, stdout=out, stderr=err)
            current_session.write_text(json.dumps({'pid': player.pid, 'executable': str(runtime / 'vlc.exe'), 'token': token}))
            try:
                snapshot = inspect('initial', 'snapshot', '--capture')
                reference = inspect('reference-viewport', 'resize', '--width', round(1920 / float(args.scale)),
                    '--height', round(1080 / float(args.scale)), '--capture')
                assert reference['presentation']['theme'] == (1 if args.theme == 'light' else 2), reference['presentation']
                assert abs(reference['window']['dpr'] - float(args.scale)) < 0.001, reference['window']
                top = [node for node in reference['tree'] if node['id'] == 'playerTopBar']
                assert len(top) == 1 and top[0]['height'] == 40, top
                records['observed_theme'] = reference['presentation']['theme']
                records['observed_dpr'] = reference['window']['dpr']
                location = Path(snapshot['optional_legacy_font']['location']).resolve()
                assert location == expected_font.resolve(), ('Wrong profile isolation', location)
                if not setup:
                    assert snapshot['optional_legacy_font']['available']
                    assert not snapshot['customization']['onboardingVisible']
                    inspect('reopen-menu', 'click', '--target', 'topBarMenuButton')
                    inspect('reopen-setup', 'widget_click', '--menu-action', 'Welcome / Appearance Setup…')
                    for page in range(3):
                        inspect('reopen-next-' + str(page), 'click', '--target', 'onboardingNext')
                    cached = inspect('reopened-cache', 'snapshot', '--capture')
                    assert cached['optional_legacy_font']['available'] and not cached['optional_legacy_font']['busy']
                    assert 'No download is needed' in cached['optional_legacy_font']['status']
                    finished = inspect('finish-reopened', 'click', '--target', 'onboardingNext')
                    assert not finished['customization']['onboardingVisible']
                    return
                for page in range(3):
                    inspect('next-' + str(page), 'click', '--target', 'onboardingNext')
                inspect('font-page', 'snapshot', '--capture')
                if args.mode in ('fallback', 'corrupt'):
                    if args.mode == 'corrupt':
                        failed = inspect('preserve-corrupt', 'click', '--target', 'onboardingNext')
                        assert not failed['optional_legacy_font']['busy'] and not failed['optional_legacy_font']['available']
                        assert expected_font.read_bytes() == original_corrupt
                    inspect('fallback-focus', 'focus', '--target', 'onboardingFontFallback')
                    inspect('use-fallback', 'click', '--target', 'onboardingFontFallback')
                elif args.mode in ('cancel', 'retry'):
                    inspect('begin-download', 'click', '--target', 'onboardingNext',
                        '--await-target', 'onboardingFontStatus', '--await-property', 'busy', '--await-value', 'true')
                    event = peer.stdout.readline()
                    records['peer_events'].append(event.strip())
                    observed = json.loads(event)
                    if args.mode == 'cancel':
                        assert observed['state'] == 'tls_pending'
                        inspect('cancel-focus', 'focus', '--target', 'onboardingFontCancel')
                        inspect('cancel-download', 'click', '--target', 'onboardingFontCancel',
                            '--await-target', 'onboardingFontStatus', '--await-property', 'busy', '--await-value', 'false')
                        assert peer.wait() == 0
                        assert not expected_font.exists()
                        inspect('fallback-focus', 'focus', '--target', 'onboardingFontFallback')
                        inspect('finish-after-cancel', 'click', '--target', 'onboardingFontFallback')
                    else:
                        assert observed['state'] == 'first_request_pending'
                        peer.stdin.write('fail\n'); peer.stdin.flush()
                        failure = inspect('observed-network-failure', 'snapshot', '--await-target', 'onboardingFontStatus',
                            '--await-property', 'busy', '--await-value', 'false', '--capture')
                        assert 'failed' in failure['optional_legacy_font']['status'].lower()
                        assert not expected_font.exists()
                        downloaded = inspect('explicit-retry-completed', 'click', '--target', 'onboardingNext',
                            '--await-target', 'onboardingFontStatus', '--await-property', 'busy', '--await-value', 'false')
                        assert downloaded['optional_legacy_font']['available'], downloaded['optional_legacy_font']
                else:
                    downloaded = inspect('download-or-use-cache', 'click', '--target', 'onboardingNext',
                        '--await-target', 'onboardingFontStatus', '--await-property', 'busy', '--await-value', 'false')
                    assert downloaded['optional_legacy_font']['available'], downloaded['optional_legacy_font']
                # With the folder blank, completion is synchronous in MainCtx.
                # Observe the next actual frame and state; the closed Loader
                # has destroyed its old Next item, so it cannot be awaited.
                final = inspect('finished', 'snapshot', '--capture')
                assert not final['customization']['onboardingVisible']
                wanted = args.mode in ('download', 'retry', 'cached')
                assert final['optional_legacy_font']['available'] == wanted
                if wanted:
                    assert hashlib.sha256(expected_font.read_bytes()).hexdigest() == FONT_HASH
                elif args.mode == 'corrupt':
                    assert expected_font.read_bytes() == original_corrupt
                else:
                    assert not expected_font.exists()
            finally:
                try:
                    inspect('quit', 'quit')
                finally:
                    code = player.wait()
                    records[name + '_exit'] = code
                    records[name + '_input_desktop_preserved'] = True
                    assert code == 0, code

    try:
        start_peer()
        qt_run('first-run', True)
        if args.mode in ('download', 'retry', 'cached'):
            if args.mode != 'cached':
                env.pop('VLC_PLAYER_DIAGNOSTICS_PROXY_PORT', None)
            qt_run('restart', False)
        if not args.skip_skin:
            directory = evidence / 'native-skin'
            directory.mkdir()
            command = [str(runtime / 'vlc.exe'), '--intf=skins2', '--no-one-instance', '--no-media-library',
                '--no-metadata-network-access', '--no-volume-save', '--mmdevice-volume=0', '--play-and-exit',
                '--file-logging', '--log-verbose=2', '--logfile=' + str(directory / 'native.log'), str(args.skin_fixture.resolve())]
            with (directory / 'stdout').open('wb') as out, (directory / 'stderr').open('wb') as err:
                player = IsolatedProcess(command, cwd=runtime, env=env, stdout=out, stderr=err)
                code = player.wait()
                records['native_skin_input_desktop_preserved'] = True
            log = (directory / 'native.log').read_text(encoding='utf-8', errors='replace')
            wanted = 'using the verified user-profile Delicious font' if args.mode in ('download', 'retry', 'cached') else 'using bundled FreeSans for the optional legacy font'
            assert code == 0 and wanted in log and 'EOF reached' in log, (code, wanted)
            records['native_skin'] = {'exit_code': code, 'actual_font': wanted, 'natural_eof': True}
        if peer:
            if args.mode == 'cached':
                peer.stdin.write('stop\n'); peer.stdin.flush()
                assert peer.wait() == 1
                assert not (scratch / 'peer/handshake.json').exists()
                cached_network = json.loads((scratch / 'peer/result.json').read_text())
                assert cached_network['state'] == 'owner_cancelled' and cached_network['accepted_connections'] == 0
                assert cached_network['forwarded_connections'] == 0
                records['cached_restart_reopen_no_download'] = True
            else:
                assert peer.wait() == 0
            records['peer_events'] += [line.strip() for line in peer.stdout]
        records['passed'] = True
    except Exception as error:
        records.update(passed=False, failure=repr(error))
        raise
    finally:
        if peer:
            if peer.poll() is None:
                peer.stdin.write('stop\n'); peer.stdin.flush()
                records['peer_stop_exit'] = peer.wait()
            peer_error.close()
        (scratch / 'result.json').write_text(json.dumps(records, indent=2) + '\n', encoding='utf-8')
        print(json.dumps(records, indent=2), flush=True)


if __name__ == '__main__':
    main()
