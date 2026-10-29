"""Exercise actual vlc_pipe in two live processes with deterministic ownership.

The first worker retains its pipe handles until the second has created its own.
This reproduces cross-process namespace collisions without GUI, sleeps, retries
or replacement pipe implementations.
"""
import argparse
import ctypes as C
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


def worker(runtime):
    with os.add_dll_directory(str(runtime)):
        core = C.CDLL(str(runtime / 'libvlccore.dll'), use_last_error=True)
        pipe = core.vlc_pipe
        pipe.argtypes = [C.POINTER(C.c_int)]
        pipe.restype = C.c_int
        close = C.CDLL('msvcrt')._close
        close.argtypes = [C.c_int]
        descriptors, records = [], []
        try:
            for _ in range(2):
                pair = (C.c_int * 2)(-1, -1)
                C.set_last_error(0)
                result = pipe(pair)
                records.append({'return': result, 'winerror': C.get_last_error() if result else 0})
                if not result:
                    descriptors.extend(pair)
            passed = all(record['return'] == 0 for record in records)
            print(json.dumps({'pid': os.getpid(), 'pipes': records, 'passed': passed}), flush=True)
            assert sys.stdin.readline().strip() == 'release'
        finally:
            for descriptor in descriptors:
                assert close(descriptor) == 0
        return 0 if passed else 2


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime', required=True, type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--expect-collision', action='store_true')
    parser.add_argument('--worker', action='store_true')
    args = parser.parse_args()
    runtime = args.runtime.resolve()
    assert (runtime / 'libvlccore.dll').is_file()
    if args.worker:
        return worker(runtime)
    assert args.output and not args.output.exists()
    command = [sys.executable, '-B', str(Path(__file__).resolve()), '--runtime', str(runtime), '--worker']
    first = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, encoding='utf-8', creationflags=subprocess.CREATE_NO_WINDOW)
    report = {'schema': 'vlc_redesign.native_pipe_process_isolation.v1',
        'core_sha256': hashlib.sha256((runtime / 'libvlccore.dll').read_bytes()).hexdigest(),
        'expected_collision': args.expect_collision}
    try:
        report['first'] = json.loads(first.stdout.readline())
        assert report['first']['passed'], report['first']
        second = subprocess.run(command, input='release\n', capture_output=True, text=True,
            encoding='utf-8', creationflags=subprocess.CREATE_NO_WINDOW)
        report['second'] = json.loads(second.stdout)
        report['second_exit'] = second.returncode
        assert not second.stderr, second.stderr
        if args.expect_collision:
            report['passed'] = second.returncode == 2 and all(item['return'] == -1
                and item['winerror'] in (5, 231) for item in report['second']['pipes'])
        else:
            report['passed'] = second.returncode == 0 and report['second']['passed']
    finally:
        first.stdin.write('release\n')
        first.stdin.flush()
        report['first_exit'] = first.wait()
        assert not first.stderr.read()
        report['passed'] = report.get('passed', False) and report['first_exit'] == 0
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
        print(json.dumps(report), flush=True)
    assert report['passed'], report


if __name__ == '__main__':
    raise SystemExit(main())
