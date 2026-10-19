// SPDX-License-Identifier: GPL-2.0-or-later
#include "player/subtitle_data.hpp"
#include "player/subtitle_archive.hpp"
#include <QCoreApplication>
#include <QDebug>
#include <cstdlib>

static void require(bool ok, const char *message)
{
    if (!ok) { qCritical() << message; std::exit(1); }
}

static QByteArray zip(const QVector<SubtitleArchive::Member> &members)
{
    QByteArray buffer(18 * 1024 * 1024, '\0');
    size_t used = 0;
    auto *writer = archive_write_new();
    require(writer && archive_write_set_format_zip(writer) == ARCHIVE_OK, "ZIP writer");
    require(archive_write_set_options(writer, "zip:zip64,zip:compression=store") == ARCHIVE_OK, "force the provider's valid ZIP64 format");
    require(archive_write_open_memory(writer, buffer.data(), size_t(buffer.size()), &used) == ARCHIVE_OK, "ZIP memory output");
    for (const auto &member : members) {
        auto *entry = archive_entry_new();
        archive_entry_set_pathname(entry, member.name.toUtf8().constData());
        archive_entry_set_filetype(entry, AE_IFREG);
        archive_entry_set_perm(entry, 0644);
        archive_entry_set_size(entry, member.bytes.size());
        require(archive_write_header(writer, entry) == ARCHIVE_OK, "ZIP header");
        require(archive_write_data(writer, member.bytes.constData(), size_t(member.bytes.size())) == member.bytes.size(), "ZIP data");
        archive_entry_free(entry);
    }
    require(archive_write_close(writer) == ARCHIVE_OK, "ZIP close");
    archive_write_free(writer);
    buffer.resize(qsizetype(used));
    return buffer;
}

