"""Install this build's FFmpeg files without retimestamping identical bytes.

The Windows-mounted prefix reports mode 777 regardless of install's requested
644, so GNU install -C's metadata comparison always replaces identical files.
This narrowly supports the static build's existing '-m 644 FILE... DIRECTORY'
and single-source '-m 644 FILE TARGET' calls. Changed files still go through GNU
install; source timestamps are never
copied onto changed outputs. No installation outside this task prefix is allowed.
"""
import json
import os
from pathlib import Path
import subprocess
import sys


def equal_bytes(left, right):
    if left.stat().st_size != right.stat().st_size:
        return False
    with left.open('rb') as source, right.open('rb') as target:
        while block := source.read(1024 * 1024):
            if block != target.read(len(block)):
                return False
        return not target.read(1)


def main():
    assert os.geteuid() == 0 and Path('/.vlc-s8-toolchain.json').is_file()
    assert Path('/proc/self/cgroup').read_text().split('::', 1)[1].strip().startswith('/llm-coordinator/')
    arguments = sys.argv[1:]
    assert len(arguments) >= 4 and arguments[:2] == ['-m', '644'], arguments
    prefix = Path('/work/mpv-runtime/prefix').resolve(strict=True)
    roots = [Path('/work/mpv-runtime/source/FFmpeg').resolve(strict=True),
             Path('/work/mpv-runtime/ffmpeg-build').resolve(strict=True)]
    destination = Path(arguments[-1])
    assert not destination.is_symlink(), destination
    destination = destination.resolve()
    assert destination.is_relative_to(prefix) and destination != prefix
    directory = destination.is_dir()
    assert directory or (len(arguments) == 4 and destination.parent.is_dir()), destination
    files = []
    for name in arguments[2:-1]:
        source = Path(name).resolve(strict=True)
        assert source.is_file() and any(source.is_relative_to(root) for root in roots), source
        target = destination / source.name if directory else destination
        assert not target.is_symlink() and (not target.exists() or target.is_file()), target
        files.append((source, target))
    installed = preserved = 0
    for source, target in files:
        before = target.stat() if target.exists() else None
        if before and equal_bytes(source, target):
            after = target.stat()
            assert (before.st_ino, before.st_mtime_ns, before.st_size) == (after.st_ino, after.st_mtime_ns, after.st_size)
            preserved += 1
            continue
        subprocess.run(['/usr/bin/install', '-m', '644', '--', str(source), str(target)], check=True)
        assert equal_bytes(source, target), target
        installed += 1
    print(json.dumps({'ffmpeg_installed': installed, 'unchanged_bytes_and_mtimes_preserved': preserved,
                      'destination': str(destination)}))


if __name__ == '__main__':
    main()
