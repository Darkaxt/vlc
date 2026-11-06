#!/bin/sh
# Incremental player build after the pinned Windows baseline and SDK repairs.
# Finish consumers of the destination runtime before replacing its plugins.
set -eu
export PYTHONDONTWRITEBYTECODE=1
mode=${1:-normal}
source_root=${2:-/work/src}
build_root=${3:-/work/build/win64}
runtime=${4:-/scratch/runtime}
plugin_scope=maintained
mpv_flags=
case "$mode" in
    normal) flags= ;;
    diagnostics) flags=-DVLC_PLAYER_DIAGNOSTICS ;;
    normal-mpv) flags=; plugin_scope=mpv ;;
    diagnostics-mpv) flags=-DVLC_PLAYER_DIAGNOSTICS; plugin_scope=mpv ;;
    normal-mpv-full) flags=; plugin_scope=full ;;
    diagnostics-mpv-full) flags=-DVLC_PLAYER_DIAGNOSTICS; plugin_scope=full ;;
    normal-mpv-current) flags=; plugin_scope=current ;;
    diagnostics-mpv-current) flags=-DVLC_PLAYER_DIAGNOSTICS; plugin_scope=current ;;
    *) printf '%s\n' 'Expected normal, diagnostics, normal-mpv or diagnostics-mpv' >&2; exit 2 ;;
esac
if test -z "$flags"; then
    test -n "${VLC_PLAYER_RELEASE_SYMBOLS:-}"
fi
test -f "$build_root/config.status"
test -f "$source_root/modules/gui/qt/maininterface/player_video_backdrop.hpp"
python3 "$source_root/tools/windows-player/configure-player.py" \
    --source "$source_root" --build "$build_root" --verify-only
if test "$plugin_scope" = mpv || test "$plugin_scope" = full || test "$plugin_scope" = current; then
    # S8 changes the Qt frontend and hotkey dispatcher. Reuse the verified 1.0
    # package's other plugins only with the exact additive public-ABI contract.
    if test "$plugin_scope" = mpv; then
        python3 "$source_root/tools/windows-player/check-mpv-plugin-abi.py" --source "$source_root"
    fi
    if test "$plugin_scope" = current; then
        python3 "$source_root/tools/windows-player/verify-retained-plugin-cohort.py" \
            --source "$source_root" --build "$build_root" --runtime "$runtime"
    fi
    mpv_flags=-DVLC_MPV_RUNTIME_IDENTITY
    python3 "$source_root/tools/windows-player/stage-built-mpv-runtime.py" \
        --runtime "$runtime" --identity-header "$build_root/modules/gui/qt/mpv_runtime_identity.hpp"
fi
if test -z "$flags"; then
    python3 "$source_root/tools/windows-player/reconcile-source-catalogs.py" \
        --source "$source_root" --commit HEAD --restore-equivalent-generated \
        --output "$runtime/../catalogs-before-normal.json"
fi
# These generated headers belong to src's Automake graph, not an include
# subdirectory Makefile. Explicit targets also support the first cold build.
make -C "$build_root/src" -j1 ../include/vlc_about.h fourcc_tables.h stamp-revision
make -C "$build_root/compat" -j1 -f Makefile -f "$source_root/tools/windows-player/release-profile-objects.mk" all-am
make -C "$build_root/src" -j1 -f Makefile -f "$source_root/tools/windows-player/release-profile-objects.mk" libvlccore.la
x86_64-w64-mingw32-strip --strip-debug \
    -o "$runtime/libvlccore.dll" "$build_root/src/.libs/libvlccore.dll"
make -C "$build_root/lib" -j1 -f Makefile -f "$source_root/tools/windows-player/release-profile-objects.mk" libvlc.la
x86_64-w64-mingw32-strip --strip-debug \
    -o "$runtime/libvlc.dll" "$build_root/lib/.libs/libvlc.dll"
