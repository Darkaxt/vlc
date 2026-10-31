"""One resumable S8 assembly, with durable step state and full compiler logs.

Run inside the pinned toolchain through the installed WSL gate. A failed process
ends this invocation; its owner diagnoses the saved log, fixes the cause and
resumes the same pipeline. This does not run product acceptance or publish.
"""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import resource
import subprocess
import sys
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=Path('/work/src'))
    parser.add_argument('--build', type=Path, default=Path('/work/build/win64'))
    parser.add_argument('--runtime', type=Path, default=Path('/scratch/runtime'))
    parser.add_argument('--state', type=Path, default=Path('/scratch/compilation/state.json'))
    parser.add_argument('--mode', choices=['diagnostics-mpv', 'normal-mpv'], default='diagnostics-mpv',
        help='Use the same pipeline for integrated acceptance or the final normal player')
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument('--from-step')
    selection.add_argument('--resume', action='store_true')
    parser.add_argument('--after-interruption', type=Path,
        help='Reconcile the original closed, empty-group supervisor report before resuming')
    parser.add_argument('--replace-mpv-buildinfo-sha256',
        help='Identity-bound refresh of the task-owned runtime after a dependency repair')
    args = parser.parse_args()
    cgroup = Path('/proc/self/cgroup').read_text().split('::', 1)[1].strip()
    assert cgroup.startswith('/llm-coordinator/'), 'Use the installed WSL gate'
    tools = args.source / 'tools/windows-player'
    sh = lambda name, *values: ['/bin/sh', str(tools / name), *map(str, values)]
    py = lambda name, *values: [sys.executable, '-B', str(tools / name), *map(str, values)]
    runtime_recipe = lambda phase: sh('build-mpv-runtime.sh', phase)
    steps = [
        ('sdk-network', sh('rebuild-qt-network.sh')),
        ('sdk-lifetimes', sh('rebuild-qt-timers.sh')),
        ('mpv-setup', runtime_recipe('setup')),
        ('shaderc', runtime_recipe('shaderc')),
        ('spirv-cross', runtime_recipe('spirv-cross')),
        ('libplacebo', runtime_recipe('placebo')),
        ('ffmpeg', runtime_recipe('ffmpeg')),
        ('mpv', runtime_recipe('mpv')),
        ('runtime', py('stage-built-mpv-runtime.py', '--prefix', '/work/mpv-runtime/prefix',
            '--inputs', '/scratch/mpv-source-inputs', '--runtime', args.runtime,
            *(['--replace-buildinfo-sha256', args.replace_mpv_buildinfo_sha256]
              if args.replace_mpv_buildinfo_sha256 else []))),
        ('notices', py('inventory-dependency-notices.py', '--sources', '/scratch/mpv-source-inputs',
            '--merge-existing', args.runtime / 'licenses/dependencies', '--output', '/scratch/dependency-notices-s8',
            *(['--verify-existing'] if Path('/scratch/dependency-notices-s8/manifest.json').is_file() else []))),
        ('release-compiler-cache', py('cache-toolchain.py', 'release')),
        ('configure-player', py('configure-player.py', '--source', args.source, '--build', args.build, '--verify-only')
            if (args.build / 'config.status').is_file()
            else sh('initialize-player-build.sh', args.source, args.build, args.runtime)),
        ('player', sh('build-player.sh', args.mode, args.source, args.build, args.runtime)),
    ]
    names = [name for name, _ in steps]
    state = json.loads(args.state.read_text()) if args.state.exists() else {
        'schema': 'vlc_redesign.compilation_pipeline.v1', 'attempts': [], 'steps': {}}
    assert state['schema'] == 'vlc_redesign.compilation_pipeline.v1'
    if args.after_interruption:
        assert args.resume and state.get('status') in ('running', 'failed')
        report_bytes = args.after_interruption.read_bytes()
        report = json.loads(report_bytes)
        assert report['populated'] is False and report['command_started'] is True
        assert report['exit_code'] != 0, 'Inspect an uncertain successful outcome instead of replaying it'
        assert state['attempts'][-1]['cgroup'] == '/llm-coordinator/' + report['id']
        assert state['steps'][state['current_step']]['run'] == state['attempts'][-1]['run']
        interruption = {'ticket_id': report['id'], 'supervisor_exit_code': report['exit_code'],
            'report_sha256': hashlib.sha256(report_bytes).hexdigest(),
            'populated': False, 'memory_events': report['memory_events']}
        state.setdefault('interruptions', []).append(interruption)
        state['steps'][state['current_step']]['interruption'] = interruption
        if state['status'] == 'running':
            state['steps'][state['current_step']]['status'] = 'interrupted'
            state['status'] = 'failed'
    if args.resume:
        assert state.get('status') == 'failed', 'Inspect an interrupted/running pipeline before recovery'
        assert state['attempts'][-1].get('mode', 'diagnostics-mpv') == args.mode, 'Resume the original build mode'
        start = names.index(state['current_step'])
    else:
        assert args.from_step in names, names
        start = names.index(args.from_step)
    if start > names.index('mpv-setup'):
        for artifact in ('/work/build/contrib/x86_64-w64-mingw32/lib/libQt6Network.a',
                         '/work/runtime-crt-only/dllcrt2.o', '/work/mpv-runtime/cross.meson'):
            assert Path(artifact).is_file(), artifact
    args.state.parent.mkdir(parents=True, exist_ok=True)
    run = len(state['attempts']) + 1
    log_root = args.state.parent / ('run-%04d' % run)
    recipes = ('compilation-pipeline.py', 'build-mpv-runtime.sh', 'build-player.sh',
        'cache-toolchain.py', 'qt-objects.mk', 'rebuild-qt-network.sh', 'rebuild-qt-timers.sh',
        'stage-built-mpv-runtime.py', 'inventory-dependency-notices.py', 'install-ffmpeg-files.py',
        'initialize-player-build.sh', 'configure-player.py', 'check-mpv-plugin-abi.py')
    identity = {str(path.relative_to(args.source)): hashlib.sha256(path.read_bytes()).hexdigest()
                for path in [*(tools / name for name in recipes),
                             args.source / 'modules/gui/qt/player/mpv/source.json']}
    log_root.mkdir()
    attempt = {'run': run, 'from_step': names[start], 'mode': args.mode, 'inputs': identity,
        'player_compile_cache': os.environ.get('VLC_PLAYER_COMPILE_CACHE', '1'),
        'player_compile_cache_reason': os.environ.get('VLC_PLAYER_COMPILE_CACHE_REASON'),
        'replace_mpv_buildinfo_sha256': args.replace_mpv_buildinfo_sha256,
        'started_at': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'cgroup': cgroup,
        'source_head': subprocess.check_output(['git', '-C', str(args.source), 'rev-parse', 'HEAD'], text=True).strip(),
        'steps': {}}
    state['attempts'].append(attempt)
    for name in names[:start]:
        state['steps'].setdefault(name, {'status': 'retained',
            'reason': 'Explicit continuation with existing prerequisites; not a product acceptance claim'})

    def save():
        attempt['status'] = state['status']
        temporary = args.state.with_suffix('.pending')
        temporary.write_text(json.dumps(state, indent=2) + '\n')
        temporary.replace(args.state)
        run_pending = log_root / 'attempt.pending'
        run_pending.write_text(json.dumps(attempt, indent=2) + '\n')
        run_pending.replace(log_root / 'attempt.json')

    environment = dict(os.environ, JOBS='1', CMAKE_BUILD_PARALLEL_LEVEL='1', CARGO_BUILD_JOBS='1')
    state.update(status='preparing', current_step=names[start])
    save()
    if start < names.index('release-compiler-cache'):
        print('PIPELINE preparing bounded compiler cache', flush=True)
        cache_began = time.monotonic()
        cache_before = resource.getrusage(resource.RUSAGE_CHILDREN)
        with (log_root / 'compiler-cache.log').open('w') as log:
            cache_options = ['--mpv-build'] if names[start] == 'mpv' else []
            code = subprocess.call(py('cache-toolchain.py', 'create', *cache_options),
                env=environment, stdout=log, stderr=subprocess.STDOUT)
        cache_after = resource.getrusage(resource.RUSAGE_CHILDREN)
        attempt['cache_preparation'] = {'exit_code': code, 'log': str(log_root / 'compiler-cache.log'),
            'wall_seconds': time.monotonic() - cache_began,
            'cpu_seconds': cache_after.ru_utime + cache_after.ru_stime - cache_before.ru_utime - cache_before.ru_stime}
        if code:
            state.update(status='failed', current_step=names[start], cache_error_log=str(log_root / 'compiler-cache.log'))
            save()
            print('PIPELINE compiler cache failed | see ' + str(log_root / 'compiler-cache.log'), flush=True)
            return code
    for index, (name, argv) in enumerate(steps[start:], start=start):
        log = log_root / (name + '.log')
        row = {'status': 'running', 'run': run, 'argv': argv, 'log': str(log)}
        state.update(status='running', current_step=name)
        state['steps'][name] = row
        attempt['steps'][name] = row
        save()
        print('PIPELINE [%d/%d] START %s | log=%s' % (index + 1, len(steps), name, log), flush=True)
        before = resource.getrusage(resource.RUSAGE_CHILDREN)
        began = time.monotonic()
        with log.open('w', buffering=1) as output:
            process = subprocess.Popen(argv, env=environment, stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, text=True, errors='replace', bufsize=1)
            for count, line in enumerate(process.stdout, 1):
                output.write(line)
                if count % 100 == 0 or any(word in line.lower() for word in ('error:', 'failed:', 'undefined reference')):
                    output.flush()
                    print('PIPELINE %s | %s' % (name, line.rstrip()), flush=True)
            process.stdout.close()
            code = process.wait()
        after = resource.getrusage(resource.RUSAGE_CHILDREN)
        row.update(status='done' if code == 0 else 'failed', exit_code=code,
            wall_seconds=time.monotonic() - began,
            cpu_seconds=after.ru_utime + after.ru_stime - before.ru_utime - before.ru_stime)
        state['status'] = 'running' if code == 0 else 'failed'
        save()
        print('PIPELINE %s %s | exit=%d wall=%.1fs cpu=%.1fs' %
              (name, row['status'].upper(), code, row['wall_seconds'], row['cpu_seconds']), flush=True)
        if code:
            return code
    state.update(status='complete', current_step=None,
        acceptance='Assembly complete; integrated S8 acceptance and normal release delivery remain required')
    save()
    print('PIPELINE ASSEMBLY COMPLETE | stage acceptance remains pending', flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
