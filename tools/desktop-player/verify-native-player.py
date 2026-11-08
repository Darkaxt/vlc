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
    # Keep the muxing input outside the playback folder. A matching sidecar
    # would correctly auto-load as a second subtitle track beside the embedded
    # track, making this embedded-subtitle acceptance fixture ambiguous.
    mux_inputs = root / 'mux-inputs'
    mux_inputs.mkdir()
    subtitles = mux_inputs / 'native.srt'
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


def seed_upstream_profile(home):
    # These are synthetic upstream VLC profiles, not the runner's real data.
    # The fork's own bundle/XDG namespace must leave every one untouched.
    roots = ([home / 'Library' / category / 'org.videolan.vlc' for category in
              ('Preferences', 'Application Support', 'Caches')] if platform.system() == 'Darwin'
             else [home / category / 'vlc' for category in ('config', 'data', 'cache')])
    for directory in roots:
        directory.mkdir(parents=True)
        (directory / 'preservation-marker').write_bytes(b'Existing upstream VLC data\n')
    (roots[0] / 'vlcrc').write_text('### Synthetic existing VLC preferences\nvolume=0.31\n')
    return roots


def profile_hashes(home, roots):
    return {path.relative_to(home).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for root in roots for path in root.rglob('*') if path.is_file()}


def check_engine(executable, root, fixture, engine, software_decoding=False):
    case = root / engine
    case.mkdir()
    evidence = case / 'evidence'; evidence.mkdir()
    home = case / 'home'; home.mkdir()
    upstream_roots = seed_upstream_profile(home)
    before_upstream = profile_hashes(home, upstream_roots)
    if platform.system() == 'Darwin':
        # Select the actual fork setting for the Figma dark reference. Preserve
        # the hosted machine's system appearance and synthetic upstream profile.
        settings = home / 'Library/Preferences/io.github.darkaxt.modern-vlc/vlc-qt-interface.ini'
        settings.parent.mkdir(parents=True)
        settings.write_text('[MainWindow]\ncolor-scheme-index=2\n')
    token = uuid.uuid4().hex + uuid.uuid4().hex
    env = os.environ.copy()
    env.update(HOME=str(home), XDG_CONFIG_HOME=str(home / 'config'),
        XDG_DATA_HOME=str(home / 'data'), XDG_CACHE_HOME=str(home / 'cache'),
        VLC_PLAYER_DIAGNOSTICS_DIR=str(evidence), VLC_PLAYER_DIAGNOSTICS_TOKEN=token,
        VLC_NATIVE_CI_CAPTURE='1', QT_FORCE_STDERR_LOGGING='1', LANG='C', LC_ALL='C',
        QML_DISK_CACHE_PATH=str(case / 'qml-cache'), QT_LOGGING_RULES='qt.qpa.gl=true')
    # Darwin selects language through its environment/preferences, not VLC's
    # Windows --language option. one-instance and qt-updates-notif are likewise
    # conditional on DBus/Windows and UPDATE_CHECK; the isolated profile retains
    # their disabled defaults without passing options absent from this build.
    argv = [str(executable), '--intf=qt',
        '--no-qt-privacy-ask', '--no-metadata-network-access',
        '--restore-playback-pos=0', '--no-video-title-show', '--start-paused',
        '--qt-playback-engine=' + engine, '--verbose=2', str(fixture)]
    if software_decoding:
        argv[1:1] = ['--codec=avcodec', '--avcodec-hw=none']
    (evidence / 'launch.json').write_text(json.dumps({'argv': argv, 'platform': platform.platform(),
        'executable_sha256': hashlib.sha256(executable.read_bytes()).hexdigest()}, indent=2) + '\n')
    records = []

    def save(label, result):
        inspect_result(result)
        records.append({'label': label, 'response_id': result['id']})
        (evidence / 'workflow.json').write_text(json.dumps(records, indent=2) + '\n')
        print(f'NATIVE {engine}: {label}', flush=True)
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
            save('subtitle-position', client.slider('progressSlider', 0.01))
            save('subtitle-seek-committed', client.await_core('time_seconds', 6, tolerance=2))
            subtitle = save('subtitle-picture', client.snapshot(capture=True, capture_native=True))
            assert any(track.get('selected') for track in subtitle['core']['subtitle_tracks']), subtitle['core']
            save('seek', client.slider('progressSlider', 0.1))
            save('seek-committed', client.await_core('time_seconds', 60, tolerance=2))
            controls = client.snapshot()
            volume = next(node for node in controls['tree'] if node['id'] == 'volumeSlider' and node['visible'])
            requested = float(volume['to']) * 0.4
            save('volume', client.slider('volumeSlider', 0.4))
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
                print((evidence / 'stderr.log').read_text(errors='replace')[-8000:], flush=True)
                raise RuntimeError('Owned native player exited with ' + str(exit_code))
    stderr_text = (evidence / 'stderr.log').read_text(errors='replace')
    if 'OpenGL (ES) 3.0 context creation failed.' in stderr_text:
        raise RuntimeError('Native Qt graphics probe fell back after context creation failure')
    if any('using services_discovery module "' + name + '"' in stderr_text
           for name in ('bonjour', 'upnp', 'sap')):
        raise RuntimeError('Local-only native playback unexpectedly started LAN discovery')
    # The live handover above saved the other engine. Reopen the same profile
    # without a command-line engine override to verify actual persistence.
    reopen = case / 'reopen'; reopen.mkdir()
    env['VLC_PLAYER_DIAGNOSTICS_DIR'] = str(reopen)
    reopened_argv = [argument for argument in argv if not argument.startswith('--qt-playback-engine=')]
    with (reopen / 'stdout.log').open('wb') as stdout, (reopen / 'stderr.log').open('wb') as stderr:
        player = subprocess.Popen(reopened_argv, cwd=executable.parent, env=env, stdout=stdout, stderr=stderr)
        client = client_module.NativePlayerClient(player, reopen, token)
        try:
            reopened = inspect_result(client.await_core('state', 3))
            assert reopened['core']['engine'] == other.lower(), reopened['core']
            (reopen / 'engine-persistence.json').write_text(json.dumps({
                'state': 'PASSED', 'expected_engine': other.lower(), 'core': reopened['core']}, indent=2) + '\n')
        finally:
            if player.poll() is None:
                client.request('quit')
            exit_code = player.wait()
            client.close()
            if exit_code:
                print((reopen / 'stderr.log').read_text(errors='replace')[-8000:], flush=True)
                raise RuntimeError('Reopened native player exited with ' + str(exit_code))
    after_upstream = profile_hashes(home, upstream_roots)
    (evidence / 'upstream-profile-preservation.json').write_text(json.dumps({
        'state': 'PASSED' if after_upstream == before_upstream else 'FAILED',
        'before': before_upstream, 'after': after_upstream}, indent=2) + '\n')
    assert after_upstream == before_upstream, 'The fork modified the synthetic upstream VLC profile'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--executable', required=True, type=Path)
    parser.add_argument('--scratch', required=True, type=Path)
    parser.add_argument('--engine', choices=('vlc', 'mpv', 'both'), default='both')
    parser.add_argument('--vlc-software-decoding', action='store_true',
                        help='Hosted VM diagnosis only; does not change packaged defaults')
    args = parser.parse_args()
    root = args.scratch.resolve()
    root.mkdir(parents=True, exist_ok=False)
    fixture = prepare_fixture(root)
    for engine in ('vlc', 'mpv') if args.engine == 'both' else (args.engine,):
        check_engine(args.executable.resolve(), root, fixture, engine, args.vlc_software_decoding)


if __name__ == '__main__':
    main()
