// SPDX-License-Identifier: GPL-2.0-or-later
#ifndef VLC_QT_SUBTITLE_SEARCH_HPP
#define VLC_QT_SUBTITLE_SEARCH_HPP
#include <QObject>
#include <QNetworkAccessManager>
#include <QNetworkReply>
#include <QPointer>
#include <QStringList>
#include <QJsonObject>
#include <QVariantList>
#include <QUrl>
#include <array>
#include <functional>
#include <memory>

class PlayerController;
class PlayerMediaTools;
class SubtitleSearch : public QObject
{
    Q_OBJECT
    Q_PROPERTY(int provider READ provider WRITE setProvider NOTIFY changed FINAL)
    Q_PROPERTY(bool busy READ busy NOTIFY changed FINAL)
    Q_PROPERTY(bool configured READ configured NOTIFY changed FINAL)
    Q_PROPERTY(QString status READ status NOTIFY changed FINAL)
    Q_PROPERTY(QVariantList results READ results NOTIFY changed FINAL)
    Q_PROPERTY(QStringList archiveFiles READ archiveFiles NOTIFY changed FINAL)
public:
    SubtitleSearch(PlayerController *, PlayerMediaTools *);
    ~SubtitleSearch() override;
    int provider() const { return m_provider; }
    bool busy() const { return m_busy; }
    bool configured() const { return !m_keys[m_provider].isEmpty(); }
    QString status() const { return m_status; }
    QVariantList results() const { return m_results; }
    QStringList archiveFiles() const;
    void setProvider(int);
    Q_INVOKABLE void setCredentials(const QString &key);
    Q_INVOKABLE void login(const QString &username, const QString &password);
    Q_INVOKABLE void search(const QString &query, const QString &language);
    Q_INVOKABLE void select(int row);
    Q_INVOKABLE void associateArchiveFile(int index);
    Q_INVOKABLE void cancel();
signals:
    void changed();
private:
    using Completion = std::function<void(const QByteArray &, const QByteArray &)>;
    struct Result { QString title, language, release, id, kind; QUrl url; };
    struct ArchiveFile { QString name; QByteArray bytes; };
    void request(const QByteArray &method, const QUrl &, const QJsonObject &, bool authenticated, Completion, int redirects = 0);
    void fail(const QString &);
    void publish();
    bool allowedDownload(const QUrl &) const;
    QUrl api(const QString &) const;
    void decodeDownload(const QByteArray &, const QByteArray &, const QString &name);
    void storeAndAssociate(const QString &, const QByteArray &);
    void subtitleResults(const QByteArray &);
    bool parseResponse(const QByteArray &, QJsonObject &);
    PlayerController *m_player;
    PlayerMediaTools *m_tools;
    QNetworkAccessManager m_network;
    QPointer<QNetworkReply> m_reply;
    std::array<QByteArray, 3> m_keys;
    QByteArray m_token;
    QString m_openSubtitlesHost = QStringLiteral("api.opensubtitles.com");
    QString m_language, m_status, m_title;
    int m_provider = 0;
    quint64 m_generation = 0;
    bool m_busy = false, m_waitingTrack = false;
    QUrl m_input;
    QJsonObject m_inputIdentity;
    Result m_selected;
    QVector<Result> m_items;
    QVariantList m_results;
    QVector<ArchiveFile> m_archive;
};
#endif
