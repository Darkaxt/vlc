#!/bin/sh
# Select only the patched CRT from the pinned baseline's MinGW install.
# A full install also contains Windows import libraries that shadow contribs.
set -eu
source_dir=${1:-/work/runtime-fixed/lib}
target_dir=${2:-/work/runtime-crt-only}
test ! -e "$target_dir"
mkdir "$target_dir"
for name in crt2.o dllcrt2.o crtbegin.o crtend.o libmingw32.a libmingwex.a \
    libmingwthrd.a libmsvcrt.a libpthread.a libwinpthread.a; do
    test -f "$source_dir/$name"
    cp "$source_dir/$name" "$target_dir/$name"
done
test ! -e "$target_dir/libupnp.a"
