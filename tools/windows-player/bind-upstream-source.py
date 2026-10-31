"""Apply a commit-bound upstream merge to the private build clone, preserving objects."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', required=True, type=Path)
    parser.add_argument('--bundle', required=True, type=Path)
    parser.add_argument('--closed-report', required=True, type=Path)
    args = parser.parse_args()
    group = Path('/proc/self/cgroup').read_text().split('::', 1)[1].strip()
    assert group.startswith('/llm-coordinator/') and Path('/.vlc-s8-toolchain.json').is_file()
    source = Path('/work/src')
    def git(*values):
        return subprocess.check_output(['git', '-C', str(source), *values])
    manifest = json.loads(args.manifest.read_text())
    assert manifest['schema'] == 'vlc_redesign.upstream_source_binding.v1'
    closed = json.loads(args.closed_report.read_text())
    assert closed['populated'] is False and closed['command_started'] is True
    state = json.loads(Path('/scratch/compilation/state.json').read_text())
    assert state['attempts'][-1]['cgroup'] == '/llm-coordinator/' + closed['id']
    assert git('rev-parse', 'HEAD').decode().strip() == manifest['previous_commit']
    assert not git('status', '--porcelain'), 'Preserve unexpected private-clone changes'
    with args.bundle.open('rb') as stream:
        assert hashlib.file_digest(stream, 'sha256').hexdigest() == manifest['bundle_sha256']
    subprocess.run(['git', '-C', str(source), 'fetch', '--no-tags', str(args.bundle), 'HEAD'], check=True)
    commit = manifest['source_commit']
    assert git('rev-parse', 'FETCH_HEAD').decode().strip() == commit
    subprocess.run(['git', '-C', str(source), 'merge-base', '--is-ancestor', manifest['upstream_commit'], commit], check=True)
    patch = git('diff', '--binary', '--full-index', '--no-renames', 'HEAD', commit)
    assert hashlib.sha256(patch).hexdigest() == manifest['patch_sha256']
    for option in ('--check', '--index'):
        subprocess.run(['git', '-C', str(source), 'apply', option, '--whitespace=nowarn', '-'], input=patch, check=True)
    tree = git('write-tree').decode().strip()
    assert tree == git('rev-parse', commit + '^{tree}').decode().strip()
    subprocess.run(['git', '-C', str(source), 'update-ref', 'HEAD', commit, manifest['previous_commit']], check=True)
    assert not git('status', '--porcelain')
    receipt = dict(manifest, group=group, predecessor=closed['id'], tree=tree,
        source_mtimes_preserved_for_unchanged_files=True, private_clone_clean=True)
    Path('/scratch/source-binding.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt), flush=True)


if __name__ == '__main__':
    main()
