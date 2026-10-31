"""Package separately downloadable symbols matching every stripped release PE."""
import argparse
import json
from pathlib import Path
import re
import zipfile
import zlib
from release_symbols import digest, verify_runtime


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime', required=True, type=Path)
    parser.add_argument('--symbols', required=True, type=Path)
    parser.add_argument('--destination', required=True, type=Path)
    parser.add_argument('--version', required=True)
    parser.add_argument('--source-commit', required=True)
    args = parser.parse_args()
    assert re.fullmatch(r'\d+\.\d+\.\d+', args.version) and re.fullmatch('[0-9a-f]{40}', args.source_commit)
    assert args.destination.resolve().is_relative_to(Path('D:/VLC-Redesign'))
    manifest = verify_runtime(args.runtime)
    assert (args.symbols / 'manifest.json').read_bytes() == (args.runtime / 'RELEASE-SYMBOLS.json').read_bytes()
    files = []
    for name, record in sorted(manifest['files'].items()):
        path = args.symbols / record['symbols_path']
        assert path.is_file() and not path.is_symlink() and digest(path) == record['symbols_sha256'], name
        crc = 0
        with path.open('rb') as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b''):
                crc = zlib.crc32(chunk, crc)
        assert crc == record['debuglink']['crc32'], name
        files.append(path)
    expected = {path.resolve() for path in files} | {(args.symbols / 'manifest.json').resolve()}
    assert {path.resolve() for path in args.symbols.rglob('*') if path.is_file()} == expected
    name = 'Modern-VLC-Fork-' + args.version + '-win64-portable'
    archive = args.destination / ('Modern-VLC-Fork-' + args.version + '-win64-symbols.zip')
    assert not archive.exists()
    with zipfile.ZipFile(archive, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=6, allowZip64=True) as output:
        output.writestr(name + '/SYMBOLS-README.txt', 'Optional matching debugging symbols for Modern VLC Fork ' + args.version
            + '\nSource commit: ' + args.source_commit + '\n'
            + 'The portable player does not need these files. For debugging, extract alongside the matching portable ZIP; '
            + 'merge its .debug directories without replacing executable binaries. GNU debuglink names/CRC and '
            + 'RELEASE-SYMBOLS.json bind these files to the exact release.\n')
        output.write(args.runtime / 'RELEASE-SYMBOLS.json', name + '/RELEASE-SYMBOLS.json')
        for path in files:
            output.write(path, name + '/' + path.relative_to(args.symbols).as_posix())
    result = {'archive': str(archive), 'sha256': digest(archive), 'bytes': archive.stat().st_size,
        'source_commit': args.source_commit, 'pe_files': len(files),
        'manifest_sha256': digest(args.runtime / 'RELEASE-SYMBOLS.json')}
    (args.destination / 'symbols-package-result.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result), flush=True)


if __name__ == '__main__':
    main()
