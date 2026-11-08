"""Focused diagnostics for native package closure and immutable MPV staging."""
import ast
import importlib.util
import json
import io
import os
import shutil
import stat
from pathlib import Path
import subprocess
import sys
import uuid
import zipfile
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
    def test_linux_gl_client_closure_preserves_the_prior_runtime(self):
        work = Path(sys.argv_scratch) / ('linux-gl-client-' + uuid.uuid4().hex)
        prefix = work / 'deps/lib'; prefix.mkdir(parents=True)
        library = prefix / 'libmpv.so.2'; library.write_bytes(b'unchanged compiled MPV')
        client = prefix / 'libOpenGL.so.0'; client.write_bytes(b'vendor-neutral client ABI')
        legacy = work / 'mpv-runtime'; legacy.mkdir()
        (legacy / 'retained-normal').write_bytes(b'protected old runtime')
        with patch.object(package, 'MAC', False), patch.object(package, 'run'), \
                patch.object(package, 'dependencies', side_effect=lambda path, **_: [str(client)] if path == library else []):
            package.stage_mpv(work, work / 'deps')
            runtime = package.mpv_runtime_directory(work)
        self.assertNotEqual(runtime, legacy)
        self.assertEqual((legacy / 'retained-normal').read_bytes(), b'protected old runtime')
        self.assertEqual((runtime / client.name).read_bytes(), client.read_bytes())
        self.assertEqual({row['name'] for row in json.loads((runtime / 'runtime.json').read_text())},
                         {library.name, client.name})

    def test_snap_uses_connected_external_graphics_and_preserves_player_payload(self):
        work = Path(sys.argv_scratch) / ('snap-gpu-' + uuid.uuid4().hex)
        app = work / 'normal'; app.mkdir(parents=True)
        (app / 'normal-player').write_bytes(b'unchanged normal payload')
        snap = work / 'snap'; snap.mkdir()
        package.stage_linux_snap_payload(app, snap, '1.1.12', 'amd64')
        self.assertEqual((snap / 'player/normal-player').read_bytes(), (app / 'normal-player').read_bytes())
        self.assertTrue((snap / 'gpu-2404').is_dir())
        metadata = (snap / 'meta/snap.yaml').read_text()
        self.assertIn('default-provider: mesa-2404', metadata)
        self.assertIn('target: $SNAP/gpu-2404', metadata)
        self.assertIn('command-chain: [bin/gpu-runtime]', metadata)
        self.assertIn('confinement: strict', metadata)
        self.assertEqual((snap / 'bin/gpu-runtime').read_bytes(),
                         (package.ROOT / 'tools/desktop-player/snap-gpu-runtime.sh').read_bytes())

    def test_linux_installer_metadata_covers_audited_host_opengl(self):
        audit = {'members': [{'dependencies': [
            {'os_dependency': '/lib/x86_64-linux-gnu/libc.so.6'},
            {'os_dependency': '/lib/x86_64-linux-gnu/libOpenGL.so.0'},
            {'os_dependency': '/lib/x86_64-linux-gnu/libGLX.so.0'}]}]}
        dependencies = package.linux_host_dependencies(audit)
        self.assertIn('libopengl0', dependencies['deb'])
        self.assertIn('libglx0', dependencies['deb'])
        self.assertIn('libOpenGL.so.0()(64bit)', dependencies['rpm'])
        self.assertIn('libGLX.so.0()(64bit)', dependencies['rpm'])
        audit['members'][0]['dependencies'].append({'os_dependency': '/lib/libUnknownDriver.so.1'})
        with self.assertRaisesRegex(RuntimeError, 'Unmapped Linux host dependency'):
            package.linux_host_dependencies(audit)

    def test_package_only_recovery_selects_one_exact_normal_generation(self):
        spec = importlib.util.spec_from_file_location('linux_recovery', HERE / 'recover-linux-packages.py')
        recovery = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(recovery)
        source = 'a' * 40
        name = 'Modern-VLC-Fork-1.1.12-linux-x86_64'
        data = io.BytesIO()
        with zipfile.ZipFile(data, 'w') as archive:
            for kind in ('tar.xz', 'AppImage', 'deb', 'rpm', 'snap'):
                archive.writestr('.desktop-build/packages/' + source + '/' + name + '.' + kind, b'package')
            archive.writestr('.desktop-build/packages/' + source + '/symbols.zip', b'symbols')
        with zipfile.ZipFile(data) as archive:
            actual, entries = recovery.package_entries(archive, source, 'linux-x86_64')
            self.assertEqual(actual, name)
            self.assertEqual(set(entries), {'tar.xz', 'AppImage', 'deb', 'rpm', 'snap'})
            with self.assertRaisesRegex(RuntimeError, 'source-bound normal Linux TAR'):
                recovery.package_entries(archive, 'b' * 40, 'linux-x86_64')
            with self.assertRaisesRegex(RuntimeError, 'exact source revision'):
                recovery.package_entries(archive, '../escape', 'linux-x86_64')

    def test_snap_seed_wait_uses_required_installer_privilege(self):
        spec = importlib.util.spec_from_file_location('linux_packages', HERE / 'verify-linux-packages.py')
        verifier = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(verifier)
        case = Path(sys.argv_scratch) / ('snap-command-' + uuid.uuid4().hex)
        case.mkdir(parents=True)
        def command(*argv, **kwargs):
            if argv == ('snap', 'debug', 'confinement'):
                kwargs['stdout'].write('strict\n')
            return SimpleNamespace(returncode=0)
        verify = MagicMock()
        with patch.object(verifier.shutil, 'which', return_value='/usr/bin/snap'), \
                patch.object(verifier.subprocess, 'run', return_value=SimpleNamespace(returncode=1)), \
                patch.object(verifier, 'run', side_effect=command) as invoked, \
                patch.object(Path, 'exists', return_value=False):
            verifier.verify_snap_installation(Path('owned.snap'), case, verify)
        self.assertIn((('sudo', '-n', 'snap', 'wait', 'system', 'seed.loaded'), {}),
                      [(call.args, call.kwargs) for call in invoked.call_args_list])
        self.assertIn((('sudo', '-n', 'snap', 'remove', '--purge', 'modern-vlc-fork'), {}),
                      [(call.args, call.kwargs) for call in invoked.call_args_list])
        verify.assert_called_once()

    def test_windows_image_sources_stage_exact_archives_without_overwriting_tampering(self):
        spec = importlib.util.spec_from_file_location('codec_builder', HERE.parent / 'windows-player/build-upstream-codecs.py')
        codecs = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(codecs)
        root = Path(sys.argv_scratch) / ('image-transfer-' + uuid.uuid4().hex)
        retained, archives = root / 'prepared', root / 'native'
        retained.mkdir(parents=True)
        archives.mkdir()
        (retained / 'image.tar.xz').write_bytes(b'prepared')
        inputs = [{'archive': 'image.tar.xz', 'sha512': codecs.sha(retained / 'image.tar.xz', 'sha512')}]
        with patch.object(codecs.importlib.util, 'module_from_spec', return_value=SimpleNamespace(definitions=lambda _: inputs)), \
             patch.object(codecs.importlib.util, 'spec_from_file_location', return_value=SimpleNamespace(loader=SimpleNamespace(exec_module=lambda _: None))):
            codecs.stage_image_sources(HERE.parents[1], archives, retained)
            self.assertEqual((archives / 'image.tar.xz').read_bytes(), b'prepared')
            stamp = (archives / 'image.tar.xz').stat().st_mtime_ns
            codecs.stage_image_sources(HERE.parents[1], archives, retained)
            self.assertEqual((archives / 'image.tar.xz').stat().st_mtime_ns, stamp)
            (archives / 'image.tar.xz').write_bytes(b'changed')
            with self.assertRaisesRegex(RuntimeError, 'native image source differs'):
                codecs.stage_image_sources(HERE.parents[1], archives, retained)
            self.assertEqual((archives / 'image.tar.xz').read_bytes(), b'changed')

    def test_mac_image_archive_linkage_is_required_and_content_bound(self):
        spec = importlib.util.spec_from_file_location('image_dependencies', HERE / 'image_dependencies.py')
        images = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(images)
        root = Path(sys.argv_scratch) / ('mac-images-' + uuid.uuid4().hex)
        work, prefix, build = root / 'images', root / 'prefix', root / 'build'
        (prefix / 'lib').mkdir(parents=True)
        (build / 'modules/.libs').mkdir(parents=True)
        libraries = []
        for name, archive in (('zlib', 'libz.a'), ('png', 'libpng16.a')):
            path = prefix / 'lib' / archive
            path.write_bytes(name.encode())
            libraries.append({'name': name, 'prefix': str(prefix), 'static_library': archive,
                              'library_sha256': images.digest(path)})
        rules = images.mac_link_rules(work, prefix)
        self.assertIn('override LIBZ = -L' + str(prefix / 'lib') + ' -lz', rules.read_text())
        self.assertIn('libvlc_mp4.la: ' + str(rules), rules.read_text())
        self.assertIn('-Wl,-map,', rules.read_text())
        self.assertNotIn('-Wl,-Map,', rules.read_text())
        stamp = rules.stat().st_mtime_ns
        images.mac_link_rules(work, prefix)
        self.assertEqual(rules.stat().st_mtime_ns, stamp)
        (work / 'build-receipt.json').write_text(json.dumps({'libraries': libraries}))
        plugin = build / 'modules/.libs/libpng_plugin.dylib'
        plugin.write_bytes(b'actual test plugin')
        link_map = work / 'link-maps/png.map'
        link_map.write_text(str(prefix / 'lib/libz.a') + '(inflate.o)\n')
        with self.assertRaisesRegex(RuntimeError, 'both updated'):
            images.verify_mac_links(work, build)
        link_map.write_text(link_map.read_text() + str(prefix / 'lib/libpng16.a') + '(png.o)\n')
        receipt = images.verify_mac_links(work, build)
        self.assertEqual(receipt['links'][0]['unstripped_plugin_sha256'], images.digest(plugin))
        (prefix / 'lib/libz.a').write_bytes(b'changed')
        with self.assertRaisesRegex(RuntimeError, 'changed after compilation'):
            images.verify_mac_links(work, build)

    def test_image_dependency_policy_rejects_debug_and_preserves_both_source_pins(self):
        spec = importlib.util.spec_from_file_location('image_dependencies', HERE / 'image_dependencies.py')
        images = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(images)
        self.assertEqual([(row['name'], row['version']) for row in images.definitions(HERE.parents[1])],
                         [('zlib', '1.4'), ('png', '1.6.59')])
        cache = ('CMAKE_BUILD_TYPE:STRING=Release\nCMAKE_C_FLAGS:STRING=\n'
                 'CMAKE_C_FLAGS_RELEASE:STRING=-O3 -g0 -DNDEBUG -D_FILE_OFFSET_BITS=64\n')
        images.verify_release(cache)
        for bad in (cache.replace('-O3', '-O0'), cache.replace('-g0', '-g'),
                    cache.replace('-DNDEBUG', '-UNDEBUG')):
            with self.assertRaises(RuntimeError):
                images.verify_release(bad)

    def test_image_link_plan_covers_transitive_plugins_and_native_qt(self):
        spec = importlib.util.spec_from_file_location('image_links', HERE.parent / 'windows-player/verify-upstream-codec-links.py')
        links = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(links)
        root = Path(sys.argv_scratch) / ('image-links-' + uuid.uuid4().hex)
        source, build, base = root / 'src', root / 'build', root / 'codec-build'
        for name in ('codec/png.c', 'demux/mkv/mkv.hpp', 'demux/mp4/libmp4.c',
                     'services_discovery/sap.c', 'stream_filter/inflate.c'):
            path = source / 'modules' / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('/* retained source consumer */\n')
        metadata = "dlname='{name}.dll'\ndependency_libs='-L/old-sdk/lib -lz -lm'\n"
        for name in ('libpng_plugin', 'libavcodec_plugin', 'libqt_plugin'):
            parent = build / ('modules/gui/qt' if name == 'libqt_plugin' else 'modules')
            parent.mkdir(parents=True, exist_ok=True)
            (parent / (name + '.la')).write_text(metadata.format(name=name))
        (build / 'modules/convenience.la').write_text("dlname=''\ndependency_libs='-lz'\n")
        (build / 'config.h').write_text('#define _FILE_OFFSET_BITS 64\n')
        prefix = base / 'prefix'
        (prefix / 'lib').mkdir(parents=True)
        libraries = []
        for name, filename in (('zlib', 'libz.a'), ('png', 'libpng16.a')):
            path = prefix / 'lib' / filename
            path.write_bytes(name.encode())
            libraries.append({'name': name, 'prefix': str(prefix), 'static_library': filename,
                              'library_sha256': links.sha(path)})
        receipt = {'image_dependencies': {'libraries': libraries}}
        links.prepare_images(source, build, base, receipt)
        plan = json.loads((build / 'player-image-inputs.json').read_text())
        self.assertEqual([row['target'] for row in plan['targets']],
                         ['libavcodec_plugin.la', 'libpng_plugin.la', 'libqt_plugin.la'])
        rules = (build / 'player-image-links.mk').read_text()
        self.assertIn('LIBZ = -L' + str(prefix / 'lib') + ' -lz', rules)
        self.assertIn('libvlc_mp4.la: ' + str(build / 'player-image-links.mk'), rules)
        self.assertIn('libavcodec_plugin.la: LDFLAGS += -Wl,-Map,', rules)
        stamp = (build / 'player-image-links.mk').stat().st_mtime_ns
        # Libtool omits static archives from dependency_libs after they have
        # been linked explicitly. A resumed build must retain its bound graph.
        (build / 'modules/libpng_plugin.la').write_text(
            "dlname='libpng_plugin.dll'\ndependency_libs='-lm'\n")
        (build / 'modules/gui/qt/libqt_plugin.la').write_text(
            "dlname='libqt_plugin.dll'\ndependency_libs='-lm'\n")
        links.prepare_images(source, build, base, receipt)
        self.assertEqual((build / 'player-image-links.mk').stat().st_mtime_ns, stamp)
        self.assertEqual(json.loads((build / 'player-image-inputs.json').read_text())['targets'], plan['targets'])
        (prefix / 'lib/libz.a').write_bytes(b'changed')
        with self.assertRaises(AssertionError):
            links.prepare_images(source, build, base, receipt)

    def test_debian_source_epochs_have_reversible_portable_paths(self):
        spec = importlib.util.spec_from_file_location('native_sources', HERE / 'collect-native-sources.py')
        sources = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(sources)
        path = sources.debian_source_path('ffmpeg', '7:6.1.1-3ubuntu5')
        self.assertEqual(path.as_posix(), 'ffmpeg/7%3A6.1.1-3ubuntu5')
        self.assertEqual(sources.urllib.parse.unquote(path.name), '7:6.1.1-3ubuntu5')
        self.assertNotIn(':', path.as_posix())

    def test_linux_readiness_consumes_events_buffered_by_owner_queries(self):
        module_spec = importlib.util.spec_from_file_location('linux_review', HERE / 'run-linux-review.py')
        review = importlib.util.module_from_spec(module_spec)
        with patch.dict(sys.modules, {'Xlib': SimpleNamespace(X=SimpleNamespace(), display=None)}):
            module_spec.loader.exec_module(review)
        class Connection:
            ready = False
            buffered = False
            armed = False
            def get_selection_owner(self, atom):
                if atom == 2 and self.armed and not self.ready:
                    self.buffered = True
                return SimpleNamespace(id=atom) if self.ready else None
            def pending_events(self):
                self.armed = True
                return int(self.buffered)
            def next_event(self):
                self.buffered = False
                self.ready = True
        connection = Connection()
        events = SimpleNamespace(select=MagicMock(side_effect=AssertionError('Buffered event was stranded')))
        observations = []
        review.wait_for_managers(connection, [1, 2], events, observations.append)
        self.assertTrue(connection.ready)
        self.assertEqual(observations[-1], [1, 2])

    def test_native_timing_observation_keeps_all_render_events(self):
        spec = importlib.util.spec_from_file_location('native_verifier', HERE / 'verify-native-player.py')
        verifier = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(verifier)
        root = Path(sys.argv_scratch) / ('timing-observation-' + uuid.uuid4().hex)
        root.mkdir()
        rows = [{'Timestamp': str(index), 'Body': {'type': 'RENDER', 'id': 'audio/2',
                 'mode': 'realtime', 'pts': str(index * 1000), 'drift': str(20 - index)}}
                for index in range(1001)]
        (root / 'native-timing.jsonl').write_text(''.join(json.dumps(row) + '\n' for row in rows))
        (root / 'stderr.log').write_text('main generic warning: clock gap, unexpected stream discontinuity:\n')
        verifier.retain_timing_observation(root)
        report = json.loads((root / 'timing-observation.json').read_text())
        group = report['groups']['RENDER|audio/2|realtime|']
        self.assertEqual(group['count'], 1001)
        self.assertEqual(group['ranges']['pts'], [0, 1000000])
        self.assertEqual(group['last'], rows[-1])
        self.assertEqual(report['input_clock_gap_warnings'], 1)

    def test_archived_debian_sources_preserve_descriptor_identity_and_patches(self):
        spec = importlib.util.spec_from_file_location('native_sources', HERE / 'collect-native-sources.py')
        sources = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(sources)
        root = Path(sys.argv_scratch) / ('archived-debian-' + uuid.uuid4().hex)
        root.mkdir()
        original = root / 'original-input'; original.write_bytes(b'original source archive')
        patch_file = root / 'patch-input'; patch_file.write_bytes(b'Ubuntu source patch')
        descriptor = root / 'descriptor-input'
        base = 'https://snapshot.ubuntu.com/ubuntu/20261101T000000Z/pool/main/p/pcre2/'
        files = [{'id': 'original', 'url': base + 'pcre2.orig.tar.gz', 'sha256': sources.sha(original),
                  'bytes': original.stat().st_size},
                 {'id': 'patch', 'url': base + 'pcre2.diff.gz', 'sha256': sources.sha(patch_file),
                  'bytes': patch_file.stat().st_size}]
        text = ('Source: pcre2\nVersion: 10.42-4ubuntu2.1\nChecksums-Sha256:\n'
                + ''.join(f" {row['sha256']} {row['bytes']} {row['url'].rsplit('/', 1)[1]}\n" for row in files)
                + 'Files:\n')
        descriptor.write_text(text)
        pin = {'source_package': 'pcre2', 'version': '10.42-4ubuntu2.1',
               'descriptor': {'id': 'dsc', 'url': base + 'pcre2.dsc', 'sha256': sources.sha(descriptor)},
               'files': files}
        output_dir = root / 'retained'; output_dir.mkdir()
        with patch.object(sources, 'fetch_source', side_effect=lambda row, cache:
                          {'dsc': descriptor, 'original': original, 'patch': patch_file}[row['id']]):
            sources.collect_archived_debian_source(pin, output_dir, root / 'cache')
            self.assertEqual((output_dir / 'pcre2.diff.gz').read_bytes(), patch_file.read_bytes())
            self.assertEqual((output_dir / 'pcre2.dsc').read_text(), text)
            missing_patch = dict(pin, files=files[:1])
            with self.assertRaisesRegex(RuntimeError, 'source closure differs'):
                sources.collect_archived_debian_source(missing_patch, output_dir, root / 'cache')
            descriptor.write_text(text.replace('Version: 10.42-4ubuntu2.1', 'Version: different'))
            with self.assertRaisesRegex(RuntimeError, 'descriptor identity differs'):
                sources.collect_archived_debian_source(pin, output_dir, root / 'cache')

    def test_mpv_cocoa_restore_retains_objects_and_rejects_other_changes(self):
        spec = importlib.util.spec_from_file_location('native_build', HERE / 'build-native.py')
        build = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(build)
        src, prefix, work = Path('/owned/mpv-source'), Path('/owned/prefix'), Path('/owned/build')
        options = ['-Dlibmpv=true', '-Dcplayer=false']
        old = dict(source=str(src), prefix=str(prefix), options=options + ['-Dswift-build=disabled'], compiler='', pkgconfig='')
        with patch.object(Path, 'exists', return_value=True), \
                patch.object(Path, 'read_text', return_value=json.dumps(old)), \
                patch.object(Path, 'write_text'), patch.object(build.platform, 'system', return_value='Darwin'), \
                patch.object(build, 'run') as run:
            build.meson(work, 'mpv', src, prefix, options, {})
            self.assertEqual(run.call_args_list[0].args,
                ('meson', 'configure', work / 'build-mpv', '-Dswift-build=auto'))
            self.assertEqual([call.args[0] for call in run.call_args_list], ['meson', 'ninja', 'ninja'])
            run.reset_mock()
            with self.assertRaisesRegex(RuntimeError, 'configuration differs'):
                build.meson(work, 'mpv', src, prefix, options, {'CC': 'different'})
            run.assert_not_called()

    def test_windows_configure_reads_current_codec_versions(self):
        path = HERE.parent / 'windows-player/configure-player.py'
        tree = ast.parse(path.read_text())
        start = next(index for index, node in enumerate(tree.body)
            if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name)
                and target.id == 'codec_modules' for target in node.targets))
        import re
        scope = {'re': re, 'args': SimpleNamespace(source=HERE.parents[1])}
        exec(compile(ast.Module(body=tree.body[start:start + 2], type_ignores=[]),
                     str(path), 'exec'), scope)
        self.assertEqual(scope['codec_modules']['AOM'], ('aom', '3.15.3', 'libaom.a'))

    def test_windows_release_codec_versions_follow_the_delivered_revision(self):
        path = HERE.parent / 'windows-player/package-release.py'
        tree = ast.parse(path.read_text())
        function = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                        and node.name == 'verify_codec_sources')
        import re
        scope = {'re': re, 'subprocess': subprocess}
        exec(compile(ast.Module(body=[function], type_ignores=[]), str(path), 'exec'), scope)
        libraries, overrides, archives = [], [], []
        for component in ('mpg123', 'zvbi', 'mad', 'aom'):
            folder = HERE.parents[1] / 'contrib/src' / component
            version = re.search(r'^' + component.upper() + r'_VERSION := ([0-9.]+)$',
                                (folder / 'rules.mak').read_text(), re.M).group(1)
            filename, checksum = next((line.split()[1], line.split()[0])
                for line in (folder / 'SHA512SUMS').read_text().splitlines()
                if '-' + version + '.tar.' in line)
            libraries.append(dict(library=component, version=version, archive=filename,
                                  sha512=checksum, archive_sha256='a' * 64))
            overrides.append(dict(library=component, version=version, archive=filename,
                                  upstream_sha512=checksum, sha256='a' * 64))
            archives.append(dict(archive=filename, sha256='a' * 64,
                notices=[dict(archive_path='libaom-' + version + '/PATENTS', file='patent')]))
        inventory = dict(vlc_dependency_overrides=overrides, archives=archives)
        def committed_source(argv, **kwargs):
            self.assertEqual(argv[:4], ['git', '-C', str(HERE.parents[1]), 'show'])
            self.assertTrue(argv[4].startswith('delivered:'))
            return (HERE.parents[1] / argv[4].split(':', 1)[1]).read_text()
        with patch.object(subprocess, 'check_output', side_effect=committed_source):
            self.assertEqual(scope['verify_codec_sources'](HERE.parents[1], 'delivered',
                libraries, inventory)['file'], 'patent')
            libraries[-1]['version'] = '0.0.0'
            with self.assertRaises(AssertionError):
                scope['verify_codec_sources'](HERE.parents[1], 'delivered', libraries, inventory)

    def test_normal_reuse_checks_bytes_outside_the_diagnostic_guard(self):
        spec = importlib.util.spec_from_file_location('native_reuse', HERE / 'reuse-native-review.py')
        reuse = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(reuse)
        original = '#ifndef HEADER\n#define HEADER\n#ifdef VLC_PLAYER_DIAGNOSTICS\nint test;\n#endif\n#endif\n'
        changed = original.replace('int test;', '#ifdef __APPLE__\nint observed;\n#endif')
        self.assertEqual(reuse.normal_diagnostic_header(original), reuse.normal_diagnostic_header(changed))
        self.assertNotEqual(reuse.normal_diagnostic_header(original),
            reuse.normal_diagnostic_header(changed.replace('#define HEADER', '#define OTHER')))
        with self.assertRaisesRegex(RuntimeError, 'production alternate'):
            reuse.normal_diagnostic_header(original.replace('int test;', '#else\nint production;'))

    def test_traced_mac_launch_cannot_pass_a_target_fault_with_debugger_exit_zero(self):
        spec = importlib.util.spec_from_file_location('mac_packages', HERE / 'verify-macos-packages.py')
        verifier = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(verifier)
        with patch.object(verifier.subprocess, 'run', return_value=SimpleNamespace(returncode=0)), \
                patch.object(Path, 'open', MagicMock()), patch.object(Path, 'write_text') as save, \
                patch.object(verifier, 'digest', return_value='0' * 64), patch('builtins.print'):
            fault = 'stop reason = EXC_BAD_ACCESS (code=1)\nProcess 42 exited with status = 0 (0x00000000)\n'
            with patch.object(Path, 'read_text', return_value=fault):
                with self.assertRaisesRegex(RuntimeError, 'Original traced Mac launch failed'):
                    verifier.trace_launch(['vlc'], {}, Path('case'), Path('app'))
            self.assertTrue(json.loads(save.call_args.args[0])['target_faulted'])
            normal = 'EOF reached\nProcess 42 exited with status = 0 (0x00000000)\n'
            with patch.object(Path, 'read_text', return_value=normal):
                self.assertEqual(verifier.trace_launch(['vlc'], {}, Path('case'), Path('app')), normal)
            self.assertFalse(json.loads(save.call_args.args[0])['target_faulted'])

    def test_native_windows_upstream_pipeline_does_not_touch_absent_copy_mounts(self):
        spec = importlib.util.spec_from_file_location('windows_pipeline',
            HERE.parent / 'windows-player/compilation-pipeline.py')
        pipeline = importlib.util.module_from_spec(spec)
        # Only the command-selection contract runs here; resource accounting
        # belongs to the real Linux supervisor and has no Windows module.
        with patch.dict(sys.modules, {'resource': SimpleNamespace()}):
            spec.loader.exec_module(pipeline)
        steps = [(name, ['command', name]) for name in ('upstream-medialibrary',
            'runtime', 'release-compiler-cache', 'upstream-codec-cache',
            'upstream-codecs', 'upstream-codec-cache-release', 'configure-player', 'player')]
        with patch.dict(os.environ, {'VLC_PLAYER_COMPILE_CACHE': '1'}):
            self.assertEqual(pipeline.select_compiler_cache_steps(steps), steps)
        with patch.dict(os.environ, {'VLC_PLAYER_COMPILE_CACHE': '0',
                'VLC_PLAYER_COMPILE_CACHE_REASON': 'Verified native ext4 cohort'}):
            self.assertEqual([name for name, _ in pipeline.select_compiler_cache_steps(steps)],
                ['upstream-medialibrary', 'runtime', 'upstream-codecs', 'configure-player', 'player'])
            os.environ['VLC_PLAYER_COMPILE_CACHE_REASON'] = ''
            with self.assertRaisesRegex(RuntimeError, 'explicit reason'):
                pipeline.select_compiler_cache_steps(steps)

    def test_native_windows_full_pipeline_runs_after_copy_cache_steps_are_removed(self):
        spec = importlib.util.spec_from_file_location('windows_pipeline',
            HERE.parent / 'windows-player/compilation-pipeline.py')
        pipeline = importlib.util.module_from_spec(spec)
        accounting = SimpleNamespace(RUSAGE_CHILDREN=0,
            getrusage=lambda _: SimpleNamespace(ru_utime=0, ru_stime=0))
        with patch.dict(sys.modules, {'resource': accounting}):
            spec.loader.exec_module(pipeline)
        def process(*args, **kwargs):
            child = MagicMock()
            child.stdout = io.StringIO('')
            child.wait.return_value = 0
            return child
        arguments = ['pipeline', '--source', str(HERE.parents[1]),
            '--state', '/owned/state.json', '--runtime', '/owned/runtime',
            '--dependency-notices', '/owned/new-notices',
            '--release-symbols', '/owned/symbols', '--mode', 'normal-mpv-full',
            '--from-step', 'upstream-medialibrary']
        with patch.dict(os.environ, {'VLC_PLAYER_COMPILE_CACHE': '0',
                'VLC_PLAYER_COMPILE_CACHE_REASON': 'Verified native ext4 cohort'}), \
                patch.object(sys, 'argv', arguments), \
                patch.object(Path, 'read_text', return_value='0::/llm-coordinator/owned\n'), \
                patch.object(Path, 'exists', return_value=False), \
                patch.object(Path, 'is_file', return_value=True), \
                patch.object(Path, 'read_bytes', return_value=b'bound recipe'), \
                patch.object(Path, 'mkdir'), patch.object(Path, 'replace'), \
                patch.object(Path, 'write_text') as save, \
                patch.object(Path, 'open', MagicMock()), \
                patch.object(pipeline.subprocess, 'check_output', return_value='a' * 40), \
                patch.object(pipeline.subprocess, 'Popen', side_effect=process) as launch, \
                patch.object(pipeline.subprocess, 'call') as prepare_cache, \
                patch('builtins.print'):
            self.assertEqual(pipeline.main(), 0)
        prepare_cache.assert_not_called()
        commands = [call.args[0] for call in launch.call_args_list]
        self.assertFalse(any('cache-toolchain.py' in str(command) for command in commands))
        self.assertIn('build-upstream-codecs.py', str(commands))
        self.assertIn('build-player.sh', str(commands))
        for command in commands:
            if any(name in str(command) for name in
                    ('prepare-upstream-runtime.py', 'prepare-upstream-codec-notices.py')):
                self.assertEqual(command[command.index('--notices') + 1], str(Path('/owned/new-notices')))
        attempt = json.loads(save.call_args.args[0])
        self.assertEqual(attempt['dependency_notices'], str(Path('/owned/new-notices')))
        self.assertEqual(attempt['runtime'], str(Path('/owned/runtime')))
        self.assertEqual(json.loads(save.call_args.args[0])['status'], 'complete')

    def test_linux_raw_dependency_discovery_uses_only_its_owned_prefix(self):
        prefix = Path('owned-prefix/lib').resolve()
        placebo = '/owned-prefix/lib/libplacebo.so.387'

        def ldd(args, **kwargs):
            if args == ['readelf', '--dynamic', 'libmpv.so.2']:
                return '0x1 (NEEDED) Shared library: [libplacebo.so.387]\n'
            self.assertEqual(args, ['ldd', 'libmpv.so.2'])
            if kwargs.get('env', {}).get('LD_LIBRARY_PATH') == str(prefix):
                return 'libplacebo.so.387 => ' + placebo + ' (0x1234)\n'
            return 'libplacebo.so.387 => not found\n'

        with patch.object(package, 'MAC', False), \
                patch.dict(os.environ, {'LD_LIBRARY_PATH': 'unrelated-sdk'}), \
                patch.object(package.subprocess, 'check_output', side_effect=ldd):
            self.assertEqual(package.dependencies('libmpv.so.2', search_paths=[prefix]), [placebo])
            # A later portable audit must not borrow the build prefix and hide
            # a missing shipped library. Missing dependencies remain failures.
            with self.assertRaisesRegex(RuntimeError, 'libplacebo.so.387 => not found'):
                package.dependencies('libmpv.so.2')
            self.assertEqual(os.environ['LD_LIBRARY_PATH'], 'unrelated-sdk')

    def test_linux_audit_keeps_direct_app_edges_and_os_driver_children_distinct(self):
        def lookup(argv, **kwargs):
            if argv[0] == 'readelf':
                return '0x1 (NEEDED) Shared library: [libGL.so.1]\n'
            return ('libGL.so.1 => /lib/libGL.so.1 (0x1)\n'
                    'libexpat.so.1 => /lib/libexpat.so.1 (0x2)\n')
        with patch.object(package, 'MAC', False), \
                patch.object(package.subprocess, 'check_output', side_effect=lookup):
            self.assertEqual(package.dependencies('app.so'), ['/lib/libGL.so.1'])
        # The same library is still a required application edge when its own
        # ELF declares it; the final ownership audit must then inspect it.
        with patch.object(package, 'MAC', False), patch.object(package, 'output', side_effect=[
                '0x1 (NEEDED) Shared library: [libexpat.so.1]',
                'libexpat.so.1 => /lib/libexpat.so.1 (0x2)']):
            self.assertEqual(package.dependencies('fontconfig.so'), ['/lib/libexpat.so.1'])

    def test_linux_declared_interpreter_resolves_without_soname_arrow(self):
        with patch.object(package, 'MAC', False), patch.object(package, 'output', side_effect=[
                '0x1 (NEEDED) Shared library: [ld-linux-x86-64.so.2]',
                ' /lib64/ld-linux-x86-64.so.2 (0x1234)']):
            self.assertEqual(package.dependencies('libvlccore.so'),
                             ['/lib64/ld-linux-x86-64.so.2'])
        with patch.object(package, 'MAC', False), patch.object(package, 'output', side_effect=[
                '0x1 (NEEDED) Shared library: [missing.so]',
                ' /lib64/ld-linux-x86-64.so.2 (0x1234)']):
            with self.assertRaisesRegex(RuntimeError, 'omitted declared entries'):
                package.dependencies('libvlccore.so')

    def test_native_picture_rejects_decoded_video_outside_its_cocoa_parent(self):
        spec = importlib.util.spec_from_file_location('native_verify', HERE / 'verify-native-player.py')
        verify = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(verify)
        display = {'class': 'VLCSampleBufferDisplayView',
                   'frame': 'NSRect: {{0, 461}, {600, 337}}'}
        result = {'core': {'engine': 'vlc'}, 'cocoa_graphics': {
            'bounds': 'NSRect: {{0, 0}, {600, 420}}', 'children': [display]}}
        with self.assertRaises(AssertionError):
            verify.inspect_cocoa_video_placement(result)
        display['frame'] = 'NSRect: {{0, 41}, {600, 337}}'
        verify.inspect_cocoa_video_placement(result)
        result['cocoa_graphics']['bounds'] = 'NSRect: {{0, 0}, {348, 196}}'
        display['frame'] = 'NSRect: {{0, 196}, {348, 196}}'
        with self.assertRaises(AssertionError):
            verify.inspect_cocoa_video_placement(result)
        display['frame'] = 'NSRect: {{0, 0}, {348, 196}}'
        verify.inspect_cocoa_video_placement(result)

    def test_hosted_cache_retirement_requires_complete_replacement_and_preserves_inputs(self):
        spec = importlib.util.spec_from_file_location('native_build', HERE / 'build-native.py')
        build = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(build)
        root = Path(sys.argv_scratch) / ('cache-retention-' + uuid.uuid4().hex)
        work = root / '.desktop-build'
        generation, previous, unrelated = 'b' * 40, 'a' * 40, 'c' * 40
        current = work / 'packages' / generation
        current.mkdir(parents=True)
        asset = current / 'normal.zip'; asset.write_bytes(b'new normal package')
        status = {'source_commit': generation,
                  'assets': [{'name': asset.name, 'sha256': build.sha(asset)}]}
        (current / 'PACKAGE-STATUS.json').write_text(json.dumps(status))
        (work / 'package-output.json').write_text(json.dumps({
            'source_commit': generation, 'directory': str(current)}))
        inputs = root / 'tools/desktop-player/native-inputs.json'
        inputs.parent.mkdir(parents=True)
        inputs.write_text(json.dumps({'macos_contrib_commit': 'd' * 40}))
        original = work / 'corresponding-contrib' / ('d' * 40)
        retired = [work / 'packages' / previous, work / 'plugin-deployment' / previous,
                   original / 'source', original / 'selection']
        retained = [work / 'packages' / unrelated, work / 'plugin-deployment' / generation,
                    work / 'deps', work / 'vlc-build', original / 'tarballs']
        for path in retired + retained:
            path.mkdir(parents=True)
            (path / 'retained.bin').write_bytes(b'owned fixture')
        with patch.object(build, 'ROOT', root), patch.object(build.platform, 'system', return_value='Darwin'), \
                patch.dict(os.environ, {'GITHUB_ACTIONS': 'true', 'GITHUB_WORKSPACE': str(root)}), \
                patch.object(build.subprocess, 'run', side_effect=lambda args, **kwargs:
                             SimpleNamespace(returncode=1 if args[-2] == unrelated else 0)), \
                patch.object(build.shutil, 'rmtree') as remove:
            asset.write_bytes(b'changed')
            with self.assertRaisesRegex(RuntimeError, 'Replacement package changed'):
                build.retire_prior_package_generations(work)
            remove.assert_not_called()
            asset.write_bytes(b'new normal package')
            build.retire_prior_package_generations(work)
        self.assertEqual({call.args[0] for call in remove.call_args_list}, set(retired))
        receipt = json.loads((work / 'generation-retention.json').read_text())
        self.assertEqual(receipt['state'], 'complete')
        self.assertEqual(len(receipt['retired']), len(retired))
        self.assertTrue(all((path / 'retained.bin').is_file() for path in retained))

    def test_native_handover_reveals_clipped_control_by_real_scroll_and_rejects_no_progress(self):
        spec = importlib.util.spec_from_file_location('native_verify', HERE / 'verify-native-player.py')
        verify = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(verify)
        client = MagicMock()
        client.target.side_effect = lambda state, identifier=None, name=None: 1 if identifier else 2
        scroll = {'value': 0, 'advance': True}

        def snapshot():
            return {'tree': [dict(node=1, id='mediaSettingsBody', y=83, height=281,
                                  contentY=scroll['value']),
                             dict(node=2, id='', name='VLC', y=465-scroll['value'], height=24)]}

        def wheel(operation, **fields):
            self.assertEqual((operation, fields),
                             ('scroll', {'target': 'mediaSettingsBody', 'delta': -120}))
            if scroll['advance']:
                scroll['value'] = min(205, scroll['value'] + 100)

        client.snapshot.side_effect = snapshot
        client.action.side_effect = wheel
        client.await_property.side_effect = lambda *args: snapshot()
        verify.reveal_setting(client, 'VLC')
        self.assertEqual(client.action.call_count, 2)
        client.await_property.assert_called_with('mediaSettingsBody', 'moving', False)
        client.action.reset_mock()
        verify.reveal_setting(client, 'VLC')
        client.action.assert_not_called()
        scroll.update(value=0, advance=False)
        with self.assertRaisesRegex(RuntimeError, 'wheel did not advance'):
            verify.reveal_setting(client, 'VLC')

    def test_source_staging_reuses_verified_downloads_and_rejects_modified_cache(self):
        spec = importlib.util.spec_from_file_location('native_sources', HERE / 'collect-native-sources.py')
        sources = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(sources)
        root = Path(sys.argv_scratch) / ('source-cache-' + uuid.uuid4().hex)
        root.mkdir()
        original = root / 'original.tar.xz'
        original.write_bytes(b'exact original archive')
        record = {'id': 'original', 'url': 'https://example.org/source.tar.xz',
                  'sha256': sources.sha(original)}
        with patch.object(sources.urllib.request, 'urlretrieve',
                          side_effect=lambda url, target: shutil.copy2(original, target)) as retrieve:
            first = sources.stage_source(dict(record), root / 'generation-one', root / 'cache')
            second = sources.stage_source(dict(record), root / 'generation-two', root / 'cache')
            self.assertEqual(first.read_bytes(), second.read_bytes())
            self.assertEqual(retrieve.call_count, 1)
            cached = next((root / 'cache').glob('*.tar.xz'))
            cached.write_bytes(b'changed cache')
            with self.assertRaisesRegex(RuntimeError, 'Retained source checksum differs'):
                sources.stage_source(dict(record), root / 'generation-three', root / 'cache')
            self.assertEqual(retrieve.call_count, 1)

    def test_contrib_vendor_fetch_does_not_inherit_application_cargo_workspace(self):
        cargo = shutil.which('cargo')
        if not cargo:
            self.skipTest('Real Cargo metadata probe requires the installed Cargo executable')
        spec = importlib.util.spec_from_file_location('native_sources', HERE / 'collect-native-sources.py')
        sources = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(sources)
        root = Path(sys.argv_scratch) / ('cargo-isolation-' + uuid.uuid4().hex)
        application = root / 'application'
        work = application / '.desktop-build'
        work.mkdir(parents=True)
        (application / 'Cargo.toml').write_text('[workspace]\nmembers=[]\n')
        inputs = application / 'tools/desktop-player/native-inputs.json'
        inputs.parent.mkdir(parents=True)
        inputs.write_text(json.dumps({'macos_contrib_commit': 'a' * 40}))
        package_text = '[package]\nname="fetch-probe"\nversion="0.1.0"\nedition="2021"\n'

        def metadata(folder):
            folder.mkdir(parents=True)
            manifest = folder / 'Cargo.toml'
            manifest.write_text(package_text)
            (folder / 'src').mkdir()
            (folder / 'src/lib.rs').write_text('')
            return subprocess.run([cargo, 'metadata', '--offline', '--no-deps', '--format-version=1',
                                   '--manifest-path', str(manifest)], capture_output=True, text=True)

        failed = metadata(work / 'vendor-rav1e-build')
        self.assertNotEqual(failed.returncode, 0)
        self.assertIn("believes it's in a workspace", failed.stderr)
        observed = []

        def run(*args, **kwargs):
            if args[0] == 'git':
                archive = Path(next(value.split('=', 1)[1] for value in args if str(value).startswith('--output=')))
                with tarfile.open(archive, 'w:gz') as bundle:
                    item = tarfile.TarInfo('contrib/bootstrap'); item.size = 0
                    bundle.addfile(item, io.BytesIO())
            elif args[0] == 'sh':
                (kwargs['cwd'] / 'Makefile').write_text('')
            elif args[-1] == 'list':
                kwargs['stdout'].write('rav1e\n')
            elif args[-1] == 'fetch':
                observed.append(kwargs['cwd'])
                passed = metadata(kwargs['cwd'] / 'vendor-rav1e-build')
                self.assertEqual(passed.returncode, 0, passed.stderr)
                cached = Path(next(value.split('=', 1)[1] for value in args if str(value).startswith('TARBALLS=')))
                (cached / 'fetched-source.tar.xz').write_bytes(b'original source')

        destination = root / 'assembly'; destination.mkdir()
        with patch.object(sources, 'ROOT', application), patch.object(sources, 'run', side_effect=run), \
                patch.dict(os.environ, {'RUNNER_TEMP': str(root / 'runner-temp')}):
            result = sources.collect_contrib(work, destination)
        self.assertEqual(len(observed), 1)
        self.assertFalse(observed[0].is_relative_to(application))
        self.assertTrue((destination / 'contrib/fetched-source.tar.xz').is_file())
        self.assertEqual(result['upstream_commit'], 'a' * 40)

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

    def test_legacy_brew_sources_bind_original_recipe_version_and_patches(self):
        spec = importlib.util.spec_from_file_location('native_sources', HERE / 'collect-native-sources.py')
        sources = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(sources)
        target = Path('/retained/libb2/0.98.1')
        keg = Path('/usr/local/Cellar/libb2/0.98.1')
        metadata = {'formula': 'libb2', 'version': '0.98.1', 'packages': [
            {'SPDXID': 'SPDXRef-Archive-libb2-src', 'downloadLocation': 'https://example.org/source.tar.gz',
             'checksums': [{'algorithm': 'SHA256', 'checksumValue': 'a' * 64}]},
            {'SPDXID': 'SPDXRef-Patch-libb2-0', 'downloadLocation': 'https://example.org/fix.patch',
             'checksums': [{'algorithm': 'SHA256', 'checksumValue': 'b' * 64}]}]}
        def read(path, *args, **kwargs):
            if path.name == 'INSTALL_RECEIPT.json':
                return json.dumps({'source': {'spec': 'stable'}})
            return 'Original hash-bound installed Ruby recipe'
        with patch.object(Path, 'is_file', return_value=False), patch.object(Path, 'read_text', read), \
                patch.object(sources, 'sha', return_value='original-recipe-digest'), \
                patch.object(Path, 'write_text') as write, patch.object(sources, 'output', return_value=json.dumps(metadata)) as query:
            self.assertEqual([row['sha256'] for row in sources.installed_brew_sources(target, 'libb2', '0.98.1', keg)],
                             ['a' * 64, 'b' * 64])
            self.assertEqual(query.call_args.args, ('brew', 'ruby', HERE / 'read-installed-brew-sources.rb',
                                                   keg / '.brew/libb2.rb', '0.98.1'))
            write.assert_called_once()
            metadata['version'] = 'newer'
            query.return_value = json.dumps(metadata)
            with self.assertRaisesRegex(RuntimeError, 'identity differs'):
                sources.installed_brew_sources(target, 'libb2', '0.98.1', keg)
        with patch.object(Path, 'is_file', return_value=False), patch.object(Path, 'read_text', read), \
                patch.object(sources, 'sha', side_effect=['modified', 'original']), patch.object(sources, 'output') as query:
            with self.assertRaisesRegex(RuntimeError, 'Original installed recipe changed'):
                sources.installed_brew_sources(target, 'libb2', '0.98.1', keg)
            query.assert_not_called()
        with patch.object(Path, 'is_file', return_value=True), \
                patch.object(Path, 'read_text', return_value='{}'), patch.object(sources, 'output') as query:
            with self.assertRaises(KeyError):
                sources.installed_brew_sources(target, 'libb2', '0.98.1', keg)
            query.assert_not_called()  # A broken present SBOM must never be ignored.

    def test_dpkg_owner_resolves_only_actual_merged_usr_aliases(self):
        spec = importlib.util.spec_from_file_location('native_sources', HERE / 'collect-native-sources.py')
        sources = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(sources)
        canonical = Path('/usr/lib/x86_64-linux-gnu/liblzo2.so.2.0.0')
        registered = Path('/lib/x86_64-linux-gnu/liblzo2.so.2.0.0')
        def resolve(path, strict=False):
            return Path('/usr/lib') if path == Path('/lib') else canonical if path == registered else path
        def query(argv, **kwargs):
            if argv[-1] == str(registered):
                return SimpleNamespace(returncode=0, stdout='liblzo2-2:amd64: ' + str(registered) + '\n', stderr='')
            return SimpleNamespace(returncode=1, stdout='', stderr='dpkg-query: no path found matching pattern ' + argv[-1])
        with patch.object(Path, 'resolve', resolve), \
                patch.object(Path, 'is_symlink', lambda path: path == Path('/lib')), \
                patch.object(sources.subprocess, 'run', side_effect=query) as run:
            binding = sources.dpkg_owner(canonical)
            self.assertEqual(binding['package'], 'liblzo2-2:amd64')
            self.assertEqual(binding['registered_paths'], [str(registered)])
            self.assertEqual({call.args[0][-1] for call in run.call_args_list}, {str(canonical), str(registered)})
        with patch.object(Path, 'resolve', resolve), \
                patch.object(Path, 'is_symlink', lambda path: path == Path('/lib')), \
                patch.object(sources.subprocess, 'run', return_value=SimpleNamespace(returncode=0,
                    stdout='liblzo2-2:amd64: ' + str(canonical) + '\n', stderr='')) as canonical_query:
            self.assertEqual(sources.dpkg_owner(registered)['registered_paths'], [str(canonical)])
            canonical_query.assert_called_once()
            self.assertEqual(canonical_query.call_args.args[0][-1], str(canonical))
            # Do not inspect the historical alias after the physical file is
            # bound, and never accept a multiple-owner row as a package name.
            canonical_query.return_value.stdout = 'liba:amd64, libb:amd64: ' + str(canonical) + '\n'
            with self.assertRaisesRegex(RuntimeError, 'Ambiguous installed dpkg owner'):
                sources.dpkg_owner(registered)
        with patch.object(Path, 'resolve', resolve), patch.object(Path, 'is_symlink', return_value=False), \
                patch.object(sources.subprocess, 'run', side_effect=query):
            with self.assertRaisesRegex(RuntimeError, 'No unique installed dpkg owner'):
                sources.dpkg_owner(canonical)
        with patch.object(Path, 'resolve', resolve), patch.object(Path, 'is_symlink', return_value=False), \
                patch.object(sources.subprocess, 'run', return_value=SimpleNamespace(returncode=2, stdout='', stderr='database inaccessible')):
            with self.assertRaisesRegex(RuntimeError, 'query failed: database inaccessible'):
                sources.dpkg_owner(canonical)

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

    def test_linux_installer_preserves_internal_library_links(self):
        root = Path(sys.argv_scratch) / ('linux-links-' + uuid.uuid4().hex)
        app = root / 'portable'
        (app / 'lib').mkdir(parents=True)
        for name in ('modern-vlc', 'modern-vlc.desktop', 'modern-vlc.png'):
            (app / name).write_bytes(b'entry point fixture')
        (app / 'lib/libvlc.so.12').write_bytes(b'library fixture')
        try:
            (app / 'lib/libvlc.so').symlink_to('libvlc.so.12')
        except OSError as error:
            if os.name == 'nt' and error.winerror == 1314:
                self.skipTest('Windows does not grant this process symbolic-link creation')
            raise
        target = root / 'system'
        package.stage_linux_system_payload(app, target)
        installed = target / 'opt/modern-vlc/lib/libvlc.so'
        self.assertTrue(installed.is_symlink())
        self.assertEqual(os.readlink(installed), 'libvlc.so.12')
        self.assertEqual(installed.read_bytes(), b'library fixture')

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

    def test_linux_review_recovery_preserves_payload_and_rejects_escape(self):
        import io
        spec = importlib.util.spec_from_file_location('review_reuse', HERE / 'reuse-native-review.py')
        reuse = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(reuse)
        root = Path(sys.argv_scratch) / ('linux-review-recovery-' + uuid.uuid4().hex)
        for escaped in (False, True):
            directory = root / ('escaped' if escaped else 'normal')
            directory.mkdir(parents=True)
            name = 'Modern-VLC-Fork-1.1.12-linux-x86_64'
            archive = directory / (name + '.tar.xz')
            with tarfile.open(archive, 'w:xz') as output:
                entry = tarfile.TarInfo(name + ('/../outside' if escaped else '/modern-vlc'))
                blob = b'verified normal player'
                entry.size, entry.mode, entry.mtime = len(blob), 0o755, 1793232000
                output.addfile(entry, io.BytesIO(blob))
            scratch = directory / 'recovered'
            if escaped:
                with self.assertRaisesRegex(RuntimeError, 'escaped'):
                    reuse.recover_linux_app(directory, scratch)
                self.assertFalse(any(scratch.iterdir()))
            else:
                application = reuse.recover_linux_app(directory, scratch)
                self.assertEqual((application / 'modern-vlc').read_bytes(), blob)
                self.assertEqual(int((application / 'modern-vlc').stat().st_mtime), entry.mtime)

    def test_review_reuse_rejects_all_production_and_configuration_changes(self):
        spec = importlib.util.spec_from_file_location('review_reuse', HERE / 'reuse-native-review.py')
        reuse = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(reuse)
        self.assertTrue(reuse.test_only(['tools/desktop-player/verify-native-player.py',
                                        'modules/gui/qt/maininterface/player_diagnostics.hpp',
                                        'tools/desktop-player/verify-linux-packages.py',
                                        'tools/desktop-player/run-linux-review.py',
                                        'tools/windows-player/build-upstream-codecs.py',
                                        'tools/windows-player/compilation-pipeline.py',
                                        'doc/redesign/PLAN.md']))
        for path in ['modules/gui/qt/player/qml/PlayerView.qml', 'configure.ac',
                     'tools/desktop-player/build-native.py', 'tools/desktop-player/package-native.py']:
            self.assertFalse(reuse.test_only([path]), path)
        workflow = (HERE.parents[1] / '.github/workflows/desktop-packages.yml').read_text()
        evidence_lines = ('            ${{ runner.temp }}/native-package-checks/*-runtime/*json\n',
                          '            ${{ runner.temp }}/native-package-checks/*-runtime/crashes/**\n',
                          '            ${{ runner.temp }}/native-package-checks/installer-exit.json\n',
                          '            ${{ runner.temp }}/native-package-checks/*/*-stdout.log\n',
                          '            ${{ runner.temp }}/native-package-checks/*/*-stderr.log\n')
        previous = workflow
        for line in evidence_lines:
            previous = previous.replace(line, '')
        self.assertEqual(reuse.workflow_build_contract(previous), reuse.workflow_build_contract(workflow))
        self.assertNotEqual(reuse.workflow_build_contract(workflow.replace("PYTHONDONTWRITEBYTECODE: '1'",
            "PYTHONDONTWRITEBYTECODE: '0'")), reuse.workflow_build_contract(workflow))
        setup = (HERE / 'install-ci-dependencies.sh').read_text()
        self.assertEqual(reuse.mac_dependency_setup(setup),
                         reuse.mac_dependency_setup(setup.replace('qml6-module-qtqml-models ', '')))
        self.assertNotEqual(reuse.mac_dependency_setup(setup),
                            reuse.mac_dependency_setup(setup.replace('brew install', 'brew upgrade')))
        self.assertNotEqual(reuse.mac_dependency_setup(setup),
                            reuse.mac_dependency_setup(setup + 'touch changed-sdk\n'))

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
        sources = {item['source']: item['sha256'] for row in rows for item in row['source_files']}
        expected = [installed / relative for relative in
                    ('qmldir', 'assets/required.png', 'Controls/qmldir', 'Controls/Basic/qmldir')]
        self.assertEqual(sources, {str(path.resolve(strict=True)): package.sha(path) for path in expected})
        # Source ownership follows copied files, never a merged module directory
        # or an unrequested sibling. Native and pure-QML inputs are both bound.
        self.assertNotIn(str(installed.resolve()), sources)

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
            rows = package.stage_qml_modules([{'type': 'module', 'name': 'QtQuick', 'path': str(installed)}], destination)
        self.assertEqual(commands, [('install_name_tool', '-rpath', '@loader_path/../../lib',
            str(installed / '../../lib'), destination / 'QtQuick/libquickplugin.dylib')])
        self.assertEqual(plugin.read_bytes(), b'\xcf\xfa\xed\xfe' + b'source plugin')
        self.assertFalse(plugin.stat().st_mode & stat.S_IWUSR)
        self.assertEqual(rows[0]['source_files'], [{'source': str(plugin.resolve()),
                                                  'sha256': package.sha(plugin)}])

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
            self.assertFalse(package.external('/lib/libOpenGL.so.0'))
            self.assertTrue(package.external('/lib/libGLdispatch.so.0'))
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
        runtime = package.mpv_runtime_directory(work); runtime.mkdir()
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
    parser.add_argument('--test', action='append', default=[], help='Run only these named focused diagnostics')
    args = parser.parse_args()
    args.scratch.mkdir(parents=True, exist_ok=True)
    sys.argv_scratch = str(args.scratch)
    unittest.main(argv=[sys.argv[0], *args.test])
