// SPDX-License-Identifier: GPL-2.0-or-later
#ifndef VLC_QT_FORK_RELEASE_HPP
#define VLC_QT_FORK_RELEASE_HPP
#include <QJsonArray>
#include <QJsonDocument>
#include <QJsonObject>
#include <QRegularExpression>
#include <QSet>
#include <QUrl>
#include <QVersionNumber>

namespace ForkRelease {
inline constexpr char currentVersion[] = "1.1.7";
inline constexpr char endpoint[] = "https://api.github.com/repos/Darkaxt/vlc/releases/latest";
struct Release {
    QVersionNumber version;
    QString description;
    QUrl page;
    bool valid = false;
};
inline Release parse(const QByteArray &bytes)
{
    Release result;
    if (bytes.size() > 1024 * 1024) return result;
    QJsonParseError error;
    const auto document = QJsonDocument::fromJson(bytes, &error);
    if (error.error != QJsonParseError::NoError || !document.isObject()) return result;
    const auto json = document.object();
    if (!json.value(QStringLiteral("draft")).isBool() || json.value(QStringLiteral("draft")).toBool()
        || !json.value(QStringLiteral("prerelease")).isBool() || json.value(QStringLiteral("prerelease")).toBool()) return result;
    const auto tag = json.value(QStringLiteral("tag_name")).toString();
    const QRegularExpression expression(QStringLiteral("^redesign-v(0|[1-9][0-9]{0,5})\\.(0|[1-9][0-9]{0,5})\\.(0|[1-9][0-9]{0,5})$"));
    const auto match = expression.match(tag);
    if (!match.hasMatch()) return result;
    result.version = QVersionNumber(match.captured(1).toInt(), match.captured(2).toInt(), match.captured(3).toInt());
    const QString page = QStringLiteral("https://github.com/Darkaxt/vlc/releases/tag/") + tag;
    if (json.value(QStringLiteral("html_url")).toString() != page) return {};
    const QString base = QStringLiteral("Modern-VLC-Fork-") + result.version.toString();
    QSet<QString> required{base + QStringLiteral("-win64-portable.zip"),
        base + QStringLiteral("-corresponding-source.tar.gz"), QStringLiteral("SHA256SUMS.txt")};
    //1.0/1.1.0 predate the separate optional symbol archive. All new releases
    // have it; they must not be announced while publication is incomplete.
    if (result.version >= QVersionNumber(1, 1, 1)) required.insert(base + QStringLiteral("-win64-symbols.zip"));
    for (const auto &value : json.value(QStringLiteral("assets")).toArray()) {
        const auto asset = value.toObject();
        const auto name = asset.value(QStringLiteral("name")).toString();
        if (!required.contains(name)) continue;
        if (asset.value(QStringLiteral("state")).toString() != QStringLiteral("uploaded")
            || asset.value(QStringLiteral("size")).toDouble() <= 0
            || asset.value(QStringLiteral("browser_download_url")).toString()
                != QStringLiteral("https://github.com/Darkaxt/vlc/releases/download/") + tag + QLatin1Char('/') + name) return {};
        required.remove(name);
    }
    if (!required.isEmpty()) return {};
    result.page = QUrl(page);
    result.description = json.value(QStringLiteral("body")).toString().left(65536);
    result.valid = true;
    return result;
}
}
#endif
