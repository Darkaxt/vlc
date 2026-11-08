#!/usr/bin/env python3
"""Reuse a normal Mac package only when every changed file is test-only.

The receipt keeps the original normal source identity. It does not qualify a
release or allow production/header/QML changes to reuse an older executable.
"""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import platform
import subprocess

ROOT = Path(__file__).resolve().parents[2]
TEST_ONLY = {
    '.github/workflows/desktop-packages.yml',
    'tools/desktop-player/reuse-native-review.py',
    'tools/desktop-player/prepare-native-review.py',
    'tools/desktop-player/verify-native-player.py',
    'tools/desktop-player/verify-macos-packages.py',
    'tools/desktop-player/verify-linux-packages.py',
    'tools/desktop-player/run-linux-review.py',
    'tools/desktop-player/install-ci-dependencies.sh',
    'tools/desktop-player/native-player-client.py',
    'tools/desktop-player/test-native-packaging.py',
    # This reuse function runs only on Mac. These Windows-only recipes are not
    # consumed by its native build, packaging or player, and cannot alter it.
    'tools/windows-player/build-upstream-codecs.py',
    'tools/windows-player/compilation-pipeline.py',
}


def test_only(paths):
    return all(path in TEST_ONLY or path.startswith('doc/redesign/') for path in paths)


def mac_dependency_setup(text):
    # A Linux-only apt repair does not change the Mac SDK. Preserve the entire
    # Mac branch, its outer condition and every command after the conditional.
    mac, separator, linux = text.partition('\nelse\n')
    _, ending, tail = linux.rpartition('\nfi\n')
    if not separator or not ending:
        raise RuntimeError('Cannot establish the native dependency setup branches')
    return mac + separator + ending + tail


def workflow_build_contract(text):
    # Only the added reuse check, build condition and evidence pointer may
    # differ. Other workflow changes (including environment/commands) need a
    # normal build, even when the compiler package binding remains identical.
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
    text = text.replace('            .desktop-build/review-reuse.json\n', '')
    text = text.replace('            ${{ runner.temp }}/native-package-checks/*-runtime/*json\n', '')
    text = text.replace('            ${{ runner.temp }}/native-package-checks/*-runtime/crashes/**\n', '')
    for evidence in ('installer-exit.json', '*/*-stdout.log', '*/*-stderr.log'):
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


def reusable(work):
    if platform.system() != 'Darwin':
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
    setup = 'tools/desktop-player/install-ci-dependencies.sh'
    old_setup = subprocess.check_output(['git', 'show', base + ':' + setup], cwd=ROOT, text=True)
    if mac_dependency_setup(old_setup) != mac_dependency_setup((ROOT / setup).read_text()):
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
    if status['source_commit'] != base or not (directory / 'Modern VLC.app').is_dir():
        raise RuntimeError('Retained normal package generation is incomplete')
    spec = importlib.util.spec_from_file_location('native_build', Path(__file__).with_name('build-native.py'))
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    # Verify every generated archive/receipt before using its original app.
    for row in status['assets']:
        path = directory / row['name']
        if path.parent != directory or builder.sha(path) != row['sha256']:
            raise RuntimeError('Retained package member changed: ' + row['name'])
    app = recover_signed_app(directory, Path(os.environ['RUNNER_TEMP']) / 'native-normal-recovered')
    previous = builder.bind_source_mtimes(work)
    builder.prepare_bootstrap_sources(work, work / 'vlc-build', os.environ.copy(), previous)
    return {'normal_source_commit': base,
            'diagnostic_source_commit': builder.output('git', 'rev-parse', 'HEAD', cwd=ROOT),
            'changed_test_only_paths': changed, 'normal_package_directory': str(directory),
            'normal_application': str(app),
            'normal_archive_hashes_and_signature_verified': True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work', required=True, type=Path)
    args = parser.parse_args()
    receipt = reusable(args.work.resolve())
    (args.work / 'review-reuse.json').write_text(json.dumps(receipt, indent=2) + '\n')
    with open(os.environ['GITHUB_OUTPUT'], 'a', encoding='utf-8') as stream:
        stream.write('reuse=' + ('true' if receipt else 'false') + '\n')
        commit = receipt['normal_source_commit'] if receipt else subprocess.check_output(
            ['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
        stream.write('normal_generation=' + commit + '\n')
    print(json.dumps(receipt or {'reuse': False}, indent=2), flush=True)


if __name__ == '__main__':
    main()
