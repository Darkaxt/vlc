/*****************************************************************************
 * Copyright (C) 2020 VLC authors and VideoLAN
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
#include "video_window_handler.hpp"
#include "mainctx.hpp"
#include "window_geometry.hpp"

#include <QApplication>
#include <QScreen>

#include <vlc_window.h>
#include "compositor.hpp"

VideoWindowHandler::VideoWindowHandler(qt_intf_t* intf, QObject *parent)
    : QObject(parent)
    , m_intf(intf)
{
    /* Does the interface resize to video size or the opposite */
    m_autoresize = var_InheritBool( m_intf, "qt-video-autoresize" );

    assert(qGuiApp);
    m_hasWayland = qGuiApp->platformName().startsWith(QLatin1String("wayland"));

    connect( this, &VideoWindowHandler::askVideoToResize,
             this, &VideoWindowHandler::setVideoSize, Qt::QueuedConnection );
    connect( this, &VideoWindowHandler::askVideoSetFullScreen,
             this, &VideoWindowHandler::setVideoFullScreen, Qt::QueuedConnection );
    connect( this, &VideoWindowHandler::askVideoOnTop,
             this, &VideoWindowHandler::setVideoOnTop, Qt::QueuedConnection );
}

void VideoWindowHandler::setWindow(QWindow* window)
{
    if (m_window == window)
        return;
    if (m_window)
    {
        WindowStateHolder::holdOnTop(m_window, WindowStateHolder::VIDEO, false);
        WindowStateHolder::holdFullscreen(m_window, WindowStateHolder::VIDEO, false);
    }

    m_window = window;
}

void VideoWindowHandler::disable()
{
    emit askVideoSetFullScreen( false );
    emit askVideoOnTop( false );
}

void VideoWindowHandler::requestResizeVideo( unsigned i_width, unsigned i_height )
{
    if (!m_window)
        return;
    emit askVideoToResize( i_width, i_height, m_window->windowStates() );
}

void VideoWindowHandler::requestVideoWindowed( )
{
   emit askVideoSetFullScreen( false );
}

void VideoWindowHandler::requestVideoFullScreen(const char * )
{
    emit askVideoSetFullScreen( true );
}

void VideoWindowHandler::requestVideoState(  unsigned i_arg )
{
    bool on_top = (i_arg & VLC_WINDOW_STATE_ABOVE) != 0;
    emit askVideoOnTop( on_top );
}

void VideoWindowHandler::setVideoSize(unsigned int w, unsigned int h, Qt::WindowStates currentStates)
{
    if (!m_window || w == 0 || h == 0)
        return;
    Qt::WindowStates states = m_window->windowStates();

    // This slot is queued, so by the time it is called
    // the window states reflect the final states.
    // `qt-video-autoresize` should not apply during state
    // transition, that was also the behavior in VLC 3.
    // Otherwise, when getting disengaged from fullscreen
    // the interface/video would forget its old (overridden)
    // size.

    // Do not resize when transitioning between states:
    if (currentStates != states)
        return;

    m_requestedVideoSize = QSize(w, h);
    if (!m_interfaceModeConnection && m_intf->p_mi) {
        m_interfaceModeConnection = connect(m_intf->p_mi, &MainCtx::mainInterfaceModesChanged,
            this, [this] {
                if (m_window && m_intf->p_mi->isPlayerView() && m_requestedVideoSize.isValid())
                    emit askVideoToResize(m_requestedVideoSize.width(), m_requestedVideoSize.height(), m_window->windowStates());
            });
    }
    if (!m_autoresize || (states & (Qt::WindowFullScreen | Qt::WindowMaximized))
        || !m_window->screen()) return;
    // A library miniature is not the main video's size owner. Its pending
    // native request is handled when the actual main player mode is entered.
    if (m_intf->p_mi && !m_intf->p_mi->isPlayerView()) return;
    const qreal factor = m_window->devicePixelRatio();
    QSize chrome;
    if (m_intf->p_compositor) {
        const auto quick = m_intf->p_compositor->quickWindow();
        const auto content = quick ? quick->contentItem() : nullptr;
        if (content) {
            if (const auto loader = content->findChild<QQuickItem*>(QStringLiteral("playerSpecializationLoader")))
                chrome = (m_window->size() - loader->size().toSize()).expandedTo(QSize(0, 0));
        }
    }
    const auto geometry = fitVideoWindow(QSizeF(w / factor, h / factor), chrome,
        m_window->screen()->availableGeometry(), m_window->frameMargins(),
        m_window->minimumSize(), m_window->maximumSize(), m_window->position());
    m_window->setGeometry(geometry);
}

void VideoWindowHandler::setVideoFullScreen( bool fs )
{
    if (!m_window)
        return;
    m_videoFullScreen = fs;
    if( fs )
    {
        int numscreen = var_InheritInteger( m_intf, "qt-fullscreen-screennumber" );

        auto screenList = QApplication::screens();
        if ( numscreen >= 0 && numscreen < screenList.count() )
        {
            QRect screenres = screenList[numscreen]->geometry();
            m_lastWinScreen = m_window->screen();
            if( !m_hasWayland )
                m_window->setScreen(screenList[numscreen]);

            /* To be sure window is on proper-screen in xinerama */
            if( !screenres.contains( m_window->position() ) )
            {
                m_window->setPosition(screenres.x(), screenres.y() );
            }
        }
        WindowStateHolder::holdFullscreen(m_window,  WindowStateHolder::VIDEO, true);
    }
    else
    {
        WindowStateHolder::holdFullscreen(m_window,  WindowStateHolder::VIDEO, false);

        if( m_lastWinScreen != NULL && !m_hasWayland )
            m_window->setScreen(m_lastWinScreen);
    }
}


/* Slot to change the video always-on-top flag.
 * Emit askVideoOnTop() to invoke this from other thread. */
void VideoWindowHandler::setVideoOnTop( bool on_top )
{
    if (!m_window)
        return;
    WindowStateHolder::holdOnTop(m_window, WindowStateHolder::VIDEO, on_top);
}
