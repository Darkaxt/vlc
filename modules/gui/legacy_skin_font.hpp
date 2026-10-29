// SPDX-License-Identifier: GPL-2.0-or-later
// Identity/path shared by first-run acquisition and the default skin consumer.
#ifndef VLC_LEGACY_SKIN_FONT_HPP
#define VLC_LEGACY_SKIN_FONT_HPP
#include <vlc_common.h>
#include <vlc_configuration.h>
#include <vlc_fs.h>
#include <vlc_hash.h>
#include <vlc_strings.h>
#include <array>
#include <cerrno>
#include <cstdio>
#include <cstdlib>
#include <string>

namespace LegacySkinFont {
constexpr char PublisherPage[] = "https://www.exljbris.com/delicious.html";
constexpr char LicensePage[] = "https://www.exljbris.com/eula.html";
constexpr char DownloadUrl[] = "https://www.exljbris.com/dl/DELICIOUS_21_OTF.zip";
constexpr char ArchiveSha256[] = "fc25f631167471a1e33f57264a8eba1f3b27bffbdcdb0487bc6e0fbc584d6672";
constexpr char ArchiveMember[] = "DELICIOUS_21_OTF/Delicious_R_2021.otf";
constexpr char FontSha256[] = "3da2532e334eb31eabcf476e826b33b5f19ecde9dd110b3fd8699585c89d2b76";
// VLC's existing core MD5 API provides a fixed-file identity check to skins2
// without adding a crypto dependency. Acquisition separately verifies SHA-256.
constexpr char FontMd5[] = "f10efb54ca77c24f6fe1f6f9bb346abd";
constexpr size_t FontBytes = 16736;
constexpr char FontId[] = "redesign-optional-legacy-font";
inline std::string cachePath()
{
    char *directory = config_GetUserDir(VLC_CONFIG_DIR);
    if (!directory) return {};
    std::string path(directory);
    free(directory);
    return path + "/redesign/fonts/Delicious_R_2021.otf";
}
enum class CacheState { Missing, Ready, Unknown, Unreadable };
inline CacheState cacheState(const std::string &path)
{
    if (path.empty()) return CacheState::Unreadable;
    FILE *file = vlc_fopen(path.c_str(), "rb");
    if (!file) return errno == ENOENT ? CacheState::Missing : CacheState::Unreadable;
    vlc_hash_md5_t hash;
    vlc_hash_md5_Init(&hash);
    std::array<char, 4096> buffer;
    size_t total = 0, count;
    while ((count = fread(buffer.data(), 1, buffer.size(), file)) != 0) {
        total += count;
        if (total > FontBytes) break;
        vlc_hash_md5_Update(&hash, buffer.data(), count);
    }
    const bool unreadable = ferror(file);
    fclose(file);
    if (unreadable) return CacheState::Unreadable;
    if (total != FontBytes) return CacheState::Unknown;
    char hex[VLC_HASH_MD5_DIGEST_HEX_SIZE];
    std::array<unsigned char, VLC_HASH_MD5_DIGEST_SIZE> digest;
    vlc_hash_md5_Finish(&hash, digest.data(), digest.size());
    vlc_hex_encode_binary(digest.data(), digest.size(), hex);
    return std::string(hex) == FontMd5 ? CacheState::Ready : CacheState::Unknown;
}
}
#endif
