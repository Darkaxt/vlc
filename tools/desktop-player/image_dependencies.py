"""Build the two source-bound VLC image/compression updates without replacing its SDK."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import tarfile
import urllib.request


def digest(path, algorithm='sha256'):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, algorithm).hexdigest()


def verify_release(cache):
    values = dict((line.split('=', 1)[0].split(':', 1)[0], line.split('=', 1)[1])
                  for line in cache.splitlines() if '=' in line and ':' in line
                  and not line.startswith(('#', '//')))
    flags = shlex.split(values.get('CMAKE_C_FLAGS', '') + ' ' + values['CMAKE_C_FLAGS_RELEASE'])
    for prefix, expected in (('-O', '-O3'), ('-g', '-g0')):
        matches = [flag for flag in flags if flag.startswith(prefix)]
        if not matches or matches[-1] != expected:
            raise RuntimeError('Image dependency did not retain release flags')
    if values['CMAKE_BUILD_TYPE'] != 'Release' or '-DNDEBUG' not in flags or '-UNDEBUG' in flags:
        raise RuntimeError('Image dependency did not retain release assertions policy')
    return {key: values[key] for key in ('CMAKE_BUILD_TYPE', 'CMAKE_C_FLAGS', 'CMAKE_C_FLAGS_RELEASE')}


def definitions(repo):
    result = []
    for name, template, location, patch in (
        ('zlib', 'zlib-{v}.tar.xz', 'https://github.com/madler/zlib/releases/download/v{v}/zlib-{v}.tar.xz',
         '0001-CMakeList.txt-force-static-library-name-to-z.patch'),
        ('png', 'libpng-{v}.tar.xz', 'https://downloads.sourceforge.net/project/libpng/libpng16/{v}/libpng-{v}.tar.xz',
         '0001-Put-the-build-include-include-before-the-CMake-Platf.patch')):
        recipe = repo / 'contrib/src' / name
        version = re.search(r'^' + name.upper() + r'_VERSION := ([0-9.]+)$',
                            (recipe / 'rules.mak').read_text(), re.M).group(1)
        archive = template.format(v=version)
        hashes = dict((line.split()[1], line.split()[0]) for line in
                      (recipe / 'SHA512SUMS').read_text().splitlines() if line.strip())
        result.append({'name': name, 'version': version, 'archive': archive,
            'url': location.format(v=version), 'sha512': hashes[archive],
            'patches': {patch: digest(recipe / patch)}})
    return result


def mac_link_rules(work, prefix):
    """Inherited by recursive GNU make; retain configured global flags."""
    maps = work / 'link-maps'
    maps.mkdir(parents=True, exist_ok=True)
    rules = ['# Exact updated image archives for VLC, including recursive module builds.',
        'override LIBZ = -L' + str(prefix / 'lib') + ' -lz',
        'override libpng_plugin_la_LIBADD = ' + str(prefix / 'lib/libpng16.a') +
        ' ' + str(prefix / 'lib/libz.a') + ' $(LIBM)']
    filename = work / 'mac-image-links.mk'
    rules.append('libvlc_mp4.la: ' + str(filename))
    for name in ('png', 'inflate', 'mkv', 'mp4', 'sap', 'avformat'):
        target = 'lib' + name + '_plugin.la'
        rules += [target + ': ' + str(prefix / 'lib/libz.a') + ' ' + str(filename),
            target + ': LDFLAGS += -L' + str(prefix / 'lib') +
            ' -Wl,-map,' + str(maps / (name + '.map'))]
    rules.append('libpng_plugin.la: ' + str(prefix / 'lib/libpng16.a'))
    text = '\n'.join(rules) + '\n'
    if not filename.exists() or filename.read_text() != text:
        filename.write_text(text)
    return filename


def verify_mac_links(work, build):
    receipt = json.loads((work / 'build-receipt.json').read_text())
    libraries = {item['name']: Path(item['prefix']) / 'lib' / item['static_library']
                 for item in receipt['libraries']}
    for item in receipt['libraries']:
        if digest(libraries[item['name']]) != item['library_sha256']:
            raise RuntimeError('Updated image archive changed after compilation')
    links = []
    for filename in sorted((work / 'link-maps').glob('*.map')):
        plugin = build / 'modules/.libs' / ('lib' + filename.stem + '_plugin.dylib')
        if not plugin.is_file():
            raise RuntimeError('Image link map lacks its actual VLC plugin: ' + str(plugin))
        text = filename.read_text()
        selected = [name for name, path in libraries.items() if str(path) + '(' in text]
        if not selected:
            raise RuntimeError('No updated archive member selected: ' + str(filename))
        links.append({'plugin': str(plugin), 'unstripped_plugin_sha256': digest(plugin),
            'link_map_sha256': digest(filename), 'linked_updates': selected})
    png = [row for row in links if Path(row['plugin']).name == 'libpng_plugin.dylib']
    if len(png) != 1 or set(png[0]['linked_updates']) != {'png', 'zlib'}:
        raise RuntimeError('PNG plugin did not link both updated image archives')
    result = dict(receipt, links=links, makefile_sha256=digest(work / 'mac-image-links.mk'))
    (work / 'link-receipt.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


def prepare_source(archive, home, source, item, recipe, env):
    marker = home / 'prepared.json'
    if marker.exists():
        prepared = json.loads(marker.read_text())
        if prepared['identity'] != item or any(digest(source / name) != expected
                for name, expected in prepared['patched_sources'].items()):
            raise RuntimeError('Image source preparation binding changed')
        return
    if home.exists():
        # A successful Git no-op left this exact original extraction unprepared.
        # Resume only a byte-for-byte pristine source, preserving any other work.
        if set(home.iterdir()) != {source}:
            raise RuntimeError('Interrupted image preparation is not pristine')
        expected = {}
        with tarfile.open(archive) as bundle:
            for member in bundle:
                path = Path(member.name)
                if path.is_absolute() or '..' in path.parts or path.parts[0] != source.name:
                    raise RuntimeError('Image archive escaped its source directory')
                target = home / path
                if member.isfile():
                    with bundle.extractfile(member) as stream:
                        expected[target] = hashlib.file_digest(stream, 'sha256').hexdigest()
                elif not member.isdir():
                    raise RuntimeError('Interrupted image source is not a pristine regular-file extraction')
        actual = {path for path in source.rglob('*') if path.is_file() or path.is_symlink()}
        if actual != set(expected) or any(path.is_symlink() or digest(path) != sha for path, sha in expected.items()):
            raise RuntimeError('Interrupted image preparation is not pristine')
    else:
        home.mkdir()
        with tarfile.open(archive) as bundle:
            bundle.extractall(home, filter='data')
    if not source.is_dir():
        raise RuntimeError('Image source archive has an unexpected root')
    # Git otherwise discovers the enclosing application checkout and silently
    # ignores patches outside that checkout-relative subdirectory.
    patch_env = dict(env, GIT_CEILING_DIRECTORIES=str(home.resolve()))
    for name in ('GIT_DIR', 'GIT_WORK_TREE', 'GIT_INDEX_FILE', 'GIT_COMMON_DIR'):
        patch_env.pop(name, None)
    patched = {}
    for patch in item['patches']:
        filename = recipe / patch
        if digest(filename) != item['patches'][patch]:
            raise RuntimeError('Image dependency patch changed after binding')
        target = source / ('CMakeLists.txt' if item['name'] == 'zlib' else 'scripts/cmake/genout.cmake.in')
        before = digest(target)
        subprocess.run(['git', 'apply', '--check', str(filename)], cwd=source, env=patch_env, check=True)
        subprocess.run(['git', 'apply', str(filename)], cwd=source, env=patch_env, check=True)
        patched[target.relative_to(source).as_posix()] = digest(target)
        if patched[target.relative_to(source).as_posix()] == before:
            raise RuntimeError('Image dependency patch did not change its actual source')
    marker.write_text(json.dumps({'identity': item, 'patched_sources': patched}, sort_keys=True) + '\n')


def build(repo, work, prefix, archives, env, toolchain=None):
    """Native macOS or the existing MinGW cross toolchain; one compiler job."""
    work.mkdir(parents=True, exist_ok=True)
    archives.mkdir(parents=True, exist_ok=True)
    records = []
    for item in definitions(repo):
        archive = archives / item['archive']
        if not archive.exists():
            pending = archive.with_suffix(archive.suffix + '.pending')
            if pending.exists():
                raise RuntimeError('Inspect original interrupted image-source retrieval: ' + str(pending))
            with urllib.request.urlopen(item['url']) as response, pending.open('xb') as stream:
                while block := response.read(1024 * 1024):
                    stream.write(block)
            if digest(pending, 'sha512') != item['sha512']:
                raise RuntimeError('Image dependency source checksum differs')
            pending.replace(archive)
        if digest(archive, 'sha512') != item['sha512']:
            raise RuntimeError('Retained image dependency source changed')
        home = work / (item['name'] + '-' + item['version'])
        source = home / item['archive'].removesuffix('.tar.xz')
        prepare_source(archive, home, source, item, repo / 'contrib/src' / item['name'], env)
        directory = home / 'build'
        flags = ['-DCMAKE_BUILD_TYPE=Release', '-DBUILD_SHARED_LIBS=OFF',
            '-DCMAKE_C_FLAGS_RELEASE=-O3 -g0 -DNDEBUG -D_FILE_OFFSET_BITS=64',
            '-DCMAKE_INSTALL_PREFIX=' + str(prefix), '-DCMAKE_INSTALL_LIBDIR=lib']
        if toolchain:
            flags.append('-DCMAKE_TOOLCHAIN_FILE=' + str(toolchain))
        if item['name'] == 'zlib':
            flags += ['-DZLIB_BUILD_SHARED=OFF', '-DZLIB_BUILD_STATIC=ON',
                      '-DZLIB_BUILD_TESTING=OFF', '-DZLIB_BUILD_EXAMPLES=OFF']
        else:
            flags += ['-DPNG_SHARED=OFF', '-DPNG_STATIC=ON', '-DPNG_TESTS=OFF',
                      '-DPNG_TOOLS=OFF', '-DPNG_FRAMEWORK=OFF', '-DPNG_DEBUG_POSTFIX:STRING=',
                      '-DZLIB_INCLUDE_DIR=' + str(prefix / 'include'),
                      '-DZLIB_LIBRARY=' + str(prefix / 'lib/libz.a')]
        binding = {'flags': flags, 'source': item,
                   'toolchain_sha256': digest(toolchain) if toolchain else None}
        signature = home / 'configuration.json'
        if signature.exists() and json.loads(signature.read_text()) != binding:
            raise RuntimeError('Image build configuration changed; inspect retained objects')
        if not (directory / 'CMakeCache.txt').exists():
            subprocess.run(['cmake', '-S', str(source), '-B', str(directory), '-G', 'Ninja', *flags],
                           env=env, check=True)
            signature.write_text(json.dumps(binding, sort_keys=True) + '\n')
        elif not signature.exists():
            raise RuntimeError('Retained image build lacks its configuration binding')
        release = verify_release((directory / 'CMakeCache.txt').read_text())
        subprocess.run(['cmake', '--build', str(directory), '--parallel', '1'], env=env, check=True)
        subprocess.run(['cmake', '--install', str(directory)], env=env, check=True)
        library = prefix / 'lib' / ('libz.a' if item['name'] == 'zlib' else 'libpng16.a')
        if not library.is_file():
            raise RuntimeError('Updated image library is missing: ' + str(library))
        record = dict(item, archive_sha256=digest(archive), prefix=str(prefix),
                      static_library=library.name, library_sha256=digest(library),
                      cmake_cache_sha256=digest(directory / 'CMakeCache.txt'), release_flags=release)
        records.append(record)
    probe = work / 'abi-probe'
    probe.mkdir(exist_ok=True)
    probe_source = '''#include <string.h>
#include <zlib.h>
#include <png.h>
_Static_assert(sizeof(z_off_t) == 8, "Preserve the 64-bit zlib offset ABI");
int main(void) {
    const unsigned char input[] = "Modern VLC compression ABI";
    unsigned char compressed[128], output[128];
    uLongf packed = sizeof(compressed), unpacked = sizeof(output);
    if (strcmp(zlibVersion(), "1.4") || png_access_version_number() != 10659) return 1;
    if (((zlibCompileFlags() >> 6) & 3) != 2) return 2;
    if (compress(compressed, &packed, input, sizeof(input)) != Z_OK) return 3;
    if (uncompress(output, &unpacked, compressed, packed) != Z_OK) return 4;
    return unpacked != sizeof(input) || memcmp(input, output, sizeof(input));
}
'''
    probe_project = '''cmake_minimum_required(VERSION 3.15)
project(vlc_image_abi C)
add_executable(vlc-image-abi probe.c)
target_include_directories(vlc-image-abi PRIVATE "${IMAGE_PREFIX}/include")
target_link_libraries(vlc-image-abi PRIVATE "${IMAGE_PREFIX}/lib/libpng16.a" "${IMAGE_PREFIX}/lib/libz.a" m)
'''
    for name, text in (('probe.c', probe_source), ('CMakeLists.txt', probe_project)):
        target = probe / name
        if not target.exists() or target.read_text() != text:
            target.write_text(text)
    probe_flags = ['-DCMAKE_BUILD_TYPE=Release',
        '-DCMAKE_C_FLAGS_RELEASE=-O3 -g0 -DNDEBUG -D_FILE_OFFSET_BITS=64',
        '-DIMAGE_PREFIX=' + str(prefix)]
    if toolchain:
        probe_flags.append('-DCMAKE_TOOLCHAIN_FILE=' + str(toolchain))
    if not (probe / 'build/CMakeCache.txt').exists():
        subprocess.run(['cmake', '-S', str(probe), '-B', str(probe / 'build'), '-G', 'Ninja', *probe_flags],
                       env=env, check=True)
    verify_release((probe / 'build/CMakeCache.txt').read_text())
    subprocess.run(['cmake', '--build', str(probe / 'build'), '--parallel', '1'], env=env, check=True)
    executable = probe / 'build' / ('vlc-image-abi.exe' if toolchain else 'vlc-image-abi')
    if not toolchain:
        subprocess.run([str(executable)], env=env, check=True)
    receipt = {'libraries': records, 'offset_bits': 64,
        'probe': {'file': str(executable), 'sha256': digest(executable), 'executed': not bool(toolchain)}}
    (work / 'build-receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    return receipt


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('repo', 'work', 'prefix', 'archives'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--toolchain', type=Path)
    args = parser.parse_args()
    print(json.dumps(build(args.repo, args.work, args.prefix, args.archives,
                           os.environ.copy(), args.toolchain)), flush=True)
