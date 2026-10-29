"""Retain known embedded license carriers and classify host-only source inputs.

Run once after the source notice inventory succeeds. This reads the unmodified
archives and augments that actual inventory; it does not fetch or publish files.
"""
import argparse
import hashlib
import json
from pathlib import Path
import tarfile

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--sources', type=Path, required=True)
parser.add_argument('--notices', type=Path, required=True)
parser.add_argument('--resume-partial', action='store_true', help='Reuse only exact verified carrier bytes from an interrupted augmentation')
args = parser.parse_args()
manifest_path = args.notices / 'manifest.json'
manifest = json.loads(manifest_path.read_text())
assert not manifest.get('embedded_carriers_reviewed'), 'Preserve the completed inventory'
carriers = {
    'AMF-1.5.2.tar.gz': ['amf-headers-v1.5.2/AMF/core/Platform.h'],
    'decklink-1977bf76bb5bde80d171373cf8d80dd01161679b.tar.xz': [
        'decklink-1977bf76bb5bde80d171373cf8d80dd01161679b/Win/include/DeckLinkAPI.idl'],
    'lua-5.4.4.tar.gz': ['lua-5.4.4/src/lua.h'],
    'nv-codec-headers-13.1.15.0.tar.gz': ['nv-codec-headers-13.1.15.0/include/ffnvcodec/nvEncodeAPI.h'],
}
seen = set()
for record in manifest['archives']:
    filename = record['archive']
    if filename not in carriers:
        continue
    archive = args.sources / filename
    with archive.open('rb') as stream:
        assert hashlib.file_digest(stream, 'sha256').hexdigest() == record['sha256'], filename
    with tarfile.open(archive, 'r:*') as source:
        for member in carriers[filename]:
            data = source.extractfile(member).read()
            assert b'Permission is hereby granted' in data and b'Copyright' in data, member
            relative = Path(record['sha256'][:16]) / member
            target = args.notices / relative
            if target.exists():
                assert args.resume_partial and target.is_file() and target.read_bytes() == data, target
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                with target.open('xb') as output:
                    output.write(data)
            record['notices'].append({'archive_path': member, 'file': relative.as_posix(),
                'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(),
                'embedded_license_carrier': True})
    seen.add(filename)
assert seen == set(carriers)
host_only = []
for record in manifest['archives']:
    name = record['archive']
    if name.startswith('fxc2-') or name.startswith('wix3.'):
        host_only.append({'archive': name, 'sha256': record['sha256'],
            'distribution': 'Excluded from the application binary and corresponding-library source package.',
            'reason': 'Host shader compiler or installer tooling, not a linked application library. The portable product contains no installer or copied compiler. Upstream pinned retrieval/build rules remain in application source.',
            'license_review': 'fxc2 pin carries no standalone grant and includes Microsoft compiler DLLs; no redistribution grant is inferred. WiX binary tool bundles are not represented as library source.'})
        record['release_archive_class'] = 'host-tool-not-redistributed'
    else:
        record['release_archive_class'] = 'corresponding-source'
assert len(host_only) == 3, host_only
manifest['host_only_inputs'] = host_only
manifest['embedded_carriers_reviewed'] = sorted(seen)
manifest['release_gate'] = 'Binary must ship complete notices and GPLv3 text; corresponding source includes actual library archives, maintained patches and build/relink instructions. Independent package verification remains required.'
manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')
print(json.dumps({'embedded_carriers_retained': sorted(seen), 'host_only_inputs': host_only}))
