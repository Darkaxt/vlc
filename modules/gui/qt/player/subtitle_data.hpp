// SPDX-License-Identifier: GPL-2.0-or-later
#ifndef VLC_QT_SUBTITLE_DATA_HPP
#define VLC_QT_SUBTITLE_DATA_HPP

#include <QFileInfo>
#include <QCryptographicHash>
#include <QRegularExpression>
#include <QStringList>
#include <QVector>
#include <algorithm>
#include <cmath>

// Filename matching and external text cue data. Neither selects a track nor
// guesses identity after a file moves. Ambiguities remain choices for the user.
namespace SubtitleData {
struct Cue { qint64 start; qint64 end; QString text; };

inline QString normalized(QString value)
{
    return value.toCaseFolded().remove(QRegularExpression(QStringLiteral("[^\\p{L}\\p{N}]+")));
}

inline QString episodeKey(const QString &stem)
{
    static const QRegularExpression episode(QStringLiteral("(?:s(\\d{1,3})e(\\d{1,4})|(\\d{1,3})x(\\d{1,4}))(?!\\d)"), QRegularExpression::CaseInsensitiveOption);
    const auto m = episode.match(stem);
    if (!m.hasMatch()) return {};
    const auto show = normalized(stem.left(m.capturedStart()));
    if (show.isEmpty()) return {};
    const int season = m.captured(1).isEmpty() ? m.captured(3).toInt() : m.captured(1).toInt();
    const int number = m.captured(2).isEmpty() ? m.captured(4).toInt() : m.captured(2).toInt();
    return show + QLatin1Char('/') + QString::number(season) + QLatin1Char('/') + QString::number(number);
}

inline QStringList match(const QString &media, const QStringList &subtitles)
{
    const auto stem = QFileInfo(media).completeBaseName();
    const auto exact = normalized(stem);
    const auto episode = episodeKey(stem);
    QStringList full, episodes;
    for (const auto &sub : subtitles) {
        const auto subStem = QFileInfo(sub).completeBaseName();
        if (normalized(subStem) == exact) full.append(sub);
        else if (!episode.isEmpty() && episodeKey(subStem) == episode) episodes.append(sub);
    }
    auto result = !full.isEmpty() ? full : episodes;
    result.removeDuplicates();
    result.sort(Qt::CaseInsensitive);
    return result;
}

inline QString downloadFileName(const QString &context, QString original, const QString &language,
                                const QString &provider, const QString &reference)
{
    original.replace(QLatin1Char('\\'), QLatin1Char('/'));
    const QFileInfo file(original);
    QString stem = file.completeBaseName();
    static const QRegularExpression generic(QStringLiteral("^(?:subtitle[s]?|sub|download|default|untitled|[0-9]+)$"), QRegularExpression::CaseInsensitiveOption);
    const bool genericName = stem.isEmpty() || generic.match(stem).hasMatch() || stem.compare(language, Qt::CaseInsensitive) == 0;
    if (genericName)
        stem = context.trimmed().isEmpty() ? QStringLiteral("Subtitle") : context.trimmed();
    else if (!context.trimmed().isEmpty() && !normalized(stem).contains(normalized(context)))
        stem += QStringLiteral(" - ") + context.trimmed();
    const auto parent = file.path();
    const bool archivePath = !parent.isEmpty() && parent != QLatin1String(".");
    if (archivePath) { QString folders = parent; folders.replace(QLatin1Char('/'), QStringLiteral(" - ")); stem = genericName ? folders + QStringLiteral(" - ") + stem : stem + QStringLiteral(" - ") + folders; }
    const auto clean = [](QString value, qsizetype limit) {
        value.replace(QRegularExpression(QStringLiteral("[<>:\"/\\\\|?*\\x00-\\x1f]")), QStringLiteral("_"));
        return value.simplified().left(limit);
    };
    const QString safeStem = clean(stem, 64);
    QString fileReference = clean(reference, 20);
    const QByteArray memberIdentity = reference.toUtf8() + '\n' + original.toUtf8() + '\n' + context.toUtf8();
    if (archivePath || genericName || safeStem != stem)
        fileReference += QLatin1Char('-') + QString::fromLatin1(QCryptographicHash::hash(memberIdentity, QCryptographicHash::Sha256).toHex().left(8));
    stem = safeStem;
    static const QRegularExpression device(QStringLiteral("^(?:CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\\.|$)"), QRegularExpression::CaseInsensitiveOption);
    if (device.match(stem).hasMatch()) stem.prepend(QLatin1Char('_'));
    const QString code = language.trimmed().isEmpty() ? QStringLiteral("und") : clean(language, 16).toLower();
    // Pinned subtitle.c get_language_from_url reads between the last two dots.
    return QLatin1Char('[') + clean(provider, 16) + QLatin1Char(' ') + fileReference
        + QStringLiteral("] ") + stem + QLatin1Char('.') + code
        + QLatin1Char('.') + file.suffix().toLower();
}

inline QString trackSourceName(const QString &fileName)
{
    // Keep the episode/title visible in a narrow track list. The full saved
    // filename and provider reference remain available in the label/tooltip.
    for (const auto *provider : {"OpenSubtitles", "SubDL", "SubSource"}) {
        const QString prefix = QStringLiteral("[%1 ").arg(QString::fromLatin1(provider));
        if (!fileName.startsWith(prefix)) continue;
        const auto end = fileName.indexOf(QStringLiteral("] "));
        if (end > prefix.size() && end + 2 < fileName.size())
            return fileName.mid(end + 2) + QLatin1Char(' ') + fileName.left(end + 1);
    }
    return fileName;
}

inline qint64 timestamp(QString text)
{
    text.replace(QLatin1Char(','), QLatin1Char('.'));
    const auto parts = text.trimmed().split(QLatin1Char(':'));
    if (parts.size() < 2 || parts.size() > 3) return -1;
    bool ok = false;
    const double seconds = parts.last().toDouble(&ok);
    if (!ok || !std::isfinite(seconds) || seconds < 0 || seconds >= 60) return -1;
    const int minutes = parts[parts.size() - 2].toInt(&ok);
    if (!ok || minutes < 0 || minutes >= 60) return -1;
    const int hours = parts.size() == 3 ? parts[0].toInt(&ok) : 0;
    if (!ok || hours < 0 || hours > 999) return -1;
    return qRound64(((hours * 60 + minutes) * 60 + seconds) * 1000);
}

inline QVector<Cue> cues(QString text, const QString &extension)
{
    QVector<Cue> out;
    text.remove(QChar(0xfeff));
    text.replace(QStringLiteral("\r\n"), QStringLiteral("\n"));
    text.replace(QLatin1Char('\r'), QLatin1Char('\n'));
    const auto add = [&out](qint64 start, qint64 end, QString label) {
        if (start < 0 || end <= start || out.size() >= 100000) return;
        out.append({start, end, label.left(4096)});
    };
    if (extension == QLatin1String("srt") || extension == QLatin1String("vtt")) {
        static const QRegularExpression time(QStringLiteral("(?m)^([\\d:]+[,.]\\d+)\\s+-->\\s+([\\d:]+[,.]\\d+)[^\\n]*\\n([\\s\\S]*?)(?=\\n\\s*\\n|\\z)"));
        auto it = time.globalMatch(text);
        while (it.hasNext()) {
            const auto m = it.next();
            add(timestamp(m.captured(1)), timestamp(m.captured(2)), m.captured(3).trimmed());
        }
    } else if (extension == QLatin1String("ass") || extension == QLatin1String("ssa")) {
        bool events = false;
        QStringList format;
        for (const auto &line : text.split(QLatin1Char('\n'))) {
            const auto clean = line.trimmed();
            if (clean.startsWith(QLatin1Char('['))) { events = clean.compare(QLatin1String("[Events]"), Qt::CaseInsensitive) == 0; continue; }
            if (!events) continue;
            if (clean.startsWith(QLatin1String("Format:"), Qt::CaseInsensitive)) {
                format = clean.mid(7).toLower().split(QLatin1Char(','));
                for (auto &field : format) field = field.trimmed();
            } else if (clean.startsWith(QLatin1String("Dialogue:"), Qt::CaseInsensitive)) {
                // Text must be last; commas inside it are preserved.
                if (format.isEmpty() || format.last() != QLatin1String("text")) continue;
                auto fields = clean.mid(9).split(QLatin1Char(','));
                const int start = format.indexOf(QStringLiteral("start")), end = format.indexOf(QStringLiteral("end"));
                if (start < 0 || end < 0 || fields.size() < format.size()) continue;
                QString label = fields.mid(format.size() - 1).join(QLatin1Char(','));
                label.remove(QRegularExpression(QStringLiteral("\\{[^}]*\\}")));
                label.replace(QStringLiteral("\\N"), QStringLiteral("\n"));
                label.replace(QStringLiteral("\\n"), QStringLiteral("\n"));
                add(timestamp(fields[start]), timestamp(fields[end]), label);
            }
        }
    }
    std::stable_sort(out.begin(), out.end(), [](const Cue &a, const Cue &b) { return a.start < b.start; });
    return out;
}
}
#endif
