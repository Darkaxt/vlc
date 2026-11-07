"""Focused diagnostics for native package closure and immutable MPV staging."""
import ast
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import uuid
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('native_package', HERE / 'package-native.py')
package = importlib.util.module_from_spec(spec)
spec.loader.exec_module(package)


class NativePackagingTest(unittest.TestCase):
    def test_python_sources_parse(self):
        for path in HERE.glob('*.py'):
            with self.subTest(path=path.name):
                ast.parse(path.read_text(), filename=str(path))

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
