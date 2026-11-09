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
import re
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


def prepare_replacements(root):
    image = root / 'native-image.png'
    audio = root / 'native-audio.wav'
    run('ffmpeg', '-hide_banner', '-loglevel', 'error', '-f', 'lavfi', '-i',
        'color=c=0x2b83b8:size=640x360', '-frames:v', '1', '-threads', '1', image)
    run('ffmpeg', '-hide_banner', '-loglevel', 'error', '-f', 'lavfi', '-i',
        'sine=frequency=800:sample_rate=48000', '-t', '30', '-c:a', 'pcm_s16le', audio)
    return image, audio


def inspect_result(result):
    if result.get('qml_errors'):
        raise RuntimeError('Native QML errors: ' + json.dumps(result['qml_errors']))
    return result


def subtitle_choices(observation):
    """Find the rendered track group without assuming a Qt-version role value."""
    rows = [row for row in observation['tree'] if row['visible'] and row['enabled']]
    none = [row for row in rows if row.get('name') == 'None'
            and 'selected' in row and row.get('actions')]
    if len(none) != 1:
        raise RuntimeError('Expected one subtitle None choice in the open tracks popup')
    return [row for row in rows if row.get('parent') == none[0]['parent']
            and row['node'] != none[0]['node'] and 'selected' in row and row.get('actions')]


def retain_x11_surface_observation(evidence, observation):
    """Read only the owned player's XIDs and backing pixmaps on its CI display."""
    from Xlib import X, display, error as xerror
    from Xlib.ext import composite
    connection = display.Display()
    rows = []
    try:
        connection.composite_query_version()
        for window in observation.get('windows', []):
            if not window.get('native_id_hex'):
                continue
            xid = int(window['native_id_hex'], 16)
            resource = connection.create_resource_object('window', xid)
            row = {'xid': xid, 'name': window['name']}
            try:
                geometry = resource.get_geometry()
                attributes = resource.get_attributes()
                row.update(parent_xid=resource.query_tree().parent.id,
                    depth=geometry.depth, visual=attributes.visual,
                    map_state=attributes.map_state, width=geometry.width, height=geometry.height)
                # Naming existing storage does not redirect/reparent or change
                # the rendering. The temporary X resource is freed below.
                failed = xerror.CatchError()
                pixmap = resource.composite_name_window_pixmap(onerror=failed)
                connection.sync()
                if failed.get_error():
                    raise RuntimeError(str(failed.get_error()))
                try:
                    row['backing_samples'] = [pixmap.get_image(
                        geometry.width * column // 8, geometry.height // 2,
                        1, 1, X.ZPixmap, 0xffffffff).data.hex() for column in range(1, 8)]
                finally:
                    pixmap.free()
            except Exception as error:
                row['observation_error'] = str(error)
            rows.append(row)
        connection.sync()
    finally:
        connection.close()
    (evidence / (observation['id'] + '-x11-surfaces.json')).write_text(
        json.dumps(rows, indent=2) + '\n')


def retain_timing_observation(evidence):
    """Summarize all native trace events without loading the trace into RAM."""
    trace = evidence / 'native-timing.jsonl'
    groups = {}
    with trace.open() as stream:
        for line in stream:
            row = json.loads(line)
            body = row['Body']
            key = '|'.join(str(body.get(name, '')) for name in ('type', 'id', 'mode', 'event'))
            group = groups.setdefault(key, {'count': 0, 'first': row, 'last': row, 'ranges': {}})
            group['count'] += 1
            group['last'] = row
            for field in ('Timestamp', 'pts', 'render_ts', 'render_pts', 'drift'):
                value = row.get(field) if field == 'Timestamp' else body.get(field)
                if value is not None:
                    number = int(value)
                    bounds = group['ranges'].setdefault(field, [number, number])
                    bounds[0], bounds[1] = min(bounds[0], number), max(bounds[1], number)
    with trace.open('rb') as stream:
        trace_digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    log = (evidence / 'stderr.log').read_text(errors='replace')
    (evidence / 'timing-observation.json').write_text(json.dumps({
        'trace_sha256': trace_digest, 'groups': groups,
        'input_clock_gap_warnings': log.count('clock gap, unexpected stream discontinuity:'),
        'coreaudio_late_start_messages': log.count('auhal audio output debug: starting late'),
        'qualification': 'Diagnostic evidence; timing correctness requires review'}, indent=2) + '\n')


