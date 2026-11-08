"""Regenerate the pinned player configuration after its CRT/QtNetwork repairs."""
import argparse
import os
from pathlib import Path
import re
import shlex
import subprocess
from release_profile import release_arguments, verify_release, configure_base_flags

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--source', type=Path, default=Path('/work/src'))
parser.add_argument('--build', type=Path, default=Path('/work/build/win64'))
parser.add_argument('--crt', type=Path, default=Path('/work/runtime-crt-only'))
parser.add_argument('--prefix', type=Path, default=Path('/work/build/contrib/x86_64-w64-mingw32'))
parser.add_argument('--verify-only', action='store_true',
                    help='Check the already configured CRT/localization without running configure again')
args = parser.parse_args()
extra_prefix = os.environ.get('VLC_PLAYER_UPSTREAM_PREFIX')
extra = Path(extra_prefix) if extra_prefix else None
codec_prefix = os.environ.get('VLC_PLAYER_UPSTREAM_CODEC_PREFIX')
codecs = Path(codec_prefix) if codec_prefix else None
codec_modules = {}
for component, module, library in (('mpg123', 'libmpg123', 'libmpg123.a'),
        ('zvbi', 'zvbi-0.2', 'libzvbi.a'), ('aom', 'aom', 'libaom.a')):
    version = re.search(r'^' + component.upper() + r'_VERSION := ([0-9.]+)$',
        (args.source / 'contrib/src' / component / 'rules.mak').read_text(), re.M).group(1)
    codec_modules[component.upper()] = (module, version, library)
if extra:
    assert (extra / 'lib/pkgconfig/medialibrary.pc').is_file()
assert (args.crt / 'dllcrt2.o').is_file()
assert not (args.crt / 'libupnp.a').exists(), 'Windows import libraries must not shadow contrib pupnp'
assert (args.prefix / 'lib/libQt6Network.a').is_file()
if not args.verify_only:
    config = shlex.split(subprocess.check_output([str(args.build / 'config.status'), '--config'], cwd=args.build, text=True))
    base_flags = configure_base_flags(config, args.prefix)
    config = [entry for entry in config if entry not in ('--disable-nls', '--enable-nls')
              and not entry.startswith(('CC=', 'CXX=', 'CPPFLAGS=', 'LDFLAGS=', 'PKG_CONFIG_LIBDIR=', 'PKG_CONFIG_PATH=', 'PKG_CONFIG_SYSROOT_DIR='))]
    config.append('--enable-nls')
    old_flags = base_flags['LDFLAGS']
    old_flags = [entry for entry in old_flags if entry not in ('-L/work/runtime-fixed/lib', f'-L{args.crt}', '-static-libgcc')]
    includes = base_flags['CPPFLAGS']
    includes = [item for item in includes if not item.startswith('-I$(top_')]
    if extra:
        includes = ['-I' + str(extra / 'include')] + [item for item in includes if item != '-I' + str(extra / 'include')]
        old_flags = ['-L' + str(extra / 'lib')] + [item for item in old_flags if item != '-L' + str(extra / 'lib')]
    if codecs:
        includes = ['-I' + str(codecs / 'include')] + [item for item in includes if item != '-I' + str(codecs / 'include')]
        old_flags = ['-L' + str(codecs / 'lib')] + [item for item in old_flags if item != '-L' + str(codecs / 'lib')]
        config = [entry for entry in config if not entry.startswith('--with-mad=')]
        config.append('--with-mad=' + str(codecs))
    config += [f'CC=x86_64-w64-mingw32-gcc -B{args.crt}/',
               f'CXX=x86_64-w64-mingw32-g++ -B{args.crt}/',
               'CPPFLAGS=' + shlex.join(includes),
               f'LDFLAGS=-L{args.crt} -static-libgcc ' + shlex.join(old_flags)]
    for variable in ('CFLAGS', 'CXXFLAGS', 'OBJCFLAGS'):
        config = [entry for entry in config if not entry.startswith(variable + '=')]
        config.append(variable + '=' + shlex.join(base_flags[variable]))
    env = dict(os.environ, PKG_CONFIG_LIBDIR=str(args.prefix / 'lib/pkgconfig'),
               PKG_CONFIG_PATH=str(args.prefix / 'lib/pkgconfig'), PKG_CONFIG_SYSROOT_DIR='/')
    if extra:
        env['PKG_CONFIG_PATH'] = str(extra / 'lib/pkgconfig') + ':' + env['PKG_CONFIG_PATH']
        env['PKG_CONFIG_LIBDIR'] = env['PKG_CONFIG_PATH']
        version = subprocess.check_output(['pkg-config', '--modversion', 'medialibrary'], env=env, text=True).strip()
        assert version == '0.14.1', version
        # configure prepends the SDK's pkg-config directory. Bind these two
        # explicit module flags to the independently verified override instead.
        for variable, option in (('MEDIALIBRARY_CFLAGS', '--cflags'), ('MEDIALIBRARY_LIBS', '--libs')):
            config = [entry for entry in config if not entry.startswith(variable + '=')]
            value = subprocess.check_output(['pkg-config', '--static', option, 'medialibrary'], env=env, text=True).strip()
            config.append(variable + '=' + value)
        for variable in ('CFLAGS', 'CXXFLAGS'):
            previous = next((entry.split('=', 1)[1] for entry in config if entry.startswith(variable + '=')), '')
            config = [entry for entry in config if not entry.startswith(variable + '=')]
            include = '-I' + str(extra / 'include')
            config.append(variable + '=' + shlex.join([include] +
                [item for item in shlex.split(previous) if item != include]))
    if codecs:
        env['PKG_CONFIG_PATH'] = str(codecs / 'lib/pkgconfig') + ':' + env['PKG_CONFIG_PATH']
        env['PKG_CONFIG_LIBDIR'] = env['PKG_CONFIG_PATH']
        for variable, (module, expected_version, library) in codec_modules.items():
            version = subprocess.check_output(['pkg-config', '--modversion', module], env=env, text=True).strip()
            assert version == expected_version, (module, version)
            for suffix, option in (('_CFLAGS', '--cflags'), ('_LIBS', '--libs')):
                key = variable + suffix
                config = [entry for entry in config if not entry.startswith(key + '=')]
                value = subprocess.check_output(['pkg-config', '--static', option, module], env=env, text=True).strip()
                if suffix == '_LIBS':
                    # Bind the actual archive, independent of SDK -L ordering.
                    flag = '-l' + library.removeprefix('lib').removesuffix('.a')
                    parts = shlex.split(value)
                    assert flag in parts, (module, parts)
                    value = shlex.join([str(codecs / 'lib' / library) if part == flag else part for part in parts])
                config.append(key + '=' + value)
    config = release_arguments(config)
    subprocess.run([str(args.source / 'configure'), *config], cwd=args.build, env=env, check=True)
