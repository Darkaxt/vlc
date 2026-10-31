"""Real HTTP handover held at incoming I/O, with a native queue change.

The existing loopback server holds libmpv's request on an owner event. Ordinary
Qt input changes the queue during that real transition; no playback engine is
mocked, no artificial timing window or desktop input is used.
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
from urllib.parse import unquote

sys.dont_write_bytecode = True
from isolated_desktop import IsolatedProcess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime', required=True, type=Path)
    parser.add_argument('--scratch', required=True, type=Path)
    parser.add_argument('--fixtures', required=True, type=Path)
    args = parser.parse_args()
    source, scratch = args.runtime.resolve(), args.scratch.resolve()
    tools = Path(__file__).resolve().parent
    assert scratch.drive.upper() == 'D:' and scratch.parent.name.startswith('vlc-s8-') and not scratch.exists()
    scratch.mkdir()
    runtime = scratch / 'runtime'
    shutil.copytree(source, runtime, ignore=lambda directory, names: ['sdk'] if Path(directory).resolve() == source else [])
    assert not any((runtime / 'portable').iterdir())
    for name in ('tmp', 'qml'):
        (scratch / name).mkdir()
    fixture = args.fixtures / 'Multi-track Ω 日本語.mp4'
    replacement = (args.fixtures / 'clip-b.mp4').resolve().as_uri()
    result = {'schema': 'vlc_redesign.s8_engine_transition.v1', 'passed': False,
        'qt_plugin_sha256': hashlib.sha256((runtime / 'plugins/gui/libqt_plugin.dll').read_bytes()).hexdigest()}
    assert b'VLC_PLAYER_DIAGNOSTICS_DIR' in (runtime / 'plugins/gui/libqt_plugin.dll').read_bytes()
    server_error = (scratch / 'server.stderr').open('wb')
    server = subprocess.Popen([sys.executable, '-B', str(tools / 'serve-s7-fixtures.py'),
        '--fixtures', str(args.fixtures.resolve()), '--transport', str((args.fixtures / 'stream.ts').resolve()),
        '--handover-fixture', str(fixture.resolve()), '--evidence', str(scratch / 'http-result.json')],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=server_error, text=True,
        encoding='utf-8', creationflags=subprocess.CREATE_NO_WINDOW)
    try:
        ready = json.loads(server.stdout.readline())
        assert ready['state'] == 'ready'
        remote = ready['base_url'] + '/handover.mp4'
        session = scratch / 'session.json'
        token = uuid.uuid4().hex + uuid.uuid4().hex
        environment = {key: value for key, value in os.environ.items() if not key.startswith('VLC_PLAYER_DIAGNOSTICS')}
        environment.pop('VLC_PLUGIN_PATH', None)
        environment.update(TEMP=str(scratch / 'tmp'), TMP=str(scratch / 'tmp'), VLC_DATA_PATH=str(runtime),
            QML_DISK_CACHE_PATH=str(scratch / 'qml'), QT_DISABLE_SHADER_DISK_CACHE='1', QSG_RHI_DISABLE_SHADER_DISK_CACHE='1',
            QT_FORCE_STDERR_LOGGING='1', VLC_PLAYER_DIAGNOSTICS_DIR=str(scratch),
            VLC_PLAYER_DIAGNOSTICS_TOKEN=token, VLC_PLAYER_DIAGNOSTICS_BUILD=result['qt_plugin_sha256'])
        command = [str(runtime / 'vlc.exe'), '--intf=qt', '--no-one-instance', '--no-media-library',
            '--qt-playback-engine=vlc', '--no-plugins-cache', '--no-qt-privacy-ask', '--no-qt-updates-notif',
            '--no-metadata-network-access', '--no-save-recentplay', '--restore-playback-pos=0', '--start-paused',
            '--no-qt-video-autoresize', '--no-video-title-show', '--no-volume-save', '--mmdevice-volume=0',
            '--aout=mmdevice', '--mmdevice-backend=wasapi', '--file-logging', '--log-verbose=2',
            '--logfile=' + str(scratch / 'native.log'), remote]

        def inspect(label, operation, *options):
            completed = subprocess.run([sys.executable, '-B', str(tools / 'inspect-player.py'),
                '--session', str(session), operation, *map(str, options)], capture_output=True,
                text=True, encoding='utf-8', creationflags=subprocess.CREATE_NO_WINDOW)
            (scratch / (label + '.client.log')).write_text(completed.stdout + completed.stderr, encoding='utf-8')
            assert completed.returncode == 0, (label, completed.stdout, completed.stderr)
            assert '"before": false, "after": false' in completed.stdout
            response = Path(re.search(r'^Response: (.+)$', completed.stdout, re.M).group(1).strip())
            state = json.loads(response.read_text(encoding='utf-8'))
            assert not state.get('qml_errors'), state.get('qml_errors')
            return state

        with (scratch / 'stdout').open('wb') as out, (scratch / 'stderr').open('wb') as err:
            player = IsolatedProcess(command, cwd=runtime, env=environment, stdout=out, stderr=err)
            session.write_text(json.dumps({'pid': player.pid, 'executable': str(runtime / 'vlc.exe'), 'token': token}))
            handover_released = False
            try:
                inspect('paused-source', 'snapshot', '--await-core', 'state', '--await-value', '3')
                inspect('seek-source', 'click', '--target', 'progressSlider', '--fraction-x', '.35')
                inspect('play-source', 'click', '--target', 'playButton', '--await-core', 'state', '--await-value', '2')
                inspect('source-clock', 'snapshot', '--await-core', 'time_seconds', '--await-value', '42', '--await-comparison', 'at_least')
                original = inspect('pause-source', 'click', '--target', 'playButton', '--await-core', 'state', '--await-value', '3')
                inspect('engine-settings', 'click', '--target', 'toolsButton')
                switching = inspect('begin-handover', 'click', '--name', 'MPV / Dolby Vision',
                    '--await-core', 'engine_switching', '--await-value', 'true')
                held = json.loads(server.stdout.readline())
                assert held['state'] == 'handover_waiting' and held['user_agent'].startswith('libmpv')
                switching = inspect('real-pending-input', 'snapshot')
                assert switching['core']['engine'] == 'mpv' and switching['core']['engine_switching']
                assert switching['core']['native_vlc']['state'] == 0
                buttons = [node for node in switching['tree'] if node['visible'] and node.get('name') in ('VLC', 'MPV / Dolby Vision') and node.get('actions')]
                assert len(buttons) == 2 and all(not node['enabled'] for node in buttons), buttons
                assert any(node['visible'] and 'Switching engines' in node.get('text', '') for node in switching['tree'])
                result['repeated_engine_requests_disabled_during_real_transition'] = True
                inspect('dismiss-settings', 'key', '--key', '0x1000000')
                changed = inspect('change-current-queue-item', 'drop', '--target', 'playerView', '--url', replacement)
                server.stdin.write('release-handover\n'); server.stdin.flush()
                handover_released = True
                assert json.loads(server.stdout.readline())['state'] == 'handover_released'
                settled = inspect('cancelled-captured-restart', 'snapshot', '--await-core', 'engine_switching', '--await-value', 'false')
                assert unquote(settled['core']['native_vlc']['url']) == unquote(replacement), settled['core']
                stopped = inspect('superseded-input-stopped', 'snapshot', '--await-core', 'state', '--await-value', '0')
                inspect('home-menu', 'click', '--target', 'menuBtn')
                inspect('playback-menu', 'widget_click', '--menu-action', 'Playback')
                inspect('play-current-selection', 'widget_click', '--menu-action', 'Play')
                loaded = inspect('replacement-loaded', 'snapshot', '--await-core', 'url', '--await-value', json.dumps(replacement))
                if loaded['core']['state'] == 3:
                    inspect('play-replacement', 'click', '--target', 'playButton', '--await-core', 'state', '--await-value', '2')
                else:
                    inspect('replacement-playing', 'snapshot', '--await-core', 'state', '--await-value', '2')
                actual = inspect('replacement-clock', 'snapshot', '--await-core', 'time_seconds', '--await-value', '1', '--await-comparison', 'at_least')
                assert actual['core']['time_seconds'] < 4 and actual['core']['native_vlc']['state'] == 0
                inspect('pause-replacement', 'click', '--target', 'playButton', '--await-core', 'state', '--await-value', '3')
                queue = inspect('actual-queue', 'click', '--target', 'playqueueToggle', '--capture')
                rows = [node for node in queue['tree'] if node['visible'] and 'isCurrent' in node and node.get('url')]
                assert [unquote(node['url']) for node in rows] == [remote, unquote(replacement)], rows
                assert [node['isCurrent'] for node in rows] == [False, True], rows
                result.update(passed=True, original_core=original['core'], pending_core=switching['core'],
                    changed_core=changed['core'], settled_core=settled['core'], stopped_core=stopped['core'],
                    replacement_core=actual['core'], queue_urls=[node['url'] for node in rows],
                    queue_current_identity_preserved=True, original_restart_cancelled=True)
            finally:
                if not handover_released:
                    # Release our fixture boundary before joining the native
                    # player, including when an assertion failed mid-transition.
                    server.stdin.write('release-handover\n'); server.stdin.flush()
                try:
                    inspect('quit', 'quit')
                finally:
                    result['exit_code'] = player.wait()
                    result['input_desktop_preserved'] = True
                    result['passed'] &= result['exit_code'] == 0
    except Exception as error:
        result.update(passed=False, failure=repr(error))
        raise
    finally:
        if server.poll() is None:
            server.stdin.write('stop\n'); server.stdin.flush()
        result['http_server_exit'] = server.wait()
        server_error.close()
        result['http_events'] = [line.strip() for line in server.stdout]
        result['passed'] &= result['http_server_exit'] == 0
        (scratch / 'result.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
        print(json.dumps({key: result.get(key) for key in ('passed', 'failure', 'exit_code', 'http_server_exit', 'queue_current_identity_preserved')}) , flush=True)
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
