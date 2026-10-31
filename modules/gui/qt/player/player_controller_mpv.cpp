/* Copyright (C) 2026 VLC authors and VideoLAN
 * SPDX-License-Identifier: GPL-2.0-or-later
 */
#ifdef HAVE_CONFIG_H
# include "config.h"
#endif
#include "player_controller.hpp"
#include "player_controller_p.hpp"
#include "mpv_playback.hpp"
#include "maininterface/mainctx.hpp"
#include "maininterface/compositor.hpp"
#include "medialibrary/medialib.hpp"
#include <vlc_media_library.h>
#include "playlist/playlist_controller.hpp"
#include <vlc_dialog.h>
#include <vlc_url.h>
#include <vlc_preparser.h>
#include <QFileInfo>
#include <QSemaphore>
#include <cmath>
#include <algorithm>

struct MpvPlaylistRequest
{
    PlayerController *owner = nullptr;
    vlc_preparser_t *parser = nullptr;
    vlc_preparser_req *request = nullptr;
    SharedInputItem item;
    QVector<SharedInputItem> children;
    QSemaphore ended;
    quint64 revision = 0;
    bool paused = false;
};

static void collectMpvPlaylistItems(const input_item_node_t *node, QVector<SharedInputItem> &items)
{
    for (int i = 0; i < node->i_children; ++i) {
        const auto *child = node->pp_children[i];
        items.push_back(SharedInputItem(child->p_item));
        collectMpvPlaylistItems(child, items);
    }
}

bool PlayerController::usesMpv() const { Q_D(const PlayerController); return bool(d->m_mpv); }
QString PlayerController::playbackEngine() const { return usesMpv() ? QStringLiteral("mpv") : QStringLiteral("vlc"); }
bool PlayerController::engineSwitching() const { Q_D(const PlayerController); return d->m_engineSwitching; }
MpvPlayback *PlayerController::mpvPlayback() const { Q_D(const PlayerController); return d->m_mpv.get(); }
bool PlayerController::mpvAutostart() const { Q_D(const PlayerController); return d->p_intf->mpvAutostart; }
bool PlayerController::mpvStartPaused() const { Q_D(const PlayerController); return var_InheritBool(d->p_intf, "start-paused"); }
#ifdef VLC_PLAYER_DIAGNOSTICS
bool PlayerController::mpvHistoryReady() const { Q_D(const PlayerController); return d->m_mpvHistoryReady; }
#endif

void PlayerController::requireVlcTool(const QString &tool)
{
    Q_D(PlayerController);
    vlc_dialog_display_error(VLC_OBJECT(d->p_intf), "Playback tool", "%s",
        qtu(tr("%1 requires VLC playback. Switch to VLC in the in-player Playback settings.").arg(tool)));
}

