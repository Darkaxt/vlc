#!/bin/sh
# Run inside the pinned Windows cross-build chroot used by the baseline recipe.
# Rebuild the same UPnP version with the fork's source patch; no SDK upgrade.
set -eu
source_root=/work/src
prefix=/work/build/contrib/x86_64-w64-mingw32
work=/work/upnp-rebuild-s2
archive=/scratch/cache/pupnp-release-1.14.31.tar.gz

(cd /scratch/cache && sha512sum --check "$source_root/contrib/src/upnp/SHA512SUMS")
test ! -e "$work"
mkdir -p "$work"
tar -xf "$archive" -C "$work"
source_dir="$work/pupnp-release-1.14.31"
for name in libtool-nostdlib-workaround.patch miniserver.patch \
    0001-Don-t-assume-strndup-to-be-missing-on-Windows.patch mingw-posix-aliases.patch; do
    (cd "$source_dir" && patch --batch -p1 < "$source_root/contrib/src/upnp/$name")
done
cat > "$work/toolchain.cmake" <<'CMAKE'
set(CMAKE_SYSTEM_NAME Windows)
set(CMAKE_C_COMPILER x86_64-w64-mingw32-gcc)
set(CMAKE_CXX_COMPILER x86_64-w64-mingw32-g++)
set(CMAKE_RC_COMPILER x86_64-w64-mingw32-windres)
set(CMAKE_FIND_ROOT_PATH /work/build/contrib/x86_64-w64-mingw32 /usr/x86_64-w64-mingw32)
set(CMAKE_FIND_ROOT_PATH_MODE_PROGRAM NEVER)
set(CMAKE_FIND_ROOT_PATH_MODE_LIBRARY ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_INCLUDE ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_PACKAGE ONLY)
set(CMAKE_C_FLAGS_INIT "-O2 -g -B/work/runtime-overlay")
set(CMAKE_CXX_FLAGS_INIT "-O2 -g -B/work/runtime-overlay")
set(CMAKE_EXE_LINKER_FLAGS_INIT "-L/work/runtime-overlay -static-libgcc")
CMAKE
cmake -S "$source_dir" -B "$work/build" -G Ninja \
    -DCMAKE_TOOLCHAIN_FILE="$work/toolchain.cmake" \
    -DCMAKE_INSTALL_PREFIX="$prefix" -DCMAKE_INSTALL_LIBDIR=lib \
    -DCMAKE_BUILD_TYPE=RelWithDebInfo -DUPNP_BUILD_SHARED=OFF \
    -DBUILD_TESTING=OFF -DUPNP_BUILD_SAMPLES=OFF -DUPNP_ENABLE_IPV6=ON
cmake --build "$work/build" --parallel 2
cmake --install "$work/build"

x86_64-w64-mingw32-gcc -B/work/runtime-overlay -L/work/runtime-overlay \
    -O2 -g -static-libgcc -I"$prefix/include/upnp" \
    "$source_root/tools/windows-player/upnp-url-check.c" \
    -L"$prefix/lib" -lupnp -lixml -lpthread -liphlpapi -lws2_32 \
    -o /scratch/runtime/upnp-url-check.exe
cd /work/build/win64/modules
make -j2 -W "$prefix/lib/libupnp.a" libupnp_plugin.la
cp .libs/libupnp_plugin.dll /scratch/runtime/plugins/services_discovery/libupnp_plugin.dll
