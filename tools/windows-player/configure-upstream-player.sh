#!/bin/sh
# Reconcile changed Autotools/manifests without resetting the retained objects.
set -eu
source_root=${1:?source}
build_root=${2:?build}
export VLC_PLAYER_UPSTREAM_PREFIX=/work/upstream-medialibrary-0.14.1/prefix
export VLC_PLAYER_UPSTREAM_CODEC_PREFIX=/work/upstream-codecs-1.1.1/prefix
export PATH="/work/build/contrib/bin:$PATH"
export AUTOM4TE="$source_root/tools/windows-player/autom4te-force.sh"
test -x "$AUTOM4TE"
cd "$source_root"
/bin/sh ./bootstrap
python3 "$source_root/tools/windows-player/cache-toolchain.py" create --qt-build
configure_result=0
python3 "$source_root/tools/windows-player/configure-player.py" --source "$source_root" --build "$build_root" || configure_result=$?
python3 "$source_root/tools/windows-player/cache-toolchain.py" release
exit "$configure_result"
