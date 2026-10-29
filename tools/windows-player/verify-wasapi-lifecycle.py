"""Record the deterministic native WASAPI reproduction or corrected regression.

The executable calls the actual compiled backend functions against controlled
COM events. This establishes ordering; real-device/player acceptance is separate.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--executable', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--expect-upstream-failure', action='store_true')
    args = parser.parse_args()
    executable, output = args.executable.resolve(), args.output.resolve()
    assert executable.drive.upper() == 'D:' and 'Temp' in executable.parts
    assert output.is_relative_to(executable.parent.parent)
    assert executable.name.startswith('wasapi-lifecycle-') and executable.suffix == '.exe'
    assert executable.is_file() and not output.exists()
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = executable.parent.parent / 'tmp'
    temporary.mkdir(exist_ok=True)
    with output.with_suffix('.stdout').open('wb') as out, output.with_suffix('.stderr').open('wb') as err:
        process = subprocess.run([str(executable)], cwd=executable.parent,
            env=dict(os.environ, TEMP=str(temporary), TMP=str(temporary)), stdout=out, stderr=err,
            creationflags=subprocess.CREATE_NO_WINDOW)
    stdout = output.with_suffix('.stdout').read_text(encoding='utf-8', errors='replace')
    stderr = output.with_suffix('.stderr').read_text(encoding='utf-8', errors='replace')
    results = [int(value) for value in re.findall(r'case=\S+ flush-before-resume=\d result=(\d+)', stdout)]
    reproduced = process.returncode == 23 and results == [23, 25, 23]
    corrected = process.returncode == 0 and results == [0, 0, 0]
    record = {'schema': 'vlc_redesign.wasapi_lifecycle_regression.v1',
        'executable_sha256': hashlib.sha256(executable.read_bytes()).hexdigest(),
        'exit_code': process.returncode, 'case_results': results, 'stdout': stdout, 'stderr': stderr,
        'upstream_failure_reproduced': reproduced, 'corrected_regression_passed': corrected,
        'scope': 'Actual WASAPI functions with controlled native COM and timer ordering. The test deliberately lacks an audio clock and does not establish hardware playback.',
        'libvlc_sha256': hashlib.sha256((executable.parent / 'libvlc.dll').read_bytes()).hexdigest(),
        'libvlccore_sha256': hashlib.sha256((executable.parent / 'libvlccore.dll').read_bytes()).hexdigest()}
    source_record = executable.with_suffix('.exe.source-sha256')
    if source_record.exists():
        record['compiled_source_hashes'] = source_record.read_text()
    output.write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(record, indent=2), flush=True)
    return 0 if (reproduced if args.expect_upstream_failure else corrected) else 1


if __name__ == '__main__':
    raise SystemExit(main())
