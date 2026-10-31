"""Fetch the medialibrary source required by an explicitly pinned VLC revision."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import urllib.request


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--upstream-ref', required=True)
    parser.add_argument('--destination', required=True, type=Path)
    parser.add_argument('--receipt', required=True, type=Path)
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[2]
    revision = subprocess.check_output(['git', '-C', str(repo), 'rev-parse', args.upstream_ref], text=True).strip()
    assert re.fullmatch('[0-9a-f]{40}', revision)
    def source(name):
        return subprocess.check_output(['git', '-C', str(repo), 'show', revision + ':contrib/src/medialibrary/' + name], text=True)
    version = re.search(r'^MEDIALIBRARY_VERSION := ([0-9.]+)$', source('rules.mak'), re.M).group(1)
    name = 'medialibrary-' + version + '.tar.bz2'
    hashes = {line.split()[1]: line.split()[0] for line in source('SHA512SUMS').splitlines() if line.strip()}
    expected = hashes[name]
    assert re.fullmatch('[0-9a-f]{128}', expected)
    destination = args.destination.resolve(strict=True)
    assert destination == Path('D:/VLC-Redesign/build/windows-x64/mpv-source-inputs')
    path = destination / name
    url = 'https://code.videolan.org/videolan/medialibrary/-/archive/' + version + '/' + name
    if not path.exists():
        pending = path.with_name(name + '.pending')
        assert not pending.exists(), 'Inspect original partial retrieval instead of replaying it'
        request = urllib.request.Request(url, headers={'User-Agent': 'Modern-VLC-Fork source verification'})
        with urllib.request.urlopen(request) as response, pending.open('xb') as output:
            while block := response.read(1024 * 1024):
                output.write(block)
        with pending.open('rb') as stream:
            assert hashlib.file_digest(stream, 'sha512').hexdigest() == expected, 'Publisher checksum mismatch; preserve exact failed output'
        pending.replace(path)
    with path.open('rb') as stream:
        assert hashlib.file_digest(stream, 'sha512').hexdigest() == expected
    with path.open('rb') as stream:
        sha256 = hashlib.file_digest(stream, 'sha256').hexdigest()
    receipt = {'schema': 'vlc_redesign.upstream_medialibrary_input.v1', 'upstream_revision': revision,
        'version': version, 'archive': name, 'url': url, 'sha512': expected, 'sha256': sha256,
        'bytes': path.stat().st_size, 'consumer': 'vlc-weekly-upstream-sync-and-release',
        'storage': 'Existing bound source-input directory; this added archive belongs to VLC medialibrary, not MPV',
        'retirement': 'Retire obsolete generated dependency inputs through transactional cleanup after replacement and consumer exit'}
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt), flush=True)


if __name__ == '__main__':
    main()
