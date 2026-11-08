#!/bin/sh
# Only the disposable Fedora container owns this package installation.
set -eu
dnf -y --setopt=max_parallel_downloads=1 install python3
exec python3 /probe/probe-fedora-rpm.py "$@"
