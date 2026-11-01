/*****************************************************************************
 * help.cpp : Help and About dialogs
 ****************************************************************************
 * Copyright (C) 2007 the VideoLAN team
 *
 * Authors: Jean-Baptiste Kempf <jb (at) videolan.org>
 *          Rémi Duraffort <ivoire (at) via.ecp.fr>
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston MA 02110-1301, USA.
 *****************************************************************************/

#ifdef HAVE_CONFIG_H
# include "config.h"
#endif

#include "qt.hpp"
#include "help.hpp"
#include "util/qt_dirs.hpp"
#include "maininterface/mainctx.hpp"

#include <vlc_about.h>
#include <vlc_intf_strings.h>

#ifdef UPDATE_CHECK
# include "fork_release.hpp"
# include <QNetworkAccessManager>
# include <QNetworkReply>
# include <QNetworkRequest>
# include <QPointer>
# include <QDesktopServices>
# include <memory>
#endif

#include <QTextBrowser>
#include <QString>
#include <QDialogButtonBox>
#include <QEvent>
#include <QDate>
#include <QPushButton>

#include <cassert>

#ifndef NDEBUG
// Uncomment the following line to make use a mock update for debugging purposes,
// it is only applicable when there is no new release found:
// #define UPDATE_MOCK
#endif

HelpDialog::HelpDialog( qt_intf_t *_p_intf ) : QVLCFrame( _p_intf )

{
    setWindowTitle( qtr( "Help" ) );
    setWindowRole( "vlc-help" );
    setMinimumSize( 350, 300 );

    QVBoxLayout *layout = new QVBoxLayout( this );

    QTextBrowser *helpBrowser = new QTextBrowser( this );
    helpBrowser->setOpenExternalLinks( true );
    helpBrowser->setHtml( qfut(I_LONGHELP) );

    QDialogButtonBox *closeButtonBox = new QDialogButtonBox( this );
    closeButtonBox->addButton(
        new QPushButton( qtr("&Close") ), QDialogButtonBox::RejectRole );
    closeButtonBox->setFocus();

    layout->addWidget( helpBrowser );
    layout->addWidget( closeButtonBox );

    connect( closeButtonBox, &QDialogButtonBox::rejected, this, &HelpDialog::close );
    restoreWidgetPosition( "Help", QSize( 500, 450 ) );
}

HelpDialog::~HelpDialog()
{
    saveWidgetPosition( "Help" );
}

AboutDialog::AboutDialog( qt_intf_t *_p_intf)
            : QVLCDialog( nullptr, _p_intf ), b_advanced( false )
{
    /* Build UI */
    ui.setupUi( this );
    setWindowTitle( qtr( "About" ) );
    setWindowRole( "vlc-about" );
    setWindowModality( Qt::WindowModal );

    ui.version->setText(qfu( " " VERSION_MESSAGE ) );
    ui.title->setText("<html><head/><body><p><span style=\" font-size:26pt; color:#353535;\"> " + qtr( "VLC media player" ) + " </span></p></body></html>");

    ui.MainBlabla->setText("<html><head/><body>" +
    qtr( "<p>VLC media player is a free and open source media player, encoder, and streamer made by the volunteers of the <a href=\"https://www.videolan.org/\"><span style=\" text-decoration: underline; color:#0057ae;\">VideoLAN</span></a> community.</p><p>VLC uses its internal codecs, works on essentially every popular platform, and can read almost all files, CDs, DVDs, network streams, capture cards and other media formats!</p><p><a href=\"https://www.videolan.org/contribute/\"><span style=\" text-decoration: underline; color:#0057ae;\">Help and join us!</span></a>" ) +
    "</p></body> </html>");

    const QDate today = QDate::currentDate();
    if( today.month() == 4 && today.day() == 1
            && var_InheritBool( p_intf, "qt-icon-change" ) )
        ui.VLCcone->setPixmap( QPixmap( ":/logo/vlc128-aprilfools.png" ) );

    ui.update->hide();

    /* GPL License */
    ui.licensePage->setText( qfu( psz_license ) );

    /* People who helped */
    ui.creditPage->setText( qfu( psz_thanks ) );

    /* People who wrote the software */
    ui.authorsPage->setText( qfu( psz_authors ) );

    ui.licenseButton->setText( "<html><head/><body><p><span style=\" text-decoration: underline; color:#0057ae;\">"+qtr( "License" )+"</span></p></body></html>");
    ui.licenseButton->installEventFilter( this );

    ui.authorsButton->setText( "<html><head/><body><p><span style=\" text-decoration: underline; color:#0057ae;\">"+qtr( "Authors" )+"</span></p></body></html>");
    ui.authorsButton->installEventFilter( this );

    ui.creditsButton->setText( "<html><head/><body><p><span style=\" text-decoration: underline; color:#0057ae;\">"+qtr( "Credits" )+"</span></p></body></html>");
    ui.creditsButton->installEventFilter( this );

    ui.version->installEventFilter( this );
}

