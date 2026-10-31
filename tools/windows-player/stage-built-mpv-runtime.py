"""Stage the source-built MPV payloads and generate their compile-time binding.

This is part of assembly, not playback acceptance. A writable runtime JSON file
is provenance only: the player checks the identities compiled into its plugin.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime', required=True, type=Path)
    parser.add_argument('--prefix', type=Path)
    parser.add_argument('--inputs', type=Path)
    parser.add_argument('--identity-header', type=Path)
    parser.add_argument('--replace-buildinfo-sha256',
        help='Explicit identity of the previous task-owned build; permits an atomic payload refresh')
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[2]
    registry = repo / 'modules/gui/qt/player/mpv/source.json'
    pins = json.loads(registry.read_text())
    runtime = args.runtime.resolve(strict=True)
    manifest_path = runtime / 'MPV-BUILDINFO.json'
    assert not any((runtime / 'portable').iterdir()), 'Finish profile consumers before assembly'
    if args.identity_header:
        assert args.prefix is None and args.inputs is None and args.replace_buildinfo_sha256 is None
        manifest = json.loads(manifest_path.read_text())
        assert manifest['schema'] == 'vlc_redesign.mpv_build.v1'
        assert manifest['registry_sha256'] == digest(registry)
        assert [item['name'] for item in manifest['files']] == pins['runtime']['files']
        rows = []
        for item in manifest['files']:
            assert re.fullmatch('[0-9a-f]{64}', item['sha256'])
            assert digest(runtime / item['name']) == item['sha256']
            rows.append('    {"' + item['name'] + '", "' + item['sha256'] + '"},')
        header = ('// Generated from the assembled source-built runtime. Do not edit.\n'
                  '#pragma once\nnamespace MpvRuntimeIdentity {\n'
                  'struct File { const char *name; const char *sha256; };\n'
                  'inline constexpr File files[] = {\n' + '\n'.join(rows) + '\n};\n}\n')
        args.identity_header.parent.mkdir(parents=True, exist_ok=True)
        if not args.identity_header.exists() or args.identity_header.read_text() != header:
            args.identity_header.write_text(header, encoding='utf-8')
        print(json.dumps({'identity_header': str(args.identity_header), 'files': manifest['files']}))
        return
    assert args.prefix and args.inputs
    assert args.prefix.is_dir() and args.inputs.is_dir()
    previous = None
    if args.replace_buildinfo_sha256:
        assert re.fullmatch('[0-9a-f]{64}', args.replace_buildinfo_sha256)
        assert digest(manifest_path) == args.replace_buildinfo_sha256
        previous = json.loads(manifest_path.read_text())
        assert previous['schema'] == 'vlc_redesign.mpv_build.v1'
        assert previous['registry_sha256'] == digest(registry)
        assert [item['name'] for item in previous['files']] == pins['runtime']['files']
    else:
        assert not manifest_path.exists(), 'Supply the exact previous build identity before refreshing it'
    patch = repo / pins['runtime']['patch']
    assert digest(patch) == pins['runtime']['patch_sha256']
    records = []
    for pin in pins['sources']:
        archive = pin.get('archive') or pin['repository'].split('/')[1] + '-' + pin['commit'] + '.tar.gz'
        path = args.inputs / archive
        assert digest(path) == pin['sha256'], archive
        records.append(dict(pin, archive=archive, bytes=path.stat().st_size))
    headers = {}
    for name in pins['headers']:
        installed = args.prefix / 'include/mpv' / name
        expected = repo / 'modules/gui/qt/player/mpv' / name
        assert installed.read_bytes() == expected.read_bytes(), name
        headers[name] = digest(installed)
    files = []
    sdk_notices = runtime / 'licenses/dependencies/manifest.json'
    baseline = json.loads((runtime / 'BUILDINFO.json').read_text())
    assert digest(sdk_notices) == baseline['dependency_notices_manifest_sha256']
    assert sorted(path.name for path in (args.prefix / 'bin').glob('*.dll')) == sorted(pins['runtime']['files'])
    for name in pins['runtime']['files']:
        source, target = args.prefix / 'bin' / name, runtime / name
        # Require a Windows x64 PE payload before handing it to the app linker.
        with source.open('rb') as stream:
            assert stream.read(2) == b'MZ', name
            stream.seek(0x3c)
            pe = int.from_bytes(stream.read(4), 'little')
            stream.seek(pe)
            assert stream.read(6) == b'PE\0\0\x64\x86', name
        actual = digest(source)
        if target.exists():
            prior = digest(target)
            allowed = {actual}
            if previous:
                allowed.add(next(item['sha256'] for item in previous['files'] if item['name'] == name))
            elif name == pins['reference_runtime']['name']:
                allowed.add(pins['reference_runtime']['sha256'])
            assert prior in allowed, name
        files.append({'name': name, 'sha256': actual, 'bytes': source.stat().st_size})
    # All inputs and existing identities passed before replacing either payload.
    # An interrupted refresh can resume with a mixture of these old/new hashes.
    for item in files:
        source, target = args.prefix / 'bin' / item['name'], runtime / item['name']
        actual = item['sha256']
        if target.exists() and digest(target) == actual:
            continue
        pending = target.with_name(target.name + '.pending')
        if not pending.exists():
            shutil.copyfile(source, pending)
        assert digest(pending) == actual, 'Inspect the interrupted exact pending payload: ' + str(pending)
        pending.replace(target)
        assert digest(target) == actual
    recipe = repo / pins['runtime']['build_script']
    manifest = {'schema': 'vlc_redesign.mpv_build.v1', 'files': files, 'sources': records,
                'host_build_tools': pins.get('host_tools', []),
                'registry_sha256': digest(registry), 'api_headers_sha256': headers,
                'build_script': pins['runtime']['build_script'], 'build_script_sha256': digest(recipe),
                'install_helper_sha256': digest(repo / 'tools/windows-player/install-ffmpeg-files.py'),
                'patch': pins['runtime']['patch'], 'patch_sha256': digest(patch),
                'sdk_dependency_notices_manifest_sha256': digest(sdk_notices),
                'system_dependencies': ['Graphics-driver Vulkan loader (System32/vulkan-1.dll); not redistributed'],
                'output': 'D3D11 presentation of libplacebo BT.709/sRGB SDR conversion; no native Dolby Vision signaling claim',
                'acceptance': 'Pending complete integrated S8 stage acceptance and final delivery verification'}
    if previous:
        manifest['previous_buildinfo_sha256'] = args.replace_buildinfo_sha256
        manifest['previous_files'] = previous['files']
    pending_manifest = manifest_path.with_suffix('.pending.json')
    pending_manifest.write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    pending_manifest.replace(manifest_path)
    print(json.dumps({'runtime': str(runtime), 'files': files}))


if __name__ == '__main__':
    main()
