// SPDX-License-Identifier: GPL-2.0-or-later
#ifdef HAVE_CONFIG_H
# include "config.h"
#endif
#include "legacy_font_setup.hpp"
#include "../../legacy_skin_font.hpp"
#include <QCryptographicHash>
#include <QDir>
#include <QFile>
#include <QFileInfo>
#include <QNetworkRequest>
#include <QRawFont>
#include <QTemporaryFile>
#include <QUrl>
#include <archive.h>
#include <archive_entry.h>
#include <memory>

namespace {
constexpr qsizetype downloadLimit = 1024 * 1024;
QByteArray fontMember(const QByteArray &bytes)
{
    if (bytes.size() > downloadLimit || QCryptographicHash::hash(bytes, QCryptographicHash::Sha256).toHex() != LegacySkinFont::ArchiveSha256)
        return {};
    std::unique_ptr<struct archive, decltype(&archive_read_free)> reader(archive_read_new(), archive_read_free);
    if (!reader || archive_read_support_filter_none(reader.get()) != ARCHIVE_OK
        || archive_read_support_format_zip(reader.get()) != ARCHIVE_OK
        || archive_read_open_memory(reader.get(), bytes.constData(), size_t(bytes.size())) != ARCHIVE_OK)
        return {};
    QByteArray font;
    archive_entry *entry = nullptr;
    int count = 0, status;
    while ((status = archive_read_next_header(reader.get(), &entry)) != ARCHIVE_EOF) {
        if (status != ARCHIVE_OK || ++count > 32) return {};
        const char *name = archive_entry_pathname_utf8(entry);
        if (!name || QByteArray(name) != LegacySkinFont::ArchiveMember) {
            if (archive_read_data_skip(reader.get()) != ARCHIVE_OK) return {};
            continue;
        }
        if (!font.isEmpty() || archive_entry_filetype(entry) != AE_IFREG
            || archive_entry_hardlink(entry) || archive_entry_size(entry) != LegacySkinFont::FontBytes)
            return {};
        font.resize(LegacySkinFont::FontBytes);
        size_t offset = 0;
        while (offset < LegacySkinFont::FontBytes) {
            const auto read = archive_read_data(reader.get(), font.data() + offset, font.size() - offset);
            if (read <= 0) return {};
            offset += size_t(read);
        }
        char excess;
        if (archive_read_data(reader.get(), &excess, 1) != 0) return {};
    }
    if (QCryptographicHash::hash(font, QCryptographicHash::Sha256).toHex() != LegacySkinFont::FontSha256)
        return {};
    return font;
}
}

