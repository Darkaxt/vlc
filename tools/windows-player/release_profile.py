"""The Windows application release profile, independent of diagnostic hooks."""
import re
import shlex
import subprocess


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
