#!/bin/sh
# Stable entry point for the named, logged, resumable S8 compilation pipeline.
set -eu
source_root=${1:-/work/src}
build_root=${2:-/work/build/win64}
runtime=${3:-/scratch/runtime}
case "${4:-build}" in
    build) start=sdk-network ;;
    shaders) start=shaderc ;;
    placebo) start=libplacebo ;;
    spirv-cross|ffmpeg|mpv|player) start=$4 ;;
    normal)
        exec python3 -B "$source_root/tools/windows-player/compilation-pipeline.py" \
            --source "$source_root" --build "$build_root" --runtime "$runtime" \
            --from-step player --mode normal-mpv ;;
    resume)
        exec python3 -B "$source_root/tools/windows-player/compilation-pipeline.py" \
            --source "$source_root" --build "$build_root" --runtime "$runtime" --resume ;;
    *) printf '%s\n' "Unsupported pipeline entry: $4" >&2; exit 2 ;;
esac
exec python3 -B "$source_root/tools/windows-player/compilation-pipeline.py" \
    --source "$source_root" --build "$build_root" --runtime "$runtime" --from-step "$start"
