#!/usr/bin/env python3
"""Install and run the RPM inside the owned Fedora acceptance container."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('identity', HERE / 'verify-macos-packages.py')
identity = importlib.util.module_from_spec(spec)
spec.loader.exec_module(identity)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--uid', type=int, required=True)
    parser.add_argument('--gid', type=int, required=True)
    args = parser.parse_args()
    case = Path('/case')
    record = {'state': 'FAILED', 'os_release': Path('/etc/os-release').read_text(), 'engines': []}
    if 'ID=fedora' not in record['os_release']:
        raise RuntimeError('RPM acceptance requires the actual Fedora package database')
    if Path('/opt/modern-vlc').exists():
        raise RuntimeError('RPM container has a pre-existing player')
    try:
        subprocess.run(['dnf', '-y', '--setopt=max_parallel_downloads=1', 'install',
            'mesa-dri-drivers', 'mesa-libGL', 'mesa-libEGL', '/input/player.rpm'], check=True)
        expected = json.loads((case / 'expected-payload.json').read_text())
        actual = identity.app_identity(Path('/opt/modern-vlc'))
        if actual != expected:
            raise RuntimeError('Fedora-installed RPM payload differs from the qualified portable payload')
        record['installed_members_identical'] = len(actual)
        record['rpm'] = subprocess.check_output(['rpm', '-q', 'modern-vlc-fork'], text=True).strip()
        for engine in ('vlc', 'mpv'):
            # The container installer runs as root; playback runs as the hosted
            # runner UID against only its owned X/audio sockets and fresh home.
            home = case / (engine + '-home')
            home.mkdir()
            os.chown(home, args.uid, args.gid)
            env = dict(os.environ, HOME=str(home), XDG_CONFIG_HOME=str(home / 'config'),
                XDG_DATA_HOME=str(home / 'data'), XDG_CACHE_HOME=str(home / 'cache'),
                XDG_RUNTIME_DIR=str(home / 'runtime'), LIBGL_ALWAYS_SOFTWARE='1',
                LP_NUM_THREADS='1', QT_FORCE_STDERR_LOGGING='1')
            (home / 'runtime').mkdir(mode=0o700)
            os.chown(home / 'runtime', args.uid, args.gid)
            if engine == 'vlc':
                # Option registration requires loading the Qt module before
                # ordinary CLI errors can enable verbose logging. Record the
                # loader and registry without launching another player UI.
                plugin = Path('/opt/modern-vlc/lib/vlc/plugins/gui/libqt_plugin.so')
                with (case / 'qt-loader.txt').open('w') as stream:
                    result = subprocess.run(['ldd', '-r', str(plugin)], env=env,
                        stdout=stream, stderr=subprocess.STDOUT, text=True)
                    stream.write('\nloader_exit=' + str(result.returncode) + '\n')
                with (case / 'module-registry.txt').open('wb') as stream:
                    subprocess.run(['/usr/bin/modern-vlc', '--list', '--verbose=2'],
                        env=env, user=args.uid, group=args.gid, extra_groups=[],
                        stdout=stream, stderr=subprocess.STDOUT, check=True)
            with (case / (engine + '-stdout.log')).open('wb') as out, \
                    (case / (engine + '-stderr.log')).open('wb') as err:
                subprocess.run(['/usr/bin/modern-vlc', '--no-qt-privacy-ask',
                    '--no-metadata-network-access', '--restore-playback-pos=0',
                    '--qt-playback-engine=' + engine, '--play-and-exit', '--verbose=2',
                    '/input/natural-eof.mkv'], env=env, user=args.uid, group=args.gid,
                    extra_groups=[], stdout=out, stderr=err, check=True)
            if 'EOF reached' not in (case / (engine + '-stderr.log')).read_text(errors='replace'):
                raise RuntimeError('Fedora-installed player did not reach media EOF: ' + engine)
            record['engines'].append({'engine': engine, 'natural_eof_exit': 0})
        record['state'] = 'PASSED'
    finally:
        installed = subprocess.run(['rpm', '-q', 'modern-vlc-fork'], stdout=subprocess.DEVNULL)
        if installed.returncode == 0:
            subprocess.run(['dnf', '-y', 'remove', 'modern-vlc-fork'], check=True)
        record['owned_installation_removed'] = not Path('/opt/modern-vlc').exists()
        (case / 'verification.json').write_text(json.dumps(record, indent=2) + '\n')
        os.chown(case / 'verification.json', args.uid, args.gid)
        if not record['owned_installation_removed']:
            raise RuntimeError('The owned RPM installation did not retire completely')


if __name__ == '__main__':
    main()