void AboutDialog::showLicense()
{
    ui.stackedWidget->setCurrentWidget( ui.licensePage );
}

void AboutDialog::showAuthors()
{
    ui.stackedWidget->setCurrentWidget( ui.authorsPage );
}

void AboutDialog::showCredit()
{
    ui.stackedWidget->setCurrentWidget( ui.creditPage );
}

bool AboutDialog::eventFilter(QObject *obj, QEvent *event)
{
    if (event->type() == QEvent::MouseButtonPress )
    {
        if( obj == ui.version )
        {
            if( !b_advanced )
            {
                ui.version->setText(qfu( VLC_CompileBy() )+ "@" + qfu( VLC_CompileHost() )
                    + " " + __DATE__ + " " + __TIME__);
                b_advanced = true;
            }
            else
            {
                ui.version->setText(qfu( " " VERSION_MESSAGE ) );
                b_advanced = false;
            }
            return true;
        }
        else if( obj == ui.licenseButton )
            showLicense();
        else if( obj == ui.authorsButton )
            showAuthors();
        else if( obj == ui.creditsButton )
            showCredit();

        return false;
    }

    return QVLCDialog::eventFilter( obj, event);
}

void AboutDialog::showEvent( QShowEvent *event )
{
    ui.stackedWidget->setCurrentWidget( ui.blablaPage );
    QVLCDialog::showEvent( event );
}

#ifdef UPDATE_CHECK

class UpdateModelPrivate
{
public:
    Q_DECLARE_PUBLIC(UpdateModel)
    explicit UpdateModelPrivate(UpdateModel *pub) : network(pub), q_ptr(pub) {}
    QNetworkAccessManager network;
    QPointer<QNetworkReply> reply;
    ForkRelease::Release release;
    UpdateModel::Status m_status = UpdateModel::Unchecked;
    bool m_explicitCheck = false;
    UpdateModel *q_ptr = nullptr;
};

UpdateModel::UpdateModel(qt_intf_t *p_intf)
    : d_ptr(new UpdateModelPrivate(this))
{
    Q_UNUSED(p_intf)
}

UpdateModel::~UpdateModel()
{
    Q_D(UpdateModel);
    if (d->reply) {
        d->reply->disconnect(this);
        d->reply->abort();
    }
}

