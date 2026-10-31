"""Private, bounded RAM cache for the pinned compiler's Windows-file metadata.

No distribution, disk, global cache or source is changed. Bind mounts preserve
the original toolchain paths and are released before the memory-heavy VLC link.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import resource
import shutil
import stat
import subprocess
import time

ROOT = Path('/work/compiler-cache')
RECEIPT = Path('/work/compiler-cache.json')
LIMIT = 512 * 1024 * 1024
QT_LIMIT = 256 * 1024 * 1024
BASE_TARGETS = ['/usr/lib/gcc/x86_64-w64-mingw32/14-posix',
                '/usr/share/mingw-w64/include']
# These inputs are immutable after FFmpeg installation. Do not cache the whole
# prefix/include directory: MPV installation must persist its new API headers.
MPV_TARGETS = ['/work/build/contrib/x86_64-w64-mingw32/include',
               '/work/mpv-runtime/source/mpv'] + [
    '/work/mpv-runtime/prefix/include/' + name for name in (
        'libavcodec', 'libavdevice', 'libavfilter', 'libavformat', 'libavutil',
        'libplacebo', 'libswresample', 'libswscale', 'shaderc', 'spirv_cross')]
QT_TARGETS = ['/usr/lib/gcc/x86_64-w64-mingw32/14-posix/include',
              '/usr/lib/gcc/x86_64-w64-mingw32/14-posix/include-fixed',
              '/usr/share/mingw-w64/include',
              '/work/build/contrib/x86_64-w64-mingw32/include',
              '/work/src/include', '/work/src/modules/gui/qt']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['create', 'release'])
    profile = parser.add_mutually_exclusive_group()
    profile.add_argument('--mpv-build', action='store_true',
        help='Cache immutable SDK/MPV inputs only after FFmpeg has been installed')
    profile.add_argument('--qt-build', action='store_true',
        help='Cache Qt/Windows/C++ headers and frozen VLC frontend sources; release before linking')
    args = parser.parse_args()
    group = Path('/proc/self/cgroup').read_text().split('::', 1)[1].strip()
    assert group.startswith('/llm-coordinator/') and os.geteuid() == 0
    assert Path('/.vlc-s8-toolchain.json').is_file()
    cap = Path('/sys/fs/cgroup' + group + '/memory.max').read_text().strip()
    assert cap != 'max' and int(cap) <= 3758096384
    if args.action == 'release':
        saved = json.loads(RECEIPT.read_text())
        assert saved['root'] == str(ROOT) and saved['targets'] in (
            BASE_TARGETS, BASE_TARGETS + MPV_TARGETS, QT_TARGETS)
        assert saved['limit_bytes'] == (QT_LIMIT if saved['targets'] == QT_TARGETS else LIMIT)
        for target in reversed(saved['targets']):
            subprocess.run(['/usr/bin/umount', target], check=True)
        subprocess.run(['/usr/bin/umount', str(ROOT)], check=True)
        saved['released_before_vlc'] = True
        RECEIPT.write_text(json.dumps(saved, indent=2) + '\n')
        print(json.dumps({'compiler_cache_released': True}), flush=True)
        return
    targets = QT_TARGETS if args.qt_build else BASE_TARGETS + (MPV_TARGETS if args.mpv_build else [])
    limit = QT_LIMIT if args.qt_build else LIMIT
    files = []
    for target in targets:
        assert Path(target).is_dir() and not Path(target).is_symlink(), target
        for directory, _, names in os.walk(target, followlinks=False):
            for name in names:
                path = Path(directory) / name
                if stat.S_ISREG(path.lstat().st_mode):
                    files.append(path)
    total = sum(path.stat().st_size for path in files)
    assert total < limit, 'Inspect working set instead of exceeding the RAM cache budget'
    ROOT.mkdir(exist_ok=True)
    assert not any(ROOT.iterdir()), 'Preserve existing cache data/consumers'
    subprocess.run(['/usr/bin/mount', '-t', 'tmpfs', '-o', 'size=' + str(limit),
                    'vlc-compiler-cache', str(ROOT)], check=True)
    for index, target in enumerate(targets):
        print(json.dumps({'cache_copy': target}), flush=True)
        shutil.copytree(target, ROOT / str(index), symlinks=True)
        print(json.dumps({'cache_copied': target}), flush=True)
    combined = hashlib.sha256()
    for count, source in enumerate(files, 1):
        index = next(i for i, target in enumerate(targets) if source.is_relative_to(target))
        copied = ROOT / str(index) / source.relative_to(targets[index])
        with source.open('rb') as original, copied.open('rb') as cached:
            digest = hashlib.file_digest(original, 'sha256').digest()
            assert hashlib.file_digest(cached, 'sha256').digest() == digest, str(source)
        combined.update(str(source).encode() + b'\0' + digest)
        if count % 500 == 0:
            print(json.dumps({'cache_verified_files': count, 'total': len(files)}), flush=True)
    for index, target in enumerate(targets):
        subprocess.run(['/usr/bin/mount', '--bind', str(ROOT / str(index)), target], check=True)
        subprocess.run(['/usr/bin/mount', '-o', 'remount,bind,ro', target], check=True)
    saved = {'schema': 'vlc_redesign.compiler_cache.v1', 'root': str(ROOT),
        'targets': targets, 'bytes': total, 'file_count': len(files),
        'content_sha256': combined.hexdigest(), 'limit_bytes': limit,
        'cgroup': group, 'released_before_vlc': False}
    RECEIPT.write_text(json.dumps(saved, indent=2) + '\n')
    before = resource.getrusage(resource.RUSAGE_CHILDREN)
    start = time.monotonic()
    result = subprocess.run(['/usr/bin/x86_64-w64-mingw32-gcc', '-E', '-x', 'c', '-'],
        input=b'#include <windows.h>\n', stdout=subprocess.DEVNULL, check=True)
    after = resource.getrusage(resource.RUSAGE_CHILDREN)
    saved['header_preprocess_wall_seconds'] = time.monotonic() - start
    saved['header_preprocess_cpu_seconds'] = after.ru_utime + after.ru_stime - before.ru_utime - before.ru_stime
    RECEIPT.write_text(json.dumps(saved, indent=2) + '\n')
    print(json.dumps(saved), flush=True)


if __name__ == '__main__':
    main()
