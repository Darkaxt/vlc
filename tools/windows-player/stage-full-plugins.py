"""Stage only current configured plugin outputs; never inherit ABI-stale DLLs."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True, type=Path)
    parser.add_argument('--build', required=True, type=Path)
    parser.add_argument('--runtime', required=True, type=Path)
    args = parser.parse_args()
    assert Path('/proc/self/cgroup').read_text().split('::', 1)[1].strip().startswith('/llm-coordinator/')
    mapping = subprocess.check_output(['make', '--no-print-directory', '-s', '-C', str(args.build / 'modules'),
        '-f', 'Makefile', '-f', str(args.source / 'tools/windows-player/full-plugin-stage.mk'),
        'pluginsdir=/plugins', 'pkglibdir=/plugins', 'player-plugin-map'], text=True)
    rows = []
    for line in mapping.splitlines():
        name, installed = line.split('\t')
        destination = PurePosixPath(installed).with_suffix('.dll')
        assert destination.is_relative_to('/plugins') and '..' not in destination.parts
        library = args.build / 'modules' / name
        binary = library.parent / '.libs' / (library.stem + '.dll')
        rows.append((binary, destination.relative_to('/').as_posix()))
    rows.append((args.build / 'modules/gui/qt/.libs/libqt_plugin.dll', 'plugins/gui/libqt_plugin.dll'))
    expected = {name for _, name in rows}
    assert len(expected) == len(rows) and len(rows) > 300, 'Inspect configured capability loss'
    previous = {path.relative_to(args.runtime).as_posix() for path in (args.runtime / 'plugins').rglob('*.dll')}
    assert previous <= expected, 'Unexpected/stale staged plugins: ' + repr(previous - expected)
    records = []
    for binary, relative in sorted(rows, key=lambda row: row[1]):
        assert binary.is_file(), binary
        target = args.runtime / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(['x86_64-w64-mingw32-strip', '--strip-debug', '-o', str(target), str(binary)], check=True)
        records.append({'file': relative, 'build_source': str(binary),
            'unstripped_sha256': hashlib.sha256(binary.read_bytes()).hexdigest()})
    commit = subprocess.check_output(['git', '-C', str(args.source), 'rev-parse', 'HEAD'], text=True).strip()
    assert not subprocess.check_output(['git', '-C', str(args.source), 'status', '--porcelain'])
    receipt = {'schema': 'vlc_redesign.full_plugin_build.v1', 'source_commit': commit,
        'upstream_commit': json.loads((args.runtime / 'UPSTREAM-ASSEMBLY.json').read_text())['upstream_commit'],
        'configured_install_map_sha256': hashlib.sha256(mapping.encode()).hexdigest(), 'plugins': records}
    (args.runtime / 'VLC-PLUGIN-BUILDINFO.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({'coherent_source_commit': commit, 'configured_plugins': len(rows)}), flush=True)


if __name__ == '__main__':
    main()
