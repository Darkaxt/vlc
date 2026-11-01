// SPDX-License-Identifier: GPL-2.0-or-later
#ifndef VLC_QT_EMBEDDED_SUBTITLES_HPP
#define VLC_QT_EMBEDDED_SUBTITLES_HPP
#include <QDateTime>
#include <QFileInfo>
#include <QThread>
#include <QVariantList>
#include <atomic>
#include <algorithm>
#include <limits>
#ifdef VLC_QT_EMBEDDED_SUBTITLES
extern "C" {
#include <libavformat/avformat.h>
#include <libavcodec/avcodec.h>
#include <libavcodec/codec_desc.h>
}
#endif

struct EmbeddedSubtitleResult {
    QVariantList cues;
    QString error;
    bool cancelled = false;
};

// Read only the selected container subtitle stream. No video/audio decoder,
// output device, subprocess, network input or persistent cache is involved.
inline EmbeddedSubtitleResult readEmbeddedSubtitles(const QString &path, int ordinal,
    int ffIndex, const std::atomic_bool &cancelled)
{
    EmbeddedSubtitleResult result;
#ifdef VLC_QT_EMBEDDED_SUBTITLES
    const QFileInfo before(path);
    if (!before.isFile() || !before.isReadable()) {
        result.error = QStringLiteral("The playing media file is unavailable."); return result;
    }
    auto *format = avformat_alloc_context();
    if (!format) { result.error = QStringLiteral("Could not allocate subtitle reader."); return result; }
    format->interrupt_callback = {[](void *data) {
        return static_cast<const std::atomic_bool *>(data)->load() ? 1 : 0;
    }, const_cast<std::atomic_bool *>(&cancelled)};
    AVDictionary *options = nullptr;
    av_dict_set(&options, "protocol_whitelist", "file", 0);
    av_dict_set(&options, "max_streams", "128", 0);
    const int opened = avformat_open_input(&format, path.toUtf8().constData(), nullptr, &options);
    av_dict_free(&options);
    if (opened < 0) {
        avformat_close_input(&format);
        result.cancelled = cancelled.load();
        if (!result.cancelled) result.error = QStringLiteral("Could not read this container's subtitle streams.");
        return result;
    }
    int selected = -1, subtitleOrdinal = 0;
    for (unsigned i = 0; i < format->nb_streams; ++i) {
        auto *stream = format->streams[i];
        stream->discard = AVDISCARD_ALL;
        if (stream->codecpar->codec_type != AVMEDIA_TYPE_SUBTITLE) continue;
        if (ffIndex >= 0 ? int(i) == ffIndex : subtitleOrdinal == ordinal) selected = int(i);
        ++subtitleOrdinal;
    }
    if (selected < 0) {
        result.error = QStringLiteral("The selected subtitle stream is not present in this container.");
        avformat_close_input(&format); return result;
    }
    auto *stream = format->streams[selected];
    const auto *description = avcodec_descriptor_get(stream->codecpar->codec_id);
    if (!description || !(description->props & AV_CODEC_PROP_TEXT_SUB)) {
        result.error = QStringLiteral("Image subtitles keep playing normally; a text cue timeline is unavailable.");
        avformat_close_input(&format); return result;
    }
    if (stream->codecpar->extradata_size > 8 * 1024 * 1024) {
        result.error = QStringLiteral("Subtitle headers exceed the timeline's size limit.");
        avformat_close_input(&format); return result;
    }
    const auto *decoder = avcodec_find_decoder(stream->codecpar->codec_id);
    auto *codec = decoder ? avcodec_alloc_context3(decoder) : nullptr;
    if (!codec || avcodec_parameters_to_context(codec, stream->codecpar) < 0 || avcodec_open2(codec, decoder, nullptr) < 0) {
        result.error = QStringLiteral("This embedded text subtitle decoder is unavailable.");
        avcodec_free_context(&codec); avformat_close_input(&format); return result;
    }
    codec->pkt_timebase = stream->time_base;
    codec->thread_count = 1;
    stream->discard = AVDISCARD_DEFAULT;
    auto *packet = av_packet_alloc();
    const auto origin = format->start_time == AV_NOPTS_VALUE ? 0 : format->start_time;
    qsizetype textBytes = 0;
    int read = AVERROR_EOF;
    while (packet && !cancelled.load() && (read = av_read_frame(format, packet)) >= 0) {
        if (packet->stream_index == selected) {
            if (packet->size > 8 * 1024 * 1024) {
                result.error = QStringLiteral("A subtitle packet exceeds the timeline's size limit."); break;
            }
            AVSubtitle subtitle{};
            int produced = 0;
            const int decoded = avcodec_decode_subtitle2(codec, &subtitle, &produced, packet);
            if (decoded < 0) {
                avsubtitle_free(&subtitle);
                result.error = QStringLiteral("Could not decode this embedded text subtitle track."); break;
            }
            if (produced) {
                const auto pts = subtitle.pts != AV_NOPTS_VALUE ? subtitle.pts
                    : packet->pts != AV_NOPTS_VALUE ? av_rescale_q(packet->pts, stream->time_base, AV_TIME_BASE_Q) : AV_NOPTS_VALUE;
                const qint64 start = pts == AV_NOPTS_VALUE ? -1 : (pts - origin) / 1000 + subtitle.start_display_time;
                qint64 end = -1;
                if (pts != AV_NOPTS_VALUE && subtitle.end_display_time > subtitle.start_display_time
                    && subtitle.end_display_time != std::numeric_limits<uint32_t>::max())
                    end = (pts - origin) / 1000 + subtitle.end_display_time;
                else if (pts != AV_NOPTS_VALUE && packet->duration > 0)
                    end = (pts - origin) / 1000 + av_rescale_q(packet->duration, stream->time_base, AVRational{1, 1000});
                QString text;
                for (unsigned r = 0; r < subtitle.num_rects; ++r) {
                    const auto *rect = subtitle.rects[r];
                    if (rect->text) text += QString::fromUtf8(rect->text);
                    else if (rect->ass) text += QString::fromUtf8(rect->ass);
                }
                textBytes += text.toUtf8().size();
                if (textBytes > 8 * 1024 * 1024 || result.cues.size() >= 100000) {
                    avsubtitle_free(&subtitle);
                    result.error = QStringLiteral("This subtitle track exceeds the bounded timeline capacity."); break;
                }
                if (pts != AV_NOPTS_VALUE && end > std::max<qint64>(0, start) && !text.trimmed().isEmpty())
                    result.cues.append(QVariantMap{{QStringLiteral("start"), std::max<qint64>(0, start)},
                        {QStringLiteral("end"), end}, {QStringLiteral("text"), text}});
            }
            avsubtitle_free(&subtitle);
        }
        av_packet_unref(packet);
    }
    result.cancelled = cancelled.load();
    if (!packet || (read < 0 && read != AVERROR_EOF && !result.cancelled))
        result.error = QStringLiteral("The media could not be read completely for its subtitle timeline.");
    av_packet_free(&packet); avcodec_free_context(&codec); avformat_close_input(&format);
    const QFileInfo after(path);
    if (!after.exists() || after.size() != before.size() || after.lastModified() != before.lastModified())
        result.error = QStringLiteral("The media file changed while its subtitle timeline was being read.");
    if (result.cancelled || !result.error.isEmpty()) result.cues.clear();
    std::stable_sort(result.cues.begin(), result.cues.end(), [](const QVariant &a, const QVariant &b) {
        return a.toMap().value(QStringLiteral("start")).toLongLong() < b.toMap().value(QStringLiteral("start")).toLongLong();
    });
#else
    Q_UNUSED(path) Q_UNUSED(ordinal) Q_UNUSED(ffIndex) Q_UNUSED(cancelled)
    result.error = QStringLiteral("This build has no embedded text timeline decoder.");
#endif
    return result;
}

class EmbeddedSubtitleWorker final : public QThread
{
public:
    EmbeddedSubtitleWorker(QString file, int ordinal, int ffIndex, QObject *parent)
        : QThread(parent), file(std::move(file)), ordinal(ordinal), ffIndex(ffIndex) {}
    void cancel() { cancelled.store(true); }
    EmbeddedSubtitleResult result;
protected:
    void run() override { result = readEmbeddedSubtitles(file, ordinal, ffIndex, cancelled); }
private:
    QString file;
    int ordinal, ffIndex;
    std::atomic_bool cancelled{false};
};
#endif