def inspect_cocoa_video_placement(result):
    """Reject a decoded Cocoa picture placed outside its native parent view."""
    if result['core']['engine'] != 'vlc' or 'cocoa_graphics' not in result:
        return

    def rectangle(value):
        numbers = re.findall(r'-?\d+(?:\.\d+)?', value)
        if len(numbers) != 4:
            raise RuntimeError('Unexpected Cocoa rectangle: ' + value)
        return tuple(map(float, numbers))

    found = []

    def visit(parent):
        for child in parent.get('children', []):
            if child.get('class') == 'VLCSampleBufferDisplayView':
                x, y, width, height = rectangle(child['frame'])
                bx, by, bw, bh = rectangle(parent['bounds'])
                assert width > 0 and height > 0, child
                assert (x >= bx - 1 and y >= by - 1 and
                        x + width <= bx + bw + 1 and
                        y + height <= by + bh + 1), {'parent': parent['bounds'], 'video': child['frame']}
                found.append(child)
            visit(child)

    visit(result['cocoa_graphics'])
    assert found, 'No native VLC display view in the Cocoa picture capture'


def reveal_setting(client, name):
    """Scroll the actual settings viewport before dispatching a visible click."""
    while True:
        state = client.snapshot()
        body = next(row for row in state['tree']
                    if row['node'] == client.target(state, 'mediaSettingsBody'))
        button = next(row for row in state['tree']
                      if row['node'] == client.target(state, name=name))
        if body['y'] <= button['y'] and button['y'] + button['height'] <= body['y'] + body['height']:
            return
        direction = 1 if button['y'] < body['y'] else -1
        before = body['contentY']
        client.action('scroll', target='mediaSettingsBody', delta=direction * 120)
        settled = client.await_property('mediaSettingsBody', 'moving', False)
        after = next(row['contentY'] for row in settled['tree'] if row['id'] == 'mediaSettingsBody')
        if direction * (after - before) >= 0:
            raise RuntimeError('Native settings wheel did not advance toward ' + name)


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


