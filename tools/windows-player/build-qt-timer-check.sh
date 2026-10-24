#!/bin/sh
# Build the native lifetime regression against the same static SDK/CRT as VLC.
set -eu
source_root=${1:-/work/src}
prefix=${2:-/work/build/contrib/x86_64-w64-mingw32}
output=${3:-/scratch/qt-timer-check.exe}
crt=${4:-/work/runtime-crt-only}
x86_64-w64-mingw32-g++ -B"$crt/" -L"$crt" -std=c++17 -O0 -g -static \
    -I"$prefix/include/QtCore/6.8.3" -I"$prefix/include/QtCore/6.8.3/QtCore" \
    -I"$prefix/include" -I"$prefix/include/QtCore" -DQT_CORE_LIB -DUNICODE -D_UNICODE \
    "$source_root/tools/windows-player/qt-timer-check.cpp" -Wl,--wrap=free \
    -Wl,--wrap=pcre2_jit_stack_create_16 -Wl,--wrap=pcre2_jit_stack_free_16 \
    -L"$prefix/lib" -lQt6Core -lz -lmpr -luserenv -ladvapi32 -lauthz -lkernel32 \
    -lnetapi32 -lole32 -luser32 -luuid -lversion -lwinmm -lws2_32 -lQt6BundledPcre2 \
    -lshell32 -pthread -o "$output"
