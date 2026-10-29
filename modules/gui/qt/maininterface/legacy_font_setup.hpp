// SPDX-License-Identifier: GPL-2.0-or-later
#ifndef VLC_QT_LEGACY_FONT_SETUP_HPP
#define VLC_QT_LEGACY_FONT_SETUP_HPP
#include <QObject>
#include <QNetworkAccessManager>
#include <QNetworkReply>
#include <QPointer>

class LegacyFontSetup final : public QObject
{
    Q_OBJECT
    Q_PROPERTY(bool busy READ busy NOTIFY changed FINAL)
    Q_PROPERTY(bool available READ available NOTIFY changed FINAL)
    Q_PROPERTY(QString status READ status NOTIFY changed FINAL)
    Q_PROPERTY(qint64 received READ received NOTIFY changed FINAL)
    Q_PROPERTY(qint64 total READ total NOTIFY changed FINAL)
    Q_PROPERTY(QString location READ location CONSTANT FINAL)
public:
    explicit LegacyFontSetup(QObject *parent);
    ~LegacyFontSetup() override;
    bool busy() const { return m_busy; }
    bool available() const { return m_available; }
    QString status() const { return m_status; }
    qint64 received() const { return m_received; }
    qint64 total() const { return m_total; }
    QString location() const;
    Q_INVOKABLE void refresh();
    Q_INVOKABLE void download();
    Q_INVOKABLE void cancel();
signals:
    void changed();
private:
    QNetworkAccessManager m_network;
    QPointer<QNetworkReply> m_reply;
    QByteArray m_bytes;
    QString m_status;
    quint64 m_generation = 0;
    qint64 m_received = 0, m_total = -1;
    bool m_busy = false, m_available = false;
    void fail(const QString &message);
    bool install(const QByteArray &archive);
};
#endif
