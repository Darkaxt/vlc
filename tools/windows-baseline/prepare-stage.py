"""Fetch immutable Windows toolchain inputs into an exact registered D: stage root.

This prepares files only. It never imports/starts WSL, compiles, installs or
publishes. Linux operations must use the installed Coordinator build gate.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tarfile
import urllib.request

IMAGE = 'registry.videolan.org/vlc-debian-win64-posix@sha256:8e83e800036f8f4a6da1031a6b80c2b5bad8337259c072ffa22398baaeaad880'
INPUTS = [
    ('debian-base.tar.gz',
     'https://registry.videolan.org/v2/vlc-debian-win64-posix/blobs/sha256:c95640bb37f6885da02c8c3b6d8e2daca996dfaa99ba6ad46f1b60155fdaf504',
     'sha256', 'c95640bb37f6885da02c8c3b6d8e2daca996dfaa99ba6ad46f1b60155fdaf504'),
    ('go-containerregistry_Windows_x86_64.tar.gz',
     'https://github.com/google/go-containerregistry/releases/download/v0.22.1/go-containerregistry_Windows_x86_64.tar.gz',
     'sha256', '0e073ea8192c3b8442ec8aaf44d53c1050a09084669fae3a6ceb0f2026cf8b21'),
    ('vlc-contrib-x86_64-w64-mingw32-a5538c557d276378d5ba0f8f8010a8b87eaa6f78.tar.zst',
     'https://artifacts.videolan.org/vlc/win64/vlc-contrib-x86_64-w64-mingw32-a5538c557d276378d5ba0f8f8010a8b87eaa6f78.tar.zst',
     'sha512', '7504d2d80be566f1caced13c8acf45af67059dc159d987a5d4e82c8912ed6fc4435fba714670e53c786bd83accf6c441f1ad345d3c97c04b5bf0ab60341f8d0d'),
    ('mingw-runtime-source.tar.gz',
     'https://codeload.github.com/mingw-w64/mingw-w64/tar.gz/refs/tags/v12.0.0',
     'sha256', 'fa41d462041ed72e29a5101049e5991d4aea5c552fd75f7ac0074989fc54ceb7'),
    ('qtbase-everywhere-src-6.8.3.tar.xz',
     'https://download.qt.io/archive/qt/6.8/6.8.3/submodules/qtbase-everywhere-src-6.8.3.tar.xz',
     'sha512', 'ef364f939f23b622f67d21833c2dbf1fb74531d9a1e25b6d2e94ea5d747a40f20c6c3a24abef1e9710287366b7cb54dd090350d315601317779235c20743cc81'),
    ('pupnp-release-1.14.31.tar.gz',
     'https://codeload.github.com/pupnp/pupnp/tar.gz/refs/tags/release-1.14.31',
     'sha512', 'be0f876adb7a0799187531cc83a29afd5bfe8f7772e909f88faf406e344f992ccb07ef410f7511766576bde8128478926e33cebfcfa8ed1ba15fe136e0bfc8c7'),
]


def digest(path, algorithm='sha256'):
    with path.open('rb') as source:
        return hashlib.file_digest(source, algorithm).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scratch', required=True, type=Path)
    options = parser.parse_args()
    root = options.scratch.resolve()
    if root.drive.upper() != 'D:' or root.parent != Path('D:/Temp'):
        parser.error('Use an exact registered D:/Temp/<stage> root for sustained active I/O')
    if (root / 'wsl').exists():
        parser.error('This root already owns a build VM. Inspect its recorded inputs and active consumers; do not recreate retired export/import downloads.')
    downloads, temporary, tools = root / 'downloads', root / 'tmp', root / 'native-tools'
    for path in (downloads, temporary, tools):
        path.mkdir(parents=True, exist_ok=True)
    evidence = []
    for name, url, algorithm, expected in INPUTS:
        path = downloads / name
        if not path.exists():
            partial = path.with_name(name + '.partial')
            if partial.exists():
                raise RuntimeError('Inspect interrupted download before reuse: ' + str(partial))
            print('Downloading ' + name, flush=True)
            with urllib.request.urlopen(url) as source, partial.open('xb') as target:
                while chunk := source.read(1024 * 1024):
                    target.write(chunk)
            assert digest(partial, algorithm) == expected, 'Downloaded hash mismatch: ' + name
            partial.rename(path)
        assert digest(path, algorithm) == expected, 'Existing input hash mismatch: ' + name
        evidence.append({'path': str(path), 'url': url, algorithm: expected, 'bytes': path.stat().st_size})
        print('Verified ' + name, flush=True)
    crane = tools / 'crane.exe'
    if not crane.exists():
        with tarfile.open(downloads / 'go-containerregistry_Windows_x86_64.tar.gz') as archive:
            member = next(item for item in archive.getmembers() if Path(item.name).name == 'crane.exe' and item.isfile())
            with archive.extractfile(member) as source, crane.open('xb') as target:
                while chunk := source.read(1024 * 1024):
                    target.write(chunk)
    image = downloads / 'toolchain-rootfs.tar'
    if not image.exists():
        partial = image.with_suffix('.tar.partial')
        if partial.exists():
            raise RuntimeError('Inspect interrupted image export before reuse: ' + str(partial))
        print('Exporting the immutable pinned image', flush=True)
        subprocess.run([str(crane), 'export', IMAGE, str(partial)],
            env=dict(os.environ, TEMP=str(temporary), TMP=str(temporary)), check=True,
            creationflags=subprocess.CREATE_NO_WINDOW)
        partial.rename(image)
    # Bind the exact complete local image export used by the later import.
    with tarfile.open(image) as archive:
        names = {item.name.removeprefix('./') for item in archive}
    assert 'usr/bin/python3' in names and ('bin/sh' in names or 'usr/bin/sh' in names)
    evidence.append({'path': str(image), 'image': IMAGE, 'sha256': digest(image), 'bytes': image.stat().st_size,
        'python3_and_shell_present': True})
    (root / 'inputs.json').write_text(json.dumps(evidence, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'inputs_verified': True, 'image': str(image), 'bytes': image.stat().st_size}), flush=True)


if __name__ == '__main__':
    main()