def check_engine(executable, root, fixture, replacements, engine, software_decoding=False,
                 compositor=None, picture_only=False):
    case = root / (engine + '-' + compositor + '-control' if compositor else engine)
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
    argv[1:1] = ['--tracer=json', '--json-tracer-file=' + str(evidence / 'native-timing.jsonl')]
    if compositor:
        argv[1:1] = ['--qt-compositor=' + compositor]
    if software_decoding:
        argv[1:1] = ['--codec=avcodec', '--avcodec-hw=none']
    (evidence / 'launch.json').write_text(json.dumps({'argv': argv, 'platform': platform.platform(),
        'executable_sha256': hashlib.sha256(executable.read_bytes()).hexdigest()}, indent=2) + '\n')
    records = []

    def save(label, result):
        inspect_result(result)
        if label in ('main-picture', 'subtitle-picture', 'floating-picture',
                     'expanded-picture', 'restored-picture', 'handover-picture', 'replacement-picture'):
            inspect_cocoa_video_placement(result)
            if platform.system() == 'Linux':
                retain_x11_surface_observation(evidence, result)
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
            assert initial['media_library_available'], 'Fresh native profile failed media-library initialization'
            if engine == 'mpv':
                initial = save('native-video-ready', client.await_core('mpv_video_ready', True))
            assert initial['core']['engine'] == engine, initial['core']
            assert initial['core']['video_tracks'] and initial['core']['audio_tracks'], initial['core']
            assert initial['core']['subtitle_tracks'], initial['core']
            save('seekable', client.await_core('seekable', True))
            save('main-picture', client.snapshot(capture=True, capture_native=True))
            if picture_only:
                (evidence / 'composition-control.json').write_text(json.dumps({
                    'purpose': 'Compare the existing X11 compositor with the platform native-child hierarchy',
                    'engine': engine, 'compositor': compositor,
                    'qualification': 'Diagnostic first-picture control only; not feature or package acceptance',
                }, indent=2) + '\n')
                return
            save('subtitle-menu', client.action('click', target='subtitleButton'))
            choices = client.snapshot()
            tracks = subtitle_choices(choices)
            assert len(tracks) == 1, tracks
            save('select-subtitle', client.action('click', name=tracks[0]['name']))
            save('close-subtitle-menu', client.action('key', key=0x1000000))
            save('subtitle-position', client.slider('progressSlider', 0.01))
            save('subtitle-seek-committed', client.await_core('time_seconds', 6, tolerance=2))
            save('leave-seek-preview', client.action('move', target='playButton'))
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
            reveal_setting(client, other)
            save('engine-revealed', client.snapshot())
            save('handover', client.action('click', name=other))
            save('handover-engine', client.await_core('engine', other.lower()))
            save('handover-settled', client.await_core('engine_switching', False))
            save('handover-subtitle-selected', client.await_core('selected_subtitle_count', 1))
            handed = save('handover-picture', client.snapshot(capture=True, capture_native=True))
            assert handed['core']['state'] == 2, handed['core']
            assert abs(handed['core']['rate'] - 1) < 0.01, handed['core']
            assert abs(handed['core']['audio_session_volume'] - requested) < 0.026, handed['core']
            assert handed['core']['time_seconds'] >= 60, handed['core']
            save('close-settings', client.action('key', key=0x1000000))
            image, audio = replacements
            save('replace-with-image', client.action('drop', target='viewLoader', urls=[image.as_uri()]))
            save('image-input', client.await_core('url', image.as_uri()))
            preview = save('image-preview', client.await_core('still_image_preview', True))
            assert not any(node['id'] == 'progressSlider' and node['visible'] and node['enabled']
                           for node in preview['tree']), 'The image preview exposes a timed seek control'
            save('image-picture', client.snapshot(capture=True, capture_native=True))
            save('replace-with-audio', client.action('drop', target='viewLoader', urls=[audio.as_uri()]))
            save('audio-input', client.await_core('url', audio.as_uri()))
            save('audio-loaded', client.await_core('state', [2, 3], comparison='one_of'))
            save('audio-layout-ready', client.await_property('playerSpecializationLoader', 'status', 1))
            save('audio-view', client.await_property('playerAudioView', 'visible', True))
            audio_state = save('audio-picture', client.snapshot(capture=True, capture_native=True))
            assert audio_state['core']['audio_tracks'] and not audio_state['core']['video_tracks'], audio_state['core']
            assert not audio_state['core']['still_image_preview'], audio_state['core']
            save('replace-with-video', client.action('drop', target='viewLoader', urls=[fixture.as_uri()]))
            save('video-input', client.await_core('url', fixture.as_uri()))
            save('video-loaded', client.await_core('state', [2, 3], comparison='one_of'))
            save('video-layout-ready', client.await_property('playerSpecializationLoader', 'status', 1))
            save('video-view', client.await_property('playerVideoSurface', 'visible', True))
            if other == 'MPV':
                save('replacement-video-ready', client.await_core('mpv_video_ready', True))
            replacement = save('replacement-picture', client.snapshot(capture=True, capture_native=True))
            assert replacement['core']['video_tracks'] and replacement['core']['audio_tracks'], replacement['core']
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
            if platform.system() == 'Linux':
                # Preserve the actual failed first-profile path state before
                # deciding whether the application or its environment failed.
                storage = home / 'data/modern-vlc/vlc/ml/mlstorage'
                directories = []
                for path in reversed((storage, *storage.parents)):
                    try:
                        status = path.stat()
                        directories.append({'path': str(path), 'mode': oct(status.st_mode),
                            'uid': status.st_uid, 'gid': status.st_gid, 'directory': path.is_dir()})
                    except OSError as error:
                        directories.append({'path': str(path), 'errno': error.errno})
                (evidence / 'library-path-state.json').write_text(json.dumps({
                    'euid': os.geteuid(), 'egid': os.getegid(), 'directories': directories}, indent=2) + '\n')
            (evidence / 'exit.json').write_text(json.dumps({'exit_code': exit_code}) + '\n')
            if exit_code:
                print((evidence / 'stderr.log').read_text(errors='replace')[-8000:], flush=True)
                raise RuntimeError('Owned native player exited with ' + str(exit_code))
    stderr_text = (evidence / 'stderr.log').read_text(errors='replace')
    retain_timing_observation(evidence)
    if 'OpenGL (ES) 3.0 context creation failed.' in stderr_text:
        raise RuntimeError('Native Qt graphics probe fell back after context creation failure')
    if any('using services_discovery module "' + name + '"' in stderr_text
           for name in ('bonjour', 'upnp', 'sap')):
        raise RuntimeError('Local-only native playback unexpectedly started LAN discovery')
    # The live handover above saved the other engine. Reopen the same profile
    # without a command-line engine override to verify actual persistence.
    reopen = case / 'reopen'; reopen.mkdir()
    env['VLC_PLAYER_DIAGNOSTICS_DIR'] = str(reopen)
    reopened_argv = [argument for argument in argv if not argument.startswith(
        ('--qt-playback-engine=', '--json-tracer-file='))]
    reopened_argv[1:1] = ['--json-tracer-file=' + str(reopen / 'native-timing.jsonl')]
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
    replacements = prepare_replacements(root)
    for engine in ('mpv', 'vlc') if args.engine == 'both' else (args.engine,):
        check_engine(args.executable.resolve(), root, fixture, replacements, engine, args.vlc_software_decoding)
    if platform.system() == 'Linux':
        # Temporary diagnostic control for the evidenced blank platform
        # hierarchy. Keep the complete default workflows above unchanged.
        check_engine(args.executable.resolve(), root, fixture, replacements, 'mpv',
                     compositor='x11', picture_only=True)


if __name__ == '__main__':
    main()