LegacyFontSetup::LegacyFontSetup(QObject *parent) : QObject(parent), m_network(this)
{
    refresh();
}
LegacyFontSetup::~LegacyFontSetup()
{
    ++m_generation;
    if (m_reply) {
        QObject::disconnect(m_reply.data(), nullptr, this, nullptr);
        m_reply->abort();
    }
}
QString LegacyFontSetup::location() const
{
    const auto path = LegacySkinFont::cachePath();
    return QString::fromUtf8(path.c_str());
}
void LegacyFontSetup::refresh()
{
    if (m_busy) return;
    const auto state = LegacySkinFont::cacheState(LegacySkinFont::cachePath());
    m_available = state == LegacySkinFont::CacheState::Ready;
    if (m_available) m_status = tr("The original classic-skin font is available. No download is needed.");
    else if (state == LegacySkinFont::CacheState::Missing)
        m_status = tr("Download Delicious directly from exljbris, or continue with the bundled FreeSans font.");
    else m_status = tr("The saved optional font is unreadable or unrecognized. It has been preserved; FreeSans is available.");
    emit changed();
}
void LegacyFontSetup::cancel()
{
    if (!m_busy) return;
    fail(tr("Font download cancelled. You can continue with FreeSans."));
}
void LegacyFontSetup::fail(const QString &message)
{
    ++m_generation;
    if (m_reply) {
        QObject::disconnect(m_reply.data(), nullptr, this, nullptr);
        m_reply->abort();
        m_reply->deleteLater();
        m_reply = nullptr;
    }
    m_busy = false;
    m_bytes.clear();
    m_status = message;
    emit changed();
}
bool LegacyFontSetup::install(const QByteArray &bytes)
{
    const QByteArray font = fontMember(bytes);
    if (font.isEmpty()) {
        m_status = tr("The download differs from the supported publisher font. You can continue with FreeSans.");
        return false;
    }
    const QRawFont parsed(font, 14);
    if (!parsed.isValid() || parsed.familyName() != QLatin1String("Delicious")) {
        m_status = tr("The downloaded font could not be loaded. FreeSans is available.");
        return false;
    }
    const auto path = LegacySkinFont::cachePath();
    const auto existing = LegacySkinFont::cacheState(path);
    if (existing == LegacySkinFont::CacheState::Ready) return true;
    if (existing != LegacySkinFont::CacheState::Missing) {
        m_status = tr("An existing optional-font file was preserved. You can continue with FreeSans.");
        return false;
    }
    const QString destination = QString::fromUtf8(path.c_str());
    const QString directory = QFileInfo(destination).absolutePath();
    if (!QDir().mkpath(directory)) {
        m_status = tr("The font folder could not be created. Your existing settings are unchanged.");
        return false;
    }
    QTemporaryFile pending(directory + QStringLiteral("/.delicious-XXXXXX.tmp"));
    if (!pending.open() || pending.write(font) != font.size() || !pending.flush()) {
        m_status = tr("The font could not be saved. Your existing files are unchanged.");
        return false;
    }
    pending.close();
    // QFile rename refuses an existing destination, preserving a concurrent
    // writer. The completed same-directory temporary file is exposed at once.
    if (!pending.rename(destination)) {
        if (LegacySkinFont::cacheState(path) == LegacySkinFont::CacheState::Ready) return true;
        m_status = tr("The font could not be installed; any existing file was preserved.");
        return false;
    }
    pending.setAutoRemove(false);
    return true;
}
void LegacyFontSetup::download()
{
    if (m_busy) return;
    const auto state = LegacySkinFont::cacheState(LegacySkinFont::cachePath());
    if (state != LegacySkinFont::CacheState::Missing) {
        refresh();
        return;
    }
    QNetworkRequest request(QUrl(QString::fromLatin1(LegacySkinFont::DownloadUrl)));
    request.setAttribute(QNetworkRequest::RedirectPolicyAttribute, QNetworkRequest::SameOriginRedirectPolicy);
    request.setRawHeader("Referer", LegacySkinFont::PublisherPage);
    request.setRawHeader("User-Agent", "VLC-Redesign optional font setup");
    m_busy = true;
    m_received = 0; m_total = -1; m_bytes.clear();
    m_status = tr("Downloading the optional font from exljbris…");
    const quint64 generation = ++m_generation;
    auto *reply = m_network.get(request);
    m_reply = reply;
    connect(reply, &QNetworkReply::downloadProgress, this, [this, generation](qint64 received, qint64 total) {
        if (generation != m_generation) return;
        if (received > downloadLimit || total > downloadLimit) {
            fail(tr("The font response exceeds the supported size. FreeSans is available."));
            return;
        }
        m_received = received; m_total = total; emit changed();
    });
    connect(reply, &QNetworkReply::readyRead, this, [this, reply, generation] {
        if (generation != m_generation) return;
        if (reply->bytesAvailable() > downloadLimit - m_bytes.size()) {
            fail(tr("The font response exceeds the supported size. FreeSans is available."));
            return;
        }
        m_bytes += reply->readAll();
    });
    connect(reply, &QNetworkReply::finished, this, [this, reply, generation] {
        if (generation != m_generation) return;
        m_reply = nullptr;
        reply->deleteLater();
        m_busy = false;
        const auto status = reply->attribute(QNetworkRequest::HttpStatusCodeAttribute).toInt();
        if (reply->error() != QNetworkReply::NoError || status != 200) {
            const QString reason = reply->error() != QNetworkReply::NoError
                ? reply->errorString() : tr("HTTP response %1").arg(status);
            m_status = tr("The font download failed: %1. Retry, or continue with FreeSans.").arg(reason);
        } else if (reply->bytesAvailable() > downloadLimit - m_bytes.size()) {
            m_status = tr("The font response exceeds the supported size. FreeSans is available.");
        } else {
            m_bytes += reply->readAll();
            m_available = install(m_bytes);
            if (m_available) m_status = tr("Delicious was downloaded and is ready for the classic skin.");
        }
        m_bytes.clear();
        emit changed();
    });
    emit changed();
}
