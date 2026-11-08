#!/bin/sh
# Test-only dependencies on the disposable hosted runner; no compiler/Qt SDK.
set -eu
test "${GITHUB_ACTIONS:-}" = true
test "$(uname -s)" = Linux
sudo -n apt-get update
sudo -n apt-get install -y --no-install-recommends python3-xlib xvfb xauth \
    openbox xcompmgr pulseaudio ffmpeg cpio rpm squashfs-tools snapd \
    libgl1-mesa-dri libegl1 libgl1
