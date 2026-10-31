"""Independently retrieve the pinned MPV SDK into exact S8 build scratch.

No installation, profile write, application launch or publication occurs here.
The selected DLL is checked separately after verified archive extraction.
"""
import argparse
import hashlib
import json
from pathlib import Path, PureWindowsPath
import subprocess
import urllib.request


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scratch', type=Path, required=True)
    parser.add_argument('--archiver', type=Path, required=True)
    args = parser.parse_args()
    root = args.scratch.resolve(strict=True)
    assert root == Path('D:/Temp/vlc-s8-20261029')
    archiver = args.archiver.resolve(strict=True)
    assert archiver.name.lower() == '7z.exe'
    repo = Path(__file__).resolve().parents[2]
    pin = json.loads((repo / 'modules/gui/qt/player/mpv/source.json').read_text())['reference_runtime']
    archive = root / 'downloads' / Path(pin['archive']).name
    if not archive.exists():
        partial = archive.with_suffix('.7z.partial')
        assert not partial.exists(), 'Inspect the prior incomplete transfer before resuming'
        with urllib.request.urlopen(pin['archive']) as source, partial.open('xb') as target:
            while chunk := source.read(1024 * 1024):
                target.write(chunk)
        assert digest(partial) == pin['archive_sha256']
        partial.rename(archive)
    assert digest(archive) == pin['archive_sha256']
    listing = subprocess.check_output([str(archiver), 'l', '-slt', str(archive)], text=True, encoding='utf-8')
    (root / 'evidence/mpv-sdk-listing.txt').write_text(listing, encoding='utf-8')
    body = listing.split('----------', 1)[1]
    for record in body.strip().split('\n\n'):
        fields = dict(line.split(' = ', 1) for line in record.splitlines() if ' = ' in line)
        if 'Path' not in fields:
            continue
        path = PureWindowsPath(fields['Path'])
        assert not path.is_absolute() and not path.drive and '..' not in path.parts, fields['Path']
        assert not fields.get('Symbolic Link') and not fields.get('Hard Link'), fields['Path']
    destination = root / 'mpv-upstream-sdk'
    assert not destination.exists(), 'Preserve the existing extraction and its consumers'
    destination.mkdir()
    subprocess.run([str(archiver), 'x', str(archive), '-o' + str(destination), '-y'], check=True)
    libraries = list(destination.rglob('libmpv-2.dll'))
    assert len(libraries) == 1 and digest(libraries[0]) == pin['sha256']
    receipt = {'archive': str(archive), 'archive_sha256': digest(archive),
               'dll': str(libraries[0]), 'dll_sha256': digest(libraries[0]),
               'files': [{'path': str(path.relative_to(destination)), 'bytes': path.stat().st_size,
                          'sha256': digest(path)} for path in sorted(destination.rglob('*')) if path.is_file()]}
    (root / 'evidence/mpv-runtime-input.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({key: value for key, value in receipt.items() if key != 'files'}))


if __name__ == '__main__':
    main()
