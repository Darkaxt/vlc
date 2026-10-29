#!/bin/sh
# Compile one native regression against the same source/SDK as the player.
set -eu
source_root=${1:-/work/src}
runtime=${2:-/scratch/runtime}
output=${3:-/scratch/wasapi-lifecycle-check.exe}
x86_64-w64-mingw32-gcc -std=gnu11 -O0 -g -DHAVE_CONFIG_H -D_WIN32_WINNT=0x0601 -static-libgcc \
    -ffunction-sections -fdata-sections -I/work/build/win64 -I"$source_root/include" \
    -I"$runtime/sdk/include" -I"$runtime/sdk/include/vlc/plugins" \
    "$source_root/tools/windows-player/wasapi-lifecycle-check.c" \
    -L"$runtime/sdk/lib" -Wl,--gc-sections -lvlc -lvlccore -lole32 -luuid -lksuser -o "$output"
sha256sum "$source_root/modules/audio_output/wasapi.c" \
    "$source_root/tools/windows-player/wasapi-lifecycle-check.c" > "$output.source-sha256"
