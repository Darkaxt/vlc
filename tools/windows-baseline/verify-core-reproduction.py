"""Verify the freshly reproduced, unchanged baseline core before the UI build.

The existing native helper decodes real video/audio through its output callbacks.
This gate does not claim Qt presentation or hardware audio; those are separate.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime', required=True, type=Path)
    parser.add_argument('--fixture-source', required=True, type=Path)
    parser.add_argument('--scratch', required=True, type=Path)
    args = parser.parse_args()
    runtime, scratch = args.runtime.resolve(), args.scratch.resolve()
    assert scratch.drive.upper() == 'D:' and scratch.parent.name.startswith('vlc-s7-') and not scratch.exists()
    assert args.fixture_source.is_file()
    scratch.mkdir()
    (scratch / 'tmp').mkdir()
    environment = dict(os.environ, TEMP=str(scratch / 'tmp'), TMP=str(scratch / 'tmp'), VLC_DATA_PATH=str(runtime))
    environment.pop('VLC_PLUGIN_PATH', None)
    fixture = scratch / 'baseline-core.mp4'
    command = ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-i', str(args.fixture_source.resolve()),
        '-t', '12', '-map', '0:v:0', '-map', '0:a:0', '-c', 'copy', str(fixture)]
    with (scratch / 'fixture.log').open('wb') as log:
        subprocess.run(command, env=environment, stdout=log, stderr=log, check=True, creationflags=subprocess.CREATE_NO_WINDOW)
    record = {'schema': 'vlc_redesign.s7_baseline_core_reproduction.v1',
        'upstream_revision': '392bc1d0abdb7396b6c97fef206efa1d23868e19',
        'scope': 'Fresh unchanged baseline core, native decoded picture/audio callbacks, expected missing-input negative control and actual module/option metadata. No Qt presentation or hardware-audio claim.'}
    for name, arguments, expected_exit in [('decoded-media', [str(runtime / 'playback-check.exe'), str(fixture)], 0),
            ('missing-media', [str(runtime / 'playback-check.exe'), str(scratch / 'intentionally-missing.mp4')], 1),
            ('inventory', [str(runtime / 'inventory.exe')], 0)]:
        with (scratch / (name + '.stdout')).open('wb') as out, (scratch / (name + '.stderr')).open('wb') as err:
            result = subprocess.run(arguments, cwd=runtime, env=environment, stdout=out, stderr=err,
                creationflags=subprocess.CREATE_NO_WINDOW)
        stdout = (scratch / (name + '.stdout')).read_text(encoding='utf-8', errors='replace')
        stderr = (scratch / (name + '.stderr')).read_text(encoding='utf-8', errors='replace')
        assert result.returncode == expected_exit, (name, result.returncode, stdout, stderr[-2000:])
        assert 'cannot load plug-in' not in stderr, stderr
        value = json.loads(stdout)
        if name == 'inventory':
            assert '392bc1d' in value['changeset'], value['changeset']
            (scratch / 'native-inventory.json').write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')
            value = {key: value[key] for key in ('version', 'compiler', 'changeset')}
        else:
            assert value['passed'] == (expected_exit == 0) and value['error'] == (expected_exit == 1), value
        record[name] = {'exit_code': result.returncode, 'observed': value}
    record['runtime_hashes'] = {name: hashlib.sha256((runtime / name).read_bytes()).hexdigest()
        for name in ('libvlc.dll', 'libvlccore.dll', 'playback-check.exe', 'inventory.exe')}
    record['fixture_sha256'] = hashlib.sha256(fixture.read_bytes()).hexdigest()
    record['passed'] = True
    (scratch / 'result.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(record, indent=2), flush=True)


if __name__ == '__main__':
    main()
