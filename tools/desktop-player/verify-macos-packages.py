#!/usr/bin/env python3
"""Verify the delivered Mac formats in disposable hosted-runner storage.

These are normal packages, without test hooks. Exact app identity binds both
formats to the normal app used to prepare the instrumented review. Its composed
picture/workflow evidence remains separate; each recovered normal app also runs
Qt playback through natural media EOF.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import plistlib
import shutil
import stat
import subprocess


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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work', required=True, type=Path)
    parser.add_argument('--scratch', required=True, type=Path)
    args = parser.parse_args()
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
        home = case / 'home'; home.mkdir()
        env = dict(os.environ, HOME=str(home), XDG_CONFIG_HOME=str(home / 'config'),
            XDG_DATA_HOME=str(home / 'data'), XDG_CACHE_HOME=str(home / 'cache'),
            QML_DISK_CACHE_PATH=str(case / 'qml-cache'), QT_FORCE_STDERR_LOGGING='1')
        argv = [app / 'Contents/MacOS/vlc', '--intf=qt', '--no-qt-privacy-ask',
                '--no-metadata-network-access', '--restore-playback-pos=0',
                '--qt-playback-engine=vlc', '--play-and-exit', '--verbose=2', fixture]
        prior_reports = {path for root in (Path.home(), home)
                         for path in (root / 'Library/Logs/DiagnosticReports').glob('vlc*')}
        try:
            with (case / 'stdout.log').open('wb') as stdout, (case / 'stderr.log').open('wb') as stderr:
                run(*argv, env=env, stdout=stdout, stderr=stderr)
        except subprocess.CalledProcessError as error:
            print((case / 'stderr.log').read_text(errors='replace')[-10000:], flush=True)
            (case / 'failure.json').write_text(json.dumps({'argv': list(map(str, argv)),
                'normal_returncode': error.returncode, 'archive_sha256': digest(archive)}, indent=2) + '\n')
            if error.returncode < 0:
                diagnose_crash(argv, env, case, app, prior_reports)
            raise
        log = (case / 'stderr.log').read_text(errors='replace')
        if 'EOF reached' not in log:
            raise RuntimeError('Normal packaged player did not report natural media EOF')
        results.append({'format': archive.suffix, 'archive_sha256': digest(archive),
            'source_commit': record['source_commit'], 'normal_bundle_members_identical': len(actual),
            'strict_signature_verified': True, 'normal_qt_playback_natural_eof_exit': 0,
            'stderr_sha256': digest(case / 'stderr.log')})
        (args.scratch / 'verification.json').write_text(json.dumps(results, indent=2) + '\n')

    archives = {suffix: sorted(packages.glob('*' + suffix)) for suffix in ('.zip', '.dmg')}
    archives['.zip'] = [path for path in archives['.zip'] if '-symbols' not in path.name]
    if any(len(paths) != 1 for paths in archives.values()):
        raise RuntimeError('Expected one normal ZIP and one DMG in the source generation')
    archive = archives['.zip'][0]
    unpacked = args.scratch / 'zip-extracted'
    run('ditto', '-x', '-k', archive, unpacked)
    verify(unpacked / 'Modern VLC.app', args.scratch / 'zip-runtime', archive)
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
