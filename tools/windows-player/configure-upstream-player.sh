#!/bin/sh
# Reconcile changed Autotools/manifests without resetting the retained objects.
set -eu
source_root=${1:?source}
build_root=${2:?build}
previous_source=${3:-}
export VLC_PLAYER_UPSTREAM_PREFIX=/work/upstream-medialibrary-0.14.1/prefix
export VLC_PLAYER_UPSTREAM_CODEC_PREFIX=/work/upstream-codecs-1.1.1/prefix
export PATH="/work/build/contrib/bin:$PATH"
export AUTOM4TE="$source_root/tools/windows-player/autom4te-force.sh"
test -x "$AUTOM4TE"
if test -n "$previous_source"; then
    changed=0
    python3 "$source_root/tools/windows-player/release_profile.py" \
        --source "$source_root" --unchanged-since "$previous_source" || changed=$?
    case "$changed" in
        0)
            python3 "$source_root/tools/windows-player/configure-player.py" \
                --source "$source_root" --build "$build_root" --verify-only
            exit 0 ;;
        3) ;; # Actual configuration inputs changed; preserve objects and reconcile.
        *) exit "$changed" ;;
    esac
fi
cd "$source_root"
/bin/sh ./bootstrap
cache_enabled=${VLC_PLAYER_COMPILE_CACHE:-1}
if test "$cache_enabled" != 0; then
    python3 "$source_root/tools/windows-player/cache-toolchain.py" create --qt-build
else
    test -n "${VLC_PLAYER_COMPILE_CACHE_REASON:-}"
fi
configure_result=0
python3 "$source_root/tools/windows-player/configure-player.py" --source "$source_root" --build "$build_root" || configure_result=$?
if test "$cache_enabled" != 0; then
    python3 "$source_root/tools/windows-player/cache-toolchain.py" release
fi
exit "$configure_result"
