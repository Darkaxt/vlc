#!/usr/bin/env python3
"""Recover every Linux format and exercise its unchanged normal Qt player.

Run on the disposable hosted Linux runner's owned X/audio session. Extraction
and playback are recorded separately from system installation qualification.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import tarfile
import uuid

HERE = Path(__file__).resolve().parent
# The existing bundle identity helper is platform independent: files, modes,
# internal symlinks. Reuse its exact comparison for the Linux payloads too.
spec = importlib.util.spec_from_file_location('package_identity', HERE / 'verify-macos-packages.py')
identity = importlib.util.module_from_spec(spec)
spec.loader.exec_module(identity)


def run(*argv, **kwargs):
    print('+', ' '.join(map(str, argv)), flush=True)
    return subprocess.run(list(map(str, argv)), check=True, **kwargs)


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def verify_rpm_installation(archive, fixture, expected, case):
    """Use a matching disposable distribution, preserving the host package DB."""
    if not shutil.which('docker'):
        raise RuntimeError('Matching RPM installation requires the hosted runner Docker engine')
    run('docker', 'info', stdout=subprocess.DEVNULL)
    # Resolve the official reference once, then run only the inspected immutable
    # image ID. Record its repository digest and actual OS/package database.
    reference = 'registry.fedoraproject.org/fedora:45'
    run('docker', 'pull', reference)
    image = json.loads(subprocess.check_output(['docker', 'image', 'inspect', reference]))[0]
    (case / 'image.json').write_text(json.dumps({key: image[key] for key in
        ('Id', 'RepoDigests', 'Architecture', 'Os')}, indent=2) + '\n')
    (case / 'expected-payload.json').write_text(json.dumps(expected, sort_keys=True) + '\n')
    authority = Path(os.environ['XAUTHORITY']).resolve(strict=True)
    runtime = Path(os.environ['XDG_RUNTIME_DIR']).resolve(strict=True)
    name = 'vlc-rpm-acceptance-' + uuid.uuid4().hex
    command = ['docker', 'run', '--name', name, '--label', 'vlc.native-acceptance=' + name,
        '--cpus=1', '--memory=3584m', '--memory-swap=4096m', '--pids-limit=256',
        '--mount', 'type=bind,src=' + str(HERE) + ',dst=/probe,readonly',
        '--mount', 'type=bind,src=' + str(case) + ',dst=/case',
        '--mount', 'type=bind,src=' + str(archive) + ',dst=/input/player.rpm,readonly',
        '--mount', 'type=bind,src=' + str(fixture) + ',dst=/input/natural-eof.mkv,readonly',
        '--mount', 'type=bind,src=' + str(authority) + ',dst=/input/xauthority,readonly',
        '--mount', 'type=bind,src=/tmp/.X11-unix,dst=/tmp/.X11-unix,readonly',
        '--mount', 'type=bind,src=' + str(runtime) + ',dst=/session-runtime',
        '--env', 'DISPLAY=' + os.environ['DISPLAY'], '--env', 'XAUTHORITY=/input/xauthority',
        '--env', 'PULSE_SERVER=unix:/session-runtime/pulse/native',
        image['Id'], '/bin/sh', '/probe/probe-fedora-rpm.sh',
        '--uid', str(os.getuid()), '--gid', str(os.getgid())]
    try:
        with (case / 'container.log').open('wb') as stream:
            result = subprocess.run(command, stdout=stream, stderr=subprocess.STDOUT)
        inspection = subprocess.run(['docker', 'container', 'inspect', name],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if inspection.returncode:
            raise RuntimeError('RPM container launch/inspection failed; inspect container.log')
        observed = json.loads(inspection.stdout)[0]
        state = observed['State']
        (case / 'container-exit.json').write_text(json.dumps({
            'id': observed['Id'], 'state': state}, indent=2) + '\n')
        if state['Running'] or result.returncode or state['ExitCode']:
            raise RuntimeError('Matching RPM installer/playback failed; inspect container.log and container-exit.json')
        record = json.loads((case / 'verification.json').read_text())
        if record['state'] != 'PASSED' or not record['owned_installation_removed']:
            raise RuntimeError('Matching RPM installation did not qualify or retire')
        return dict(record, image_id=image['Id'], archive_sha256=digest(archive))
    finally:
        # Name is unique and label-bound; this never targets another workload.
        inspection = subprocess.run(['docker', 'container', 'inspect', name],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if inspection.returncode == 0:
            owned = json.loads(inspection.stdout)[0]
            if owned['Config']['Labels'].get('vlc.native-acceptance') != name:
                raise RuntimeError('RPM container ownership changed')
            if owned['State']['Running']:
                run('docker', 'stop', '--time=-1', owned['Id'])
            run('docker', 'rm', owned['Id'])


def verify_snap_installation(archive, case, verify):
    """Attempt the actual unsigned local package under strict confinement."""
    # These commands affect only this disposable GitHub runner. No devmode,
    # classic fallback, host security relaxation or store publication is used.
    if not shutil.which('snap'):
        run('sudo', '-n', 'apt-get', 'install', '-y', 'snapd')
    run('sudo', '-n', 'systemctl', 'start', 'snapd.socket')
    run('sudo', '-n', 'snap', 'wait', 'system', 'seed.loaded')
    prior = subprocess.run(['snap', 'list', 'modern-vlc-fork'],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if prior.returncode == 0 or Path('/snap/modern-vlc-fork').exists():
        raise RuntimeError('Refusing to replace an existing Snap installation')
    base = subprocess.run(['snap', 'list', 'core24'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if base.returncode:
        run('sudo', '-n', 'snap', 'install', 'core24')
    graphics = subprocess.run(['snap', 'list', 'mesa-2404'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if graphics.returncode:
        run('sudo', '-n', 'snap', 'install', 'mesa-2404')
    installed = False
    try:
        run('sudo', '-n', 'snap', 'install', '--dangerous', archive)
        installed = True
        for plug in ('desktop', 'desktop-legacy', 'x11', 'audio-playback', 'opengl', 'home'):
            run('sudo', '-n', 'snap', 'connect', 'modern-vlc-fork:' + plug)
        run('sudo', '-n', 'snap', 'connect', 'modern-vlc-fork:gpu-2404', 'mesa-2404:gpu-2404')
        for name, argv in [('connections.txt', ['snap', 'connections', 'modern-vlc-fork']),
                           ('confinement.txt', ['snap', 'debug', 'confinement']),
                           ('installed.txt', ['snap', 'list', 'modern-vlc-fork', 'core24', 'mesa-2404'])]:
            with (case / name).open('w') as stream:
                run(*argv, stdout=stream)
        if (case / 'confinement.txt').read_text().strip() != 'strict':
            raise RuntimeError('Hosted Snap confinement is not strict')
        verify(Path('/snap/modern-vlc-fork/current/player'), case, archive,
            'snap-installed', {'state': 'installed through snapd; strict confinement'},
            Path('/snap/bin/modern-vlc-fork.modern-vlc'))
    finally:
        if installed:
            run('sudo', '-n', 'snap', 'remove', '--purge', 'modern-vlc-fork')
            if Path('/snap/modern-vlc-fork').exists():
                raise RuntimeError('The owned Snap installation did not retire completely')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work', required=True, type=Path)
    parser.add_argument('--scratch', required=True, type=Path)
    args = parser.parse_args()
    if platform.system() != 'Linux' or os.environ.get('GITHUB_ACTIONS') != 'true':
        raise RuntimeError('Linux format checks require the disposable hosted Linux runner')
    work = args.work.resolve()
    record = json.loads((work / 'package-output.json').read_text())
    packages = Path(record['directory']).resolve()
    if packages != work / 'packages' / record['source_commit']:
        raise RuntimeError('Linux package pointer escaped its source generation')
    normal = [path for path in packages.glob('Modern-VLC-Fork-*-linux-*') if path.is_dir()]
    if len(normal) != 1:
        raise RuntimeError('Expected one normal Linux payload')
    normal = normal[0]
    expected = identity.app_identity(normal)
    args.scratch.mkdir(parents=True, exist_ok=False)
    fixture = args.scratch / 'natural-eof.mkv'
    run('ffmpeg', '-hide_banner', '-loglevel', 'error', '-f', 'lavfi', '-i',
        'testsrc2=size=320x180:rate=30', '-f', 'lavfi', '-i', 'sine=frequency=600',
        '-t', '1', '-c:v', 'libx264', '-preset', 'ultrafast', '-threads', '1', '-c:a', 'aac', fixture)
    results = []

    def verify(app, case, archive, kind, installation, launcher=None):
        actual = identity.app_identity(app)
        if actual != expected:
            different = sorted(key for key in set(actual) | set(expected)
                               if actual.get(key) != expected.get(key))
            raise RuntimeError('Recovered Linux payload changed: ' + str(different))
        engines = []
        for engine in ('vlc', 'mpv'):
            home = case / (engine + '-home'); home.mkdir()
            env = dict(os.environ, HOME=str(home), XDG_CONFIG_HOME=str(home / 'config'),
                XDG_DATA_HOME=str(home / 'data'), XDG_CACHE_HOME=str(home / 'cache'),
                QML_DISK_CACHE_PATH=str(home / 'qml-cache'), QT_FORCE_STDERR_LOGGING='1')
            if engine == 'vlc':
                with (case / 'qt-loader.txt').open('w') as stream:
                    observed = subprocess.run(['ldd', '-r', str(app / 'lib/vlc/plugins/gui/libqt_plugin.so')],
                        env=env, stdout=stream, stderr=subprocess.STDOUT, text=True)
                    stream.write('\nloader_exit=' + str(observed.returncode) + '\n')
                with (case / 'module-registry.txt').open('wb') as stream:
                    subprocess.run([str(launcher or app / 'modern-vlc'), '--list', '--verbose=2'],
                        env=env, stdout=stream, stderr=subprocess.STDOUT, check=True)
                if 'stale plugins cache' in (case / 'module-registry.txt').read_text(errors='replace'):
                    raise RuntimeError('Shipped Linux plugin index does not match final module sizes/mtimes: ' + kind)
            stdout, stderr = case / (engine + '-stdout.log'), case / (engine + '-stderr.log')
            with stdout.open('wb') as out, stderr.open('wb') as err:
                run(launcher or app / 'modern-vlc', '--no-qt-privacy-ask', '--no-metadata-network-access',
                    '--restore-playback-pos=0', '--qt-playback-engine=' + engine,
                    '--play-and-exit', '--verbose=2', fixture, env=env, stdout=out, stderr=err)
            if 'EOF reached' not in stderr.read_text(errors='replace'):
                raise RuntimeError('Normal Linux player did not report natural media EOF: ' + kind + '/' + engine)
            engines.append({'engine': engine, 'natural_eof_exit': 0, 'stderr_sha256': digest(stderr)})
        results.append({'format': kind, 'archive_sha256': digest(archive),
            'source_commit': record['source_commit'], 'identical_payload_members': len(actual),
            'normal_player': engines, 'installation': installation})
        (args.scratch / 'verification.json').write_text(json.dumps(results, indent=2) + '\n')

    for kind in ('tar.xz', 'AppImage', 'deb', 'rpm', 'snap'):
        archive = packages / (normal.name + '.' + kind)
        if not archive.is_file():
            raise RuntimeError('Required generated Linux format is missing: ' + str(archive))
        case = args.scratch / kind; case.mkdir()
        extracted = case / 'extracted'; extracted.mkdir()
        installation = {'state': 'not applicable; portable format'}
        if kind == 'tar.xz':
            with tarfile.open(archive, 'r:xz') as stream:
                stream.extractall(extracted, filter='data')
            app = extracted / normal.name
        elif kind == 'AppImage':
            # Exercise the pinned AppImage runtime's own extractor without
            # requiring a runner FUSE mount or changing its host configuration.
            run(archive, '--appimage-extract', cwd=extracted, stdout=subprocess.DEVNULL)
            app = extracted / 'squashfs-root'
        elif kind == 'deb':
            run('dpkg-deb', '--extract', archive, extracted)
            app = extracted / 'opt/modern-vlc'
            installation = {'state': 'extracted; system installation pending'}
        elif kind == 'rpm':
            with subprocess.Popen(['rpm2cpio', str(archive)], stdout=subprocess.PIPE) as source:
                try:
                    run('cpio', '--extract', '--make-directories', '--no-absolute-filenames',
                        cwd=extracted, stdin=source.stdout, stdout=subprocess.DEVNULL)
                finally:
                    source.stdout.close()
                    code = source.wait()
                if code:
                    raise RuntimeError('RPM payload decoding failed: ' + str(code))
            app = extracted / 'opt/modern-vlc'
            installation = {'state': 'unverified',
                'unmet_criterion': 'Install through a matching RPM distribution dependency database; Ubuntu extraction is not that proof'}
        else:
            run('unsquashfs', '-processors', '1', '-d', extracted / 'snap', archive,
                stdout=subprocess.DEVNULL)
            app = extracted / 'snap/player'
            installation = {'state': 'unverified',
                'unmet_criterion': 'Install and execute with snapd, core24 and strict desktop/audio interfaces; extraction does not prove confinement'}
        verify(app, case, archive, kind, installation)

    # Exercise the normal DEB installer only in this disposable runner, and
    # refuse to replace an existing package or filesystem consumer.
    installed = Path('/opt/modern-vlc')
    launcher = Path('/usr/bin/modern-vlc')
    query = subprocess.run(['dpkg-query', '-W', '-f=${Status}', 'modern-vlc-fork'],
                           text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if installed.exists() or launcher.exists() or query.returncode == 0:
        raise RuntimeError('Refusing to replace an existing Modern VLC installation')
    archive = packages / (normal.name + '.deb')
    case = args.scratch / 'deb-installed'; case.mkdir()
    try:
        run('sudo', '-n', 'dpkg', '--install', archive)
        verify(installed, case, archive, 'deb-installed', {'state': 'installed through dpkg'}, launcher)
    finally:
        run('sudo', '-n', 'dpkg', '--purge', 'modern-vlc-fork')
        if installed.exists() or launcher.exists():
            raise RuntimeError('The owned DEB installation did not retire completely')
    (args.scratch / 'installer-exit.json').write_text(json.dumps({
        'owned_deb_removed': True, 'original_installation_absent': True}, indent=2) + '\n')
    # Finish both real installer attempts, retaining each exact failure instead
    # of treating extraction as installability or skipping the second format.
    failures = []
    for kind in ('rpm', 'snap'):
        case = args.scratch / (kind + '-installed'); case.mkdir()
        try:
            archive = packages / (normal.name + '.' + kind)
            if kind == 'rpm':
                rpm_result = verify_rpm_installation(archive, fixture, expected, case)
                results.append(dict(rpm_result, format='rpm-installed', source_commit=record['source_commit']))
            else:
                verify_snap_installation(archive, case, verify)
        except (OSError, RuntimeError, subprocess.CalledProcessError) as error:
            failure = {'format': kind, 'state': 'FAILED', 'error': str(error)}
            (case / 'failure.json').write_text(json.dumps(failure, indent=2) + '\n')
            failures.append(failure)
        (args.scratch / 'verification.json').write_text(json.dumps(results, indent=2) + '\n')
    if failures:
        raise RuntimeError('Real installer qualification failed: ' + json.dumps(failures))


if __name__ == '__main__':
    main()
