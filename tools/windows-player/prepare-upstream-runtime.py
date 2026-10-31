"""Create a fresh upstream candidate from retained nonbinary resources and notices."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tarfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime', required=True, type=Path)
    parser.add_argument('--notices', required=True, type=Path)
    args = parser.parse_args()
    assert Path('/proc/self/cgroup').read_text().split('::', 1)[1].strip().startswith('/llm-coordinator/')
    repo = Path(__file__).resolve().parents[2]
    baseline = Path('/scratch/runtime')
    assert baseline != args.runtime and not any((baseline / 'portable').iterdir())
    identity = {'schema': 'vlc_redesign.fresh_upstream_runtime.v1', 'baseline': str(baseline),
        'source_commit': subprocess.check_output(['git', '-C', str(repo), 'rev-parse', 'HEAD'], text=True).strip()}
    binding = json.loads(Path('/scratch/source-binding.json').read_text())
    assert binding['source_commit'] == identity['source_commit']
    identity['upstream_commit'] = binding['upstream_commit']
    marker = args.runtime / 'UPSTREAM-ASSEMBLY.json'
    if args.runtime.exists():
        assert json.loads(marker.read_text()) == identity
    else:
        args.runtime.mkdir(parents=True)
        for path in baseline.rglob('*'):
            relative = path.relative_to(baseline)
            if relative.parts[0] in ('plugins', 'portable') or path.suffix.lower() in ('.exe', '.dll', '.pdb', '.debug'):
                continue
            if path.name in ('MPV-BUILDINFO.json', 'RELEASE-SYMBOLS.json', 'VLC-PLUGIN-BUILDINFO.json'):
                continue
            assert not path.is_symlink()
            if path.is_file():
                target = args.runtime / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(path, target)
        (args.runtime / 'portable').mkdir()
        marker.write_text(json.dumps(identity, indent=2) + '\n')
    old = Path('/scratch/dependency-notices-s8')
    subprocess.run([sys.executable, '-B', str(repo / 'tools/windows-player/inventory-dependency-notices.py'),
        '--sources', '/scratch/mpv-source-inputs', '--merge-existing', baseline / 'licenses/dependencies',
        '--output', str(old), '--verify-existing'], check=True)
    archive = Path('/scratch/mpv-source-inputs/medialibrary-0.14.1.tar.bz2')
    expected = (repo / 'contrib/src/medialibrary/SHA512SUMS').read_text().split()[0]
    with archive.open('rb') as stream:
        assert hashlib.file_digest(stream, 'sha512').hexdigest() == expected
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    if args.notices.exists():
        saved = json.loads((args.notices / 'manifest.json').read_text())
        assert saved['vlc_dependency_overrides'][0]['sha256'] == digest
        return
    shutil.copytree(old, args.notices)
    manifest = json.loads((args.notices / 'manifest.json').read_text())
    notices = []
    with tarfile.open(archive) as tar:
        for item in tar:
            if not item.isfile() or not re.match(r'(?i)^(license|licence|copying|copyright|notice|authors)([._-]|$)', Path(item.name).name):
                continue
            assert '..' not in Path(item.name).parts and not Path(item.name).is_absolute()
            blob = tar.extractfile(item).read()
            target = args.notices / digest[:16] / item.name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(blob)
            notices.append({'archive_path': item.name, 'file': target.relative_to(args.notices).as_posix(),
                'bytes': len(blob), 'sha256': hashlib.sha256(blob).hexdigest()})
    assert notices
    manifest['archives'].append({'archive': archive.name, 'sha256': digest, 'bytes': archive.stat().st_size,
        'release_archive_class': 'corresponding-source', 'notices': notices,
        'notice_coverage': 'Named source license/copyright/notice/authors files; complete archive also delivered.'})
    manifest['vlc_dependency_overrides'] = [{'library': 'medialibrary', 'version': '0.14.1',
        'archive': archive.name, 'sha256': digest, 'upstream_sha512': expected,
        'prefix': '/work/upstream-medialibrary-0.14.1/prefix',
        'replaces': 'SDK medialibrary0.13.0; its archive remains as historical SDK input, not selected for new linkage'}]
    (args.notices / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps({'fresh_runtime': str(args.runtime), 'inventoried_archives': len(manifest['archives']),
        'corresponding_sources': sum(item['release_archive_class'] == 'corresponding-source' for item in manifest['archives']),
        'medialibrary': '0.14.1', 'no_baseline_plugin_binaries_copied': True}), flush=True)


if __name__ == '__main__':
    main()
