#!/bin/sh
# Add HTTPS support to the pinned Windows SDK using its exact Qt source/patches.
# The upstream binary contrib archive explicitly disabled QtNetwork.
set -eu
source_root=${1:-/work/src}
contrib_build=${2:-/work/build/contrib/contrib-win64}
archive_dir=${3:-/scratch/downloads}
test -f "$contrib_build/Makefile"
test -f "$archive_dir/qtbase-everywhere-src-6.8.3.tar.xz"
(cd "$archive_dir" && sha512sum --check "$source_root/contrib/src/qt/SHA512SUMS")
export JOBS=1 CMAKE_BUILD_PARALLEL_LEVEL=1 MESON_BUILD='-j 1' CARGO_BUILD_JOBS=1
# Use the maintained contrib dependency graph, Windows toolchain and existing
# Qt patches. Native build tools keep networking disabled. Target QtNetwork
# uses Schannel and Windows certificate validation; no OpenSSL DLL is added.
make -C "$contrib_build" -j1 TARBALLS="$archive_dir" .qt
prefix=/work/build/contrib/x86_64-w64-mingw32
test -f "$prefix/lib/libQt6Network.a"
test -f "$prefix/mkspecs/modules/qt_lib_network.pri"
grep -q 'schannel' "$prefix/mkspecs/modules/qt_lib_network.pri"
printf '%s\n' 'Matching QtNetwork/Schannel SDK build completed; native TLS verification remains required.'
