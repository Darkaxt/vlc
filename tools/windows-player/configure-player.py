"""Regenerate the pinned player configuration after its CRT/QtNetwork repairs."""
import argparse
import os
from pathlib import Path
import re
import shlex
import subprocess

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
if extra:
    assert (extra / 'lib/pkgconfig/medialibrary.pc').is_file()
assert (args.crt / 'dllcrt2.o').is_file()
assert not (args.crt / 'libupnp.a').exists(), 'Windows import libraries must not shadow contrib pupnp'
assert (args.prefix / 'lib/libQt6Network.a').is_file()
if not args.verify_only:
    config = shlex.split(subprocess.check_output([str(args.build / 'config.status'), '--config'], cwd=args.build, text=True))
    config = [entry for entry in config if entry not in ('--disable-nls', '--enable-nls')
              and not entry.startswith(('CC=', 'CXX=', 'CPPFLAGS=', 'LDFLAGS=', 'PKG_CONFIG_LIBDIR=', 'PKG_CONFIG_PATH=', 'PKG_CONFIG_SYSROOT_DIR='))]
    config.append('--enable-nls')
    makefile = (args.build / 'Makefile').read_text(encoding='utf-8')
    old_flags = shlex.split(re.search(r'^LDFLAGS = (.*)$', makefile, re.M).group(1))
    old_flags = [entry for entry in old_flags if entry not in ('-L/work/runtime-fixed/lib', f'-L{args.crt}', '-static-libgcc')]
    includes = shlex.split(re.search(r'^CPPFLAGS = (.*)$', makefile, re.M).group(1))
    includes = [item for item in includes if not item.startswith('-I$(top_')]
    if extra:
        includes = ['-I' + str(extra / 'include')] + [item for item in includes if item != '-I' + str(extra / 'include')]
        old_flags = ['-L' + str(extra / 'lib')] + [item for item in old_flags if item != '-L' + str(extra / 'lib')]
    config += [f'CC=x86_64-w64-mingw32-gcc -B{args.crt}/',
               f'CXX=x86_64-w64-mingw32-g++ -B{args.crt}/',
               'CPPFLAGS=' + shlex.join(includes),
               f'LDFLAGS=-L{args.crt} -static-libgcc ' + shlex.join(old_flags)]
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
            config.append(variable + '=-I' + str(extra / 'include') + ' ' + previous)
    subprocess.run([str(args.source / 'configure'), *config], cwd=args.build, env=env, check=True)
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
print('Verified the configured CRT, compiler flags and localization.' if args.verify_only else
      'Configured the maintained fork with the selected CRT and target pkg-config paths.')