int main(int argc, char **argv)
{
    QCoreApplication app(argc, argv);
    using namespace SubtitleData;
    require(match(QStringLiteral("The.Wand.S01E02.mkv"),
        {QStringLiteral("The_Wand_S01E01.en.srt"), QStringLiteral("The_Wand_S01E02.en.srt")})
        == QStringList{QStringLiteral("The_Wand_S01E02.en.srt")}, "episode matching");
    require(match(QStringLiteral("The.Wand.S01E02.mkv"),
        {QStringLiteral("Other.Show.S01E02.srt")}).isEmpty(), "never match another show");
    require(match(QStringLiteral("The.Wand.S01E02.mkv"),
        {QStringLiteral("The.Wand.S01E02.en.srt"), QStringLiteral("The.Wand.S01E02.de.srt")}).size() == 2,
        "keep language collision ambiguous");
    require(match(QStringLiteral("Movie.mkv"),
        {QStringLiteral("Movie.srt"), QStringLiteral("Movie.en.srt")})
        == QStringList{QStringLiteral("Movie.srt")}, "prefer exact stem");
    require(match(QStringLiteral("Movie.mkv"), {QStringLiteral("Movie.Up.srt")}).isEmpty(),
        "do not reinterpret title words as language suffixes");
    const auto srt = cues(QStringLiteral("1\r\n00:00:01,250 --> 00:00:03,500\r\nHello\r\n\r\n2\r\n00:00:05,000 --> 00:00:06,000\r\nWorld\r\n"), QStringLiteral("srt"));
    require(srt.size() == 2 && srt[0].start == 1250 && srt[0].end == 3500, "SRT cue time");
    const auto vtt = cues(QStringLiteral("WEBVTT\n\nid\n00:01.250 --> 00:02.500 align:start\nHello\n"), QStringLiteral("vtt"));
    require(vtt.size() == 1 && vtt[0].start == 1250, "VTT short timestamps and settings");
    const auto multiline = cues(QStringLiteral("1\n00:00:01,000 --> 00:00:02,000\nOne\nTwo\n"), QStringLiteral("srt"));
    require(multiline.size() == 1 && multiline[0].text == QStringLiteral("One\nTwo"), "preserve multiline cue text");
    const auto ass = cues(QStringLiteral("[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\nDialogue: 0,0:00:01.25,0:00:03.50,Default,,0,0,0,,{\\i1}Hello, world\\NAgain\n"), QStringLiteral("ass"));
    require(ass.size() == 1 && ass[0].start == 1250 && ass[0].text == QStringLiteral("Hello, world\nAgain"), "ASS dialogue and escaped text");
    require(cues(QStringLiteral("1\n00:00:05,000 --> 00:00:01,000\nInvalid\n"), QStringLiteral("srt")).isEmpty(), "reject reversed cue");
    require(cues(QStringLiteral("binary bitmap"), QStringLiteral("sup")).isEmpty(), "bitmap timeline unavailable");
    const auto named = downloadFileName(QStringLiteral("Sintel.2010.BluRay"), QStringLiteral("subtitle.ass"), QStringLiteral("english"), QStringLiteral("SubSource"), QStringLiteral("1501625"));
    require(named.contains(QStringLiteral("Sintel.2010.BluRay")) && named.contains(QStringLiteral("english")) && named.contains(QStringLiteral("SubSource")) && named.contains(QStringLiteral("1501625")) && named.endsWith(QStringLiteral(".ass")), "descriptive name preserves release language provider and actual format");
    require(named != downloadFileName(QStringLiteral("Sintel.2010.BluRay"), QStringLiteral("subtitle.ass"), QStringLiteral("english"), QStringLiteral("SubSource"), QStringLiteral("1501626")), "different provider records remain distinct");
    require(downloadFileName(QStringLiteral("Film"), QStringLiteral("Fansub A/subtitle.ass"), QStringLiteral("en"), QStringLiteral("SubDL"), QStringLiteral("abc")) != downloadFileName(QStringLiteral("Film"), QStringLiteral("Fansub B/subtitle.ass"), QStringLiteral("en"), QStringLiteral("SubDL"), QStringLiteral("abc")), "archive parent folders distinguish generic member names");
    require(!downloadFileName(QStringLiteral("Film: Bad/Path"), QStringLiteral("subtitle.srt"), QStringLiteral("en"), QStringLiteral("SubDL"), QStringLiteral("123")).contains(QLatin1Char('/')), "provider names cannot create filesystem paths");
    require(timestamp(QStringLiteral("00:NaN")) < 0, "reject nonfinite cue timestamps");
    const auto released = downloadFileName(QStringLiteral("Sintel.2010.Xvid-VODO"), QStringLiteral("sintel_en.srt"), QStringLiteral("en"), QStringLiteral("OpenSubtitles"), QStringLiteral("65509"));
    require(released.contains(QStringLiteral("Xvid-VODO")), "saved name retains the provider release when its original filename omits it");
    require(released.endsWith(QStringLiteral(".en.srt")), "use VLC's language suffix rather than parentheses that corrupt detected track language");
    require(downloadFileName(QStringLiteral("Film"), QStringLiteral("Fansub A/Rip/subtitle.ass"), QStringLiteral("en"), QStringLiteral("SubDL"), QStringLiteral("abc")) != downloadFileName(QStringLiteral("Film"), QStringLiteral("Fansub B/Rip/subtitle.ass"), QStringLiteral("en"), QStringLiteral("SubDL"), QStringLiteral("abc")), "full archive paths distinguish repeated immediate folder names");
    const QString longStem(80, QLatin1Char('a'));
    require(downloadFileName(QStringLiteral("Film"), longStem + QStringLiteral("-A.ass"), QStringLiteral("en"), QStringLiteral("SubDL"), QStringLiteral("abc")) != downloadFileName(QStringLiteral("Film"), longStem + QStringLiteral("-B.ass"), QStringLiteral("en"), QStringLiteral("SubDL"), QStringLiteral("abc")), "truncated archive member names retain distinct file references");
    require(downloadFileName(QStringLiteral("Film"), QStringLiteral("subtitle.ass"), QStringLiteral("en"), QStringLiteral("SubSource"), QStringLiteral("123")) != downloadFileName(QStringLiteral("Film"), QStringLiteral("subtitles.ass"), QStringLiteral("en"), QStringLiteral("SubSource"), QStringLiteral("123")), "generic members at an archive root remain distinct after replacing their generic stems");
    const QString seasonRelease = QStringLiteral("Chernobyl.S01.INTERNAL.1080p.BluRay.X264-REWARD.en");
    const auto episode = downloadFileName(seasonRelease, QStringLiteral("Chernobyl.S01E03.INTERNAL.1080p.BluRay.X264-REWARD.en.srt"), QStringLiteral("en"), QStringLiteral("SubSource"), QStringLiteral("3067660"));
    require(episode.contains(QStringLiteral("S01E03")), "season-pack release must not truncate away the chosen member's episode identity");
    require(episode != downloadFileName(seasonRelease, QStringLiteral("Chernobyl.S01E04.INTERNAL.1080p.BluRay.X264-REWARD.en.srt"), QStringLiteral("en"), QStringLiteral("SubSource"), QStringLiteral("3067660")), "episodes remain distinguishable after saving");
    const auto trackName = trackSourceName(episode);
    require(trackName.startsWith(QStringLiteral("Chernobyl.S01E03"))
        && trackName.contains(QStringLiteral(".en.srt")) && trackName.contains(QStringLiteral("[SubSource 3067660")),
        "episode appears before the provider reference in a narrow track list");
    require(trackSourceName(QStringLiteral("[Fansub] Local.ass")) == QStringLiteral("[Fansub] Local.ass"),
        "preserve original local subtitle names");
    using SubtitleArchive::Member;
    using SubtitleArchive::Result;
    QVector<Member> members;
    const QByteArray content("SUBTITLE CONTENT");
    auto archive = zip({{QStringLiteral("Fansub A/subtitle.ass"), content}, {QStringLiteral("Fansub B/subtitle.ass"), content}});
    require(SubtitleArchive::decode(archive, members) == Result::Ok && members.size() == 2
        && members[0].name != members[1].name && members[0].bytes == content, "ZIP64 preserves distinct original archive member paths and payloads");
    require(SubtitleArchive::decode(zip({{QStringLiteral("same.srt"), content}, {QStringLiteral("same.srt"), content}}), members) == Result::Duplicate && members.isEmpty(), "reject repeated archive paths without publishing partial members");
    QVector<Member> many;
    for (int i = 0; i < 257; ++i) many.append({QString::number(i) + QStringLiteral(".srt"), content});
    require(SubtitleArchive::decode(zip(many), members) == Result::TooManyEntries && members.isEmpty(), "bound archive entries");
    require(SubtitleArchive::decode(zip({{QStringLiteral("large.srt"), QByteArray(9 * 1024 * 1024, 'x')}}), members) == Result::TooLarge, "bound expanded subtitle bytes");
    require(SubtitleArchive::decode(zip({{QStringLiteral("readme.txt"), content}}), members) == Result::NoSupportedFiles, "skip files outside the supported subtitle formats");
    const auto dataOffset = archive.indexOf(content);
    require(dataOffset >= 0, "stored test payload");
    archive[dataOffset] = 'X';
    require(SubtitleArchive::decode(archive, members) == Result::Invalid && members.isEmpty(), "reject corrupt archive CRC without publishing partial members");
    qInfo() << "Subtitle naming, matching, cue and bounded ZIP64 archive contracts passed";
}
