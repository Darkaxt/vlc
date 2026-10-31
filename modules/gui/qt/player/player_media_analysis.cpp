// SPDX-License-Identifier: GPL-2.0-or-later
#ifdef HAVE_CONFIG_H
# include "config.h"
#endif
#include "player_media_analysis.hpp"
#include "mpv_playback.hpp"
#include "player_media_tools.hpp"
#include <vlc_block.h>
#include <vlc_picture.h>
#include <QThread>
#include <QWaitCondition>
#include <QPainter>
#include <algorithm>
#include <array>
#include <cmath>
#include <cstring>

void PlayerAnalysisStrip::paint(QPainter *painter)
{
    if (width() <= 0 || height() <= 0) return;
    painter->setClipRect(boundingRect());
    if (!m_samples.isEmpty()) {
        const int columns = std::min(4096, std::max(1, int(std::ceil(width()))));
        for (int x = 0; x < columns; ++x) {
            const auto first = qsizetype(double(x) / columns * m_samples.size());
            const auto last = std::min(m_samples.size(), std::max(first + 1,
                qsizetype(std::ceil(double(x + 1) / columns * m_samples.size()))));
            double peak = 0;
            for (auto i = first; i < last; ++i) peak = std::max(peak, m_samples[i].toDouble());
            const double h = std::max(1., std::clamp(peak, 0., 1.) * std::max(0., height() - 4));
            painter->fillRect(QRectF(double(x) / columns * width(), (height() - h) / 2,
                                     width() / columns, h), m_color);
        }
        return;
    }
    if (!(m_duration > 0) || !std::isfinite(m_duration) || !(m_scale > 0)
        || !std::isfinite(m_scale) || !std::isfinite(m_delay)) return;
    double lastEnd = -1;
    for (const auto &value : m_cues) {
        const auto cue = value.toMap();
        const double start = std::max(0., std::floor((cue.value(QStringLiteral("start")).toDouble() * m_scale + m_delay) / m_duration * width()));
        const double end = std::min(width(), std::ceil((cue.value(QStringLiteral("end")).toDouble() * m_scale + m_delay) / m_duration * width()));
        if (end <= start || end <= lastEnd) continue;
        const double left = std::max(start, lastEnd);
        painter->fillRect(QRectF(left, 1, std::max(1., end - left), std::max(0., height() - 2)), m_color);
        lastEnd = end;
    }
}

static void prepareAnalysisInput(input_item_t *item)
{
    // Auxiliary decoding must not inherit the primary player's pause, repeat
    // or playback-range restrictions. These options belong only to its copy.
    for (const auto *option : {"no-start-paused", "input-repeat=0", "start-time=0", "stop-time=0", "run-time=0"})
        input_item_AddOption(item, option, VLC_INPUT_OPTION_TRUSTED);
}

