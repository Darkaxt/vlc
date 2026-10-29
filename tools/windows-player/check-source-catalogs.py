"""Prove that catalog reconciliation preserves a real changed translation."""
import argparse
import json
from pathlib import Path
import re
import subprocess
import sys

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--source', required=True, type=Path)
parser.add_argument('--scratch', required=True, type=Path)
args = parser.parse_args()
source = args.source.resolve()
assert source == Path('/work/src') and args.scratch.is_relative_to(Path('/scratch'))
assert not subprocess.check_output(['git', '-C', str(source), 'diff', '--name-only']).strip()
path = source / 'po/el.po'
original = path.read_bytes()
modified, count = re.subn(rb'(msgid "Cancel"\r?\nmsgstr )"[^"\n]*"',
    rb'\1"S7 changed-translation negative control"', original)
assert count == 1 and modified != original
args.scratch.mkdir(parents=True, exist_ok=False)
try:
    path.write_bytes(modified)
    completed = subprocess.run([sys.executable, '-B', str(Path(__file__).with_name('reconcile-source-catalogs.py')),
        '--source', str(source), '--commit', 'HEAD', '--restore-equivalent-generated',
        '--output', str(args.scratch / 'refusal.json')], capture_output=True)
    (args.scratch / 'stdout').write_bytes(completed.stdout)
    (args.scratch / 'stderr').write_bytes(completed.stderr)
    refusal = json.loads((args.scratch / 'refusal.json').read_text())
    assert completed.returncode != 0 and not refusal['restored']
    assert refusal['changed_message_count'] == 1 and path.read_bytes() == modified
finally:
    path.write_bytes(original)
assert not subprocess.check_output(['git', '-C', str(source), 'diff', '--name-only']).strip()
result = {'changed_translation_rejected': True, 'changed_source_preserved_by_helper': True,
    'test_fixture_restored': True, 'passed': True}
(args.scratch / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result))
