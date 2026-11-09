#!/usr/bin/env python3
"""Reuse a normal native package only when every changed file is test-only.

The receipt keeps the original normal source identity. It does not qualify a
release or allow production/header/QML changes to reuse an older executable.
"""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import tarfile

ROOT = Path(__file__).resolve().parents[2]
TEST_ONLY = {
    'modules/gui/qt/maininterface/player_diagnostics.hpp',
    'modules/gui/qt/maininterface/compositor_x11_renderwindow.hpp',
    '.github/workflows/desktop-packages.yml',
    'tools/desktop-player/reuse-native-review.py',
    'tools/desktop-player/prepare-native-review.py',
    'tools/desktop-player/verify-native-player.py',
    'tools/desktop-player/verify-macos-packages.py',
    'tools/desktop-player/verify-linux-packages.py',
    'tools/desktop-player/run-linux-review.py',
    'tools/desktop-player/install-ci-dependencies.sh',
    'tools/desktop-player/native-player-client.py',
    'tools/desktop-player/native-jit-unwinder.py',
    'tools/desktop-player/test-native-packaging.py',
    'tools/desktop-player/compact-native-cache.py',
    'tools/desktop-player/diagnose-linux-startup.py',
    # These Windows-only recipes are not consumed by the native Mac/Linux
    # build, packaging or player, and cannot alter their normal packages.
    'tools/windows-player/build-upstream-codecs.py',
    'tools/windows-player/compilation-pipeline.py',
}


def test_only(paths):
    return all(path in TEST_ONLY or path.startswith('doc/redesign/') for path in paths)


def normal_diagnostic_header(text):
    """Compare every byte outside the diagnostic-only preprocessor branch."""
    lines = text.splitlines(keepends=True)
    normal = []
    depth = 0
    for line in lines:
        directive = line.lstrip()
        if depth == 0:
            if line == '#ifdef VLC_PLAYER_DIAGNOSTICS\n':
                depth = 1
            else:
                normal.append(line)
        elif re.match(r'#\s*(if|ifdef|ifndef)\b', directive):
            depth += 1
        elif re.match(r'#\s*endif\b', directive):
            depth -= 1
        elif depth == 1 and re.match(r'#\s*(else|elif)\b', directive):
            raise RuntimeError('Diagnostic header has a production alternate branch')
    if depth:
        raise RuntimeError('Unclosed diagnostic header guard')
    return ''.join(normal)


def mac_dependency_setup(text):
    # A Linux-only apt repair does not change the Mac SDK. Preserve the entire
    # Mac branch, its outer condition and every command after the conditional.
    mac, separator, linux = text.partition('\nelse\n')
    _, ending, tail = linux.rpartition('\nfi\n')
    if not separator or not ending:
        raise RuntimeError('Cannot establish the native dependency setup branches')
    return mac + separator + ending + tail


def workflow_build_contract(text):
    # Bind the complete normal build job through its package-generation command.
    # Diagnostic-only jobs and post-upload retention cannot change its bytes.
    # A global environment change still invalidates this binding.
    head, separator, jobs = text.partition('\njobs:\n')
    if not separator:
        raise RuntimeError('Native workflow has no explicit jobs mapping')
    global_environment = re.search(r'^env:\n(?:(?:[ \t].*|)\n)*', head, re.MULTILINE)
    _, separator, build = jobs.partition('  build:\n')
    build, end, _ = build.partition('      - name: Verify recovered normal macOS ZIP and DMG applications\n')
    if not separator or not end:
        raise RuntimeError('Native workflow normal build boundaries changed')
    text = (global_environment[0] if global_environment else '') + build
    # Cache-retirement API authority does not participate in compilation.
    text = re.sub(r'^    permissions:\n(?:      [^\n]*\n)*', '', text, flags=re.MULTILINE)
    text = text.replace(" ${{ inputs.native_ui_only && '--require-reuse' || '' }}", '')
    text = text.replace('      - name: Check unchanged normal package for test-only repair\n'
        '        id: review_reuse\n'
        '        run: python3 tools/desktop-player/reuse-native-review.py --work "$GITHUB_WORKSPACE/.desktop-build"\n', '')
    text = text.replace("        if: steps.review_reuse.outputs.reuse != 'true'\n", '')
    text = text.replace('        id: normal_build\n', '')
    text = text.replace(' --scratch "$RUNNER_TEMP/native-package-checks" --trace-launch\n',
                        ' --scratch "$RUNNER_TEMP/native-package-checks"\n')
    text = text.replace("        if: ${{ !cancelled() && runner.os == 'macOS' && (steps.normal_build.outcome == 'success' || steps.review_reuse.outputs.reuse == 'true') }}\n",
                        "        if: runner.os == 'macOS'\n")
    text = text.replace("        if: ${{ !cancelled() && runner.os == 'Linux' && steps.normal_build.outcome == 'success' }}\n",
                        "        if: runner.os == 'Linux'\n")
    text = text.replace("        if: ${{ !cancelled() && runner.os == 'Linux' && (steps.normal_build.outcome == 'success' || steps.review_reuse.outputs.reuse == 'true') }}\n",
                        "        if: runner.os == 'Linux'\n")
    text = text.replace('            .desktop-build/review-reuse.json\n', '')
    text = text.replace('            ${{ runner.temp }}/native-package-checks/*-runtime/*json\n', '')
    text = text.replace('            ${{ runner.temp }}/native-package-checks/*-runtime/crashes/**\n', '')
    for evidence in ('installer-exit.json', '*/*-stdout.log', '*/*-stderr.log',
                     '*-runtime/*/*.log', '*-runtime/*/*.json', '*-runtime/*/crashes/**'):
        text = text.replace('            ${{ runner.temp }}/native-package-checks/' + evidence + '\n', '')
    return text.replace('${{ steps.review_reuse.outputs.normal_generation || github.sha }}', '${{ github.sha }}')


