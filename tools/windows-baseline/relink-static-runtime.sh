#!/bin/sh
set -eu
cd /work/build/win64/modules
srt=$(sed -n 's/^SRT_LIBS = //p' Makefile | sed 's/-lgcc_s/-lgcc_eh/g')
x265=$(sed -n 's/^X265_LIBS = //p' Makefile | sed 's/-lgcc_s/-lgcc_eh/g')
gme=$(sed -n 's/^GME_LIBS = //p' Makefile | sed 's/-lgcc_s/-lgcc_eh/g')
make -j1 -W access/libaccess_srt_plugin_la-srt.lo -W access_output/libaccess_output_srt_plugin_la-srt.lo -W codec/libx265_plugin_la-x265.lo -W demux/gme.lo libaccess_srt_plugin.la libaccess_output_srt_plugin.la libx265_plugin.la libgme_plugin.la "SRT_LIBS=$srt" "LIBS_x265=$x265" "LIBS_gme=$gme" LDFLAGS=-static-libgcc
for pair in access/libaccess_srt_plugin access_output/libaccess_output_srt_plugin codec/libx265_plugin demux/libgme_plugin; do
 dir=${pair%/*}; name=${pair##*/}
 echo "$name IMPORTS"
 x86_64-w64-mingw32-objdump -p ".libs/$name.dll" | grep 'DLL Name'
 cp ".libs/$name.dll" "/scratch/runtime/plugins/$dir/$name.dll"
done
git -C /work/src diff --exit-code
