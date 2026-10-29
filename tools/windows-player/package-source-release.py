"""Package commit-bound application/library source without Git history or tools.

The intentional versioned deliverable stays on D:. Private font downloads,
diagnostic profiles, compiler trees and VM/image exports are never inputs.
"""
import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import tarfile


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def validate_application_entry(item, prefix):
    path = PurePosixPath(item.name)
    assert not path.is_absolute() and '..' not in path.parts, item.name
    # tarfile removes the trailing slash from Git's directory entry.
    assert (item.name == prefix and item.isdir()) or item.name.startswith(prefix + '/'), item.name


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-commit', required=True)
    parser.add_argument('--version', required=True)
    parser.add_argument('--sources', type=Path, required=True)
    parser.add_argument('--notices', type=Path, required=True)
    parser.add_argument('--destination', type=Path, required=True)
    parser.add_argument('--scratch', type=Path, required=True)
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[2]
    assert re.fullmatch('[0-9a-f]{40}', args.source_commit)
    assert re.fullmatch(r'\d+\.\d+\.\d+', args.version)
    destination, scratch = args.destination.resolve(), args.scratch.resolve()
    assert destination.is_relative_to(Path('D:/VLC-Redesign'))
    assert scratch.parent.parent == Path('D:/Temp') and scratch.parent.name.startswith('vlc-s7-') and not scratch.exists()
    assert subprocess.check_output(['git', '-C', str(repo), 'rev-parse', 'HEAD'], text=True).strip() == args.source_commit
    assert not subprocess.check_output(['git', '-C', str(repo), 'ls-tree', args.source_commit,
        '--', 'share/skins2/default/subX/font.otf']).strip(), 'Removed font must not be redistributed'
    dependencies = json.loads((args.notices / 'manifest.json').read_text())
    assert len(dependencies.get('embedded_carriers_reviewed', [])) == 4
    assert dependencies.get('host_only_inputs')
    selected = [item for item in dependencies['archives'] if item['release_archive_class'] == 'corresponding-source']
    for item in selected:
        source = args.sources / item['archive']
        # The separately pinned CRT source was fetched outside contrib-sources.
        if item['archive'] == 'mingw-runtime-source.tar.gz':
            source = args.sources.parent / 'downloads' / item['archive']
        assert source.is_file() and digest(source) == item['sha256'], source
        item['resolved_path'] = source
    name = 'Modern-VLC-Fork-' + args.version + '-corresponding-source'
    destination.mkdir(parents=True, exist_ok=True)
    archive = destination / (name + '.tar.gz')
    assert not archive.exists()
    scratch.mkdir()
    records = []

    def add_bytes(output, relative, blob):
        info = tarfile.TarInfo(name + '/' + relative)
        info.mode, info.mtime, info.size = 0o644, 1793232000, len(blob)
        output.addfile(info, io.BytesIO(blob))
        records.append({'path': relative, 'bytes': len(blob), 'sha256': hashlib.sha256(blob).hexdigest()})

    with archive.open('xb') as raw, gzip.GzipFile(filename='', fileobj=raw, mode='wb', mtime=0) as compressed, \
            tarfile.open(fileobj=compressed, mode='w|') as output:
        with (scratch / 'git-archive.stderr').open('wb') as error:
            process = subprocess.Popen(['git', '-C', str(repo), 'archive', '--format=tar',
                '--prefix=' + name + '/application/', args.source_commit], stdout=subprocess.PIPE, stderr=error)
            try:
                with tarfile.open(fileobj=process.stdout, mode='r|') as application:
                    for item in application:
                        validate_application_entry(item, name + '/application')
                        assert item.name != name + '/application/share/skins2/default/subX/font.otf'
                        assert '.git' not in Path(item.name).parts
                        relative = item.name.removeprefix(name + '/')
                        if item.isfile():
                            blob = application.extractfile(item).read()
                            output.addfile(item, io.BytesIO(blob))
                            records.append({'path': relative, 'bytes': len(blob),
                                'sha256': hashlib.sha256(blob).hexdigest()})
                        else:
                            output.addfile(item)
                            if item.issym() or item.islnk():
                                records.append({'path': relative, 'link_target': item.linkname})
            finally:
                process.stdout.close()
                result = process.wait()
            assert result == 0, (scratch / 'git-archive.stderr').read_text(errors='replace')
        for item in selected:
            source = item['resolved_path']
            info = tarfile.TarInfo(name + '/dependencies/' + source.name)
            info.size, info.mode, info.mtime = source.stat().st_size, 0o644, 1793232000
            with source.open('rb') as stream:
                output.addfile(info, stream)
            records.append({'path': 'dependencies/' + source.name, 'bytes': info.size, 'sha256': item['sha256']})
        add_bytes(output, 'dependency-source-and-notice-manifest.json', (args.notices / 'manifest.json').read_bytes())
        readme = ('Modern VLC Fork ' + args.version + ' corresponding source\n\n'
            'Application commit: ' + args.source_commit + '\n'
            'The application/ tree is git archive of that exact commit, without Git history.\n'
            'dependencies/ contains the recorded original source archives for linked libraries.\n'
            'See application/doc/redesign/REPRODUCTION.md for pinned tools, maintained patches,\n'
            'configuration, build, normal packaging, relinking and profile-preserving recovery.\n'
            'Rebuild Qt with changes, then relink the application using those same instructions.\n'
            'The portable product imposes no signing or device-activation restriction on that result.\n\n'
            'Component license and copyright statements remain in their original sources.\n'
            'The combined Qt 6 application is conveyed under GNU GPL version 3.\n'
            'The binary package includes the GPLv3 text and complete dependency notices.\n\n'
            'Host compiler/installer tool bundles are classified separately in the manifest.\n'
            'They are absent from the portable application and are not republished here; pinned\n'
            'retrieval/build rules remain in application/contrib and the reproduction instructions.\n'
            'No downloaded Delicious font, user profile, credential, task-generated playback media, SDK or VM is included.\n')
        add_bytes(output, 'README-SOURCE.txt', readme.encode())
        manifest = {'schema': 'vlc_redesign.corresponding_source.v1', 'source_commit': args.source_commit,
            'version': args.version, 'files': records,
            'host_only_inputs': dependencies['host_only_inputs'], 'private_font_payload_included': False}
        info = json.dumps(manifest, indent=2).encode() + b'\n'
        add_bytes(output, 'SOURCE-MANIFEST.json', info)
    result = {'archive': str(archive), 'bytes': archive.stat().st_size, 'sha256': digest(archive),
        'source_commit': args.source_commit, 'version': args.version,
        'delivery_verification': 'Pending independent archive and published readback.'}
    (destination / 'source-package-result.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result), flush=True)


if __name__ == '__main__':
    main()
