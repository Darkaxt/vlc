// SPDX-License-Identifier: GPL-2.0-or-later
#ifndef VLC_QT_PLAYER_MEDIA_ANALYSIS_HPP
#define VLC_QT_PLAYER_MEDIA_ANALYSIS_HPP
#include "player_controller.hpp"
#include <QImage>
#include <QMutex>
#include <QQuickImageProvider>
#include <QQuickPaintedItem>
#include <QVariantList>
#include <vlc_preparser.h>
#include <memory>

class PlayerMediaTools;
class WaveformWorker;

// The pinned QtQuick SDK disables Canvas. Paint these two bounded analysis
// strips with Qt's supported native item instead of requiring another module.
class PlayerAnalysisStrip : public QQuickPaintedItem
{
    Q_OBJECT
    Q_PROPERTY(QVariantList samples READ samples WRITE setSamples NOTIFY changed FINAL)
    Q_PROPERTY(QVariantList cues READ cues WRITE setCues NOTIFY changed FINAL)
    Q_PROPERTY(double durationMS READ durationMS WRITE setDurationMS NOTIFY changed FINAL)
    Q_PROPERTY(double timeScale READ timeScale WRITE setTimeScale NOTIFY changed FINAL)
    Q_PROPERTY(double delayMS READ delayMS WRITE setDelayMS NOTIFY changed FINAL)
    Q_PROPERTY(QColor color READ color WRITE setColor NOTIFY changed FINAL)
public:
    explicit PlayerAnalysisStrip(QQuickItem *parent = nullptr) : QQuickPaintedItem(parent) {}
    QVariantList samples() const { return m_samples; }
    QVariantList cues() const { return m_cues; }
    double durationMS() const { return m_duration; }
    double timeScale() const { return m_scale; }
    double delayMS() const { return m_delay; }
    QColor color() const { return m_color; }
    void setSamples(const QVariantList &v) { if (m_samples == v) return; m_samples = v; update(); emit changed(); }
    void setCues(const QVariantList &v) { if (m_cues == v) return; m_cues = v; update(); emit changed(); }
    void setDurationMS(double v) { if (m_duration == v) return; m_duration = v; update(); emit changed(); }
    void setTimeScale(double v) { if (m_scale == v) return; m_scale = v; update(); emit changed(); }
    void setDelayMS(double v) { if (m_delay == v) return; m_delay = v; update(); emit changed(); }
    void setColor(const QColor &v) { if (m_color == v) return; m_color = v; update(); emit changed(); }
    void paint(QPainter *) override;
signals:
    void changed();
private:
    QVariantList m_samples, m_cues;
    double m_duration = 0, m_scale = 1, m_delay = 0;
    QColor m_color;
};

struct PlayerPreviewImage { QMutex mutex; QImage image; };
class PlayerPreviewProvider : public QQuickImageProvider
{
public:
    explicit PlayerPreviewProvider(std::shared_ptr<PlayerPreviewImage> image)
        : QQuickImageProvider(QQuickImageProvider::Image), m_image(std::move(image)) {}
    QImage requestImage(const QString &, QSize *size, const QSize &) override
    {
        QMutexLocker lock(&m_image->mutex); if (size) *size = m_image->image.size(); return m_image->image;
    }
private:
    std::shared_ptr<PlayerPreviewImage> m_image;
};
class PlayerMediaAnalysis : public QObject
{
    Q_OBJECT
    Q_PROPERTY(QString previewSource READ previewSource NOTIFY previewChanged FINAL)
    Q_PROPERTY(QString previewStatus READ previewStatus NOTIFY previewChanged FINAL)
    Q_PROPERTY(double previewPosition READ previewPosition NOTIFY previewChanged FINAL)
    Q_PROPERTY(QVariantList waveform READ waveform NOTIFY waveformChanged FINAL)
    Q_PROPERTY(QString waveformStatus READ waveformStatus NOTIFY waveformChanged FINAL)
    Q_PROPERTY(bool waveformBusy READ waveformBusy NOTIFY waveformChanged FINAL)
    Q_PROPERTY(bool previewSupported READ previewSupported NOTIFY previewChanged FINAL)
    Q_PROPERTY(double durationMS READ durationMS NOTIFY previewChanged FINAL)
public:
    PlayerMediaAnalysis(qt_intf_t *, PlayerController *, PlayerMediaTools *);
    ~PlayerMediaAnalysis() override;
    std::shared_ptr<PlayerPreviewImage> previewImage() const { return m_image; }
    QString previewSource() const { return m_previewSource; }
    QString previewStatus() const;
    bool previewSupported() const { return !m_player->usesMpv() && m_player->isSeekable() && m_player->getLength().valid() && m_player->getVideoTracks()->getCount() > 0; }
    double durationMS() const { return double(m_player->getLength().toVLCTick()) / 1000.; }
    double previewPosition() const { return m_publishedPosition; }
    QVariantList waveform() const { return m_waveform; }
    QString waveformStatus() const { return m_waveformStatus; }
    bool waveformBusy() const { return m_worker != nullptr; }
    Q_INVOKABLE void requestPreview(double position);
    Q_INVOKABLE void hidePreview();
signals:
    void previewChanged();
    void waveformChanged();
private:
    void inputChanged();
    void updateWaveform(bool invalidate = false);
    void startPreview();
    qt_intf_t *m_intf;
    PlayerController *m_player;
    PlayerMediaTools *m_tools;
    vlc_preparser_t *m_preparser = nullptr;
    vlc_preparser_req *m_request = nullptr;
    std::shared_ptr<PlayerPreviewImage> m_image = std::make_shared<PlayerPreviewImage>();
    WaveformWorker *m_worker = nullptr;
    QVariantList m_waveform;
    QString m_previewSource, m_previewStatus, m_waveformStatus;
    quint64 m_generation = 0, m_waveGeneration = 0, m_imageRevision = 0;
    double m_wantedPosition = 0, m_publishedPosition = 0;
    bool m_wantPreview = false, m_wantWaveform = false, m_requestCancelled = false;
    QUrl m_waveInput;
    int m_waveAudioTrack = -1;
};
#endif
