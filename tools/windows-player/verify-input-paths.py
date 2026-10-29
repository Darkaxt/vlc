"""R61 native Qt local audio/playlist, HTTP playlist/live and missing-input paths.

All media are synthetic, all HTTP bindings are loopback, and every native
process owns an inactive desktop. Completion uses real process/core events.
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

sys.dont_write_bytecode = True
from isolated_desktop import IsolatedProcess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime', type=Path, required=True)
    parser.add_argument('--scratch', type=Path, required=True)
    parser.add_argument('--fixtures', type=Path, required=True)
    parser.add_argument('--transport', type=Path, required=True)
    parser.add_argument('--image-fixture', type=Path)
    args = parser.parse_args()
    source, scratch = args.runtime.resolve(), args.scratch.resolve()
    assert scratch.drive.upper() == 'D:' and scratch.parent.name.startswith('vlc-s7-') and not scratch.exists()
    assert args.fixtures.is_dir() and args.transport.is_file()
    plugin = source / 'plugins/gui/libqt_plugin.dll'
    assert b'VLC_PLAYER_DIAGNOSTICS_DIR' in plugin.read_bytes()
    scratch.mkdir()
    runtime = scratch / 'runtime'
    shutil.copytree(source, runtime, ignore=lambda directory, names: ['sdk'] if Path(directory).resolve() == source else [])
    portable = runtime / 'portable'
    portable.mkdir(exist_ok=True)
    assert not any(portable.iterdir())
    (scratch / 'tmp').mkdir()
    (scratch / 'qml').mkdir()
    environment = {key: value for key, value in os.environ.items() if not key.startswith('VLC_PLAYER_DIAGNOSTICS')}
    environment.pop('VLC_PLUGIN_PATH', None)
    environment.update(TEMP=str(scratch / 'tmp'), TMP=str(scratch / 'tmp'), VLC_DATA_PATH=str(runtime),
        QML_DISK_CACHE_PATH=str(scratch / 'qml'), QT_DISABLE_SHADER_DISK_CACHE='1',
        QSG_RHI_DISABLE_SHADER_DISK_CACHE='1', QT_FORCE_STDERR_LOGGING='1',
        QT_SCREEN_SCALE_FACTORS='1;1;1;1;1;1;1;1', QT_SCALE_FACTOR='1')
    result = {'schema': 'vlc_redesign.s7_input_paths.v1', 'cases': [],
        'qt_plugin_sha256': hashlib.sha256(plugin.read_bytes()).hexdigest(),
        'scope': 'Actual native Qt/VLC, muted MMDevice/WASAPI; synthetic fixtures and loopback HTTP; no OS input or physical-output claim.'}
    server_error = (scratch / 'server.stderr').open('wb')
    peer = subprocess.Popen([sys.executable, '-B', str(Path(__file__).with_name('serve-s7-fixtures.py')),
        '--fixtures', str(args.fixtures.resolve()), '--transport', str(args.transport.resolve()),
        '--evidence', str(scratch / 'http-result.json')], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=server_error, text=True, encoding='utf-8', creationflags=subprocess.CREATE_NO_WINDOW)
    try:
        ready = json.loads(peer.stdout.readline())
        assert ready['state'] == 'ready'
        base = ready['base_url']
        cases = [('audio', str((args.fixtures / 'audio.wav').resolve())),
            ('local-playlist', str((args.fixtures / 'local-playlist.m3u8').resolve())),
            ('http-playlist', base + '/playlist.m3u8'), ('nonseekable', base + '/live.ts'),
            ('missing', str(scratch / 'intentionally-missing.mp4'))]
        if args.image_fixture:
            assert args.image_fixture.is_file()
            cases.insert(2, ('embedded-image', str(args.image_fixture.resolve())))
        for name, media in cases:
            directory = scratch / name
            directory.mkdir()
            session = directory / 'session.json'
            token = uuid.uuid4().hex + uuid.uuid4().hex
            env = dict(environment, VLC_PLAYER_DIAGNOSTICS_DIR=str(directory),
                VLC_PLAYER_DIAGNOSTICS_TOKEN=token, VLC_PLAYER_DIAGNOSTICS_BUILD=result['qt_plugin_sha256'])
            command = [str(runtime / 'vlc.exe'), '--intf=qt', '--no-one-instance', '--no-media-library',
                '--no-plugins-cache', '--no-qt-privacy-ask', '--no-qt-updates-notif', '--no-metadata-network-access',
                '--no-save-recentplay', '--restore-playback-pos=0', '--no-qt-video-autoresize',
                '--no-video-title-show', '--no-volume-save', '--mmdevice-volume=0',
                '--aout=mmdevice', '--mmdevice-backend=wasapi', '--verbose=2', '--file-logging', '--log-verbose=2',
                '--logfile=' + str(directory / 'native.log')]
            if name != 'nonseekable':
                command.append('--play-and-exit')
            if name == 'embedded-image':
                command.append('--start-paused')
            command.append(media)

            def inspect(label, operation, *options):
                completed = subprocess.run([sys.executable, '-B', str(Path(__file__).with_name('inspect-player.py')),
                    '--session', str(session), operation, *options], capture_output=True,
                    text=True, encoding='utf-8', creationflags=subprocess.CREATE_NO_WINDOW)
                (directory / (label + '.client.log')).write_text(completed.stdout + completed.stderr, encoding='utf-8')
                assert completed.returncode == 0, (label, completed.stdout, completed.stderr)
                assert '"before": false, "after": false' in completed.stdout
                response = Path(re.search(r'^Response: (.+)$', completed.stdout, re.M).group(1).strip())
                snapshot = json.loads(response.read_text(encoding='utf-8'))
                assert not snapshot.get('qml_errors'), snapshot.get('qml_errors')
                return snapshot

            entry = {'case': name, 'input': media}
            result['cases'].append(entry)
            with (directory / 'stdout').open('wb') as out, (directory / 'stderr').open('wb') as err:
                player = IsolatedProcess(command, cwd=runtime, env=env, stdout=out, stderr=err)
                session.write_text(json.dumps({'pid': player.pid, 'executable': str(runtime / 'vlc.exe'), 'token': token}))
                natural_wait = name != 'embedded-image'
                try:
                    if name == 'nonseekable':
                        snapshot = inspect('advancing-live-clock', 'snapshot', '--await-core', 'time_seconds',
                            '--await-comparison', 'at_least', '--await-value', '1', '--capture')
                        entry['core'] = snapshot['core']
                        assert snapshot['core']['state'] == 2 and not snapshot['core']['seekable']
                        assert snapshot['core']['url'] == media
                        inspect('pause-live', 'click', '--target', 'playButton', '--await-core', 'state', '--await-value', '3')
                        inspect('resume-live', 'click', '--target', 'playButton', '--await-core', 'state', '--await-value', '2')
                        inspect('clock-after-live-resume', 'snapshot', '--await-core', 'time_seconds',
                            '--await-comparison', 'at_least', '--await-value', '2')
                    elif name == 'embedded-image':
                        inspect('paused-image-input', 'snapshot', '--await-core', 'state', '--await-value', '3')
                        image = inspect('image-subtitle-popup', 'click', '--target', 'subtitleButton', '--capture')
                        assert len(image['core']['subtitle_tracks']) == 1
                        assert image['core']['subtitle_tracks'][0]['selected']
                        tools = image['media_tools']['redesignMediaTools']
                        assert not tools['cues'] and 'image' in tools['timelineStatus'].lower(), tools
                        entry['image_track_and_unavailable_text_timeline'] = {
                            'tracks': image['core']['subtitle_tracks'], 'status': tools['timelineStatus'], 'cues': tools['cues']}
                        inspect('dismiss-image-popup', 'key', '--key', '0x1000000')
                        inspect('play-image-input', 'click', '--target', 'playButton', '--await-core', 'state', '--await-value', '2')
                        natural_wait = True
                finally:
                    try:
                        if name == 'nonseekable' or not natural_wait:
                            inspect('quit-live', 'quit')
                    finally:
                        entry['exit_code'] = player.wait()
                        entry['input_desktop_preserved'] = True
            log = (directory / 'native.log').read_text(encoding='utf-8', errors='replace')
            stderr = (directory / 'stderr').read_text(encoding='utf-8', errors='replace')
            assert entry['exit_code'] == 0
            assert 'QApp exec() finished' in log
            assert not re.search(r'TypeError:|ReferenceError:|Binding loop detected|failed to load component|cannot load plug-in', log + stderr)
            entry['qt_event_loop_finished'] = True
            if name == 'missing':
                assert re.search(r'cannot open file|unable to open|cannot access', log, re.I), log[-4000:]
                entry['expected_missing_input_error'] = True
            else:
                assert 'using aout stream module "wasapi"' in log
                entry['wasapi_selected'] = True
                if name != 'nonseekable':
                    assert 'EOF reached' in log
                    entry['natural_eof'] = True
                if name.endswith('playlist'):
                    released = re.findall(r"destroying input for '([^']+)'", log)
                    if name == 'http-playlist':
                        # Embedded MP4 metadata replaces EXTINF names during
                        # playback. Bind both requested URLs and started inputs,
                        # then require both real video EOF/release sequences.
                        assert all("Creating an input for playback'" + title + "'" in log
                            for title in ('S7 first clip', 'S7 second clip'))
                        assert log.count('Received first picture') == 2 and log.count('EOF reached') >= 2
                        assert len([label for label in released if label != 'playlist.m3u8']) == 2
                    else:
                        assert all(any(filename in label for label in released) for filename in ('clip-a.mp4', 'clip-b.mp4'))
                    entry['both_playlist_entries_played_and_released'] = True
            entry['passed'] = True
            print(json.dumps(entry), flush=True)
        result['passed'] = True
    except Exception as error:
        result.update(passed=False, failure=repr(error))
        raise
    finally:
        if peer.poll() is None:
            peer.stdin.write('stop\n'); peer.stdin.flush()
        result['http_server_exit'] = peer.wait()
        result['http_events'] = [line.strip() for line in peer.stdout]
        server_error.close()
        if (scratch / 'http-result.json').exists():
            result['http'] = json.loads((scratch / 'http-result.json').read_text())
        result['passed'] = result.get('passed', False) and result['http_server_exit'] == 0
        (scratch / 'result.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
        print(json.dumps(result, indent=2), flush=True)
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
