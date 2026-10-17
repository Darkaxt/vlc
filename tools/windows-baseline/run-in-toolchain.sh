#!/bin/sh
# Temporary WSL distributions may stop between commands. Own mounts and command
# in one lifetime rather than assuming mounts from an earlier invocation survive.
set -eu
mountpoint -q /toolchain/proc || mount -t proc proc /toolchain/proc
mountpoint -q /toolchain/dev || mount --bind /dev /toolchain/dev
mountpoint -q /toolchain/sys || mount --bind /sys /toolchain/sys
mountpoint -q /toolchain/scratch || mount --bind /mnt/e/Temp/vlc-s1-20261017 /toolchain/scratch
mountpoint -q /toolchain/etc/resolv.conf || mount --bind /etc/resolv.conf /toolchain/etc/resolv.conf
result=0
chroot /toolchain /usr/bin/env -i \
  PATH=/opt/tools/bin:/opt/tools/libexec:/opt/rust/cargo/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
  HOME=/work/home TMPDIR=/work/tmp LANG=en_US.UTF-8 \
  WINE_SDK_PATH=/usr/include/wine/wine/windows \
  RUST_HOME=/opt/rust RUSTUP_HOME=/opt/rust/rustup CARGO_HOME=/opt/rust/cargo \
  "$@" || result=$?
chroot /toolchain /usr/bin/env HOME=/work/home /usr/bin/wineserver -w || result=1
umount /toolchain/etc/resolv.conf /toolchain/scratch /toolchain/sys /toolchain/dev /toolchain/proc || result=1
exit "$result"