// One bounded, optional background audio decode; no output device, disk cache,
// sampling deadline or playback-clock dependency. Cancellation uses VLC Stop.
class WaveformWorker : public QThread
{
public:
    WaveformWorker(qt_intf_t *intf, const QUrl &url, double seconds, int track, QObject *parent)
        : QThread(parent), m_intf(intf), m_url(url), m_seconds(seconds), m_track(track) {}
    void cancel()
    {
        // Callbacks acquire only m_completionMutex, never m_handleMutex. This
        // keeps the decoder alive through Stop without a lock-order inversion.
        QMutexLocker lock(&m_handleMutex); m_cancelled = true;
        if (m_decoder) { vlc_player_locker playerLock(m_decoder); vlc_player_Stop(m_decoder); }
    }
    QVariantList result() const { QVariantList out; for (float peak : m_peaks) out.append(peak); return out; }
    bool successful() const { return !m_cancelled && !m_error && m_alignedSamples > 0; }
    bool decodedAudio() const { return m_samples > 0; }
protected:
    void run() override
    {
        auto *player = vlc_player_New(VLC_OBJECT(m_intf), VLC_PLAYER_LOCK_NORMAL);
        if (!player) { m_error = true; return; }
        auto *media = input_item_New(m_url.toEncoded().constData(), "Waveform analysis");
        if (!media) { m_error = true; vlc_player_Delete(player); return; }
        const auto address = [](auto pointer) { return QString::number(qulonglong(reinterpret_cast<uintptr_t>(pointer))); };
        const QString output = QStringLiteral("sout=#transcode{vcodec=none,acodec=fl32,channels=1,samplerate=8000}:smem{audio-prerender-callback=%1,audio-postrender-callback=%2,audio-data=%3,time-sync=0}")
            .arg(address(&WaveformWorker::prerender), address(&WaveformWorker::postrender), address(this));
        const QStringList options{output, QStringLiteral("no-video"), QStringLiteral("no-spu"), QStringLiteral("sout-audio"), QStringLiteral("no-sout-video"), QStringLiteral("no-sout-all"), QStringLiteral("no-sout-keep"), QStringLiteral("no-input-fast-seek"), QStringLiteral("avcodec-threads=1"), QStringLiteral("audio-track=%1").arg(m_track)};
        prepareAnalysisInput(media);
        for (const auto &option : options) input_item_AddOption(media, option.toUtf8().constData(), VLC_INPUT_OPTION_TRUSTED);
        vlc_player_cbs callbacks{};
        callbacks.on_state_changed = [](vlc_player_t *, vlc_player_state state, void *data) {
            if (state != VLC_PLAYER_STATE_STOPPED) return;
            auto *self = static_cast<WaveformWorker *>(data); QMutexLocker lock(&self->m_completionMutex);
            self->m_stopped = true; self->m_completed.wakeAll();
        };
        callbacks.on_error_changed = [](vlc_player_t *, vlc_player_error error, void *data) {
            if (error != VLC_PLAYER_ERROR_NONE) { auto *self = static_cast<WaveformWorker *>(data); QMutexLocker lock(&self->m_completionMutex); self->m_error = true; }
        };
        vlc_player_listener_id *listener = nullptr; bool started = false;
        {
            QMutexLocker handle(&m_handleMutex); m_decoder = player;
            vlc_player_locker lock(player);
            listener = vlc_player_AddListener(player, &callbacks, this);
            if (!m_cancelled && listener && vlc_player_SetCurrentMedia(player, media) == VLC_SUCCESS)
                started = vlc_player_Start(player) == VLC_SUCCESS;
        }
        input_item_Release(media);
        if (started) { QMutexLocker lock(&m_completionMutex); while (!m_stopped) m_completed.wait(&m_completionMutex); }
        else { QMutexLocker lock(&m_completionMutex); m_error = true; }
        { QMutexLocker handle(&m_handleMutex); m_decoder = nullptr; }
        { vlc_player_locker lock(player); if (listener) vlc_player_RemoveListener(player, listener); }
        vlc_player_Delete(player); // Join decoder/output callbacks before result publication.
    }
private:
    static void prerender(void *data, uint8_t **buffer, size_t size)
    {
        auto *self = static_cast<WaveformWorker *>(data);
        if (size > 1024 * 1024) { *buffer = nullptr; return; }
        self->m_pcm.resize(qsizetype(size)); *buffer = reinterpret_cast<uint8_t *>(self->m_pcm.data());
    }
    static void postrender(void *data, uint8_t *buffer, unsigned channels, unsigned rate, unsigned samples, unsigned bits, size_t size, vlc_tick_t pts)
    {
        auto *self = static_cast<WaveformWorker *>(data);
        if (bits != 32 || channels != 1 || rate == 0 || size < size_t(samples) * sizeof(float)) return;
        const auto *pcm = reinterpret_cast<const float *>(buffer);
        for (unsigned i = 0; i < samples; ++i) {
            const double seconds = double(pts) / CLOCK_FREQ + double(i) / rate;
            ++self->m_samples;
            if (!std::isfinite(seconds) || seconds < 0 || seconds >= self->m_seconds) continue;
            ++self->m_alignedSamples;
            const size_t bin = std::min(self->m_peaks.size() - 1, size_t(seconds / self->m_seconds * self->m_peaks.size()));
            if (std::isfinite(pcm[i])) self->m_peaks[bin] = std::max(self->m_peaks[bin], std::min(1.f, std::abs(pcm[i])));
        }
    }
    qt_intf_t *m_intf;
    QUrl m_url;
    double m_seconds;
    int m_track;
    QMutex m_handleMutex, m_completionMutex;
    QWaitCondition m_completed;
    vlc_player_t *m_decoder = nullptr;
    bool m_cancelled = false, m_stopped = false, m_error = false;
    QByteArray m_pcm;
    std::array<float, 2048> m_peaks{};
    quint64 m_samples = 0, m_alignedSamples = 0;
};

