"""Regression for converting the retained Windows debug configuration."""
import shlex
import unittest
from release_profile import release_arguments


class ReleaseProfileTest(unittest.TestCase):
    def test_retained_debug_configuration(self):
        previous = ['--host=x86_64-w64-mingw32', '--enable-debug', '--disable-optimizations',
                    '--enable-qt-qml-debug', 'CFLAGS=-I/work/media/include -DWINVER=0x0601 -g -Og',
                    'CXXFLAGS=-fstack-protector-strong -ggdb3 -O0', 'LTCFLAGS=-O0']
        actual = release_arguments(previous)
        self.assertEqual(actual, release_arguments(actual))
        self.assertIn('--disable-debug', actual)
        self.assertIn('--enable-optimizations', actual)
        self.assertIn('--disable-qt-qml-debug', actual)
        self.assertNotIn('--enable-debug', actual)
        flags = dict(item.split('=', 1) for item in actual if not item.startswith('--'))
        self.assertEqual(shlex.split(flags['CFLAGS']), ['-I/work/media/include', '-DWINVER=0x0601', '-g0'])
        self.assertEqual(shlex.split(flags['CXXFLAGS']), ['-fstack-protector-strong', '-g0'])
        self.assertEqual(shlex.split(flags['LTCFLAGS']), ['-O2', '-g0'])


if __name__ == '__main__':
    unittest.main()
