#!/bin/sh
# Incremental S2 build after the pinned Windows baseline and UPnP repair.
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
# Make does not track changed preprocessor flags. Rebuild both guarded units.
make -C "$build_root/modules/gui/qt" -j2 \
    -W "$source_root/modules/gui/qt/maininterface/mainui.cpp" \
    -W "$source_root/modules/gui/qt/maininterface/compositor_dcomp.cpp" \
    PLAYER_DIAGNOSTICS_CPPFLAGS="$flags" libqt_plugin.la
mkdir -p "$runtime/plugins/gui" "$runtime/plugins/services_discovery"
x86_64-w64-mingw32-strip --strip-debug \
    -o "$runtime/plugins/gui/libqt_plugin.dll" \
    "$build_root/modules/gui/qt/.libs/libqt_plugin.dll"
x86_64-w64-mingw32-strip --strip-debug \
    -o "$runtime/plugins/services_discovery/libupnp_plugin.dll" \
    "$build_root/modules/.libs/libupnp_plugin.dll"
sha256sum "$runtime/plugins/gui/libqt_plugin.dll" \
    "$runtime/plugins/services_discovery/libupnp_plugin.dll"
