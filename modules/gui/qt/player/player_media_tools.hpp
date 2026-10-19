// SPDX-License-Identifier: GPL-2.0-or-later
#ifndef VLC_QT_PLAYER_MEDIA_TOOLS_HPP
#define VLC_QT_PLAYER_MEDIA_TOOLS_HPP

#include "player_controller.hpp"
#include "subtitle_data.hpp"
#include <QJsonObject>
#include <QMap>
#include <QTimer>
#include <QVariantList>

class PlayerMediaTools : public QObject
{
    Q_OBJECT
    Q_PROPERTY(QString status READ status NOTIFY changed FINAL)
    Q_PROPERTY(QVariantList matches READ matches NOTIFY matchesChanged FINAL)
    Q_PROPERTY(QVariantList cues READ cues NOTIFY cuesChanged FINAL)
    Q_PROPERTY(QVariantList associations READ associations NOTIFY changed FINAL)
    Q_PROPERTY(QVariantMap videoInfo READ videoInfo NOTIFY changed FINAL)
    Q_PROPERTY(QString timelineStatus READ timelineStatus NOTIFY cuesChanged FINAL)
    Q_PROPERTY(bool subtitleLoaded READ subtitleLoaded NOTIFY cuesChanged FINAL)
    Q_PROPERTY(QStringList presets READ presets NOTIFY changed FINAL)
    Q_PROPERTY(QString activePreset READ activePreset NOTIFY changed FINAL)
    Q_PROPERTY(bool timelineVisible READ timelineVisible WRITE setTimelineVisible NOTIFY changed FINAL)
    Q_PROPERTY(bool waveformVisible READ waveformVisible WRITE setWaveformVisible NOTIFY changed FINAL)
    Q_PROPERTY(bool statisticsVisible READ statisticsVisible WRITE setStatisticsVisible NOTIFY changed FINAL)
    Q_PROPERTY(QString statisticsText READ statisticsText NOTIFY statisticsChanged FINAL)
    Q_PROPERTY(int sleepMinutes READ sleepMinutes NOTIFY changed FINAL)
    Q_PROPERTY(QString sleepStatus READ sleepStatus NOTIFY changed FINAL)
public:
    static QString languageCode(const QString &language);
    explicit PlayerMediaTools(qt_intf_t *intf, PlayerController *player);
    QString status() const { return m_status; }
    QVariantList matches() const { return m_matches; }
    QVariantList associations() const;
    QVariantMap videoInfo() const;
    QVariantList cues() const { return m_cues; }
    QString timelineStatus() const { return m_timelineStatus; }
    bool subtitleLoaded() const { return m_subtitleLoaded; }
    QStringList presets() const;
    QString activePreset() const { return m_activePreset; }
    bool timelineVisible() const { return m_timelineVisible; }
    bool waveformVisible() const { return m_waveformVisible; }
    bool statisticsVisible() const { return m_statisticsVisible; }
    QString statisticsText() const { return m_statisticsText; }
    void setStatisticsVisible(bool);
    int sleepMinutes() const { return m_sleepMinutes; }
    QString sleepStatus() const { return m_sleepStatus; }
    void setTimelineVisible(bool);
    void setWaveformVisible(bool);
    Q_INVOKABLE void prepareMatches(const QVariantList &media, const QVariantList &subtitles);
    Q_INVOKABLE void matchFolder(const QUrl &folder);
    Q_INVOKABLE void matchQueue(const QVariantList &subtitles);
    Q_INVOKABLE void chooseMatch(int row, const QUrl &subtitle);
    Q_INVOKABLE bool saveMatches();
    Q_INVOKABLE bool addSubtitle(const QUrl &subtitle);
    Q_INVOKABLE void browseSubtitle(int row = -1);
    Q_INVOKABLE void browseSubtitleFolder();
    Q_INVOKABLE void browseQueueSubtitles();
    Q_INVOKABLE QUrl browsePresetFolder();
    Q_INVOKABLE bool associateAndSave(const QUrl &subtitle);
    Q_INVOKABLE void forgetAssociation(const QUrl &media);
    Q_INVOKABLE QVariantList options(const QString &section) const;
    Q_INVOKABLE QVariant value(const QString &key) const;
    Q_INVOKABLE bool setValue(const QString &key, const QVariant &value);
    Q_INVOKABLE bool filterEnabled(const QString &module) const;
    Q_INVOKABLE void enableFilter(const QString &module, bool enabled);
    Q_INVOKABLE void resetSection(const QString &section);
    Q_INVOKABLE void savePreset(const QString &name, const QUrl &folder);
    Q_INVOKABLE void applyPreset(const QString &name);
    Q_INVOKABLE void removePreset(const QString &name);
    Q_INVOKABLE void setPreferredTrack(bool subtitle, const QString &language, int index);
    Q_INVOKABLE QVariantMap preferredTrack(bool subtitle) const;
    Q_INVOKABLE void armSleep(int minutes);
    Q_INVOKABLE void cancelSleep();
    Q_INVOKABLE QVariantMap metadata() const;
    Q_INVOKABLE QVariantList trackLanguages(bool subtitle) const;
    Q_INVOKABLE QString selectedLanguage(bool subtitle) const;
    bool isCurrentMedia(const QUrl &media) const;
    QJsonObject identity(const QUrl &url) const;
    Q_PROPERTY(double subtitleTimeScale READ subtitleTimeScale NOTIFY cuesChanged FINAL)
    double subtitleTimeScale() const;
    Q_PROPERTY(bool subtitleFPSSupported READ subtitleFPSSupported NOTIFY cuesChanged FINAL)
    bool subtitleFPSSupported() const;
signals:
    void changed();
    void matchesChanged();
    void cuesChanged();
    void analysisTogglesChanged();
    void statisticsChanged();
private:
    void inputChanged();
    void restoreTracks();
    void loadTimeline();
    void readState();
    bool writeState(const QJsonObject &state);
    QString mediaKey(const QUrl &url) const;
    bool validAssociation(const QUrl &media, const QJsonObject &association) const;
    void report(const QString &text);
    qt_intf_t *m_intf;
    PlayerController *m_player;
    QJsonObject m_state;
    QJsonObject m_sessionValues;
    QMap<QString, bool> m_sessionFilters;
    int m_globalSubtitleDelay = 0;
    QVariantList m_matches, m_cues;
    QString m_statePath, m_status, m_timelineStatus, m_activePreset, m_sleepStatus;
    QUrl m_subtitle;
    QByteArray m_expectedSubtitlePrefix;
    bool m_awaitingSubtitleTrack = false, m_subtitleLoaded = false;
    QTimer m_sleep;
    int m_sleepMinutes = 0;
    bool m_writable = true, m_timelineVisible = false, m_waveformVisible = false;
    bool m_restoringTracks = false, m_statisticsVisible = false;
    bool m_manualAudioChoice = false, m_manualSubtitleChoice = false, m_preferAssociation = false;
    QString m_statisticsText;
    void updateStatistics(const input_stats_t &stats);
    QString m_preferredAudio, m_preferredSubtitle;
    int m_preferredAudioIndex = -1, m_preferredSubtitleIndex = -1;
};
#endif
