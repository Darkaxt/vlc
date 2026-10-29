"""Stage the maintained fork delta for the pinned baseline's isolated chroot.

No build, extraction, deletion, or WSL operation occurs here. The archive and
per-file identity manifest are written to an explicit task-owned scratch root.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tarfile

BASELINE = '392bc1d0abdb7396b6c97fef206efa1d23868e19'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--tests-only', action='store_true')
    group.add_argument('--wasapi-only', action='store_true')
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[2]
    output = args.output.resolve()
    assert output.drive.upper() == 'D:' and output.parent.parent == Path('D:/Temp')
    assert output.parent.name.startswith('vlc-s7-') and output.suffix == '.tar'
    assert not output.exists() and not output.with_suffix('.json').exists()

    def git(*arguments):
        return subprocess.check_output(['git', '-C', str(repo), *arguments]).decode('utf-8').splitlines()

    narrow = args.tests_only or args.wasapi_only
    if narrow:
        names = ['tools/windows-player/wasapi-lifecycle-check.c', 'tools/windows-player/build-wasapi-check.sh']
        if args.wasapi_only:
            names.append('modules/audio_output/wasapi.c')
    else:
        removed = git('diff', '--name-only', '--diff-filter=D', BASELINE)
        assert set(removed) <= {'share/skins2/default/subX/font.otf'}, 'Unreviewed source deletion: ' + repr(removed)
        names = git('diff', '--name-only', '--diff-filter=d', BASELINE)
        names += git('ls-files', '--others', '--exclude-standard', 'tools/windows-baseline',
            'tools/windows-player', 'doc/redesign/resources/s7')
    records = []
    with tarfile.open(output, 'w') as archive:
        for name in sorted(set(names)):
            source = repo / name
            assert not source.is_symlink(), name
            assert source.suffix != '.pyc' and '__pycache__' not in source.parts, name
            if source.is_file():
                blob = source.read_bytes()
                origin = 'working tree'
            else:
                flags = git('ls-files', '-v', '--', name)
                assert len(flags) == 1 and flags[0].startswith('S '), 'Missing non-sparse source: ' + name
                blob = subprocess.check_output(['git', '-C', str(repo), 'show', ':' + name])
                origin = 'Git index outside sparse checkout'
            if source.suffix.lower() in {'.c', '.h', '.cpp', '.hpp', '.sh', '.py', '.qml', '.js', '.mjs', '.json', '.md', '.txt', '.qrc', '.pro', '.patch', '.am', '.mak'}:
                blob = blob.replace(b'\r\n', b'\n')
            info = tarfile.TarInfo(name)
            info.size, info.mode = len(blob), 0o644
            archive.addfile(info, io.BytesIO(blob))
            records.append({'path': name, 'bytes': len(blob), 'sha256': hashlib.sha256(blob).hexdigest(), 'origin': origin})
    with output.open('rb') as stream:
        archive_digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    manifest = {'schema': 'vlc_redesign.chroot_overlay.v1', 'upstream_baseline': BASELINE,
        'fork_head_before_uncommitted_s7': git('rev-parse', 'HEAD')[0], 'tests_only': args.tests_only,
        'wasapi_only': args.wasapi_only,
        'archive': output.name, 'archive_sha256': archive_digest,
        'files': records}
    if not narrow and removed:
        patch = output.with_suffix('.deletions.patch')
        assert not patch.exists()
        blob = subprocess.check_output(['git', '-C', str(repo), 'diff', '--binary', BASELINE, '--', *removed])
        patch.write_bytes(blob)
        manifest['removed_sources'] = removed
        manifest['deletion_patch'] = {'file': patch.name, 'sha256': hashlib.sha256(blob).hexdigest(),
            'application': 'Inspect, git apply --check, then git apply in the disposable source checkout. This is an authorized tracked source change, not temporary-file cleanup.'}
    output.with_suffix('.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'archive': str(output), 'files': len(records), 'sha256': manifest['archive_sha256']}))


if __name__ == '__main__':
    main()
