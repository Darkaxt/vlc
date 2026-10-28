#!/bin/sh
# Dependency-only backport for the June CI image's MinGW 12 process-exit deadlock.
set -eu
cd /scratch/downloads
printf '%s  %s\n' fa41d462041ed72e29a5101049e5991d4aea5c552fd75f7ac0074989fc54ceb7 mingw-runtime-source.tar.gz | sha256sum -c -
printf '%s  %s\n' 6b3bd4443d05257c6df80aec79d04014f4fc3665660a47171fa6b7701d65e9e4 /scratch/patches/mingw-v12-process-exit.patch | sha256sum -c -
mkdir /work/runtime-source /work/runtime-crt-build /work/runtime-pthread-build
tar -xf mingw-runtime-source.tar.gz -C /work/runtime-source --strip-components=1
cd /work/runtime-source
patch --fuzz=0 -p1 < /scratch/patches/mingw-v12-process-exit.patch
cd /work/runtime-crt-build
/work/runtime-source/mingw-w64-crt/configure --host=x86_64-w64-mingw32 --prefix=/work/runtime-fixed --with-sysroot=/usr/x86_64-w64-mingw32 --enable-lib64 --disable-lib32 --with-default-msvcrt=msvcrt
make -j1
make install
cd /work/runtime-pthread-build
/work/runtime-source/mingw-w64-libraries/winpthreads/configure --host=x86_64-w64-mingw32 --prefix=/work/runtime-fixed --disable-shared --enable-static
make -j1
make install