verify_release(args.build)
assert re.search(r'^#define ENABLE_NLS 1$', (args.build / 'config.h').read_text(), re.M), 'Production localization was not enabled'
predeps = re.findall(r'^predep_objects="(.*)"$', (args.build / 'libtool').read_text(encoding='utf-8'), re.M)
assert any(str(args.crt / 'dllcrt2.o') in value for value in predeps), predeps
makefile = (args.build / 'Makefile').read_text(encoding='utf-8')
for variable, compiler in (('CC', 'gcc'), ('CXX', 'g++')):
    command = shlex.split(re.search(r'^' + variable + r' = (.*)$', makefile, re.M).group(1))
    assert command[:2] == ['x86_64-w64-mingw32-' + compiler, '-B' + str(args.crt) + '/'], command
linker_flags = shlex.split(re.search(r'^LDFLAGS = (.*)$', makefile, re.M).group(1))
assert '-L' + str(args.crt) in linker_flags and '-static-libgcc' in linker_flags
assert '-L/work/runtime-fixed/lib' not in linker_flags
if extra:
    assert re.search(r'^LTLIBmedialibrary = libmedialibrary_plugin.la$', makefile, re.M), 'Required library plugin was disabled'
    modules = (args.build / 'modules/Makefile').read_text()
    for variable, expected in (('MEDIALIBRARY_CFLAGS', '-I' + str(extra / 'include')),
                               ('MEDIALIBRARY_LIBS', '-L' + str(extra / 'lib'))):
        values = shlex.split(re.search(r'^' + variable + r' = (.*)$', modules, re.M).group(1))
        assert values[0] == expected, (variable, values)
if codecs:
    modules = (args.build / 'modules/Makefile').read_text()
    for variable, (_, _, library) in codec_modules.items():
        assert re.search(r'^' + variable + r'_CFLAGS = -I' + re.escape(str(codecs / 'include')),
            modules, re.M), variable
        libs = shlex.split(re.search(r'^' + variable + r'_LIBS = (.*)$', modules, re.M).group(1))
        assert str(codecs / 'lib' / library) in libs, (variable, libs)
    assert re.search(r'^MAD_CFLAGS = -I' + re.escape(str(codecs / 'include')), modules, re.M)
    assert re.search(r'^MAD_LIBS = -L' + re.escape(str(codecs / 'lib')) + r' -lmad$', modules, re.M)
print('Verified the configured CRT, compiler flags and localization.' if args.verify_only else
      'Configured the maintained fork with the selected CRT and target pkg-config paths.')
