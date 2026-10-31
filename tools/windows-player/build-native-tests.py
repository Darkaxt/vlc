"""Build the new upstream audio/blending/CSD regressions for native Windows."""
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
    args = parser.parse_args()
    assert Path('/proc/self/cgroup').read_text().split('::', 1)[1].strip().startswith('/llm-coordinator/')
    assert args.windows_layout.startswith('D:/Temp/vlc-s8-') and ' ' not in args.windows_layout
    assert '"' not in args.windows_layout and '..' not in args.windows_layout
    windows_source = args.windows_layout + '/source'
    flags = ' '.join('-D' + key + '=\\"' + value + '\\"' for key, value in (
        ('SRCDIR', windows_source + '/test'), ('TOP_SRCDIR', windows_source),
        ('TOP_BUILDDIR', args.windows_layout)))
    suites = []
    selection = {'test': ['test_src_audio_output_dec.exe', 'test_modules_video_filter_blend.exe'],
        'modules/gui/qt': ['test_qt_csd_button_model.exe']}
    for relative in ('test', 'modules/gui/qt'):
        directory = args.build / relative
        names = subprocess.check_output(['make', '-s', '--no-print-directory', '-C', str(directory),
            '-f', 'Makefile', '-f', str(args.make_fragment), 'native-test-programs'], text=True).splitlines()
        assert names and len(names) == len(set(names)) and all(name.endswith('.exe') for name in names)
        configured_programs = names
        names = selection[relative]
        assert set(names) <= set(configured_programs)
        cases = names
        # No test process is run under Linux. Override only test-path macros;
        # library/plugin code continues to use the actual merged configuration.
        command = ['make', '-C', str(directory), '-j1', *names,
            'PLAYER_DIAGNOSTICS_CPPFLAGS=-DVLC_PLAYER_DIAGNOSTICS', 'PLAYER_MPV_CPPFLAGS=-DVLC_MPV_RUNTIME_IDENTITY']
        if relative == 'test':
            command.append('AM_CPPFLAGS=' + flags)
        else:
            command.append('QT_QTEST_COMMON_cppflags=$(libqt_plugin_la_CPPFLAGS) -I$(builddir)/tests '
                '-DTOP_BUILDDIR=\\"' + args.windows_layout + '\\"')
        subprocess.run(command, check=True)
        records = []
        for name in names:
            binary = directory / '.libs' / name
            if not binary.exists():
                binary = directory / name
            assert binary.is_file(), binary
            with binary.open('rb') as stream:
                digest = hashlib.file_digest(stream, 'sha256').hexdigest()
            records.append({'name': name, 'file': str(binary), 'sha256': digest})
        if relative == 'test':
            subprocess.run(['/bin/sh', str(args.source / 'test/check_POTFILES.sh')], check=True)
        suites.append({'directory': relative, 'programs': records, 'cases': cases,
            'configured_programs': configured_programs,
            'linux_script_checks': ['check_POTFILES.sh'] if relative == 'test' else []})
    receipt = {'schema': 'vlc_redesign.native_test_build.v1',
        'source_commit': subprocess.check_output(['git', '-C', str(args.source), 'rev-parse', 'HEAD'], text=True).strip(),
        'windows_layout': args.windows_layout, 'suites': suites,
        'scope': 'Focused regressions added by this upstream merge. The fork full Windows acceptance matrix owns broad product regression. The complete upstream C suite includes POSIX /tmp assumptions and is not claimed as a native Windows suite.',
        'execution': 'Not run; execute these exact binaries natively on owned inactive Windows desktops'}
    args.receipt.write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({'native_test_build_receipt': str(args.receipt), 'suites': len(suites)}), flush=True)


if __name__ == '__main__':
    main()
