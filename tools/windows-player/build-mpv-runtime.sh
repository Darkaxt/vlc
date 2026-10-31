#!/bin/sh
# Source-bound Windows libmpv, separate from the VLC contrib SDK and FFmpeg.
# Run through with-isolated-toolchain.py and the installed bounded WSL gate.
# A failed phase resumes in its existing build tree; setup never overwrites it.
set -eu
phase=${1:?Supply build, setup, shaders, shaderc, spirv-cross, placebo, ffmpeg or mpv}
sdk=/work/build/contrib/x86_64-w64-mingw32
crt=/work/runtime-crt-only
base=/work/mpv-runtime
prefix=$base/prefix
export JOBS=1 CMAKE_BUILD_PARALLEL_LEVEL=1 CARGO_BUILD_JOBS=1
export PKG_CONFIG_LIBDIR="$prefix/lib/pkgconfig:$sdk/lib/pkgconfig"
export PKG_CONFIG_PATH="$PKG_CONFIG_LIBDIR"
export PATH="$sdk/../bin:$PATH"
test -f "$crt/dllcrt2.o"
test -f "$sdk/lib/libass.a"

case "$phase" in
build)
    # One supervised dependency build. A failure stops at its actual phase;
    # resume that named phase after correction instead of restarting setup.
    for next in setup shaders placebo ffmpeg mpv; do
        /bin/sh "$0" "$next"
    done
    ;;
