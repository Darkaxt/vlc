"""Protect installer payload integrity and the nonrecursive uninstall contract."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import unittest
import uuid

spec = importlib.util.spec_from_file_location('installer', Path(__file__).with_name('package-windows-installer.py'))
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


class InstallerContract(unittest.TestCase):
    def root(self):
        base = os.environ.get('VLC_INSTALLER_TEST_ROOT') or os.environ.get('RUNNER_TEMP')
        if not base:
            self.skipTest('Set an exact task-owned VLC_INSTALLER_TEST_ROOT or use native CI RUNNER_TEMP')
        root = Path(base) / ('installer-fixture-' + uuid.uuid4().hex)
        root.mkdir(parents=True)
        return root

    def payload(self, root):
        (root / 'portable').mkdir()
        info = dict(product='Modern VLC Fork', source_commit='a' * 40, version='1.1.12')
        (root / 'BUILDINFO.json').write_text(json.dumps(info))
        raw = (root / 'BUILDINFO.json').read_bytes()
        manifest = dict(info, files=[dict(path='BUILDINFO.json', bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())])
        (root / 'FILE-MANIFEST.json').write_text(json.dumps(manifest))

    def test_untouched_payload_and_profile_are_required(self):
        root = self.root()
        self.payload(root)
        self.assertEqual(installer.verify_payload(root, 'a' * 40, '1.1.12'), {'BUILDINFO.json', 'FILE-MANIFEST.json'})
        (root / 'portable/settings.ini').write_text('private=true')
        with self.assertRaises(AssertionError):
            installer.verify_payload(root, 'a' * 40, '1.1.12')

    def test_unlisted_file_and_mutated_payload_are_rejected(self):
        root = self.root()
        self.payload(root)
        (root / 'unexpected.log').write_text('private')
        with self.assertRaises(AssertionError):
            installer.verify_payload(root, 'a' * 40, '1.1.12')
        root = self.root()
        self.payload(root)
        with (root / 'BUILDINFO.json').open('a') as stream:
            stream.write(' ')
        with self.assertRaises(AssertionError):
            installer.verify_payload(root, 'a' * 40, '1.1.12')

    def test_removal_preserves_unlisted_data_and_escapes_nsis_tokens(self):
        script = installer.removal_script({'vlc.exe', 'plugins/one.dll', 'locale/el/vlc.mo', 'icons/$name.ico'})
        self.assertNotIn('RMDir /r', script)
        self.assertNotIn('portable', script)
        self.assertNotIn('Delete "$INSTDIR\\*', script)
        self.assertIn('Delete "$INSTDIR\\icons\\$$name.ico"', script)
        self.assertLess(script.index('RMDir "$INSTDIR\\locale\\el"'), script.index('RMDir "$INSTDIR\\locale"'))
        with self.assertRaises(AssertionError):
            installer.nsis_string('name\nDelete *')


if __name__ == '__main__':
    unittest.main()
