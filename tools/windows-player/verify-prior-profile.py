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
import subprocess
import sys
import uuid

sys.dont_write_bytecode = True
from isolated_desktop import IsolatedProcess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime', required=True, type=Path)
    parser.add_argument('--scratch', required=True, type=Path)
    parser.add_argument('--fixture', required=True, type=Path)
    args = parser.parse_args()
    source, scratch = args.runtime.resolve(), args.scratch.resolve()
    assert scratch.drive.upper() == 'D:' and scratch.parent.name.startswith('vlc-s7-') and not scratch.exists()
    assert args.fixture.is_file()
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
    (portable / 'vlcrc').write_text('qt-privacy-ask=0\nqt-accent-color=#8e42ff\naudio-language=spa\n'
        'metadata-network-access=0\nkey-play-pause=Space\nqt-shortcut-feedback=0\n', encoding='utf-8')
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
    records = {'schema': 'vlc_redesign.s7_prior_profile.v1', 'qt_plugin_sha256': plugin_hash, 'runs': []}
    try:
        for run in ('first', 'restart'):
            directory = scratch / run
            directory.mkdir()
            session = directory / 'session.json'
            token = uuid.uuid4().hex + uuid.uuid4().hex
            environment = dict(env, VLC_PLAYER_DIAGNOSTICS_DIR=str(directory),
                VLC_PLAYER_DIAGNOSTICS_TOKEN=token, VLC_PLAYER_DIAGNOSTICS_BUILD=plugin_hash)
            command = [str(runtime / 'vlc.exe'), '--intf=qt', '--no-one-instance', '--no-media-library',
                '--no-plugins-cache', '--no-qt-updates-notif', '--no-metadata-network-access',
                '--no-save-recentplay', '--restore-playback-pos=0', '--no-qt-video-autoresize',
                '--no-video-title-show', '--no-volume-save', '--mmdevice-volume=0', '--start-paused',
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
                    assert snapshot['presentation']['theme'] == 2 and snapshot['presentation']['accent'] == '#8e42ff'
                    assert snapshot['customization']['error'] and not snapshot['customization']['onboardingVisible']
                    assert snapshot['customization_saved']['sha256'] == hashlib.sha256(malformed.encode()).hexdigest()
                    selected = [track for track in snapshot['core']['audio_tracks'] if track['selected']]
                    assert len(selected) == 1 and selected[0]['language'].lower() in ('spa', 'es', 'spanish'), selected
                    assert not snapshot['optional_legacy_font']['available'] and not snapshot['optional_legacy_font']['busy']
                    assert Path(snapshot['optional_legacy_font']['location']).resolve() == font.resolve()
                    if run == 'first':
                        inspect('open-menu', 'click', '--target', 'topBarMenuButton')
                        inspect('reopen-existing-profile-setup', 'widget_click', '--menu-action', 'Welcome / Appearance Setup…')
                        snapshot = inspect('skip-existing-profile-setup', 'click', '--target', 'onboardingSkip')
                        assert not snapshot['customization']['onboardingVisible']
                        assert snapshot['presentation']['theme'] == 2 and snapshot['presentation']['accent'] == '#8e42ff'
                    records['runs'].append({'run': run, 'presentation': snapshot['presentation'],
                        'selected_audio': selected, 'preserved_store': snapshot['customization_saved'],
                        'font': snapshot['optional_legacy_font']})
                finally:
                    try:
                        inspect('quit', 'quit')
                    finally:
                        code = player.wait()
                        assert code == 0, code
                        records[run + '_exit'] = code
                        records[run + '_input_desktop_preserved'] = True
            assert font.read_bytes() == unknown
        records['passed'] = True
    except Exception as error:
        records.update(passed=False, failure=repr(error))
        raise
    finally:
        (scratch / 'result.json').write_text(json.dumps(records, indent=2) + '\n', encoding='utf-8')
        print(json.dumps(records, indent=2), flush=True)


if __name__ == '__main__':
    main()
