#!/bin/sh
# Initial application configuration in the already prepared pinned SDK.
# Run through with-isolated-toolchain.py and the installed WSL build gate.
set -eu
source_root=${1:-/work/src}
build_root=${2:-/work/build/win64}
runtime=${3:-/scratch/runtime}
prefix=/work/build/contrib/x86_64-w64-mingw32
crt=/work/runtime-crt-only
test ! -e "$build_root/config.status"
test -f "$runtime/vlc.exe"
test -f "$prefix/lib/libQt6Network.a"
test -f "$crt/dllcrt2.o"
test ! -e "$crt/libupnp.a"
test -x /usr/bin/autom4te
export JOBS=1 CMAKE_BUILD_PARALLEL_LEVEL=1 CARGO_BUILD_JOBS=1
export PATH="$prefix/../bin:$PATH"
export PKG_CONFIG_LIBDIR="$prefix/lib/pkgconfig"
export PKG_CONFIG_PATH="$prefix/lib/pkgconfig"
export PKG_CONFIG_SYSROOT_DIR=/
chmod +x "$source_root/tools/windows-player/autom4te-force.sh"
export AUTOM4TE="$source_root/tools/windows-player/autom4te-force.sh"
cd "$source_root"
./bootstrap
mkdir -p "$build_root"
cd "$build_root"
export CC="x86_64-w64-mingw32-gcc -B$crt/"
export CXX="x86_64-w64-mingw32-g++ -B$crt/"
export CPPFLAGS='-D__MSVCRT_VERSION__=0x700 -D_WIN32_WINNT=0x0601 -DWINVER=0x0601'
export CFLAGS="$CPPFLAGS -g"
export CXXFLAGS="$CPPFLAGS -g"
export LDFLAGS="-L$crt -static-libgcc"
"$source_root/extras/package/win32/configure.sh" \
    --host=x86_64-w64-mingw32 --with-contrib="$prefix" \
    --with-packagedir="$runtime" --enable-live555 --enable-dvdread \
    --enable-qt --enable-skins2 --enable-update-check --enable-caca \
    --enable-debug --enable-nls LTCFLAGS=-O0
# The first configure already uses the repaired CRT and target SDK. Reuse the
# maintained postconditions without paying for an identical second configure.
python3 "$source_root/tools/windows-player/configure-player.py" \
    --source "$source_root" --build "$build_root" --crt "$crt" --prefix "$prefix" --verify-only
printf '%s\n' 'Initial pinned player build configured; playback acceptance has not run.'
