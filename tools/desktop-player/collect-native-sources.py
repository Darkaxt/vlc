#!/usr/bin/env python3
"""Collect sources/notices from the native package's actual runtime owners.

Installed Homebrew receipts/SBOMs and dpkg source versions are authoritative;
the current package-manager recipe is not a replacement for the installed one.
No compiler, installed SDK or application profile is modified here.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path, PurePosixPath
import platform
import re
import shutil
import subprocess
import tarfile
import urllib.parse
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('dependency_notices',
    ROOT / 'tools/windows-player/inventory-dependency-notices.py')
notices = importlib.util.module_from_spec(spec)
spec.loader.exec_module(notices)


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def run(*args, **kwargs):
    print('+', ' '.join(map(str, args)), flush=True)
    subprocess.run(list(map(str, args)), check=True, **kwargs)


def output(*args):
    return subprocess.check_output(list(map(str, args)), text=True).strip()


def brew_sources(sbom, formula, recipe):
    """Exclude dependency bottles while retaining this formula's resources/patches."""
    result = []
    for item in sbom['packages']:
        identifier = item['SPDXID']
        # Homebrew encodes characters such as '@' in SPDX IDs. Dependencies
        # use the distinct Package-SPDXRef prefix; do not infer an ID from a
        # display/formula name or accidentally select those binary bottles.
        if not identifier.startswith(('SPDXRef-Archive-', 'SPDXRef-Patch-', 'SPDXRef-Resource-')):
            continue
        url = item.get('downloadLocation', '')
        hashes = [entry['checksumValue'] for entry in item.get('checksums', [])
                  if entry['algorithm'] == 'SHA256' and entry['checksumValue']]
        record = {'id': identifier, 'url': url,
                  'license': item.get('licenseConcluded', 'NOASSERTION')}
        if len(hashes) == 1 and re.fullmatch('[0-9a-f]{64}', hashes[0]):
            record['sha256'] = hashes[0]
        elif url.endswith('.git') and identifier.endswith('-src'):
            # Git formulae such as x264 retain their revision in the installed
            # recipe. An empty SBOM checksum must never be treated as verified.
            pin = re.search(r'url\s+"' + re.escape(url) + r'".*?revision:\s*"([0-9a-f]{40})"',
                            recipe, re.S)
            if not pin:
                raise RuntimeError('No exact installed Git revision: ' + formula)
            record['git_revision'] = pin.group(1)
        else:
            raise RuntimeError('Missing installed source checksum: ' + identifier)
        if not url.startswith(('https://', 'http://')):
            raise RuntimeError('Unsupported installed source URL: ' + url)
        result.append(record)
    if not any(item['id'].startswith('SPDXRef-Archive-') and item['id'].endswith('-src') for item in result):
        raise RuntimeError('No original source in installed SBOM: ' + formula)
    return result


def owner_of(path, installed):
    path = Path(path).resolve(strict=True)
    matches = [row for row in installed if path.is_relative_to(Path(row['keg']))]
    if len(matches) != 1:
        raise RuntimeError('Runtime input has no unique installed owner: ' + str(path))
    return matches[0]


def retain_archive_notices(archive, destination):
    records = []

    def retain(name, read):
        if not (notices.notice_name(name) or PurePosixPath(name).name.upper() in ('PATENTS', 'PATENT')):
            return
        relative = PurePosixPath(name)
        if relative.is_absolute() or '..' in relative.parts:
            raise RuntimeError('Unsafe archive notice path: ' + name)
        target = destination.joinpath(*relative.parts)
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            with read() as source:
                digest = hashlib.file_digest(source, 'sha256').hexdigest()
            if sha(target) != digest:
                raise RuntimeError('Retained notice changed: ' + str(target))
        else:
            with target.open('xb') as sink, read() as source:
                shutil.copyfileobj(source, sink)
        records.append({'file': target.relative_to(destination).as_posix(), 'sha256': sha(target)})

    if zipfile.is_zipfile(archive):
        with zipfile.ZipFile(archive) as bundle:
            for item in bundle.infolist():
                if not item.is_dir():
                    retain(item.filename, lambda item=item: bundle.open(item))
    else:
        with tarfile.open(archive) as bundle:
            for item in bundle:
                if item.isfile():
                    retain(item.name, lambda item=item: bundle.extractfile(item))
    return records


