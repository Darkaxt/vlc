"""Bind loose packaged media/fonts and the default skin to upstream sources.

Qt's embedded resources are covered by audit-release-assets.py. This separately
reads the actual package's loose assets and font license/name records, without
extracting a skin or modifying the inspected runtime.
"""
import argparse
import gettext
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess
import tarfile

BASELINE = '392bc1d0abdb7396b6c97fef206efa1d23868e19'


def font_names(blob):
    # OpenType's fixed name-table records; no glyph decoding or rendering.
    count = struct.unpack_from('>H', blob, 4)[0]
    name_offset = None
    for index in range(count):
        tag, _, offset, size = struct.unpack_from('>4sIII', blob, 12 + 16 * index)
        assert offset + size <= len(blob)
        if tag == b'name':
            name_offset = offset
    assert name_offset is not None
    _, count, strings = struct.unpack_from('>HHH', blob, name_offset)
    names = {}
    for index in range(count):
        platform, encoding, language, name_id, length, offset = struct.unpack_from('>HHHHHH', blob, name_offset + 6 + 12 * index)
        if name_id not in (0, 1, 2, 5, 13, 14) or language not in (0, 0x409):
            continue
        start = name_offset + strings + offset
        assert start + length <= len(blob)
        text = blob[start:start + length].decode('utf-16-be' if platform in (0, 3) else 'mac_roman')
        names.setdefault(str(name_id), []).append(text)
    return {key: sorted(set(value)) for key, value in names.items()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[2]
    records = []
    missing_grants = []
    def record(package_path, source_path, blob):
        original = subprocess.check_output(['git', '-C', str(repo), 'show', BASELINE + ':' + source_path])
        current_xml = source_path == 'share/skins2/default/theme.xml'
        expected = (repo / source_path).read_bytes().replace(b'\r\n', b'\n') if current_xml else original
        assert blob == expected, 'Packaged resource differs from its recorded source: ' + package_path
        entry = {'package_path': package_path, 'source_path': source_path, 'source_revision': BASELINE,
            'sha256': hashlib.sha256(blob).hexdigest(), 'bytes': len(blob),
            'license': 'GPL-2.0-or-later (upstream VLC distribution; retain per-file notices)'}
        if current_xml and blob != original:
            entry['source_revision'] = 'Current fork working tree, bound by the source hash; bind to final commit before release'
        if Path(package_path).suffix.lower() in ('.ttf', '.otf'):
            entry['opentype_names'] = font_names(blob)
            entry['license'] = 'Retain exact embedded font license/copyright statements recorded in opentype_names and their applicable full license text.'
            if not entry['opentype_names'].get('13'):
                missing_grants.append({'package_path': package_path,
                    'reason': 'The font has copyright/name metadata but no embedded license grant; redistribution terms need a verified source.'})
        if package_path.endswith('.sofa'):
            license_match = re.search(rb'Copyright \(C\) 2017 3D Sound Labs[^\x00]+', blob)
            assert license_match, 'Inspect missing HRTF license metadata'
            entry['embedded_license'] = license_match.group().decode('utf-8')
            assert 'Lesser General Public License' in entry['embedded_license']
            entry['license'] = 'LGPL-2.1-or-later'
        records.append(entry)
    suffixes = {'.png', '.jpg', '.jpeg', '.svg', '.gif', '.bmp', '.ico', '.ttf', '.otf', '.sofa', '.wav'}
    for directory in ('hrtfs', 'skins', 'lua'):
        for asset in sorted((args.runtime / directory).rglob('*')):
            if not asset.is_file():
                continue
            relative = asset.relative_to(args.runtime).as_posix()
            if asset.name == 'default.vlt':
                with tarfile.open(asset) as archive:
                    for member in archive:
                        if member.isfile():
                            assert member.name.startswith('default/')
                            source = 'share/skins2/' + member.name
                            if member.name == 'default/subX/FreeSans.ttf':
                                source = 'share/skins2/fonts/FreeSans.ttf'
                            record(relative + '!/' + member.name, source, archive.extractfile(member).read())
                continue
            if asset.suffix.lower() not in suffixes:
                continue
            source = ('share/skins2/' + relative.removeprefix('skins/')) if directory == 'skins' else 'share/' + relative
            record(relative, source, asset.read_bytes())
    assert any(item['package_path'].endswith('.sofa') for item in records)
    assert any('default.vlt!/' in item['package_path'] for item in records)
    catalogs = []
    for catalog in sorted((args.runtime / 'locale').glob('*/LC_MESSAGES/vlc.mo')):
        language = catalog.parent.parent.name
        source_path = 'po/' + language + '.po'
        source = subprocess.check_output(['git', '-C', str(repo), 'show', 'HEAD:' + source_path])
        blob = catalog.read_bytes()
        with catalog.open('rb') as stream:
            translation = gettext.GNUTranslations(stream)
        catalogs.append({'package_path': catalog.relative_to(args.runtime).as_posix(),
            'sha256': hashlib.sha256(blob).hexdigest(), 'bytes': len(blob),
            'source_path': source_path, 'source_revision': subprocess.check_output(
                ['git', '-C', str(repo), 'rev-parse', 'HEAD'], text=True).strip(),
            'source_sha256': hashlib.sha256(source).hexdigest(),
            'header': translation.info(), 'translated_entries': len(translation._catalog) - 1,
            'binding': 'Generated catalog parsed successfully; source and catalog identities recorded separately, not byte-equivalent formats.'})
    assert any(item['package_path'] == 'locale/el/LC_MESSAGES/vlc.mo' for item in catalogs), 'Language catalogs are required'
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({'schema': 'vlc_redesign.loose_asset_inventory.v1',
        'assets': records, 'all_source_bytes_verified': True, 'language_catalogs': catalogs,
        'missing_font_license_grants': missing_grants,
        'separate_final_gate': 'Preserve all corresponding full font/media notices in the actual delivered package.'}, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'assets_verified': len(records), 'missing_font_license_grants': missing_grants, 'output': str(args.output)}))
    return 1 if missing_grants else 0


if __name__ == '__main__':
    raise SystemExit(main())
