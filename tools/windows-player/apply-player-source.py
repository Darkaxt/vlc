"""Apply a verified fork overlay without invalidating unchanged build inputs.

Use only inside the owned toolchain after its predecessor is confirmed empty.
Validate every frozen member before writing; changed bytes get a fresh mtime,
while identical sources keep the timestamps needed by the existing Make graph.
"""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess
import tarfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True, type=Path)
    parser.add_argument('--overlay', required=True, type=Path)
    parser.add_argument('--manifest', required=True, type=Path)
    parser.add_argument('--closed-report', required=True, type=Path)
    args = parser.parse_args()
    group = Path('/proc/self/cgroup').read_text().split('::', 1)[1].strip()
    assert group.startswith('/llm-coordinator/')
    source = args.source.resolve(strict=True)
    assert source == Path('/work/src') and Path('/.vlc-s8-toolchain.json').is_file()
    previous = json.loads(args.closed_report.read_text())
    assert previous['populated'] is False and previous['command_started'] is True
    state = json.loads(Path('/scratch/compilation/state.json').read_text())
    # A killed pipeline can leave a stale "running" checkpoint. The original
    # matching supervisor's empty-group report is the actual lifecycle proof;
    # the pipeline's --after-interruption path reconciles that checkpoint later.
    assert state['schema'] == 'vlc_redesign.compilation_pipeline.v1'
    assert state['attempts'][-1]['cgroup'] == '/llm-coordinator/' + previous['id']
    manifest = json.loads(args.manifest.read_text())
    assert manifest['schema'] == 'vlc_redesign.chroot_overlay.v1'
    assert not manifest.get('removed_sources'), 'Apply authorized tracked deletions separately'
    head = subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip()
    assert head == manifest['overlay_base_commit']
    with args.overlay.open('rb') as stream:
        assert hashlib.file_digest(stream, 'sha256').hexdigest() == manifest['archive_sha256']
    expected = {item['path']: item for item in manifest['files']}
    assert len(expected) == len(manifest['files'])
    payloads = {}
    with tarfile.open(args.overlay, 'r:') as archive:
        for item in archive:
            path = PurePosixPath(item.name)
            assert item.isfile() and not path.is_absolute() and '..' not in path.parts
            assert '.git' not in path.parts and item.name != 'AGENTS.md'
            assert item.name in expected and item.name not in payloads
            target = source / item.name
            assert not target.is_symlink() and target.resolve().is_relative_to(source)
            blob = archive.extractfile(item).read()
            assert len(blob) == expected[item.name]['bytes']
            assert hashlib.sha256(blob).hexdigest() == expected[item.name]['sha256']
            payloads[item.name] = blob
    assert payloads.keys() == expected.keys()
    changed, unchanged = [], []
    for name, blob in payloads.items():
        target = source / name
        if target.is_file() and target.read_bytes() == blob:
            unchanged.append(name)
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(blob)
        assert target.read_bytes() == blob
        changed.append(name)
    receipt = {'schema': 'vlc_redesign.applied_overlay.v1', 'source_head': head,
        'overlay_sha256': manifest['archive_sha256'], 'predecessor': previous['id'],
        'cgroup': group, 'changed': changed, 'unchanged': unchanged}
    args.manifest.with_suffix('.applied.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt), flush=True)


if __name__ == '__main__':
    main()
