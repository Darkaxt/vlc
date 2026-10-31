"""Inventory fetched corresponding-source archives and retain their notices.

Run under the WSL gate after collect-dependency-sources.sh. Archive payloads
remain unmodified; only notice text is extracted into a fresh output folder.
"""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import tarfile
import zipfile


def notice_name(name):
    path = PurePosixPath(name)
    return bool(re.match(r'(?i)^(license|licence|copying|copyright|notice|authors)([._-]|$)', path.name)
        or any(part.lower() in ('licenses', 'licences') for part in path.parts[:-1]))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sources', type=Path, default=Path('/scratch/contrib-sources'))
    parser.add_argument('--output', type=Path, default=Path('/scratch/dependency-notices'))
    parser.add_argument('--extra-source', action='append', type=Path, default=[])
    parser.add_argument('--merge-existing', type=Path,
                        help='Retain the verified SDK inventory and add the source-built MPV inputs')
    parser.add_argument('--verify-existing', action='store_true',
                        help='Verify unchanged source and notice identities before reusing a completed inventory')
    args = parser.parse_args()
    if args.verify_existing:
        assert args.merge_existing and not args.extra_source
        saved = json.loads((args.output / 'manifest.json').read_text())
        assert saved['schema'] == 'vlc_redesign.dependency_notices.v1'
        baseline = (args.merge_existing / 'manifest.json').read_bytes()
        assert saved['baseline_sdk_manifest_sha256'] == hashlib.sha256(baseline).hexdigest()
        baseline_records = json.loads(baseline)
        actual_archives = {item['archive']: item['sha256'] for item in saved['archives']}
        assert all(actual_archives[item['archive']] == item['sha256'] for item in baseline_records['archives'])
        pins = json.loads((Path(__file__).resolve().parents[2] / 'modules/gui/qt/player/mpv/source.json').read_text())
        expected = {(item.get('archive') or item['repository'].split('/')[1] + '-' + item['commit'] + '.tar.gz'): item['sha256']
                    for item in pins['sources']}
        assert {item['archive']: item['sha256'] for item in saved['mpv_sources']} == expected
        assert saved['host_only_inputs'] == baseline_records['host_only_inputs'] + pins.get('host_tools', [])
        compiler = {key: subprocess.check_output(['x86_64-w64-mingw32-gcc', flag], text=True).strip()
                    for key, flag in (('version', '-dumpfullversion'), ('target', '-dumpmachine'))}
        assert compiler == saved['compiler'] == baseline_records['compiler']
        for name, expected_hash in expected.items():
            with (args.sources / name).open('rb') as stream:
                assert hashlib.file_digest(stream, 'sha256').hexdigest() == expected_hash, name
        count = 0
        for notice_list in [*(archive['notices'] for archive in saved['archives']), saved['compiler_runtime_notices']]:
            for item in notice_list:
                relative = PurePosixPath(item['file'])
                assert not relative.is_absolute() and '..' not in relative.parts
                with (args.output / Path(*relative.parts)).open('rb') as stream:
                    assert hashlib.file_digest(stream, 'sha256').hexdigest() == item['sha256'], item['file']
                count += 1
        print(json.dumps({'verified_existing_notices': str(args.output), 'source_archives': len(expected),
                          'notice_files': count, 'baseline_sdk_sha256': hashlib.sha256(baseline).hexdigest()}))
        return
    assert not args.output.exists(), 'Preserve existing inventory; choose a fresh exact output'
    existing = None
    if args.merge_existing:
        original = (args.merge_existing / 'manifest.json').read_bytes()
        existing = json.loads(original)
        assert len(existing['embedded_carriers_reviewed']) == 4 and existing['host_only_inputs']
        assert not existing.get('mpv_sources'), 'Preserve an already merged inventory'
        shutil.copytree(args.merge_existing, args.output)
        (args.output / 'baseline-sdk-manifest.json').write_bytes(original)
    else:
        args.output.mkdir(parents=True)
    records = list(existing['archives']) if existing else []
    added = []
    inputs = sorted(path for path in args.sources.iterdir() if path.is_file())
    source_revisions = list(existing['source_revision_records']) if existing else []
    source_markers = list(existing['upstream_source_markers']) if existing else []
    for path in inputs:
        if path.suffix == '.githash':
            fields = path.read_text(encoding='utf-8').split()
            assert len(fields) == 2 and re.fullmatch('[0-9a-f]{40}', fields[0]), path
            source_revisions.append({'file': path.name, 'revision': fields[0],
                'archive': Path(fields[1]).name, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
        elif path.name.endswith('.skip-hash'):
            # Created by contrib's vendored Rust-source rule, not an archive.
            archive_name = path.name.removesuffix('.skip-hash')
            assert path.stat().st_size == 0 and (args.sources / archive_name).is_file(), path
            source_markers.append({'file': path.name, 'bytes': 0, 'archive': archive_name,
                'meaning': 'Upstream contrib marker bypasses its archive checksum step; this inventory records actual archive SHA-256, not an independently verified expected checksum.'})
    archives = [path for path in inputs if path.suffix != '.githash'
        and not path.name.endswith('.skip-hash')] + args.extra_source
    for archive in archives:
        assert archive.name not in {item['archive'] for item in records}, archive
        print(json.dumps({'reading_archive': archive.name}), flush=True)
        with archive.open('rb') as stream:
            digest = hashlib.file_digest(stream, 'sha256').hexdigest()
        notices = []
        def retain(name, size, read):
            if not notice_name(name):
                return
            relative = PurePosixPath(name)
            assert not relative.is_absolute() and '..' not in relative.parts, name
            assert size <= 8 * 1024 * 1024, 'Inspect unusually large notice: ' + name
            data = read()
            assert len(data) == size
            target = args.output / digest[:16] / Path(*relative.parts)
            assert not target.exists(), name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            notices.append({'archive_path': name, 'file': target.relative_to(args.output).as_posix(),
                'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()})
        if zipfile.is_zipfile(archive):
            with zipfile.ZipFile(archive) as source:
                for item in source.infolist():
                    if not item.is_dir():
                        retain(item.filename, item.file_size, lambda item=item: source.read(item))
        else:
            decoder = None
            if archive.suffix == '.zst':
                decoder = subprocess.Popen(['zstd', '-dc', str(archive)], stdout=subprocess.PIPE)
                stream = decoder.stdout
            else:
                stream = archive.open('rb')
            try:
                # Regular compressed readers handle concatenated bzip2 members.
                # tarfile's streaming bzip2 decoder stops after the first one
                # in the original MinGW archive. Keep streaming for the explicit
                # zstd subprocess, whose output is already uncompressed tar.
                with tarfile.open(fileobj=stream, mode='r|' if decoder else 'r:*') as source:
                    for item in source:
                        if item.isfile():
                            retain(item.name, item.size, lambda item=item: source.extractfile(item).read())
            finally:
                stream.close()
                if decoder:
                    assert decoder.wait() == 0, 'Source decompression failed: ' + str(archive)
        record = {'archive': archive.name, 'bytes': archive.stat().st_size,
            'sha256': digest, 'notices': notices,
            'notice_coverage': 'Retained named license/copyright/notice/authors files recursively; full corresponding source archive remains authoritative.'}
        if existing:
            record['release_archive_class'] = 'corresponding-source'
        records.append(record)
        added.append(record)
        print(json.dumps({'archive': archive.name, 'notices': len(notices)}), flush=True)
    compiler_notices = []
    for relative in ('doc/gcc-mingw-w64-x86-64-posix/copyright',
            'doc/g++-mingw-w64-x86-64-posix/copyright', 'doc/gcc-14-base/copyright',
            'common-licenses/GPL-2', 'common-licenses/GPL-3',
            'common-licenses/LGPL-2.1', 'common-licenses/LGPL-3'):
        source = Path('/usr/share') / relative
        blob = source.read_bytes()
        target = args.output / 'compiler-runtime' / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(blob)
        compiler_notices.append({'source_image_path': str(source), 'file': target.relative_to(args.output).as_posix(),
            'bytes': len(blob), 'sha256': hashlib.sha256(blob).hexdigest()})
    compiler = {key: subprocess.check_output(['x86_64-w64-mingw32-gcc', flag], text=True).strip()
        for key, flag in (('version', '-dumpfullversion'), ('target', '-dumpmachine'))}
    manifest = {'schema': 'vlc_redesign.dependency_notices.v1', 'archives': records,
        'source_revision_records': source_revisions,
        'upstream_source_markers': source_markers,
        'compiler': compiler, 'compiler_runtime_notices': compiler_notices,
        'notice_source_image': 'registry.videolan.org/vlc-debian-win64-posix@sha256:8e83e800036f8f4a6da1031a6b80c2b5bad8337259c072ffa22398baaeaad880',
        'selection': 'The configured Windows contrib package selection, with found-package detection disabled only for source fetching; plus explicit MinGW source.',
        'limits': 'This records actual archives/notices, not a substitute for linking-license compatibility review or final package/source delivery verification.'}
    if existing:
        assert compiler == existing['compiler'], 'Do not mix a different compiler/runtime SDK'
        pins = json.loads((Path(__file__).resolve().parents[2] / 'modules/gui/qt/player/mpv/source.json').read_text())
        expected = {(item.get('archive') or item['repository'].split('/')[1] + '-' + item['commit'] + '.tar.gz'): item['sha256']
                    for item in pins['sources']}
        assert {item['archive']: item['sha256'] for item in added} == expected
        manifest.update(embedded_carriers_reviewed=existing['embedded_carriers_reviewed'],
                        host_only_inputs=existing['host_only_inputs'] + pins.get('host_tools', []), release_gate=existing['release_gate'],
                        baseline_sdk_manifest_sha256=hashlib.sha256(original).hexdigest(),
                        mpv_sources=[{'archive': item['archive'], 'sha256': item['sha256']} for item in added])
    (args.output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')


if __name__ == '__main__':
    main()
