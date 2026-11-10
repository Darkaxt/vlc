"""Select native runner rows without GitHub matrix.include adding extra jobs."""
import json
import os
import re

TARGETS = {
    'macos-arm64': 'macos-15',
    'macos-intel': 'macos-15-intel',
    'linux-x86_64': 'ubuntu-24.04',
    'linux-aarch64': 'ubuntu-24.04-arm',
}

selected = os.environ['TARGET']
if os.environ.get('RESUME_PACKAGES') == 'true':
    if selected not in ('linux-x86_64', 'linux-aarch64'):
        raise RuntimeError('Choose one exact Linux target for package continuation')
    for key in ('BUILT_SOURCE', 'SOURCE_SEED_COMMIT'):
        if not re.fullmatch('[0-9a-f]{40}', os.environ.get(key, '')):
            raise RuntimeError('Package continuation requires exact source revisions')
    if not re.fullmatch('[1-9][0-9]*', os.environ.get('SOURCE_SEED_ARTIFACT', '')):
        raise RuntimeError('Package continuation requires the exact source artifact ID')
names = list(TARGETS) if selected == 'all' else [selected]
rows = [{'target': name, 'runner': TARGETS[name]} for name in names]
with open(os.environ['GITHUB_OUTPUT'], 'a', encoding='utf-8') as stream:
    stream.write('targets=' + json.dumps(rows, separators=(',', ':')) + '\n')
