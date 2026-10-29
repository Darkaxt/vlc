"""Compare actual native module roles and option keys/types with the VLC baseline.

The baseline public inventory may omit internal/obsolete options. Additional
raw entries are recorded, not described as new product features. Reachability
and persistence still require the separate source/native UI reconciliation.
"""
import argparse
import hashlib
import json
from pathlib import Path


def normalized(value):
    roles = set()
    options = set()
    for module in value['modules']:
        roles.add((module['id'], module['capability']))
        for option in module['options']:
            options.add((option['name'], option['type']))
    return roles, options


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', required=True, type=Path)
    parser.add_argument('--current', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    assert not args.output.exists()
    baseline = json.loads(args.baseline.read_text(encoding='utf-8'))
    current = json.loads(args.current.read_text(encoding='utf-8'))
    old_roles, old_options = normalized(baseline)
    new_roles, new_options = normalized(current)
    missing_roles = sorted(old_roles - new_roles)
    missing_options = sorted(old_options - new_options)
    result = {'schema': 'vlc_redesign.native_capability_preservation.v1',
        'baseline_sha256': hashlib.sha256(args.baseline.read_bytes()).hexdigest(),
        'current_sha256': hashlib.sha256(args.current.read_bytes()).hexdigest(),
        'baseline_identity': {key: baseline.get(key) for key in ('version', 'compiler', 'changeset')},
        'current_identity': {key: current.get(key) for key in ('version', 'compiler', 'changeset')},
        'missing_module_roles': missing_roles, 'missing_option_name_type_pairs': missing_options,
        'additional_raw_roles': sorted(new_roles - old_roles),
        'additional_raw_options': sorted(new_options - old_options),
        'baseline_roles_preserved': not missing_roles, 'baseline_option_types_preserved': not missing_options,
        'scope': 'Actual native metadata only. No user values. Does not replace action/dialog reachability, option-editor mapping or persistence verification.',
        'passed': not missing_roles and not missing_options}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, indent=2), flush=True)
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
