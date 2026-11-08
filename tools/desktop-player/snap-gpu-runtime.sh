#!/bin/sh
# Use the connected platform graphics provider without bundling its drivers.
set -eu
if ! snapctl is-connected gpu-2404; then
    echo 'The graphics runtime is not connected. Connect modern-vlc-fork:gpu-2404 to mesa-2404.' >&2
    exit 1
fi
exec "$SNAP/gpu-2404/bin/gpu-2404-provider-wrapper" "$@"
