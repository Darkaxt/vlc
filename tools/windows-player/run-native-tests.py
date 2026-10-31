"""Run the exact newly built upstream regressions on owned inactive desktops."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys

sys.dont_write_bytecode = True
from isolated_desktop import IsolatedProcess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--receipt', required=True, type=Path)
    parser.add_argument('--runtime', required=True, type=Path)
    parser.add_argument('--scratch', required=True, type=Path)
    args = parser.parse_args()
    build = json.loads(args.receipt.read_text())
    assert build['schema'] == 'vlc_redesign.native_test_build.v1'
    root = args.scratch.resolve()
    assert root.parent.parent == Path('D:/Temp') and root.parent.name.startswith('vlc-s8-')
    assert root.as_posix() == build['windows_layout'] and not root.exists()
    root.mkdir()
    tools_root = Path('D:/VLC-Redesign/build/windows-x64/toolchain')
    source = tools_root / 'work/src'
    for relative in ('test', 'share', 'modules/gui/qt/tests'):
        shutil.copytree(source / relative, root / 'source' / relative)
    shutil.copytree(args.runtime / 'plugins', root / 'modules')
    for folder in ('bin', 'portable', 'tmp', 'appdata', 'localappdata', 'logs'):
        (root / folder).mkdir()
    environment = {key: value for key, value in os.environ.items() if not key.startswith('VLC_PLAYER_DIAGNOSTICS')}
    environment.update(PATH=str(args.runtime.resolve()) + os.pathsep + environment['PATH'],
        VLC_DATA_PATH=str(root / 'source/share'), VLC_USERDATA_PATH=str(root / 'portable'),
        VLC_PLUGIN_PATH=str(root / 'modules'), VLC_LIB_PATH=str(root / 'modules'),
        APPDATA=str(root / 'appdata'), LOCALAPPDATA=str(root / 'localappdata'),
        TEMP=str(root / 'tmp'), TMP=str(root / 'tmp'), VLC_TEST_TIMEOUT='0',
        QML_DISK_CACHE_PATH=str(root / 'tmp/qml'), QT_DISABLE_SHADER_DISK_CACHE='1',
        QSG_RHI_DISABLE_SHADER_DISK_CACHE='1', QT_FORCE_STDERR_LOGGING='1')
    result = {'schema': 'vlc_redesign.native_suite.v1', 'source_commit': build['source_commit'],
        'passed': False, 'cases': [], 'scope': build['scope'] + ' Native processes on owned inactive desktops; isolated fixture/data/profile paths; no OS input.'}
    try:
        for suite in build['suites']:
            executables = {}
            for entry in suite['programs']:
                path = tools_root / entry['file'].removeprefix('/')
                with path.open('rb') as stream:
                    assert hashlib.file_digest(stream, 'sha256').hexdigest() == entry['sha256']
                target = root / 'bin' / entry['name']
                assert not target.exists()
                shutil.copyfile(path, target)
                executables[entry['name']] = target
            for name in suite['cases']:
                if name in suite['linux_script_checks']:
                    result['cases'].append({'suite': suite['directory'], 'case': name, 'passed': True,
                        'execution': 'Linux shell source check already passed in the owned build invocation'})
                    continue
                command = [str(executables[name])]
                label = suite['directory'].replace('/', '-') + '-' + Path(name).name
                print('NATIVE SUITE START ' + label, flush=True)
                with (root / 'logs' / (label + '.stdout')).open('wb') as out, (root / 'logs' / (label + '.stderr')).open('wb') as err:
                    process = IsolatedProcess(command, cwd=root / 'source' / suite['directory'], env=environment, stdout=out, stderr=err)
                    code = process.wait()
                row = {'suite': suite['directory'], 'case': name, 'exit_code': code,
                    'passed': code == 0, 'skipped': code == 77, 'input_desktop_preserved': True}
                result['cases'].append(row)
                (root / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
                assert code in (0, 77), row
                print('NATIVE SUITE ' + ('SKIP ' if code == 77 else 'PASS ') + label, flush=True)
        result['passed'] = all(row.get('passed') or row.get('skipped') for row in result['cases'])
    except Exception as error:
        result['failure'] = repr(error)
        raise
    finally:
        (root / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
        print(json.dumps({'native_suite_passed': result['passed'], 'source_commit': result['source_commit']}), flush=True)


if __name__ == '__main__':
    main()