setup)
    test ! -e "$base"
    printf '%s  %s\n' fc6f68dc77884c7f07a997219ef76c7809e868956d14e7d41d64cb8f1d5c6d28 /scratch/mpv-wasapi-session.patch | sha256sum -c -
    mkdir -p "$base/source" "$prefix"
    cd /scratch/mpv-source-inputs
    printf '%s  %s\n' \
      562674ce7a0f6ac0681291037abc4c8595e0d1202d86d27eb341113eb7d984ba mpv-e471496c56f0f49c133bd88b50aed62b845f1909.tar.gz \
      c1b0fd16eae5b06838e456ab58924553a94aba087e3ad2e7d983c288003d6f6a FFmpeg-9a861e9687d30e657d59521817cad18405995983.tar.gz \
      6f2616cffcbb0fbd4109a80fb7bc9ce59e13ba24749ad4a3085bd80f90cb542d libplacebo-285d1cc8af2ab79b72ac662eb09736de8c12392b.tar.gz \
      2b132274539286e41f37857cac22aa8441d21bd86d55de825a3342b149f66801 fast_float-97b54ca9e75f5303507699d27c6b4f4efe4641a1.tar.gz \
      e6d6492a363cdef271e466f67cae3ad0d48f7e748491b8e2fe51424c08e391ad shaderc-2c8cae778eec0283b44acbe7ed1a386865d78799.tar.gz \
      c167b2474af06cbab93abae8249efaf88fb79a09f30488e2a24d399e4258ce7a glslang-168d452a4f460d24b588fed08477a81c44ee27a1.tar.gz \
      232899f1ad4104fb5bc377b94596c7621575eee62ad9a9e8f929b63a7dd8a7ad SPIRV-Headers-29981f65241605e08b0ede4cfeb999fe3b723c6a.tar.gz \
      05d8af89737bde57571c48dbd36714c9f520a69623e14de72c3be6b600e277d6 SPIRV-Tools-b707790a898e44038547df54580022fc1cf89c3d.tar.gz \
      3d54721c7db5cf955c6b5f01be2702ea1154c86d5ef322685a3738788a093b3e SPIRV-Cross-7affe74d77f93a622bb5002789d5332d32e512ee.tar.gz | sha256sum -c -
    for item in \
      mpv:e471496c56f0f49c133bd88b50aed62b845f1909 \
      FFmpeg:9a861e9687d30e657d59521817cad18405995983 \
      libplacebo:285d1cc8af2ab79b72ac662eb09736de8c12392b \
      shaderc:2c8cae778eec0283b44acbe7ed1a386865d78799 \
      SPIRV-Cross:7affe74d77f93a622bb5002789d5332d32e512ee; do
        name=${item%%:*}
        commit=${item#*:}
        mkdir "$base/source/$name"
        tar -xzf "$name-$commit.tar.gz" --strip-components=1 -C "$base/source/$name"
    done
    mkdir -p "$base/source/libplacebo/3rdparty/fast_float"
    tar -xzf fast_float-97b54ca9e75f5303507699d27c6b4f4efe4641a1.tar.gz \
      --strip-components=1 -C "$base/source/libplacebo/3rdparty/fast_float"
    for item in \
      glslang:168d452a4f460d24b588fed08477a81c44ee27a1:glslang \
      SPIRV-Headers:29981f65241605e08b0ede4cfeb999fe3b723c6a:spirv-headers \
      SPIRV-Tools:b707790a898e44038547df54580022fc1cf89c3d:spirv-tools; do
        name=${item%%:*}
        rest=${item#*:}
        commit=${rest%%:*}
        target=$base/source/shaderc/third_party/${rest#*:}
        mkdir -p "$target"
        tar -xzf "$name-$commit.tar.gz" --strip-components=1 -C "$target"
    done
    git -C "$base/source/mpv" apply --check /scratch/mpv-wasapi-session.patch
    git -C "$base/source/mpv" apply /scratch/mpv-wasapi-session.patch
    cp /scratch/mpv-wasapi-session.patch "$base/mpv-wasapi-session.patch"
    cat > "$base/cross.meson" <<EOF
[binaries]
c = ['x86_64-w64-mingw32-gcc', '-B$crt/', '-B$prefix/lib/', '-B$sdk/lib/']
cpp = ['x86_64-w64-mingw32-g++', '-B$crt/', '-B$prefix/lib/', '-B$sdk/lib/']
ar = 'x86_64-w64-mingw32-gcc-ar'
strip = 'x86_64-w64-mingw32-strip'
pkg-config = 'pkg-config'
windres = 'x86_64-w64-mingw32-windres'
dlltool = 'x86_64-w64-mingw32-dlltool'
cmake = '/usr/bin/cmake'
[properties]
needs_exe_wrapper = true
[host_machine]
system = 'windows'
cpu_family = 'x86_64'
cpu = 'x86_64'
endian = 'little'
[built-in options]
c_args = ['-I$prefix/include', '-isystem$sdk/include']
cpp_args = ['-I$prefix/include', '-isystem$sdk/include']
c_link_args = ['-L$prefix/lib', '-L$sdk/lib', '-L$crt', '-static', '-static-libgcc', '-static-libstdc++', '-pthread']
cpp_link_args = ['-L$prefix/lib', '-L$sdk/lib', '-L$crt', '-static', '-static-libgcc', '-static-libstdc++', '-pthread']
EOF
    cat > "$base/cross.cmake" <<EOF
set(CMAKE_SYSTEM_NAME Windows)
set(CMAKE_SYSTEM_PROCESSOR x86_64)
set(CMAKE_C_COMPILER x86_64-w64-mingw32-gcc)
set(CMAKE_CXX_COMPILER x86_64-w64-mingw32-g++)
set(CMAKE_RC_COMPILER x86_64-w64-mingw32-windres)
set(CMAKE_C_FLAGS_INIT "-B$crt/ -O2")
set(CMAKE_CXX_FLAGS_INIT "-B$crt/ -O2")
set(CMAKE_SHARED_LINKER_FLAGS_INIT "-B$crt/ -L$crt -static-libgcc -static-libstdc++ -pthread")
set(CMAKE_EXE_LINKER_FLAGS_INIT "-B$crt/ -L$crt -static-libgcc -static-libstdc++ -pthread")
set(CMAKE_FIND_ROOT_PATH "$prefix;$sdk")
set(CMAKE_FIND_ROOT_PATH_MODE_PROGRAM NEVER)
set(CMAKE_FIND_ROOT_PATH_MODE_LIBRARY ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_INCLUDE ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_PACKAGE ONLY)
EOF
    ;;
shaders)
    /bin/sh "$0" shaderc
    /bin/sh "$0" spirv-cross
    ;;
shaderc)
    test -f "$base/cross.cmake"
    if test ! -f "$base/shaderc-build/build.ninja"; then
        # Keep dependency export sets consistent. This shaderc revision sets
        # glslang's configure-time install switch to a generator expression;
        # SKIP_INSTALL=ON still enables glslang exports but removes their SPIRV
        # dependencies. We never invoke cmake --install for this tree; only
        # the combined archive/API are copied below.
        cmake -S "$base/source/shaderc" -B "$base/shaderc-build" -G Ninja \
          -DCMAKE_TOOLCHAIN_FILE="$base/cross.cmake" -DCMAKE_BUILD_TYPE=Release \
          -DCMAKE_INSTALL_PREFIX="$prefix" -DCMAKE_INSTALL_LIBDIR=lib -DBUILD_SHARED_LIBS=OFF \
          -DSHADERC_SKIP_TESTS=ON -DSHADERC_SKIP_INSTALL=OFF \
          -DSHADERC_SKIP_EXAMPLES=ON -DSHADERC_SKIP_EXECUTABLES=ON \
          -DSPIRV_SKIP_EXECUTABLES=ON -DSPIRV_SKIP_TESTS=ON \
          -DENABLE_GLSLANG_BINARIES=OFF -DSPIRV_TOOLS_BUILD_STATIC=ON
    fi
    ninja -C "$base/shaderc-build" -j1 shaderc_combined shaderc_combined-pkg-config
    # Install only the combined archive and public API. MPV and its private
    # libplacebo share this compiler; VLC's SDK glslang remains untouched.
    mkdir -p "$prefix/include/shaderc" "$prefix/lib/pkgconfig"
    cp "$base/source/shaderc/libshaderc/include/shaderc/"*.h "$prefix/include/shaderc/"
    cp "$base/shaderc-build/libshaderc/libshaderc_combined.a" "$prefix/lib/"
    cp "$base/shaderc-build/shaderc_combined.pc" "$prefix/lib/pkgconfig/shaderc.pc"
    ;;
spirv-cross)
    test -f "$base/cross.cmake"
    # SPVC's GNU visibility annotation alone does not define a PE DLL export
    # boundary. Explicitly export its C API and keep static runtime symbols
    # private; otherwise MinGW auto-exports pthread/unwind implementation names.
        cmake -S "$base/source/SPIRV-Cross" -B "$base/spirv-cross-build" -G Ninja \
          -DCMAKE_TOOLCHAIN_FILE="$base/cross.cmake" -DCMAKE_BUILD_TYPE=Release \
          "-DCMAKE_CXX_FLAGS=-B$crt/ -O2 -include /work/src/tools/windows-player/spirv-cross-exports.h" \
          "-DCMAKE_SHARED_LINKER_FLAGS=-B$crt/ -L$crt -static-libgcc -static-libstdc++ -pthread -Wl,--exclude-libs,ALL" \
          -DCMAKE_INSTALL_PREFIX="$prefix" -DCMAKE_INSTALL_LIBDIR=lib \
          -DSPIRV_CROSS_SHARED=ON -DSPIRV_CROSS_STATIC=OFF \
          -DSPIRV_CROSS_CLI=OFF -DSPIRV_CROSS_ENABLE_TESTS=OFF \
          -DSPIRV_CROSS_ENABLE_MSL=OFF -DSPIRV_CROSS_ENABLE_CPP=OFF \
          -DSPIRV_CROSS_ENABLE_REFLECT=OFF -DSPIRV_CROSS_ENABLE_UTIL=OFF
    ninja -C "$base/spirv-cross-build" -j1
    cmake --install "$base/spirv-cross-build"
    x86_64-w64-mingw32-nm -g --defined-only "$prefix/lib/libspirv-cross-c-shared.dll.a" \
        > "$base/spirv-cross-build/api-symbols.txt"
    grep -q ' T spvc_' "$base/spirv-cross-build/api-symbols.txt"
    if grep -E ' [TW] (pthread_|_Unwind_|_Z)' "$base/spirv-cross-build/api-symbols.txt"; then
        printf '%s\n' 'SPIRV-Cross imports expose private C++/Windows runtime symbols' >&2
        exit 1
    fi
    ;;
