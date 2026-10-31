"""R04/R65 prior settings, read-only recovery and optional-font preservation.

Only an explicitly seeded synthetic portable profile is used. Existing installed
VLC settings and Windows language are checked separately, never copied or edited.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sqlite3
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
    parser.add_argument('--fixture', required=True, type=Path)
    parser.add_argument('--engine', choices=['vlc', 'mpv'], default='vlc')
    parser.add_argument('--audio-language', choices=['spa', 'eng'], default='spa',
        help='Synthetic profile language; default remains Spanish for preference acceptance')
    parser.add_argument('--check-volume-persistence', action='store_true')
    parser.add_argument('--check-history', action='store_true',
        help='Verify real ML position/rate resume and preservation across a history-disabled launch')
    parser.add_argument('--external-subtitle', type=Path,
        help='Restore an existing, fingerprint-bound subtitle association across both launches')
    args = parser.parse_args()
    source, scratch = args.runtime.resolve(), args.scratch.resolve()
    assert scratch.drive.upper() == 'D:' and scratch.parent.name.startswith(('vlc-s7-', 'vlc-s8-')) and not scratch.exists()
    assert not args.check_volume_persistence or args.engine == 'mpv'
    assert not args.check_history or args.engine == 'mpv'
    assert args.fixture.is_file()
    if args.external_subtitle:
        assert args.external_subtitle.is_file()
    scratch.mkdir()
    runtime = scratch / 'runtime'
    shutil.copytree(source, runtime, ignore=lambda directory, names: ['sdk'] if Path(directory).resolve() == source else [])
    portable = runtime / 'portable'
    portable.mkdir(exist_ok=True)
    assert not any(portable.iterdir())
    malformed = '{bad-json}'
    qt_settings = portable / 'vlc/vlc-qt-interface.ini'
    qt_settings.parent.mkdir()
    qt_settings.write_text('[MainWindow]\ncolor-scheme-index=2\n[redesign]\ncustomization-v1="'
        + malformed + '"\n', encoding='utf-8')
    (portable / 'vlcrc').write_text('qt-privacy-ask=0\nqt-accent-color=#8e42ff\naudio-language=' + args.audio_language + '\n'
        'metadata-network-access=0\nkey-play-pause=Space\nqt-shortcut-feedback=0\n'
        'qt-playback-engine=' + args.engine + '\n', encoding='utf-8')
    associations = None
    if args.external_subtitle:
        def identity(path):
            stat = path.stat()
            with path.open('rb') as stream:
                if stat.st_size <= 8 * 1024 * 1024:
                    payload = stream.read()
                    scope = 'full'
                else:
                    payload = stream.read(65536)
                    stream.seek(stat.st_size - 65536)
                    payload += stream.read(65536)
                    scope = 'first-last-64KiB'
            return {'size': str(stat.st_size), 'modified': str(stat.st_mtime_ns // 1000000),
                'fingerprint': hashlib.sha256(payload).hexdigest(), 'fingerprintScope': scope}
        subtitle = args.external_subtitle.resolve()
        # This is the existing on-disk profile contract, consumed by the real
        # media-tools owner. No fake player, track or backend is introduced.
        media_key = Path(args.fixture.resolve().as_posix().casefold()).as_uri()
        associations = portable / 'redesign-media-tools.json'
        associations.write_text(json.dumps({'version': 1, 'associations': {media_key: {
            'subtitle': subtitle.as_uri(), 'mediaIdentity': identity(args.fixture.resolve()),
            'subtitleIdentity': identity(subtitle)}}}, ensure_ascii=False) + '\n', encoding='utf-8')
        association_bytes = associations.read_bytes()
    font = portable / 'redesign/fonts/Delicious_R_2021.otf'
    font.parent.mkdir(parents=True)
    unknown = b'Synthetic prior unknown font; preserve exact bytes.'
    font.write_bytes(unknown)
    (scratch / 'tmp').mkdir()
    (scratch / 'qml').mkdir()
    plugin = runtime / 'plugins/gui/libqt_plugin.dll'
    assert b'VLC_PLAYER_DIAGNOSTICS_DIR' in plugin.read_bytes()
    plugin_hash = hashlib.sha256(plugin.read_bytes()).hexdigest()
    env = {key: value for key, value in os.environ.items() if not key.startswith('VLC_PLAYER_DIAGNOSTICS')}
    env.pop('VLC_PLUGIN_PATH', None)
    env.update(TEMP=str(scratch / 'tmp'), TMP=str(scratch / 'tmp'), VLC_DATA_PATH=str(runtime),
        QML_DISK_CACHE_PATH=str(scratch / 'qml'), QT_DISABLE_SHADER_DISK_CACHE='1',
        QSG_RHI_DISABLE_SHADER_DISK_CACHE='1', QT_FORCE_STDERR_LOGGING='1',
        QT_SCREEN_SCALE_FACTORS='1;1;1;1;1;1;1;1', QT_SCALE_FACTOR='1')
    records = {'schema': 'vlc_redesign.s7_prior_profile.v1', 'qt_plugin_sha256': plugin_hash,
               'engine': args.engine, 'saved_startup_engine': True,
               'configured_audio_language': args.audio_language,
               'volume_persistence': args.check_volume_persistence, 'runs': []}
    saved_volume = None
    original_audio_session = None
    saved_history_time = None
    history_before_privacy = None

    def stored_history():
        databases = []
        for path in portable.rglob('*.db'):
            with path.open('rb') as stream:
                if stream.read(16) != b'SQLite format 3\0':
                    continue
            with sqlite3.connect(path.as_uri() + '?mode=ro', uri=True) as database:
                database.row_factory = sqlite3.Row
                if not database.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='Media'").fetchone():
                    continue
                columns = {row['name'] for row in database.execute('PRAGMA table_info(Media)')}
                required = {'last_position', 'play_count', 'last_played_date'}
                assert required <= columns, sorted(columns)
                fields = sorted(required | (columns & {'last_time', 'real_last_played_date'}))
                rows = [dict(row) for row in database.execute('SELECT ' + ','.join(fields) + ' FROM Media')]
                assert len(rows) == 1, rows
                databases.append({'database': str(path.relative_to(portable)), 'state': rows[0]})
        assert len(databases) == 1, databases
        return databases[0]

    try:
        for run in (('first', 'restart', 'privacy', 'after-privacy') if args.check_history else ('first', 'restart')):
            directory = scratch / run
            directory.mkdir()
            session = directory / 'session.json'
            token = uuid.uuid4().hex + uuid.uuid4().hex
            environment = dict(env, VLC_PLAYER_DIAGNOSTICS_DIR=str(directory),
                VLC_PLAYER_DIAGNOSTICS_TOKEN=token, VLC_PLAYER_DIAGNOSTICS_BUILD=plugin_hash)
            command = [str(runtime / 'vlc.exe'), '--intf=qt', '--no-one-instance',
                *(['--media-library', '--restore-playback-states',
                    *(['--no-save-recentplay', '--restore-playback-pos=0'] if run == 'privacy' else
                      ['--save-recentplay', '--restore-playback-pos=2'])] if args.check_history else
                  ['--no-media-library', '--no-save-recentplay', '--restore-playback-pos=0']),
                '--no-plugins-cache', '--no-qt-updates-notif', '--no-metadata-network-access',
                '--no-qt-video-autoresize',
                '--no-video-title-show',
                *(['--volume-save'] if args.check_volume_persistence else ['--no-volume-save', '--mmdevice-volume=0']),
                '--aout=mmdevice', '--mmdevice-backend=wasapi', '--start-paused',
                '--file-logging', '--log-verbose=2', '--logfile=' + str(directory / 'native.log'), str(args.fixture.resolve())]

            def inspect(label, operation, *options):
                result = subprocess.run([sys.executable, '-B', str(Path(__file__).with_name('inspect-player.py')),
                    '--session', str(session), operation, *options], capture_output=True,
                    text=True, encoding='utf-8', creationflags=subprocess.CREATE_NO_WINDOW)
                (directory / (label + '.client.log')).write_text(result.stdout + result.stderr, encoding='utf-8')
                assert result.returncode == 0, (label, result.stdout, result.stderr)
                assert '"before": false, "after": false' in result.stdout
                response = Path(re.search(r'^Response: (.+)$', result.stdout, re.M).group(1).strip())
                value = json.loads(response.read_text(encoding='utf-8'))
                assert not value.get('qml_errors'), value.get('qml_errors')
                return value

            with (directory / 'stdout').open('wb') as out, (directory / 'stderr').open('wb') as err:
                player = IsolatedProcess(command, cwd=runtime, env=environment, stdout=out, stderr=err)
                session.write_text(json.dumps({'pid': player.pid, 'executable': str(runtime / 'vlc.exe'), 'token': token}))
                try:
                    snapshot = inspect('prior-settings-loaded', 'snapshot', '--await-core', 'state', '--await-value', '3', '--capture')
                    assert snapshot['core']['engine'] == args.engine
                    if args.check_history:
                        inspect('native-history-read-complete', 'snapshot', '--await-core', 'mpv_history_ready', '--await-value', 'true')
                        if run in ('restart', 'after-privacy'):
                            resumed = inspect('native-position-restored', 'snapshot', '--await-core', 'time_seconds',
                                '--await-value', str(saved_history_time - 0.2), '--await-comparison', 'at_least')
                            assert abs(resumed['core']['time_seconds'] - saved_history_time) < 0.25, resumed['core']
                            rate = inspect('native-rate-restored', 'snapshot', '--await-core', 'rate', '--await-value', '1.1',
                                '--await-tolerance', '0.0001')
                            records[run + '_history_restored'] = {'time': resumed['core']['time_seconds'], 'rate': rate['core']['rate']}
                        if run in ('first', 'privacy'):
                            inspect('history-seek', 'click', '--target', 'progressSlider', '--fraction-x', '0.7' if run == 'privacy' else '0.35')
                            inspect('history-play', 'click', '--target', 'playButton', '--await-core', 'state', '--await-value', '2')
                            inspect('history-real-clock-advanced', 'snapshot', '--await-core', 'time_seconds',
                                '--await-value', '84' if run == 'privacy' else '42', '--await-comparison', 'at_least')
                            paused = inspect('history-pause', 'click', '--target', 'playButton', '--await-core', 'state', '--await-value', '3')
                            if run == 'first':
                                saved_history_time = paused['core']['time_seconds']
                                inspect('history-change-rate', 'key', '--target', 'playButton', '--key', hex(ord(']')),
                                    '--text', ']', '--await-core', 'rate', '--await-value', '1.1', '--await-tolerance', '0.0001')
                    if associations:
                        associated = inspect('saved-subtitle-loaded', 'snapshot', '--await-service', 'redesignMediaTools',
                            '--await-property', 'subtitleLoaded', '--await-value', 'true')
                        selected_subtitles = [track for track in associated['core']['subtitle_tracks'] if track['selected']]
                        assert selected_subtitles, associated['core']
                        if args.engine == 'mpv':
                            expected_names = {subtitle.as_posix().casefold(), unquote(subtitle.as_uri()).casefold()}
                            assert any(track.get('external') is True and
                                unquote(track.get('external-filename', '')).replace('\\', '/').casefold() in expected_names
                                for track in selected_subtitles), selected_subtitles
                        records[run + '_saved_subtitle'] = {'selected': selected_subtitles,
                            'real_track_loaded': True, 'association_sha256': hashlib.sha256(association_bytes).hexdigest()}
                    assert snapshot['presentation']['theme'] == 2 and snapshot['presentation']['accent'] == '#8e42ff'
                    assert snapshot['customization']['error'] and not snapshot['customization']['onboardingVisible']
                    assert snapshot['customization_saved']['sha256'] == hashlib.sha256(malformed.encode()).hexdigest()
                    selected = [track for track in snapshot['core']['audio_tracks'] if track['selected']]
                    languages = ('spa', 'es', 'spanish') if args.audio_language == 'spa' else ('eng', 'en', 'english')
                    assert len(selected) == 1 and selected[0]['language'].lower() in languages, selected
                    assert not snapshot['optional_legacy_font']['available'] and not snapshot['optional_legacy_font']['busy']
                    assert Path(snapshot['optional_legacy_font']['location']).resolve() == font.resolve()
                    if run == 'first':
                        inspect('open-menu', 'click', '--target', 'topBarMenuButton')
                        inspect('reopen-existing-profile-setup', 'widget_click', '--menu-action', 'Welcome / Appearance Setup…')
                        snapshot = inspect('skip-existing-profile-setup', 'click', '--target', 'onboardingSkip')
                        assert not snapshot['customization']['onboardingVisible']
                        assert snapshot['presentation']['theme'] == 2 and snapshot['presentation']['accent'] == '#8e42ff'
                    if args.check_volume_persistence:
                        inspect('native-mpv-audio-ready', 'snapshot', '--await-core', 'mpv_audio_output',
                            '--await-value', json.dumps('wasapi'))
                        if run == 'first':
                            original_volume = inspect('original-session-volume', 'snapshot', '--await-core', 'mpv_audio_volume',
                                '--await-value', '0', '--await-comparison', 'at_least')
                            original_mute = inspect('original-session-mute', 'snapshot', '--await-core', 'mpv_audio_muted',
                                '--await-value', '0', '--await-comparison', 'at_least')
                            original_audio_session = {'volume': original_volume['core']['mpv_audio_volume'],
                                'muted': original_mute['core']['mpv_audio_muted']}
                            assert 0 <= original_audio_session['volume'] <= 100
                            assert isinstance(original_audio_session['muted'], bool)
                            records['original_shared_audio_session'] = original_audio_session
                            sliders = [node for node in snapshot['tree'] if node['id'] == 'volumeSlider' and node['visible']]
                            assert len(sliders) == 1
                            level = inspect('set-remembered-volume', 'click', '--target', 'volumeSlider',
                                '--fraction-x', str(0.35 / sliders[0]['to']), '--await-core', 'audio_session_volume',
                                '--await-value', '0.35', '--await-tolerance', '0.026')
                            saved_volume = level['core']['audio_session_volume']
                            if level['core']['audio_session_muted'] != 1:
                                inspect('set-remembered-mute', 'click', '--target', 'muteButton',
                                    '--await-core', 'audio_session_muted', '--await-value', '1')
                        else:
                            inspect('remembered-volume-after-restart', 'snapshot', '--await-core', 'audio_session_volume',
                                '--await-value', str(saved_volume), '--await-tolerance', '0.001')
                            inspect('remembered-mute-after-restart', 'snapshot', '--await-core', 'audio_session_muted', '--await-value', '1')
                        actual = inspect('native-mpv-session-volume', 'snapshot', '--await-core', 'mpv_audio_volume',
                            '--await-value', str(100 * saved_volume ** 3), '--await-tolerance', '0.02')
                        muted = inspect('native-mpv-session-mute', 'snapshot', '--await-core', 'mpv_audio_muted',
                            '--await-value', 'true')
                        assert actual['core']['mpv_audio_output'] == 'wasapi'
                        assert abs(actual['core']['volume'] - 100) < 0.01
                        assert muted['core']['audio_session_muted'] == 1
                        records[run + '_native_audio_session'] = muted['core']
                    records['runs'].append({'run': run, 'presentation': snapshot['presentation'],
                        'selected_audio': selected, 'preserved_store': snapshot['customization_saved'],
                        'font': snapshot['optional_legacy_font']})
                finally:
                    try:
                        # volume-save deliberately joins VLC's persistent Windows
                        # session. Restore its observed hardware state after the
                        # final launch, and on any failed case, before closing.
                        final_run = 'after-privacy' if args.check_history else 'restart'
                        try:
                            if original_audio_session is not None and (run == final_run or sys.exc_info()[0] is not None):
                                current = inspect('restore-session-state', 'snapshot', '--await-core', 'mpv_audio_muted',
                                    '--await-value', '0', '--await-comparison', 'at_least')
                                sliders = [node for node in current['tree'] if node['id'] == 'volumeSlider' and node['visible']]
                                assert len(sliders) == 1
                                level = (original_audio_session['volume'] / 100.) ** (1. / 3.)
                                current = inspect('restore-original-session-volume', 'click', '--target', 'volumeSlider',
                                    '--fraction-x', str(level / sliders[0]['to']), '--await-core', 'audio_session_volume',
                                    '--await-value', str(level), '--await-tolerance', '0.001')
                                # The native volume action can itself unmute.
                                # Compare its resulting state, not the earlier
                                # asynchronous MPV query cached before that action.
                                if bool(current['core']['audio_session_muted']) != original_audio_session['muted']:
                                    inspect('restore-original-session-mute', 'click', '--target', 'muteButton',
                                        '--await-core', 'audio_session_muted', '--await-value', str(int(original_audio_session['muted'])))
                                actual = inspect('verify-original-session-volume', 'snapshot', '--await-core', 'mpv_audio_volume',
                                    '--await-value', str(original_audio_session['volume']), '--await-tolerance', '0.002')
                                muted = inspect('verify-original-session-mute', 'snapshot', '--await-core', 'mpv_audio_muted',
                                    '--await-value', json.dumps(original_audio_session['muted']))
                                records['original_shared_audio_session_restored'] = {
                                    'volume': actual['core']['mpv_audio_volume'], 'muted': muted['core']['mpv_audio_muted']}
                        finally:
                            inspect('quit', 'quit')
                    finally:
                        code = player.wait()
                        assert code == 0, code
                        records[run + '_exit'] = code
                        records[run + '_input_desktop_preserved'] = True
            assert font.read_bytes() == unknown
            if args.check_history:
                saved = stored_history()
                records[run + '_stored_history'] = saved
                assert 0.3 < saved['state']['last_position'] < 0.5, saved
                if run == 'restart':
                    history_before_privacy = saved
                elif run == 'privacy':
                    assert saved == history_before_privacy, (history_before_privacy, saved)
            if associations:
                assert associations.read_bytes() == association_bytes, 'Existing subtitle association was rewritten'
        records['passed'] = True
    except Exception as error:
        records.update(passed=False, failure=repr(error))
        raise
    finally:
        (scratch / 'result.json').write_text(json.dumps(records, indent=2) + '\n', encoding='utf-8')
        print(json.dumps(records, indent=2), flush=True)


if __name__ == '__main__':
    main()