PlayerMediaAnalysis::PlayerMediaAnalysis(qt_intf_t *intf, PlayerController *player, PlayerMediaTools *tools)
    : QObject(tools), m_intf(intf), m_player(player), m_tools(tools)
{
    vlc_preparser_cfg configuration{}; configuration.types = VLC_PREPARSER_TYPE_THUMBNAIL;
    configuration.max_thumbnailer_threads = 1; configuration.timeout = 0;
    m_preparser = vlc_preparser_New(VLC_OBJECT(intf), &configuration);
    connect(player, &PlayerController::inputChanged, this, &PlayerMediaAnalysis::inputChanged);
    connect(player, &PlayerController::playbackEngineChanged, this, &PlayerMediaAnalysis::inputChanged);
    connect(player, &PlayerController::lengthChanged, this, [this] { updateWaveform(); });
    connect(player, &PlayerController::lengthChanged, this, &PlayerMediaAnalysis::previewChanged);
    connect(player, &PlayerController::seekableChanged, this, &PlayerMediaAnalysis::previewChanged);
    connect(player->getVideoTracks(), &TrackListModel::countChanged, this, &PlayerMediaAnalysis::previewChanged);
    connect(player, &PlayerController::seekableChanged, this, [this] { updateWaveform(); });
    connect(tools, &PlayerMediaTools::analysisTogglesChanged, this, [this] { updateWaveform(); });
    connect(player->getAudioTracks(), &TrackListModel::countChanged, this, [this] { updateWaveform(); });
    connect(player->getAudioTracks(), &QAbstractItemModel::dataChanged, this, [this] { updateWaveform(); });
    inputChanged();
}
QString PlayerMediaAnalysis::previewStatus() const
{
    if (m_player->usesMpv()) return tr("Seek previews require VLC playback. The MPV video keeps its Dolby Vision color processing.");
    if (!previewSupported()) return tr("Seek previews are unavailable for nonseekable inputs or inputs without a known video timeline.");
    return m_previewStatus;
}
PlayerMediaAnalysis::~PlayerMediaAnalysis()
{
    ++m_generation; m_wantPreview = false; m_wantWaveform = false;
    if (m_preparser) { vlc_preparser_Cancel(m_preparser, nullptr); vlc_preparser_Delete(m_preparser); }
    if (m_request) { vlc_preparser_req_Release(m_request); m_request = nullptr; }
    if (m_worker) { m_worker->cancel(); m_worker->wait(); delete m_worker; m_worker = nullptr; }
}
void PlayerMediaAnalysis::inputChanged()
{
    ++m_generation; ++m_waveGeneration; m_wantPreview = false;
    if (m_request) { m_requestCancelled = true; vlc_preparser_Cancel(m_preparser, m_request); }
    { QMutexLocker lock(&m_image->mutex); m_image->image = {}; }
    m_previewSource.clear(); m_previewStatus = tr("Hover the seek bar for a preview of this input."); emit previewChanged();
    m_waveInput = QUrl(); m_waveAudioTrack = -1; m_waveform.clear(); updateWaveform(true);
}
void PlayerMediaAnalysis::requestPreview(double position)
{
    if (m_player->usesMpv()) { hidePreview(); m_previewSource.clear(); emit previewChanged(); return; }
    if (!std::isfinite(position)) return;
    const double wanted = std::round(std::clamp(position, 0., 1.) * 1000.) / 1000.;
    // Hover points can be re-emitted when the preview renders. One unchanged
    // position owns one request/result until the pointer leaves or moves.
    if (m_wantPreview && !m_requestCancelled && wanted == m_wantedPosition) return;
    m_wantedPosition = wanted; m_wantPreview = true;
    if (!m_player->isSeekable() || !m_player->getLength().valid() || m_player->getVideoTracks()->getCount() == 0) {
        m_wantPreview = false;
        if (m_request) { m_requestCancelled = true; vlc_preparser_Cancel(m_preparser, m_request); }
        m_previewSource.clear(); m_previewStatus = tr("Seek previews are unavailable for nonseekable inputs or inputs without a known video timeline."); emit previewChanged(); return;
    }
    if (m_request) { m_requestCancelled = true; vlc_preparser_Cancel(m_preparser, m_request); return; }
    startPreview();
}
void PlayerMediaAnalysis::hidePreview()
{
    m_wantPreview = false; if (m_request) { m_requestCancelled = true; vlc_preparser_Cancel(m_preparser, m_request); }
}
void PlayerMediaAnalysis::startPreview()
{
    if (!m_preparser || !m_wantPreview || m_request) return;
    m_requestCancelled = false;
    struct Context { PlayerMediaAnalysis *self; quint64 generation; double position; };
    auto *context = new Context{this, m_generation, m_wantedPosition};
    vlc_thumbnailer_arg argument{}; argument.seek.type = vlc_thumbnailer_arg::seek::VLC_THUMBNAILER_SEEK_POS;
    argument.seek.pos = m_wantedPosition; argument.seek.speed = vlc_thumbnailer_arg::seek::VLC_THUMBNAILER_SEEK_PRECISE;
    static const vlc_thumbnailer_cbs callbacks{[](vlc_preparser_req *request, int status, picture_t *picture, void *opaque) {
        std::unique_ptr<Context> ctx(static_cast<Context *>(opaque)); auto *self = ctx->self;
        QImage image;
        if (status == VLC_SUCCESS && picture) {
            block_t *encoded = nullptr; video_format_t format{};
            if (picture_Export(VLC_OBJECT(self->m_intf), &encoded, &format, picture, VLC_CODEC_PNG, 320, 180, false) == VLC_SUCCESS && encoded) {
                image = QImage::fromData(encoded->p_buffer, qsizetype(encoded->i_buffer), "PNG"); block_Release(encoded); video_format_Clean(&format);
            }
        }
        QMetaObject::invokeMethod(self, [self, request, generation = ctx->generation, position = ctx->position, image] {
            if (self->m_request != request) return;
            const bool cancelled = self->m_requestCancelled;
            self->m_request = nullptr; self->m_requestCancelled = false; vlc_preparser_req_Release(request);
            if (!cancelled && generation == self->m_generation && self->m_wantPreview && position == self->m_wantedPosition) {
                if (image.isNull()) { self->m_previewSource.clear(); self->m_previewStatus = tr("VLC could not decode a seek preview for this input."); }
                else {
                    { QMutexLocker lock(&self->m_image->mutex); self->m_image->image = image; }
                    self->m_publishedPosition = position;
                    self->m_previewSource = QStringLiteral("image://redesignPreview/frame/%1").arg(++self->m_imageRevision);
                    self->m_previewStatus.clear();
                }
                emit self->previewChanged();
            }
            if (self->m_wantPreview && (cancelled || generation != self->m_generation || position != self->m_wantedPosition)) self->startPreview();
        }, Qt::QueuedConnection);
    }};
    input_item_t *source = nullptr;
    {
        vlc_player_locker lock(m_player->getPlayer());
        if (auto *input = vlc_player_GetCurrentMedia(m_player->getPlayer())) source = input_item_Hold(input);
    }
    input_item_t *copy = source ? input_item_Copy(source) : nullptr;
    if (source) input_item_Release(source);
    if (copy) {
        prepareAnalysisInput(copy);
        m_request = vlc_preparser_req_NewThumbnail(m_preparser, copy, &argument, &callbacks, context);
        input_item_Release(copy);
    }
    if (!m_request) { delete context; m_previewStatus = tr("Seek preview decoder is unavailable."); emit previewChanged(); return; }
    if (vlc_preparser_Submit(m_preparser, m_request) != VLC_SUCCESS) {
        vlc_preparser_req_Release(m_request); m_request = nullptr; delete context;
        m_previewStatus = tr("Seek preview could not be started."); emit previewChanged(); return;
    }
    m_previewStatus = tr("Decoding seek preview…"); emit previewChanged();
}
void PlayerMediaAnalysis::updateWaveform(bool invalidate)
{
    const QUrl url = m_player->getUrl(); int trackIndex = -1;
    if (m_player->usesMpv()) {
        int ordinal = 0;
        for (const auto &entry : m_player->mpvPlayback()->value(QStringLiteral("track-list")).toList()) {
            const auto track = entry.toMap();
            if (track.value(QStringLiteral("type")).toString() != QStringLiteral("audio")) continue;
            if (track.value(QStringLiteral("selected")).toBool()) { trackIndex = ordinal; break; }
            ++ordinal;
        }
    } else {
        vlc_player_locker lock(m_player->getPlayer()); const auto *selected = vlc_player_GetSelectedTrack(m_player->getPlayer(), AUDIO_ES);
        for (size_t i = 0; selected && i < vlc_player_GetTrackCount(m_player->getPlayer(), AUDIO_ES); ++i)
            if (vlc_player_GetTrackAt(m_player->getPlayer(), AUDIO_ES, i)->es_id == selected->es_id) { trackIndex = int(i); break; }
    }
    const bool enabled = m_tools->waveformVisible();
    const double seconds = double(m_player->getLength().toVLCTick()) / CLOCK_FREQ;
    const bool supported = enabled && url.isLocalFile() && m_player->isSeekable() && seconds > 0 && trackIndex >= 0;
    if (invalidate || url != m_waveInput || trackIndex != m_waveAudioTrack || !supported) {
        ++m_waveGeneration; m_waveform.clear(); if (m_worker) m_worker->cancel();
    }
    m_wantWaveform = supported;
    if (!supported) {
        m_waveformStatus = !enabled ? tr("Audio waveform is off.") : tr("Audio waveform is unavailable for this input: a seekable local audio track with known duration is required."); emit waveformChanged(); return;
    }
    if (m_worker || (!invalidate && url == m_waveInput && trackIndex == m_waveAudioTrack && !m_waveform.isEmpty())) return;
    m_waveInput = url; m_waveAudioTrack = trackIndex; const auto generation = m_waveGeneration;
    m_waveformStatus = tr("Decoding the selected audio track for its waveform…");
    auto *worker = new WaveformWorker(m_intf, url, seconds, trackIndex, this); m_worker = worker;
    connect(worker, &QThread::finished, this, [this, worker, generation] {
        m_worker = nullptr;
        if (generation == m_waveGeneration && m_wantWaveform) {
            if (worker->successful()) { m_waveform = worker->result(); m_waveformStatus = tr("Waveform of the decoded source audio; 2048 peak bins, no disk cache."); }
            else m_waveformStatus = worker->decodedAudio() ? tr("Decoded audio timestamps could not be aligned with this input's timeline.") : tr("VLC could not decode a waveform for this input.");
        }
        worker->deleteLater(); emit waveformChanged();
        if (generation != m_waveGeneration && m_wantWaveform) updateWaveform();
    });
    worker->start(); emit waveformChanged();
}
