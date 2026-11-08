"""Build selected upstream codec updates without modifying the retained SDK."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import tarfile


def sha(path, algorithm='sha256'):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, algorithm).hexdigest()


def main():
    assert Path('/proc/self/cgroup').read_text().split('::', 1)[1].strip().startswith('/llm-coordinator/')
    repo = Path(__file__).resolve().parents[2]
    policy_spec = importlib.util.spec_from_file_location(
        'native_release_policy', repo / 'tools/desktop-player/build-native.py')
    policy = importlib.util.module_from_spec(policy_spec)
    policy_spec.loader.exec_module(policy)
    base = Path('/work/upstream-codecs-1.1.1')
    prefix = base / 'prefix'
    sdk = Path('/work/build/contrib/x86_64-w64-mingw32')
    crt = Path('/work/runtime-crt-only')
    base.mkdir(exist_ok=True)
    cross = (Path('/work/mpv-runtime/cross.cmake').read_text()
        .replace('/work/mpv-runtime/prefix', str(prefix)))
    cross += '\nset(CMAKE_STATIC_LINKER_FLAGS_INIT "")\n'
    cross_path = base / 'cross.cmake'
    if cross_path.exists():
        assert cross_path.read_text() == cross
    else:
        cross_path.write_text(cross)
    env = dict(os.environ, CMAKE_BUILD_PARALLEL_LEVEL='1',
        PKG_CONFIG_LIBDIR=str(sdk / 'lib/pkgconfig'),
        PKG_CONFIG_PATH=str(sdk / 'lib/pkgconfig'), PKG_CONFIG_SYSROOT_DIR='/')
    image_work = base / 'image-dependencies'
    subprocess.run(['python3', '-B', str(repo / 'tools/desktop-player/image_dependencies.py'),
        '--repo', str(repo), '--work', str(image_work), '--prefix', str(prefix),
        '--archives', '/scratch/mpv-source-inputs', '--toolchain', str(cross_path)],
        env=env, check=True)
    images = json.loads((image_work / 'build-receipt.json').read_text())
    patches = {
        'aom': ['0001-Do-not-force-_WIN32_WINNT.patch'],
        'mad': ['0001-CMake-case-of-AND-test.patch'],
        'mpg123': ['0001-ports-cmake-Fix-detecting-asm-align-directives-in-cm.patch',
            '0002-ports-cmake-Fix-building-ARM-assembly-for-Windows-fo.patch',
            '0003-libmpg123-select-the-NEON64-dct36-on-aarch64.patch',
            'cmake_arm64_more_than_just_apple.patch'],
        'zvbi': ['zvbi-ssize_max.patch', 'zvbi-fix-static-linking.patch', 'zvbi-win32.patch',
            'zvbi-fix-clang-support.patch', '0001-configure-hardcode-liconv-instead-of-the-full-path.patch',
            '0009-fix-Android-usage-of-pthread.patch',
            '0001-fix-Windows-API-calls-when-UNICODE-is-defined.patch'],
    }
    names = {'aom': ('libaom-{v}.tar.gz', 'libaom.a', 'aom'),
        'mad': ('libmad-{v}.tar.gz', 'libmad.a', 'mad'),
        'mpg123': ('mpg123-{v}.tar.bz2', 'libmpg123.a', 'libmpg123'),
        'zvbi': ('zvbi-{v}.tar.gz', 'libzvbi.a', 'zvbi-0.2')}
    records = []
    for component in ('mpg123', 'zvbi', 'mad', 'aom'):
        rules_dir = repo / 'contrib/src' / component
        version = re.search(r'^' + component.upper() + r'_VERSION := ([0-9.]+)$',
            (rules_dir / 'rules.mak').read_text(), re.M).group(1)
        template, library, pc = names[component]
        archive = Path('/scratch/mpv-source-inputs') / template.format(v=version)
        expected = {line.split()[1]: line.split()[0] for line in
            (rules_dir / 'SHA512SUMS').read_text().splitlines() if line.strip()}[archive.name]
        assert sha(archive, 'sha512') == expected
        home = base / (component + '-' + version)
        source, build = home / 'source', home / 'build'
        identity = {'archive': archive.name, 'sha512': expected,
            'patches': {name: sha(rules_dir / name) for name in patches[component]}}
        marker = home / 'prepared.json'
        print('UPSTREAM CODEC START ' + component + ' ' + version, flush=True)
        if not marker.exists():
            assert not home.exists(), 'Inspect interrupted source preparation before changing it'
            source.mkdir(parents=True)
            with tarfile.open(archive) as tar:
                for item in tar:
                    parts = Path(item.name).parts
                    assert not Path(item.name).is_absolute() and '..' not in parts
                    assert item.isdir() or item.isfile(), 'Unexpected archive link: ' + item.name
                    if len(parts) <= 1:
                        continue
                    target = source.joinpath(*parts[1:])
                    if item.isdir():
                        target.mkdir(parents=True, exist_ok=True)
                    else:
                        target.parent.mkdir(parents=True, exist_ok=True)
                        target.write_bytes(tar.extractfile(item).read())
            for name in patches[component]:
                patch = rules_dir / name
                subprocess.run(['git', 'apply', '--check', str(patch)], cwd=source, check=True)
                subprocess.run(['git', 'apply', str(patch)], cwd=source, check=True)
            if component == 'zvbi':
                configure = source / 'configure.ac'
                text = configure.read_text().replace('AM_GNU_GETTEXT_VERSION([0.21])',
                    'AM_GNU_GETTEXT_VERSION([0.19])')
                text = text.replace('AC_FUNC_MALLOC', 'dnl AC_FUNC_MALLOC').replace('AC_FUNC_REALLOC', 'dnl AC_FUNC_REALLOC')
                configure.write_text(text)
                (source / 'README').touch()
            marker.write_text(json.dumps(identity, indent=2) + '\n')
        assert json.loads(marker.read_text()) == identity
        build.mkdir(exist_ok=True)
        if component == 'zvbi':
            if not (source / 'configure').exists():
                subprocess.run(['autoreconf', '-fiv', '-I', 'm4'], cwd=source, env=env, check=True)
            zvbi_env = dict(env, CC='x86_64-w64-mingw32-gcc -B' + str(crt) + '/',
                CXX='x86_64-w64-mingw32-g++ -B' + str(crt) + '/',
                AR='x86_64-w64-mingw32-gcc-ar', RANLIB='x86_64-w64-mingw32-gcc-ranlib',
                CFLAGS='-O3 -g0 -DNDEBUG -I' + str(sdk / 'include'),
                CPPFLAGS='-I' + str(sdk / 'include'),
                LDFLAGS='-L' + str(crt) + ' -L' + str(sdk / 'lib') + ' -static-libgcc')
            if not (build / 'Makefile').exists():
                subprocess.run([str(source / 'configure'), '--host=x86_64-w64-mingw32',
                    '--build=x86_64-linux-gnu', '--prefix=' + str(prefix), '--disable-shared', '--enable-static',
                    '--disable-dvb', '--disable-bktr', '--disable-nls', '--disable-proxy', '--without-doxygen'],
                    cwd=build, env=zvbi_env, check=True)
            for target in ([], ['install']):
                subprocess.run(['make', '-j1', 'bin_PROGRAMS=', 'noinst_PROGRAMS=', *target],
                    cwd=build, env=zvbi_env, check=True)
        else:
            options = {'aom': ['-DCONFIG_RUNTIME_CPU_DETECT=1', '-DCONFIG_MULTITHREAD=1',
                '-DENABLE_DOCS=OFF', '-DENABLE_APPS=OFF', '-DENABLE_EXAMPLES=OFF',
                '-DENABLE_TOOLS=OFF', '-DENABLE_TESTS=OFF', '-DCONFIG_LIBYUV:STRING=0', '-DCONFIG_AV1_ENCODER=1'],
                'mad': ['-DEXAMPLE=OFF'],
                'mpg123': ['-DBUILD_LIBOUT123=OFF', '-DBUILD_PROGRAMS=OFF']}[component]
            if not (build / 'CMakeCache.txt').exists():
                subprocess.run(['cmake', '-S', str(source / 'ports/cmake' if component == 'mpg123' else source),
                    '-B', str(build), '-G', 'Ninja', '-DCMAKE_TOOLCHAIN_FILE=' + str(cross_path),
                    '-DCMAKE_INSTALL_PREFIX=' + str(prefix), '-DCMAKE_INSTALL_LIBDIR=lib',
                    '-DCMAKE_BUILD_TYPE=Release', '-DCMAKE_C_FLAGS_RELEASE=-O3 -g0 -DNDEBUG',
                    '-DCMAKE_CXX_FLAGS_RELEASE=-O3 -g0 -DNDEBUG',
                    '-DBUILD_SHARED_LIBS=OFF', *options], env=env, check=True)
            if component == 'aom':
                policy.verify_aom_release_flags((build / 'CMakeCache.txt').read_text())
            subprocess.run(['cmake', '--build', str(build), '--parallel', '1'], env=env, check=True)
            subprocess.run(['cmake', '--install', str(build)], env=env, check=True)
        pc_path = prefix / 'lib/pkgconfig' / (pc + '.pc')
        assert 'Version: ' + version in pc_path.read_text(), pc_path
        assert (prefix / 'lib' / library).is_file()
        record = dict(identity, library=component, version=version, prefix=str(prefix),
            archive_sha256=sha(archive), static_library=library,
            library_sha256=sha(prefix / 'lib' / library), pkg_config=pc)
        if component == 'aom':
            record['release_flags'] = policy.verify_aom_release_flags((build / 'CMakeCache.txt').read_text())
            record['cmake_cache_sha256'] = sha(build / 'CMakeCache.txt')
        (home / 'build-receipt.json').write_text(json.dumps(record, indent=2) + '\n')
        records.append(record)
        print('UPSTREAM CODEC DONE ' + json.dumps(record), flush=True)
    receipt = {'schema': 'vlc_redesign.upstream_codec_build.v1', 'libraries': records,
        'cross_sha256': sha(cross_path), 'sdk_unchanged': True, 'image_dependencies': images}
    (base / 'build-receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')


if __name__ == '__main__':
    main()
