"""Build VLC's newly required medialibrary in a separate, source-bound prefix."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tarfile


def main():
    assert Path('/proc/self/cgroup').read_text().split('::', 1)[1].strip().startswith('/llm-coordinator/')
    source = Path(__file__).resolve().parents[2]
    rules = (source / 'contrib/src/medialibrary/rules.mak').read_text()
    version = re.search(r'^MEDIALIBRARY_VERSION := ([0-9.]+)$', rules, re.M).group(1)
    name = 'medialibrary-' + version + '.tar.bz2'
    expected = dict((line.split()[1], line.split()[0]) for line in
        (source / 'contrib/src/medialibrary/SHA512SUMS').read_text().splitlines() if line.strip())[name]
    archive = Path('/scratch/mpv-source-inputs') / name
    with archive.open('rb') as stream:
        assert hashlib.file_digest(stream, 'sha512').hexdigest() == expected
    base = Path('/work/upstream-medialibrary-' + version)
    src, build, prefix = base / 'source', base / 'build', base / 'prefix'
    if not src.exists():
        src.mkdir(parents=True)
        with tarfile.open(archive) as tar:
            for item in tar:
                parts = Path(item.name).parts
                assert parts[0] == 'medialibrary-' + version and '..' not in parts
                assert item.isfile() or item.isdir(), 'Unexpected source link'
                if len(parts) == 1:
                    continue
                target = src.joinpath(*parts[1:])
                if item.isdir():
                    target.mkdir(parents=True, exist_ok=True)
                else:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(tar.extractfile(item).read())
        (base / 'extracted.json').write_text(json.dumps({'archive': name, 'sha512': expected}))
    assert json.loads((base / 'extracted.json').read_text()) == {'archive': name, 'sha512': expected}
    # Reuse the established Windows CRT/SDK, without MPV's separate FFmpeg prefix.
    cross = Path('/work/mpv-runtime/cross.meson').read_text()
    cross = cross.replace("'-B/work/mpv-runtime/prefix/lib/', ", '')
    cross = cross.replace("'-I/work/mpv-runtime/prefix/include', ", '')
    cross = cross.replace("'-L/work/mpv-runtime/prefix/lib', ", '')
    cross_path = base / 'cross.meson'
    if cross_path.exists():
        assert cross_path.read_text() == cross
    else:
        cross_path.write_text(cross)
    sdk = '/work/build/contrib/x86_64-w64-mingw32'
    env = dict(os.environ, PKG_CONFIG_LIBDIR=sdk + '/lib/pkgconfig',
        PKG_CONFIG_PATH=sdk + '/lib/pkgconfig', PKG_CONFIG_SYSROOT_DIR='/',
        CMAKE_BUILD_PARALLEL_LEVEL='1', CARGO_BUILD_JOBS='1')
    if not (build / 'build.ninja').exists():
        subprocess.run(['meson', 'setup', str(build), str(src), '--cross-file', str(cross_path),
            '--prefix', str(prefix), '--libdir', 'lib', '--default-library', 'static',
            '--buildtype', 'debugoptimized', '--wrap-mode', 'nodownload',
            '-Dlibvlc=disabled', '-Dtests=disabled', '-Dlibtool_workaround=true'], env=env, check=True)
    subprocess.run(['ninja', '-C', str(build), '-j1'], env=env, check=True)
    subprocess.run(['meson', 'install', '-C', str(build), '--no-rebuild'], env=env, check=True)
    pc = prefix / 'lib/pkgconfig/medialibrary.pc'
    assert 'Version: ' + version in pc.read_text() and (prefix / 'lib/libmedialibrary.a').is_file()
    receipt = {'schema': 'vlc_redesign.upstream_medialibrary_build.v1', 'version': version,
        'archive': name, 'sha512': expected, 'prefix': str(prefix),
        'library_sha256': hashlib.sha256((prefix / 'lib/libmedialibrary.a').read_bytes()).hexdigest(),
        'cross_sha256': hashlib.sha256(cross.encode()).hexdigest()}
    (base / 'build-receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt), flush=True)


if __name__ == '__main__':
    main()