void UpdateModel::checkUpdate(bool explicitCheck)
{
    Q_D(UpdateModel);
    // A manual check can adopt the original in-flight request.
    if (explicitCheck && !d->m_explicitCheck) {
        d->m_explicitCheck = true;
        emit explicitCheckChanged();
    }
    if (d->reply) {
        d->m_status = Checking;
        emit updateStatusChanged();
        return;
    }
    if (d->m_explicitCheck != explicitCheck) {
        d->m_explicitCheck = explicitCheck;
        emit explicitCheckChanged();
    }
    d->release = {};
    d->m_status = Checking;
    emit updateStatusChanged();
    QUrl url(QString::fromLatin1(ForkRelease::endpoint));
#ifdef VLC_PLAYER_DIAGNOSTICS
    // Controlled network cases use an actual test-only loopback HTTP peer.
    // Normal binaries have no endpoint override.
    const QUrl peer(QString::fromUtf8(qgetenv("VLC_PLAYER_DIAGNOSTICS_UPDATE_URL")));
    if (!qgetenv("VLC_PLAYER_DIAGNOSTICS_DIR").isEmpty() && peer.scheme() == QStringLiteral("http")
        && peer.host() == QStringLiteral("127.0.0.1") && peer.port() > 0
        && peer.path() == QStringLiteral("/releases/latest")) url = peer;
#endif
    QNetworkRequest request(url);
    request.setAttribute(QNetworkRequest::RedirectPolicyAttribute, QNetworkRequest::ManualRedirectPolicy);
    request.setRawHeader("Accept", "application/vnd.github+json");
    request.setRawHeader("X-GitHub-Api-Version", "2022-11-28");
    request.setRawHeader("User-Agent", QByteArray("Modern-VLC-Fork/") + ForkRelease::currentVersion);
    auto *reply = d->network.get(request);
    d->reply = reply;
    reply->setReadBufferSize(1024 * 1024 + 1);
    auto bytes = std::make_shared<QByteArray>();
    connect(reply, &QNetworkReply::readyRead, this, [reply, bytes] {
        bytes->append(reply->readAll());
        if (bytes->size() > 1024 * 1024) reply->abort();
    });
    connect(reply, &QNetworkReply::finished, this, [this, reply, bytes] {
        Q_D(UpdateModel);
        bytes->append(reply->readAll());
        d->reply = nullptr;
        if (reply->error() == QNetworkReply::NoError
            && reply->attribute(QNetworkRequest::HttpStatusCodeAttribute).toInt() == 200)
            d->release = ForkRelease::parse(*bytes);
        d->m_status = !d->release.valid ? CheckFailed
            : d->release.version > QVersionNumber::fromString(QString::fromLatin1(ForkRelease::currentVersion))
                ? NeedUpdate : UpToDate;
        reply->deleteLater();
        emit updateStatusChanged();
    });
}

bool UpdateModel::download(QString destDir)
{
    Q_UNUSED(destDir)
    Q_D(UpdateModel);
    // The portable fork is updated through its verified release page. Never
    // download/install a VideoLAN binary over this fork or alter a live profile.
    return d->m_status == NeedUpdate && d->release.valid
        && QDesktopServices::openUrl(d->release.page);
}

bool UpdateModel::download()
{
    return download(QString());
}

void UpdateModel::resetStatus()
{
    Q_D(UpdateModel);
    if (d->m_status == Unchecked)
        return;
    d->m_status = Unchecked;
    emit updateStatusChanged();
}

UpdateModel::Status UpdateModel::updateStatus() const
{
    Q_D(const UpdateModel);
    return d->m_status;
}

int UpdateModel::getMajor() const
{
    Q_D(const UpdateModel);
    return d->release.version.majorVersion();
}
int UpdateModel::getMinor() const
{
    Q_D(const UpdateModel);
    return d->release.version.minorVersion();
}
int UpdateModel::getRevision() const
{
    Q_D(const UpdateModel);
    return d->release.version.microVersion();
}
int UpdateModel::getExtra() const
{
    return 0;
}
QString UpdateModel::getDescription() const
{
    Q_D(const UpdateModel);
    return d->release.description;
}
QString UpdateModel::getUrl() const
{
    Q_D(const UpdateModel);
    return d->release.page.toString();
}

double UpdateModel::getProgress() const
{
    // TODO: Stub
    return 0.0;
}

bool UpdateModel::explicitCheck() const
{
    Q_D(const UpdateModel);
    return d->m_explicitCheck;
}

void UpdateModel::resetExplicitCheck()
{
    Q_D(UpdateModel);
    if (!d->m_explicitCheck)
        return;
    d->m_explicitCheck = false;
    emit explicitCheckChanged();
}

/*****************************************************************************
 * UpdateDialog
 *****************************************************************************/

