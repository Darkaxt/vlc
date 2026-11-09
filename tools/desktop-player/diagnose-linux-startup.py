#!/usr/bin/env python3
"""Capture live thread observations of a recovered normal Linux player.

Diagnostic only: no compiler, runtime substitution or package acceptance. The
five-second observation cadence requests stacks; it is not a playback deadline.
After the requested observations, retire only this owned debugger/process group.
MPV mode instead follows the finite clip through its actual exit or crash.
"""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import platform
import re
import resource
import select
import selectors
import signal
import subprocess
import time

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('native_builder', HERE / 'build-native.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


def untraced_shutdown(app, fixture, scratch, env, argv, result):
    """Observe the intermittent EOF fault without ptrace changing its timing.

    Twelve independent fresh profiles are a diagnostic census, never retries
    after a failure or package acceptance. Stop at the first failed process.
    Raw cores stay outside the uploaded evidence and die with this hosted VM.
    """
    if not Path('/proc/sys/kernel/core_pattern').is_file():
        raise RuntimeError('The owned Linux runner has no kernel core-dump interface')
    pattern_file = Path('/proc/sys/kernel/core_pattern')
    previous_pattern = pattern_file.read_text()
    private = scratch.with_name(scratch.name + '-private-cores')
    private.mkdir(mode=0o700)
    pattern = str(private / 'core.%p') + '\n'
    if '%' in str(private) or '\n' in str(private):
        raise RuntimeError('Private diagnostic core path contains kernel substitutions')
    result.update(purpose='Untraced normal MPV EOF shutdown crash census; not acceptance',
                  observations=[], maximum_observations=12, raw_cores_uploaded=False)
    # The normal player needs no CI credential. Never include a runner token
    # in its private core, even though that core is never uploaded.
    env = {key: value for key, value in env.items()
           if not any(word in key.upper() for word in ('TOKEN', 'SECRET', 'PASSWORD', 'CREDENTIAL'))}

    mask = signal.pthread_sigmask(signal.SIG_BLOCK, (signal.SIGINT, signal.SIGTERM))
    previous_handlers = {sig: signal.signal(sig, builder.cancel_build)
                         for sig in (signal.SIGINT, signal.SIGTERM)}
    signal.pthread_sigmask(signal.SIG_SETMASK, mask)

    def core_limit():
        signal.pthread_sigmask(signal.SIG_SETMASK, mask)
        resource.setrlimit(resource.RLIMIT_CORE, (resource.RLIM_INFINITY, resource.RLIM_INFINITY))

    try:
        subprocess.run(['sudo', '-n', 'tee', str(pattern_file)], input=pattern,
                       text=True, stdout=subprocess.DEVNULL, check=True)
        if pattern_file.read_text() != pattern:
            raise RuntimeError('Private hosted-runner core destination was not applied')
        for observation in range(result['maximum_observations']):
            case = scratch / ('launch-' + str(observation + 1))
            case.mkdir()
            launch_env = dict(env, HOME=str(case / 'home'), XDG_CONFIG_HOME=str(case / 'config'),
                XDG_DATA_HOME=str(case / 'data'), XDG_CACHE_HOME=str(case / 'cache'),
                QML_DISK_CACHE_PATH=str(case / 'qml-cache'))
            Path(launch_env['HOME']).mkdir()
            with (case / 'stdout.log').open('wb') as out, (case / 'stderr.log').open('wb') as err:
                player = None
                signal.pthread_sigmask(signal.SIG_BLOCK, (signal.SIGINT, signal.SIGTERM))
                try:
                    player = subprocess.Popen(argv, cwd=case, env=launch_env, stdout=out, stderr=err,
                                              start_new_session=True, preexec_fn=core_limit)
                    signal.pthread_sigmask(signal.SIG_SETMASK, mask)
                    code = player.wait()
                except builder.NativeBuildCancelled:
                    for sig in previous_handlers:
                        signal.signal(sig, signal.SIG_IGN)
                    if player is not None:
                        builder.stop_command(player)
                    raise
                finally:
                    signal.pthread_sigmask(signal.SIG_SETMASK, mask)
            stderr = (case / 'stderr.log').read_text(errors='replace')
            row = {'pid': player.pid, 'exit_code': code, 'natural_eof': 'MPV natural EOF reached' in stderr,
                   'mpv_released': 'MPV native resources released' in stderr,
                   'qt_exited': 'QApp exec() finished' in stderr,
                   'stderr_sha256': builder.sha(case / 'stderr.log')}
            result['observations'].append(row)
            print('NORMAL SHUTDOWN ' + json.dumps(row), flush=True)
            if code:
                core = private / ('core.' + str(player.pid))
                row['private_core_exists'] = core.is_file()
                if core.is_file():
                    builder.run('gdb', '--quiet', '--nx', '--batch',
                        '-ex', 'set debuginfod enabled off', '-ex', 'set pagination off',
                        '-ex', 'set logging file ' + str(scratch / 'gdb-mi.log'),
                        '-ex', 'set logging redirect on', '-ex', 'set logging enabled on',
                        '-ex', 'set print frame-arguments none', '-ex', 'thread apply all bt',
                        str(app / 'bin/vlc'), str(core), env=env)
                    row['debugger_exit'] = 0
                    result['gdb_log_sha256'] = builder.sha(scratch / 'gdb-mi.log')
                    result['owned_debugger_group_exited'] = True
                break
            if not all(row[key] for key in ('natural_eof', 'mpv_released', 'qt_exited')):
                raise RuntimeError('Untraced diagnostic exited without the requested EOF lifecycle')
        result['normal_exit'] = all(row['exit_code'] == 0 for row in result['observations'])
        result['owned_inferior_exit_verified'] = True
    finally:
        for sig in previous_handlers:
            signal.signal(sig, signal.SIG_IGN)
        subprocess.run(['sudo', '-n', 'tee', str(pattern_file)], input=previous_pattern,
                       text=True, stdout=subprocess.DEVNULL, check=True)
        result['hosted_core_pattern_restored'] = pattern_file.read_text() == previous_pattern
        (scratch / 'diagnosis.json').write_text(json.dumps(result, indent=2) + '\n')
        for sig, handler in previous_handlers.items():
            signal.signal(sig, handler)
        if not result['hosted_core_pattern_restored']:
            raise RuntimeError('Hosted-runner core pattern did not restore')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work', required=True, type=Path)
    parser.add_argument('--scratch', required=True, type=Path)
    parser.add_argument('--engine', choices=('vlc', 'mpv'), default='vlc')
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
        '--restore-playback-pos=0', '--qt-playback-engine=' + args.engine,
        '--play-and-exit', '--verbose=2', str(fixture)]
    result = {'purpose': ('Known normal startup stall' if args.engine == 'vlc' else
                         'Normal MPV EOF shutdown crash') + ': thread-stack diagnosis, not acceptance',
        'normal_source_commit': record['source_commit'], 'verifier_commit': os.environ['GITHUB_SHA'],
        'artifact_sha256_verified': recovery['artifact_sha256_verified'], 'compiler_invoked': False,
        'launcher_sha256': builder.sha(app / 'modern-vlc'), 'executable_sha256': builder.sha(app / 'bin/vlc'),
        'argv': argv, 'stack_observations': [], 'normal_exit': False, 'package_qualified': False}
    if args.engine == 'mpv':
        untraced_shutdown(app, fixture, args.scratch, env, argv, result)
        return
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
                        if args.engine == 'vlc' and theme_announcements >= 2 and running and not interrupted:
                            next_observation = time.monotonic() + 5
                    if line.startswith('*running'):
                        running = True
                        if args.engine == 'vlc' and theme_announcements >= 2 and next_observation is None and not interrupted:
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
        # GDB must handle its own ptrace exit stops before a pidfd can become
        # readable. Waiting for the inferior first deadlocks the observer.
        # communicate drains the MI pipe while GDB quits and retires its target.
        remaining, _ = process.communicate(input=(str(token + 1) + '-gdb-exit\n').encode())
        if remaining:
            with (args.scratch / 'gdb-mi.log').open('ab') as log:
                log.write(remaining)
            print(remaining.decode('utf-8', errors='backslashreplace'), flush=True)
        if inferior_fd is not None:
            select.select([inferior_fd], [], [])
            os.close(inferior_fd)
            result['owned_inferior_exit_verified'] = True
        # communicate reaped GDB; never signal its now reusable PID/group.
        members = [line for line in builder.output('ps', '-axo', 'pid=,pgid=,stat=').splitlines()
                   if int(line.split()[1]) == process.pid and not line.split()[2].startswith('Z')]
        if members or process.returncode != 0:
            raise RuntimeError('Debugger quit did not leave its owned group empty')
        result['owned_debugger_group_exited'] = True
        result['gdb_log_sha256'] = builder.sha(args.scratch / 'gdb-mi.log')
        (args.scratch / 'diagnosis.json').write_text(json.dumps(result, indent=2) + '\n')
        for sig, handler in previous.items():
            signal.signal(sig, handler)


if __name__ == '__main__':
    main()
