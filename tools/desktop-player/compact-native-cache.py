#!/usr/bin/env python3
"""Keep native compiler continuation separate from uploaded package duplicates.

Only runs after the existing artifact upload. Generated copies are moved to the
same disposable runner's scratch, never deleted or moved out of the runner.
SDKs, dependency sources/objects, configuration and exact source mtimes stay put.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[2]
RUNTIME = re.compile(r'Modern-VLC-Fork-[0-9.]+-(?:macos-[a-z0-9_]+\.zip|linux-[a-z0-9_]+\.tar\.xz)')
NORMAL_FORMAT = re.compile(r'Modern-VLC-Fork-[0-9.]+-(?:macos-[a-z0-9_]+\.(?:zip|dmg)|linux-[a-z0-9_]+\.(?:tar\.xz|AppImage|deb|rpm|snap))')


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def census(work):
    result = {}
    for root, directories, files in os.walk(work, followlinks=False):
        directories[:] = [name for name in directories if not (Path(root) / name).is_symlink()]
        for name in files:
            path = Path(root) / name
            if path.is_symlink():
                continue
            key = path.relative_to(work).parts[0]
            result[key] = result.get(key, 0) + path.stat().st_size
    return result


def compact(work, destination, expected_generation=None):
    work, destination = work.resolve(), destination.resolve()
    if destination.exists() or destination.is_relative_to(work) or work.is_relative_to(destination):
        raise RuntimeError('Native cache scratch must be a new independent runner directory')
    before = census(work)
    result = {'before_bytes': sum(before.values()), 'before_directories': before, 'moved': []}
    pointer = work / 'package-output.json'
    if not pointer.exists():
        return dict(result, state='No package generation; original compiler continuation preserved')
    package = json.loads(pointer.read_text())
    generation = package['source_commit']
    if not re.fullmatch('[0-9a-f]{40}', generation):
        raise RuntimeError('Invalid retained source generation')
    output = work / 'packages' / generation
    if Path(package['directory']).resolve() != output.resolve() or output.is_symlink():
        raise RuntimeError('Native package generation was redirected')
    status_path = output / 'PACKAGE-STATUS.json'
    if (expected_generation is not None and generation != expected_generation) or not status_path.exists():
        return dict(result, state='Incomplete new package; original compiler continuation preserved')
    status = json.loads(status_path.read_text())
    if status['source_commit'] != generation or not status['assets']:
        raise RuntimeError('Native package source identity changed')
    names = []
    for row in status['assets']:
        name = row['name']
        if Path(name).name != name or '/' in name or '\\' in name or name in names:
            raise RuntimeError('Invalid or duplicate native package asset')
        asset = output / name
        if asset.is_symlink() or not asset.is_file() or sha(asset) != row['sha256']:
            raise RuntimeError('Uploaded package asset changed: ' + name)
        names.append(name)
    runtimes = [name for name in names if RUNTIME.fullmatch(name)]
    if len(runtimes) != 1 or 'NATIVE-SOURCE-ASSETS.json' not in names:
        raise RuntimeError('Expected one normal runtime archive and source index')
    keep = {name for name in names if NORMAL_FORMAT.fullmatch(name)}
    keep.update(('NATIVE-SOURCE-ASSETS.json', 'PACKAGE-STATUS.json'))
    targets = [path for path in sorted(output.iterdir()) if path.name not in keep]
    targets += [work / name for name in ('linux-package-staging', 'corresponding-contrib')
                if (work / name).exists()]
    # Check the entire move set before changing any path. A same-volume rename
    # preserves every byte and timestamp and cannot become a copy/delete fallback.
    for path in targets:
        if path.is_symlink() or not path.resolve().is_relative_to(work):
            raise RuntimeError('Generated native package copy was redirected')
        if path.stat().st_dev != destination.parent.stat().st_dev:
            raise RuntimeError('Native cache scratch is on another filesystem')
    destination.mkdir()
    for path in targets:
        relative = path.relative_to(work)
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        path.rename(target)
        result['moved'].append(relative.as_posix())
    after = census(work)
    result.update(state='compacted', after_bytes=sum(after.values()), after_directories=after,
                  retained_runtime_archive=runtimes[0], source_commit=generation,
                  retained_asset_hashes={row['name']: row['sha256'] for row in status['assets'] if row['name'] in keep},
                  generated_copy_destination=str(destination),
                  retirement='Uploaded package copies; disposable hosted runner owns their final lifecycle')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare-request', help='Exact existing cache/artifact/source binding; no compiler execution')
    parser.add_argument('--target', choices=('macos-arm64', 'macos-intel', 'linux-x86_64', 'linux-aarch64'))
    parser.add_argument('--work', type=Path)
    parser.add_argument('--uploaded-artifact', type=int)
    parser.add_argument('--normal-source')
    args = parser.parse_args()
    if (os.environ.get('GITHUB_ACTIONS') != 'true' or os.name != 'posix'
            or Path(os.environ['GITHUB_WORKSPACE']).resolve() != ROOT):
        raise RuntimeError('Cache compaction requires the exact owned hosted runner and completed upload')
    if args.prepare_request:
        request = json.loads(args.prepare_request)
        key, source, artifact_id = request['key'], request['source'], request['artifact']
        if (not args.target or not re.fullmatch('[0-9a-f]{40}', source)
                or not key.startswith('native-' + args.target + '-')
                or not re.fullmatch('[A-Za-z0-9_-]+', key) or not isinstance(artifact_id, int)):
            raise RuntimeError('Invalid exact native cache migration binding')
        artifact = json.loads(subprocess.check_output(['gh', 'api',
            'repos/Darkaxt/vlc/actions/artifacts/' + str(artifact_id)], text=True))
        caches = json.loads(subprocess.check_output(['gh', 'api',
            'repos/Darkaxt/vlc/actions/caches?per_page=100'], text=True))
        if (artifact['expired'] or artifact['name'] != 'desktop-' + args.target + '-' + source
                or artifact['workflow_run']['head_sha'] != source
                or not key.endswith('-' + str(artifact['workflow_run']['id']))
                or len([row for row in caches['actions_caches'] if row['key'] == key]) != 1):
            raise RuntimeError('Original native cache or uploaded source identity is unavailable')
        with Path(os.environ['GITHUB_OUTPUT']).open('a') as output:
            output.write('key=' + key + '\nsource=' + source + '\nartifact=' + str(artifact_id) + '\n')
        print(json.dumps({'source':source, 'artifact':artifact_id, 'cache_key':key, 'compiler_invoked':False}))
        return
    if (args.work is None or args.work.resolve() != ROOT / '.desktop-build'
            or not args.uploaded_artifact or args.uploaded_artifact <= 0 or not args.normal_source):
        raise RuntimeError('Exact owned work directory, uploaded artifact and source are required')
    scratch = Path(os.environ['RUNNER_TEMP']).resolve() / 'native-cache-retirement'
    result = compact(args.work, scratch, args.normal_source)
    result['uploaded_artifact'] = args.uploaded_artifact
    (args.work / 'native-cache-retention.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2), flush=True)


if __name__ == '__main__':
    main()
