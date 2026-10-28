"""Regenerate libtool's cached startup objects, then relink the Qt plugin only."""
import os
from pathlib import Path
import re
import shlex
import subprocess

build = Path('/work/build/win64')
os.chdir(build)
args = shlex.split(subprocess.check_output(['./config.status', '--config'], text=True))
args = [arg for arg in args if not arg.startswith(('CC=', 'CXX=', 'LDFLAGS='))]
original_flags = re.search(r'^LDFLAGS = (.*)$', (build / 'Makefile').read_text(), re.M).group(1)
args += ['CC=x86_64-w64-mingw32-gcc -B/work/runtime-fixed/lib/',
         'CXX=x86_64-w64-mingw32-g++ -B/work/runtime-fixed/lib/',
         f'LDFLAGS=-L/work/runtime-fixed/lib -static-libgcc {original_flags}']
subprocess.run(['/work/src/configure', *args], check=True)
libtool = (build / 'libtool').read_text()
predeps = re.findall(r'^predep_objects="(.*)"$', libtool, re.M)
assert any('/work/runtime-fixed/lib/dllcrt2.o' in value for value in predeps), predeps
subprocess.run(['make', '-C', 'modules/gui/qt', 'V=1', '-j1',
                '-W', 'libqt_plugin_la-qt.lo', 'libqt_plugin.la'], check=True)
plugin = build / 'modules/gui/qt/.libs/libqt_plugin.dll'
subprocess.run(['x86_64-w64-mingw32-objdump', '-p', str(plugin)], check=True)
subprocess.run(['cp', str(plugin), '/scratch/runtime/plugins/gui/libqt_plugin.dll'], check=True)
subprocess.run(['git', '-C', '/work/src', 'diff', '--exit-code'], check=True)