void PlayerController::initializeMpvPlayback()
{
    Q_D(PlayerController);
    assert(!d->m_mpv);
    d->m_mpv = d->m_mpvCandidate ? std::move(d->m_mpvCandidate) : std::make_unique<MpvPlayback>(d->p_intf, this);
    d->m_mpvVolumeReady = false;
    const auto select = [d](const QString &property, const QString &id, bool selected) {
        if (property == QStringLiteral("sid") && d->m_subtitleTracks.getMultiSelect()) {
            const QString primary = d->m_mpv->value(QStringLiteral("sid")).toString();
            const QString secondary = d->m_mpv->value(QStringLiteral("secondary-sid")).toString();
            if (selected && primary.toLongLong() > 0 && primary != id)
                d->m_mpv->set(QStringLiteral("secondary-sid"), id);
            else if (!selected && secondary == id)
                d->m_mpv->set(QStringLiteral("secondary-sid"), QStringLiteral("no"));
            else d->m_mpv->set(property, selected ? id : QStringLiteral("no"));
        } else d->m_mpv->set(property, selected ? id : QStringLiteral("no"));
    };
    d->m_videoTracks.setExternalSelection([select](const QString &id, bool selected) { select(QStringLiteral("vid"), id, selected); });
    d->m_audioTracks.setExternalSelection([select](const QString &id, bool selected) { select(QStringLiteral("aid"), id, selected); });
    d->m_subtitleTracks.setExternalSelection([select](const QString &id, bool selected) { select(QStringLiteral("sid"), id, selected); });
    connect(d->m_mpv.get(), &MpvPlayback::seekStarted, this, [d] {
        if (d->m_engineSeekPending) d->m_engineMpvSeekStarted = true;
    });
    connect(d->m_mpv.get(), &MpvPlayback::playbackRestarted, this, [this, d] {
        if (d->m_engineSeekPending && d->m_engineMpvSeekStarted) finishEngineHandoff();
    });
    connect(d->m_mpv.get(), &MpvPlayback::failed, this, [this, d](const QString &error) {
        // A rejected incoming command is a terminal handover result, not a
        // reason to leave engine selection busy while awaiting a seek event
        // that the native player will never emit. Keep the loaded input paused
        // for explicit retry/engine selection after displaying the real error.
        if (d->m_engineRestorePending || d->m_engineSeekPending) {
            cancelEngineRestart();
            d->m_mpvHistoryReady = d->m_mpvLoaded;
        }
        vlc_dialog_display_error(VLC_OBJECT(d->p_intf), "MPV playback", "%s", qtu(error));
    });
    connect(d->m_mpv.get(), &MpvPlayback::changed, this, [this, d](const QString &name, const QVariant &value) {
        if (name == QStringLiteral("time-pos") || name == QStringLiteral("duration")) {
            // MPV makes these properties unavailable while stopping, before
            // END_FILE saves history. QVariant's unchecked conversion turned
            // that absence into zero and overwrote the actual resume position.
            if (!value.isValid() || value.isNull()) return;
            bool timeKnown = false, durationKnown = false;
            const double time = d->m_mpv->value(QStringLiteral("time-pos")).toDouble(&timeKnown);
            double duration = d->m_mpv->value(QStringLiteral("duration")).toDouble(&durationKnown);
            if (!timeKnown || !std::isfinite(time)) return;
            // A live stream can have a real clock and no duration. Preserve its
            // unknown-length presentation while still advancing that clock.
            if (!durationKnown || !std::isfinite(duration) || duration < 0.)
                duration = double(d->m_length.toVLCTick()) / CLOCK_FREQ;
            d->m_time = VLCTime(vlc_tick_t(time * CLOCK_FREQ));
            d->m_length = VLCDuration(vlc_tick_t(duration * CLOCK_FREQ));
            d->m_remainingTime = VLCDuration(vlc_tick_t(std::max(0., duration - time) * CLOCK_FREQ));
            d->m_position = duration > 0 ? std::clamp(time / duration, 0., 1.) : 0.;
            emit timeChanged(d->m_time); emit lengthChanged(d->m_length);
            emit remainingTimeChanged(VLCTime(d->m_remainingTime.toVLCTick()));
            emit positionChanged(d->m_position); emit positionUpdated(d->m_position, d->m_time, d->m_length);
        } else if (name == QStringLiteral("pause") && d->m_currentItem && d->m_mpvLoaded) {
            d->m_playing_status = value.toBool() ? PLAYING_STATE_PAUSED : PLAYING_STATE_PLAYING;
            emit playingStateChanged(d->m_playing_status);
            if (value.toBool()) saveMpvHistory();
        } else if (name == QStringLiteral("speed")) {
            d->m_rate = value.toFloat(); emit rateChanged(d->m_rate);
        } else if (name == QStringLiteral("audio-delay")) {
            d->m_audioDelay = VLCDuration(std::llround(value.toDouble() * CLOCK_FREQ)); emit audioDelayChanged(d->m_audioDelay);
        } else if (name == QStringLiteral("sub-delay")) {
            d->m_subtitleDelay = VLCDuration(std::llround(value.toDouble() * CLOCK_FREQ)); emit subtitleDelayChanged(d->m_subtitleDelay);
        } else if (name == QStringLiteral("secondary-sub-delay")) {
            d->m_secondarySubtitleDelay = VLCDuration(std::llround(value.toDouble() * CLOCK_FREQ)); emit secondarySubtitleDelayChanged(d->m_secondarySubtitleDelay);
        } else if (name == QStringLiteral("track-list")) {
            d->m_videoTracks.updateExternalTracks(value.toList(), QStringLiteral("video"));
            d->m_audioTracks.updateExternalTracks(value.toList(), QStringLiteral("audio"));
            d->m_subtitleTracks.updateExternalTracks(value.toList(), QStringLiteral("sub"));
        } else if (name == QStringLiteral("video-params")) {
            const bool video = !value.toMap().isEmpty();
            if (video != d->m_hasVideo) { d->m_hasVideo = video; emit hasVideoOutputChanged(video); }
        } else if (name == QStringLiteral("seekable")) {
            if (!value.isValid()) return;
            d->m_capabilities = VLC_PLAYER_CAP_PAUSE | VLC_PLAYER_CAP_CHANGE_RATE;
            if (value.toBool()) d->m_capabilities |= VLC_PLAYER_CAP_SEEK;
            emit seekableChanged(value.toBool()); emit rewindableChanged(false);
            emit pausableChanged(true); emit rateChangableChanged(true);
            emit capabilitiesChanged();
        } else if (name == QStringLiteral("paused-for-cache")) {
            d->m_buffering = value.toBool() ? 0.f : 1.f; emit bufferingChanged(d->m_buffering);
        } else if (name == QStringLiteral("chapter-list")) {
            d->m_chapterList.updateExternalChapters(value.toList(), d->m_length.toVLCTick(), [d](int index) {
                d->m_mpv->set(QStringLiteral("chapter"), index);
            });
            d->m_hasChapters = !value.toList().isEmpty();
            emit hasChaptersChanged(d->m_hasChapters);
        } else if (name == QStringLiteral("chapter")) {
            d->m_chapterList.setCurrent(value.toInt());
        } else if (name == QStringLiteral("media-title")) {
            d->m_title = value.toString(); d->m_name = d->m_title;
            emit nameChanged(d->m_name); emit currentMetaChanged(d->m_currentItem.get());
        } else if (name == QStringLiteral("metadata")) {
            const auto tags = value.toMap();
            d->m_artist = tags.value(QStringLiteral("ARTIST"), tags.value(QStringLiteral("artist"))).toString();
            d->m_album = tags.value(QStringLiteral("ALBUM"), tags.value(QStringLiteral("album"))).toString();
            emit currentMetaChanged(d->m_currentItem.get());
        }
    });
    connect(d->m_mpv.get(), &MpvPlayback::fileLoaded, this, [this, d] {
        d->m_mpvLoaded = true;
        d->m_engineCapabilitiesKnown = true;
        d->m_playing_status = d->m_mpv->value(QStringLiteral("pause")).toBool() ? PLAYING_STATE_PAUSED : PLAYING_STATE_PLAYING;
        d->m_buffering = 1.f;
        // Saved associations/presets may submit commands only after MPV has
        // loaded this input. Restore handover values after those defaults.
        emit inputChanged(true);
        if (d->m_engineRestorePending) restoreEngineHandoff();
        else restoreMpvHistory();
        emit playingStateChanged(d->m_playing_status); emit bufferingChanged(1.f);
    });
    connect(d->m_mpv.get(), &MpvPlayback::ended, this, [this, d](bool eof, const QString &error) {
        saveMpvHistory(eof);
        d->m_mpvLoaded = false;
        ++d->m_mpvMediaRevision;
        auto *queue = d->p_intf->p_mainPlaylistController;
        const bool parsingPlaylist = bool(d->m_mpvPlaylistRequest);
        const bool advanceQueue = !parsingPlaylist && !d->m_engineSwitching && !d->m_shutdownRequested;
        const bool continuing = (eof || !error.isEmpty()) && advanceQueue &&
            queue->getMediaStopAction() != vlc::playlist::PlaylistController::MEDIA_STOPPED_STOP &&
            (queue->getRepeatMode() == vlc::playlist::PlaylistController::PLAYBACK_REPEAT_CURRENT || queue->hasNext());
        d->m_playing_status = continuing ? PLAYING_STATE_STARTED : PLAYING_STATE_STOPPED;
        d->m_hasVideo = false;
        {
            vlc_player_locker lock(d->m_player);
            d->m_currentItem.reset(nullptr);
        }
        d->m_videoTracks.clear(); d->m_audioTracks.clear(); d->m_subtitleTracks.clear();
        d->m_chapterList.resetTitle(nullptr); d->m_hasChapters = false; emit hasChaptersChanged(false);
        emit hasVideoOutputChanged(false); emit playingStateChanged(d->m_playing_status); emit inputChanged(false);
        if (d->m_engineRestorePending || d->m_engineSeekPending) cancelEngineRestart();
        if (!error.isEmpty()) {
            msg_Err(d->p_intf, "MPV playback failed: %s", qtu(error));
            vlc_dialog_display_error(VLC_OBJECT(d->p_intf), "MPV playback", "%s", qtu(error));
        }
        // A superseded input ending while its replacement playlist is being
        // parsed must not advance past the user's newly selected container.
        emit mpvPlaybackEnded(eof && advanceQueue, !error.isEmpty() && advanceQueue);
    });
    if (d->m_mpv->isAvailable()) {
        {
            vlc_player_locker lock(d->m_player);
            const float volume = vlc_player_aout_GetVolume(d->m_player);
            const int muted = vlc_player_aout_IsMuted(d->m_player);
            if (volume >= 0.f) d->m_volume = volume;
            if (muted >= 0) d->m_muted = bool(muted);
        }
        // A saved Windows session may not have reported its initial level
        // yet. Keep that state unknown until the native callback arrives;
        // writing a guessed default here could erase the remembered level.
        if (d->m_volume >= 0.f) setVolume(d->m_volume);
        else d->m_mpv->set(QStringLiteral("volume"), 100.);
        emit volumeChanged(d->m_volume);
        emit soundMuteChanged(d->m_muted);
    }
}

