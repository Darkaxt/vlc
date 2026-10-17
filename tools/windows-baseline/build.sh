#!/bin/sh
# Run inside the pinned upstream CI filesystem, with /scratch on the E: task root.
set -eu
cd /work/src
test "$(git rev-parse HEAD)" = 392bc1d0abdb7396b6c97fef206efa1d23868e19
test "$(extras/ci/get-contrib-sha.sh win64)" = a5538c557d276378d5ba0f8f8010a8b87eaa6f78
git diff --exit-code
cd /scratch/downloads
printf '%s  %s\n' \
  7504d2d80be566f1caced13c8acf45af67059dc159d987a5d4e82c8912ed6fc4435fba714670e53c786bd83accf6c441f1ad345d3c97c04b5bf0ab60341f8d0d \
  vlc-contrib-x86_64-w64-mingw32-a5538c557d276378d5ba0f8f8010a8b87eaa6f78.tar.zst | sha512sum -c -
export VLC_PREBUILT_CONTRIBS_URL=file:///scratch/downloads/vlc-contrib-x86_64-w64-mingw32-a5538c557d276378d5ba0f8f8010a8b87eaa6f78.tar.zst
export JOBS=2 MESON_BUILD='-j 1' CMAKE_BUILD_PARALLEL_LEVEL=2
export CONFIGFLAGS='--with-packagedir=/scratch/runtime'
cd /work/build
date -u '+Build started %FT%TZ'
/work/src/extras/package/win32/build.sh -a x86_64 -p -o /scratch/runtime
date -u '+Build completed %FT%TZ'
git -C /work/src diff --exit-code
