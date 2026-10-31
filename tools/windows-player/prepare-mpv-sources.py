"""Fetch exact core sources for a source-bound S8 Windows libmpv build.

The reference nightly binary has no complete dependency-source manifest. These
archives are inputs to a separate build against the documented VLC contrib SDK;
fetching them does not establish provenance for that prebuilt nightly binary.
"""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import tarfile
import urllib.request


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scratch', type=Path, required=True)
    selection = parser.add_mutually_exclusive_group()
    selection.add_argument('--shader-inputs', action='store_true')
    selection.add_argument('--host-inputs', action='store_true')
    selection.add_argument('--text-inputs', action='store_true')
    args = parser.parse_args()
    root = args.scratch.resolve(strict=True)
    assert root == Path('D:/Temp/vlc-s8-20261029')
    destination = root / ('downloads' if args.host_inputs else 'mpv-source-inputs')
    destination.mkdir(exist_ok=True)
    receipt = root / ('evidence/mpv-host-source-inputs.json' if args.host_inputs else
                     'evidence/mpv-text-source-inputs.json' if args.text_inputs else
                     'evidence/mpv-shader-source-inputs.json' if args.shader_inputs
                      else 'evidence/mpv-source-inputs.json')
    assert not receipt.exists(), 'Inspect and preserve the existing source receipt'
    records = []
    registry = Path(__file__).resolve().parents[2] / 'modules/gui/qt/player/mpv/source.json'
    pins = json.loads(registry.read_text())
    group = 'text' if args.text_inputs else 'shaders' if args.shader_inputs else 'core'
    selected = pins['host_tools'] if args.host_inputs else [item for item in pins['sources'] if item['group'] == group]
    for pin in selected:
        expected_sha256 = pin['sha256']
        if args.host_inputs or pin.get('archive'):
            archive, url, expected_root = destination / pin['archive'], pin['url'], pin['root']
        else:
            repository, commit = pin['repository'], pin['commit']
            name = repository.split('/')[1]
            expected_root = name + '-' + commit
            archive = destination / (expected_root + '.tar.gz')
            url = 'https://codeload.github.com/' + repository + '/tar.gz/' + commit
        if not archive.exists():
            partial = archive.with_suffix('.gz.partial')
            assert not partial.exists(), 'Inspect the previous interrupted transfer'
            with urllib.request.urlopen(url) as incoming, partial.open('xb') as outgoing:
                while blob := incoming.read(1024 * 1024):
                    outgoing.write(blob)
            assert digest(partial) == expected_sha256, partial
            partial.rename(archive)
        assert digest(archive) == expected_sha256, archive
        members = 0
        with tarfile.open(archive, mode='r|*') as source:
            for member in source:
                path = PurePosixPath(member.name)
                assert not path.is_absolute() and '..' not in path.parts, member.name
                assert path.parts[0] == expected_root, member.name
                members += 1
        assert members > 1
        record = {**pin, 'url': url,
                  'archive': archive.name, 'sha256': digest(archive),
                  'bytes': archive.stat().st_size, 'members': members}
        records.append(record)
        print(json.dumps(record), flush=True)
    receipt.write_text(json.dumps({'schema': 'vlc_redesign.mpv_core_source_inputs.v1',
        'scope': 'Source-bound build inputs; not corresponding-source proof for the reference nightly DLL',
        'sdk_dependencies': 'Existing exact VLC contrib sources/notices must accompany the eventual linked build',
        'sources': records}, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
