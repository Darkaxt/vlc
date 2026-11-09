/*****************************************************************************
 * Copyright (C) 2021 VLC authors and VideoLAN
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
#ifndef COMPOSITOR_X11_RENDERWINDOW_HPP
#define COMPOSITOR_X11_RENDERWINDOW_HPP

#ifdef HAVE_CONFIG_H
# include "config.h"
#endif

#include <memory>

#include <QObject>
#include <QMutex>
#include <QWindow>
#ifdef VLC_PLAYER_DIAGNOSTICS
#include <QVariantMap>
#endif

#include <xcb/xcb.h>
#include <xcb/render.h>
#include <xcb/damage.h>

#include <vlc_common.h>
#include <vlc_interface.h>

#include "qt.hpp"

#include "compositor_x11_utils.hpp"
#include "compositor_common.hpp"
#include "compositor_accessibility.hpp"

class QWidget;
class QSocketNotifier;
class QAccessibleInterface;

namespace vlc {

class CompositorX11RenderClient;
class CompositorX11UISurface;

/**
 * @brief The RenderTask class does the actual rendering into the window
 * it grab the offscreen surface from the interface and the video and blends
 * them into the output surface. It will refresh the composition when either the
 * interface refresh or the video surface is updated
 */
class RenderTask : public QObject
{
    Q_OBJECT
public:
    explicit RenderTask(qt_intf_t* intf,
                        xcb_connection_t* conn,
                        xcb_drawable_t wid,
                        QMutex& pictureLock,
                        QObject* parent = nullptr);
    ~RenderTask();
#ifdef VLC_PLAYER_DIAGNOSTICS
    QVariantMap diagnosticState() const {
        return {{QStringLiteral("visible"), m_visible},
                {QStringLiteral("request_id"), m_refreshRequestId},
                {QStringLiteral("window_id"), m_wid},
                {QStringLiteral("drawing_picture"), m_drawingarea.get()},
                {QStringLiteral("resize_pending"), m_resizeRequested},
                {QStringLiteral("video_embedded"), m_videoEmbed},
                {QStringLiteral("video_client"), m_videoClient != nullptr},
                {QStringLiteral("interface_client"), m_interfaceClient != nullptr},
                {QStringLiteral("render_width"), m_renderSize.width()},
                {QStringLiteral("render_height"), m_renderSize.height()},
                {QStringLiteral("interface_width"), m_interfaceSize.width()},
                {QStringLiteral("interface_height"), m_interfaceSize.height()}};
    }
#endif

public slots:
    void render(unsigned int requestId);
    void onWindowSizeChanged(const QSize& newSize);

    void requestRefresh();

    void onInterfaceSurfaceChanged(CompositorX11RenderClient*);
    void onVideoSurfaceChanged(CompositorX11RenderClient*);
    void onRegisterVideoWindow(unsigned int surface);

    void onVideoPositionChanged(const QRect& position);
    void onInterfaceSizeChanged(const QSize& size);

    void onVisibilityChanged(bool visible);

    void onAcrylicChanged(bool enabled);
    void onExtendedFrameChanged(bool enabled);

signals:
    void requestRefreshInternal(unsigned int requestId, QPrivateSignal priv);

private:
    xcb_render_picture_t getBackTexture();

    qt_intf_t* m_intf = nullptr;
    xcb_connection_t* m_conn = nullptr;

    QMutex& m_pictureLock;

    PicturePtr m_drawingarea;
    QSize m_renderSize;
    bool m_resizeRequested = true;

    xcb_drawable_t m_wid = 0;
    unsigned int m_refreshRequestId = 0;
    QRect m_videoPosition;
    QSize m_interfaceSize;

    CompositorX11RenderClient* m_videoClient = nullptr;
    bool m_videoEmbed = false;
    CompositorX11RenderClient* m_interfaceClient = nullptr;

    bool m_hasAcrylic = false;
    bool m_hasExtendedFrame = false;
    bool m_visible = true;
};

/**
 * @brief The X11DamageObserver class  allows to register and listen to
 * damages on a X11 surface. This is performed on a separate X11 connection
 * from Qt, as we want to be able to be able to continue refreshing the composition
 * when Qt main thread is stalled.
 */
