"""Inventory fetched corresponding-source archives and retain their notices.

Run under the WSL gate after collect-dependency-sources.sh. Archive payloads
remain unmodified; only notice text is extracted into a fresh output folder.
"""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
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
    args = parser.parse_args()
    assert not args.output.exists(), 'Preserve existing inventory; choose a fresh exact output'
    args.output.mkdir(parents=True)
    records = []
    inputs = sorted(path for path in args.sources.iterdir() if path.is_file())
    source_revisions = []
    source_markers = []
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
        records.append({'archive': archive.name, 'bytes': archive.stat().st_size,
            'sha256': digest, 'notices': notices,
            'notice_coverage': 'Retained named license/copyright/notice/authors files recursively; full corresponding source archive remains authoritative.'})
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
    (args.output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')


if __name__ == '__main__':
    main()
