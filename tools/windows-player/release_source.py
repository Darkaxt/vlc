"""Bind artifact-only producers to an unchanged compiled application source."""
import hashlib
from pathlib import Path
import re
import subprocess


PACKAGING_FILES = frozenset((
    'tools/windows-player/release_source.py',
    'tools/windows-player/package-release.py',
    'tools/windows-player/package-source-release.py',
    'tools/windows-player/package-windows-installer.py',
    'tools/windows-player/fork-installer.nsi',
    'tools/windows-player/verify-installer-guest.ps1',
    'tools/desktop-player/test-native-packaging.py',
    # Builds a separate diagnostic payload, restoring normal objects afterward.
    # Its producer bytes are carried separately from the unchanged application.
    'tools/desktop-player/prepare-native-review.py',
    'tools/desktop-player/check-channel-mixer.c',
    'tools/desktop-player/check-channel-mixer.mk',
    '.github/workflows/desktop-packages.yml',
    'tools/desktop-player/package-native.py',
    'tools/desktop-player/collect-native-sources.py',
    'doc/redesign/PLAN.md',
    'doc/redesign/SPECIFICATION.md',
    'doc/redesign/REPRODUCTION.md',
))


def validate_producer_delta(paths):
    forbidden = [name for name in paths if name not in PACKAGING_FILES]
    if forbidden:
        raise RuntimeError('Packaging producer changes application/build inputs: ' + repr(forbidden))


def packaging_identity(repo, application):
    repo = Path(repo)
    assert re.fullmatch('[0-9a-f]{40}', application)
    def git(*args):
        return subprocess.check_output(['git', '-C', str(repo), *args])
    producer = git('rev-parse', 'HEAD').decode().strip()
    subprocess.run(['git', '-C', str(repo), 'merge-base', '--is-ancestor', application, producer], check=True)
    changes = git('diff', '--name-only', application, producer).decode().splitlines()
    validate_producer_delta(changes)
    files = []
    for name in changes:
        blob = git('show', producer + ':' + name)
        path = repo / name
        assert path.is_file() and not path.is_symlink(), name
        assert path.read_bytes() == blob, 'Packaging producer has uncommitted inputs: ' + name
        files.append({'path': name, 'bytes': len(blob), 'sha256': hashlib.sha256(blob).hexdigest()})
    return {'source_commit': application, 'packager_commit': producer, 'files': files}
