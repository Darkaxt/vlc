#!/bin/sh
# Incremental player build after the pinned Windows baseline and SDK repairs.
# Finish consumers of the destination runtime before replacing its plugins.
set -eu
mode=${1:-normal}
source_root=${2:-/work/src}
build_root=${3:-/work/build/win64}
runtime=${4:-/scratch/runtime}
case "$mode" in
    normal) flags= ;;
    diagnostics) flags=-DVLC_PLAYER_DIAGNOSTICS ;;
    *) printf '%s\n' 'Expected normal or diagnostics' >&2; exit 2 ;;
esac
test -f "$build_root/config.status"
test -f "$source_root/modules/gui/qt/maininterface/player_video_backdrop.hpp"
# Make does not track changed preprocessor flags. Rebuild all guarded units.
make -C "$build_root/modules/gui/qt" -j2 \
    -W "$source_root/modules/gui/qt/maininterface/mainui.cpp" \
    -W "$source_root/modules/gui/qt/player/player_controller.cpp" \
    -W "$source_root/modules/gui/qt/maininterface/compositor_dcomp.cpp" \
    PLAYER_DIAGNOSTICS_CPPFLAGS="$flags" libqt_plugin.la
make -C "$build_root/modules" -j2 libfreetype_plugin.la libequalizer_plugin.la
mkdir -p "$runtime/plugins/gui" "$runtime/plugins/services_discovery" "$runtime/plugins/text_renderer" "$runtime/plugins/audio_filter"
x86_64-w64-mingw32-strip --strip-debug \
    -o "$runtime/plugins/audio_filter/libequalizer_plugin.dll" \
    "$build_root/modules/.libs/libequalizer_plugin.dll"
x86_64-w64-mingw32-strip --strip-debug \
    -o "$runtime/plugins/text_renderer/libfreetype_plugin.dll" \
    "$build_root/modules/.libs/libfreetype_plugin.dll"
x86_64-w64-mingw32-strip --strip-debug \
    -o "$runtime/plugins/gui/libqt_plugin.dll" \
    "$build_root/modules/gui/qt/.libs/libqt_plugin.dll"
x86_64-w64-mingw32-strip --strip-debug \
    -o "$runtime/plugins/services_discovery/libupnp_plugin.dll" \
    "$build_root/modules/.libs/libupnp_plugin.dll"
sha256sum "$runtime/plugins/gui/libqt_plugin.dll" \
    "$runtime/plugins/services_discovery/libupnp_plugin.dll"