def fetch_source(record, directory):
    directory.mkdir(parents=True, exist_ok=True)
    if 'git_revision' in record:
        revision = record['git_revision']
        repository = directory / 'repository'
        if not repository.exists():
            run('git', 'init', repository)
        if subprocess.run(['git', '-C', str(repository), 'cat-file', '-e', revision + '^{commit}'],
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode:
            run('git', '-C', repository, 'fetch', '--depth=1', record['url'], revision)
        if output('git', '-C', repository, 'rev-parse', revision + '^{commit}') != revision:
            raise RuntimeError('Fetched Git source revision differs')
        archive = directory / ('source-' + revision + '.tar.gz')
        if not archive.exists():
            run('git', '-C', repository, 'archive', '--format=tar.gz', '--prefix=source/',
                '--output=' + str(archive), revision)
        record['archive_sha256'] = sha(archive)
    else:
        name = PurePosixPath(urllib.parse.urlsplit(record['url']).path).name
        if not name or name in ('.', '..'):
            raise RuntimeError('Source URL has no archive name')
        archive = directory / (record['sha256'][:16] + '-' + name)
        if not archive.exists():
            temporary = archive.with_name(archive.name + '.download')
            urllib.request.urlretrieve(record['url'], temporary)
            if sha(temporary) != record['sha256']:
                raise RuntimeError('Downloaded source checksum differs: ' + record['id'])
            temporary.replace(archive)
        if sha(archive) != record['sha256']:
            raise RuntimeError('Retained source checksum differs: ' + record['id'])
        record['archive_sha256'] = record['sha256']
    record['archive'] = str(archive)
    return archive


def collect_brew(work, app, generation, destination):
    installed = json.loads((ROOT / '.desktop-toolchain/installed-metadata.json').read_text())
    resources = app / 'Contents/Resources'
    paths = []
    for filename in ('NATIVE-DEPENDENCIES.json', 'MPV-RUNTIME.json'):
        for item in json.loads((resources / filename).read_text()):
            path = Path(item['source_path'])
            if not path.is_relative_to(work):
                if sha(path) != item['source_sha256']:
                    raise RuntimeError('Runtime source changed: ' + str(path))
                paths.append(path)
    for item in json.loads((resources / 'QT-PLUGINS.json').read_text()):
        origin = Path(item['source'])
        if sha(origin) != item['source_sha256']:
            raise RuntimeError('Qt plugin source changed: ' + str(origin))
        paths.append(origin)
    qml = json.loads((work / 'qml-deployment' / (generation + '.json')).read_text())
    for item in qml['modules']:
        origin = Path(item['source'])
        paths.append(origin)
        module = Path(*item['name'].split('.'))
        for binding in item['native_bindings']:
            source = origin / Path(binding['file']).relative_to(module)
            if sha(source) != binding['source_sha256']:
                raise RuntimeError('QML plugin source changed: ' + str(source))
            paths.append(source)
    for framework in (app / 'Contents/Frameworks').glob('*.framework'):
        candidates = [Path(row['keg']) / 'lib' / framework.name / 'Versions/A' / framework.stem
                      for row in installed]
        found = [path for path in candidates if path.is_file()]
        if len(found) != 1:
            raise RuntimeError('Packaged framework has no unique installed source: ' + framework.name)
        paths.extend(found)
    # macdeployqt also introduces non-Qt dylibs (fontconfig, Cairo, etc.). Follow
    # the *original* framework/plugin graph before rewritten loader paths lose
    # their installed ownership. The MPV/VLC closure alone is insufficient.
    loader = importlib.util.spec_from_file_location('native_package_sources', Path(__file__).with_name('package-native.py'))
    package = importlib.util.module_from_spec(loader)
    loader.loader.exec_module(package)
    pending, visited = list(paths), set()
    while pending:
        origin = pending.pop().resolve(strict=True)
        if origin in visited:
            continue
        visited.add(origin)
        if not package.native(origin):
            continue
        for dependency in package.dependencies(origin):
            if not package.external(dependency):
                resolved = package.resolve_mac_dependency(dependency, origin, package.mac_runpaths(origin))
                if not resolved.is_relative_to(work):
                    pending.append(resolved)
    owners = {(row['name'], row['version']): row for path in visited
              for row in [owner_of(path, installed)]}
    records = []
    for (formula, version), row in sorted(owners.items()):
        print('Corresponding source:', formula, version, flush=True)
        retained = ROOT / '.desktop-toolchain/installed-metadata' / formula / version
        target = destination / 'homebrew' / formula / version
        target.mkdir(parents=True, exist_ok=True)
        for relative, digest in row['metadata_sha256'].items():
            source = retained / Path(relative).name
            if sha(source) != digest:
                raise RuntimeError('Installed source metadata changed: ' + str(source))
            shutil.copy2(source, target / source.name)
        recipe = (target / (formula + '.rb')).read_text()
        sources = brew_sources(json.loads((target / 'sbom.spdx.json').read_text()), formula, recipe)
        for record in sources:
            archive = fetch_source(record, target)
            if not record['id'].startswith('SPDXRef-Patch-'):
                legal = target / ('notices-' + record['archive_sha256'][:16])
                legal.mkdir(exist_ok=True)
                record['notices'] = retain_archive_notices(archive, legal)
                (legal / 'manifest.json').write_text(json.dumps(record['notices'], indent=2) + '\n')
                if not record['notices']:
                    raise RuntimeError('Inspect source without notice files: ' + formula)
            record['archive'] = archive.relative_to(destination).as_posix()
        runtime_inputs = [{'path': str(path), 'sha256': sha(path) if path.is_file() else None}
                          for path in sorted(visited) if path.is_relative_to(Path(row['keg']))]
        records.append({'formula': formula, 'version': version, 'runtime_inputs': runtime_inputs, 'sources': sources})
    return records


def collect_contrib(work, destination):
    inputs = json.loads((ROOT / 'tools/desktop-player/native-inputs.json').read_text())
    revision = inputs['macos_contrib_commit']
    original = work / 'corresponding-contrib' / revision
    original.mkdir(parents=True, exist_ok=True)
    recipe = original / 'recipes.tar.gz'
    if not recipe.exists():
        run('git', '-C', ROOT, 'archive', '--format=tar.gz', '--output=' + str(recipe), revision,
            'contrib', 'extras/tools', 'extras/package/macosx', 'extras/ci')
    source = original / 'source'
    if not source.exists():
        source.mkdir()
        with tarfile.open(recipe) as bundle:
            bundle.extractall(source, filter='data')
    build = original / 'selection'
    build.mkdir(exist_ok=True)
    triplet = ('aarch64' if platform.machine() == 'arm64' else 'x86_64') + '-apple-darwin19'
    if not (build / 'Makefile').exists():
        run('sh', source / 'contrib/bootstrap', '--build=' + triplet, '--host=' + triplet,
            '--enable-sections', cwd=build)
    tarballs = destination / 'contrib'
    tarballs.mkdir(parents=True, exist_ok=True)
    flags = ['make', '-j1', 'PKGS_FOUND=', 'TARBALLS=' + str(tarballs)]
    with (tarballs / 'selection.txt').open('w') as stream:
        run(*flags, 'list', cwd=build, stdout=stream)
    run(*flags, 'fetch', cwd=build)
    shutil.copy2(recipe, tarballs / 'original-recipes.tar.gz')
    return {'upstream_commit': revision, 'triplet': triplet,
            'selection': (tarballs / 'selection.txt').read_text(),
            'files': [{'file': path.relative_to(destination).as_posix(), 'sha256': sha(path)}
                      for path in sorted(tarballs.iterdir()) if path.is_file()]}


def collect_linux(work, app, destination):
    paths = []
    for filename in (app / 'NATIVE-DEPENDENCIES.json', app / 'lib/mpv/runtime.json'):
        for row in json.loads(filename.read_text()):
            source = Path(row['source_path'])
            if not source.is_relative_to(work):
                if sha(source) != row['source_sha256']:
                    raise RuntimeError('Runtime source changed: ' + str(source))
                paths.append(source)
    qt = json.loads((app / 'QT-SOURCES.json').read_text())
    paths.extend(Path(path) for path in qt)
    packages = set()
    for path in paths:
        owners = output('dpkg-query', '-S', path).splitlines()
        for owner in owners:
            package, separator, original = owner.partition(': ')
            if not separator or original != str(path):
                raise RuntimeError('Ambiguous installed dpkg owner: ' + owner)
            packages.add(package)
    sources = {}
    for package in sorted(packages):
        record = output('dpkg-query', '-W', '-f=${source:Package}\t${source:Version}', package).split('\t')
        if len(record) != 2 or not all(record):
            raise RuntimeError('No installed source version: ' + package)
        sources.setdefault(tuple(record), []).append(package)
    result = []
    for (name, version), binaries in sorted(sources.items()):
        directory = destination / 'debian' / name / version
        directory.mkdir(parents=True, exist_ok=True)
        run('apt-get', 'source', '--download-only', '--only-source', name + '=' + version, cwd=directory)
        for package in binaries:
            copyright_file = Path('/usr/share/doc') / package.split(':')[0] / 'copyright'
            if not copyright_file.is_file():
                raise RuntimeError('Missing installed Debian copyright: ' + package)
            shutil.copy2(copyright_file, directory / (package.replace(':', '_') + '-copyright'))
        result.append({'source_package': name, 'version': version, 'binary_packages': binaries,
                       'files': [{'file': path.relative_to(destination).as_posix(), 'sha256': sha(path)}
                                 for path in sorted(directory.iterdir()) if path.is_file()]})
    shutil.copytree('/usr/share/common-licenses', destination / 'common-licenses', dirs_exist_ok=True)
    return result


def runtime_notices(destination, app):
    target = app / ('Contents/Resources/licenses' if platform.system() == 'Darwin' else 'licenses')
    target.mkdir(parents=True, exist_ok=True)
    for source, name in [('COPYING', 'GPL-2.0.txt'), ('COPYING.LIB', 'LGPL-2.1.txt'),
            ('modules/gui/qt/fonts/redesign/LICENSE.txt', 'INTER-OFL-1.1.txt'),
            ('modules/gui/qt/pixmaps/redesign/mpv-source.json', 'MPV-ICON-SOURCE.json'),
            ('modules/gui/qt/pixmaps/redesign/mpv-display-source.json', 'MPV-ICON-DISPLAY.json'),
            ('doc/redesign/resources/s7/FLUENT-ICONS-LICENSE.txt', 'FLUENT-ICONS-MIT.txt'),
            ('doc/redesign/resources/s7/THIRD-PARTY-NOTICES.md', 'THIRD-PARTY-NOTICES.md')]:
        blob = subprocess.check_output(['git', '-C', str(ROOT), 'show', 'HEAD:' + source])
        (target / name).write_bytes(blob)
    # Copy actual copyright/licenses, never the source archives into the player.
    for legal in sorted(destination.rglob('*')):
        if not legal.is_file() or 'repository' in legal.relative_to(destination).parts:
            continue
        parts = legal.relative_to(destination).parts
        if any(part.startswith('notices-') for part in parts) or legal.name.endswith('-copyright') \
                or 'common-licenses' in parts:
            copied = target / 'dependencies' / legal.relative_to(destination)
            copied.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(legal, copied)
    gpl = [path for path in target.rglob('*') if path.is_file()
           and path.name in ('GPL-3', 'GPL-3.0.txt', 'GPL-3.0-only.txt', 'GPL-3.0-or-later.txt')]
    if not gpl:
        raise RuntimeError('The native distribution is missing the GPL version 3 text')
    shutil.copy2(gpl[0], target / 'GPL-3.0.txt')
    (target / 'CORRESPONDING-SOURCE.txt').write_text(
        'Modern VLC Fork is a modified VLC/Qt application conveyed under GPL version 3.\n'
        'Component licenses and attributions remain in this directory.\n'
        'The matching release contains the application, original dependency sources,\n'
        'installed package recipes, patches and build instructions in its\n'
        'corresponding-source assets at https://github.com/Darkaxt/vlc/releases.\n')
    shutil.copy2(destination / 'manifest.json', target / 'NATIVE-SOURCES.json')


def collect(work, app, out, generation):
    # Source downloads are not compiler inputs. Keep the large extracted notice
    # graph outside the retained build cache; published source ZIPs remain in
    # this generation's package output and are retained with its other assets.
    destination = ROOT / '.desktop-sources' / generation
    destination.mkdir(parents=True, exist_ok=True)
    manifest = {'source_commit': generation, 'platform': platform.system(), 'architecture': platform.machine()}
    if platform.system() == 'Darwin':
        manifest['installed_dependencies'] = collect_brew(work, app, generation, destination)
        manifest['original_vlc_contrib'] = collect_contrib(work, destination)
    else:
        manifest['installed_dependencies'] = collect_linux(work, app, destination)
    built = json.loads((work / 'native-build.json').read_text())
    for original, name in [(work / 'native-build.json', 'native-build.json'),
                           (work / 'toolchain-binding.json', 'toolchain-binding.json')]:
        shutil.copy2(original, destination / name)
    manifest['source_built'] = []
    archives = destination / 'source-built'
    archives.mkdir(exist_ok=True)
    for row in built['sources']:
        if row['name'] == 'vlc-native-contrib':
            continue  # binary SDK: its source graph is collected separately above
        original = work / 'sources' / row['archive']
        if sha(original) != row['sha256']:
            raise RuntimeError('Compiled source changed: ' + row['name'])
        target = archives / original.name
        shutil.copy2(original, target)
        manifest['source_built'].append(dict(row, file=target.relative_to(destination).as_posix()))
    # Retain license and patent texts from source-built and original contrib
    # archives, in addition to the installed Homebrew/Debian notices above.
    for folder in (destination / 'contrib', archives):
        if not folder.is_dir():
            continue
        for archive in sorted(folder.iterdir()):
            if not archive.is_file() or not (zipfile.is_zipfile(archive) or tarfile.is_tarfile(archive)):
                continue
            legal = folder / ('notices-' + sha(archive)[:16])
            legal.mkdir(exist_ok=True)
            rows = retain_archive_notices(archive, legal)
            (legal / 'manifest.json').write_text(json.dumps(rows, indent=2) + '\n')
    application = destination / 'application.tar.gz'
    if not application.exists():
        run('git', '-C', ROOT, 'archive', '--format=tar.gz', '--prefix=Modern-VLC-Fork/',
            '--output=' + str(application), generation)
    manifest['application'] = {'file': application.name, 'sha256': sha(application)}
    (destination / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    runtime_notices(destination, app)
    # Preserve every source/notices/recipe member, grouped into bounded assets.
    # Compressed source archives are stored without a second compression pass.
    files = sorted(path for path in destination.rglob('*') if path.is_file() and '.git' not in path.parts
                   and 'repository' not in path.relative_to(destination).parts)
    parts, current, size = [], [], 0
    for path in files:
        if current and size + path.stat().st_size > 1500 * 1024 * 1024:
            parts.append(current); current, size = [], 0
        current.append(path); size += path.stat().st_size
    if current:
        parts.append(current)
    version = re.search(r'"(\d+\.\d+\.\d+)"',
        (ROOT / 'modules/gui/qt/dialogs/help/fork_release.hpp').read_text()).group(1)
    index = {'source_commit': generation, 'platform': platform.system(),
             'architecture': platform.machine(), 'parts': []}
    for number, members in enumerate(parts, 1):
        target = out / (f'Modern-VLC-Fork-{version}-{platform.system().lower()}-'
                        f'{platform.machine()}-corresponding-source-{number:02}.zip')
        with zipfile.ZipFile(target, 'x', zipfile.ZIP_STORED, allowZip64=True) as bundle:
            for path in members:
                bundle.write(path, path.relative_to(destination))
        index['parts'].append({'name': target.name, 'bytes': target.stat().st_size,
                               'sha256': sha(target), 'members': [
                                   {'file': path.relative_to(destination).as_posix(), 'sha256': sha(path)}
                                   for path in members]})
    (out / 'NATIVE-SOURCE-ASSETS.json').write_text(json.dumps(index, indent=2) + '\n')
    return destination


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work', required=True, type=Path)
    parser.add_argument('--app', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--generation', required=True)
    args = parser.parse_args()
    collect(args.work.resolve(), args.app.resolve(), args.out.resolve(), args.generation)