void PlayerController::playWithMpv(input_item_t *item, bool paused)
{
    Q_D(PlayerController);
    if (d->m_shutdownRequested || !usesMpv()) return;
    cancelMpvPlaylist();
    if (parseMpvPlaylist(item, paused)) return;
    loadMpvItem(item, paused);
}

bool PlayerController::cancelMpvPlaylist(input_item_t *stillCurrent)
{
    Q_D(PlayerController);
    if (stillCurrent && d->m_mpvPlaylistRequest && d->m_mpvPlaylistRequest->item.get() == stillCurrent) return false;
    ++d->m_mpvPlaylistRevision;
    auto pending = std::move(d->m_mpvPlaylistRequest);
    if (!pending) return false;
    vlc_preparser_Cancel(pending->parser, pending->request);
    // The native callback only queues UI work. Join its actual completion
    // before destroying the owner/context; it never waits on the GUI thread.
    pending->ended.acquire();
    vlc_preparser_req_Release(pending->request);
    return true;
}

bool PlayerController::parseMpvPlaylist(input_item_t *item, bool paused)
{
    Q_D(PlayerController);
    const auto uri = vlc::wrap_cptr(input_item_GetURI(item));
    const QUrl url(qfu(uri.get()));
    const auto suffix = QFileInfo(url.path()).suffix().toLower();
    bool network;
    const auto type = input_item_GetType(item, &network);
    const bool container = type == ITEM_TYPE_DIRECTORY || type == ITEM_TYPE_NODE || type == ITEM_TYPE_PLAYLIST
        || (url.isLocalFile() && QFileInfo(url.toLocalFile()).isDir())
        || QStringList{QStringLiteral("m3u"), QStringLiteral("m3u8"), QStringLiteral("pls"),
            QStringLiteral("xspf"), QStringLiteral("asx"), QStringLiteral("b4s"),
            QStringLiteral("zpl"), QStringLiteral("wpl"), QStringLiteral("cue")}.contains(suffix);
    if (!container) return false;
    auto *parser = d->p_intf->p_mi ? d->p_intf->p_mi->getNetworkPreparser() : nullptr;
    if (!parser) {
        vlc_dialog_display_error(VLC_OBJECT(d->p_intf), "MPV playlist", "%s",
            qtu(tr("VLC's playlist parser is unavailable. Switch to VLC playback or open a media file directly.")));
        return true;
    }
    auto pending = std::make_shared<MpvPlaylistRequest>();
    pending->owner = this; pending->parser = parser; pending->item = SharedInputItem(item);
    pending->revision = d->m_mpvPlaylistRevision; pending->paused = paused;
    const static vlc_preparser_cbs callbacks = {
        [](vlc_preparser_req *, int, void *opaque) {
            auto *context = static_cast<std::shared_ptr<MpvPlaylistRequest> *>(opaque);
            auto pending = *context;
            QMetaObject::invokeMethod(pending->owner, [pending] {
                auto *owner = pending->owner;
                auto *d = owner->d_func();
                if (pending != d->m_mpvPlaylistRequest) return;
                pending->ended.acquire();
                vlc_preparser_req_Release(pending->request);
                d->m_mpvPlaylistRequest.reset();
                if (pending->revision != d->m_mpvPlaylistRevision || d->m_shutdownRequested
                    || d->m_engineSwitching || !owner->usesMpv()) return;
                if (!pending->children.isEmpty()) {
                    d->p_intf->p_mainPlaylistController->expandMpvPlaylist(
                        pending->item.get(), pending->children, pending->paused);
                } else {
                    // HLS manifests and playable streams do not produce a VLC
                    // item subtree. Their original URL belongs to the decoder.
                    {
                        vlc::playlist::vlc_playlist_locker lock(d->p_intf->p_playlist);
                        const auto index = vlc_playlist_GetCurrentIndex(d->p_intf->p_playlist);
                        if (index < 0 || vlc_playlist_item_GetMedia(vlc_playlist_Get(d->p_intf->p_playlist, index))
                            != pending->item.get()) return;
                    }
                    owner->loadMpvItem(pending->item.get(), pending->paused);
                }
            }, Qt::QueuedConnection);
            delete context;
            pending->ended.release();
        },
        [](vlc_preparser_req *, input_item_node_t *subtree, void *opaque) {
            const auto &pending = *static_cast<std::shared_ptr<MpvPlaylistRequest> *>(opaque);
            collectMpvPlaylistItems(subtree, pending->children);
            input_item_node_Delete(subtree);
        },
        nullptr
    };
    auto *context = new std::shared_ptr<MpvPlaylistRequest>(pending);
    pending->request = vlc_preparser_req_NewParse(parser, item,
        VLC_PREPARSER_TYPE_PARSE | VLC_PREPARSER_OPTION_SUBITEMS, &callbacks, context);
    if (!pending->request) {
        delete context;
        vlc_dialog_display_error(VLC_OBJECT(d->p_intf), "MPV playlist", "%s", qtu(tr("The playlist could not be opened.")));
        return true;
    }
    d->m_mpvPlaylistRequest = pending;
    if (vlc_preparser_Submit(parser, pending->request) != VLC_SUCCESS) {
        d->m_mpvPlaylistRequest.reset();
        vlc_preparser_req_Release(pending->request);
        delete context;
        vlc_dialog_display_error(VLC_OBJECT(d->p_intf), "MPV playlist", "%s", qtu(tr("The playlist parser could not start.")));
    }
    return true;
}

