# MinGW 12 process-exit backport

[mingw-v12-process-exit.patch](mingw-v12-process-exit.patch) backports upstream MinGW-w64 commit [a556c6943c442465dc9a051bc6d3a6d452df4a1d](https://github.com/mingw-w64/mingw-w64/commit/a556c6943c442465dc9a051bc6d3a6d452df4a1d) onto the June VLC CI image's v12 runtime. Copyright and license remain those of the original MinGW-w64 files. The patch skips user TLS/static destructors when Windows is already terminating the process, while retaining cleanup for `FreeLibrary`. It changes no VLC application source.

Base: `https://codeload.github.com/mingw-w64/mingw-w64/tar.gz/refs/tags/v12.0.0`, SHA-256 `fa41d462041ed72e29a5101049e5991d4aea5c552fd75f7ac0074989fc54ceb7`.

Original upstream patch: `https://github.com/mingw-w64/mingw-w64/commit/a556c6943c442465dc9a051bc6d3a6d452df4a1d.patch`, SHA-256 `6a420d822ded83825683daefe50cbec5418e2fdcafc7a4423b477f34de75d616`.

The v12 backport SHA-256 is `6b3bd4443d05257c6df80aec79d04014f4fc3665660a47171fa6b7701d65e9e4`. Only the four upstream process-detach guards are ported; context differs from current MinGW. Apply with `patch --fuzz=0 -p1` to clean v12 sources. Build into the isolated `/work/runtime-fixed` prefix with [prepare-runtime.sh](../prepare-runtime.sh); do not replace host or system compiler runtimes.