UpdateDialog::UpdateDialog( qt_intf_t *_p_intf ) : QVLCFrame( _p_intf )
{
    /* build Ui */
    ui.setupUi( this );
    ui.updateDialogButtonBox->addButton( new QPushButton( qtr("&Close"), this ),
                                         QDialogButtonBox::RejectRole );
    QPushButton *recheckButton = new QPushButton( qtr("&Recheck version"), this );
    ui.updateDialogButtonBox->addButton( recheckButton, QDialogButtonBox::ActionRole );

    ui.updateNotifyButtonBox->addButton( new QPushButton( qtr("&Open release page"), this ),
                                         QDialogButtonBox::AcceptRole );
    ui.updateNotifyButtonBox->addButton( new QPushButton( qtr("&No"), this ),
                                         QDialogButtonBox::RejectRole );

    setWindowTitle( qtr( "Modern VLC Fork updates" ) );
    setWindowRole( "vlc-update" );

    BUTTONACT( recheckButton, &UpdateDialog::checkOrDownload );
    connect( ui.updateDialogButtonBox, &QDialogButtonBox::rejected, this, &UpdateDialog::close );

    connect( ui.updateNotifyButtonBox, &QDialogButtonBox::accepted, this, &UpdateDialog::checkOrDownload );
    connect( ui.updateNotifyButtonBox, &QDialogButtonBox::rejected, this, &UpdateDialog::close );

    setMinimumSize( 300, 300 );
    setMaximumSize( 500, 300 );

    restoreWidgetPosition( "Update", maximumSize() );

    m_model = p_intf->p_mi->getUpdateModel();
    connect(m_model, &UpdateModel::updateStatusChanged, this, &UpdateDialog::updateUI);
    /* update status*/
    updateUI();
}

UpdateDialog::~UpdateDialog()
{
    saveWidgetPosition( "Update" );
}

bool UpdateDialog::event(QEvent* event)
{
    assert(event);

    if (Q_LIKELY(m_model))
    {
        switch(event->type())
        {
        case QEvent::Hide:
        case QEvent::Show:
        case QEvent::Close:
        case QEvent::Destroy:
            m_model->resetExplicitCheck();
            break;
        default:
            break;
        }
    }

    return QVLCFrame::event(event);
}

/* Check for updates */
void UpdateDialog::checkOrDownload()
{
    switch (m_model->updateStatus()) {
    case UpdateModel::Unchecked:
    case UpdateModel::UpToDate:
    case UpdateModel::CheckFailed:
    {
        ui.stackedWidget->setCurrentWidget( ui.updateRequestPage );
        m_model->checkUpdate(true);
        break;
    }
    case UpdateModel::NeedUpdate:
    {
        if (m_model->download())
            toggleVisible();
        break;
    }
    default: // Checking
        break;
    }
}

/* Notify the end of the update_Check */
void UpdateDialog::updateUI( )
{
    switch (m_model->updateStatus()) {
    case UpdateModel::NeedUpdate:
    {
        ui.stackedWidget->setCurrentWidget( ui.updateNotifyPage );
        int extra = m_model->getExtra();
        QString message = QString(
                              qtr( "A new version of Modern VLC Fork (%1.%2.%3%4) is available." ) )
                              .arg( m_model->getMajor() )
                              .arg( m_model->getMinor() )
                              .arg( m_model->getRevision()  )
                              .arg( extra == 0 ? QStringLiteral("") : QStringLiteral(".") + QString::number( extra ) );

        ui.updateNotifyLabel->setText( message );
        message = m_model->getDescription().toHtmlEscaped().replace( "\n", "<br/>" );

        /* Try to highlight releases featuring security changes */
        int i_index = message.indexOf( "security", Qt::CaseInsensitive );
        if ( i_index >= 0 )
        {
            message.insert( i_index + 8, "</font>" );
            message.insert( i_index, "<font style=\"color:red\">" );
        }
        ui.updateNotifyTextEdit->setHtml( message );
        break;
    }
    case UpdateModel::UpToDate:
    {
        ui.stackedWidget->setCurrentWidget( ui.updateDialogPage );
        ui.updateDialogLabel->setText(
            qtr( "You have the latest available Modern VLC Fork release." ) );
        break;
    }
    case UpdateModel::CheckFailed:
    {
        ui.stackedWidget->setCurrentWidget( ui.updateDialogPage );
        ui.updateDialogLabel->setText(
            qtr( "Could not check the Modern VLC Fork releases. Check your connection and choose Recheck version." ) );
        break;
    }
    case UpdateModel::Checking:
    {
        ui.stackedWidget->setCurrentWidget( ui.updateDialogPage );
        ui.updateDialogLabel->setText(
            qtr( "Checking for updates..." ) );
        break;
    }
    case UpdateModel::Unchecked:
        // do nothing
        break;
    case UpdateModel::Downloading:
        // NOTE: It is not planned to implement this in the legacy dialog.
        //       The new update pane already respects it, we are only
        //       waiting for the core to provide this information.
        break;
    }

    if (isVisible())
    {
        if (const auto w = windowHandle())
        {
            w->alert(0);
        }
    }
}

#endif
