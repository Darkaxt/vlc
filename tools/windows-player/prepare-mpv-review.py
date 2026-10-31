"""Copy the verified 1.0 runtime and pinned MPV DLL into fresh S8 build scratch.

This is an isolated compiler/test destination, not an installation or release.
It preserves all source profiles and checks the exact existing release identity.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime', required=True, type=Path)
    parser.add_argument('--library', required=True, type=Path)
    parser.add_argument('--scratch', required=True, type=Path)
    args = parser.parse_args()
    source, library, root = (path.resolve(strict=True) for path in (args.runtime, args.library, args.scratch))
    assert root == Path('D:/Temp/vlc-s8-20261029')
    identity = json.loads((source / 'BUILDINFO.json').read_text())
    assert identity['version'] == '1.0.0'
    assert identity['source_commit'] == 'dd61caec26f8cc65f15d78369d09fb254196c810'
    assert digest(source / 'plugins/gui/libqt_plugin.dll') == identity['qt_plugin_sha256']
    assert not any((source / 'portable').iterdir()), 'Preserve the existing source profile'
    repo = Path(__file__).resolve().parents[2]
    pin = json.loads((repo / 'modules/gui/qt/player/mpv/source.json').read_text())['reference_runtime']
    assert digest(library) == pin['sha256']
    target = root / 'scratch-share/runtime'
    assert not target.exists(), 'Inspect existing consumers instead of overwriting a review runtime'
    shutil.copytree(source, target)
    shutil.copyfile(library, target / 'libmpv-2.dll')
    receipt = {'schema': 'vlc_redesign.s8_review_input.v1', 'source': str(source),
               'destination': str(target), 'source_identity': identity,
               'mpv_library': str(library), 'mpv_sha256': digest(target / 'libmpv-2.dll'),
               'scope': 'Isolated input for subsequent instrumented compilation; not a delivered S8 build'}
    (root / 'evidence/review-runtime-input.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'destination': str(target), 'mpv_sha256': receipt['mpv_sha256']}))


if __name__ == '__main__':
    main()