class X11DamageObserver : public QObject
{
    Q_OBJECT
public:
    X11DamageObserver(qt_intf_t* intf, xcb_connection_t* conn, QObject* parent = nullptr);

    bool init();
    void start();

public slots:
    bool onRegisterSurfaceDamage(unsigned int surface);

signals:
    void needRefresh();

private:
    void onEvent();

public:
    qt_intf_t* m_intf = nullptr;

    xcb_connection_t* m_conn = nullptr;
    int m_connFd = 0;
    xcb_damage_damage_t m_dammage = 0;
    uint8_t m_xdamageBaseEvent = 0;

    QSocketNotifier* m_socketNotifier = nullptr;
};

class CompositorX11RenderWindow : public DummyRenderWindow, public AccessibleRenderWindow
{
    friend class CompositorX11;

    Q_OBJECT
public:
    explicit CompositorX11RenderWindow(qt_intf_t* p_intf, xcb_connection_t* conn,
                                       QWindow* parent = nullptr, bool initiallyVisible = true,
                                       Qt::WindowFlags initialFlags = {});
    ~CompositorX11RenderWindow();

    bool init();

    bool startRendering();
    void stopRendering();

    void setVideoPosition(const QPoint& position, bool signalChange = true);
    void setVideoSize(const QSize& size, bool signalChange = true);
    void setVideoGeometry(const std::optional<QPoint>& position,
                          const std::optional<QSize>& size);

    inline bool hasAcrylic() const { return m_hasAcrylic; }
    void setAcrylic(bool value);
    inline bool supportExtendedFrame() const { return m_supportExtendedFrame; }

    void setVideoWindow(QWindow* window);
    void setInterfaceWindow(CompositorX11UISurface* window);
    void setInterfaceWindow(QQuickWindow* window);

    void enableVideoWindow();
    void disableVideoWindow();

    QQuickWindow* getOffscreenWindow() const override;
#ifdef VLC_PLAYER_DIAGNOSTICS
    // Read-only observation of this output's X server request stream.
    xcb_connection_t* diagnosticConnection() const { return m_conn; }
    RenderTask* diagnosticTask() const { return m_renderTask; }
#endif

signals:
    void windowSizeChanged(const QSize& newSize);
    void requestUIRefresh();
    void interfaceSizeChanged(const QSize& size);
    void videoPositionChanged(const QRect& position);
    void videoSurfaceChanged(CompositorX11RenderClient*);
    void visiblityChanged(bool visible);
    void registerVideoWindow(unsigned int xid);
    bool hasExtendedFrameChanged(bool hasExtendedFrame);
    void acrylicChanged(bool value);

protected:
    //override from QWindow
    bool event(QEvent *) override;
    void resizeEvent(QResizeEvent *) override;
    void showEvent(QShowEvent *) override;
    void hideEvent(QHideEvent *) override;

private:
    void resetClientPixmaps();
    void onWindowExtendedMarginChanged(unsigned margin);
    void setHasExtendedFrame(bool hasExtendedFrame);

    qt_intf_t* m_intf = nullptr;
    xcb_connection_t* m_conn = nullptr;

    QThread* m_renderThread = nullptr;
    RenderTask* m_renderTask = nullptr;
    X11DamageObserver* m_damageObserver = nullptr;
    QMutex m_pictureLock;

    xcb_window_t m_wid = 0;

    bool m_hasAcrylic = false;
    //does the compositor support extended frames
    bool m_supportExtendedFrame = false;
    //is extended frame enabled
    bool m_hasExtendedFrame = false;

    QWindow* m_videoWindow = nullptr;
    std::unique_ptr<CompositorX11RenderClient> m_videoClient;
    QRect m_videoPosition;

    CompositorX11UISurface* m_interfaceWindow = nullptr;
    QQuickWindow* m_quickWindow = nullptr;
    std::unique_ptr<CompositorX11RenderClient> m_interfaceClient;

    QWindow::Visibility m_lastVisibility;
};

}

#endif // RENDERWINDOW_HPP
