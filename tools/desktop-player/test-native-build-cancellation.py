#!/usr/bin/env python3
"""Prove hosted build cancellation retires configure-like descendants."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--role', choices=('test', 'supervisor', 'child', 'grandchild'), default='test')
    parser.add_argument('--receipt', type=Path)
    args = parser.parse_args()
    if args.role == 'grandchild':
        print('READY ' + json.dumps({'pid': os.getpid(), 'group': os.getpgrp()}), flush=True)
        signal.pause()
        return
    if args.role == 'child':
        subprocess.run([sys.executable, __file__, '--role', 'grandchild'], check=True)
        return
    if args.role == 'supervisor':
        spec = importlib.util.spec_from_file_location('native_build', HERE / 'build-native.py')
        build = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(build)
        try:
            build.run(sys.executable, __file__, '--role', 'child')
        except build.NativeBuildCancelled as error:
            raise SystemExit(128 + error.signum)
        raise RuntimeError('Cancellation did not interrupt the owned command')
    if args.receipt is None:
        parser.error('--receipt is required for the native cancellation test')
    process = subprocess.Popen([sys.executable, __file__, '--role', 'supervisor'],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    lines = []
    for line in process.stdout:
        lines.append(line)
        if line.startswith('READY '):
            ready = json.loads(line.removeprefix('READY '))
            break
    else:
        process.wait()
        raise RuntimeError('Descendant did not become ready: ' + ''.join(lines))
    process.send_signal(signal.SIGTERM)
    lines.extend(process.stdout.readlines())
    code = process.wait()
    expected = 'NATIVE COMMAND GROUP EXITED ' + str(ready['group'])
    if code != 128 + signal.SIGTERM or expected not in ''.join(lines):
        raise RuntimeError('Cancellation ownership failed: ' + ''.join(lines))
    members = []
    for line in subprocess.check_output(['ps', '-axo', 'pid=,pgid=,stat='], text=True).splitlines():
        pid, group, state = line.split()
        if int(group) == ready['group'] and not state.startswith('Z'):
            members.append(int(pid))
    if members:
        raise RuntimeError('Owned descendants remain active: ' + str(members))
    args.receipt.write_text(json.dumps({'passed': True, 'exit_code': code,
        'group': ready['group'], 'active_descendants': members,
        'synchronization': 'descendant ready event, SIGTERM, native exit events; no deadline'}, indent=2) + '\n')
    print('Native command cancellation verified:', args.receipt, flush=True)


if __name__ == '__main__':
    main()
