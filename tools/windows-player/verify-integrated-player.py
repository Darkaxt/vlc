"""S7 native player regression through the existing app-owned Qt event bridge.

Run only against an explicitly instrumented build. Each invocation copies that
runtime into a fresh task-owned directory and uses its portable profile. This
does not send Windows input, switch desktops, or test physical display output.
"""
import argparse
import gettext
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
    parser.add_argument('--runtime', type=Path, required=True)
    parser.add_argument('--scratch', type=Path, required=True)
    parser.add_argument('--fixture', type=Path, required=True)
    parser.add_argument('--start-paused', action='store_true')
    parser.add_argument('--engine', choices=['vlc', 'mpv'], default='vlc')
    parser.add_argument('--default-engine', action='store_true',
        help='Verify the untouched VLC startup default without an engine command-line override')
    parser.add_argument('--switch-engines', action='store_true', help='Verify actual paused and playing in-player handovers in both directions')
    parser.add_argument('--backend-controls', action='store_true',
        help='Verify real keyboard rate and audio/subtitle delays, including their handover preservation')
    parser.add_argument('--runtime-failure', choices=['missing', 'incompatible'],
        help='Verify a rejected MPV selection leaves the current VLC item usable')
    parser.add_argument('--theme', choices=['light', 'dark'], default='light')
    parser.add_argument('--scale', choices=['1', '1.5', '2'], default='1')
    parser.add_argument('--presentation-only', action='store_true')
    parser.add_argument('--with-media-library', action='store_true')
    parser.add_argument('--language-code', default='en')
    args = parser.parse_args()
    assert not args.default_engine or args.engine == 'vlc'
    assert not args.runtime_failure or (args.engine == 'vlc' and not args.switch_engines
        and args.language_code == 'en' and not args.presentation_only)
    assert not args.backend_controls or not args.presentation_only
    source, scratch, fixture = (p.resolve() for p in (args.runtime, args.scratch, args.fixture))
    assert scratch.drive.upper() in ('D:', 'E:') and scratch.parent.name.lower().startswith(('vlc-s7-', 'vlc-s8-'))
    assert not scratch.exists(), 'Use a fresh exact case directory; preserve previous results'
    assert fixture.is_file()
    assert re.fullmatch('[a-z]{2,3}(?:_[A-Z]{2})?', args.language_code)
    translate = lambda text: text
    if args.language_code != 'en':
        with (source / 'locale' / args.language_code / 'LC_MESSAGES/vlc.mo').open('rb') as stream:
            catalog = gettext.GNUTranslations(stream)
        translate = catalog.gettext
        assert translate('Cancel') != 'Cancel', 'Localized acceptance needs a real translated control'
    marker = 'VLC_PLAYER_DIAGNOSTICS_DIR'
    plugin = source / 'plugins/gui/libqt_plugin.dll'
    assert marker.encode() in plugin.read_bytes(), 'Expected an explicitly instrumented Qt plugin'
    scratch.mkdir()
    runtime, evidence = scratch / 'runtime', scratch / 'evidence'
    def omitted(directory, names):
        if Path(directory).resolve() != source:
            return []
        return ['sdk'] + (['libmpv-2.dll'] if args.runtime_failure else [])
    shutil.copytree(source, runtime, ignore=omitted)
    if args.runtime_failure == 'incompatible':
        (runtime / 'libmpv-2.dll').write_bytes(b'Synthetic incompatible payload; the compiled hash must reject this before loading.\n')
    # The input build profile must be empty. Do not remove pre-existing state.
    portable = runtime / 'portable'
    portable.mkdir(exist_ok=True)
    assert not any(portable.iterdir()), 'The source runtime has a populated portable profile'
    qt_settings = portable / 'vlc/vlc-qt-interface.ini'
    qt_settings.parent.mkdir()
    qt_settings.write_text(
        '[MainWindow]\ncolor-scheme-index=' + ('1' if args.theme == 'light' else '2') + '\n', encoding='utf-8')
    evidence.mkdir()
    (scratch / 'tmp').mkdir()
    (scratch / 'qml-cache').mkdir()
    session = evidence / 'session.json'
    token = uuid.uuid4().hex + uuid.uuid4().hex
    env = {k: v for k, v in os.environ.items() if not k.startswith('VLC_PLAYER_DIAGNOSTICS')}
    env.pop('VLC_PLUGIN_PATH', None)
    env.pop('QT_SCREEN_SCALE_FACTORS', None)
    # The agent shell sets LC_ALL=C.UTF-8. Its precedence would suppress the
    # launcher's supported --language override even with valid native catalogs.
    for variable in ('LC_ALL', 'LC_MESSAGES', 'LANGUAGE'):
        env.pop(variable, None)
    env.update(TEMP=str(scratch / 'tmp'), TMP=str(scratch / 'tmp'), VLC_DATA_PATH=str(runtime),
        VLC_USERDATA_PATH=str(portable), QML_DISK_CACHE_PATH=str(scratch / 'qml-cache'),
        QT_DISABLE_SHADER_DISK_CACHE='1', QSG_RHI_DISABLE_SHADER_DISK_CACHE='1',
        QT_FORCE_STDERR_LOGGING='1', QT_ENABLE_HIGHDPI_SCALING='0', QT_FONT_DPI='96',
        QT_SCALE_FACTOR=args.scale, VLC_PLAYER_DIAGNOSTICS_DIR=str(evidence),
        VLC_PLAYER_DIAGNOSTICS_TOKEN=token,
        VLC_PLAYER_DIAGNOSTICS_BUILD=hashlib.sha256(plugin.read_bytes()).hexdigest())
    command = [str(runtime / 'vlc.exe'), '--language', args.language_code, '--intf=qt', '--no-one-instance',
        *([] if args.default_engine else ['--qt-playback-engine=' + args.engine]),
        *([] if args.with_media_library else ['--no-media-library']),
        '--no-plugins-cache', '--restore-playback-pos=0', '--no-save-recentplay',
        '--no-qt-privacy-ask', '--no-qt-updates-notif', '--no-metadata-network-access',
        '--no-qt-video-autoresize', '--no-video-title-show', '--no-volume-save',
        '--aout=mmdevice', '--mmdevice-backend=wasapi', '--mmdevice-volume=0',
        '--verbose=2', '--file-logging', '--log-verbose=2', '--logfile=' + str(evidence / 'native-ui.log')]
    if args.start_paused:
        command.append('--start-paused')
    command.append(str(fixture))
    (evidence / 'launch-argv.json').write_text(json.dumps(command, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    records = {'schema': 'vlc_redesign.s7_integrated_player.v1', 'steps': [],
        'start_paused': args.start_paused, 'theme': args.theme, 'scale': args.scale,
        'initial_engine': args.engine, 'switch_engines': args.switch_engines,
        'untouched_startup_default': args.default_engine,
        'backend_controls': args.backend_controls,
        'runtime_failure': args.runtime_failure,
        'language': args.language_code,
        'qt_plugin_sha256': hashlib.sha256(plugin.read_bytes()).hexdigest(),
        'scope': 'App-owned native Qt events on an inactive desktop; no OS input or physical-output claim.'}
    inspector = Path(__file__).with_name('inspect-player.py')

    def inspect(label, operation, *options):
        completed = subprocess.run([sys.executable, '-B', str(inspector), '--session', str(session),
            operation, *map(str, options)], capture_output=True, text=True, encoding='utf-8',
            creationflags=subprocess.CREATE_NO_WINDOW)
        (evidence / (label + '.client.log')).write_text(completed.stdout + completed.stderr, encoding='utf-8')
        assert completed.returncode == 0, (label, completed.stdout, completed.stderr)
        output = Path(re.search(r'^Response: (.+)$', completed.stdout, re.M).group(1).strip())
        result = json.loads(output.read_text(encoding='utf-8'))
        assert not result.get('qml_errors'), (label, result.get('qml_errors'))
        assert '"before": false, "after": false' in completed.stdout, 'Owned player gained OS foreground'
        records['steps'].append({'name': label, 'response': output.name, 'core': result.get('core')})
        return result, output

    def state(label, expected):
        return inspect(label, 'snapshot', '--await-core', 'state', '--await-value', expected)

    def click_state(label, expected):
        return inspect(label, 'click', '--target', 'playButton', '--await-core', 'state', '--await-value', expected)

    def clock(label, minimum):
        return inspect(label, 'snapshot', '--await-core', 'time_seconds', '--await-value', minimum,
            '--await-comparison', 'at_least')

    def keyboard_control(label, character, property_name, expected, comparison='equal'):
        # Dispatch real Qt key events through the existing application hotkeys.
        # The observed value comes from the active engine, not a displayed label.
        inspect(label + '-focus', 'focus', '--target', 'playButton')
        return inspect(label, 'key', '--target', 'playButton',
            '--key', hex(ord(character.upper())), '--text', character,
            '--await-core', property_name, '--await-value', expected, '--await-tolerance', 0.0001,
            '--await-comparison', comparison)

    def backend_controls():
        before, _ = inspect('before-backend-controls', 'snapshot')
        assert abs(before['core']['rate'] - 1.) < 0.0001, before['core']
        keyboard_control('keyboard-faster', ']', 'rate', 1.1)
        keyboard_control('keyboard-audio-delay', 'k', 'audio_delay_ms', before['core']['audio_delay_ms'] + 50.)
        changed, _ = keyboard_control('keyboard-subtitle-delay', 'h', 'subtitle_delay_ms', before['core']['subtitle_delay_ms'] + 50.)
        assert abs(changed['core']['rate'] - 1.1) < 0.0001, changed['core']
        records['native_backend_controls'] = {'before': before['core'], 'changed': changed['core'],
            'real_keyboard_events': True, 'actual_engine_notify_observed': True}
        return before['core']

    def restore_backend_controls(original):
        keyboard_control('restore-normal-rate', '=', 'rate', 1.)
        keyboard_control('restore-audio-delay', 'j', 'audio_delay_ms', original['audio_delay_ms'])
        restored, _ = keyboard_control('restore-subtitle-delay', 'g', 'subtitle_delay_ms', original['subtitle_delay_ms'])
        records['native_backend_controls']['restored'] = restored['core']

    def handovers():
        assert args.language_code == 'en', 'Engine labels are checked in an English workflow case'
        records['engine_handovers'] = []
        for playing in (False, True):
            volume_level = 1.2 if playing else 0.35
            current, _ = inspect('before-handover-volume', 'snapshot')
            sliders = [node for node in current['tree'] if node['id'] == 'volumeSlider' and node['visible']]
            assert len(sliders) == 1 and sliders[0]['to'] >= volume_level, sliders
            # Change the actual slider while paused, then mute before resuming.
            # The two passes cover attenuation and software amplification.
            level, _ = inspect('handover-volume-' + str(volume_level), 'click', '--target', 'volumeSlider',
                '--fraction-x', volume_level / sliders[0]['to'],
                '--await-core', 'audio_session_volume', '--await-value', volume_level, '--await-tolerance', 0.026)
            if level['core']['audio_session_muted'] != 1:
                inspect('mute-before-handover', 'click', '--target', 'muteButton',
                    '--await-core', 'audio_session_muted', '--await-value', 1)
            if playing:
                click_state('handover-resume', 2)
            for engine in ('mpv', 'vlc') if args.engine == 'vlc' else ('vlc', 'mpv'):
                before, _ = inspect('before-handover-' + engine, 'snapshot')
                expected_state = 2 if playing else 3
                assert before['core']['state'] == expected_state, before['core']
                inspect('handover-settings-' + engine, 'click', '--target', 'toolsButton', '--capture')
                inspect('choose-' + engine, 'click', '--name', 'MPV / Dolby Vision' if engine == 'mpv' else 'VLC')
                settled, _ = inspect('handover-settled-' + engine, 'snapshot',
                    '--await-core', 'engine_switching', '--await-value', 'false')
                if settled['core']['engine'] != engine:
                    # An initialization rejection is a terminal result. Waiting
                    # for the requested engine would hide it indefinitely.
                    error_state, _ = inspect('engine-selection-error-' + engine, 'snapshot', '--capture')
                    details, _ = inspect('engine-selection-details-' + engine, 'click', '--target', 'detailsBtn', '--capture')
                    records['engine_selection_failure'] = {'requested': engine,
                        'observed_core': error_state['core'], 'widget_captures': details.get('widget_captures', [])}
                    raise AssertionError(('Engine selection rejected', engine, records['engine_selection_failure']))
                after, _ = state('handover-state-' + engine, expected_state)
                assert after['core']['engine'] == engine, after['core']
                assert unquote(after['core']['url']) == unquote(before['core']['url']), (before['core'], after['core'])
                difference = after['core']['time_seconds'] - before['core']['time_seconds']
                assert abs(difference) <= (3 if playing else 0.2), (engine, playing, difference)
                assert abs(after['core']['audio_session_volume'] - before['core']['audio_session_volume']) < 0.001, (before['core'], after['core'])
                assert after['core']['audio_session_muted'] == before['core']['audio_session_muted'] == 1
                for property_name in ('rate', 'audio_delay_ms', 'subtitle_delay_ms'):
                    assert abs(after['core'][property_name] - before['core'][property_name]) < 0.0001, (property_name, before['core'], after['core'])
                if engine == 'mpv':
                    assert any(track['selected'] for track in after['core']['video_tracks']), after['core']
                    assert after['core']['video-out-params'], after['core']
                    restrictions = [node for node in after['tree'] if node['visible']
                        and node.get('name') == 'Show Statistics (VLC)' and node.get('actions')
                        and 'Press' in node['actions']]
                    assert len(restrictions) == 1 and not restrictions[0]['enabled'], restrictions
                    assert any(node['visible'] and 'statistics require VLC playback' in node.get('text', '')
                        for node in after['tree']), 'Missing actionable VLC-only tool disclosure'
                    inspect('mpv-audio-ready', 'snapshot', '--await-core', 'mpv_audio_output',
                        '--await-value', json.dumps('wasapi'))
                    actual_audio, _ = inspect('mpv-session-volume', 'snapshot', '--await-core', 'mpv_audio_volume',
                        '--await-value', 100 * min(1, before['core']['audio_session_volume'] ** 3),
                        '--await-tolerance', 0.02)
                    actual_mute, _ = inspect('mpv-session-mute', 'snapshot', '--await-core', 'mpv_audio_muted',
                        '--await-value', 'true')
                    assert after['core']['observation'] == 'native_mpv_events'
                    assert after['core']['native_vlc']['state'] == 0, after['core']['native_vlc']
                    expected_gain = 100 * max(1, before['core']['audio_session_volume'] ** 3)
                    assert abs(actual_audio['core']['volume'] - expected_gain) < 0.1, actual_audio['core']
                    assert actual_mute['core']['mpv_audio_muted'] is True
                records['engine_handovers'].append({'from': before['core']['engine'], 'to': engine,
                    'playing': playing, 'position_delta_seconds': difference,
                    'native_session_volume': after['core']['audio_session_volume'],
                    'native_session_muted': after['core']['audio_session_muted'],
                    'rate_and_delays_preserved': True,
                    'vlc_only_tool_disclosed_and_disabled': engine == 'mpv',
                    'same_media': True, 'incoming_native_state': after['core']['state']})
                inspect('dismiss-engine-settings-' + engine, 'key', '--key', '0x1000000')
                if engine == 'mpv' and args.backend_controls:
                    # The contract here is an effective increase followed by
                    # exact handover preservation, independent of the engine's
                    # additive/multiplicative fine-step implementation.
                    keyboard_control('mpv-rate-before-return-' + str(playing), ']', 'rate',
                        after['core']['rate'] + 0.001, comparison='at_least')
            if playing:
                click_state('handover-pause', 3)
        inspect('restore-silent-test-volume', 'click', '--target', 'volumeSlider', '--fraction-x', 0,
            '--await-core', 'audio_session_volume', '--await-value', 0, '--await-tolerance', 0.001)

    def idle_handovers():
        before, _ = inspect('before-idle-stop', 'snapshot')
        stopped, _ = inspect('stop-for-idle-switch', 'key', '--key', '0x53', '--text', 's',
            '--await-core', 'state', '--await-value', 0)
        records['idle_engine_handovers'] = []
        for engine in ('mpv', 'vlc') if args.engine == 'vlc' else ('vlc', 'mpv'):
            # Stop returns to Home. Its native Playback menu deliberately owns
            # idle engine selection; the in-player tools popup is not visible.
            inspect('idle-home-menu-' + engine, 'click', '--target', 'menuBtn')
            inspect('idle-playback-menu-' + engine, 'widget_click', '--menu-action', 'Playback')
            inspect('idle-engine-menu-' + engine, 'widget_click', '--menu-action', 'Playback engine')
            inspect('idle-engine-choice-' + engine, 'widget_click', '--menu-action', 'MPV / Dolby Vision' if engine == 'mpv' else 'VLC')
            selected, _ = inspect('idle-engine-settled-' + engine, 'snapshot',
                '--await-core', 'engine_switching', '--await-value', 'false')
            assert selected['core']['engine'] == engine and selected['core']['state'] == 0, selected['core']
            records['idle_engine_handovers'].append({'engine': engine, 'state': selected['core']['state']})
        inspect('idle-home-play-menu', 'click', '--target', 'menuBtn')
        inspect('idle-playback-play-menu', 'widget_click', '--menu-action', 'Playback')
        restarted, _ = inspect('restart-same-queue-item-after-idle-switch', 'widget_click', '--menu-action', 'Play',
            '--await-core', 'state', '--await-value', 2)
        assert unquote(restarted['core']['url']) == unquote(before['core']['url']), restarted['core']
        clock('advancing-after-idle-switch', 1)
        click_state('pause-after-idle-switch', 3)

    def track_choices(snapshot, body):
        nodes = {node['node']: node for node in snapshot['tree']}
        def inside(node):
            while node['parent'] >= 0:
                node = nodes[node['parent']]
                if node['id'] == body:
                    return True
            return False
        choices = [node for node in snapshot['tree'] if node['visible'] and node['enabled']
            and node.get('actions') and 'selected' in node and inside(node)]
        none = [node for node in choices if node.get('name') == translate('None')]
        assert len(none) == 1, none
        # Output devices share the popup's scroll body, but belong to another
        # rendered group. Only the real None/track group is a track selector.
        return [node for node in choices if node['parent'] == none[0]['parent']]

    def library_workflow():
        # Native indexing, queue and stored-playlist owners, through real UI.
        assert args.language_code == 'en', 'Run the library data case separately from localized labels'
        initial, _ = inspect('library-data-before', 'snapshot')
        preserved = (initial['core']['url'], initial['core']['time_seconds'])

        def unchanged(snapshot):
            assert snapshot['core']['state'] == 3, snapshot['core']
            assert (snapshot['core']['url'], snapshot['core']['time_seconds']) == preserved, snapshot['core']

        def count(label, expected, comparison='equal'):
            snapshot, _ = inspect(label, 'snapshot', '--await-target', 'fullLibrary',
                '--await-property', 'itemCount', '--await-value', expected,
                '--await-comparison', comparison, '--capture')
            snapshot, _ = inspect(label + '-mounted', 'snapshot', '--await-target', 'fullLibrary',
                '--await-property', 'ready', '--await-value', 'true', '--capture')
            unchanged(snapshot)
            return snapshot

        def enter(label, text):
            inspect(label, 'key', '--target', 'libraryDialogInput', '--key', '0', '--text', text)
            inspect(label + '-submit', 'click', '--target', 'libraryDialogSubmit')

        playlist_name = 'S7 stored playlist Ω — ' + 'long-title-' * 20
        inspect('stored-playlists', 'click', '--target', 'libraryNav_playlists')
        count('empty-stored-playlists', 0)
        inspect('new-stored-playlist', 'click', '--target', 'libraryNewPlaylist')
        enter('stored-playlist-name', playlist_name)
        count('stored-playlist-created', 1)
        inspect('library-index-menu', 'click', '--target', 'libraryAddItem')
        inspect('library-index-dialog', 'click', '--name', 'Index library folder…')
        enter('library-index-folder', str(fixture.parent))
        inspect('all-videos-menu', 'click', '--target', 'libraryAddItem')
        inspect('all-videos', 'click', '--name', 'All videos')
        indexed = count('real-indexed-videos', 3, 'at_least')
        inspect('indexed-fixture-idle', 'snapshot', '--await-target', 'fullLibrary',
            '--await-property', 'indexing', '--await-value', 'false')
        candidates = [node for node in indexed['tree'] if node['visible']
            and node['id'].startswith('libraryItem_') and node.get('url')
            and unquote(node['url']) != unquote(preserved[0])]
        assert candidates, indexed['library']
        chosen = candidates[0]
        selected, _ = inspect('select-indexed-media', 'click', '--target', chosen['id'])
        unchanged(selected)
        inspect('enqueue-indexed-media', 'click', '--target', 'libraryEnqueue')
        inspect('stored-playlist-picker', 'click', '--target', 'libraryAddToPlaylist')
        appended, _ = inspect('append-to-stored-playlist', 'click', '--name', playlist_name)
        unchanged(appended)
        inspect('return-stored-playlists', 'click', '--target', 'libraryNav_playlists')
        stored = count('stored-playlist-list', 1, 'at_least')
        stored_count = stored['library']['indexed_model_count']
        # Indexing the fixture's M3U also creates a native stored playlist.
        # Select our exact named target and preserve every other playlist.
        others = {node['name'] for node in stored['tree'] if node['visible']
            and node['id'].startswith('libraryItem_') and node.get('name') != playlist_name}
        assert 'local-playlist.m3u8' in others, others
        inspect('choose-stored-playlist', 'click', '--name', playlist_name)
        inspect('open-stored-playlist', 'key', '--target', 'libraryItems', '--key', '0x1000004')
        contents = count('stored-playlist-real-content', 1)
        content_urls = [node['url'] for node in contents['tree'] if node['visible']
            and node['id'].startswith('libraryItem_') and node.get('url')]
        assert content_urls == [chosen['url']], content_urls
        content_rows = [node for node in contents['tree'] if node['visible']
            and node['id'].startswith('libraryItem_') and node.get('url')]
        assert len(content_rows) == 1
        inspect('choose-stored-content', 'click', '--target', content_rows[0]['id'])
        inspect('remove-stored-content', 'click', '--name', 'Remove from playlist')
        count('stored-content-removed', 0)
        inspect('stored-playlists-for-delete', 'click', '--target', 'libraryNav_playlists')
        count('stored-playlists-before-delete', stored_count)
        inspect('choose-stored-delete', 'click', '--name', playlist_name)
        inspect('delete-stored-confirmation', 'click', '--name', 'Delete playlist')
        inspect('delete-stored-playlist', 'click', '--name', 'Delete playlists')
        remaining = count('stored-playlist-deleted', stored_count - 1)
        remaining_names = {node['name'] for node in remaining['tree'] if node['visible']
            and node['id'].startswith('libraryItem_')}
        assert remaining_names == others, (remaining_names, others)
        inspect('library-data-return-player', 'click', '--target', 'libraryReturnToPlayer')
        queue, _ = inspect('independent-playback-queue', 'click', '--target', 'playqueueToggle', '--capture')
        unchanged(queue)
        queue_urls = [node['url'] for node in queue['tree'] if node['visible']
            and 'isCurrent' in node and node.get('url')]
        assert list(map(unquote, queue_urls)) == list(map(unquote, [preserved[0], chosen['url']])), queue_urls
        summary = [node['text'] for node in queue['tree'] if node['visible'] and node['id'] == 'playqueueSummary']
        assert len(summary) == 1 and summary[0].startswith('2 items'), summary
        records['library_data'] = {'indexed_video_count': indexed['library']['indexed_model_count'],
            'stored_playlist_create_append_remove_delete': True,
            'unrelated_imported_playlists_preserved': sorted(others),
            'queue_urls_after_stored_edits': queue_urls, 'paused_input_and_time_preserved': True,
            'long_unicode_playlist_name': playlist_name}
        inspect('close-independent-queue', 'click', '--target', 'playqueueToggle')

    with (evidence / 'stdout.log').open('wb') as out, (evidence / 'stderr.log').open('wb') as err:
        player = IsolatedProcess(command, cwd=runtime, env=env, stdout=out, stderr=err)
        session.write_text(json.dumps({'pid': player.pid, 'executable': str(runtime / 'vlc.exe'), 'token': token}), encoding='utf-8')
        try:
            state('initial-state', 3 if args.start_paused else 2)
            selected_engine, _ = inspect('initial-engine', 'snapshot')
            assert selected_engine['core']['engine'] == args.engine, selected_engine['core']
            if not args.start_paused:
                clock('initial-clock', 1)
                click_state('pause', 3)
            snapshot, reference_output = inspect('reference-size', 'resize', '--width', round(1920 / float(args.scale)),
                '--height', round(1080 / float(args.scale)), '--capture')
            assert snapshot['player_ready'], snapshot.get('missing_required_items')
            assert snapshot['presentation']['theme'] == (1 if args.theme == 'light' else 2), snapshot['presentation']
            assert abs(snapshot['window']['dpr'] - float(args.scale)) < 0.001, snapshot['window']
            records['observed_theme'] = snapshot['presentation']['theme']
            records['observed_dpr'] = snapshot['window']['dpr']
            assert len(snapshot['core']['audio_tracks']) == 2
            assert any(track['selected'] for track in snapshot['core']['video_tracks']), snapshot['core']
            if args.engine == 'mpv':
                assert snapshot['core']['video-out-params'], snapshot['core']
            assert len(snapshot['core']['subtitle_tracks']) >= 1
            assert snapshot['core']['seekable']
            from importlib.util import module_from_spec, spec_from_file_location
            capture_spec = spec_from_file_location('player_capture', Path(__file__).with_name('verify-player-capture.py'))
            capture_checks = module_from_spec(capture_spec)
            capture_spec.loader.exec_module(capture_checks)
            records['player_geometry'] = capture_checks.verify_capture(snapshot, reference_output.with_suffix('.png'))
            if not args.presentation_only:
                inspect('paused-seek', 'click', '--target', 'progressSlider', '--fraction-x', 0.35)
                click_state('resume', 2)
                resumed, _ = clock('committed-seek-clock', 40)
                assert resumed['core']['time_seconds'] < 60, 'Seek did not commit to the intended interval'
                click_state('pause-again', 3)
                inspect('keyboard-focus', 'focus', '--target', 'playButton')
                inspect('keyboard-resume', 'key', '--target', 'playButton', '--key', '0x20',
                    '--await-core', 'state', '--await-value', 2)
                clock('advancing-after-keyboard', 42)
                click_state('pause-for-tracks', 3)
                if args.runtime_failure:
                    before, _ = inspect('before-rejected-engine', 'snapshot')
                    inspect('open-engine-menu', 'click', '--target', 'toolsButton')
                    inspect('choose-unavailable-mpv', 'click', '--name', 'MPV / Dolby Vision')
                    after, _ = inspect('rejected-engine-error', 'snapshot', '--capture')
                    assert after['core']['engine'] == 'vlc' and not after['core']['engine_switching']
                    assert after['core']['state'] == before['core']['state'] == 3
                    assert after['core']['url'] == before['core']['url']
                    assert abs(after['core']['time_seconds'] - before['core']['time_seconds']) < 0.2
                    visible = '\n'.join(str(node.get('text', '')) for node in after['tree'] if node['visible'])
                    expected = 'MPV runtime is incomplete' if args.runtime_failure == 'missing' else 'does not match this release'
                    assert 'MPV playback' in visible, visible
                    details, _ = inspect('runtime-error-details', 'click', '--target', 'detailsBtn', '--capture')
                    dialogs = [node for node in details['widgets'] if node['parent'] < 0
                        and node['type'] == 'MessagesDialog']
                    assert len(dialogs) == 1, dialogs
                    captures = [item for item in details['widget_captures'] if item['widget'] == dialogs[0]['node']]
                    assert len(captures) == 1 and captures[0]['saved'], captures
                    inspect('close-runtime-error-details', 'widget_click', '--widget-text', 'Close')
                    click_state('resume-after-rejected-engine', 2)
                    clock('clock-after-rejected-engine', before['core']['time_seconds'] + 1)
                    click_state('pause-after-rejected-engine', 3)
                    records['runtime_failure_recovery'] = {'kind': args.runtime_failure,
                        'error_popup_visible': True, 'engine_item_pause_position_preserved': True,
                        'details_capture': captures[0]['file'], 'expected_details': expected,
                        'actionable_error_visual_review': 'Pending inspection of the actual native details capture, including the portable-package recovery instruction',
                        'native_vlc_resume_clock_verified': True}
                original_controls = backend_controls() if args.backend_controls else None
                if args.switch_engines:
                    handovers()
                if original_controls is not None:
                    restore_backend_controls(original_controls)
                if args.switch_engines:
                    idle_handovers()
                fullscreen, _ = inspect('fullscreen-button', 'click', '--target', 'fullscreenButton',
                    '--await-core', 'fullscreen', '--await-value', 'true', '--capture')
                assert fullscreen['window']['visibility'] == 5, fullscreen['window']
                windowed, _ = inspect('escape-fullscreen', 'key', '--key', '0x1000000',
                    '--await-core', 'fullscreen', '--await-value', 'false', '--capture')
                assert windowed['window']['visibility'] != 5, windowed['window']
            tracks, _ = inspect('audio-popup', 'click', '--target', 'audioButton', '--capture')
            assert not tracks['images'].get('failed', 0)
            alternate = [node for node in track_choices(tracks, 'audioTracksBody')
                if node.get('name') != translate('None') and not node['selected']]
            assert len(alternate) == 1, alternate
            previous_audio = [track['id'] for track in tracks['core']['audio_tracks'] if track['selected']]
            selected, _ = inspect('select-alternate-audio', 'click', '--name', alternate[0]['name'],
                '--await-property', 'selected', '--await-value', 'true')
            assert [track['id'] for track in selected['core']['audio_tracks'] if track['selected']] != previous_audio
            inspect('dismiss-audio', 'key', '--key', '0x1000000')
            subtitles, _ = inspect('subtitle-popup', 'click', '--target', 'subtitleButton', '--capture')
            subtitle_choices = track_choices(subtitles, 'subtitleTracksBody')
            none = [node for node in subtitle_choices if node.get('name') == translate('None')]
            assert len(none) == 1
            disabled, _ = inspect('disable-subtitles', 'click', '--name', translate('None'),
                '--await-property', 'selected', '--await-value', 'true')
            assert not any(track['selected'] for track in disabled['core']['subtitle_tracks'])
            available = [node for node in track_choices(disabled, 'subtitleTracksBody')
                if node.get('name') != translate('None')]
            assert available
            enabled, _ = inspect('enable-text-subtitle', 'click', '--name', available[0]['name'],
                '--await-property', 'selected', '--await-value', 'true')
            assert any(track['selected'] for track in enabled['core']['subtitle_tracks'])
            inspect('dismiss-subtitles', 'key', '--key', '0x1000000')
            # Native Widgets participate in every theme/DPI case.
            preferences, _ = inspect('native-preferences', 'key', '--key', '0x50', '--modifiers', '0x4000000', '--capture')
            dialogs = [widget for widget in preferences['widgets'] if widget['parent'] < 0
                and 'Prefs' in widget['type']]
            assert len(dialogs) == 1, dialogs
            assert dialogs[0]['font_family'].startswith('Inter'), dialogs[0]
            records['native_preferences'] = dialogs[0]
            inspect('cancel-preferences', 'widget_click', '--widget-text', translate('Cancel'))
            records['localized_cancel_text'] = translate('Cancel')
            if args.with_media_library:
                inspect('open-compact-library', 'click', '--target', 'mediaBrowserButton')
                compact, compact_output = inspect('compact-library', 'snapshot',
                    '--await-target', 'compactLibrary', '--await-property', 'ready', '--await-value', 'true', '--capture')
                records['compact_library_geometry'] = capture_checks.verify_library_capture(compact, compact_output.with_suffix('.png'))
                inspect('expand-library', 'click', '--target', 'expandLibrary')
                full, full_output = inspect('full-library', 'snapshot',
                    '--await-target', 'fullLibrary', '--await-property', 'ready', '--await-value', 'true', '--capture')
                records['full_library_geometry'] = capture_checks.verify_library_capture(full, full_output.with_suffix('.png'))
                library_workflow()
            inspect('narrow-player', 'resize', '--width', 680, '--height', 420, '--capture')
            final, _ = inspect('final-engine-state', 'snapshot')
            records['final_native_core'] = final['core']
            records['passed'] = True
        except Exception as error:
            records.update(passed=False, failure=repr(error))
            raise
        finally:
            try:
                inspect('quit', 'quit')
            finally:
                records['exit_code'] = player.wait()
                records['passed'] = records.get('passed', False) and records['exit_code'] == 0
                log = (evidence / 'native-ui.log').read_text(encoding='utf-8', errors='replace')
                records['wasapi_selected'] = 'using aout stream module "wasapi"' in log
                records['qt_event_loop_finished'] = 'QApp exec() finished' in log
                # Upstream MessagesDialog replaces the process's file logger
                # with its native message view. Error-recovery cases inspect
                # that dialog, then verify subsequent real playback, owned
                # window close and native process exit instead of requiring a
                # line in a logger that no longer exists. Keep the missing log
                # observation explicit; do not report it as observed completion.
                records['file_logger_transferred_to_messages_dialog'] = bool(
                    args.runtime_failure and records.get('runtime_failure_recovery')
                    and '-- logger module stopped --' in log)
                records['native_lifecycle_verified'] = records['exit_code'] == 0 and (
                    records['qt_event_loop_finished'] or records['file_logger_transferred_to_messages_dialog'])
                records['shutdown_evidence'] = ('qt_loop_completion_log_and_native_exit'
                    if records['qt_event_loop_finished'] else 'owned_window_close_and_native_exit_after_message_logger_transfer'
                    if records['file_logger_transferred_to_messages_dialog'] else 'native_exit_without_loop_completion_evidence')
                if args.language_code != 'en':
                    records['native_translation_selected'] = ('translation test: code is "' + translate('C') + '"') in log
                    records['passed'] &= records['native_translation_selected']
                records['input_desktop_preserved'] = True  # IsolatedProcess.wait verifies this.
                audio_verified = records['wasapi_selected'] if args.engine == 'vlc' or args.switch_engines else \
                    records.get('final_native_core', {}).get('current-ao') == 'wasapi'
                records['native_audio_output_verified'] = audio_verified
                records['passed'] &= audio_verified and records['native_lifecycle_verified']
                (scratch / 'result.json').write_text(json.dumps(records, indent=2) + '\n', encoding='utf-8')
                summary = {key: records[key] for key in ('passed', 'exit_code', 'failure', 'start_paused',
                    'theme', 'scale', 'language', 'observed_theme', 'observed_dpr', 'wasapi_selected',
                    'qt_event_loop_finished', 'input_desktop_preserved', 'library_data') if key in records}
                print(json.dumps(summary), flush=True)
    return 0 if records['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
