"""Regression contracts for the shared Windows/native codec-policy boundary."""
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('retained_cohort',
    Path(__file__).with_name('verify-retained-plugin-cohort.py'))
cohort = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cohort)


class SharedCodecPolicy(unittest.TestCase):
    before = '''"""Hosted builder."""
import shlex
FLAGS = '-O3 -g0 -DNDEBUG'
def verify_aom_release_flags(cache):
    return shlex.split(cache) == shlex.split(FLAGS)
def meson():
    return 'old Cocoa setup'
def main():
    meson()
if __name__ == '__main__':
    main()
'''

    def test_hosted_cocoa_repair_preserves_shared_codec_contract(self):
        after = self.before.replace('old Cocoa setup', 'guarded Cocoa setup')
        after += '\ndef prepare_mpv_cocoa_guard():\n    return True\n'
        self.assertTrue(cohort.verify_shared_codec_policy(self.before, after)
                        ['shared_codec_policy_unchanged'])

    def test_changed_codec_policy_is_rejected(self):
        with self.assertRaisesRegex(AssertionError, 'codec policy changed'):
            cohort.verify_shared_codec_policy(self.before,
                self.before.replace('return shlex.split(cache)', 'return not shlex.split(cache)'))

    def test_changed_module_input_is_rejected(self):
        with self.assertRaisesRegex(AssertionError, 'codec policy changed'):
            cohort.verify_shared_codec_policy(self.before, self.before.replace('-g0', '-g'))


if __name__ == '__main__':
    unittest.main()
