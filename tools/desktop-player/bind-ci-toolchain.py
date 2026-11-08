"""Bind cached native objects to installed package versions, not install dates."""
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess


def retain_brew_metadata(raw, directory):
    """Retain installed recipes/receipts; current API formulae can differ."""
    cellar = Path(subprocess.check_output(['brew', '--cellar'], text=True).strip()).resolve()
    rows = []
    for formula in raw['formulae']:
        for installed in formula['installed']:
            keg = (cellar / formula['name'] / installed['version']).resolve()
            if not keg.is_relative_to(cellar) or not keg.is_dir():
                raise RuntimeError('Installed Homebrew keg is not present: ' + str(keg))
            target = directory / 'installed-metadata' / formula['name'] / installed['version']
            target.mkdir(parents=True, exist_ok=True)
            files = {}
            for relative in ('.brew/' + formula['name'] + '.rb',
                             'INSTALL_RECEIPT.json', 'sbom.spdx.json'):
                source = keg / relative
                if source.is_file():
                    destination = target / Path(relative).name
                    shutil.copy2(source, destination)
                    files[relative] = hashlib.sha256(destination.read_bytes()).hexdigest()
            rows.append({'name': formula['name'], 'version': installed['version'],
                         'keg': str(keg), 'metadata_sha256': files})
    (directory / 'installed-metadata.json').write_text(json.dumps(rows, indent=2) + '\n')


def main():
    directory = Path('.desktop-toolchain')
    if platform.system() == 'Darwin':
        raw = json.loads((directory / 'brew-packages.json').read_text())
        retain_brew_metadata(raw, directory)
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


if __name__ == '__main__':
    main()
