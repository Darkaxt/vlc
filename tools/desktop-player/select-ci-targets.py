"""Select native runner rows without GitHub matrix.include adding extra jobs."""
import json
import os

TARGETS = {
    'macos-arm64': 'macos-15',
    'macos-intel': 'macos-15-intel',
    'linux-x86_64': 'ubuntu-24.04',
    'linux-aarch64': 'ubuntu-24.04-arm',
}

selected = os.environ['TARGET']
names = list(TARGETS) if selected == 'all' else [selected]
rows = [{'target': name, 'runner': TARGETS[name]} for name in names]
with open(os.environ['GITHUB_OUTPUT'], 'a', encoding='utf-8') as stream:
    stream.write('targets=' + json.dumps(rows, separators=(',', ':')) + '\n')