placebo)
    test -f "$base/cross.meson"
    test -f "$prefix/lib/pkgconfig/shaderc.pc"
    # This libplacebo revision generates shader C sources with Jinja2. Keep
    # the pure Python build dependency local; do not modify Ubuntu or pip's
    # global environment. MarkupSafe 2.1.5 is already in the pinned image.
    printf '%s  %s\n' 0137fb05990d35f1275a587e9aee6d56da821fc83491a0fb838183be43f66d6d /scratch/downloads/jinja2-3.1.6.tar.gz | sha256sum -c -
    if test ! -d "$base/host-python/jinja2"; then
        mkdir -p "$base/host-python"
        tar -xzf /scratch/downloads/jinja2-3.1.6.tar.gz --strip-components=2 \
            -C "$base/host-python" jinja2-3.1.6/src/jinja2
    fi
    export PYTHONPATH="$base/host-python"
    test -f "$sdk/share/vulkan/registry/vk.xml"
    # FFmpeg's software-frame libplacebo filter creates its own Vulkan device.
    # It therefore requires libplacebo's vkGetInstanceProcAddr fallback. Keep
    # the SDK untouched and name its import archive explicitly under -static.
    test -f "$sdk/lib/libvulkan-1.dll.a"
    sed 's@-lvulkan-1.dll@-l:libvulkan-1.dll.a@g' "$sdk/lib/pkgconfig/vulkan.pc" \
      > "$prefix/lib/pkgconfig/vulkan.pc"
    if test -f "$base/placebo-build/build.ninja"; then
        meson setup --reconfigure --clearcache "$base/placebo-build" "$base/source/libplacebo" \
          -Dvk-proc-addr=enabled -Dvulkan-registry="$sdk/share/vulkan/registry/vk.xml"
    else
        meson setup "$base/placebo-build" "$base/source/libplacebo" \
          --cross-file "$base/cross.meson" --prefix "$prefix" --libdir lib \
          --wrap-mode=nofallback -Ddefault_library=static -Dprefer_static=true \
          -Db_lto=false -Doptimization=2 -Ddebug=false -Db_ndebug=true \
          -Dvulkan=enabled -Dvk-proc-addr=enabled -Dd3d11=enabled \
          -Dvulkan-registry="$sdk/share/vulkan/registry/vk.xml" \
          -Dglslang=disabled -Dshaderc=enabled -Dopengl=disabled \
          -Ddovi=enabled -Dlibdovi=disabled -Dlcms=disabled -Dxxhash=disabled \
          -Dunwind=disabled -Ddemos=false -Dtests=false -Dbench=false -Dfuzz=false
    fi
    ninja -C "$base/placebo-build" -j1
    meson install -C "$base/placebo-build" --no-rebuild --only-changed
    ;;
