#!/bin/sh
# Repair the pinned Qt timer/regex owner lifetimes in the existing target SDK.
set -eu
source_root=${1:-/work/src}
qt_root=${2:-/work/build/contrib/contrib-win64/qt}
test -f "$qt_root/vlc_build/CMakeCache.txt"
cd "$qt_root"
for name in 0001-Mingw-own-animation-timers-in-QThreadStorage.patch \
            0002-Mingw-own-regex-JIT-in-QThreadStorage.patch; do
    patch_file="$source_root/contrib/src/qt/$name"
    if ! patch --dry-run --reverse --fuzz=0 -p1 < "$patch_file" >/dev/null 2>&1; then
        patch --fuzz=0 -p1 < "$patch_file"
    fi
    patch --dry-run --reverse --fuzz=0 -p1 < "$patch_file"
done
cmake --build vlc_build --target Core --parallel 2
cmake --install vlc_build
