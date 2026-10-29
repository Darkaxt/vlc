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
args = parser.parse_args()
assert (args.crt / 'dllcrt2.o').is_file()
assert not (args.crt / 'libupnp.a').exists(), 'Windows import libraries must not shadow contrib pupnp'
assert (args.prefix / 'lib/libQt6Network.a').is_file()
config = shlex.split(subprocess.check_output([str(args.build / 'config.status'), '--config'], cwd=args.build, text=True))
config = [entry for entry in config if entry not in ('--disable-nls', '--enable-nls')
          and not entry.startswith(('CC=', 'CXX=', 'LDFLAGS=', 'PKG_CONFIG_LIBDIR=', 'PKG_CONFIG_PATH=', 'PKG_CONFIG_SYSROOT_DIR='))]
config.append('--enable-nls')
makefile = (args.build / 'Makefile').read_text(encoding='utf-8')
old_flags = shlex.split(re.search(r'^LDFLAGS = (.*)$', makefile, re.M).group(1))
old_flags = [entry for entry in old_flags if entry not in ('-L/work/runtime-fixed/lib', f'-L{args.crt}', '-static-libgcc')]
config += [f'CC=x86_64-w64-mingw32-gcc -B{args.crt}/',
           f'CXX=x86_64-w64-mingw32-g++ -B{args.crt}/',
           f'LDFLAGS=-L{args.crt} -static-libgcc ' + shlex.join(old_flags)]
env = dict(os.environ, PKG_CONFIG_LIBDIR=str(args.prefix / 'lib/pkgconfig'),
           PKG_CONFIG_PATH=str(args.prefix / 'lib/pkgconfig'), PKG_CONFIG_SYSROOT_DIR='/')
subprocess.run([str(args.source / 'configure'), *config], cwd=args.build, env=env, check=True)
assert re.search(r'^#define ENABLE_NLS 1$', (args.build / 'config.h').read_text(), re.M), 'Production localization was not enabled'
predeps = re.findall(r'^predep_objects="(.*)"$', (args.build / 'libtool').read_text(encoding='utf-8'), re.M)
assert any(str(args.crt / 'dllcrt2.o') in value for value in predeps), predeps
print('Configured the maintained fork with the selected CRT and target pkg-config paths.')
