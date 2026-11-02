"""Prove a Qt-only change can retain this exact completed application cohort."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

from release_profile import verify_release


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
    changes = [name for name in source_changes if not name.startswith(('doc/redesign/', 'tools/windows-player/', 'tools/design-source/'))]
    assert all(name.startswith('modules/gui/qt/') for name in changes), changes
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
        'release_profile': verify_release(args.build), 'plugins': retained}
    (args.runtime / 'VLC-PLUGIN-REUSE.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'qt_only_source_verified': head, 'unchanged_plugin_cohort': baseline,
        'retained_plugins': len(retained)}), flush=True)


if __name__ == '__main__':
    main()