ffmpeg)
    test -f "$prefix/lib/libplacebo.a"
    # All implementation libraries remain static except the deliberately shared
    # SPIRV-Cross C API. Under -static, GNU ld excludes *.dll.a from -l searches.
    # Use -l: to name that import archive without changing static selection.
    # FFmpeg sorts only -l arguments into the libraries following its test
    # object; absolute *.a paths are moved before it and break archive order.
    test -f "$prefix/lib/libspirv-cross-c-shared.dll.a"
    sed -i -e 's@ -lspirv-cross-c-shared$@ -l:libspirv-cross-c-shared.dll.a@' \
        -e 's@ ${libdir}/libspirv-cross-c-shared.dll.a$@ -l:libspirv-cross-c-shared.dll.a@' \
        "$prefix/lib/pkgconfig/spirv-cross-c-shared.pc"
    sed -i -e 's@ /usr/x86_64-w64-mingw32/lib/libshlwapi.a@ -lshlwapi@g' \
        -e 's@ /usr/x86_64-w64-mingw32/lib/libversion.a@ -lversion@g' \
        "$prefix/lib/pkgconfig/libplacebo.pc"
    grep -F -- '-l:libspirv-cross-c-shared.dll.a' "$prefix/lib/pkgconfig/spirv-cross-c-shared.pc"
    grep -F -- '-lshlwapi -lversion' "$prefix/lib/pkgconfig/libplacebo.pc"
    mkdir -p "$base/ffmpeg-build"
    cd "$base/ffmpeg-build"
    if test ! -f ffbuild/config.mak; then
        # Reproduce the actual dependency link before the long configure pass.
        # This diagnoses the known build boundary; it is not player acceptance.
        flags=
        libraries=
        for argument in $(pkg-config --static --libs libplacebo spirv-cross-c-shared); do
            case "$argument" in
                -l*|*.so) libraries="$libraries $argument" ;;
                *) flags="$flags $argument" ;;
            esac
        done
        x86_64-w64-mingw32-gcc -B"$crt/" -std=c17 \
            $(pkg-config --cflags libplacebo spirv-cross-c-shared) \
            -c /work/src/tools/windows-player/mpv-dependency-link.c -o "$base/dependency-link.o"
        x86_64-w64-mingw32-gcc -B"$crt/" -L"$prefix/lib" -L"$sdk/lib" -L"$crt" \
            -static -static-libgcc -static-libstdc++ $flags \
            -o "$base/dependency-link.exe" "$base/dependency-link.o" $libraries -lstdc++ -lwinpthread
        "$base/source/FFmpeg/configure" --prefix="$prefix" \
          --target-os=mingw32 --arch=x86_64 --cross-prefix=x86_64-w64-mingw32- \
          --cc="x86_64-w64-mingw32-gcc -B$crt/" \
          --cxx="x86_64-w64-mingw32-g++ -B$crt/" \
          --pkg-config=pkg-config --pkg-config-flags=--static \
          --extra-cflags="-I$prefix/include -I$sdk/include" \
          --extra-ldflags="-L$prefix/lib -L$sdk/lib -L$crt -static -static-libgcc -static-libstdc++" \
          --extra-libs='-lstdc++ -lwinpthread' \
          --disable-autodetect --disable-programs --disable-doc --disable-debug \
          --disable-shared --enable-static --enable-gpl --enable-version3 \
          --enable-libplacebo --enable-vulkan --enable-schannel \
          --enable-d3d11va --enable-dxva2 --enable-w32threads --enable-zlib
    fi
    make -j1
    # Preserve identical installed headers/archives so this dependency repair
    # does not invalidate every retained MPV object solely through new mtimes.
    make -j1 install INSTALL="python3 -B /work/src/tools/windows-player/install-ffmpeg-files.py"
    ;;