def recover_signed_app(directory, scratch):
    # actions/cache's tar does not preserve extended code signatures on data
    # (Lua, JAR and plugins.dat). The normal ditto ZIP explicitly does. Recover
    # from the already hash-verified archive, never re-sign changed cache bytes.
    archives = [path for path in directory.glob('*.zip')
                if '-symbols' not in path.name and '-corresponding-source-' not in path.name]
    if len(archives) != 1:
        raise RuntimeError('Expected one normal Mac ZIP for signature-preserving recovery')
    scratch.mkdir(parents=True, exist_ok=False)
    subprocess.run(['ditto', '-x', '-k', archives[0], scratch], check=True)
    app = scratch / 'Modern VLC.app'
    subprocess.run(['codesign', '--verify', '--deep', '--strict', app], check=True)
    return app


def recover_linux_app(directory, scratch):
    archives = list(directory.glob('*.tar.xz'))
    if len(archives) != 1:
        raise RuntimeError('Expected one hash-verified normal Linux TAR')
    name = archives[0].name.removesuffix('.tar.xz')
    scratch.mkdir(parents=True, exist_ok=False)
    with tarfile.open(archives[0], 'r:xz') as archive:
        for member in archive.getmembers():
            path = Path(member.name)
            if path.is_absolute() or '..' in path.parts or not path.parts or path.parts[0] != name:
                raise RuntimeError('Normal TAR escaped its source-bound payload')
        archive.extractall(scratch, filter='data')
    app = scratch / name
    if not (app / 'modern-vlc').is_file():
        raise RuntimeError('Recovered Linux payload has no native player')
    return app


