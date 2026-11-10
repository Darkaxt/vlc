"""Seed exact archived dependency inputs from an existing complete source carrier.

Explicit failed-package recovery only. No compiler, runtime or dependency version
is changed. The original artifact, carrier and every selected input are hashed.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import platform
import re
import shutil
import subprocess
import urllib.error
import urllib.parse
import urllib.request
import zipfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def seed_part(archive, expected, pins, work):
    """Read only originals declared by the current checksum-pinned input graph."""
    copied = []
    for pin in pins:
        relative = Path('debian') / pin['source_package'] / urllib.parse.quote(pin['version'], safe='.+~-')
        cache = work / 'corresponding-source-inputs' / relative
        for row in [pin['descriptor'], *pin['files']]:
            name = PurePosixPath(urllib.parse.urlsplit(row['url']).path).name
            member = (relative / name).as_posix()
            if member not in expected:
                continue
            if expected[member] != row['sha256']:
                raise RuntimeError('Historical source differs from the current dependency pin')
            value = archive.read(member)
            if hashlib.sha256(value).hexdigest() != row['sha256'] or ('bytes' in row and len(value) != row['bytes']):
                raise RuntimeError('Recovered original source checksum/size differs')
            cache.mkdir(parents=True, exist_ok=True)
            target = cache / (row['sha256'][:16] + '-' + name)
            if target.exists():
                if digest(target) != row['sha256']:
                    raise RuntimeError('Existing dependency cache differs; preserve it')
            else:
                with target.open('xb') as stream:
                    stream.write(value)
            copied.append({'file':member, 'sha256':row['sha256'], 'cache':str(target)})
    return copied


def seed_debian_originals(archive, expected, work):
    """Seed content-addressed originals; current APT metadata still selects them.

    Never seed source-binding.json or unqualified plain filenames. The collector
    independently checks the installed version and current authenticated APT
    hashes before consuming any recovered byte.
    """
    copied = []
    for member in sorted(expected):
        path = PurePosixPath(member)
        if len(path.parts) != 4 or path.parts[0] != 'debian' or path.suffix != '.dsc':
            continue
        package, version = path.parts[1:3]
        if not re.fullmatch(r'[a-z0-9][a-z0-9+.-]*', package):
            raise RuntimeError('Unsafe recovered source package')
        descriptor = archive.read(member)
        if hashlib.sha256(descriptor).hexdigest() != expected[member]:
            raise RuntimeError('Recovered descriptor checksum differs')
        text = descriptor.decode('utf-8')
        if not re.search(r'^Source: ' + re.escape(package) + r'$', text, re.M) or not re.search(
                r'^Version: ' + re.escape(urllib.parse.unquote(version)) + r'$', text, re.M):
            raise RuntimeError('Recovered descriptor identity differs')
        section = re.search(r'^Checksums-Sha256:\n((?:[ \t].*(?:\n|$))+)', text, re.M)
        if not section:
            raise RuntimeError('Recovered descriptor has no SHA256 closure')
        rows = {path.name: (expected[member], len(descriptor))}
        for line in section[1].splitlines():
            checksum, size, name = line.split()
            if (name in rows or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9+._~%-]*', name)
                    or not re.fullmatch('[0-9a-f]{64}', checksum) or not size.isdecimal()):
                raise RuntimeError('Invalid recovered descriptor member')
            rows[name] = (checksum, int(size))
        cache = work / 'corresponding-source-inputs' / Path(*path.parent.parts)
        for name, (checksum, size) in rows.items():
            original = (path.parent / name).as_posix()
            if expected.get(original) != checksum:
                raise RuntimeError('Historical source index differs from its descriptor')
            value = descriptor if name == path.name else archive.read(original)
            if len(value) != size or hashlib.sha256(value).hexdigest() != checksum:
                raise RuntimeError('Recovered original source checksum/size differs')
            cache.mkdir(parents=True, exist_ok=True)
            target = cache / (checksum[:16] + '-' + name)
            if target.exists():
                if target.is_symlink() or digest(target) != checksum:
                    raise RuntimeError('Existing dependency cache differs; preserve it')
            else:
                with target.open('xb') as stream:
                    stream.write(value)
            copied.append({'file':original, 'sha256':checksum, 'cache':str(target)})
    return copied


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--artifact', type=int, required=True)
    parser.add_argument('--source', required=True)
    parser.add_argument('--built-source', required=True)
    parser.add_argument('--work', type=Path, required=True)
    parser.add_argument('--scratch', type=Path, required=True)
    args = parser.parse_args()
    if os.environ.get('GITHUB_ACTIONS') != 'true' or platform.system() != 'Linux':
        raise RuntimeError('Source recovery requires an owned disposable Linux CI job')
    built = json.loads((args.work / 'native-build.json').read_text())
    if built['source_commit'] != args.built_source or built['architecture'] != platform.machine():
        raise RuntimeError('Original retained build source/architecture differs')
    if (ROOT / '.desktop-toolchain/binding.json').read_bytes() != (args.work / 'toolchain-binding.json').read_bytes():
        raise RuntimeError('Retained toolchain differs; no source recovery or compiler was started')
    metadata = json.loads(subprocess.check_output(['gh','api',
        'repos/Darkaxt/vlc/actions/artifacts/' + str(args.artifact)], text=True))
    if metadata['expired'] or metadata['workflow_run']['head_sha'] != args.source or not metadata['name'].endswith('-' + args.source):
        raise RuntimeError('Historical source artifact identity differs')
    if not metadata.get('digest', '').startswith('sha256:'):
        raise RuntimeError('Historical source artifact has no published digest')
    args.scratch.mkdir(parents=True, exist_ok=False)
    spec = importlib.util.spec_from_file_location('ci_evidence', HERE / 'read-ci-evidence.py')
    evidence = importlib.util.module_from_spec(spec); spec.loader.exec_module(evidence)
    token = subprocess.check_output(['gh','auth','token'], text=True).strip()
    request = urllib.request.Request(metadata['archive_download_url'], headers={
        'Authorization':'Bearer ' + token, 'Accept':'application/vnd.github+json'})
    try:
        urllib.request.build_opener(evidence.NoRedirect()).open(request)
        raise RuntimeError('Expected authenticated artifact redirect')
    except urllib.error.HTTPError as error:
        if error.code != 302:
            raise
        location = error.headers['Location']
    del token, request
    if not location.startswith('https://'):
        raise RuntimeError('Source artifact redirect is not HTTPS')
    downloaded = args.scratch / 'source-artifact.zip'
    with urllib.request.urlopen(location) as response, downloaded.open('xb') as stream:
        shutil.copyfileobj(response, stream, 1024 * 1024)
    if downloaded.stat().st_size != metadata['size_in_bytes'] or 'sha256:' + digest(downloaded) != metadata['digest']:
        raise RuntimeError('Historical source artifact bytes differ')
    pins = json.loads((ROOT / 'tools/desktop-player/native-inputs.json').read_text())['linux_archived_sources']
    copied = []
    with zipfile.ZipFile(downloaded) as outer:
        indices = [row for row in outer.infolist() if row.filename.endswith('/packages/' + args.source + '/NATIVE-SOURCE-ASSETS.json')]
        if len(indices) != 1:
            raise RuntimeError('No unique original complete source index')
        index = json.loads(outer.read(indices[0]))
        if index['source_commit'] != args.source:
            raise RuntimeError('Historical source index has another application identity')
        prefix = indices[0].filename.removesuffix('NATIVE-SOURCE-ASSETS.json')
        for part in index['parts']:
            expected = {row['file']:row['sha256'] for row in part['members']}
            if not any(name.startswith('debian/') and name.endswith('.dsc') for name in expected):
                continue
            name = part['name']
            if Path(name).name != name or '/' in name or '\\' in name:
                raise RuntimeError('Unsafe historical source carrier name')
            target = args.scratch / name
            with outer.open(prefix + name) as original, target.open('xb') as stream:
                shutil.copyfileobj(original, stream, 1024 * 1024)
            if target.stat().st_size != part['bytes'] or digest(target) != part['sha256']:
                raise RuntimeError('Historical source carrier checksum differs')
            with zipfile.ZipFile(target) as archive:
                copied.extend(seed_part(archive, expected, pins, args.work))
                copied.extend(seed_debian_originals(archive, expected, args.work))
    copied = list({row['file']:row for row in copied}.values())
    required = {row['sha256'] for pin in pins for row in [pin['descriptor'], *pin['files']]}
    if not required.issubset({row['sha256'] for row in copied}):
        raise RuntimeError('Historical carrier does not cover the exact archived input closure')
    # Checkout timestamps must not turn the later diagnostic-hook build into a
    # whole-player rebuild. Restore only byte-identical tracked inputs and the
    # existing hash-bound bootstrap archive; never run bootstrap/configure here.
    spec = importlib.util.spec_from_file_location('native_build', HERE / 'build-native.py')
    build = importlib.util.module_from_spec(spec); spec.loader.exec_module(build)
    tracked = set(build.output('git','ls-files','-z',cwd=ROOT).split('\0'))
    binding = args.work / 'bootstrap-inputs.json'
    if not (args.work / 'bootstrap-generated.tar').is_file() or not binding.is_file() or \
            json.loads(binding.read_text()) != build.bootstrap_inputs(tracked):
        raise RuntimeError('Original generated-source binding is missing or differs')
    previous = build.bind_source_mtimes(args.work)
    build.prepare_bootstrap_sources(args.work, args.work / 'vlc-build', os.environ.copy(), previous)
    result = {'artifact':metadata, 'original_source':args.source, 'built_source':args.built_source,
              'compiler_invoked':False, 'inputs':copied}
    (args.work / 'source-input-recovery.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'recovered_inputs':len(copied), 'built_source':args.built_source}), flush=True)


if __name__ == '__main__':
    main()
