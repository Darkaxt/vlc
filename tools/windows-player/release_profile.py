"""The Windows application release profile, independent of diagnostic hooks."""
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import subprocess


def configure_base_flags(arguments, prefix):
    """Recover user flags, excluding the exact flags configure adds itself.

    Never deduplicate arbitrary libraries: repeated -l arguments can be required
    for static link order. These entries come from this pinned Windows target's
    configure.ac branches and are appended again by configure.
    """
    generated = {
        'CPPFLAGS': {'-I' + str(prefix / 'include'), '-D__USE_MINGW_ANSI_STDIO=1'},
        'CFLAGS': {'-I' + str(prefix / 'include')},
        'CXXFLAGS': {'-I' + str(prefix / 'include')},
        'OBJCFLAGS': {'-I' + str(prefix / 'include'), '-F' + str(prefix),
                      '-F' + str(prefix / 'Frameworks')},
        'LDFLAGS': {'-L' + str(prefix / 'lib'), '-lssp', '-Wl,--nxcompat',
            '-Wl,--no-seh', '-Wl,--dynamicbase', '-Wl,--high-entropy-va',
            '-Wl,--image-base,0x140000000'},
    }
    return {key: [flag for flag in shlex.split(next((entry.split('=', 1)[1]
            for entry in arguments if entry.startswith(key + '=')), ''))
            if flag not in generated[key]] for key in generated}


def write_object_profile(build):
    """Invalidate objects only when their effective configuration changes."""
    profiles = {}
    for relative in ('Makefile', 'src/Makefile', 'modules/Makefile', 'modules/gui/qt/Makefile'):
        content = (build / relative).read_text()
        profiles[relative] = {key: match.group(1) if (match := re.search(
            r'^' + key + r' = (.*)$', content, re.M)) else None
            for key in ('CC', 'CXX', 'CFLAGS', 'CXXFLAGS', 'OBJCFLAGS',
                        'CPPFLAGS', 'LDFLAGS', 'LTCFLAGS', 'DEFS')}
    record = {'schema': 'vlc_redesign.object_profile.v1', 'flags': profiles,
              'config_h_sha256': hashlib.sha256((build / 'config.h').read_bytes()).hexdigest()}
    data = (json.dumps(record, sort_keys=True, indent=2) + '\n').encode()
    marker = build / 'player-object-profile.json'
    if not marker.exists() or marker.read_bytes() != data:
        initial = not marker.exists()
        pending = marker.with_suffix('.pending')
        pending.write_bytes(data)
        pending.replace(marker)
        if initial:
            # Adopt the existing, verified configured cohort. Objects completed
            # after this configuration remain reusable after a failed link.
            stamp = (build / 'config.status').stat().st_mtime_ns
            os.utime(marker, ns=(stamp, stamp))
    return marker


def configuration_sources_unchanged(source, previous):
    paths = ['configure.ac', 'bootstrap', 'm4', 'autotools', 'Makefile.am',
        '**/Makefile.am', 'include/vlc_version.h.in',
        'contrib/src/medialibrary', 'contrib/src/mpg123', 'contrib/src/zvbi',
        'contrib/src/aom', 'contrib/src/mad',
        'tools/windows-player/configure-player.py',
        'tools/windows-player/configure-upstream-player.sh',
        'tools/windows-player/release_profile.py']
    return not subprocess.check_output(['git', '-C', str(source), 'diff',
        '--name-only', previous, 'HEAD', '--', *paths], text=True).strip()


def release_arguments(arguments):
    """Preserve target/security flags while removing a retained debug profile."""
    result = [item for item in arguments if item.split('=', 1)[0] not in
              ('--enable-debug', '--disable-debug', '--enable-optimizations',
               '--disable-optimizations', '--enable-qt-qml-debug', '--disable-qt-qml-debug')]
    for variable in ('CFLAGS', 'CXXFLAGS', 'OBJCFLAGS', 'LTCFLAGS'):
        value = next((item.split('=', 1)[1] for item in result
                      if item.startswith(variable + '=')), '')
        flags = [flag for flag in shlex.split(value)
                 if not flag.startswith(('-g', '-O'))]
        # VLC's --disable-debug selects its upstream -O3 application profile.
        # Libtool's separate compiler flags do not receive that selection.
        flags += ['-O2', '-g0'] if variable == 'LTCFLAGS' else ['-g0']
        result = [item for item in result if not item.startswith(variable + '=')]
        result.append(variable + '=' + shlex.join(flags))
    return result + ['--disable-debug', '--enable-optimizations', '--disable-qt-qml-debug']


def verify_release(build):
    config = shlex.split(subprocess.check_output(
        [str(build / 'config.status'), '--config'], cwd=build, text=True))
    assert '--disable-debug' in config and '--enable-debug' not in config, config
    assert '--disable-qt-qml-debug' in config, config
    assert re.search(r'^#define NDEBUG 1$', (build / 'config.h').read_text(), re.M), 'Assertions/debug profile remains enabled'
    for relative in ('Makefile', 'src/Makefile', 'modules/Makefile', 'modules/gui/qt/Makefile'):
        content = (build / relative).read_text()
        for variable in ('CFLAGS', 'CXXFLAGS'):
            flags = shlex.split(re.search(r'^' + variable + r' = (.*)$', content, re.M).group(1))
            optimization = [flag for flag in flags if flag.startswith('-O')]
            assert optimization and optimization[-1] == '-O3', (relative, variable, flags)
            assert '-g0' in flags and not any(flag.startswith('-g') and flag != '-g0' for flag in flags), (relative, variable, flags)
    return {'application_optimization': '-O3', 'debug_information': '-g0', 'assertions': False,
            'qml_debugger': False, 'diagnostic_hooks_are_a_separate_build_option': True}


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--write-object-profile', type=Path)
    mode.add_argument('--unchanged-since')
    parser.add_argument('--source', type=Path)
    args = parser.parse_args()
    if args.write_object_profile:
        verify_release(args.write_object_profile)
        print(write_object_profile(args.write_object_profile))
    else:
        assert args.source
        raise SystemExit(0 if configuration_sources_unchanged(args.source, args.unchanged_since) else 3)
