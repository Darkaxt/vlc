"""Bind updated static codec libraries to their actual VLC plugin link maps."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shlex


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def image_targets(build, retained=()):
    targets = []
    retained = {row['target'] for row in retained}
    candidates = [*(build / 'modules').glob('*.la'), build / 'modules/gui/qt/libqt_plugin.la']
    for path in candidates:
        text = path.read_text()
        dependencies = re.search(r"^dependency_libs='(.*)'$", text, re.M)
        dlname = re.search(r"^dlname='(.+)'$", text, re.M)
        if not dependencies or not dlname:
            continue
        tokens = shlex.split(dependencies.group(1))
        # Explicitly linked static archive members disappear from libtool's
        # dependency_libs after linking. The previously bound consumer remains
        # part of this retained graph; re-read its actual DLL identity here.
        if path.name in retained or any(token in ('-lz', '-lpng', '-lpng16') or Path(token).name in
               ('libz.a', 'libpng.a', 'libpng16.a') for token in tokens):
            targets.append({'target': path.name, 'build_source': str(path.parent / '.libs' / dlname.group(1))})
    missing = retained - {row['target'] for row in targets}
    if missing:
        raise RuntimeError('Retained image consumer metadata disappeared: ' + ', '.join(sorted(missing)))
    return sorted(targets, key=lambda row: row['target'])


def prepare_images(source, build, base, receipt):
    if not re.search(r'^#define _FILE_OFFSET_BITS 64$', (build / 'config.h').read_text(), re.M):
        raise RuntimeError('Updated zlib requires the retained Windows 64-bit offset configuration')
    images = receipt['image_dependencies']
    signature = hashlib.sha256(json.dumps(images, sort_keys=True).encode()).hexdigest()
    plan_path = build / 'player-image-inputs.json'
    previous = json.loads(plan_path.read_text()) if plan_path.exists() else None
    targets = image_targets(build, previous['targets'] if previous else ())
    if not any(row['target'] == 'libpng_plugin.la' for row in targets):
        raise RuntimeError('The configured PNG plugin is missing from the image link graph')
    libraries = [Path(row['prefix']) / 'lib' / row['static_library'] for row in images['libraries']]
    for row, path in zip(images['libraries'], libraries):
        assert sha(path) == row['library_sha256'], path
    if not previous or previous['receipt_sha256'] != signature:
        # The prefix already precedes SDK includes, but these dependency files
        # still name the old headers. Invalidate only their real source consumers.
        for name in ('codec/png.c', 'demux/mkv/mkv.hpp', 'demux/mp4/libmp4.c',
                     'services_discovery/sap.c', 'stream_filter/inflate.c'):
            (source / 'modules' / name).touch()
    prefix = Path(images['libraries'][0]['prefix'])
    rules = ['# Exact image/compression archive consumers; generated from retained libtool metadata.',
        'LDFLAGS := -L' + str(prefix / 'lib') + ' $(LDFLAGS)',
        'LIBZ = -L' + str(prefix / 'lib') + ' -lz',
        # A failed prior link can retain this convenience archive with an
        # embedded libz.a member. Relink it when its actual LIBADD rule changes.
        'libvlc_mp4.la: ' + str(build / 'player-image-links.mk'),
        'libpng_plugin_la_LIBADD = ' + str(prefix / 'lib/libpng16.a') + ' ' + str(prefix / 'lib/libz.a') + ' $(LIBM)']
    for row in targets:
        row['map'] = str(base / 'link-maps' / ('image-' + Path(row['target']).stem + '.map'))
        rules += [row['target'] + ': ' + ' '.join(map(str, libraries)) + ' ' + str(build / 'player-image-links.mk'),
                  row['target'] + ': LDFLAGS += -Wl,-Map,' + row['map']]
    text = '\n'.join(rules) + '\n'
    makefile = build / 'player-image-links.mk'
    if not makefile.exists() or makefile.read_text() != text:
        makefile.write_text(text)
    plan_path.write_text(json.dumps({'receipt_sha256': signature, 'targets': targets,
        'libraries': images['libraries'], 'makefile_sha256': sha(makefile)}, indent=2) + '\n')


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
        prepare_images(args.source, args.build, base, receipt)
        if not marker.exists() or json.loads(marker.read_text())['build_receipt_sha256'] != signature:
            for item in receipt['libraries']:
                source = args.source / 'modules/codec' / (item['library'] + '.c')
                assert source.is_file(), source
                source.touch()
            marker.write_text(json.dumps({'build_receipt_sha256': signature}) + '\n')
        return
    assert args.runtime and json.loads(marker.read_text())['build_receipt_sha256'] == signature
    links = []
    image_plan = json.loads((args.build / 'player-image-inputs.json').read_text())
    image_maps = {row['target']: Path(row['map']) for row in image_plan['targets']}
    for item in receipt['libraries']:
        library = Path(item['prefix']) / 'lib' / item['static_library']
        assert sha(library) == item['library_sha256']
        link_map = image_maps.get('lib' + item['library'] + '_plugin.la',
                                  base / 'link-maps' / (item['library'] + '.map'))
        text = link_map.read_text(errors='strict')
        assert str(library) + '(' in text, 'No archive member linked: ' + str(library)
        old = '/work/build/contrib/x86_64-w64-mingw32/lib/' + item['static_library']
        assert old + '(' not in text, 'Old SDK archive selected'
        plugin = args.build / 'modules/.libs' / ('lib' + item['library'] + '_plugin.dll')
        assert plugin.is_file()
        links.append(dict(item, link_map_sha256=sha(link_map), unstripped_plugin_sha256=sha(plugin)))
    observed = set()
    image_links = []
    for row in image_plan['targets']:
        text = Path(row['map']).read_text()
        selected = []
        for library in image_plan['libraries']:
            path = Path(library['prefix']) / 'lib' / library['static_library']
            assert sha(path) == library['library_sha256']
            if str(path) + '(' in text:
                observed.add(library['name'])
                selected.append(library['name'])
        assert not re.search(r'/work/build/contrib/[^\s(]+/lib(?:z|png(?:16)?)\.a\(', text), row
        image_links.append(dict(row, linked_updates=selected, link_map_sha256=sha(Path(row['map'])),
                               unstripped_plugin_sha256=sha(Path(row['build_source']))))
    assert observed == {'zlib', 'png'}, observed
    output = {'schema': 'vlc_redesign.upstream_codec_linkage.v1',
        'build_receipt_sha256': signature, 'libraries': links,
        'image_dependencies': dict(receipt['image_dependencies'], links=image_links),
        'verification': 'Exact new archive member paths present and old SDK archive members absent in all four GNU linker maps'}
    (args.runtime / 'VLC-CODEC-BUILDINFO.json').write_text(json.dumps(output, indent=2) + '\n')
    print(json.dumps(output), flush=True)


if __name__ == '__main__':
    main()
