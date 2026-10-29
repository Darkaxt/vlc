#!/bin/sh
# Temporary WSL distributions may stop between commands. Own mounts and command
# in one lifetime rather than assuming mounts from an earlier invocation survive.
set -eu
stage_scratch=${VLC_STAGE_SCRATCH:?Set the exact registered Linux path to stage scratch}
test -d "$stage_scratch"
finish()
{
    result=$?
    trap - EXIT
    for path in /toolchain/etc/resolv.conf /toolchain/scratch /toolchain/sys /toolchain/dev /toolchain/proc; do
        if mountpoint -q "$path"; then
            umount "$path" || result=1
        fi
    done
    exit "$result"
}
trap finish EXIT
mountpoint -q /toolchain/proc || mount -t proc proc /toolchain/proc
mountpoint -q /toolchain/dev || mount --bind /dev /toolchain/dev
mountpoint -q /toolchain/sys || mount --bind /sys /toolchain/sys
mountpoint -q /toolchain/scratch || mount --bind "$stage_scratch" /toolchain/scratch
mountpoint -q /toolchain/etc/resolv.conf || mount --bind /etc/resolv.conf /toolchain/etc/resolv.conf
chroot /toolchain /usr/bin/env -i \
  PATH=/opt/tools/bin:/opt/tools/libexec:/opt/rust/cargo/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
  HOME=/work/home TMPDIR=/work/tmp LANG=en_US.UTF-8 \
  WINE_SDK_PATH=/usr/include/wine/wine/windows \
  RUST_HOME=/opt/rust RUSTUP_HOME=/opt/rust/rustup CARGO_HOME=/opt/rust/cargo \
  WINEPREFIX=/work/wine JOBS=1 CMAKE_BUILD_PARALLEL_LEVEL=1 CARGO_BUILD_JOBS=1 \
  "$@"
# The pinned Wine wait client crashes without a server. The enclosing installed
# WSL gate observes all descendants through real group-empty completion.
