"""Build the selected affected regressions for native Windows execution."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=Path('/work/src'))
    parser.add_argument('--build', type=Path, default=Path('/work/build/win64'))
    parser.add_argument('--make-fragment', required=True, type=Path)
    parser.add_argument('--windows-layout', required=True)
    parser.add_argument('--receipt', required=True, type=Path)
    parser.add_argument('--platform-header', required=True, type=Path)
    parser.add_argument('--qt-platform-source', required=True, type=Path)
    parser.add_argument('--scope',choices=['upstream','settings'],default='upstream')
    args = parser.parse_args()
    assert args.platform_header.is_file()
    assert args.qt_platform_source.is_file()
    assert Path('/proc/self/cgroup').read_text().split('::', 1)[1].strip().startswith('/llm-coordinator/')
    assert args.windows_layout.startswith('D:/Temp/vlc-s8-') and ' ' not in args.windows_layout
    assert '"' not in args.windows_layout and '..' not in args.windows_layout
    windows_source = args.windows_layout + '/source'
    flags = ' '.join('-D' + key + '=\\"' + value + '\\"' for key, value in (
        ('SRCDIR', windows_source + '/test'), ('TOP_SRCDIR', windows_source),
        ('TOP_BUILDDIR', args.windows_layout)))
    suites = []
    failures = []
    selection = {'test': ['test_src_audio_output_dec.exe', 'test_modules_video_filter_blend.exe'],
        'modules/gui/qt': ['test_qt_csd_button_model.exe']}
    if args.scope=='settings':
        selection={'test':['test_src_misc_history.exe','test_src_misc_saved_options.exe'],
            'modules/gui/qt':['test_player_chrome.exe']}
    input_state = args.build / 'native-test-inputs.json'
    inputs = {'windows_layout': args.windows_layout, 'scope':args.scope, 'build_helper_sha256': sha_file(Path(__file__)),
        'platform_header_sha256': sha_file(args.platform_header),
        'make_fragment_sha256': sha_file(args.make_fragment),
        'qt_platform_source_sha256': sha_file(args.qt_platform_source),
        'makefiles': {name: sha_file(args.build / name / 'Makefile') for name in selection}}
    # Make does not track compiler arguments. Bind the exact path macros and
    # native-only recipe to the selected test objects, preserving unchanged ones.
    inputs_changed = not input_state.exists() or json.loads(input_state.read_text()) != inputs
    if inputs_changed:
        pending = input_state.with_suffix('.pending')
        pending.write_text(json.dumps(inputs, indent=2) + '\n')
        pending.replace(input_state)
    for relative in ('test', 'modules/gui/qt'):
        directory = args.build / relative
        listing = subprocess.check_output(['make', '-s', '--no-print-directory', '-C', str(directory),
            '-f', 'Makefile', '-f', str(args.make_fragment), 'native-test-programs'], text=True)
        args.receipt.with_name('native-programs-' + relative.replace('/', '-') + '.log').write_text(listing)
        names = [line.removeprefix('NATIVE-TEST\t') for line in listing.splitlines() if line.startswith('NATIVE-TEST\t')]
        assert names and len(names) == len(set(names)) and all(name.endswith('.exe') for name in names)
        configured_programs = names
        names = selection[relative]
        assert set(names) <= set(configured_programs)
        cases = names
        # No test process is run under Linux. Override only test-path macros;
        # library/plugin code continues to use the actual merged configuration.
        # Collect independent errors in these three selected regression builds;
        # any failure still rejects the whole native-unit build receipt.
        command = ['make', '-C', str(directory), '-j1', '-k', '-f', 'Makefile', '-f', str(args.make_fragment), *names,
            'NATIVE_TEST_INPUT_STATE=' + str(input_state),
            'PLAYER_DIAGNOSTICS_CPPFLAGS=-DVLC_PLAYER_DIAGNOSTICS', 'PLAYER_MPV_CPPFLAGS=-DVLC_MPV_RUNTIME_IDENTITY']
        if inputs_changed:
            # Force the exact dependency edge even on coarse timestamp filesystems.
            command += ['-W', str(input_state)]
        if relative == 'test':
            command.append('AM_CPPFLAGS=' + flags + ' -include ' + str(args.platform_header))
        else:
            offscreen = Path('/work/build/contrib/x86_64-w64-mingw32/plugins/platforms/libqoffscreen.a')
            assert offscreen.is_file()
            command += ['NATIVE_QT_PLATFORM_SOURCE=' + str(args.qt_platform_source),
                'NATIVE_QT_OFFSCREEN_ARCHIVE=' + str(offscreen)]
            command.append('QT_QTEST_COMMON_cppflags=$(libqt_plugin_la_CPPFLAGS) -I$(builddir)/tests '
                '-DTOP_BUILDDIR=\\"' + args.windows_layout + '\\"')
        build_log=args.receipt.with_name('native-build-'+relative.replace('/','-')+'.log')
        print('NATIVE BUILD '+relative+' | log='+str(build_log),flush=True)
        with build_log.open('w') as log:
            code=subprocess.call(command,stdout=log,stderr=subprocess.STDOUT)
        print('NATIVE BUILD '+relative+' | exit='+str(code)+' | log='+str(build_log),flush=True)
        if relative == 'test':
            with args.receipt.with_name('native-potfiles.log').open('w') as log:
                script_code = subprocess.call(['/bin/sh', str(args.source / 'test/check_POTFILES.sh')],
                    stdout=log, stderr=subprocess.STDOUT)
            if script_code:
                failures.append({'check': 'check_POTFILES.sh', 'exit_code': script_code})
        if code:
            failures.append({'directory': relative, 'targets': names, 'exit_code': code,'log':str(build_log)})
            continue
        records = []
        for name in names:
            binary = directory / '.libs' / name
            if not binary.exists():
                binary = directory / name
            assert binary.is_file(), binary
            with binary.open('rb') as stream:
                digest = hashlib.file_digest(stream, 'sha256').hexdigest()
            records.append({'name': name, 'file': str(binary), 'sha256': digest})
        suites.append({'directory': relative, 'programs': records, 'cases': cases,'build_log':str(build_log),
            'configured_programs': configured_programs,
            'linux_script_checks': ['check_POTFILES.sh'] if relative == 'test' else []})
    assert not failures, failures
    receipt = {'schema': 'vlc_redesign.native_test_build.v1',
        'source_commit': subprocess.check_output(['git', '-C', str(args.source), 'rev-parse', 'HEAD'], text=True).strip(),
        'windows_layout': args.windows_layout, 'suites': suites,
        'native_build_helper_sha256': sha_file(Path(__file__)),
        'platform_header_sha256': sha_file(args.platform_header),
        'make_fragment_sha256': sha_file(args.make_fragment),
        'qt_platform_source_sha256': sha_file(args.qt_platform_source),
        'native_input_state_sha256': sha_file(input_state),
        'qt_platform': 'Existing static SDK offscreen integration, explicitly imported for native CSD and chrome/SVG tests; no windows or OS input',
        'native_timeout_contract': 'VLC_TEST_TIMEOUT=0 required; any POSIX alarm request exits with failure instead of being ignored',
        'scope': ('M4 history exclusions, saved-option parser, real chrome state machine and original SVG icons at requested size/DPR. The complete native settings/player acceptance owns integrated behavior and pixels.' if args.scope=='settings' else
            'Focused regressions added by this upstream merge. The fork full Windows acceptance matrix owns broad product regression. The complete upstream C suite includes POSIX /tmp assumptions and is not claimed as a native Windows suite.'),
        'execution': 'Not run; execute these exact binaries natively on owned inactive Windows desktops'}
    args.receipt.write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({'native_test_build_receipt': str(args.receipt), 'suites': len(suites)}), flush=True)


def sha_file(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


if __name__ == '__main__':
    main()
