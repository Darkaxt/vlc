"""Prove a Qt-only change can retain this exact completed application cohort."""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import subprocess

from release_profile import verify_release
from repair_qt_backingstore_contract import verify_qt_accessor


def verify_shared_codec_policy(before, after):
    # Windows imports verify_aom_release_flags from this hosted build helper.
    # Permit the reviewed Cocoa/main build changes only; retain every import,
    # module assignment and shared codec-policy definition bytecode-equivalent.
    def shared_tree(text):
        tree = ast.parse(text)
        tree.body = [node for node in tree.body
            if not (isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant)
                    and isinstance(node.value.value, str))
            and not (isinstance(node, ast.FunctionDef)
                     and node.name in ('meson', 'prepare_mpv_cocoa_guard', 'main'))]
        return ast.dump(tree, include_attributes=False)
    assert shared_tree(before) == shared_tree(after), 'Shared Windows codec policy changed'
    return {'shared_codec_policy_unchanged': True,
        'before_sha256': hashlib.sha256(before.encode()).hexdigest(),
        'after_sha256': hashlib.sha256(after.encode()).hexdigest()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--build', type=Path, required=True)
    parser.add_argument('--runtime', type=Path, required=True)
    args = parser.parse_args()
    assert Path('/proc/self/cgroup').read_text().split('::', 1)[1].strip().startswith('/llm-coordinator/')
    source = args.source.resolve()
    assert not subprocess.check_output(['git', '-C', str(source), 'status', '--porcelain'])
    manifest = args.runtime / 'VLC-PLUGIN-BUILDINFO.json'
    original = json.loads(manifest.read_text())
    baseline = original['source_commit']
    head = subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip()
    subprocess.run(['git', '-C', str(source), 'merge-base', '--is-ancestor', baseline, head], check=True)
    source_changes = subprocess.check_output(['git', '-C', str(source), 'diff', '--name-only', baseline, head], text=True).splitlines()
    # Hosted packaging/scripts do not build Windows plugins. The shared native
    # helper is the exception: prove its imported codec policy stayed identical.
    native_policy = 'tools/desktop-player/build-native.py'
    shared_policy = None
    if native_policy in source_changes:
        def policy_at(commit):
            return subprocess.check_output(['git', '-C', str(source), 'show',
                commit + ':' + native_policy], text=True)
        shared_policy = verify_shared_codec_policy(policy_at(baseline), policy_at(head))
    changes = [name for name in source_changes
               if name not in ('test/libvlc/test.h', 'README.md', '.github/workflows/desktop-packages.yml')
               and not name.startswith(('doc/redesign/', 'tools/windows-player/',
                                        'tools/design-source/', 'tools/desktop-player/'))]
    qt_accessor=verify_qt_accessor(source,args.runtime,baseline,changes)
    assert all(name.startswith('modules/gui/qt/') or name in qt_accessor['allowed_source_paths'] for name in changes), changes
    assert original['schema'] == 'vlc_redesign.full_plugin_build.v1'
    retained = []
    for item in original['plugins']:
        if item['file'] == 'plugins/gui/libqt_plugin.dll':
            continue
        binary = Path(item['build_source'])
        target = args.runtime / item['file']
        assert binary.resolve().is_relative_to(args.build.resolve())
        assert hashlib.sha256(binary.read_bytes()).hexdigest() == item['unstripped_sha256'], binary
        retained.append(dict(item, staged_sha256=hashlib.sha256(target.read_bytes()).hexdigest()))
    assert len(retained) > 300
    result = {'schema': 'vlc_redesign.qt_only_cohort.v1', 'source_commit': head,
        'retained_from_source': baseline, 'original_manifest_sha256': hashlib.sha256(manifest.read_bytes()).hexdigest(),
        'source_changes': source_changes, 'production_changes': changes,
        'shared_native_codec_policy': shared_policy,
        'qt_private_accessor':qt_accessor,
        'release_profile': verify_release(args.build), 'plugins': retained}
    (args.runtime / 'VLC-PLUGIN-REUSE.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'qt_only_source_verified': head, 'unchanged_plugin_cohort': baseline,
        'retained_plugins': len(retained)}), flush=True)


if __name__ == '__main__':
    main()
