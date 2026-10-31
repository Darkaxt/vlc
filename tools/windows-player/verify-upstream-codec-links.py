"""Bind updated static codec libraries to their actual VLC plugin link maps."""
import argparse
import hashlib
import json
from pathlib import Path


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--build', type=Path, required=True)
    parser.add_argument('--runtime', type=Path)
    parser.add_argument('--prepare', action='store_true')
    args = parser.parse_args()
    base = Path('/work/upstream-codecs-1.1.1')
    receipt_path = base / 'build-receipt.json'
    receipt = json.loads(receipt_path.read_text())
    signature = sha(receipt_path)
    marker = args.build / 'player-upstream-codec-inputs.json'
    if args.prepare:
        if not marker.exists() or json.loads(marker.read_text())['build_receipt_sha256'] != signature:
            for item in receipt['libraries']:
                source = args.source / 'modules/codec' / (item['library'] + '.c')
                assert source.is_file(), source
                source.touch()
            marker.write_text(json.dumps({'build_receipt_sha256': signature}) + '\n')
        return
    assert args.runtime and json.loads(marker.read_text())['build_receipt_sha256'] == signature
    links = []
    for item in receipt['libraries']:
        library = Path(item['prefix']) / 'lib' / item['static_library']
        assert sha(library) == item['library_sha256']
        link_map = base / 'link-maps' / (item['library'] + '.map')
        text = link_map.read_text(errors='strict')
        assert str(library) + '(' in text, 'No archive member linked: ' + str(library)
        old = '/work/build/contrib/x86_64-w64-mingw32/lib/' + item['static_library']
        assert old + '(' not in text, 'Old SDK archive selected'
        plugin = args.build / 'modules/.libs' / ('lib' + item['library'] + '_plugin.dll')
        assert plugin.is_file()
        links.append(dict(item, link_map_sha256=sha(link_map), unstripped_plugin_sha256=sha(plugin)))
    output = {'schema': 'vlc_redesign.upstream_codec_linkage.v1',
        'build_receipt_sha256': signature, 'libraries': links,
        'verification': 'Exact new archive member paths present and old SDK archive members absent in all four GNU linker maps'}
    (args.runtime / 'VLC-CODEC-BUILDINFO.json').write_text(json.dumps(output, indent=2) + '\n')
    print(json.dumps(output), flush=True)


if __name__ == '__main__':
    main()