void PlayerController::loadMpvItem(input_item_t *item, bool paused)
{
    Q_D(PlayerController);
    assert(d->m_mpv && item);
    if (!d->m_mpv->isAvailable()) {
        vlc_dialog_display_error(VLC_OBJECT(d->p_intf), "MPV playback", "%s", qtu(d->m_mpv->error()));
        return;
    }
    if (d->m_currentItem.get() == item && isStarted()) { d->m_mpv->set(QStringLiteral("pause"), paused); return; }
    saveMpvHistory();
    d->m_mpvLoaded = false;
    d->m_mpvHistoryReady = false;
#ifdef VLC_PLAYER_DIAGNOSTICS
    emit mpvHistoryReadyChanged();
#endif
    ++d->m_mpvMediaRevision;
    d->m_mpvResumePosition = 0.;
    d->m_canRestorePlayback = false;
    emit playbackRestoreQueried();
    {
        vlc_player_locker lock(d->m_player);
        d->m_currentItem = SharedInputItem(item);
    }
    const auto uri = vlc::wrap_cptr(input_item_GetURI(item));
    const auto name = vlc::wrap_cptr(input_item_GetName(item));
    d->m_url = QUrl(qfu(uri.get()));
    d->m_name = qfu(name.get()); d->m_title = d->m_name;
    d->m_time = VLCTime(0); d->m_length = VLCDuration(0); d->m_position = 0.;
    d->m_playing_status = PLAYING_STATE_STARTED;
    d->m_buffering = 0.f;
    d->UpdateArt(item); d->UpdateMeta(item);
    emit nameChanged(d->m_name); emit playingStateChanged(d->m_playing_status);
    emit timeChanged(d->m_time); emit positionChanged(0.); emit lengthChanged(d->m_length); emit bufferingChanged(0.f);
    d->m_mpv->load(d->m_url, paused);
}

