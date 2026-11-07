"""Bind cached native objects to installed package versions, not install dates."""
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess

directory = Path('.desktop-toolchain')
if platform.system() == 'Darwin':
    raw = json.loads((directory / 'brew-packages.json').read_text())
    packages = sorted((formula['full_name'], installed['version'], installed.get('built_as_bottle'))
                      for formula in raw['formulae'] for installed in formula['installed'])
else:
    packages = sorted((directory / 'dpkg-packages.tsv').read_text().splitlines())
binding = {'platform': platform.system(), 'arch': platform.machine(), 'packages': packages,
           'compiler': subprocess.check_output(['cc', '--version'], text=True).splitlines()[0]}
payload = json.dumps(binding, sort_keys=True, separators=(',', ':')).encode()
(directory / 'binding.json').write_bytes(payload)
with open(os.environ['GITHUB_OUTPUT'], 'a', encoding='utf-8') as stream:
    stream.write('sha256=' + hashlib.sha256(payload).hexdigest() + '\n')
