#!/usr/bin/env python3
"""Capture two live thread observations of a recovered normal Linux player.

Diagnostic only: no compiler, runtime substitution or package acceptance. The
five-second observation cadence requests stacks; it is not a playback deadline.
After the requested observations, retire only this owned debugger/process group.
"""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import platform
import re
import select
import selectors
import signal
import subprocess
import time

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('native_builder', HERE / 'build-native.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work', required=True, type=Path)
    parser.add_argument('--scratch', required=True, type=Path)
    args = parser.parse_args()
    if platform.system() != 'Linux' or os.environ.get('GITHUB_ACTIONS') != 'true':
        raise RuntimeError('Startup tracing requires the disposable hosted Linux runner')
    work = args.work.resolve()
    record = json.loads((work / 'package-output.json').read_text())
    recovery = json.loads((work / 'package-recovery.json').read_text())
    if not recovery.get('artifact_sha256_verified') or recovery['normal_source_commit'] != record['source_commit']:
        raise RuntimeError('Normal package recovery was not source/hash verified')
    packages = work / 'packages' / record['source_commit']
    apps = [path for path in packages.glob('Modern-VLC-Fork-*-linux-*') if path.is_dir()]
    if Path(record['directory']).resolve() != packages or len(apps) != 1:
        raise RuntimeError('Expected one recovered normal generation')
    app = apps[0]
    args.scratch.mkdir(parents=True, exist_ok=False)
    fixture = args.scratch / 'natural-eof.mkv'
    builder.run('ffmpeg', '-hide_banner', '-loglevel', 'error', '-f', 'lavfi', '-i',
        'testsrc2=size=320x180:rate=30', '-f', 'lavfi', '-i', 'sine=frequency=600',
        '-t', '1', '-c:v', 'libx264', '-preset', 'ultrafast', '-threads', '1', '-c:a', 'aac', fixture)
    env = dict(os.environ, HOME=str(args.scratch / 'home'),
        XDG_CONFIG_HOME=str(args.scratch / 'config'), XDG_DATA_HOME=str(args.scratch / 'data'),
        XDG_CACHE_HOME=str(args.scratch / 'cache'))
    Path(env['HOME']).mkdir()
    argv = [str(app / 'modern-vlc'), '--no-qt-privacy-ask', '--no-metadata-network-access',
        '--restore-playback-pos=0', '--qt-playback-engine=vlc', '--play-and-exit', '--verbose=2', str(fixture)]
    result = {'purpose': 'Known normal startup stall: thread-stack diagnosis, not acceptance',
        'normal_source_commit': record['source_commit'], 'verifier_commit': os.environ['GITHUB_SHA'],
        'artifact_sha256_verified': recovery['artifact_sha256_verified'], 'compiler_invoked': False,
        'launcher_sha256': builder.sha(app / 'modern-vlc'), 'executable_sha256': builder.sha(app / 'bin/vlc'),
        'argv': argv, 'stack_observations': [], 'normal_exit': False, 'package_qualified': False}
    previous = {sig: signal.signal(sig, builder.cancel_build) for sig in (signal.SIGINT, signal.SIGTERM)}
    process = subprocess.Popen(['gdb', '--quiet', '--nx', '--interpreter=mi2'], env=env,
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, start_new_session=True)
    token, stack_token = 0, None
    next_observation = None
    interrupted = False
    running = False
    theme_announcements = 0
    inferior_fd = None
    buffer = b''
    started = time.monotonic()

    def send(command):
        nonlocal token
        token += 1
        process.stdin.write((str(token) + command + '\n').encode())
        process.stdin.flush()
        return token

    try:
        for command in ('-gdb-set pagination off', '-gdb-set confirm off', '-gdb-set mi-async on',
                '-interpreter-exec console "set debuginfod enabled off"',
                '-interpreter-exec console "set print thread-events off"',
                '-interpreter-exec console "handle SIGSTOP stop print nopass"',
                '-file-exec-and-symbols "/bin/sh"',
                '-exec-arguments ' + ' '.join(json.dumps(arg) for arg in argv)):
            send(command)
        send('-exec-run')
        finished = False
        with (args.scratch / 'gdb-mi.log').open('wb') as log, selectors.DefaultSelector() as events:
            events.register(process.stdout, selectors.EVENT_READ)
            while not finished:
                interval = None if next_observation is None else max(0, next_observation - time.monotonic())
                readable = events.select(interval)
                if not readable:
                    # This timer collects an observation; expiry does not judge or
                    # cancel the application, and the first observation resumes it.
                    if inferior_fd is None:
                        raise RuntimeError('No bound inferior process for the debug observation')
                    # VLC blocks SIGINT until interface startup completes, so
                    # MI exec-interrupt can acknowledge without stopping it.
                    # A pidfd-bound SIGSTOP is unmaskable; GDB consumes it and
                    # does not reinject it when the observation resumes.
                    signal.pidfd_send_signal(inferior_fd, signal.SIGSTOP)
                    interrupted, next_observation = True, None
                    continue
                chunk = os.read(process.stdout.fileno(), 65536)
                if not chunk:
                    raise RuntimeError('Debugger exited before its requested observations')
                log.write(chunk); log.flush()
                buffer += chunk
                while b'\n' in buffer:
                    raw, buffer = buffer.split(b'\n', 1)
                    line = raw.decode('utf-8', errors='backslashreplace')
                    print(line, flush=True)
                    if re.match(r'^\d+\^error', line):
                        raise RuntimeError('GDB command failed: ' + line)
                    if match := re.match(r'^=thread-group-started,id="i1",pid="(\d+)"', line):
                        if inferior_fd is not None:
                            raise RuntimeError('Debugger unexpectedly replaced its inferior process')
                        result['inferior_pid'] = int(match[1])
                        inferior_fd = os.pidfd_open(result['inferior_pid'])
                    if 'using qt theme provider module' in line:
                        theme_announcements += 1
                        if theme_announcements >= 2 and running and not interrupted:
                            next_observation = time.monotonic() + 5
                    if line.startswith('*running'):
                        running = True
                        if theme_announcements >= 2 and next_observation is None and not interrupted:
                            next_observation = time.monotonic() + 5
                    if line.startswith('*stopped'):
                        running = False
                        next_observation = None
                        if 'reason="exited' in line:
                            result['normal_exit'] = 'reason="exited-normally"' in line
                            result['terminal_event'] = line
                            finished = True
                            break
                        result['stack_observations'].append({'elapsed_seconds': time.monotonic() - started,
                            'theme_announcements': theme_announcements,
                            'event': line, 'requested_health_observation': interrupted})
                        stack_token = send('-interpreter-exec console "thread apply all bt"')
                    if stack_token is not None and line.startswith(str(stack_token) + '^done'):
                        if len(result['stack_observations']) == 2 or not interrupted:
                            finished = True
                            break
                        interrupted = False
                        stack_token = None
                        send('-exec-continue')
    except BaseException as error:
        result['failure'] = repr(error)
        raise
    finally:
        for sig in previous:
            signal.signal(sig, signal.SIG_IGN)
        if inferior_fd is not None:
            if not select.select([inferior_fd], [], [], 0)[0]:
                signal.pidfd_send_signal(inferior_fd, signal.SIGKILL)
            select.select([inferior_fd], [], [])
            os.close(inferior_fd)
            result['owned_inferior_exit_verified'] = True
        # The existing native cancellation helper owns this exact new process
        # group and verifies its exit. Diagnostic completion is not media EOF.
        builder.stop_command(process)
        result['owned_debugger_group_exited'] = True
        result['gdb_log_sha256'] = builder.sha(args.scratch / 'gdb-mi.log')
        (args.scratch / 'diagnosis.json').write_text(json.dumps(result, indent=2) + '\n')
        for sig, handler in previous.items():
            signal.signal(sig, handler)


if __name__ == '__main__':
    main()
