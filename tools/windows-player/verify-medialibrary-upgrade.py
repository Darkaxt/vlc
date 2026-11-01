"""Open a real prior-version synthetic library with the updated native player."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import sys

sys.dont_write_bytecode = True
from isolated_desktop import IsolatedProcess


def database_state(profile):
    path = profile / 'ml/ml.db'
    with sqlite3.connect(path.as_uri() + '?mode=ro', uri=True) as db:
        return {'settings': db.execute('SELECT * FROM Settings').fetchall(),
            'media': db.execute('SELECT id_media, type, duration, last_position, play_count FROM Media ORDER BY id_media').fetchall(),
            'files': db.execute('SELECT id_file, mrl, media_id FROM File ORDER BY id_file').fetchall()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime', type=Path, required=True)
    parser.add_argument('--profile', type=Path, required=True)
    parser.add_argument('--seed-result', type=Path, required=True)
    parser.add_argument('--fixture', type=Path, required=True)
    parser.add_argument('--scratch', type=Path, required=True)
    args = parser.parse_args()
    scratch = args.scratch.resolve()
    assert scratch.drive.upper() == 'D:' and scratch.parent.name.startswith('vlc-s8-') and not scratch.exists()
    seed = json.loads(args.seed_result.read_text())
    assert seed['passed'] and seed['source_version'] == '1.1.0' and seed['exit_code'] == 0
    baseline = database_state(args.profile)
    original = hashlib.sha256((args.profile / 'ml/ml.db').read_bytes()).hexdigest()
    runtime = scratch / 'runtime'
    shutil.copytree(args.runtime, runtime)
    assert not any((runtime / 'portable').iterdir())
    shutil.copytree(args.profile, runtime / 'portable', dirs_exist_ok=True)
    (scratch / 'tmp').mkdir()
    (scratch / 'qml').mkdir()
    env = {key: value for key, value in os.environ.items() if not key.startswith('VLC_PLAYER_DIAGNOSTICS')}
    env.pop('VLC_PLUGIN_PATH', None)
    env.update(TEMP=str(scratch / 'tmp'), TMP=str(scratch / 'tmp'), VLC_DATA_PATH=str(runtime),
        VLC_USERDATA_PATH=str(runtime / 'portable'), QML_DISK_CACHE_PATH=str(scratch / 'qml'),
        QT_DISABLE_SHADER_DISK_CACHE='1', QSG_RHI_DISABLE_SHADER_DISK_CACHE='1', QT_FORCE_STDERR_LOGGING='1')
    command = [str(runtime / 'vlc.exe'), '--intf=qt', '--no-one-instance', '--qt-playback-engine=vlc',
        '--media-library', '--no-save-recentplay', '--restore-playback-pos=0', '--no-plugins-cache',
        '--no-qt-privacy-ask', '--no-qt-updates-notif', '--no-metadata-network-access',
        '--no-qt-video-autoresize', '--no-video-title-show', '--no-volume-save', '--mmdevice-volume=0',
        '--play-and-exit', '--file-logging', '--log-verbose=2', '--logfile=' + str(scratch / 'native.log'), str(args.fixture)]
    (scratch / 'launch-argv.json').write_text(json.dumps(command, indent=2) + '\n')
    with (scratch / 'stdout').open('wb') as out, (scratch / 'stderr').open('wb') as err:
        player = IsolatedProcess(command, cwd=runtime, env=env, stdout=out, stderr=err)
        code = player.wait()
    result = {'schema': 'vlc_redesign.medialibrary_upgrade.v1', 'passed': False,
        'exit_code': code, 'input_desktop_preserved': True, 'before': baseline,
        'inspection': 'Native library opens the real old profile. Stock SQLite reads stored rows only; no substitute FILENAME collation or integrity-check claim.'}
    try:
        log = (scratch / 'native.log').read_text(encoding='utf-8', errors='replace')
        assert code == 0 and 'EOF reached' in log and 'QApp exec() finished' in log
        assert 'using medialibrary module "medialibrary"' in log and 'Received first picture' in log
        current = database_state(runtime / 'portable')
        result['after'] = current
        # The pinned0.14.1 migration38->39 updates only db_model_version.
        # Preserve media/file identities, history and every other setting.
        assert len(baseline['settings']) == len(current['settings']) == 1
        assert baseline['settings'][0][0] == 38 and current['settings'][0][0] == 39
        assert current['settings'][0][1:] == baseline['settings'][0][1:]
        assert current['media'] == baseline['media'] and current['files'] == baseline['files']
        assert hashlib.sha256((args.profile / 'ml/ml.db').read_bytes()).hexdigest() == original
        result.update(after=current, original_seed_unchanged=True,
            schema_change_required=current['settings'][0][0] != baseline['settings'][0][0], passed=True)
    finally:
        (scratch / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
        print(json.dumps(result), flush=True)


if __name__ == '__main__':
    main()