void PlayerController::prepareToClose(std::function<void()> completion)
{
    Q_D(PlayerController);
    d->m_shutdownRequested = true;
    cancelMpvPlaylist();
    cancelEngineRestart();
    if (d->m_engineSwitching) {
        auto connection = std::make_shared<QMetaObject::Connection>();
        *connection = connect(this, &PlayerController::engineSwitchingChanged, this,
            [this, connection, completion=std::move(completion)]() mutable {
                if (engineSwitching()) return;
                disconnect(*connection);
                prepareToClose(std::move(completion));
            });
        return;
    }
    if (d->m_mpv) saveMpvHistory(false, [d, completion=std::move(completion)]() mutable {
        d->m_mpv->prepareToClose(std::move(completion));
    });
    else completion();
}

bool PlayerController::cancelEngineRestart(input_item_t *stillCurrent)
{
    Q_D(PlayerController);
    if (stillCurrent && stillCurrent == d->m_engineItem.get()) return false;
    d->m_engineRestart = false;
    if (d->m_engineRestorePending || d->m_engineSeekPending) {
        d->m_engineRestorePending = false;
        d->m_engineSeekPending = false; d->m_engineMpvSeekStarted = false;
        d->m_engineSwitching = false;
        emit engineSwitchingChanged();
    }
    return true;
}