mpv)
    test -f "$prefix/lib/libavfilter.a"
    test -f "$prefix/lib/pkgconfig/shaderc.pc"
    test -f "$prefix/lib/pkgconfig/spirv-cross-c-shared.pc"
    # Meson's static system detector enumerates the compiler's library search
    # directories, ignoring linker-only -L arguments. The cross-file's -B
    # prefixes expose the retained target SDK; keep the selected CRT first.
    test "$(x86_64-w64-mingw32-g++ -B"$crt/" -B"$prefix/lib/" -B"$sdk/lib/" -print-file-name=libiconv.a)" = "$sdk/lib/libiconv.a"
    # Preserve MPV's subtitle encoding detection. The retained VLC SDK does
    # not contain uchardet; build this small static dependency in our prefix.
    printf '%s  %s\n' e97a60cfc00a1c147a674b097bb1422abd9fa78a2d9ce3f3fdcc2e78a34ac5f0 /scratch/mpv-source-inputs/uchardet-0.0.8.tar.xz | sha256sum -c -
    if test ! -d "$base/source/uchardet"; then
        mkdir "$base/source/uchardet"
        tar -xJf /scratch/mpv-source-inputs/uchardet-0.0.8.tar.xz --strip-components=1 -C "$base/source/uchardet"
    fi
    if test ! -f "$base/uchardet-build/build.ninja"; then
        cmake -S "$base/source/uchardet" -B "$base/uchardet-build" -G Ninja \
          -DCMAKE_TOOLCHAIN_FILE="$base/cross.cmake" -DCMAKE_BUILD_TYPE=Release \
          -DCMAKE_INSTALL_PREFIX="$prefix" -DCMAKE_INSTALL_LIBDIR=lib \
          -DBUILD_SHARED_LIBS=OFF -DBUILD_STATIC=ON -DBUILD_BINARY=OFF
    fi
    ninja -C "$base/uchardet-build" -j1 libuchardet
    cmake --install "$base/uchardet-build"
    pkg-config --exists libavcodec libavfilter libavformat libavutil libswresample libswscale libplacebo libass shaderc spirv-cross-c-shared zlib uchardet
    if test ! -f "$base/mpv-build/build.ninja"; then
        meson setup "$base/mpv-build" "$base/source/mpv" \
          --cross-file "$base/cross.meson" --prefix "$prefix" --libdir lib \
          --wrap-mode=nofallback -Ddefault_library=shared -Dprefer_static=true \
          -Db_lto=false -Doptimization=2 -Ddebug=false -Db_ndebug=true \
          -Dauto_features=disabled -Dlibmpv=true -Dcplayer=false -Dbuild-date=false \
          -Dgpl=true -Dlua=disabled -Dd3d11=enabled -Dd3d-hwaccel=enabled \
          -Dwasapi=enabled -Dwin32-threads=enabled -Diconv=enabled \
          -Dshaderc=enabled -Dspirv-cross=enabled \
          -Duchardet=enabled -Dzlib=enabled -Dgl=disabled -Dvulkan=disabled
    else
        # SDK pkg-config dependencies can put their broad include directory
        # before our newer libplacebo/FFmpeg APIs. Mark the external SDK as a
        # system fallback: GCC ignores its duplicate -I even if Meson reorders
        # dependency flags. Update supported options, preserving the build tree.
        meson configure "$base/mpv-build" \
          "-Dc_args=['-I$prefix/include', '-isystem$sdk/include']" \
          "-Dcpp_args=['-I$prefix/include', '-isystem$sdk/include']"
    fi
    ninja -C "$base/mpv-build" -j1
    meson install -C "$base/mpv-build" --no-rebuild --only-changed
    test -f "$prefix/bin/libmpv-2.dll"
    sha256sum "$prefix/bin/libmpv-2.dll"
    ;;
*) printf '%s\n' "Unknown phase: $phase" >&2; exit 2 ;;
esac
printf '%s\n' "Source-bound MPV phase finished: $phase; native playback acceptance remains required."
