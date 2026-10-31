"""Split PE release symbols while proving the runtime sections are unchanged.

GNU tools run only in the owned Linux build. The parser/verification functions
also run on Windows for package and independently downloaded artifact checks.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import zlib


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def pe_image(path):
    data = Path(path).read_bytes()
    assert data[:2] == b'MZ', path
    header = struct.unpack_from('<I', data, 0x3c)[0]
    assert data[header:header + 4] == b'PE\0\0', path
    machine, count, _, symbols, symbol_count, optional_size, characteristics = struct.unpack_from('<HHIIIHH', data, header + 4)
    optional = header + 24
    assert machine == 0x8664 and struct.unpack_from('<H', data, optional)[0] == 0x20b
    strings = symbols + symbol_count * 18
    string_size = struct.unpack_from('<I', data, strings)[0] if symbols else 0
    assert not string_size or strings + string_size <= len(data)
    sections = []
    debug_bytes = 0
    debuglink = None
    for index in range(count):
        offset = optional + optional_size + index * 40
        name, virtual_size, rva, raw_size, raw, _, _, _, _, flags = struct.unpack_from('<8sIIIIIIHHI', data, offset)
        name = name.rstrip(b'\0').decode('ascii')
        if name.startswith('/') and name[1:].isdigit():
            value = int(name[1:])
            assert string_size and 4 <= value < string_size
            name = data[strings + value:strings + string_size].split(b'\0', 1)[0].decode('ascii')
        assert not raw_size or raw + raw_size <= len(data), (path, name)
        payload = data[raw:raw + raw_size] if raw_size else b''
        if name.startswith(('.debug', '.zdebug')):
            debug_bytes += raw_size
            continue
        if name == '.gnu_debuglink':
            filename = payload.split(b'\0', 1)[0]
            crc_offset = (len(filename) + 1 + 3) & ~3
            debuglink = {'name': filename.decode('ascii'), 'crc32': struct.unpack_from('<I', payload, crc_offset)[0]}
            continue
        sections.append({'name': name, 'rva': rva, 'virtual_size': virtual_size,
            'raw_size': raw_size, 'characteristics': flags, 'sha256': hashlib.sha256(payload).hexdigest()})
    directories = [list(struct.unpack_from('<II', data, optional + 112 + index * 8))
        for index in range(min(16, struct.unpack_from('<I', data, optional + 108)[0]))]
    # A PE debug directory is file metadata; all runtime directories (including
    # exports/imports/exception/TLS/IAT/relocations) must remain identical.
    if len(directories) > 6:
        directories[6] = [0, 0]
    image = {'machine': machine, 'characteristics': characteristics & ~(0x4 | 0x8 | 0x200),
        'entry_point': struct.unpack_from('<I', data, optional + 16)[0],
        'image_base': struct.unpack_from('<Q', data, optional + 24)[0],
        'section_alignment': struct.unpack_from('<I', data, optional + 32)[0],
        'subsystem_and_dll_characteristics': list(struct.unpack_from('<HH', data, optional + 68)),
        'directories': directories, 'sections': sections}
    return {'image': image, 'image_sha256': hashlib.sha256(json.dumps(image, sort_keys=True).encode()).hexdigest(),
        'debug_bytes': debug_bytes, 'coff_symbols': symbol_count,
        'coff_bytes': symbol_count * 18 + string_size, 'debuglink': debuglink}


def verify_binary(path, record):
    assert digest(path) == record['stripped_sha256'], path
    image = pe_image(path)
    assert image['image_sha256'] == record['runtime_image_sha256'], path
    assert image['debug_bytes'] == 0 and image['coff_symbols'] == 0, path
    assert image['debuglink'] == record['debuglink'], path
    return image


def verify_runtime(runtime, manifest=None):
    runtime = Path(runtime)
    assert not any(path.is_file() and path.name.endswith(('.debug', '.pdb', '.release-pending'))
        for path in runtime.rglob('*')), 'Symbol or unfinished staging output in runtime'
    manifest = manifest or json.loads((runtime / 'RELEASE-SYMBOLS.json').read_text())
    assert manifest['schema'] == 'vlc_redesign.release_symbols.v1' and manifest['complete']
    files = sorted(path.relative_to(runtime).as_posix() for path in runtime.rglob('*')
        if path.is_file() and path.suffix.lower() in ('.dll', '.exe'))
    assert files == sorted(manifest['files']), 'Every shipped PE must be covered'
    for name in files:
        verify_binary(runtime / name, manifest['files'][name])
    return manifest


def save(path, value):
    pending = path.with_suffix('.pending.json')
    pending.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')
    pending.replace(path)


def strip_binary(source, symbols, relative, debug_source=None):
    original_sha = digest(source)
    before = pe_image(source)
    debug_source = debug_source or source
    assert pe_image(debug_source)['image'] == before['image'], 'Debug source does not match runtime: ' + str(source)
    debug = symbols / Path(relative).parent / '.debug' / (Path(relative).name + '.debug')
    debug.parent.mkdir(parents=True, exist_ok=True)
    pending = source.with_name(source.name + '.release-pending')
    assert not pending.exists() and not debug.exists(), 'Inspect interrupted exact output before resuming'
    subprocess.run(['x86_64-w64-mingw32-objcopy', '--only-keep-debug', str(debug_source), str(debug)], check=True)
    # Fully linked PE images keep loader imports/exports/relocations in their
    # runtime sections. strip-unneeded retains extra COFF import symbols; remove
    # that table completely and prove all runtime sections/directories unchanged.
    subprocess.run(['x86_64-w64-mingw32-strip', '--strip-all', '-o', str(pending), str(source)], check=True)
    subprocess.run(['x86_64-w64-mingw32-objcopy', '--add-gnu-debuglink=' + str(debug), str(pending)], check=True)
    after = pe_image(pending)
    assert after['image'] == before['image'], 'Stripping changed runtime sections/directories: ' + str(source)
    assert not after['debug_bytes'] and not after['coff_symbols']
    crc = 0
    with debug.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            crc = zlib.crc32(chunk, crc)
    assert after['debuglink'] == {'name': debug.name, 'crc32': crc}
    record = {'original_sha256': original_sha, 'original_bytes': source.stat().st_size,
        'stripped_sha256': digest(pending), 'stripped_bytes': pending.stat().st_size,
        'runtime_image_sha256': before['image_sha256'], 'debuglink': after['debuglink'],
        'symbols_path': debug.relative_to(symbols).as_posix(), 'symbols_sha256': digest(debug),
        'symbols_bytes': debug.stat().st_size, 'full_build_debug_source': debug_source != source}
    pending.replace(source)
    verify_binary(source, record)
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime', required=True, type=Path)
    parser.add_argument('--symbols', type=Path)
    parser.add_argument('--build', type=Path)
    parser.add_argument('--mpv-only', action='store_true')
    parser.add_argument('--verify-only', action='store_true')
    args = parser.parse_args()
    if args.verify_only:
        manifest = verify_runtime(args.runtime)
        print(json.dumps({'verified_all_pe_files': len(manifest['files']), 'debug_and_coff_symbols_absent': True}))
        return
    assert Path('/proc/self/cgroup').read_text().split('::', 1)[1].strip().startswith('/llm-coordinator/')
    assert args.symbols and not any((args.runtime / 'portable').iterdir())
    args.symbols.mkdir(parents=True, exist_ok=True)
    manifest_path = args.symbols / 'manifest.json'
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {
        'schema': 'vlc_redesign.release_symbols.v1', 'complete': False,
        'method': 'GNU objcopy --only-keep-debug; strip --strip-all; objcopy --add-gnu-debuglink',
        'helper_sha256': digest(__file__), 'tools': {name: subprocess.check_output([name, '--version'], text=True).splitlines()[0]
            for name in ('x86_64-w64-mingw32-strip', 'x86_64-w64-mingw32-objcopy')}, 'files': {}}
    assert manifest['helper_sha256'] == digest(__file__) and not manifest['complete']
    if args.mpv_only:
        paths = [args.runtime / name for name in ('libmpv-2.dll', 'libspirv-cross-c-shared.dll')]
    else:
        paths = sorted(path for path in args.runtime.rglob('*') if path.is_file() and path.suffix.lower() in ('.dll', '.exe'))
    original_build = {'libvlccore.dll': 'src/.libs/libvlccore.dll', 'libvlc.dll': 'lib/.libs/libvlc.dll',
        'plugins/gui/libqt_plugin.dll': 'modules/gui/qt/.libs/libqt_plugin.dll'}
    original_build.update({name: 'bin/.libs/' + name for name in ('vlc.exe', 'vlc-cache-gen.exe', 'vlc-preparser.exe')})
    for path in paths:
        relative = path.relative_to(args.runtime).as_posix()
        if relative in manifest['files']:
            record = manifest['files'][relative]
            verify_binary(path, record)
            assert digest(args.symbols / record['symbols_path']) == record['symbols_sha256']
            continue
        debug_source = None
        if args.build:
            candidate = args.build / original_build.get(relative, 'modules/.libs/' + path.name)
            if candidate.is_file() and pe_image(candidate)['image'] == pe_image(path)['image']:
                debug_source = candidate
        manifest['files'][relative] = strip_binary(path, args.symbols, relative, debug_source)
        save(manifest_path, manifest)
    if not args.mpv_only:
        manifest['complete'] = True
        verify_runtime(args.runtime, manifest)
        save(manifest_path, manifest)
        save(args.runtime / 'RELEASE-SYMBOLS.json', manifest)
    print(json.dumps({'symbols_manifest': str(manifest_path), 'files': len(manifest['files']),
        'complete': manifest['complete'], 'runtime_bytes': sum(value['stripped_bytes'] for value in manifest['files'].values())}), flush=True)


if __name__ == '__main__':
    main()