void PlayerController::switchPlaybackEngine(const QString &engine)
{
    Q_D(PlayerController);
    if (d->m_shutdownRequested || d->m_engineSwitching || engine == playbackEngine()) return;
    if (engine != QStringLiteral("vlc") && engine != QStringLiteral("mpv")) return;
    cancelMpvPlaylist();
    if (engine == QStringLiteral("mpv")) {
        if (!d->p_intf->p_compositor || d->p_intf->p_compositor->type() != vlc::Compositor::DirectCompositionCompositor) {
            vlc_dialog_display_error(VLC_OBJECT(d->p_intf), "MPV playback", "%s",
                qtu(tr("MPV requires the DirectComposition video surface. VLC remains selected.")));
            return;
        }
        d->m_mpvCandidate = std::make_unique<MpvPlayback>(d->p_intf, this);
        if (!d->m_mpvCandidate->isAvailable()) {
            const auto error = d->m_mpvCandidate->error();
            d->m_mpvCandidate.reset();
            vlc_dialog_display_error(VLC_OBJECT(d->p_intf), "MPV playback", "%s", qtu(error));
            return;
        }
    }
    d->m_engineItem = SharedInputItem(getInput());
    d->m_engineRestart = isStarted() && bool(d->m_engineItem);
    d->m_engineTime = isSeekable() ? getTime() : VLCTime(0);
    d->m_enginePaused = getPlayingState() == PLAYING_STATE_PAUSED;
    d->m_engineRate = getRate(); d->m_engineVolume = getVolume(); d->m_engineMuted = isMuted();
    d->m_engineAudioDelay = getAudioDelayMS(); d->m_engineSubtitleDelay = getSubtitleDelayMS();
    if (!usesMpv()) {
        // Paused native hotkeys can commit without another UI timer update.
        // The outgoing core owns the handover snapshot, not its cached labels.
        vlc_player_locker lock(d->m_player);
        d->m_engineItem = SharedInputItem(vlc_player_GetCurrentMedia(d->m_player));
        d->m_engineRestart = vlc_player_IsStarted(d->m_player) && bool(d->m_engineItem);
        d->m_engineTime = vlc_player_CanSeek(d->m_player) ? VLCTime(vlc_player_GetTime(d->m_player)) : VLCTime(0);
        d->m_enginePaused = vlc_player_IsPaused(d->m_player);
        d->m_engineRate = vlc_player_GetRate(d->m_player);
        d->m_engineAudioDelay = MS_FROM_VLC_TICK(vlc_player_GetAudioDelay(d->m_player));
        d->m_engineSubtitleDelay = MS_FROM_VLC_TICK(vlc_player_GetSubtitleDelay(d->m_player));
    }
    d->m_engineSwitching = true;
    var_SetBool(vlc_object_instance(d->p_intf), "qt-mpv-active", true);
    {
        vlc_player_locker lock(d->m_player);
        vlc_player_SetExternalPlayback(d->m_player, true);
    }
    emit engineSwitchingChanged();
    if (usesMpv()) {
        saveMpvHistory(false, [this, d] {
            d->m_mpv->prepareToClose([this] {
                // Leave the MPV completion stack before releasing its QObject.
                QMetaObject::invokeMethod(this, &PlayerController::completeEngineSwitch, Qt::QueuedConnection);
            });
        });
    } else {
        auto *compositor = static_cast<vlc::CompositorVideo *>(d->p_intf->p_compositor.get());
        d->m_engineVlcReleased = false;
        d->m_engineWindowConnection = connect(compositor, &vlc::CompositorVideo::videoWindowReleased, this, [this, d] {
            if (d->m_engineVlcReleased) finishVlcEngineRelease(VLC_SUCCESS);
        });
        int status;
        {
            vlc_player_locker lock(d->m_player);
            vlc_player_Stop(d->m_player);
            status = vlc_player_vout_ReleaseUnused(d->m_player, [](void *opaque, int status) {
                auto *controller = static_cast<PlayerController *>(opaque);
                QMetaObject::invokeMethod(controller, [controller, status] {
                    controller->finishVlcEngineRelease(status);
                }, Qt::QueuedConnection);
            }, this);
        }
        if (status != VLC_SUCCESS) finishVlcEngineRelease(status);
    }
}

void PlayerController::finishVlcEngineRelease(int status)
{
    Q_D(PlayerController);
    assert(d->m_engineSwitching && !d->m_mpv && d->m_mpvCandidate);
    if (status != VLC_SUCCESS) {
        disconnect(d->m_engineWindowConnection);
        d->m_mpvCandidate->prepareToClose([this] {
            QMetaObject::invokeMethod(this, [this] {
                Q_D(PlayerController);
                d->m_mpvCandidate.reset();
                d->m_engineRestart = false;
                d->m_engineSwitching = false;
                var_SetBool(vlc_object_instance(d->p_intf), "qt-mpv-active", false);
                {
                    vlc_player_locker lock(d->m_player);
                    vlc_player_SetExternalPlayback(d->m_player, false);
                }
                emit engineSwitchingChanged();
                if (!d->m_shutdownRequested)
                    vlc_dialog_display_error(VLC_OBJECT(d->p_intf), "Playback engine", "%s",
                        qtu(tr("VLC could not release its video resources because its playback state changed. VLC remains selected; retry the switch when playback has settled.")));
            }, Qt::QueuedConnection);
        });
        return;
    }
    d->m_engineVlcReleased = true;
    auto *compositor = static_cast<vlc::CompositorVideo *>(d->p_intf->p_compositor.get());
    if (compositor->hasVideoWindow()) return;
    disconnect(d->m_engineWindowConnection);
    completeEngineSwitch();
}

