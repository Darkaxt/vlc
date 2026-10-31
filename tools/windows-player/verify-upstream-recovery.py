"""Verify actual queued recovery ownership, unanswered preservation and Yes/No paths."""
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
    scratch = args.scratch.resolve()
    assert scratch.drive.upper() == 'D:' and scratch.parent.name.startswith('vlc-s8-') and not scratch.exists()
    source = args.runtime.resolve(strict=True)
    assert not any((source / 'portable').iterdir()) and args.fixture.is_file()
    scratch.mkdir()
    records = {'schema': 'vlc_redesign.upstream_recovery.v1', 'passed': False,
        'qt_plugin_sha256': hashlib.sha256((source / 'plugins/gui/libqt_plugin.dll').read_bytes()).hexdigest(),
        'scope': 'Native Qt dialog events on owned inactive desktops; synthetic queue only', 'runs': []}
    try:
        for scenario in ('preserve-then-restore', 'decline'):
            base = scratch / scenario
            runtime = base / 'runtime'
            shutil.copytree(source, runtime)
            portable = runtime / 'portable'
            settings = portable / 'vlc/vlc-qt-interface.ini'
            settings.parent.mkdir()
            recovery = base / 'synthetic-recovery.m3u8'
            payload = '#EXTM3U\n' + args.fixture.resolve().as_uri() + '\n'
            recovery.write_text(payload, encoding='utf-8')
            expected_bytes = recovery.read_bytes()
            settings.write_text('[Playlist]\nRecoveryFilePath=' + recovery.as_posix() + '\n', encoding='utf-8')
            for action in (('unanswered', 'Yes') if scenario == 'preserve-then-restore' else ('No',)):
                evidence = base / action
                evidence.mkdir()
                (evidence / 'tmp').mkdir()
                (evidence / 'qml').mkdir()
                session = evidence / 'session.json'
                token = uuid.uuid4().hex + uuid.uuid4().hex
                env = {key: value for key, value in os.environ.items() if not key.startswith('VLC_PLAYER_DIAGNOSTICS')}
                for key in ('VLC_PLUGIN_PATH', 'LC_ALL', 'LC_MESSAGES', 'LANGUAGE'):
                    env.pop(key, None)
                env.update(TEMP=str(evidence / 'tmp'), TMP=str(evidence / 'tmp'),
                    VLC_DATA_PATH=str(runtime), VLC_USERDATA_PATH=str(portable),
                    QML_DISK_CACHE_PATH=str(evidence / 'qml'), QT_DISABLE_SHADER_DISK_CACHE='1',
                    QSG_RHI_DISABLE_SHADER_DISK_CACHE='1', QT_FORCE_STDERR_LOGGING='1',
                    VLC_PLAYER_DIAGNOSTICS_DIR=str(evidence), VLC_PLAYER_DIAGNOSTICS_TOKEN=token,
                    VLC_PLAYER_DIAGNOSTICS_BUILD=records['qt_plugin_sha256'])
                command = [str(runtime / 'vlc.exe'), '--language=en', '--intf=qt', '--no-one-instance',
                    '--no-media-library', '--qt-playback-engine=vlc', '--no-plugins-cache', '--start-paused',
                    '--no-qt-privacy-ask', '--no-qt-updates-notif', '--no-metadata-network-access',
                    '--no-save-recentplay', '--restore-playback-pos=0', '--no-qt-video-autoresize',
                    '--no-volume-save', '--mmdevice-volume=0', '--aout=mmdevice', '--mmdevice-backend=wasapi',
                    '--file-logging', '--log-verbose=2', '--logfile=' + str(evidence / 'native.log')]
                def inspect(label, operation, *options):
                    process = subprocess.run([sys.executable, '-B', str(Path(__file__).with_name('inspect-player.py')),
                        '--session', str(session), operation, *map(str, options)], capture_output=True,
                        text=True, encoding='utf-8', creationflags=subprocess.CREATE_NO_WINDOW)
                    (evidence / (label + '.client.log')).write_text(process.stdout + process.stderr, encoding='utf-8')
                    assert process.returncode == 0, (label, process.stdout, process.stderr)
                    assert '"before": false, "after": false' in process.stdout
                    path = Path(re.search(r'^Response: (.+)$', process.stdout, re.M).group(1).strip())
                    value = json.loads(path.read_text(encoding='utf-8'))
                    assert not value.get('qml_errors'), value.get('qml_errors')
                    return value
                with (evidence / 'stdout').open('wb') as out, (evidence / 'stderr').open('wb') as err:
                    player = IsolatedProcess(command, cwd=runtime, env=env, stdout=out, stderr=err)
                    session.write_text(json.dumps({'pid': player.pid, 'executable': str(runtime / 'vlc.exe'), 'token': token}))
                    try:
                        snapshot = inspect('queued-prompt', 'snapshot', '--capture')
                        dialogs = [widget for widget in snapshot['widgets'] if widget['id'] == 'modelRecoveryQuestion']
                        assert len(dialogs) == 1 and dialogs[0]['font_family'].startswith('Inter'), dialogs
                        assert snapshot['player_ready'] and recovery.read_bytes() == expected_bytes
                        if action != 'unanswered':
                            after = inspect('answer-' + action.lower(), 'widget_click', '--widget-text', action, '--capture')
                            assert not any(widget['id'] == 'modelRecoveryQuestion' for widget in after['widgets'])
                            if action == 'Yes':
                                restored = inspect('play-restored-queue', 'click', '--target', 'playButton',
                                    '--await-core', 'url', '--await-value', json.dumps(args.fixture.resolve().as_uri()))
                                assert restored['core']['engine'] == 'vlc'
                                inspect('restored-paused-input', 'snapshot', '--await-core', 'state', '--await-value', '3')
                    finally:
                        try:
                            inspect('quit', 'quit')
                        finally:
                            assert player.wait() == 0
                if action == 'unanswered':
                    assert recovery.read_bytes() == expected_bytes and 'RecoveryFilePath=' in settings.read_text()
                else:
                    assert not recovery.exists() and 'RecoveryFilePath=' not in settings.read_text()
                records['runs'].append({'scenario': scenario, 'answer': action,
                    'one_styled_queued_dialog': True, 'normal_exit': True, 'input_desktop_preserved': True,
                    'pending_preserved': action == 'unanswered', 'restored_queue_playable': action == 'Yes'})
        records['passed'] = True
    except Exception as error:
        records['failure'] = repr(error)
        raise
    finally:
        (scratch / 'result.json').write_text(json.dumps(records, indent=2) + '\n')
        print(json.dumps(records), flush=True)


if __name__ == '__main__':
    main()
