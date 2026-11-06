// SPDX-License-Identifier: GPL-2.0-or-later
#pragma once
#include "player_controller.hpp"
#include "audio_visualization_data.hpp"
#include <QTimer>
#include <QVariantList>

struct PlayerVisualizationState;
struct filter_t;
int QtAudioVisualizerOpen(filter_t *);

class PlayerAudioVisualizer : public QObject {
    Q_OBJECT
    Q_PROPERTY(QString mode READ mode WRITE setMode NOTIFY changed FINAL)
    Q_PROPERTY(bool available READ available NOTIFY changed FINAL)
    Q_PROPERTY(bool active READ active NOTIFY changed FINAL)
    Q_PROPERTY(QString status READ status NOTIFY changed FINAL)
    Q_PROPERTY(QVariantList samples READ samples NOTIFY changed FINAL)
    Q_PROPERTY(quint64 frameRevision READ frameRevision NOTIFY changed FINAL)
public:
    explicit PlayerAudioVisualizer(PlayerController *,QObject *parent);
    ~PlayerAudioVisualizer() override;
    QString mode() const { return m_mode; }
    void setMode(const QString &);
    bool available() const { return m_available; }
    bool active() const { return !m_samples.isEmpty() && available() && !m_mode.isEmpty(); }
    QString status() const;
    QVariantList samples() const { return m_samples; }
    quint64 frameRevision() const { return m_frameRevision; }
signals:
    void changed();
private:
    void updateOutput();
    void resetOutput();
    void resetSamples();
    void detach();
    void refresh();
    PlayerController *m_player;
    SharedAOut m_output;
    std::shared_ptr<PlayerVisualizationState> m_state;
    AudioVisualization::Transform m_transform;
    QTimer m_renderClock;
    QString m_mode,m_error;
    QVariantList m_samples;
    quint64 m_seenRevision=0,m_frameRevision=0;
    bool m_available=false,m_loaded=false;
};