void PlayerController::completeEngineSwitch()
{
    Q_D(PlayerController);
    if (!d->m_engineSwitching) return;
    const bool toMpv = !bool(d->m_mpv);
    d->m_mpvLoaded = false; d->m_mpvHistoryReady = false;
    ++d->m_nativeEventGeneration;
    d->m_acceptNativeEvents = !toMpv;
    d->m_time_timer.stop();
    if (toMpv && d->m_player_timer_smpte) d->removeSMPTETimer();
    else if (!toMpv && d->m_smpteTimerRequestCount > 0 && !d->m_player_timer_smpte) d->addSMPTETimer();
    d->m_videoTracks.clear(); d->m_audioTracks.clear(); d->m_subtitleTracks.clear();
    d->m_chapterList.resetTitle(nullptr);
    d->m_hasVideo = false; d->m_hasChapters = false;
    emit hasVideoOutputChanged(false); emit hasChaptersChanged(false);
    if (toMpv) initializeMpvPlayback();
    else {
        d->m_mpv.reset();
        d->m_videoTracks.setExternalSelection({}); d->m_audioTracks.setExternalSelection({});
        d->m_subtitleTracks.setExternalSelection({});
    }
    d->p_intf->mpvPlayback = toMpv;
    var_SetBool(vlc_object_instance(d->p_intf), "qt-mpv-active", toMpv);
    {
        vlc_player_locker lock(d->m_player);
        vlc_player_SetExternalPlayback(d->m_player, toMpv);
    }
    d->m_playing_status = PLAYING_STATE_STOPPED;
    emit playbackEngineChanged();
    bool sameItem = false;
    {
        auto *playlist = d->p_intf->p_playlist;
        vlc::playlist::vlc_playlist_locker lock(playlist);
        const auto index = vlc_playlist_GetCurrentIndex(playlist);
        sameItem = index >= 0 && vlc_playlist_item_GetMedia(vlc_playlist_Get(playlist, index)) == d->m_engineItem.get();
    }
    const bool restart = d->m_engineRestart && sameItem && !d->m_shutdownRequested;
    d->m_engineCapabilitiesKnown = false;
    d->m_engineSeekPending = false; d->m_engineMpvSeekStarted = false;
    d->m_engineRestorePending = restart;
    if (!restart) {
        d->m_engineSwitching = false; emit engineSwitchingChanged();
        emit playingStateChanged(PLAYING_STATE_STOPPED); return;
    }
    if (toMpv) playWithMpv(d->m_engineItem.get(), true);
    else {
        vlc_player_locker lock(d->m_player);
        vlc_player_SetStartPaused(d->m_player, true);
        vlc_player_Start(d->m_player);
        vlc_player_SetStartPaused(d->m_player, false);
    }
}

void PlayerController::restoreEngineHandoff()
{
    Q_D(PlayerController);
    if (!d->m_engineRestorePending || d->m_shutdownRequested) return;
    if (!usesMpv() && getPlayingState() == PLAYING_STATE_STOPPED) {
        cancelEngineRestart();
        return;
    }
    if (usesMpv() ? !d->m_mpvLoaded : (getPlayingState() != PLAYING_STATE_PAUSED && getPlayingState() != PLAYING_STATE_PLAYING)) return;
    if (getInput() != d->m_engineItem.get()) return;
    bool canSeek = isSeekable();
    if (!usesMpv()) {
        vlc_player_locker lock(d->m_player);
        canSeek = vlc_player_CanSeek(d->m_player);
        d->m_engineCapabilitiesKnown = true;
    }
    if (!d->m_engineCapabilitiesKnown) return;
    d->m_engineRestorePending = false;
    setRate(d->m_engineRate); setVolume(d->m_engineVolume); setMuted(d->m_engineMuted);
    setAudioDelayMS(d->m_engineAudioDelay); setSubtitleDelayMS(d->m_engineSubtitleDelay);
    if (canSeek) {
        d->m_engineSeekPending = true; d->m_engineMpvSeekStarted = false;
        setTime(d->m_engineTime);
        return;
    }
    if (d->m_engineTime.toVLCTick() > 0)
        vlc_dialog_display_error(VLC_OBJECT(d->p_intf), "Playback engine", "%s",
            qtu(tr("The selected engine cannot seek this input. Playback continues from its available starting point.")));
    finishEngineHandoff();
}