make -C "$build_root/bin" -j1 -f Makefile -f "$source_root/tools/windows-player/windows-icon.mk" -f "$source_root/tools/windows-player/release-profile-objects.mk" vlc.exe vlc-cache-gen.exe vlc-preparser.exe
cp "$source_root/share/icons/vlc.ico" "$runtime/vlc.ico"
cp "$source_root/modules/gui/qt/pixmaps/redesign/mpv.ico" "$runtime/mpv.ico"
# The shared Windows module resource belongs to the parent modules graph.
# Building Qt directly does not run that parent's BUILT_SOURCES target.
make -C "$build_root/modules" -j1 module.rc.lo
for executable in vlc.exe vlc-cache-gen.exe vlc-preparser.exe; do
    test -f "$build_root/bin/.libs/$executable"
    x86_64-w64-mingw32-strip --strip-debug \
        -o "$runtime/$executable" "$build_root/bin/.libs/$executable"
done
# Make does not track changed command-line preprocessor flags. Persist their
# exact signature and invalidate guarded sources once on a change. Keeping the
# mtimes after a failed make lets an identical retry reuse completed objects;
# unfinished objects still remain older than their required source inputs.
qt_flags_file="$build_root/player-qt-cppflags"
requested_qt_flags="$flags:$mpv_flags"
prior_qt_flags=
if test -f "$qt_flags_file"; then
    prior_qt_flags=$(cat "$qt_flags_file")
fi
if test "$prior_qt_flags" != "$requested_qt_flags"; then
    touch "$source_root/modules/gui/qt/maininterface/mainui.cpp" \
        "$source_root/modules/gui/qt/qt.cpp" \
        "$source_root/modules/gui/qt/dialogs/help/help.cpp" \
        "$source_root/modules/gui/qt/player/player_controller.cpp" \
        "$source_root/modules/gui/qt/player/player_controller_mpv.cpp" \
        "$source_root/modules/gui/qt/player/mpv_playback.cpp" \
        "$source_root/modules/gui/qt/maininterface/compositor_dcomp.cpp" \
        "$source_root/modules/gui/qt/maininterface/win32windoweffects_module.cpp" \
        "$source_root/modules/gui/qt/menus/menus.cpp" \
        "$source_root/modules/gui/qt/dialogs/preferences/preferences.cpp"
    # The diagnostic-only controller properties also change MOC output. Generate
    # that metadata with the selected flags, without retimestamping an unchanged
    # widely included source header and invalidating unrelated frontend objects.
    make -C "$build_root/modules/gui/qt" -j1 -f Makefile \
        -f "$source_root/tools/windows-player/qt-objects.mk" \
        PLAYER_DIAGNOSTICS_CPPFLAGS="$flags" PLAYER_MPV_CPPFLAGS="$mpv_flags" \
        qt-regenerate-player-moc
    printf '%s\n' "$requested_qt_flags" > "$qt_flags_file"
fi
compile_cache=${VLC_PLAYER_COMPILE_CACHE:-1}
case "$compile_cache" in
    1) ;;
    0) test -n "${VLC_PLAYER_COMPILE_CACHE_REASON:-}" ;;
    *) printf '%s\n' 'VLC_PLAYER_COMPILE_CACHE must be 0 or 1' >&2; exit 2 ;;
esac
if test "$plugin_scope" != maintained && test "$compile_cache" = 1; then
    # The SDK/header fan-out is expensive on the Windows-mounted build tree.
    # Cache only immutable inputs during compilation, within the same cgroup.
    # Keep the generated build directory writable and preserve every object.
    python3 "$source_root/tools/windows-player/cache-toolchain.py" create --qt-build
    qt_compile_result=0
    # Collect independent frontend compiler failures in this one assembly.
    # A failed object still fails the whole step; no Qt link or acceptance runs.
    make -C "$build_root/modules/gui/qt" -j1 -k -f Makefile \
        -f "$source_root/tools/windows-player/qt-objects.mk" \
        -f "$source_root/tools/windows-player/release-profile-objects.mk" \
        PLAYER_DIAGNOSTICS_CPPFLAGS="$flags" PLAYER_MPV_CPPFLAGS="$mpv_flags" \
        qt-player-objects || qt_compile_result=$?
    python3 "$source_root/tools/windows-player/cache-toolchain.py" release
    if test "$qt_compile_result" -ne 0; then
        exit "$qt_compile_result"
    fi
