#!/usr/bin/env python3
"""Exercise the actual instrumented native Qt player in a task-owned profile.

This is hosted-runner acceptance, not a host desktop controller. Native captures
remain separate from Quick-only snapshots; both require inspected evidence.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import subprocess
import uuid

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('native_client', HERE / 'native-player-client.py')
client_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(client_module)


def run(*args):
    subprocess.run(list(map(str, args)), check=True)


def prepare_fixture(root):
    subtitles = root / 'native.srt'
    subtitles.write_text('1\n00:00:01,000 --> 00:00:15,000\nNative subtitle one\n\n'
                         '2\n00:00:20,000 --> 00:09:59,000\nNative subtitle two\n')
    video = root / 'native.mkv'
    run('ffmpeg', '-hide_banner', '-loglevel', 'error', '-f', 'lavfi', '-i',
        'testsrc2=size=640x360:rate=1', '-f', 'lavfi', '-i', 'sine=frequency=600:sample_rate=48000',
        '-i', subtitles, '-t', '600', '-map', '0:v', '-map', '1:a', '-map', '2:s',
        '-c:v', 'libx264', '-preset', 'ultrafast', '-pix_fmt', 'yuv420p', '-threads', '1',
        '-c:a', 'aac', '-c:s', 'srt', '-metadata:s:s:0', 'language=eng', video)
    return video


def inspect_result(result):
    if result.get('qml_errors'):
        raise RuntimeError('Native QML errors: ' + json.dumps(result['qml_errors']))
    return result


def check_engine(executable, root, fixture, engine):
    case = root / engine
    case.mkdir()
    evidence = case / 'evidence'; evidence.mkdir()
    home = case / 'home'; home.mkdir()
    token = uuid.uuid4().hex + uuid.uuid4().hex
    env = os.environ.copy()
    env.update(HOME=str(home), XDG_CONFIG_HOME=str(home / 'config'),
        XDG_DATA_HOME=str(home / 'data'), XDG_CACHE_HOME=str(home / 'cache'),
        VLC_PLAYER_DIAGNOSTICS_DIR=str(evidence), VLC_PLAYER_DIAGNOSTICS_TOKEN=token,
        VLC_NATIVE_CI_CAPTURE='1', QT_FORCE_STDERR_LOGGING='1',
        QML_DISK_CACHE_PATH=str(case / 'qml-cache'))
    argv = [str(executable), '--intf=qt', '--language=en', '--no-one-instance',
        '--no-qt-privacy-ask', '--no-qt-updates-notif', '--no-metadata-network-access',
        '--restore-playback-pos=0', '--no-video-title-show', '--start-paused',
        '--qt-playback-engine=' + engine, '--verbose=2', str(fixture)]
    (evidence / 'launch.json').write_text(json.dumps({'argv': argv, 'platform': platform.platform(),
        'executable_sha256': hashlib.sha256(executable.read_bytes()).hexdigest()}, indent=2) + '\n')
    records = []

    def save(label, result):
        inspect_result(result)
        records.append({'label': label, 'response_id': result['id']})
        (evidence / 'workflow.json').write_text(json.dumps(records, indent=2) + '\n')
        return result

    with (evidence / 'stdout.log').open('wb') as stdout, (evidence / 'stderr.log').open('wb') as stderr:
        player = subprocess.Popen(argv, cwd=executable.parent, env=env, stdout=stdout, stderr=stderr)
        client = client_module.NativePlayerClient(player, evidence, token)
        try:
            save('view-mounted', client.await_property('viewLoader', 'status', 1))
            initial = save('paused', client.await_core('state', 3))
            if engine == 'mpv':
                initial = save('native-video-ready', client.await_core('mpv_video_ready', True))
            assert initial['core']['engine'] == engine, initial['core']
            assert initial['core']['video_tracks'] and initial['core']['audio_tracks'], initial['core']
            assert initial['core']['subtitle_tracks'], initial['core']
            save('seekable', client.await_core('seekable', True))
            save('main-picture', client.snapshot(capture=True, capture_native=True))
            save('subtitle-menu', client.action('click', target='subtitleButton'))
            choices = client.snapshot()
            tracks = [node for node in choices['tree'] if node['visible'] and node['enabled']
                      and node.get('role') == 45 and node.get('name') != 'None' and node.get('actions')]
            assert len(tracks) == 1, tracks
            save('select-subtitle', client.action('click', name=tracks[0]['name']))
            save('close-subtitle-menu', client.action('key', key=0x1000000))
            save('subtitle-position', client.action('click', target='progressSlider', fraction_x=0.01))
            save('subtitle-seek-committed', client.await_core('time_seconds', 6, tolerance=2))
            subtitle = save('subtitle-picture', client.snapshot(capture=True, capture_native=True))
            assert any(track.get('selected') for track in subtitle['core']['subtitle_tracks']), subtitle['core']
            save('seek', client.action('click', target='progressSlider', fraction_x=0.1))
            save('seek-committed', client.await_core('time_seconds', 60, tolerance=2))
            controls = client.snapshot()
            volume = next(node for node in controls['tree'] if node['id'] == 'volumeSlider' and node['visible'])
            requested = float(volume['to']) * 0.4
            save('volume', client.action('click', target='volumeSlider', fraction_x=0.4))
            save('volume-committed', client.await_core('mpv_audio_volume' if engine == 'mpv' else 'audio_session_volume',
                requested ** 3 * 100 if engine == 'mpv' else requested,
                tolerance=3 if engine == 'mpv' else 0.026))
            save('mute', client.action('click', target='muteButton'))
            save('mute-committed', client.await_core('mpv_audio_muted' if engine == 'mpv' else 'audio_session_muted', True))
            save('unmute', client.action('click', target='muteButton'))
            save('unmute-committed', client.await_core('mpv_audio_muted' if engine == 'mpv' else 'audio_session_muted', False))
            save('play', client.action('click', target='playButton'))
            save('playing', client.await_core('state', 2))
            save('time-advances', client.await_core('time_seconds', 61, comparison='at_least'))
            save('minimize', client.action('minimize'))
            save('floating-ready', client.await_property('floatingPlayer', 'ready', True))
            save('floating-hover', client.action('move', target='floatingVideoSurface'))
            mini = save('floating-picture', client.snapshot(capture=True, capture_native=True))
            assert mini['main_window']['visibility'] == 3, mini['main_window']
            save('expand-queue', client.action('click', target='floatingQueueToggle'))
            save('expanded-picture', client.snapshot(capture=True, capture_native=True))
            save('restore', client.action('click', target='floatingRestore'))
            restored = save('restored-picture', client.snapshot(capture=True, capture_native=True))
            assert restored['main_window']['visibility'] != 3, restored['main_window']
            save('minimize-again', client.action('minimize'))
            save('floating-again', client.await_property('floatingPlayer', 'ready', True))
            save('hover-dismiss', client.action('move', target='floatingVideoSurface'))
            save('dismiss', client.action('click', target='floatingClose'))
            dismissed = save('still-playing-minimized', client.await_core('state', 2))
            assert dismissed['main_window']['visibility'] == 3, dismissed['main_window']
            save('restore-background', client.action('restore'))
            save('settings', client.action('click', target='toolsButton'))
            other = 'MPV' if engine == 'vlc' else 'VLC'
            save('engine-focus', client.action('focus', name=other))
            save('handover', client.action('click', name=other))
            save('handover-engine', client.await_core('engine', other.lower()))
            save('handover-settled', client.await_core('engine_switching', False))
            save('handover-picture', client.snapshot(capture=True, capture_native=True))
            captures = [json.loads(path.read_text()) for path in evidence.glob('*.json')
                        if len(path.stem) == 32 and path.stem.isalnum()]
            native = [row for row in captures if 'native_capture_saved' in row]
            assert native and all(row['native_capture_saved'] for row in native), native
            (evidence / 'acceptance.json').write_text(json.dumps({
                'state': 'WORKFLOW PASSED; composed pictures require separate inspection',
                'engine': engine, 'native_capture_ids': [row['id'] for row in native]}, indent=2) + '\n')
        finally:
            if player.poll() is None:
                client.request('quit')
            exit_code = player.wait()
            client.close()
            (evidence / 'exit.json').write_text(json.dumps({'exit_code': exit_code}) + '\n')
            if exit_code:
                raise RuntimeError('Owned native player exited with ' + str(exit_code))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--executable', required=True, type=Path)
    parser.add_argument('--scratch', required=True, type=Path)
    parser.add_argument('--engine', choices=('vlc', 'mpv', 'both'), default='both')
    args = parser.parse_args()
    root = args.scratch.resolve()
    root.mkdir(parents=True, exist_ok=False)
    fixture = prepare_fixture(root)
    for engine in ('vlc', 'mpv') if args.engine == 'both' else (args.engine,):
        check_engine(args.executable.resolve(), root, fixture, engine)


if __name__ == '__main__':
    main()
