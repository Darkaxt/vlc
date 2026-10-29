"""Bind the real Qt resource inputs to their retained design/font provenance.

This inventories production resource sources. Final binary notice/source and
native appearance checks are separate S7 acceptance requirements.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import urllib.request
import xml.etree.ElementTree as ET

BASELINE = '392bc1d0abdb7396b6c97fef206efa1d23868e19'
FIGMA_HASH = '86637a31ad4ffbcaddc89244e0588df2c0cbe0954a6fe87c7bf5b6a65345e49e'
FLUENT_REF = '64e5aa757d1b70c24a283256ddcb8269d0f58773'


def digest(path):
    with path.open('rb') as source:
        return hashlib.file_digest(source, 'sha256').hexdigest()


def manifest_entries(value):
    if isinstance(value, dict):
        if 'filename' in value and 'sha256' in value:
            yield value
        for child in value.values():
            yield from manifest_entries(child)
    elif isinstance(value, list):
        for child in value:
            yield from manifest_entries(child)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    options = parser.parse_args()
    repo = Path(__file__).resolve().parents[2]
    qt = repo / 'modules/gui/qt'
    design = qt / 'pixmaps/redesign'
    manifest = json.loads((design / 'manifest.json').read_text())
    assert manifest['source_sha256'] == FIGMA_HASH
    assert digest(repo / 'doc/redesign/resources/vlc-redesign.fig') == FIGMA_HASH
    entries = {entry['filename']: entry for entry in manifest_entries(manifest)}
    resources, custom_names = [], set()
    for qrc in [qt / 'assets.qrc', qt / 'windows.qrc']:
        for group in ET.parse(qrc).getroot().findall('qresource'):
            for item in group.findall('file'):
                asset = (qt / item.text).resolve()
                if asset.suffix.lower() not in {'.svg', '.svgz', '.png', '.jpg', '.jpeg', '.bmp', '.gif', '.webp', '.ico', '.ttf', '.otf', '.mp4', '.wav'}:
                    continue  # QML, JavaScript, shaders and text are code, not media/font/icon inputs.
                path = asset.relative_to(repo).as_posix()
                content = asset.read_bytes() if asset.is_file() else subprocess.check_output(['git', '-C', str(repo), 'show', 'HEAD:' + path])
                record = {'path': path, 'resource': group.get('prefix', '') + '/' + item.get('alias', item.text),
                    'sha256': hashlib.sha256(content).hexdigest(), 'bytes': len(content),
                    'input_source': 'working tree' if asset.is_file() else 'HEAD object outside sparse checkout'}
                if asset.parent == design:
                    source = entries[asset.name]
                    assert record['sha256'] == source['sha256'], path
                    record.update(license='CC-BY-4.0', creator='Juxtopposed',
                        source='https://www.figma.com/community/file/1691465999134370980/vlc-redesign',
                        source_node=source.get('id'), changes=manifest['extraction'])
                    custom_names.add(asset.name)
                elif asset.name == 'InterVariable.ttf' and 'redesign' in asset.parts:
                    record.update(license='OFL-1.1', creator='The Inter Project Authors',
                        provenance='modules/gui/qt/fonts/redesign/source.json',
                        notice='modules/gui/qt/fonts/redesign/LICENSE.txt', changes='Unmodified retained upstream font')
                else:
                    original = subprocess.check_output(['git', '-C', str(repo), 'show', BASELINE + ':' + path])
                    assert hashlib.sha256(original).hexdigest() == record['sha256'], 'Unreviewed upstream resource change: ' + path
                    record.update(source_revision=BASELINE, license='GPL-2.0-or-later',
                        notice='COPYING; AUTHORS; THANKS; retained per-file notices',
                        provenance='Unmodified upstream VLC production resource; preserve existing source notices and COPYING')
                    if asset.name == 'VLCIcons.ttf':
                        record.update(license='GPL-2.0-or-later AND MIT',
                            glyph_sources='modules/gui/qt/pixmaps/VLCIcons.json',
                            additional_notice='doc/redesign/resources/s7/FLUENT-ICONS-LICENSE.txt')
                resources.append(record)
    all_svg = {path.name for path in design.glob('*.svg')}
    assert custom_names == all_svg == set(entries), {'unregistered': sorted(all_svg - custom_names), 'unused': sorted(set(entries) - custom_names)}
    font_provenance = json.loads((qt / 'fonts/redesign/source.json').read_text())
    upstream_font = font_provenance['repo'].replace('https://github.com/', 'https://raw.githubusercontent.com/')
    verified_font_sources = []
    for name in font_provenance['files']:
        url = upstream_font + '/' + font_provenance['revision'] + '/' + name
        with urllib.request.urlopen(url) as source:
            upstream_digest = hashlib.file_digest(source, 'sha256').hexdigest()
        local = qt / 'fonts/redesign' / Path(name).name
        # Git normalizes the text license's line endings. Font bytes must match.
        if local.suffix == '.ttf':
            assert digest(local) == upstream_digest, str(local)
        verified_font_sources.append({'url': url, 'upstream_sha256': upstream_digest, 'local_sha256': digest(local)})
    glyphs = []
    icon_font = qt / 'pixmaps/VLCIcons.json'
    for glyph in json.loads(icon_font.read_text())['glyphs']:
        source = (icon_font.parent / glyph['path']).resolve()
        relative = source.relative_to(repo).as_posix()
        content = source.read_bytes() if source.is_file() else subprocess.check_output(['git', '-C', str(repo), 'show', 'HEAD:' + relative])
        original = subprocess.check_output(['git', '-C', str(repo), 'show', BASELINE + ':' + relative])
        assert content.replace(b'\r\n', b'\n') == original.replace(b'\r\n', b'\n'), relative
        glyphs.append({'key': glyph['key'], 'path': relative,
            'sha256': hashlib.sha256(content.replace(b'\r\n', b'\n')).hexdigest(),
            'license': 'MIT' if source.name.startswith('ic_fluent_') else 'GPL-2.0-or-later',
            'provenance': 'Unmodified glyph source named in the pinned upstream VLC font manifest'})
    fluent_url = 'https://raw.githubusercontent.com/microsoft/fluentui-system-icons/' + FLUENT_REF + '/LICENSE'
    with urllib.request.urlopen(fluent_url) as response:
        fluent_license = response.read().replace(b'\r\n', b'\n')
    assert fluent_license.startswith(b'MIT License') and b'Microsoft Corporation' in fluent_license
    notice = repo / 'doc/redesign/resources/s7/FLUENT-ICONS-LICENSE.txt'
    if notice.exists():
        assert notice.read_bytes().replace(b'\r\n', b'\n') == fluent_license
    else:
        notice.parent.mkdir(parents=True, exist_ok=True)
        notice.write_bytes(fluent_license)
    output = {'schema': 'vlc_redesign.production_resource_inventory.v1', 'source_baseline': BASELINE,
        'figma_sha256': FIGMA_HASH, 'resources': resources, 'font_source_readback': verified_font_sources,
        'upstream_icon_font_glyphs': glyphs,
        'fluent_notice': {'url': fluent_url, 'sha256': hashlib.sha256(fluent_license).hexdigest(),
            'scope': 'MIT notice for retained upstream Fluent-named icon glyphs; no new replacement glyphs downloaded.'},
        'production_media_policy': 'No embedded Figma raster artwork or test media promoted into new production assets. Existing unchanged upstream resources remain inventoried above.',
        'separate_final_gates': ['Package all design/font and upstream/dependency notices.',
            'Provide matching application and modified-dependency source/build inputs for the final package.',
            'Verify actual final normal runtime and complete native presentation matrix.'],
        'custom_assets_verified': True}
    options.output.parent.mkdir(parents=True, exist_ok=True)
    options.output.write_text(json.dumps(output, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'custom_assets_verified': True, 'resource_count': len(resources), 'design_vectors': len(custom_names), 'output': str(options.output)}))


if __name__ == '__main__':
    main()
