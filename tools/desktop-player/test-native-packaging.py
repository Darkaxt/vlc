"""Focused diagnostics for native package closure and immutable MPV staging."""
import ast
import importlib.util
import json
import io
import os
import stat
from pathlib import Path
import subprocess
import sys
import uuid
import tarfile
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('native_package', HERE / 'package-native.py')
package = importlib.util.module_from_spec(spec)
spec.loader.exec_module(package)


class NativePackagingTest(unittest.TestCase):
    def test_framework_source_coalesces_meta_formula_aliases_but_rejects_distinct_sources(self):
        spec = importlib.util.spec_from_file_location('native_sources', HERE / 'collect-native-sources.py')
        sources = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(sources)
        framework = Path('QtVirtualKeyboardQml.framework')
        installed = [{'keg': '/opt/homebrew/Cellar/qt/6.12.0'},
                     {'keg': '/opt/homebrew/Cellar/qtvirtualkeyboard/6.12.0_1'}]
        candidates = [Path(row['keg']) / 'lib' / framework / 'Versions/A' / framework.stem
                      for row in installed]
        aliases = dict.fromkeys(candidates, candidates[1])
        with patch.object(Path, 'is_file', lambda path: path in aliases), \
                patch.object(Path, 'resolve', lambda path, strict=False: aliases[path]):
            self.assertEqual(sources.framework_source(framework, installed), candidates[1])
            aliases[candidates[0]] = candidates[0]
            with self.assertRaisesRegex(RuntimeError, 'no unique installed source'):
                sources.framework_source(framework, installed)
            aliases.clear()
            with self.assertRaisesRegex(RuntimeError, 'no unique installed source'):
                sources.framework_source(framework, installed)

    def test_installed_source_graph_uses_original_resources_and_rejects_unpinned_git(self):
        spec = importlib.util.spec_from_file_location('native_sources', HERE / 'collect-native-sources.py')
        sources = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(sources)
        def row(identifier, url, digest):
            return {'SPDXID': identifier, 'downloadLocation': url,
                    'checksums': [{'algorithm': 'SHA256', 'checksumValue': digest}]}
        sbom = {'packages': [row('SPDXRef-Archive-example-src', 'https://example.org/source.tar.xz', 'a' * 64),
            row('SPDXRef-Patch-example-0', 'https://example.org/fix.patch', 'b' * 64),
            row('SPDXRef-Package-SPDXRef-dependency', 'https://example.org/bottle.tar.gz', 'c' * 64)]}
        result = sources.brew_sources(sbom, 'example', '')
        self.assertEqual([item['sha256'] for item in result], ['a' * 64, 'b' * 64])
        encoded = {'packages': [row('SPDXRef-Archive-example.40.2-src',
            'https://example.org/source.tar.xz', 'e' * 64)]}
        self.assertEqual(sources.brew_sources(encoded, 'example@2', '')[0]['sha256'], 'e' * 64)
        git = {'packages': [row('SPDXRef-Archive-x264-src', 'https://example.org/x264.git', '')]}
        with self.assertRaisesRegex(RuntimeError, 'exact installed Git revision'):
            sources.brew_sources(git, 'x264', 'url "https://example.org/x264.git"')
        result = sources.brew_sources(git, 'x264',
            'url "https://example.org/x264.git", revision: "' + 'd' * 40 + '"')
        self.assertEqual(result[0]['git_revision'], 'd' * 40)
        self.assertNotIn('sha256', result[0])

    def test_source_notice_extraction_is_safe_and_resumable(self):
        spec = importlib.util.spec_from_file_location('native_sources', HERE / 'collect-native-sources.py')
        sources = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(sources)
        root = Path(sys.argv_scratch) / ('notices-' + uuid.uuid4().hex)
        root.mkdir()
        archive = root / 'source.tar.gz'
        with tarfile.open(archive, 'w:gz') as bundle:
            for name, data in [('project/COPYING', b'license'), ('project/PATENTS', b'patent grant'),
                               ('project/src/code.c', b'not a notice')]:
                item = tarfile.TarInfo(name); item.size = len(data)
                bundle.addfile(item, io.BytesIO(data))
        target = root / 'notices'
        first = sources.retain_archive_notices(archive, target)
        self.assertEqual(first, sources.retain_archive_notices(archive, target))
        self.assertEqual([row['file'] for row in first], ['project/COPYING', 'project/PATENTS'])
        (target / 'project/COPYING').write_bytes(b'changed')
        with self.assertRaisesRegex(RuntimeError, 'Retained notice changed'):
            sources.retain_archive_notices(archive, target)
        with tarfile.open(root / 'unsafe.tar', 'w') as bundle:
            item = tarfile.TarInfo('../COPYING'); item.size = 1
            bundle.addfile(item, io.BytesIO(b'x'))
        with self.assertRaisesRegex(RuntimeError, 'Unsafe archive notice path'):
            sources.retain_archive_notices(root / 'unsafe.tar', root / 'unsafe')

    def test_cancelled_command_waits_for_native_descendants_and_closes_kqueue(self):
        spec = importlib.util.spec_from_file_location('native_build', HERE / 'build-native.py')
        build = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(build)
        # kqueue exposes close(), not a context-manager protocol. Its exit
        # event must be consumed before the build may return to cache retention.
        queue = SimpleNamespace(control=MagicMock(side_effect=[[], [SimpleNamespace(ident=22)]]),
                                close=MagicMock())
        process = SimpleNamespace(pid=11, wait=MagicMock())
        with patch.object(build.os, 'killpg', create=True) as kill, \
                patch.object(build.signal, 'SIGKILL', 9, create=True), \
                patch.object(build, 'output', return_value='22 11 R\n'), \
                patch.object(build.platform, 'system', return_value='Darwin'), \
                patch.object(build.select, 'kqueue', return_value=queue, create=True), \
                patch.object(build.select, 'kevent', create=True), \
                patch.multiple(build.select, KQ_FILTER_PROC=-5, KQ_EV_ADD=1,
                               KQ_EV_ONESHOT=16, KQ_NOTE_EXIT=0x80000000, create=True), \
                patch('builtins.print'):
            build.stop_command(process)
        kill.assert_called_once_with(11, 9)
        process.wait.assert_called_once()
        self.assertEqual(queue.control.call_count, 2)
        queue.close.assert_called_once()

    def test_linux_installable_payload_has_real_desktop_entry_points(self):
        root = Path(sys.argv_scratch) / ('linux-system-' + uuid.uuid4().hex)
        app = root / 'portable'
        app.mkdir(parents=True)
        (app / 'modern-vlc').write_text('#!/bin/sh\n')
        desktop = '[Desktop Entry]\nExec=modern-vlc %U\nIcon=modern-vlc\n'
        (app / 'modern-vlc.desktop').write_text(desktop)
        (app / 'modern-vlc.png').write_bytes(b'icon fixture')
        target = root / 'system'
        package.stage_linux_system_payload(app, target)
        self.assertEqual((target / 'usr/bin/modern-vlc').read_text(),
                         '#!/bin/sh\nexec /opt/modern-vlc/modern-vlc "$@"\n')
        if os.name == 'posix':
            self.assertTrue((target / 'usr/bin/modern-vlc').stat().st_mode & stat.S_IEXEC)
        self.assertEqual((target / 'usr/share/applications/modern-vlc.desktop').read_text(), desktop)
        self.assertEqual((target / 'usr/share/icons/hicolor/256x256/apps/modern-vlc.png').read_bytes(),
                         (app / 'modern-vlc.png').read_bytes())
        self.assertEqual((target / 'opt/modern-vlc/modern-vlc').read_bytes(),
                         (app / 'modern-vlc').read_bytes())

    def test_aom_release_policy_accepts_upstream_flags_and_rejects_overrides(self):
        spec = importlib.util.spec_from_file_location('native_build', HERE / 'build-native.py')
        build = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(build)
        cache = ('CMAKE_BUILD_TYPE:STRING=Release\n'
            'CMAKE_C_FLAGS:STRING=-O3 -g0 -DNDEBUG -I/sdk/include\n'
            'CMAKE_CXX_FLAGS:STRING=-O3 -g0 -DNDEBUG -stdlib=libc++\n'
            'CMAKE_C_FLAGS_RELEASE:STRING=-O3 -g0 -DNDEBUG -std=c11 -Wall\n'
            'CMAKE_CXX_FLAGS_RELEASE:STRING=-O3 -g0 -DNDEBUG -Wall -Wextra\n')
        with patch('builtins.print'):
            self.assertEqual(build.verify_aom_release_flags(cache)['CMAKE_BUILD_TYPE'], 'Release')
            for original, changed in [('=Release', '=RelWithDebInfo'),
                    ('-std=c11 -Wall', '-std=c11 -Wall -O0'),
                    ('-std=c11 -Wall', '-std=c11 -Wall -g'),
                    ('-Wall -Wextra', '-Wall -Wextra -g2'),
                    ('-Wall -Wextra', '-Wall -Wextra -UNDEBUG')]:
                with self.assertRaisesRegex(RuntimeError, 'required release compiler flags'):
                    build.verify_aom_release_flags(cache.replace(original, changed))

    def test_review_recovery_preserves_archived_signatures_instead_of_signing_cache(self):
        spec = importlib.util.spec_from_file_location('review_reuse', HERE / 'reuse-native-review.py')
        reuse = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(reuse)
        directory = Path('D:/owned-native-generation')
        scratch = Path('E:/Temp/owned-native-recovery')
        archive = directory / 'normal.zip'
        with patch.object(Path, 'glob', return_value=[archive, directory / 'normal-symbols.zip',
                directory / 'normal-corresponding-source-01.zip']), \
                patch.object(Path, 'mkdir'), patch.object(reuse.subprocess, 'run') as run:
            self.assertEqual(reuse.recover_signed_app(directory, scratch), scratch / 'Modern VLC.app')
        self.assertEqual(run.call_args_list[0].args[0], ['ditto', '-x', '-k', archive, scratch])
        self.assertEqual(run.call_args_list[1].args[0],
                         ['codesign', '--verify', '--deep', '--strict', scratch / 'Modern VLC.app'])

    def test_review_reuse_rejects_all_production_and_configuration_changes(self):
        spec = importlib.util.spec_from_file_location('review_reuse', HERE / 'reuse-native-review.py')
        reuse = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(reuse)
        self.assertTrue(reuse.test_only(['tools/desktop-player/verify-native-player.py',
                                        'doc/redesign/PLAN.md']))
        for path in ['modules/gui/qt/maininterface/player_diagnostics.hpp',
                     'modules/gui/qt/player/qml/PlayerView.qml', 'configure.ac',
                     'tools/desktop-player/build-native.py', 'tools/desktop-player/package-native.py',
                     'tools/desktop-player/install-ci-dependencies.sh']:
            self.assertFalse(reuse.test_only([path]), path)
        workflow = (HERE.parents[1] / '.github/workflows/desktop-packages.yml').read_text()
        evidence_lines = ('            ${{ runner.temp }}/native-package-checks/*-runtime/*json\n',
                          '            ${{ runner.temp }}/native-package-checks/*-runtime/crashes/**\n')
        previous = workflow
        for line in evidence_lines:
            previous = previous.replace(line, '')
        self.assertEqual(reuse.workflow_build_contract(previous), reuse.workflow_build_contract(workflow))
        self.assertNotEqual(reuse.workflow_build_contract(workflow.replace("PYTHONDONTWRITEBYTECODE: '1'",
            "PYTHONDONTWRITEBYTECODE: '0'")), reuse.workflow_build_contract(workflow))

    def test_native_slider_click_uses_handle_center_at_all_window_sizes(self):
        spec = importlib.util.spec_from_file_location('native_client', HERE / 'native-player-client.py')
        client = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(client)
        # The former 1%-of-widget click lands before the handle center on a
        # compact seekbar, mapping to zero rather than six seconds of 600.
        for width, padding, handle in [(80, 2, 8), (170, 2, 8), (340, 4, 16)]:
            for mirrored in (False, True):
                geometry = dict(width=width, left_padding=padding, right_padding=padding,
                                available_width=width - padding * 2, handle_width=handle,
                                mirrored=mirrored)
                for position in (0, 0.01, 0.1, 0.4, 1):
                    fraction = client.NativePlayerClient.slider_fraction(
                        {'slider_geometry': geometry}, position)
                    x = fraction * width
                    offset = width - x - padding if mirrored else x - padding
                    observed = (offset - handle / 2) / (width - padding * 2 - handle)
                    self.assertAlmostEqual(observed, position)
                    self.assertGreaterEqual(fraction, 0)
                    self.assertLessEqual(fraction, 1)

    def test_installed_homebrew_metadata_preserves_the_exact_recipe_and_sdk(self):
        spec = importlib.util.spec_from_file_location('toolchain', HERE / 'bind-ci-toolchain.py')
        toolchain = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(toolchain)
        root = Path(sys.argv_scratch) / ('brew-metadata-' + uuid.uuid4().hex)
        cellar = root / 'Cellar'
        keg = cellar / 'qtbase/6.12.0_2'
        (keg / '.brew').mkdir(parents=True)
        originals = {'.brew/qtbase.rb': b'Exact installed recipe\n',
                     'INSTALL_RECEIPT.json': b'{"version":"6.12.0_2"}\n',
                     'sbom.spdx.json': b'{"SPDXID":"SPDXRef-DOCUMENT"}\n'}
        for relative, content in originals.items():
            (keg / relative).write_bytes(content)
            (keg / relative).chmod(stat.S_IREAD)
        destination = root / 'metadata'
        raw = {'formulae': [{'name': 'qtbase', 'installed': [{'version': '6.12.0_2'}]}]}
        with patch.object(toolchain.subprocess, 'check_output', return_value=str(cellar)):
            toolchain.retain_brew_metadata(raw, destination)
        rows = json.loads((destination / 'installed-metadata.json').read_text())
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['metadata_sha256'],
            {relative: package.sha(keg / relative) for relative in originals})
        for relative, content in originals.items():
            self.assertEqual((destination / 'installed-metadata/qtbase/6.12.0_2' /
                              Path(relative).name).read_bytes(), content)
            self.assertEqual((keg / relative).read_bytes(), content)
            self.assertFalse((keg / relative).stat().st_mode & stat.S_IWUSR)

    def test_macos_gui_plugin_keeps_source_runpath_without_mutating_sdk(self):
        root = Path(sys.argv_scratch) / ('qt-plugins-' + uuid.uuid4().hex)
        installed = root / 'sdk/plugins'
        app = root / 'Modern VLC.app'
        (app / 'Contents/Resources').mkdir(parents=True)
        for category, names in [('platforms', ['libqcocoa.dylib', 'libqminimal.dylib']),
                                ('imageformats', ['libqpdf.dylib'])]:
            (installed / category).mkdir(parents=True)
            for name in names:
                (installed / category / name).write_bytes(b'\xcf\xfa\xed\xfe' + name.encode())
                (installed / category / name).chmod(stat.S_IREAD)
        with patch.object(package, 'output', return_value=str(installed)), \
                patch.object(package, 'mac_runpath_bindings',
                    side_effect=lambda path: [('@loader_path/../../lib', str(path.parent / '../../lib'))]), \
                patch.object(package, 'run') as command:
            plugins = package.stage_mac_qt_plugins(root / 'sdk', app)
        self.assertEqual({path.name for path in plugins}, {'libqcocoa.dylib', 'libqpdf.dylib'})
        self.assertTrue(all(path.stat().st_mode & stat.S_IWUSR for path in plugins))
        self.assertEqual(command.call_count, 2)
        self.assertFalse((installed / 'imageformats/libqpdf.dylib').stat().st_mode & stat.S_IWUSR)
        rows = json.loads((app / 'Contents/Resources/QT-PLUGINS.json').read_text())
        self.assertEqual({row['source_sha256'] for row in rows},
            {package.sha(installed / path.relative_to(app / 'Contents/PlugIns')) for path in plugins})

    def test_packaged_macos_dependency_rejects_runner_sdk_resolution(self):
        app = Path('E:/Temp/owned-app')
        framework = 'QtCore.framework/Versions/A/QtCore'
        origin = app / 'Contents/PlugIns/libtest.dylib'
        executable = app / 'Contents/MacOS/vlc'
        bundled = app / 'Contents/Frameworks'
        host = Path('D:/native-sdk/lib')
        exists = {bundled / framework, host / framework}
        with patch.object(Path, 'is_file', lambda path: path in exists), \
                patch.object(package, 'mac_runpaths', return_value=[str(host), str(bundled)]):
            with self.assertRaisesRegex(RuntimeError, 'outside the app'):
                package.resolve_packaged_mac_dependency('@rpath/' + framework, origin, executable, app)
        with patch.object(Path, 'is_file', lambda path: path in exists), \
                patch.object(package, 'mac_runpaths', return_value=[str(bundled), str(host)]):
            self.assertEqual(package.resolve_packaged_mac_dependency('@rpath/' + framework,
                origin, executable, app), (bundled / framework).resolve())

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
        (original / 'Makefile.am').write_bytes(protected.read_bytes())
        tracked = {'Makefile.am'}
        with patch.object(build_module, 'ROOT', original):
            build_module.retain_bootstrap_sources(work, tracked)
        with patch.object(build_module, 'ROOT', restored), \
                patch.object(build_module, 'output', return_value='Makefile.am'), \
                patch.object(build_module, 'run') as invoked:
            build_module.prepare_bootstrap_sources(work, work / 'build', {},
                {'Makefile.am': {'sha256': build_module.sha(protected)}})
            invoked.assert_not_called()
        self.assertEqual((restored / 'configure').read_bytes(), generated.read_bytes())
        self.assertEqual((restored / 'configure').stat().st_mtime_ns, expected_time)
        self.assertEqual(protected.read_bytes(), b'current tracked source')

    def test_changed_upstream_bootstrap_inputs_regenerate_without_discarding_objects(self):
        spec = importlib.util.spec_from_file_location('native_build', HERE / 'build-native.py')
        builder = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(builder)
        work = Path(sys.argv_scratch) / ('upstream-bootstrap-' + uuid.uuid4().hex)
        source = work / 'source'; source.mkdir(parents=True)
        for name in ('autotools', 'm4', 'po'):
            (source / name).mkdir()
        make_input = source / 'Makefile.am'
        make_input.write_bytes(b'old upstream make input')
        (source / 'configure').write_bytes(b'old generated configure')
        build = work / 'build'; build.mkdir()
        (build / 'config.status').write_bytes(b'existing configured cohort')
        (build / 'retained.o').write_bytes(b'existing compiler object')
        with patch.object(builder, 'ROOT', source):
            builder.retain_bootstrap_sources(work, {'Makefile.am'})
            make_input.write_bytes(b'new upstream make input')
            with patch.object(builder, 'output', return_value='Makefile.am'), \
                    patch.object(builder, 'run', side_effect=lambda *a, **kw:
                        (source / 'configure').write_bytes(b'new generated configure')) as invoked:
                builder.prepare_bootstrap_sources(work, build, {},
                    # An interrupted pre-bootstrap dependency build has already
                    # advanced source-times.json. The archive's own input
                    # binding must still reject its old generated configure.
                    {'Makefile.am': {'sha256': builder.sha(make_input)}})
                invoked.assert_called_once()
        self.assertEqual((source / 'configure').read_bytes(), b'new generated configure')
        self.assertEqual((build / 'retained.o').read_bytes(), b'existing compiler object')

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
