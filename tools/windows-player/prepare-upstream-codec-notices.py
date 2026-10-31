"""Add source-bound codec overrides and notices to the existing release inventory."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import tarfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--notices', type=Path, required=True)
    parser.add_argument('--sources', type=Path, default=Path('/scratch/mpv-source-inputs'))
    parser.add_argument('--build-receipt', type=Path, default=Path('/work/upstream-codecs-1.1.1/build-receipt.json'))
    args = parser.parse_args()
    receipt = json.loads(args.build_receipt.read_text())
    manifest_path = args.notices / 'manifest.json'
    manifest = json.loads(manifest_path.read_text())
    for record in receipt['libraries']:
        archive = args.sources / record['archive']
        with archive.open('rb') as stream:
            digest = hashlib.file_digest(stream, 'sha256').hexdigest()
        assert digest == record['archive_sha256']
        existing = next((item for item in manifest['archives'] if item['archive'] == archive.name), None)
        notices = []
        with tarfile.open(archive) as tar:
            for item in tar:
                if not item.isfile() or not re.match(r'(?i)^(license|licence|copying|copyright|notice|authors|patents)([._-]|$)', Path(item.name).name):
                    continue
                assert '..' not in Path(item.name).parts and not Path(item.name).is_absolute()
                blob = tar.extractfile(item).read()
                target = args.notices / digest[:16] / item.name
                if target.exists():
                    assert target.read_bytes() == blob
                else:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(blob)
                notices.append({'archive_path': item.name, 'file': target.relative_to(args.notices).as_posix(),
                    'bytes': len(blob), 'sha256': hashlib.sha256(blob).hexdigest()})
        assert notices
        entry = {'archive': archive.name, 'sha256': digest, 'bytes': archive.stat().st_size,
            'release_archive_class': 'corresponding-source', 'notices': notices,
            'notice_coverage': 'Named source license/patent/copyright/notice/authors files; complete archive also delivered.'}
        if existing:
            for key in ('archive', 'sha256', 'bytes', 'release_archive_class'):
                assert existing[key] == entry[key]
            assert all(item in notices for item in existing['notices']), 'Preserve verified notice identities'
            manifest['archives'][manifest['archives'].index(existing)] = entry
        else:
            manifest['archives'].append(entry)
        override = {'library': record['library'], 'version': record['version'],
            'archive': archive.name, 'sha256': digest, 'upstream_sha512': record['sha512'],
            'prefix': record['prefix'], 'patches': record['patches'],
            'replaces': 'Previous compatible SDK version; its archive remains as historical SDK input, not selected for this VLC plugin linkage'}
        old_override = next((item for item in manifest['vlc_dependency_overrides'] if item['library'] == record['library']), None)
        if old_override:
            assert old_override == override
        else:
            manifest['vlc_dependency_overrides'].append(override)
    pending = manifest_path.with_suffix('.pending')
    pending.write_text(json.dumps(manifest, indent=2) + '\n')
    pending.replace(manifest_path)
    print(json.dumps({'codec_overrides': [item['library'] for item in receipt['libraries']],
        'corresponding_sources': sum(item['release_archive_class'] == 'corresponding-source' for item in manifest['archives'])}), flush=True)


if __name__ == '__main__':
    main()