fi
# Cache omission changes no build target: the complete normal graph below
# still compiles any missing/outdated input before linking.
if test "$compile_cache" = 0; then
    printf 'Player compile caches omitted: %s\n' "$VLC_PLAYER_COMPILE_CACHE_REASON"
fi
make -C "$build_root/modules/gui/qt" -j1 -f Makefile \
    -f "$source_root/tools/windows-player/qt-objects.mk" \
    -f "$source_root/tools/windows-player/release-profile-objects.mk" \
    PLAYER_DIAGNOSTICS_CPPFLAGS="$flags" PLAYER_MPV_CPPFLAGS="$mpv_flags" qt-player-objects all-am
if test "$plugin_scope" = full; then
    # All configured modules use this source/header/core cohort after an ABI change.
    if test "$compile_cache" = 1; then
        python3 "$source_root/tools/windows-player/cache-toolchain.py" create
    fi
    module_result=0
    mkdir -p /work/upstream-codecs-1.1.1/link-maps
    # The separate dependency prefix changes both headers and archive inputs.
    # Invalidate these four header consumers once for each exact library cohort.
    python3 "$source_root/tools/windows-player/verify-upstream-codec-links.py" --prepare --source "$source_root" --build "$build_root"
    make -C "$build_root/modules" -j1 -f Makefile \
        -f "$source_root/tools/windows-player/upstream-codec-links.mk" \
        -f "$source_root/tools/windows-player/release-profile-objects.mk" \
        PLAYER_DIAGNOSTICS_CPPFLAGS="$flags" PLAYER_MPV_CPPFLAGS="$mpv_flags" all-am || module_result=$?
    if test "$compile_cache" = 1; then
        python3 "$source_root/tools/windows-player/cache-toolchain.py" release
    fi
    if test "$module_result" -ne 0; then
        exit "$module_result"
    fi
    python3 "$source_root/tools/windows-player/verify-upstream-codec-links.py" --source "$source_root" --build "$build_root" --runtime "$runtime"
    python3 "$source_root/tools/windows-player/stage-full-plugins.py" \
        --source "$source_root" --build "$build_root" --runtime "$runtime"
fi
if test "$plugin_scope" = current; then
    # This cohort has already passed the global release-profile rebuild. Only
    # Qt production sources changed, proven against the exact retained commit.
    python3 "$source_root/tools/windows-player/stage-full-plugins.py" \
        --source "$source_root" --build "$build_root" --runtime "$runtime" --retain-non-qt
fi
if test "$plugin_scope" != current; then
make -C "$build_root/modules" -j1 -f Makefile -f "$source_root/tools/windows-player/release-profile-objects.mk" libhotkeys_plugin.la
mkdir -p "$runtime/plugins/control"
x86_64-w64-mingw32-strip --strip-debug \
    -o "$runtime/plugins/control/libhotkeys_plugin.dll" \
    "$build_root/modules/.libs/libhotkeys_plugin.dll"
fi
if test "$plugin_scope" = maintained || test "$plugin_scope" = full; then
make -C "$build_root/modules" -j1 -f Makefile -f "$source_root/tools/windows-player/release-profile-objects.mk" libfreetype_plugin.la libequalizer_plugin.la libmedialibrary_plugin.la libstream_out_transcode_plugin.la libwasapi_plugin.la libskins2_plugin.la
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
    -o "$runtime/plugins/services_discovery/libupnp_plugin.dll" \
    "$build_root/modules/.libs/libupnp_plugin.dll"
fi
x86_64-w64-mingw32-strip --strip-debug \
    -o "$runtime/plugins/gui/libqt_plugin.dll" \
    "$build_root/modules/gui/qt/.libs/libqt_plugin.dll"
if test -z "$flags"; then
    python3 "$source_root/tools/windows-player/release_symbols.py" \
        --runtime "$runtime" --symbols "$VLC_PLAYER_RELEASE_SYMBOLS" --build "$build_root"
fi
sha256sum "$runtime/plugins/gui/libqt_plugin.dll" \
    "$runtime/plugins/control/libhotkeys_plugin.dll"
