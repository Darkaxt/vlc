#!/bin/sh
# Fetch corresponding sources for the configured Windows contrib selection.
# Run inside the pinned chroot, under the installed WSL gate. No compilation.
set -eu
contrib_build=${1:-/work/build/contrib/contrib-win64}
destination=${2:-/scratch/contrib-sources}
evidence=${3:-/scratch/evidence/dependency-sources}
test -f "$contrib_build/Makefile"
mkdir -p "$destination" "$evidence"
# Found packages are supplied by the prebuilt SDK, but their sources must still
# accompany distribution. Override only detection, keeping the same platform,
# enabled packages, versions, upstream rules and source checksum checks.
# The pinned Qt 6.8.3 modules have moved from official_releases to Qt's
# official archive. Change only the mirror base, retaining exact source hashes.
qt_source_base=https://download.qt.io/archive/qt/6.8
make -C "$contrib_build" -j1 PKGS_FOUND= QT="$qt_source_base" TARBALLS="$destination" list > "$evidence/selection.txt"
make -C "$contrib_build" -j1 PKGS_FOUND= QT="$qt_source_base" TARBALLS="$destination" fetch
printf '%s\n' 'Configured Windows contrib source downloads/checks completed.'
