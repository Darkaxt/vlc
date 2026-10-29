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
if test "$mode" = normal; then
    python3 "$source_root/tools/windows-player/reconcile-source-catalogs.py" \
        --source "$source_root" --commit HEAD --restore-equivalent-generated \
        --output "$runtime/../catalogs-before-normal.json"
fi
make -C "$build_root/src" -j1 stamp-revision
make -C "$build_root/src" -j1 libvlccore.la
x86_64-w64-mingw32-strip --strip-debug \
    -o "$runtime/libvlccore.dll" "$build_root/src/.libs/libvlccore.dll"
make -C "$build_root/lib" -j1 libvlc.la
x86_64-w64-mingw32-strip --strip-debug \
    -o "$runtime/libvlc.dll" "$build_root/lib/.libs/libvlc.dll"
make -C "$build_root/bin" -j1 vlc.exe vlc-cache-gen.exe vlc-preparser.exe
for executable in vlc.exe vlc-cache-gen.exe vlc-preparser.exe; do
    test -f "$build_root/bin/.libs/$executable"
    x86_64-w64-mingw32-strip --strip-debug \
        -o "$runtime/$executable" "$build_root/bin/.libs/$executable"
done
# Make does not track changed preprocessor flags. Rebuild all guarded units.
make -C "$build_root/modules/gui/qt" -j1 \
    -W "$source_root/modules/gui/qt/maininterface/mainui.cpp" \
    -W "$source_root/modules/gui/qt/player/player_controller.cpp" \
    -W "$source_root/modules/gui/qt/maininterface/compositor_dcomp.cpp" \
    -W "$source_root/modules/gui/qt/dialogs/preferences/preferences.cpp" \
    PLAYER_DIAGNOSTICS_CPPFLAGS="$flags" libqt_plugin.la
make -C "$build_root/modules" -j1 libfreetype_plugin.la libequalizer_plugin.la libmedialibrary_plugin.la libstream_out_transcode_plugin.la libwasapi_plugin.la libskins2_plugin.la
make -C "$build_root/share" -j1 lua/extensions/VLSub.luac skins2/default.vlt
# Compile against the existing template without updating tracked translator
# sources. GNU gettext still performs its build-only --for-msgfmt merge.
make -C "$build_root/po" -j1 PO_DEPENDS_ON_POT=no install-data "localedir=$runtime/locale"
test -f "$runtime/locale/el/LC_MESSAGES/vlc.mo"
mkdir -p "$runtime/plugins/gui" "$runtime/plugins/services_discovery" "$runtime/plugins/text_renderer" "$runtime/plugins/audio_filter" "$runtime/plugins/misc" "$runtime/plugins/stream_out"
mkdir -p "$runtime/lua/extensions"
mkdir -p "$runtime/plugins/audio_output" "$runtime/skins"
cp "$build_root/share/lua/extensions/VLSub.luac" "$runtime/lua/extensions/VLSub.luac"
cp "$build_root/share/skins2/default.vlt" "$runtime/skins/default.vlt"
x86_64-w64-mingw32-strip --strip-debug \
    -o "$runtime/plugins/audio_output/libwasapi_plugin.dll" \
    "$build_root/modules/.libs/libwasapi_plugin.dll"
x86_64-w64-mingw32-strip --strip-debug \
    -o "$runtime/plugins/gui/libskins2_plugin.dll" \
    "$build_root/modules/.libs/libskins2_plugin.dll"
x86_64-w64-mingw32-strip --strip-debug \
    -o "$runtime/plugins/stream_out/libstream_out_transcode_plugin.dll" \
    "$build_root/modules/.libs/libstream_out_transcode_plugin.dll"
x86_64-w64-mingw32-strip --strip-debug \
    -o "$runtime/plugins/misc/libmedialibrary_plugin.dll" \
    "$build_root/modules/.libs/libmedialibrary_plugin.dll"
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