void PlayerController::finishEngineHandoff()
{
    Q_D(PlayerController);
    if (!d->m_engineSwitching || d->m_shutdownRequested || d->m_engineRestorePending) return;
    acknowledgeRestoreCallback();
    d->m_engineSeekPending = false; d->m_engineMpvSeekStarted = false;
    if (usesMpv()) d->m_mpvHistoryReady = true;
    if (usesMpv()) d->m_mpv->set(QStringLiteral("pause"), d->m_enginePaused);
    else {
        vlc_player_locker lock(d->m_player);
        if (d->m_enginePaused) vlc_player_Pause(d->m_player);
        else vlc_player_Resume(d->m_player);
    }
    d->m_engineSwitching = false;
    emit engineSwitchingChanged();
}

void PlayerController::saveMpvHistory(bool eof, std::function<void()> completion)
{
    Q_D(PlayerController);
    auto *library = d->p_intf->p_mi ? d->p_intf->p_mi->getMediaLibrary() : nullptr;
    if (!library || !d->m_mpvLoaded || !d->m_mpvHistoryReady || !d->m_currentItem) {
        if (completion) completion();
        return;
    }
    const auto uri = d->m_url.toEncoded();
    const double progress = eof ? 1. : d->m_position;
    const bool video = d->m_hasVideo;
    const bool recent = var_InheritBool(d->p_intf, "save-recentplay");
    const auto rate = QByteArray::number(d->m_rate, 'g', 9);
    library->runOnMLThread(this, [uri, progress, video, recent, rate, eof](vlc_medialibrary_t *ml) {
        auto *media = vlc_ml_get_media_by_mrl(ml, uri.constData());
        if (!media) media = vlc_ml_new_external_media(ml, uri.constData());
        if (!media) return;
        if (media->i_type == VLC_ML_MEDIA_TYPE_UNKNOWN)
            vlc_ml_media_set_type(ml, media->i_id, video ? VLC_ML_MEDIA_TYPE_VIDEO : VLC_ML_MEDIA_TYPE_AUDIO);
        if (recent) {
            vlc_ml_media_update_progress(ml, media->i_id, progress);
            if (eof) vlc_ml_media_set_played(ml, media->i_id, true);
        }
        // Shared rate/progress use the existing media-library contract. Engine-
        // specific track ids never overwrite VLC's incompatible native ids.
        vlc_ml_media_set_playback_state(ml, media->i_id, VLC_ML_PLAYBACK_STATE_SPEED, rate.constData());
        vlc_ml_media_release(media);
    }, [completion=std::move(completion)] { if (completion) completion(); }, "mpv-history");
}

void PlayerController::restoreMpvHistory()
{
    Q_D(PlayerController);
    auto *library = d->p_intf->p_mi ? d->p_intf->p_mi->getMediaLibrary() : nullptr;
    if (!library) return;
    struct State { double progress = 0.; float rate = 0.; };
    const auto revision = d->m_mpvMediaRevision;
    const auto uri = d->m_url.toEncoded();
    library->runOnMLThread<State>(this, [uri](vlc_medialibrary_t *ml, State &state) {
        auto *media = vlc_ml_get_media_by_mrl(ml, uri.constData());
        if (!media) return;
        state.progress = media->f_progress;
        vlc_ml_playback_states_all prefs{};
        if (vlc_ml_media_get_all_playback_pref(ml, media->i_id, &prefs) == VLC_SUCCESS) state.rate = prefs.rate;
        vlc_ml_playback_states_all_release(&prefs);
        vlc_ml_media_release(media);
    }, [this, d, revision](quint64, State &state) {
        if (revision != d->m_mpvMediaRevision || !d->m_mpvLoaded) return;
        d->m_mpvHistoryReady = true;
#ifdef VLC_PLAYER_DIAGNOSTICS
        emit mpvHistoryReadyChanged();
#endif
        if (var_InheritBool(d->p_intf, "restore-playback-states") && state.rate > 0.) setRate(state.rate);
        const auto mode = var_InheritInteger(d->p_intf, "restore-playback-pos");
        if (!std::isfinite(state.progress) || state.progress <= 0. || state.progress >= 1.) return;
        d->m_mpvResumePosition = state.progress;
        if (mode == VLC_PLAYER_RESTORE_PLAYBACK_POS_ALWAYS) restorePlaybackPos();
        else if (mode == VLC_PLAYER_RESTORE_PLAYBACK_POS_ASK) {
            d->m_canRestorePlayback = true;
            emit playbackRestoreQueried();
        }
    }, "mpv-history");
}

void PlayerController::mpvQueueFinished(bool exitAfterQueue)
{
    Q_D(PlayerController);
    if (!d->m_currentItem && d->m_playing_status != PLAYING_STATE_STOPPED) {
        d->m_playing_status = PLAYING_STATE_STOPPED;
        emit playingStateChanged(d->m_playing_status);
    }
    if ((exitAfterQueue || var_InheritBool(d->p_intf, "play-and-exit")) && d->p_intf->p_mi)
        emit d->p_intf->p_mi->askToQuit();
}
