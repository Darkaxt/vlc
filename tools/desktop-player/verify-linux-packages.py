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
import subprocess
import tarfile

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


if __name__ == '__main__':
    main()
