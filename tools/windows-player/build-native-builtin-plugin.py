"""Build only the Windows registration adapter for upstream regression mocks."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--receipt', required=True, type=Path)
    args = parser.parse_args()
    assert not args.output.exists() and not args.receipt.exists()
    command = ['x86_64-w64-mingw32-gcc', '-DHAVE_CONFIG_H', '-DVLC_DYNAMIC_PLUGIN',
        '-I/work/build/win64', '-I/work/src/include', '-shared', '-O2', '-static-libgcc',
        str(args.source), '-o', str(args.output)]
    subprocess.run(command, check=True)
    result = {'schema': 'vlc_redesign.native_builtin_adapter.v1',
        'source_commit': subprocess.check_output(['git', '-C', '/work/src', 'rev-parse', 'HEAD'], text=True).strip(),
        'source_sha256': sha(args.source), 'builder_sha256': sha(Path(__file__)),
        'plugin_header_sha256': sha(Path('/work/src/include/vlc_plugin.h')),
        'file': str(args.output), 'sha256': sha(args.output), 'command': command,
        'scope': 'Test-only Windows discovery of the unchanged upstream EXE builtin entry and mock state'}
    args.receipt.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result), flush=True)


if __name__ == '__main__':
    main()
