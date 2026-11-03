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
    parser.add_argument('--compiler-runtime', required=True, type=Path)
    parser.add_argument('--resume-loader-failure', action='store_true')
    parser.add_argument('--resume-builtin-failure', action='store_true')
    parser.add_argument('--builtin-plugin-receipt', required=True, type=Path)
    args = parser.parse_args()
    build = json.loads(args.receipt.read_text())
    assert build['schema'] == 'vlc_redesign.native_test_build.v1'
    def sha_file(path):
        with path.open('rb') as stream:
            return hashlib.file_digest(stream, 'sha256').hexdigest()
    assert build['native_build_helper_sha256'] == sha_file(Path(__file__).with_name('build-native-tests.py'))
    assert build['platform_header_sha256'] == sha_file(Path(__file__).with_name('native-test-platform.h'))
    assert build['make_fragment_sha256'] == sha_file(Path(__file__).with_name('native-tests.mk'))
    assert build['qt_platform_source_sha256'] == sha_file(Path(__file__).with_name('native-test-qt-platform.cpp'))
    assert build['native_input_state_sha256'] == sha_file(Path('D:/VLC-Redesign/build/windows-x64/toolchain/work/build/win64/native-test-inputs.json'))
    assert build['source_commit'] == json.loads((args.runtime / 'VLC-PLUGIN-BUILDINFO.json').read_text())['source_commit']
    root = args.scratch.resolve()
    assert root.parent.parent == Path('D:/Temp') and root.parent.name.startswith('vlc-s8-')
    assert root.as_posix() == build['windows_layout']
    tools_root = Path('D:/VLC-Redesign/build/windows-x64/toolchain')
    adapter = json.loads(args.builtin_plugin_receipt.read_text())
    assert adapter['source_commit'] == build['source_commit']
    assert adapter['source_sha256'] == sha_file(Path(__file__).with_name('native-test-builtin-plugin.c'))
    assert adapter['builder_sha256'] == sha_file(Path(__file__).with_name('build-native-builtin-plugin.py'))
    assert adapter['plugin_header_sha256'] == sha_file(tools_root / 'work/src/include/vlc_plugin.h')
    adapter_binary = args.receipt.parent / Path(adapter['file']).name
    assert sha_file(adapter_binary) == adapter['sha256']
    compiler_runtime = args.compiler_runtime.resolve(strict=True)
    assert compiler_runtime == tools_root / 'usr/lib/gcc/x86_64-w64-mingw32/14-posix/libssp-0.dll'
    resuming = args.resume_loader_failure or args.resume_builtin_failure
    assert not (args.resume_loader_failure and args.resume_builtin_failure)
    if resuming:
        previous = json.loads((root / 'result.json').read_text())
        assert previous['source_commit'] == build['source_commit'] and not previous['passed']
        assert len(previous['cases']) == 1
        assert previous['cases'][0]['exit_code'] == (0xC0000135 if args.resume_loader_failure else 3)
        failure_name = 'loader-failure' if args.resume_loader_failure else 'builtin-failure'
        if args.resume_loader_failure:
            assert not any((root / 'bin/portable').iterdir())
        else:
            assert 'Assertion failed: resampling > 0' in (root / 'logs/test-test_src_audio_output_dec.exe.stderr').read_text()
        saved = root / ('result-' + failure_name + '.json')
        assert not saved.exists()
        saved.write_bytes((root / 'result.json').read_bytes())
        for log in (root / 'logs').iterdir():
            if not log.name.endswith(('.loader-failure', '.builtin-failure')):
                log.rename(log.with_name(log.name + '.' + failure_name))
    else:
        assert not root.exists()
        root.mkdir()
    source = tools_root / 'work/src'
    for relative in ('test', 'share', 'modules/gui/qt/tests'):
        if not resuming:
            shutil.copytree(source / relative, root / 'source' / relative)
    has_chrome=any(program['name']=='test_player_chrome.exe' for suite in build['suites'] for program in suite['programs'])
    if has_chrome and not resuming:
        relative=Path('modules/gui/qt/player/qml/PlayerChromeState.qml')
        destination=root/'source'/relative
        destination.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(source/relative,destination)
        for name in ('settings-info.svg','search.svg','settings-general-active.svg'):
            relative=Path('modules/gui/qt/pixmaps/redesign')/name
            destination=root/'source'/relative
            destination.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(source/relative,destination)
            assert sha_file(destination)==sha_file(source/relative)
        (root/'icon-evidence').mkdir()
    if not resuming:
        shutil.copytree(args.runtime / 'plugins', root / 'modules')
    for folder in ('bin', 'tmp', 'appdata', 'localappdata', 'logs'):
        (root / folder).mkdir(exist_ok=resuming)
    adapter_target = root / 'modules/native-tests/libnative_test_builtin_plugin.dll'
    assert not adapter_target.exists()
    adapter_target.parent.mkdir()
    shutil.copyfile(adapter_binary, adapter_target)
    assert sha_file(adapter_target) == adapter['sha256']
    # Windows config_GetAppDir checks portable beside the actual test EXE.
    # APPDATA alone does not override SHGetKnownFolderPath for configuration.
    portable = root / 'bin/portable'
    portable.mkdir(exist_ok=resuming)
    runtime_dlls = {}
    for binary in args.runtime.glob('*.dll'):
        target = root / 'bin' / binary.name
        shutil.copyfile(binary, target)
        runtime_dlls[binary.name] = sha_file(binary)
        assert sha_file(target) == runtime_dlls[binary.name]
    shutil.copyfile(compiler_runtime, root / 'bin' / compiler_runtime.name)
    compiler_runtime_hash = sha_file(compiler_runtime)
    assert sha_file(root / 'bin' / compiler_runtime.name) == compiler_runtime_hash
    environment = {key: value for key, value in os.environ.items() if not key.startswith('VLC_PLAYER_DIAGNOSTICS')}
    environment.update(PATH=str(args.runtime.resolve()) + os.pathsep + environment['PATH'],
        VLC_DATA_PATH=str(root / 'source/share'), VLC_USERDATA_PATH=str(portable),
        VLC_PLUGIN_PATH=str(root / 'modules'), VLC_LIB_PATH=str(root / 'modules'),
        APPDATA=str(root / 'appdata'), LOCALAPPDATA=str(root / 'localappdata'),
        TEMP=str(root / 'tmp'), TMP=str(root / 'tmp'), VLC_TEST_TIMEOUT='0',
        QML_DISK_CACHE_PATH=str(root / 'tmp/qml'), QT_DISABLE_SHADER_DISK_CACHE='1',
        QSG_RHI_DISABLE_SHADER_DISK_CACHE='1', QT_FORCE_STDERR_LOGGING='1')
    environment['QT_QPA_PLATFORM'] = 'offscreen'
    if has_chrome:
        chrome=root/'source/modules/gui/qt/player/qml/PlayerChromeState.qml'
        assert chrome.is_file()
        assert sha_file(chrome)==sha_file(tools_root/'work/src/modules/gui/qt/player/qml/PlayerChromeState.qml')
        environment['VLC_TEST_PLAYER_CHROME_QML']=str(chrome)
        environment['VLC_TEST_SETTINGS_SVG_ROOT']=str(root/'source/modules/gui/qt/pixmaps/redesign')
        environment['VLC_TEST_SETTINGS_ICON_EVIDENCE']=str(root/'icon-evidence')
    result = {'schema': 'vlc_redesign.native_suite.v1', 'source_commit': build['source_commit'],
        'native_build_helper_sha256': build['native_build_helper_sha256'],
        'platform_header_sha256': build['platform_header_sha256'],
        'make_fragment_sha256': build['make_fragment_sha256'],
        'qt_platform_source_sha256': build['qt_platform_source_sha256'],
        'native_input_state_sha256': build['native_input_state_sha256'],
        'qt_platform': build['qt_platform'],
        'runtime_dlls_sha256': runtime_dlls,
        'compiler_runtime': {'file': str(compiler_runtime), 'sha256': compiler_runtime_hash},
        'builtin_adapter': adapter,
        'portable_profile_beside_test_executables': str(portable),
        'runner_sha256': sha_file(Path(__file__)),
        'native_timeout_contract': build['native_timeout_contract'],
        'passed': False, 'cases': [], 'scope': build['scope'] + ' Native processes on owned inactive desktops; isolated fixture/data/profile paths; no OS input.'}
    try:
        for suite in build['suites']:
            executables = {}
            for entry in suite['programs']:
                path = tools_root / entry['file'].removeprefix('/')
                with path.open('rb') as stream:
                    assert hashlib.file_digest(stream, 'sha256').hexdigest() == entry['sha256']
                target = root / 'bin' / entry['name']
                if target.exists():
                    assert resuming and sha_file(target) == entry['sha256']
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
