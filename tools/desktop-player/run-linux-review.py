#!/usr/bin/env python3
"""Own the hosted Linux review's compositor, window manager and audio daemon.

Invoke through xvfb-run on a disposable native runner, never on a user's
desktop. Manager-selection events establish readiness without timing guesses.
"""
import argparse
import json
import os
from pathlib import Path
import select
import selectors
import signal
import subprocess
import sys

from Xlib import X, display

HERE = Path(__file__).resolve().parent


def wait_for_managers(connection, atoms, events, observe):
    previous = None
    while True:
        while connection.pending_events():
            connection.next_event()
        owners = [connection.get_selection_owner(atom) for atom in atoms]
        identities = [owner.id if owner else 0 for owner in owners]
        if identities != previous:
            observe(identities)
            previous = identities
        if all(owners):
            return identities
        # Reply requests above may read X events into python-xlib's own queue.
        # The socket can then be empty; consume that queue before selecting it.
        if connection.pending_events():
            continue
        for key, _ in events.select():
            if key.data != 'x11':
                raise RuntimeError('Owned Linux manager exited before readiness: ' + key.data)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work', required=True, type=Path)
    parser.add_argument('--review-root', required=True, type=Path)
    parser.add_argument('--packages-only', action='store_true',
        help='Verify recovered immutable packages without building a diagnostic Qt module')
    args = parser.parse_args()
    session = args.review_root.with_name(args.review_root.name + '-session')
    session.mkdir(parents=True, exist_ok=False)
    runtime = session / 'runtime'; runtime.mkdir(mode=0o700)
    home = session / 'home'; home.mkdir()
    env = os.environ.copy()
    env.update(HOME=str(home), XDG_RUNTIME_DIR=str(runtime),
        PULSE_RUNTIME_PATH=str(runtime / 'pulse'),
        PULSE_SERVER='unix:' + str(runtime / 'pulse/native'),
        LIBGL_ALWAYS_SOFTWARE='1', LP_NUM_THREADS='1',
        MESA_SHADER_CACHE_DIR=str(session / 'mesa-cache'))
    connection = display.Display()
    root = connection.screen().root
    root.change_attributes(event_mask=X.StructureNotifyMask)
    connection.sync()
    atoms = [connection.intern_atom(name) for name in ('WM_S0', '_NET_WM_CM_S0')]
    if any(connection.get_selection_owner(atom) for atom in atoms):
        raise RuntimeError('The disposable X server already has a manager owner')
    # Observe the selections themselves, including compositors that do not
    # announce ownership through a root-window MANAGER ClientMessage.
    from Xlib.ext import xfixes
    if not connection.has_extension('XFIXES'):
        raise RuntimeError('Owned Linux display requires XFIXES selection notifications')
    connection.xfixes_query_version()
    for atom in atoms:
        connection.xfixes_select_selection_input(root, atom,
            xfixes.XFixesSetSelectionOwnerNotifyMask |
            xfixes.XFixesSelectionWindowDestroyNotifyMask |
            xfixes.XFixesSelectionClientCloseNotifyMask)
    connection.sync()
    children = []
    descriptors = []
    logs = []
    pulse_fd = None
    try:
        with selectors.DefaultSelector() as events:
            events.register(connection.fileno(), selectors.EVENT_READ, 'x11')
            for name, argv in [('openbox', ['openbox', '--sm-disable']),
                               ('compositor', ['xcompmgr', '-n'])]:
                log = (session / (name + '.log')).open('wb'); logs.append(log)
                child = subprocess.Popen(argv, env=env, stdout=log, stderr=log)
                children.append(child)
                descriptor = os.pidfd_open(child.pid); descriptors.append(descriptor)
                events.register(descriptor, selectors.EVENT_READ, name)
            def observe(owners):
                record = {'manager_selections': dict(zip(('WM_S0', '_NET_WM_CM_S0'), owners)),
                          'owned_pids': [child.pid for child in children]}
                (session / 'display-readiness.json').write_text(json.dumps(record, indent=2) + '\n')
                print('LINUX DISPLAY ' + json.dumps(record), flush=True)
            owners = wait_for_managers(connection, atoms, events, observe)
            (session / 'display-ready.json').write_text(json.dumps({
                'display': os.environ['DISPLAY'], 'manager_selections': dict(zip(
                    ('WM_S0', '_NET_WM_CM_S0'), owners)),
                'owned_pids': [child.pid for child in children]}, indent=2) + '\n')
        # PulseAudio's daemon startup handshake returns only after its server
        # initialization. Its pid/runtime files belong to this fresh directory.
        subprocess.run(['pulseaudio', '--daemonize=yes', '--exit-idle-time=-1',
            '--use-pid-file=yes', '--log-target=file:' + str(session / 'pulse.log'), '-n',
            '--load=module-native-protocol-unix', '--load=module-null-sink sink_name=native_acceptance'],
            env=env, check=True)
        pulse_pid = int((runtime / 'pulse/pid').read_text().splitlines()[0])
        if Path('/proc/' + str(pulse_pid) + '/exe').resolve().name != 'pulseaudio':
            raise RuntimeError('Private PulseAudio PID does not identify its daemon')
        pulse_fd = os.pidfd_open(pulse_pid)
        with (session / 'audio-ready.txt').open('w') as stream:
            subprocess.run(['pactl', 'info'], env=env, stdout=stream, check=True)
        subprocess.run([sys.executable, HERE / 'verify-linux-packages.py', '--work', args.work,
                        '--scratch', args.review_root.with_name('native-package-checks')], env=env, check=True)
        if not args.packages_only:
            subprocess.run([sys.executable, HERE / 'prepare-native-review.py', '--work', args.work,
                            '--review-root', args.review_root], env=env, check=True)
    finally:
        try:
            if pulse_fd is not None:
                if not select.select([pulse_fd], [], [], 0)[0]:
                    signal.pidfd_send_signal(pulse_fd, signal.SIGTERM)
                select.select([pulse_fd], [], [])
                os.close(pulse_fd)
        finally:
            for child in reversed(children):
                if child.poll() is None:
                    child.terminate()
                child.wait()
            for descriptor in descriptors:
                os.close(descriptor)
            for log in logs:
                log.close()
            connection.close()
        (session / 'session-exit.json').write_text(json.dumps({
            'owned_managers_exited': all(child.poll() is not None for child in children),
            'private_audio_exited': pulse_fd is not None}, indent=2) + '\n')


if __name__ == '__main__':
    main()
