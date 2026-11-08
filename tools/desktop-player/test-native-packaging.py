"""Focused diagnostics for native package closure and immutable MPV staging."""
import ast
import importlib.util
import json
import os
import stat
from pathlib import Path
import subprocess
import sys
import uuid
import unittest
from unittest.mock import MagicMock, patch

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('native_package', HERE / 'package-native.py')
package = importlib.util.module_from_spec(spec)
spec.loader.exec_module(package)


class NativePackagingTest(unittest.TestCase):
    def test_qml_deployment_uses_requested_module_graph_not_neighbor_modules(self):
        root = Path(sys.argv_scratch) / ('qml-graph-' + uuid.uuid4().hex)
        installed = root / 'installed/QtQuick'
        (installed / 'Controls/Basic').mkdir(parents=True)
        (installed / 'Scene3D').mkdir()
        (installed / 'assets').mkdir()
        for relative in ('qmldir', 'Controls/qmldir', 'Controls/Basic/qmldir',
                         'Scene3D/qmldir', 'assets/required.png'):
            (installed / relative).write_text(relative)
        graph = [{'type': 'module', 'name': name, 'path': str(path)} for name, path in
                 [('QtQuick', installed), ('QtQuick.Controls', installed / 'Controls'),
                  ('QtQuick.Controls.Basic', installed / 'Controls/Basic')]]
        destination = root / 'staged'
        rows = package.stage_qml_modules(graph, destination)
        self.assertTrue((destination / 'QtQuick/assets/required.png').is_file())
        self.assertTrue((destination / 'QtQuick/Controls/Basic/qmldir').is_file())
        self.assertFalse((destination / 'QtQuick/Scene3D').exists())
        self.assertEqual({row['name'] for row in rows}, {row['name'] for row in graph})
        self.assertTrue((installed / 'Scene3D/qmldir').is_file())

    def test_python_sources_parse(self):
        for path in HERE.glob('*.py'):
            with self.subTest(path=path.name):
                ast.parse(path.read_text(), filename=str(path))

    def test_staged_qml_rebases_source_runpath_without_mutating_sdk(self):
        root = Path(sys.argv_scratch) / ('qml-runpath-' + uuid.uuid4().hex)
        installed = root / 'sdk/qml/QtQuick'; installed.mkdir(parents=True)
        plugin = installed / 'libquickplugin.dylib'
        plugin.write_bytes(b'\xcf\xfa\xed\xfe' + b'source plugin')
        plugin.chmod(stat.S_IREAD)
        destination = root / 'staged'
        commands = []

        def record(*args):
            commands.append(args)
            self.assertTrue(args[-1].stat().st_mode & stat.S_IWUSR)

        with patch.object(package, 'MAC', True), patch.object(package, 'output',
                return_value='Load command 1\n cmd LC_RPATH\n cmdsize 64\n path @loader_path/../../lib (offset 12)'), \
                patch.object(package, 'run', side_effect=record):
            package.stage_qml_modules([{'type': 'module', 'name': 'QtQuick', 'path': str(installed)}], destination)
        self.assertEqual(commands, [('install_name_tool', '-rpath', '@loader_path/../../lib',
            str(installed / '../../lib'), destination / 'QtQuick/libquickplugin.dylib')])
        self.assertEqual(plugin.read_bytes(), b'\xcf\xfa\xed\xfe' + b'source plugin')
        self.assertFalse(plugin.stat().st_mode & stat.S_IWUSR)

    def test_native_ncurses_link_uses_consumer_sdk_and_preserves_libraries(self):
        spec = importlib.util.spec_from_file_location('native_build', HERE / 'build-native.py')
        build_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(build_module)
        work = MagicMock()
        original = '-L/pinned/lib -lncursesw -isysroot /producer/MacOSX26.2.sdk -lm'
        placebo = '-L/pinned/lib -lplacebo -lSPIRV -lMachineIndependent'
        with patch.object(build_module.platform, 'system', return_value='Darwin'), \
                patch.object(build_module.subprocess, 'check_output', side_effect=[original, placebo]), \
                patch.object(build_module, 'output', return_value='/selected SDK/MacOSX.sdk'):
            flags = build_module.native_make_flags(work, {})
        self.assertEqual(flags[0], 'PLAYER_MPV_CPPFLAGS=-DVLC_MPV_RUNTIME_IDENTITY')
        self.assertEqual(build_module.shlex.split(flags[1].removeprefix('NCURSES_LIBS=')),
            ['-L/pinned/lib', '-lncursesw', '-isysroot', '/selected SDK/MacOSX.sdk', '-lm'])
        record = json.loads((work / 'native-link-bindings.json').write_text.call_args.args[0])
        self.assertEqual(record['ncurses_pkgconfig_libs'], original)
        self.assertEqual(build_module.shlex.split(flags[2].removeprefix('LIBPLACEBO_LIBS=')),
            ['-L/pinned/lib', '-lplacebo', '-lSPIRV', '-lMachineIndependent', '-lc++'])

    def test_bootstrap_cache_restores_generated_bytes_and_exact_mtime(self):
        spec = importlib.util.spec_from_file_location('native_build', HERE / 'build-native.py')
        build_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(build_module)
        work = Path(sys.argv_scratch) / ('bootstrap-cache-' + uuid.uuid4().hex)
        original = work / 'original'; restored = work / 'restored'
        original.mkdir(parents=True); restored.mkdir()
        for root in (original, restored):
            for directory in ('autotools', 'm4', 'po'):
                (root / directory).mkdir()
        generated = original / 'configure'
        generated.write_bytes(b'generated configure')
        os.utime(generated, ns=(1670000000123456700, 1670000000123456700))
        expected_time = generated.stat().st_mtime_ns
        protected = restored / 'Makefile.am'; protected.write_bytes(b'current tracked source')
        tracked = {'Makefile.am'}
        with patch.object(build_module, 'ROOT', original):
            build_module.retain_bootstrap_sources(work, tracked)
        with patch.object(build_module, 'ROOT', restored), \
                patch.object(build_module, 'output', return_value='Makefile.am'), \
                patch.object(build_module, 'run') as invoked:
            build_module.prepare_bootstrap_sources(work, work / 'build', {}, {})
            invoked.assert_not_called()
        self.assertEqual((restored / 'configure').read_bytes(), generated.read_bytes())
        self.assertEqual((restored / 'configure').stat().st_mtime_ns, expected_time)
        self.assertEqual(protected.read_bytes(), b'current tracked source')

    def test_os_driver_and_c_runtime_stay_external(self):
        with patch.object(package, 'MAC', False):
            for path in ('/lib/libc.so.6', '/lib/libm.so.6', '/lib/libGLX_mesa.so.0', '/lib/libEGL.so.1'):
                self.assertTrue(package.external(path), path)
            for path in ('/lib/libavcodec.so.60', '/lib/libass.so.9', '/lib/libcairo.so.2'):
                self.assertFalse(package.external(path), path)
        with patch.object(package, 'MAC', True):
            self.assertTrue(package.external('/System/Library/Frameworks/Cocoa.framework/Cocoa'))
            self.assertFalse(package.external('/opt/homebrew/lib/libavcodec.62.dylib'))

    def test_macos_loader_uses_declared_runpaths(self):
        origin = Path('/opt/homebrew/Cellar/brotli/1.2.1/lib/libbrotlidec.dylib')
        expected = origin.parent / 'libbrotlicommon.1.dylib'
        with patch.object(Path, 'is_file', lambda path: path == expected):
            self.assertEqual(package.resolve_mac_dependency('@rpath/libbrotlicommon.1.dylib',
                origin, [str(origin.parent)]), expected)
            with self.assertRaisesRegex(RuntimeError, 'Unresolved LC_RPATH'):
                package.resolve_mac_dependency('@rpath/libbrotlicommon.1.dylib', origin, ['/unrelated'])

    def test_macos_minimum_uses_deployment_target_not_sdk(self):
        self.assertEqual(package.mac_minimum_system('''Load command 4
      cmd LC_BUILD_VERSION
  cmdsize 32
 platform 1
    minos 15.0
      sdk 26.0
'''), (15, 0))
        self.assertEqual(package.mac_minimum_system('''Load command 6
      cmd LC_VERSION_MIN_MACOSX
  cmdsize 16
  version 13.3
      sdk 15.0
'''), (13, 3))

    def test_ci_selection_does_not_add_unrequested_architectures(self):
        scratch = Path(sys.argv_scratch)
        for target, count in [('macos-arm64', 1), ('all', 4)]:
            result = scratch / ('ci-matrix-' + uuid.uuid4().hex + '.txt')
            env = dict(os.environ, TARGET=target, GITHUB_OUTPUT=str(result))
            subprocess.run([sys.executable, HERE / 'select-ci-targets.py'], env=env, check=True)
            rows = json.loads(result.read_text().split('=', 1)[1])
            self.assertEqual(len(rows), count)
            if target != 'all':
                self.assertEqual(rows, [{'target': 'macos-arm64', 'runner': 'macos-15'}])

    def test_resume_partial_closure_with_read_only_homebrew_library(self):
        work = Path(sys.argv_scratch) / ('readonly-closure-' + uuid.uuid4().hex)
        source = work / 'source/libass.9.dylib'
        target = work / 'runtime/libass.9.dylib'
        source.parent.mkdir(parents=True)
        target.parent.mkdir(parents=True)
        source.write_bytes(b'current library')
        target.write_bytes(b'partial earlier staging')
        target.chmod(stat.S_IREAD)
        with patch.object(package, 'MAC', True), patch.object(package, 'dependencies', return_value=[]), \
                patch.object(package, 'mac_runpaths', return_value=[]), patch.object(package, 'run'):
            rows = package.copy_closure([source], target.parent)
        self.assertEqual(target.read_bytes(), source.read_bytes())
        self.assertEqual(rows[0]['sha256'], package.sha(source))

    def test_modified_runtime_is_rejected_before_header_write(self):
        # No native executable is run. Model a retained runtime whose bytes no
        # longer match its receipt; this must fail instead of accepting a
        # mutable manifest as trust or silently generating new trusted hashes.
        scratch = Path(sys.argv_scratch)
        work = scratch / ('runtime-rejection-' + uuid.uuid4().hex)
        prefix = work / 'deps/lib'; prefix.mkdir(parents=True)
        runtime = work / 'mpv-runtime'; runtime.mkdir()
        library = prefix / 'libmpv.so.2'; library.write_bytes(b'original native output')
        (runtime / library.name).write_bytes(b'altered')
        (runtime / 'runtime.json').write_text(json.dumps([{
            'name': library.name, 'source_sha256': package.sha(library), 'sha256': '0' * 64}]))
        with patch.object(package, 'MAC', False):
            with self.assertRaisesRegex(RuntimeError, 'payload was changed'):
                package.stage_mpv(work, work / 'deps')
        self.assertFalse((work / 'vlc-build/modules/gui/qt/mpv_runtime_identity.hpp').exists())
        # The owning task retires this attributed fixture through transactional
        # cleanup after the test process exits; no recursive ad-hoc deletion.


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--scratch', required=True, type=Path)
    args = parser.parse_args()
    args.scratch.mkdir(parents=True, exist_ok=True)
    sys.argv_scratch = str(args.scratch)
    unittest.main(argv=[sys.argv[0]])
