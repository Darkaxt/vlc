#!/usr/bin/env python3
"""Verify the delivered Mac formats in disposable hosted-runner storage.

These are normal packages, without test hooks. Exact app identity binds both
formats to the normal app used to prepare the instrumented review. Its composed
picture/workflow evidence remains separate; each recovered normal app also runs
both VLC and MPV through natural media EOF.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import plistlib
import re
import shutil
import signal
import stat
import subprocess
import threading
import time


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def app_identity(app):
    records = {}
    for path in sorted(app.rglob('*')):
        relative = path.relative_to(app).as_posix()
        if path.is_symlink():
            if not path.resolve(strict=True).is_relative_to(app.resolve()):
                raise RuntimeError('App link escapes its bundle: ' + relative)
            records[relative] = {'link': os.readlink(path)}
        elif path.is_file():
            records[relative] = {'sha256': digest(path),
                'executable_bits': stat.S_IMODE(path.stat().st_mode) & 0o111}
    return records


def run(*argv, **kwargs):
    print('+', ' '.join(map(str, argv)), flush=True)
    return subprocess.run(list(map(str, argv)), check=True, **kwargs)


def diagnose_crash(argv, environment, case, app, prior_reports):
    """One stack-capture reproduction; never convert the failed launch to a pass."""
    command = ['xcrun', 'lldb', '--batch', '--no-lldbinit',
        '-o', 'settings set target.disable-aslr false', '-o', 'run',
        '-o', 'thread backtrace all', '-k', 'thread backtrace all',
        '-k', 'register read', '-k', 'image list', '-k', 'process kill', '--', *map(str, argv)]
    with (case / 'crash-lldb.log').open('wb') as stream:
        result = subprocess.run(command, cwd=app / 'Contents/MacOS', env=environment,
                                stdout=stream, stderr=subprocess.STDOUT)
    print((case / 'crash-lldb.log').read_text(errors='replace')[-18000:], flush=True)
    reports = []
    roots = {Path.home() / 'Library/Logs/DiagnosticReports',
             Path(environment['HOME']) / 'Library/Logs/DiagnosticReports'}
    executable = str(app / 'Contents/MacOS/vlc')
    for root in roots:
        for path in root.glob('vlc*'):
            if path in prior_reports or not path.is_file() or path.suffix not in ('.ips', '.crash'):
                continue
            text = path.read_text(errors='replace')
            if executable not in text:
                continue
            destination = case / 'crashes' / path.name
            destination.parent.mkdir(exist_ok=True)
            shutil.copy2(path, destination)
            reports.append({'file': destination.name, 'sha256': digest(destination)})
    (case / 'crash-diagnostics.json').write_text(json.dumps({
        'purpose': 'Capture stacks for the already failed normal launch; not a retry acceptance',
        'debugger_returncode': result.returncode, 'reports': reports}, indent=2) + '\n')


def trace_launch(argv, environment, case, app):
    """Stop at the original fault instead of hoping a later launch repeats it."""
    command = ['xcrun', 'lldb', '--batch', '--no-lldbinit',
        '-o', 'settings set target.disable-aslr false', '-o', 'run',
        '-k', 'thread backtrace all', '-k', 'register read', '-k', 'image list',
        '-k', 'process kill', '--', *map(str, argv)]
    trace = case / 'launch-lldb.log'
    with trace.open('wb') as stream:
        result = subprocess.run(command, cwd=app / 'Contents/MacOS', env=environment,
                                stdout=stream, stderr=subprocess.STDOUT)
    text = trace.read_text(errors='replace')
    exited = re.search(r'Process \d+ exited with status = 0 \(0x0+\)', text) is not None
    faulted = re.search(r'stop reason\s*=\s*(?:signal|EXC_)', text) is not None
    (case / 'traced-launch.json').write_text(json.dumps({
        'debugger_returncode': result.returncode, 'target_natural_exit_zero': exited,
        'target_faulted': faulted, 'log_sha256': digest(trace),
        'qualification': 'DIAGNOSTIC; does not clear an earlier untraced launch failure'}, indent=2) + '\n')
    if result.returncode or not exited or faulted:
        print(text[-20000:], flush=True)
        raise RuntimeError('Original traced Mac launch failed; inspect launch-lldb.log')
    return text


def core_observation(case):
    """Bind private core storage only on the disposable hosted Mac runner."""
    import resource
    root = os.environ.get('RUNNER_TEMP')
    if os.environ.get('GITHUB_ACTIONS') != 'true' or not root \
            or not case.resolve().is_relative_to(Path(root).resolve()):
        raise RuntimeError('Private core setup requires owned disposable hosted-runner scratch')
    pattern = subprocess.check_output(['/usr/sbin/sysctl', '-n', 'kern.corefile'], text=True).strip()
    enabled = subprocess.check_output(['/usr/sbin/sysctl', '-n', 'kern.coredump'], text=True).strip()
    if enabled not in ('0', '1'):
        raise RuntimeError('Unexpected native core capability: ' + enabled)
    soft, hard = resource.getrlimit(resource.RLIMIT_CORE)
    limit = 4 * 1024 ** 3 if hard == resource.RLIM_INFINITY else min(hard, 4 * 1024 ** 3)
    if limit <= 0:
        raise RuntimeError('Native core hard limit forbids child-only capture')
    result = {'pattern': str(case.resolve() / 'core.%P'),
              'original_settings': {'kern.corefile': pattern, 'kern.coredump': enabled},
              'modified': [], 'original_soft_limit': soft, 'hard_limit': hard,
              'child_soft_limit': limit, 'started_ns': time.time_ns(), 'user_host_settings_changed': False}
    (case / 'core-observer.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


def configure_core_observation(observation, restore=False):
    if restore:
        changes = [(key, observation['original_settings'][key])
                   for key in reversed(observation['modified'])]
    else:
        changes = [('kern.corefile', observation['pattern'])]
        if observation['original_settings']['kern.coredump'] != '1':
            changes.append(('kern.coredump', '1'))
    for key, value in changes:
        run('sudo', '-n', '/usr/sbin/sysctl', key + '=' + value, stdout=subprocess.DEVNULL)
        if not restore:
            observation['modified'].append(key)
        actual = subprocess.check_output(['/usr/sbin/sysctl', '-n', key], text=True).strip()
        if actual != value:
            raise RuntimeError('Hosted native core setting readback differs: ' + key)


def capture_native_core(pid, argv, case, observation):
    """Inspect the original dead child; never rerun it to manufacture a stack."""
    core = Path(observation['pattern'].replace('%P', str(pid)))
    result = dict(pid=pid, path=str(core), captured=False)
    if core.is_file() and not core.is_symlink() and core.stat().st_mtime_ns >= observation['started_ns']:
        retained = core
        result.update(captured=True, bytes=retained.stat().st_size, sha256=digest(retained))
        with (case / 'original-core-lldb.log').open('wb') as stream:
            diagnostic = subprocess.run(['xcrun', 'lldb', '--batch', '--no-lldbinit',
                '-c', str(retained), '-o', 'thread backtrace all', '-o', 'register read',
                '-o', 'image list', '--', str(argv[0])], stdout=stream, stderr=subprocess.STDOUT)
        result['debugger_returncode'] = diagnostic.returncode
        print((case / 'original-core-lldb.log').read_text(errors='replace')[-24000:], flush=True)
    (case / 'original-core.json').write_text(json.dumps(result, indent=2) + '\n')


def normal_launch(argv, environment, case, capture_core=False):
    """Keep normal file-backed output; capture only the original child's fault."""
    core = core_observation(case) if capture_core else None

    def child_setup():
        import resource
        resource.setrlimit(resource.RLIMIT_CORE, (core['child_soft_limit'], core['hard_limit']))

    try:
        if core:
            configure_core_observation(core)
        with (case / 'stdout.log').open('wb') as stdout, (case / 'stderr.log').open('wb') as stderr:
            if not core:
                run(*argv, env=environment, stdout=stdout, stderr=stderr)
                return
            clean_environment = {key: value for key, value in environment.items()
                if not any(word in key.upper() for word in ('TOKEN', 'SECRET', 'PASSWORD', 'CREDENTIAL'))}
            print('+', ' '.join(map(str, argv)), flush=True)
            # No pipe reader, debugger, new session, signal-mask change or
            # playback deadline: preserve the failed normal check's launch path.
            with subprocess.Popen(list(map(str, argv)), env=clean_environment,
                    stdout=stdout, stderr=stderr, preexec_fn=child_setup) as process:
                code = process.wait()
                if code < 0:
                    try:
                        capture_native_core(process.pid, argv, case, core)
                    except Exception as error:
                        (case / 'core-capture-error.json').write_text(json.dumps({
                            'pid':process.pid, 'normal_returncode':code,
                            'diagnostic_error':str(error)}, indent=2) + '\n')
                if code:
                    raise subprocess.CalledProcessError(code, list(map(str, argv)))
    finally:
        if core:
            configure_core_observation(core, restore=True)
            (case / 'core-settings-restored.json').write_text(json.dumps({
                'restored':True, 'original_settings':core['original_settings']}, indent=2) + '\n')


