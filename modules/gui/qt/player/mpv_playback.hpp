/* Copyright (C) 2026 VLC authors and VideoLAN
 * SPDX-License-Identifier: GPL-2.0-or-later
 */
#ifndef VLC_QT_MPV_PLAYBACK_HPP
#define VLC_QT_MPV_PLAYBACK_HPP

#include "qt.hpp"
#include <QObject>
#include <QVariant>
#include <QUrl>
#include <QStringList>
#include <functional>
#include <memory>

// One optional native player; the existing VLC playlist remains the queue owner.
// Normal commands/events belong to the UI thread. The native render surface owns
// its own thread, window and D3D device and is released before the player core.
class MpvPlayback final : public QObject
{
    Q_OBJECT
public:
    explicit MpvPlayback(qt_intf_t *, QObject *parent = nullptr);
    ~MpvPlayback() override;
    bool isAvailable() const;
    bool isMediaLoaded() const;
    QString error() const;
    void load(const QUrl &, bool paused);
    void command(const QStringList &);
    void set(const QString &, const QVariant &);
    QVariant value(const QString &) const;
    void requestAudioSessionState();
    void prepareToClose(std::function<void()> completion);

signals:
    void changed(const QString &name, const QVariant &value);
    void fileLoaded();
    void seekStarted();
    void playbackRestarted();
    void ended(bool eof, const QString &error);
    void failed(const QString &message);
    void surfaceReady();

private:
    struct Private;
    std::unique_ptr<Private> d;
};
#endif
