"""Fetch selected VLC dependency sources with the pinned upstream SHA-512 values."""
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
    parser.add_argument('--components', nargs='+', choices=['medialibrary', 'aom', 'mad', 'mpg123', 'zvbi', 'zlib', 'png'], default=['medialibrary'])
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[2]
    revision = subprocess.check_output(['git', '-C', str(repo), 'rev-parse', args.upstream_ref], text=True).strip()
    assert re.fullmatch('[0-9a-f]{40}', revision)
    destination = args.destination.resolve(strict=True)
    assert destination == Path('D:/VLC-Redesign/build/windows-x64/mpv-source-inputs')
    definitions = {
        'medialibrary': ('MEDIALIBRARY', 'medialibrary-{v}.tar.bz2', 'https://code.videolan.org/videolan/medialibrary/-/archive/{v}/medialibrary-{v}.tar.bz2'),
        'aom': ('AOM', 'libaom-{v}.tar.gz', 'https://storage.googleapis.com/aom-releases/libaom-{v}.tar.gz'),
        'mad': ('MAD', 'libmad-{v}.tar.gz', 'https://codeberg.org/tenacityteam/libmad/archive/{v}.tar.gz'),
        'mpg123': ('MPG123', 'mpg123-{v}.tar.bz2', 'https://downloads.sourceforge.net/project/mpg123/mpg123/{v}/mpg123-{v}.tar.bz2'),
        'zvbi': ('ZVBI', 'zvbi-{v}.tar.gz', 'https://github.com/zapping-vbi/zvbi/archive/refs/tags/v{v}.tar.gz'),
        'zlib': ('ZLIB', 'zlib-{v}.tar.xz', 'https://github.com/madler/zlib/releases/download/v{v}/zlib-{v}.tar.xz'),
        'png': ('PNG', 'libpng-{v}.tar.xz', 'https://downloads.sourceforge.net/project/libpng/libpng16/{v}/libpng-{v}.tar.xz')}
    records = []
    for component in args.components:
        def source(name):
            return subprocess.check_output(['git', '-C', str(repo), 'show', revision + ':contrib/src/' + component + '/' + name], text=True)
        variable, template, location = definitions[component]
        version = re.search(r'^' + variable + r'_VERSION := ([0-9.]+)$', source('rules.mak'), re.M).group(1)
        name, url = template.format(v=version), location.format(v=version)
        expected = {line.split()[1]: line.split()[0] for line in source('SHA512SUMS').splitlines() if line.strip()}[name]
        assert re.fullmatch('[0-9a-f]{128}', expected)
        path = destination / name
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
        record = {'library': component, 'version': version, 'archive': name, 'url': url,
            'sha512': expected, 'sha256': sha256, 'bytes': path.stat().st_size}
        records.append(record)
        print(json.dumps({'verified_source': record}), flush=True)
    receipt = {'schema': 'vlc_redesign.upstream_dependency_inputs.v2', 'upstream_revision': revision,
        'sources': records, 'consumer': 'vlc-weekly-upstream-sync-and-release',
        'storage': 'Existing bound source-input directory; these added archives belong to VLC dependencies, not MPV',
        'retirement': 'Retire obsolete generated dependency inputs through transactional cleanup after replacement and consumer exit'}
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt), flush=True)


if __name__ == '__main__':
    main()
