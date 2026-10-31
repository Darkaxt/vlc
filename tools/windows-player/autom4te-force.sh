#!/bin/sh
# Executable AUTOM4TE values are required by Autoconf's Perl and shell callers.
# The pinned SDK provides this exact native tool; force regenerates stale traces.
exec /usr/bin/autom4te --force "$@"