def reusable(work):
    mac = platform.system() == 'Darwin'
    if not mac and platform.system() != 'Linux':
        return None
    required = ['native-build.json', 'package-output.json', 'toolchain-binding.json',
                'bootstrap-generated.tar', 'source-times.json']
    if any(not (work / path).is_file() for path in required):
        return None
    build = json.loads((work / 'native-build.json').read_text())
    package = json.loads((work / 'package-output.json').read_text())
    base = build['source_commit']
    if package['source_commit'] != base or build['architecture'] != platform.machine():
        return None
    if (ROOT / '.desktop-toolchain/binding.json').read_bytes() != (work / 'toolchain-binding.json').read_bytes():
        return None
    changed = subprocess.check_output(['git', 'diff', '--name-only', '-z', base, 'HEAD'],
                                      cwd=ROOT, text=True).split('\0')
    changed = [path for path in changed if path]
    if not test_only(changed):
        return None
    for diagnostic_header in ('modules/gui/qt/maininterface/player_diagnostics.hpp',
                              'modules/gui/qt/maininterface/compositor_x11_renderwindow.hpp'):
        if diagnostic_header in changed:
            original = subprocess.check_output(['git', 'show', base + ':' + diagnostic_header], cwd=ROOT, text=True)
            if normal_diagnostic_header(original) != normal_diagnostic_header((ROOT / diagnostic_header).read_text()):
                return None
    setup = 'tools/desktop-player/install-ci-dependencies.sh'
    old_setup = subprocess.check_output(['git', 'show', base + ':' + setup], cwd=ROOT, text=True)
    current_setup = (ROOT / setup).read_text()
    same_setup = (mac_dependency_setup(old_setup) == mac_dependency_setup(current_setup)) if mac else old_setup == current_setup
    if not same_setup:
        return None
    workflow = '.github/workflows/desktop-packages.yml'
    old_workflow = subprocess.check_output(['git', 'show', base + ':' + workflow], cwd=ROOT, text=True)
    if workflow_build_contract(old_workflow) != workflow_build_contract((ROOT / workflow).read_text()):
        return None
    directory = Path(package['directory']).resolve()
    if directory != (work / 'packages' / base).resolve():
        raise RuntimeError('Normal package escaped its source generation')
    if not (directory / 'PACKAGE-STATUS.json').is_file():
        return None
    status = json.loads((directory / 'PACKAGE-STATUS.json').read_text())
    if status['source_commit'] != base:
        raise RuntimeError('Retained normal package generation is incomplete')
    spec = importlib.util.spec_from_file_location('native_build', Path(__file__).with_name('build-native.py'))
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    # The full source/symbol/installer copies were uploaded before cache
    # compaction. Test-only reuse needs the exact retained runtime and source
    # index; it does not claim to reverify the other uploaded assets.
    runtime_assets = [row['name'] for row in status['assets'] if
        (row['name'].endswith('.zip') if mac else row['name'].endswith('.tar.xz'))
        and '-symbols' not in row['name'] and '-corresponding-source-' not in row['name']]
    if len(runtime_assets) != 1:
        raise RuntimeError('Retained normal runtime archive is ambiguous')
    required_assets = {runtime_assets[0], 'NATIVE-SOURCE-ASSETS.json'}
    if mac:
        required_assets.add(runtime_assets[0].removesuffix('.zip') + '.dmg')
    else:
        stem = runtime_assets[0].removesuffix('.tar.xz')
        required_assets.update(stem + '.' + suffix for suffix in ('AppImage', 'deb', 'rpm', 'snap'))
    verified_assets, archived_assets = [], []
    for row in status['assets']:
        path = directory / row['name']
        if path.parent != directory or path.is_symlink():
            raise RuntimeError('Retained package member was redirected: ' + row['name'])
        if not path.exists() and row['name'] not in required_assets:
            archived_assets.append(row['name'])
            continue
        if not path.is_file() or builder.sha(path) != row['sha256']:
            raise RuntimeError('Retained package member changed: ' + row['name'])
        verified_assets.append(row['name'])
    if not required_assets <= set(verified_assets):
        raise RuntimeError('Retained runtime or source index is incomplete')
    recovery = Path(os.environ['RUNNER_TEMP']) / 'native-normal-recovered'
    app = recover_signed_app(directory, recovery) if mac else recover_linux_app(directory, recovery)
    previous = builder.bind_source_mtimes(work)
    builder.prepare_bootstrap_sources(work, work / 'vlc-build', os.environ.copy(), previous)
    return {'normal_source_commit': base,
            'diagnostic_source_commit': builder.output('git', 'rev-parse', 'HEAD', cwd=ROOT),
            'changed_test_only_paths': changed, 'normal_package_directory': str(directory),
            'normal_application': str(app),
            'verified_retained_assets': verified_assets,
            'other_assets_in_original_artifact_not_reverified': archived_assets,
            'normal_archive_hashes_verified': True,
            'normal_archive_hashes_and_signature_verified': mac}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work', required=True, type=Path)
    parser.add_argument('--require-reuse', action='store_true',
        help='Reject an unavailable unchanged runtime instead of allowing a normal rebuild')
    args = parser.parse_args()
    receipt = reusable(args.work.resolve())
    if args.require_reuse and receipt is None:
        raise RuntimeError('Requested UI-only observation has no verified reusable normal runtime; no rebuild allowed')
    (args.work / 'review-reuse.json').write_text(json.dumps(receipt, indent=2) + '\n')
    with open(os.environ['GITHUB_OUTPUT'], 'a', encoding='utf-8') as stream:
        stream.write('reuse=' + ('true' if receipt else 'false') + '\n')
        commit = receipt['normal_source_commit'] if receipt else subprocess.check_output(
            ['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
        stream.write('normal_generation=' + commit + '\n')
    print(json.dumps(receipt or {'reuse': False}, indent=2), flush=True)


if __name__ == '__main__':
    main()