def observe_launch(argv, environment, case, capture_core=False):
    """Stream one diagnostic launch and sample it; never impose an exit deadline."""
    spec = importlib.util.spec_from_file_location('owned_native_build', Path(__file__).with_name('build-native.py'))
    owner = importlib.util.module_from_spec(spec); spec.loader.exec_module(owner)
    core = core_observation(case) if capture_core else None
    completed = threading.Event()
    signals = (signal.SIGINT, signal.SIGTERM)
    mask = signal.pthread_sigmask(signal.SIG_BLOCK, signals)
    previous = {sig: signal.signal(sig, owner.cancel_build) for sig in signals}
    process = None
    observer = None
    observer_started = False
    reaped = False

    def sample():
        # This cadence only requests a read-only stack observation. It neither
        # classifies playback nor stops, retries or changes the player.
        if capture_core or completed.wait(5) or process.poll() is not None:
            return
        trace = case / 'running-process-sample.txt'
        result = subprocess.run(['/usr/bin/sample', str(process.pid), '1', '1', '-file', str(trace)],
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        print('MAC NATIVE SAMPLE', process.pid, 'exit', result.returncode, result.stdout, flush=True)
        if trace.is_file():
            print(trace.read_text(errors='replace'), flush=True)

    def child_setup():
        if core:
            import resource
            resource.setrlimit(resource.RLIMIT_CORE, (core['child_soft_limit'], core['hard_limit']))
        signal.pthread_sigmask(signal.SIG_SETMASK, mask)

    try:
        if core:
            configure_core_observation(core)
        print('+ DIAGNOSTIC', ' '.join(map(str, argv)), flush=True)
        clean_environment = {key: value for key, value in environment.items()
            if not capture_core or not any(word in key.upper()
                for word in ('TOKEN', 'SECRET', 'PASSWORD', 'CREDENTIAL'))}
        process = subprocess.Popen(list(map(str, argv)), env=clean_environment, start_new_session=True,
            preexec_fn=child_setup,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, errors='replace', bufsize=1)
        observer = threading.Thread(target=sample, name='mac-native-stack-observation')
        observer.start()
        observer_started = True
        signal.pthread_sigmask(signal.SIG_SETMASK, mask)
        with (case / 'stderr.log').open('w', encoding='utf-8') as stream:
            for line in process.stdout:
                stream.write(line); stream.flush()
                print(line, end='', flush=True)
        # Keep the child PID reserved until the observer has finished sampling it.
        completed.set(); observer.join()
        code = process.wait()
        reaped = True
        if code < 0 and core:
            try:
                capture_native_core(process.pid, argv, case, core)
            except Exception as error:
                (case / 'core-capture-error.json').write_text(json.dumps({
                    'pid': process.pid, 'normal_returncode': code,
                    'diagnostic_error': str(error)}, indent=2) + '\n')
        if code:
            raise subprocess.CalledProcessError(code, list(map(str, argv)))
    except owner.NativeBuildCancelled:
        for sig in previous:
            signal.signal(sig, signal.SIG_IGN)
        completed.set()
        if observer_started:
            observer.join()
        if process is not None:
            owner.stop_command(process)
        raise
    except BaseException:
        completed.set()
        if observer_started:
            observer.join()
        if process is not None and not reaped:
            owner.stop_command(process)
        raise
    finally:
        completed.set()
        if observer_started:
            observer.join()
        for sig, handler in previous.items():
            signal.signal(sig, handler)
        signal.pthread_sigmask(signal.SIG_SETMASK, mask)
        if core:
            configure_core_observation(core, restore=True)
            (case / 'core-settings-restored.json').write_text(json.dumps({
                'restored': True, 'original_settings':core['original_settings']}, indent=2) + '\n')
    return (case / 'stderr.log').read_text(errors='replace')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work', required=True, type=Path)
    parser.add_argument('--scratch', required=True, type=Path)
    parser.add_argument('--trace-launch', action='store_true',
                        help='Capture the original process fault; diagnostic evidence, not untraced release clearance')
    parser.add_argument('--observe-launch', choices=('vlc', 'mpv'),
                        help='Diagnostic only: stream one ZIP launch and sample its running native threads')
    parser.add_argument('--capture-core', action='store_true',
                        help='Observe without attaching; retain the original child core on a native fault')
    parser.add_argument('--observe-count', type=int, choices=range(1, 13), default=1,
                        help='Bounded fresh-profile teardown census; stop at the first original fault')
    args = parser.parse_args()
    if args.observe_launch and args.trace_launch:
        parser.error('Select one diagnostic launch mechanism')
    if args.capture_core and args.trace_launch:
        parser.error('Core capture requires an untraced child')
    if args.observe_count != 1 and not args.observe_launch:
        parser.error('A launch census requires the diagnostic observation path')
    if platform.system() != 'Darwin':
        raise RuntimeError('Mac package verification requires a native Mac')
    record = json.loads((args.work / 'package-output.json').read_text())
    packages = Path(record['directory']).resolve()
    if not packages.is_relative_to((args.work / 'packages').resolve()):
        raise RuntimeError('Package pointer escaped its owned generation')
    reuse_path = args.work / 'review-reuse.json'
    reuse = json.loads(reuse_path.read_text()) if reuse_path.exists() else None
    if reuse and reuse['normal_source_commit'] != record['source_commit']:
        raise RuntimeError('Recovered normal app belongs to another source generation')
    normal = Path(reuse['normal_application']) if reuse else packages / 'Modern VLC.app'
    expected = app_identity(normal)
    args.scratch.mkdir(parents=True, exist_ok=False)
    fixture = args.scratch / 'natural-eof.mkv'
    run('ffmpeg', '-hide_banner', '-loglevel', 'error', '-f', 'lavfi', '-i',
        'testsrc2=size=320x180:rate=30', '-f', 'lavfi', '-i', 'sine=frequency=600',
        '-t', '1', '-c:v', 'libx264', '-preset', 'ultrafast', '-threads', '1', '-c:a', 'aac', fixture)
    results = []

    def verify(app, case, archive):
        case.mkdir()
        actual = app_identity(app)
        if actual != expected:
            different = sorted(key for key in set(actual) | set(expected)
                               if actual.get(key) != expected.get(key))
            raise RuntimeError('Recovered app differs from its normal package: ' + str(different))
        run('codesign', '--verify', '--deep', '--strict', app)
        engines = (args.observe_launch,) if args.observe_launch else ('vlc', 'mpv')
        for engine, attempt in ((engine, attempt) for engine in engines for attempt in range(args.observe_count)):
            name = engine if args.observe_count == 1 else engine + '-' + str(attempt + 1)
            engine_case = case / name; engine_case.mkdir()
            home = engine_case / 'home'; home.mkdir()
            env = dict(os.environ, HOME=str(home), XDG_CONFIG_HOME=str(home / 'config'),
                XDG_DATA_HOME=str(home / 'data'), XDG_CACHE_HOME=str(home / 'cache'),
                QML_DISK_CACHE_PATH=str(engine_case / 'qml-cache'), QT_FORCE_STDERR_LOGGING='1', QSG_INFO='1')
            argv = [app / 'Contents/MacOS/vlc', '--intf=qt', '--no-qt-privacy-ask',
                    '--no-metadata-network-access', '--restore-playback-pos=0',
                    '--qt-playback-engine=' + engine, '--play-and-exit', '--verbose=2', fixture]
            prior_reports = {path for root in (Path.home(), home)
                             for path in (root / 'Library/Logs/DiagnosticReports').glob('vlc*')}
            try:
                if args.trace_launch:
                    log = trace_launch(argv, env, engine_case, app)
                elif args.observe_launch:
                    log = observe_launch(argv, env, engine_case, capture_core=args.capture_core)
                else:
                    normal_launch(argv, env, engine_case, capture_core=args.capture_core)
            except subprocess.CalledProcessError as error:
                print((engine_case / 'stderr.log').read_text(errors='replace')[-10000:], flush=True)
                (engine_case / 'failure.json').write_text(json.dumps({'argv': list(map(str, argv)),
                    'normal_returncode': error.returncode, 'archive_sha256': digest(archive)}, indent=2) + '\n')
                if error.returncode < 0 and not args.capture_core:
                    diagnose_crash(argv, env, engine_case, app, prior_reports)
                raise
            if not args.trace_launch:
                log = (engine_case / 'stderr.log').read_text(errors='replace')
            marker = 'MPV natural EOF reached' if engine == 'mpv' else 'EOF reached'
            if marker not in log:
                raise RuntimeError('Normal packaged player did not report natural media EOF: ' + engine)
            results.append({'format': archive.suffix, 'engine': engine, 'archive_sha256': digest(archive),
                'source_commit': record['source_commit'], 'normal_bundle_members_identical': len(actual),
                'strict_signature_verified': True, 'normal_qt_playback_natural_eof_exit': 0,
                'launch_traced': args.trace_launch,
                'launch_observed': bool(args.observe_launch),
                'fresh_profile_attempt': attempt + 1,
                'qualification': 'DIAGNOSTIC ONLY' if args.trace_launch or args.observe_launch else 'normal untraced package playback',
                'stderr_sha256': digest(engine_case / ('launch-lldb.log' if args.trace_launch else 'stderr.log'))})
            (args.scratch / 'verification.json').write_text(json.dumps(results, indent=2) + '\n')

    archives = {suffix: sorted(packages.glob('*' + suffix)) for suffix in ('.zip', '.dmg')}
    archives['.zip'] = [path for path in archives['.zip']
                        if '-symbols' not in path.name and '-corresponding-source-' not in path.name]
    if any(len(paths) != 1 for paths in archives.values()):
        raise RuntimeError('Expected one normal ZIP and one DMG in the source generation')
    archive = archives['.zip'][0]
    unpacked = args.scratch / 'zip-extracted'
    run('ditto', '-x', '-k', archive, unpacked)
    verify(unpacked / 'Modern VLC.app', args.scratch / 'zip-runtime', archive)
    if args.observe_launch:
        return
    archive = archives['.dmg'][0]
    mount = args.scratch / 'dmg-mounted'; mount.mkdir()
    attached = run('hdiutil', 'attach', archive, '-readonly', '-nobrowse', '-noautoopen',
        '-mountpoint', mount, '-plist', stdout=subprocess.PIPE)
    entities = plistlib.loads(attached.stdout)['system-entities']
    mounted = [row for row in entities if row.get('mount-point') == str(mount)]
    if len(mounted) != 1:
        # Detach the explicitly requested mount even if its plist is unexpected.
        run('hdiutil', 'detach', mount)
        raise RuntimeError('Owned DMG mount was not uniquely identified')
    try:
        installed = args.scratch / 'dmg-installed/Modern VLC.app'
        installed.parent.mkdir()
        run('ditto', '--rsrc', '--extattr', mount / 'Modern VLC.app', installed)
        verify(installed, args.scratch / 'dmg-runtime', archive)
    finally:
        run('hdiutil', 'detach', mounted[0]['dev-entry'])


if __name__ == '__main__':
    main()
