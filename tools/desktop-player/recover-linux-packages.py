"""Recover an exact prior Linux package artifact for compiler-free qualification.

The normal build workflow is unchanged. This mode tests immutable prior packages,
records both their source and the current verifier revision, and never publishes.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import tarfile
import urllib.error
import urllib.request
import zipfile

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('ci_evidence', HERE / 'read-ci-evidence.py')
evidence = importlib.util.module_from_spec(spec)
spec.loader.exec_module(evidence)


def package_entries(archive, source, target):
    if not re.fullmatch('[0-9a-f]{40}', source):
        raise RuntimeError('Package recovery requires an exact source revision')
    architecture = target.removeprefix('linux-')
    pattern = re.compile(r'(?:^|.*/)packages/' + source +
        r'/(Modern-VLC-Fork-[0-9.]+-linux-' + re.escape(architecture) + r')\.tar\.xz$')
    matches = [(item, match.group(1)) for item in archive.infolist()
               if (match := pattern.fullmatch(item.filename))]
    if len(matches) != 1:
        raise RuntimeError('Artifact has no unique source-bound normal Linux TAR')
    entry, name = matches[0]
    prefix = entry.filename.removesuffix(name + '.tar.xz')
    result = {}
    for kind in ('tar.xz', 'AppImage', 'deb', 'rpm', 'snap'):
        items = [item for item in archive.infolist() if item.filename == prefix + name + '.' + kind]
        if len(items) != 1:
            raise RuntimeError('Artifact has no unique matching package: ' + kind)
        result[kind] = items[0]
    return name, result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--artifact', required=True, type=int)
    parser.add_argument('--source', required=True)
    parser.add_argument('--target', required=True, choices=('linux-x86_64', 'linux-aarch64'))
    parser.add_argument('--work', required=True, type=Path)
    parser.add_argument('--scratch', required=True, type=Path)
    args = parser.parse_args()
    if os.environ.get('GITHUB_ACTIONS') != 'true' or platform.system() != 'Linux':
        raise RuntimeError('Package recovery requires the disposable hosted Linux runner')
    if args.target != 'linux-' + platform.machine():
        raise RuntimeError('Package architecture does not match the actual runner')
    metadata = json.loads(subprocess.check_output(['gh', 'api',
        'repos/Darkaxt/vlc/actions/artifacts/' + str(args.artifact)], text=True))
    if metadata['expired'] or metadata['name'] != 'desktop-' + args.target + '-' + args.source or \
            metadata['workflow_run']['head_sha'] != args.source:
        raise RuntimeError('Artifact identity/source does not match the requested normal generation')
    if not re.fullmatch(r'sha256:[0-9a-f]{64}', metadata.get('digest', '')):
        raise RuntimeError('Artifact has no exact published SHA256 digest')
    args.work.mkdir(parents=True, exist_ok=False)
    args.scratch.mkdir(parents=True, exist_ok=False)
    token = subprocess.check_output(['gh', 'auth', 'token'], text=True).strip()
    request = urllib.request.Request(metadata['archive_download_url'], headers={
        'Authorization': 'Bearer ' + token, 'Accept': 'application/vnd.github+json'})
    try:
        urllib.request.build_opener(evidence.NoRedirect()).open(request)
        raise RuntimeError('Expected the authenticated artifact redirect')
    except urllib.error.HTTPError as error:
        if error.code != 302:
            raise
        location = error.headers['Location']
    del token, request
    if not location.startswith('https://'):
        raise RuntimeError('Artifact redirect did not use HTTPS')
    downloaded = args.scratch / 'original-artifact.zip'
    digest = hashlib.sha256()
    with urllib.request.urlopen(location) as response, downloaded.open('xb') as output:
        while block := response.read(1024 * 1024):
            output.write(block)
            digest.update(block)
    if downloaded.stat().st_size != metadata['size_in_bytes'] or \
            'sha256:' + digest.hexdigest() != metadata['digest']:
        raise RuntimeError('Downloaded artifact differs from its published identity')
    directory = args.work / 'packages' / args.source
    directory.mkdir(parents=True)
    recovered = []
    with zipfile.ZipFile(downloaded) as archive:
        name, entries = package_entries(archive, args.source, args.target)
        for kind, entry in entries.items():
            destination = directory / (name + '.' + kind)
            with archive.open(entry) as original, destination.open('xb') as output:
                shutil.copyfileobj(original, output, 1024 * 1024)
            if kind == 'AppImage':
                destination.chmod(0o755)
            with destination.open('rb') as stream:
                recovered.append({'file': destination.name,
                    'sha256': hashlib.file_digest(stream, 'sha256').hexdigest()})
    # The normal TAR preserves native executable modes and internal symlinks;
    # GitHub's outer artifact ZIP does not. Recover only that exact payload.
    with tarfile.open(directory / (name + '.tar.xz'), 'r:xz') as archive:
        for member in archive.getmembers():
            parts = Path(member.name).parts
            if not parts or parts[0] != name or '..' in parts or Path(member.name).is_absolute():
                raise RuntimeError('Normal TAR escaped its source-bound payload')
        archive.extractall(directory, filter='data')
    (args.work / 'package-output.json').write_text(json.dumps({
        'source_commit': args.source, 'directory': str(directory.resolve()),
        'qualification': 'PENDING; recovered normal artifact'}) + '\n')
    (args.work / 'package-recovery.json').write_text(json.dumps({
        'artifact': metadata, 'artifact_sha256_verified': digest.hexdigest(),
        'normal_source_commit': args.source, 'verifier_commit': os.environ['GITHUB_SHA'],
        'compiler_invoked': False, 'recovered_packages': recovered}, indent=2) + '\n')
    print(json.dumps({'artifact': args.artifact, 'source': args.source,
        'compiler_invoked': False, 'recovered_formats': list(entries)}), flush=True)


if __name__ == '__main__':
    main()
