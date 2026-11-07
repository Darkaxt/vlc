#!/usr/bin/env python3
"""Build the native Qt redesign and unpatched libmpv on a hosted native runner.

Builds have one compiler job. Retained inputs are content-bound; a failed build
keeps its outputs for diagnosis/resumption and never triggers a blind clean build.
Packaging and release qualification are separate steps, not inferred from make.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import tarfile
import urllib.request

ROOT = Path(__file__).resolve().parents[2]


def run(*args, cwd=None, env=None):
    print('+', ' '.join(map(str, args)), flush=True)
    subprocess.run(list(map(str, args)), cwd=cwd, env=env, check=True)


def output(*args, cwd=None):
    return subprocess.check_output(list(map(str, args)), cwd=cwd, text=True).strip()


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def source(work, name, url, expected=None):
    archive = work / 'sources' / (name + '.tar.gz')
    archive.parent.mkdir(parents=True, exist_ok=True)
    if not archive.exists():
        temporary = archive.with_suffix('.download')
        urllib.request.urlretrieve(url, temporary)
        temporary.replace(archive)
    digest = sha(archive)
    if expected and digest != expected:
        raise RuntimeError(f'Source digest mismatch: {name}')
    target = work / 'deps-src' / name
    if not target.exists():
        target.mkdir(parents=True)
        with tarfile.open(archive) as bundle:
            # GitHub/VideoLAN archives have one enclosing source directory.
            members = bundle.getmembers()
            top = members[0].name.split('/')[0]
            for member in members:
                if not member.name.startswith(top + '/'):
                    continue
                member.name = member.name[len(top) + 1:]
                if member.name:
                    bundle.extract(member, target, filter='data')
    return target, {'name': name, 'url': url, 'sha256': digest, 'archive': archive.name}


def meson(work, name, src, prefix, options, env):
    build = work / ('build-' + name)
    signature = json.dumps({'source': str(src), 'prefix': str(prefix), 'options': options,
                            'compiler': env.get('CC', ''), 'pkgconfig': env.get('PKG_CONFIG_PATH', '')}, sort_keys=True)
    binding = build / 'modern-vlc-configuration.json'
    if (build / 'build.ninja').exists():
        if not binding.exists() or binding.read_text() != signature:
            raise RuntimeError(f'{name}: configuration differs from retained build; use a distinct build directory')
    else:
        run('meson', 'setup', build, src, '--prefix=' + str(prefix), '--libdir=lib',
            '--buildtype=release', '-Db_ndebug=true', *options, env=env)
        binding.write_text(signature)
    run('ninja', '-C', build, '-j1', env=env)
    run('ninja', '-C', build, '-j1', 'install', env=env)


def bind_source_mtimes(work):
    manifest = work / 'source-times.json'
    previous = json.loads(manifest.read_text()) if manifest.exists() else {}
    current = {}
    paths = output('git', 'ls-files', '-z', cwd=ROOT).split('\0')
    for relative in paths:
        path = ROOT / relative
        if not relative or not path.is_file():
            continue
        digest = sha(path)
        old = previous.get(relative)
        if old and old['sha256'] == digest:
            os.utime(path, ns=(path.stat().st_atime_ns, old['mtime_ns']))
        current[relative] = {'sha256': digest, 'mtime_ns': path.stat().st_mtime_ns}
    manifest.write_text(json.dumps(current, sort_keys=True))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work', required=True, type=Path)
    args = parser.parse_args()
    work = args.work.resolve()
    work.mkdir(parents=True, exist_ok=True)
    native_mac = platform.system() == 'Darwin'
    arch = platform.machine()
    if arch not in ('arm64', 'aarch64', 'x86_64'):
        raise RuntimeError('Unqualified native architecture: ' + arch)
    bind_source_mtimes(work)
    env = os.environ.copy()
    env.update(CFLAGS='-O3 -g0 -DNDEBUG', CXXFLAGS='-O3 -g0 -DNDEBUG',
               MAKEFLAGS='-j1', CMAKE_BUILD_PARALLEL_LEVEL='1', PYTHONDONTWRITEBYTECODE='1')
    prefix = work / 'deps'
    sources = []
    if native_mac:
        brew = output('brew', '--prefix')
        qt = output('brew', '--prefix', 'qt')
        env['PATH'] = ':'.join([qt + '/bin', brew + '/opt/gettext/bin', brew + '/opt/bison/bin', env['PATH']])
        env['PKG_CONFIG_PATH'] = ':'.join([str(prefix / 'lib/pkgconfig'), qt + '/lib/pkgconfig',
            brew + '/opt/ffmpeg/lib/pkgconfig', brew + '/opt/libarchive/lib/pkgconfig',
            brew + '/lib/pkgconfig'])
        env['MACOSX_DEPLOYMENT_TARGET'] = '13.0'
    else:
        env['PATH'] = '/usr/lib/qt6/bin:' + env['PATH']
        env['PKG_CONFIG_PATH'] = str(prefix / 'lib/pkgconfig')
        # Stock MPV 0.42 requires libplacebo >= 7.387; Ubuntu 24.04 ships 6.
        placebo_pin = json.loads((ROOT / 'modules/gui/qt/player/mpv/source.json').read_text())
        placebo_pin = next(p for p in placebo_pin['sources'] if p['repository'] == 'haasn/libplacebo')
        placebo, record = source(work, 'libplacebo-' + placebo_pin['commit'],
            'https://codeload.github.com/haasn/libplacebo/tar.gz/' + placebo_pin['commit'], placebo_pin['sha256'])
        sources.append(record)
        meson(work, 'placebo', placebo, prefix, ['-Ddemos=false', '-Dtests=false',
            '-Dopengl=enabled', '-Dvulkan=disabled', '-Dshaderc=disabled', '-Dglslang=disabled'], env)

    pin = json.loads((ROOT / 'modules/gui/qt/player/mpv/source-portable.json').read_text())
    mpv, record = source(work, 'mpv-' + pin['commit'],
        'https://codeload.github.com/mpv-player/mpv/tar.gz/' + pin['commit'])
    sources.append(record)
    meson(work, 'mpv', mpv, prefix, ['-Dlibmpv=true', '-Dcplayer=false', '-Dbuild-date=false',
        '-Dplain-gl=enabled', '-Dmanpage-build=disabled', '-Dhtml-build=disabled', '-Dtests=false'], env)

    # VLC's required medialibrary ABI is newer than Ubuntu's packaged ABI.
    medialibrary_url = ('https://code.videolan.org/videolan/medialibrary/-/archive/0.14.1/'
                        'medialibrary-0.14.1.tar.bz2')
    medialibrary, record = source(work, 'medialibrary-0.14.1', medialibrary_url)
    sources.append(record)
    meson(work, 'medialibrary', medialibrary, prefix, ['-Dlibvlc=disabled', '-Dlibtool_workaround=true'], env)

    build = work / 'vlc-build'
    build.mkdir(exist_ok=True)
    install = work / 'installed'
    # The runtime dependency closure is staged before compiling its immutable
    # identities into the Qt plugin; packaging must preserve these exact bytes.
    run('python3', ROOT / 'tools/desktop-player/package-native.py', 'stage-mpv',
        '--work', work, '--prefix', prefix)
    flags = ['--prefix=' + str(install), '--enable-qt', '--disable-debug',
             '--disable-skins2', '--disable-nls', '--enable-libass', '--disable-merge-ffmpeg']
    if native_mac:
        # Reuse upstream's full native codec graph. Qt comes from the native
        # toolchain; the stock MPV graph above remains separate from these VLC
        # contribs (whose libplacebo ABI is older).
        triplet = ('aarch64' if arch == 'arm64' else arch) + '-apple-darwin19'
        contrib_sha = output('bash', ROOT / 'extras/ci/get-contrib-sha.sh', 'macos-' + arch, cwd=ROOT)
        archive = work / 'sources' / ('vlc-contrib-' + triplet + '-' + contrib_sha + '.tar.zst')
        url = 'https://artifacts.videolan.org/vlc/macos-' + ('arm64' if arch == 'arm64' else 'x86_64') + '/' + archive.name
        contrib_root = work / 'native-contrib'
        contrib = contrib_root / triplet
        if not archive.exists():
            urllib.request.urlretrieve(url, archive)
        if not contrib.exists():
            contrib_root.mkdir(exist_ok=True)
            run('tar', '-xf', archive, '-C', contrib_root)
            run('sh', ROOT / 'contrib/src/change_prefix.sh', cwd=contrib, env=env)
        sources.append({'name': 'vlc-native-contrib', 'upstream_input_commit': contrib_sha,
                        'url': url, 'archive': archive.name, 'sha256': sha(archive)})
        env['PKG_CONFIG_PATH'] = str(contrib / 'lib/pkgconfig') + ':' + env['PKG_CONFIG_PATH']
        flags += ['--with-contrib=' + str(contrib)]
        flags += ['--disable-macosx', '--disable-xcb', '--without-x', '--with-macosx-version-min=13.0']
    else:
        flags += ['--enable-xcb', '--disable-wayland']
    # Preserve configure and generated objects when relevant inputs are equal.
    config = json.dumps({'flags': flags, 'environment': {k: env.get(k) for k in
        ('CFLAGS', 'CXXFLAGS', 'PKG_CONFIG_PATH', 'MACOSX_DEPLOYMENT_TARGET')},
        'configure_inputs': {str(p.relative_to(ROOT)): sha(p) for p in
            [ROOT / 'configure.ac', ROOT / 'modules/gui/qt/qt6.pro']}}, sort_keys=True)
    binding = build / 'native-config.json'
    if (build / 'config.status').exists():
        if not binding.exists() or binding.read_text() != config:
            raise RuntimeError('Retained VLC configuration changed; select a new content-keyed work directory')
    else:
        run('sh', ROOT / 'bootstrap', cwd=ROOT, env=env)
        run(ROOT / 'configure', *flags, cwd=build, env=env)
        binding.write_text(config)
    run('make', '-j1', 'PLAYER_MPV_CPPFLAGS=-DVLC_MPV_RUNTIME_IDENTITY', cwd=build, env=env)
    run('make', '-j1', 'install', 'PLAYER_MPV_CPPFLAGS=-DVLC_MPV_RUNTIME_IDENTITY', cwd=build, env=env)
    (work / 'native-build.json').write_text(json.dumps({
        'schema': 'modern-vlc.native-build.v1', 'source_commit': output('git', 'rev-parse', 'HEAD', cwd=ROOT),
        'platform': platform.platform(), 'architecture': arch, 'mpv': pin,
        'sources': sources, 'configuration': json.loads(config),
        'qualification': 'NOT RUN; build/packaging is not playback acceptance'}, indent=2) + '\n')
    run('python3', ROOT / 'tools/desktop-player/package-native.py', 'packages', '--work', work, '--prefix', prefix)


if __name__ == '__main__':
    main()
