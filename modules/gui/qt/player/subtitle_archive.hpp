// SPDX-License-Identifier: GPL-2.0-or-later
#ifndef VLC_QT_SUBTITLE_ARCHIVE_HPP
#define VLC_QT_SUBTITLE_ARCHIVE_HPP
#include <archive.h>
#include <archive_entry.h>
#include <QByteArray>
#include <QFileInfo>
#include <QSet>
#include <QStringList>
#include <QVector>
#include <array>
#include <memory>

// Read subtitle members in memory using VLC's existing libarchive dependency.
// Never extract paths to disk; reject limits before retaining decompressed data.
namespace SubtitleArchive {
struct Member { QString name; QByteArray bytes; };
enum class Result { Ok, TooLarge, TooManyEntries, Duplicate, Invalid, NoSupportedFiles };
inline Result decode(const QByteArray &bytes, QVector<Member> &members)
{
    constexpr qsizetype memberLimit = 8 * 1024 * 1024;
    constexpr qsizetype totalLimit = 16 * 1024 * 1024;
    members.clear();
    if (bytes.size() > totalLimit) return Result::TooLarge;
    std::unique_ptr<struct archive, decltype(&archive_read_free)> reader(archive_read_new(), archive_read_free);
    if (!reader || archive_read_support_filter_none(reader.get()) != ARCHIVE_OK
        || archive_read_support_format_zip(reader.get()) != ARCHIVE_OK
        || archive_read_open_memory(reader.get(), bytes.constData(), size_t(bytes.size())) != ARCHIVE_OK)
        return Result::Invalid;
    QVector<Member> pending;
    QSet<QString> names;
    qsizetype total = 0;
    int count = 0;
    struct archive_entry *entry = nullptr;
    for (;;) {
        const int status = archive_read_next_header(reader.get(), &entry);
        if (status == ARCHIVE_EOF) break;
        if (status != ARCHIVE_OK) return Result::Invalid;
        if (++count > 256) return Result::TooManyEntries;
        const char *raw = archive_entry_pathname_utf8(entry);
        if (!raw) raw = archive_entry_pathname(entry);
        const QString name = QString::fromUtf8(raw ? raw : "");
        if (archive_entry_filetype(entry) != AE_IFREG || archive_entry_hardlink(entry)
            || !QStringList{QStringLiteral("srt"), QStringLiteral("vtt"), QStringLiteral("ass"), QStringLiteral("ssa")}.contains(QFileInfo(name).suffix().toLower())) {
            if (archive_read_data_skip(reader.get()) != ARCHIVE_OK) return Result::Invalid;
            continue;
        }
        if (name.isEmpty() || name.contains(QChar::ReplacementCharacter)) return Result::Invalid;
        if (names.contains(name)) return Result::Duplicate;
        names.insert(name);
        if (archive_entry_size_is_set(entry)
            && (archive_entry_size(entry) < 0 || archive_entry_size(entry) > memberLimit
                || archive_entry_size(entry) > totalLimit - total)) return Result::TooLarge;
        QByteArray data;
        std::array<char, 65536> chunk;
        for (;;) {
            const auto read = archive_read_data(reader.get(), chunk.data(), chunk.size());
            if (read < 0) return Result::Invalid;
            if (read == 0) break;
            if (read > memberLimit - data.size() || read > totalLimit - total) return Result::TooLarge;
            data.append(chunk.data(), qsizetype(read));
            total += qsizetype(read);
        }
        pending.append({name, data});
    }
    if (pending.isEmpty()) return Result::NoSupportedFiles;
    members = std::move(pending);
    return Result::Ok;
}
}
#endif
