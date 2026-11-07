#!/usr/bin/env bash
# Native hosted-runner setup; never invoked on the user's Windows installation.
set -euo pipefail
export HOMEBREW_NO_AUTO_UPDATE=1 HOMEBREW_NO_INSTALL_CLEANUP=1
if [[ $(uname -s) == Darwin ]]; then
    brew install autoconf automake libtool gettext pkgconf bison flex meson ninja nasm \
        qt ffmpeg libass libplacebo libarchive protobuf protobuf-c sqlite zstd
    brew info --json=v2 --installed > "$1/brew-packages.json"
else
    sudo install -m 644 /dev/null /etc/apt/sources.list.d/modern-vlc-build.sources
    sudo tee /etc/apt/sources.list.d/modern-vlc-build.sources >/dev/null <<'SOURCES'
Types: deb-src
URIs: http://archive.ubuntu.com/ubuntu/
Suites: noble noble-updates
Components: main universe restricted multiverse
Signed-By: /usr/share/keyrings/ubuntu-archive-keyring.gpg
SOURCES
    if [[ $(uname -m) == aarch64 ]]; then
        sudo sed -i 's|archive.ubuntu.com/ubuntu|ports.ubuntu.com/ubuntu-ports|' /etc/apt/sources.list.d/modern-vlc-build.sources
    fi
    sudo apt-get update
    sudo apt-get -y build-dep vlc
    sudo apt-get install -y meson ninja-build nasm python3-jinja2 python3-mako \
        qt6-base-dev qt6-base-private-dev qt6-declarative-dev qt6-declarative-private-dev \
        qt6-svg-dev qt6-tools-dev qt6-tools-dev-tools qt6-shadertools-dev qt6-wayland-dev \
        qml6-module-qtquick-controls qml6-module-qtquick-layouts qml6-module-qtquick-templates \
        qml6-module-qtqml-workerscript qml6-module-qtquick-window libqt6opengl6-dev \
        libavcodec-dev libavformat-dev libavutil-dev libavfilter-dev libswscale-dev libswresample-dev \
        libass-dev libarchive-dev libpulse-dev libpipewire-0.3-dev libgl-dev libegl-dev \
        libxcb-composite0-dev libxcb-damage0-dev libxcb-render0-dev libxcb-xfixes0-dev \
        libxcb-keysyms1-dev libxkbcommon-x11-dev libprotobuf-dev protobuf-compiler \
        libprotobuf-c-dev protobuf-c-compiler libsqlite3-dev libxxhash-dev liblcms2-dev \
        patchelf rpm squashfs-tools zstd xvfb openbox xcompmgr pulseaudio-utils
    dpkg-query -W -f='${binary:Package}\t${Version}\n' > "$1/dpkg-packages.tsv"
fi
