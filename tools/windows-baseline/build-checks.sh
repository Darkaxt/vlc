#!/bin/sh
set -eu
x86_64-w64-mingw32-gcc -std=c11 -D_WIN32_WINNT=0x0601 \
  -I/scratch/runtime/sdk/include /scratch/playback-check.c \
  -L/scratch/runtime/sdk/lib -lvlc -o /scratch/runtime/playback-check.exe
x86_64-w64-mingw32-gcc -std=c11 -D_WIN32_WINNT=0x0601 \
  -I/scratch/runtime/sdk/include -I/scratch/runtime/sdk/include/vlc/plugins \
  /scratch/inventory.c -L/scratch/runtime/sdk/lib -lvlc -lvlccore \
  -o /scratch/runtime/inventory.exe
