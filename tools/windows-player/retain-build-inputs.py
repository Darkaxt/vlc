"""Retain this verified SDK/build cohort for the existing weekly consumer.

Windows-only, same-volume moves after the original workflows exit. This changes
no canonical checkout, installed profile, WSL distribution or virtual disk.
Three bounded private DV clips remain local inputs for that weekly consumer.
Other test profiles/media/captures remain in the original task for cleanup.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess

SOURCE = Path('D:/Temp/vlc-s8-20261029')
DESTINATION = Path('D:/VLC-Redesign/build/windows-x64')
PRIVATE_VALIDATION = {
    'dv-keyframes/p5-selfcontained.mp4': 'ae412bb4f10822c904f8d4b3aba21a443464636bb920b2391d9406a24a1a6442',
    'dv-keyframes/p81-selfcontained.mp4': '88e54200ecf6f0fd488dbdaae46bdde16b4aae56fff751658b90e82aff4e9e07',
    'dv-keyframes/p84-selfcontained.mp4': '2bd63456b8e5debc4560671518e119f9499b38333ba00a1d627cafc6095dfb8b',
}
MEMBERS = ('toolchain', 'mpv-source-inputs', 'downloads', 'scratch-share/runtime',
           'scratch-share/dependency-notices-s8', 'scratch-share/compilation', *PRIVATE_VALIDATION)


def normal_path(path):
    assert path.resolve() == path
    for parent in (path, *path.parents):
        if parent.exists():
            assert not parent.stat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT, parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-commit', required=True)
    parser.add_argument('--closed-report', type=Path, action='append', required=True)
    args = parser.parse_args()
    assert os.name == 'nt' and re.fullmatch('[0-9a-f]{40}', args.source_commit)
    repo = Path(__file__).resolve().parents[2]
    assert subprocess.check_output(['git', '-C', str(repo), 'rev-parse', 'HEAD'], text=True).strip() == args.source_commit
    normal_path(SOURCE)
    normal_path(DESTINATION)
    reports = []
    for path in args.closed_report:
        blob = path.read_bytes()
        result = json.loads(blob)
        assert result['populated'] is False and result['command_started'] is True
        assert result['exit_code'] == 0, 'Complete and verify the selected assembly before retention'
        reports.append({'id': result['id'], 'sha256': hashlib.sha256(blob).hexdigest()})
    journal = DESTINATION / 'build-retention.json'
    if journal.exists():
        saved = json.loads(journal.read_text())
        assert saved['source_commit'] == args.source_commit and saved['closed_reports'] == reports
        assert saved['state'] == 'moving', 'Inspect an already completed retention instead of replaying it'
    else:
        assert not DESTINATION.exists(), 'Preserve an existing project build cohort'
        state = json.loads((SOURCE / 'scratch-share/compilation/state.json').read_text())
        assert state['status'] == 'complete'
        assert state['attempts'][-1]['cgroup'] in ['/llm-coordinator/' + item['id'] for item in reports]
        marker = json.loads((SOURCE / 'toolchain/.vlc-s8-toolchain.json').read_text())
        private = SOURCE / 'toolchain/work/src'
        assert subprocess.check_output(['git', '-C', str(private), 'rev-parse', 'HEAD'], text=True).strip() == args.source_commit
        assert not subprocess.check_output(['git', '-C', str(private), 'status', '--porcelain'], text=True).strip(), 'Bind the verified source commit before retention'
        saved = {'schema': 'vlc_redesign.retained_build.v1', 'state': 'moving',
            'source': SOURCE.as_posix(), 'destination': DESTINATION.as_posix(),
            'consumer': 'vlc-weekly-upstream-sync-and-release', 'source_commit': args.source_commit,
            'toolchain_marker': marker, 'closed_reports': reports,
            'retirement': 'After the pinned cohort is superseded and its weekly/build consumers exit, retire obsolete generated inputs through transactional-cleanup. Preserve required source/provenance and delivery evidence.',
            'private_validation': {
                'consumer': 'vlc-weekly-upstream-sync-and-release',
                'purpose': 'Local P5/P8.1/P8.4 acceptance of the existing Dolby Vision playback requirement',
                'distribution': 'Never include these private clips or their frames in Git/source/binary release assets',
                'retirement': 'Retire through transactional cleanup after replacement or removal of this weekly acceptance consumer',
                'files': PRIVATE_VALIDATION},
            'members': {}}
        for relative in MEMBERS:
            path = SOURCE / relative
            normal_path(path)
            if relative in PRIVATE_VALIDATION:
                with path.open('rb') as stream:
                    assert hashlib.file_digest(stream, 'sha256').hexdigest() == PRIVATE_VALIDATION[relative]
            identity = path.stat()
            saved['members'][relative] = {'volume': identity.st_dev, 'file_id': identity.st_ino}
        DESTINATION.mkdir(parents=True)

    def save():
        temporary = journal.with_suffix('.pending')
        temporary.write_text(json.dumps(saved, indent=2) + '\n')
        temporary.replace(journal)

    save()
    for relative, expected in saved['members'].items():
        source, target = SOURCE / relative, DESTINATION / relative
        normal_path(source)
        normal_path(target)
        assert source.exists() != target.exists(), relative
        if source.exists():
            identity = source.stat()
            assert (identity.st_dev, identity.st_ino) == (expected['volume'], expected['file_id'])
            target.parent.mkdir(parents=True, exist_ok=True)
            source.rename(target)
        identity = target.stat()
        assert (identity.st_dev, identity.st_ino) == (expected['volume'], expected['file_id'])
        expected['moved'] = True
        save()
    for relative, expected_hash in PRIVATE_VALIDATION.items():
        with (DESTINATION / relative).open('rb') as stream:
            assert hashlib.file_digest(stream, 'sha256').hexdigest() == expected_hash
    (DESTINATION / 'inputs.json').write_bytes((SOURCE / 'inputs.json').read_bytes())
    ownership = json.loads((SOURCE / 'evidence/toolchain-filesystem.json').read_text())
    assert ownership['uuid'] == saved['toolchain_marker']['uuid']
    ownership['previous_filesystem'] = ownership['filesystem']
    ownership['filesystem'] = '/mnt/d/VLC-Redesign/build/windows-x64/toolchain'
    ownership['placement'] = 'D: intentional project build inputs for the existing weekly automation'
    (DESTINATION / 'evidence').mkdir(exist_ok=True)
    (DESTINATION / 'evidence/toolchain-filesystem.json').write_text(json.dumps(ownership, indent=2) + '\n')
    saved['state'] = 'moved'
    saved['verification'] = 'Pending gated launch/read-only configuration check at the new binding and inspected group-empty completion'
    save()
    print(json.dumps({'destination': str(DESTINATION), 'state': saved['state'], 'members': saved['members']}))


if __name__ == '__main__':
    main()
