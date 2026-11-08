"""Compile a source-bound per-user installer from the verified portable tree.

Run in the pinned native toolchain through Coordinator. This creates an unsigned
artifact; actual install/playback/upgrade/uninstall qualification is separate.
"""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def nsis_string(value):
    assert '\n' not in value and '\r' not in value and '\0' not in value
    return value.replace('$', '$$').replace('"', '$\\"')


def verify_payload(payload, commit, version):
    info = json.loads((payload / 'BUILDINFO.json').read_text())
    manifest = json.loads((payload / 'FILE-MANIFEST.json').read_text())
    assert info['product'] == 'Modern VLC Fork'
    assert info['source_commit'] == manifest['source_commit'] == commit
    assert info['version'] == manifest['version'] == version
    assert not any((payload / 'portable').iterdir())
    assert not any(path.is_symlink() for path in payload.rglob('*'))
    names = set()
    for row in manifest['files']:
        name = PurePosixPath(row['path'])
        assert not name.is_absolute() and '..' not in name.parts
        assert '\\' not in row['path'] and ':' not in row['path'] and str(name) == row['path']
        assert name.parts[0] != 'portable' and row['path'] not in names
        path = payload / row['path']
        assert path.is_file() and not path.is_symlink()
        assert path.stat().st_size == row['bytes'] and digest(path) == row['sha256'], name
        names.add(row['path'])
    names.add('FILE-MANIFEST.json')
    assert {path.relative_to(payload).as_posix() for path in payload.rglob('*') if path.is_file()} == names
    return names


def removal_script(names):
    directories = set()
    lines = ['!macro RemoveShippedFiles']
    for name in sorted(names):
        relative = PurePosixPath(name)
        lines.append('  Delete "$INSTDIR\\' + nsis_string(name.replace('/', '\\')) + '"')
        for parent in relative.parents:
            if str(parent) != '.':
                directories.add(parent.as_posix())
    for name in sorted(directories, key=lambda value: (-len(PurePosixPath(value).parts), value)):
        lines.append('  RMDir "$INSTDIR\\' + nsis_string(name.replace('/', '\\')) + '"')
    return '\n'.join([*lines, '!macroend', ''])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--payload', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--work', type=Path, required=True)
    parser.add_argument('--source-commit', required=True)
    parser.add_argument('--version', required=True)
    args = parser.parse_args()
    assert Path('/proc/self/cgroup').read_text().split('::', 1)[1].strip().startswith('/llm-coordinator/')
    assert re.fullmatch('[0-9a-f]{40}', args.source_commit)
    assert re.fullmatch(r'\d+\.\d+\.\d+', args.version)
    repo = Path(__file__).resolve().parents[2]
    assert subprocess.check_output(['git', '-C', str(repo), 'rev-parse', 'HEAD'], text=True).strip() == args.source_commit
    assert not subprocess.check_output(['git', '-C', str(repo), 'status', '--porcelain'])
    payload = args.payload.resolve(strict=True)
    assert not args.work.exists() and not args.output.exists()
    names = verify_payload(payload, args.source_commit, args.version)
    args.work.mkdir(parents=True)
    remove = args.work / 'remove-shipped-files.nsh'
    remove.write_text(removal_script(names), encoding='utf-8')
    script = Path(__file__).with_name('fork-installer.nsi')
    notice = Path('/usr/share/doc/nsis/copyright')
    assert notice.is_file()
    command = ['makensis', '-V3', *['-D' + name + '=' + nsis_string(value) for name, value in {
        'VERSION': args.version, 'SOURCE_COMMIT': args.source_commit,
        'PAYLOAD': str(payload), 'OUTPUT': str(args.output.resolve()),
        'REMOVE_LIST': str(remove.resolve()), 'NSIS_NOTICE': str(notice)}.items()], str(script)]
    with (args.work / 'makensis.log').open('w') as log:
        done = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT)
    if done.returncode:
        raise RuntimeError('NSIS failed; inspect ' + str(args.work / 'makensis.log'))
    from release_symbols import pe_image
    image = pe_image(args.output)
    assert not image['debug_bytes'] and not image['coff_symbols']
    receipt = {'schema': 'modern-vlc.windows-installer.v1', 'source_commit': args.source_commit,
        'version': args.version, 'payload_manifest_sha256': digest(payload / 'FILE-MANIFEST.json'),
        'template_sha256': digest(script), 'removal_list_sha256': digest(remove),
        'nsis_version': subprocess.check_output(['makensis', '-VERSION'], text=True).strip(),
        'runtime_notice_sha256': digest(notice), 'command': command,
        'artifact': str(args.output), 'sha256': digest(args.output), 'bytes': args.output.stat().st_size,
        'pe_runtime_image_sha256': image['image_sha256'], 'debug_and_coff_symbols_absent': True,
        'install_scope': 'Dedicated per-user fork folder and HKCU ModernVLCFork uninstall entry; no VLC associations',
        'uninstall_policy': 'Exact shipped names, nonrecursive directories; preserve portable and extra user files',
        'signing': 'Unsigned', 'qualification': 'Pending isolated native install/playback/upgrade/uninstall'}
    (args.work / 'installer-result.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt), flush=True)


if __name__ == '__main__':
    main()
