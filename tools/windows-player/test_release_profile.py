"""Regression for converting the retained Windows debug configuration."""
import shlex
import json
import os
from pathlib import Path, PurePosixPath
import sys
import unittest
import uuid
from unittest.mock import patch
from release_profile import release_arguments, write_object_profile, configure_base_flags, configuration_sources_unchanged


class ReleaseProfileTest(unittest.TestCase):
    def test_configure_flags_do_not_accumulate_generated_sdk_flags(self):
        prefix = PurePosixPath('/sdk')
        arguments = ['CPPFLAGS=-DWINVER=0x0601 -I/sdk/include -D__USE_MINGW_ANSI_STDIO=1 -I/sdk/include',
            'LDFLAGS=-Wl,--nxcompat -L/sdk/lib -lssp -Wl,--nxcompat -L/sdk/lib -lssp -Wl,--gc-sections -lcustom -lcustom',
            'CFLAGS=-I/sdk/include -g0']
        flags = configure_base_flags(arguments, prefix)
        self.assertEqual(flags['CPPFLAGS'], ['-DWINVER=0x0601'])
        self.assertEqual(flags['LDFLAGS'], ['-Wl,--gc-sections', '-lcustom', '-lcustom'])
        self.assertEqual(flags['CFLAGS'], ['-g0'])
        self.assertEqual(flags, configure_base_flags(
            [key + '=' + shlex.join(value) for key, value in flags.items()], prefix))

    def test_object_profile_tracks_content_instead_of_configure_timestamp(self):
        build = Path(sys.argv_scratch) / ('object-profile-' + uuid.uuid4().hex)
        build.mkdir(parents=True)
        (build / 'config.status').write_text('configured')
        (build / 'config.h').write_text('#define NDEBUG 1\n')
        for relative in ('Makefile', 'src/Makefile', 'modules/Makefile', 'modules/gui/qt/Makefile'):
            path = build / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('CC = gcc\nCFLAGS = -O3 -g0\nCPPFLAGS = -D_WIN32_WINNT=0x0601\n')
        os.utime(build / 'config.status', ns=(1000000000, 1000000000))
        marker = write_object_profile(build)
        self.assertEqual(marker.stat().st_mtime_ns, 1000000000)
        original = marker.read_bytes(), marker.stat().st_mtime_ns
        os.utime(build / 'config.status', ns=(2000000000, 2000000000))
        self.assertEqual(write_object_profile(build), marker)
        self.assertEqual((marker.read_bytes(), marker.stat().st_mtime_ns), original)
        (build / 'config.h').write_text('#define NDEBUG 1\n#define NEW_API 1\n')
        write_object_profile(build)
        self.assertNotEqual(marker.read_bytes(), original[0])
        self.assertGreater(marker.stat().st_mtime_ns, original[1])
        self.assertEqual(json.loads(marker.read_text())['schema'], 'vlc_redesign.object_profile.v1')

    def test_configuration_reuse_checks_actual_source_delta(self):
        with patch('release_profile.subprocess.check_output', return_value='') as invoked:
            self.assertTrue(configuration_sources_unchanged(Path('/source'), 'prior'))
            self.assertIn('configure.ac', invoked.call_args.args[0])
            self.assertIn('contrib/src/aom', invoked.call_args.args[0])
        with patch('release_profile.subprocess.check_output', return_value='configure.ac\n'):
            self.assertFalse(configuration_sources_unchanged(Path('/source'), 'prior'))

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
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--scratch', required=True)
    args = parser.parse_args()
    sys.argv_scratch = args.scratch
    unittest.main(argv=[sys.argv[0]])
