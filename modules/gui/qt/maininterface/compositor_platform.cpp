/*****************************************************************************
 * Copyright (C) 2024 VLC authors and VideoLAN
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
#include "compositor_platform.hpp"

#include <QApplication>
#include <QQuickView>
#include <QOperatingSystemVersion>
#include <QQuickItem>
#include <QScreen>
#include <algorithm>
#include <cmath>

#include "maininterface/interface_window_handler.hpp"
#include "mainctx.hpp"
#include "videosurface.hpp"

#include <vlc_window.h>

#ifdef __APPLE__
#include <objc/runtime.h>
#endif

using namespace vlc;


CompositorPlatform::CompositorPlatform(qt_intf_t *p_intf, QObject *parent)
    : CompositorVideo(p_intf, parent)
{

}

bool CompositorPlatform::init()
{
    // TODO: For now only qwindows and qdirect2d
    //       running on Windows 8+, and cocoa
    //       platforms are supported.

    const QString& platformName = qApp->platformName();

#ifdef _WIN32
    if (QOperatingSystemVersion::current() >= QOperatingSystemVersion::Windows8)
    {
        if (platformName == QLatin1String("windows") || platformName == QLatin1String("direct2d"))
        {
            // Video embedding with RHI often does not work, VirtualBox drivers may work, but VMWare
            // and Nvidia drivers (non-VM) don't. So we only allow this in non-RHI modes at the
            // moment. Note that using software rasterizer (such as D3D Warp), that can be requested
            // with `QSG_RHI_PREFER_SOFTWARE_RENDERER`, also does not work.
            if (qEnvironmentVariable("QT_QUICK_BACKEND", QStringLiteral("rhi")) == QLatin1String("rhi"))
                return false;

            return true; // Practically "software" and "openvg" modes (non-RHI).
        }
    }
#endif

#ifdef __APPLE__
    if (platformName == QLatin1String("cocoa") || platformName == QLatin1String("ios"))
        return true;
#endif

#ifdef QT_HAS_X11_COMPOSITOR
    // Use native child windows under X11/XWayland, just as Cocoa does. A
    // Wayland foreign wl_surface cannot be wrapped by QWindow::fromWinId.
    if (platformName == QLatin1String("xcb")) return true;
#endif

    return false;
}

bool CompositorPlatform::makeMainInterface(MainCtx *mainCtx, std::function<void (QQuickWindow *)> aboutToShowQuickWindowCallback)
{
    m_mainCtx = mainCtx;

    m_rootWindow = std::make_unique<QWindow>();

    m_videoWindow = new QWindow(m_rootWindow.get());

    m_quickWindow = new QQuickView(m_rootWindow.get());
    m_quickWindow->setResizeMode(QQuickView::SizeRootObjectToView);

    {
        // Transparency set-up:
        m_quickWindow->setColor(Qt::transparent);

        QSurfaceFormat format = m_quickWindow->format();
        format.setAlphaBufferSize(8);
        m_quickWindow->setFormat(format);
    }

    // Make sure the UI child window has the same size as the root parent window:
    connect(m_rootWindow.get(), &QWindow::widthChanged, m_quickWindow, &QWindow::setWidth);
    connect(m_rootWindow.get(), &QWindow::heightChanged, m_quickWindow, &QWindow::setHeight);

    m_quickWindow->create();

    const bool ret = commonGUICreate(m_rootWindow.get(), m_quickWindow, CompositorVideo::CAN_SHOW_PIP | CompositorVideo::HAS_ACRYLIC);

    m_quickWindow->setFlag(Qt::FramelessWindowHint);
    // Qt QPA Bug (qwindows, qdirect2d(?)): to trigger WS_EX_LAYERED set up.
    m_quickWindow->setOpacity(0.0);
    m_quickWindow->setOpacity(1.0);

    m_rootWindow->installEventFilter(this);

    if (aboutToShowQuickWindowCallback)
        aboutToShowQuickWindowCallback(m_quickWindow);

    m_rootWindow->setVisible(true);
    m_videoWindow->setVisible(true);
    m_quickWindow->setVisible(true);

    m_quickWindow->raise(); // Make sure quick window is above the video window.

    return ret;
}

void CompositorPlatform::destroyMainInterface()
{
    commonIntfDestroy();
}

void CompositorPlatform::unloadGUI()
{
    hideFloatingPlayer();
    if (m_floatingView) m_floatingView->setSource(QUrl());
    m_floatingRoot.reset();
    m_rootWindow->removeEventFilter(this);
    m_interfaceWindowHandler.reset();
    m_quickWindow->setSource(QUrl());
    commonGUIDestroy();
}

bool CompositorPlatform::setupVoutWindow(vlc_window_t *p_wnd, VoutDestroyCb destroyCb)
{
    if (m_wnd)
        return false;

    commonSetupVoutWindow(p_wnd, destroyCb);

#ifdef __WIN32
    p_wnd->type = VLC_WINDOW_TYPE_HWND;
    p_wnd->handle.hwnd = reinterpret_cast<void*>(m_videoWindow->winId());

    return true;
#endif

#ifdef __APPLE__
    p_wnd->type = VLC_WINDOW_TYPE_NSOBJECT;
    p_wnd->handle.nsobject = reinterpret_cast<id>(m_videoWindow->winId());

    return true;
#endif

#ifdef QT_HAS_X11_COMPOSITOR
    p_wnd->type = VLC_WINDOW_TYPE_XID;
    p_wnd->handle.xid = m_videoWindow->winId();
    m_x11Display = qgetenv("DISPLAY");
    p_wnd->display.x11 = m_x11Display.constData();
    return true;
#endif

    vlc_assert_unreachable();
}

QWindow *CompositorPlatform::interfaceMainWindow() const
{
    return m_rootWindow.get();
}

QQuickWindow *CompositorPlatform::quickWindow() const
{
    return m_quickWindow.get();
}

Compositor::Type CompositorPlatform::type() const
{
    return Compositor::PlatformCompositor;
}

QQuickItem *CompositorPlatform::activeFocusItem() const
{
    assert(m_quickWindow);
    if (m_floatingView && m_floatingRoot->isActive()) return m_floatingView->activeFocusItem();
    return m_quickWindow->activeFocusItem();
}

bool CompositorPlatform::showFloatingPlayer(Qt::WindowStates previousState)
{
#ifdef _WIN32
    // The Windows DComp implementation retains its own visual ownership.
    Q_UNUSED(previousState);
    return false;
#else
    if (!m_videoWindow || !m_videoSurfaceProvider->isEnabled()) return false;
    if (m_mainCtx->floatingPlayer()) return true;
    m_mainStateBeforeFloating = previousState & ~Qt::WindowMinimized;
    if (!m_floatingRoot) {
        m_floatingRoot = std::make_unique<QWindow>();
        auto root = m_floatingRoot.get();
        root->setObjectName(QStringLiteral("floatingPlayerWindow"));
        root->setFlags(Qt::Tool | Qt::FramelessWindowHint | Qt::WindowStaysOnTopHint);
        root->setProperty("_q_showWithoutActivating", true);
        m_floatingView = new QQuickView(m_quickWindow->engine(), root);
        auto view = m_floatingView.get();
        view->setColor(Qt::transparent);
        auto format = view->format(); format.setAlphaBufferSize(8); view->setFormat(format);
        view->setPersistentGraphics(true);
        view->setPersistentSceneGraph(true);
        view->setResizeMode(QQuickView::SizeRootObjectToView);
        connect(root, &QWindow::widthChanged, view, &QWindow::setWidth);
        connect(root, &QWindow::heightChanged, view, &QWindow::setHeight);
        root->installEventFilter(this);
        view->setSource(QUrl(QStringLiteral("qrc:/qt/qml/VLC/Player/FloatingPlayer.qml")));
        if (view->status() != QQuickView::Ready || !view->rootObject()) {
            msg_Err(m_intf, "Floating player QML failed to load");
            m_floatingRoot.reset();
            return false;
        }
        // QML drag/resize acts on the top-level native window, not its
        // transparent Quick overlay child. It still uses the same controllers.
        view->rootObject()->setProperty("nativeWindow", QVariant::fromValue(root));
        // implicitHeight can be notifying from inside queueHeight's binding.
        // Read the completed layout in the next GUI event, not reentrantly.
        connect(view->rootObject(), &QQuickItem::implicitHeightChanged, this,
                &CompositorPlatform::constrainFloatingPlayer, Qt::QueuedConnection);
        connect(root, &QWindow::screenChanged, this, &CompositorPlatform::constrainFloatingPlayer);
        connect(root, &QWindow::xChanged, this, &CompositorPlatform::constrainFloatingPlayer);
        connect(root, &QWindow::yChanged, this, &CompositorPlatform::constrainFloatingPlayer);
        connect(root, &QWindow::widthChanged, this, &CompositorPlatform::constrainFloatingPlayer);
        const auto identity = [this] {
            m_floatingRoot->setTitle(m_rootWindow->title() + QStringLiteral(" — ") + tr("Miniplayer"));
            m_floatingRoot->setIcon(m_mainCtx->getRedesignWindowIcon());
        };
        connect(m_rootWindow.get(), &QWindow::windowTitleChanged, view, identity);
        connect(m_mainCtx, &MainCtx::redesignAccentChanged, view, identity);
        identity();
    }
    const auto screen = m_rootWindow->screen();
    const auto area = screen->availableGeometry();
    m_floatingRoot->setScreen(screen);
    m_floatingRoot->resize(std::min(360, area.width() - 32), 280);
    m_floatingRoot->setPosition(area.right() + 1 - m_floatingRoot->width() - 16,
                                area.bottom() + 1 - m_floatingRoot->height() - 16);
    m_videoWindow->setParent(m_floatingRoot.get());
    m_mainCtx->setFloatingPlayer(true);
    constrainFloatingPlayer();
    m_floatingRoot->show();
    m_videoWindow->show();
    m_floatingView->show();
    m_floatingView->raise();
    m_floatingView->rootObject()->setProperty("ready", true);
    return true;
#endif
}

void CompositorPlatform::hideFloatingPlayer()
{
    if (!m_floatingRoot || !m_mainCtx || !m_mainCtx->floatingPlayer()) return;
    m_videoWindow->setParent(m_rootWindow.get());
    m_mainCtx->setFloatingPlayer(false);
    m_floatingView->rootObject()->setProperty("ready", false);
    m_floatingRoot->hide();
    m_videoWindow->show();
    m_quickWindow->raise();
}

void CompositorPlatform::restoreFloatingPlayer()
{
    hideFloatingPlayer();
    m_rootWindow->setWindowStates(m_mainStateBeforeFloating);
    m_rootWindow->show();
    m_rootWindow->raise();
    m_rootWindow->requestActivate();
}

void CompositorPlatform::dismissFloatingPlayer()
{
    m_mainCtx->dismissFloatingPlayerUntilRestore();
    hideFloatingPlayer();
}

void CompositorPlatform::constrainFloatingPlayer()
{
    if (!m_floatingView || !m_floatingView->rootObject() || m_constrainingFloating) return;
    m_constrainingFloating = true;
    const auto area = m_floatingRoot->screen()->availableGeometry().adjusted(8, 8, -8, -8);
    auto item = m_floatingView->rootObject();
    item->setProperty("availableHeight", area.height());
    const int maximum = std::max(1, std::min({640, area.width(), int((area.height() - 100) * 16 / 9)}));
    const int width = std::clamp(m_floatingRoot->width(), std::min(260, maximum), maximum);
    m_floatingView->setWidth(width);
    const int height = std::min(area.height(), int(std::ceil(item->implicitHeight())));
    m_floatingRoot->resize(width, height);
    m_floatingRoot->setPosition(std::clamp(m_floatingRoot->x(), area.left(), area.right() + 1 - width),
                                std::clamp(m_floatingRoot->y(), area.top(), area.bottom() + 1 - height));
    m_constrainingFloating = false;
}

bool CompositorPlatform::eventFilter(QObject *watched, QEvent *event)
{
    if (watched == m_floatingRoot.get() && event->type() == QEvent::Close) {
        event->ignore();
        dismissFloatingPlayer();
        return true;
    }
    // Forward drag events to the child quick window,
    // as it is not done automatically by Qt with
    // nested windows:
    if (m_quickWindow && watched == m_rootWindow.get())
    {
        switch (event->type()) {
        case QEvent::DragEnter:
        case QEvent::DragLeave:
        case QEvent::DragMove:
        case QEvent::DragResponse:
        case QEvent::Drop:
            QApplication::sendEvent(m_quickWindow, event);
            return true;
        default:
            break;
        };
    }
    return false;
}

void CompositorPlatform::commitSurface()
{
    if (!m_videoWindow)
        return;

    if (m_pendingPosition && m_pendingSize)
    {
        m_videoWindow->setGeometry(m_pendingPosition->x(), m_pendingPosition->y(),
                                   m_pendingSize->width(), m_pendingSize->height());
        m_pendingPosition.reset();
        m_pendingSize.reset();
    }
    else
    {
        if (m_pendingSize)
        {
            m_videoWindow->resize(*m_pendingSize);
            m_pendingSize.reset();
        }
        else if (m_pendingPosition)
        {
            m_videoWindow->setPosition(*m_pendingPosition);
            m_pendingPosition.reset();
        }
    }
}

int CompositorPlatform::windowEnable(const vlc_window_cfg_t *)
{
    commonWindowEnable();
    return VLC_SUCCESS;
}

void CompositorPlatform::windowDisable()
{
    commonWindowDisable();
}

void CompositorPlatform::onSurfacePositionChanged(const QPointF &position)
{
    const QPointF point = position / m_videoWindow->devicePixelRatio();
    m_pendingPosition = QPoint{static_cast<int>(point.x()), static_cast<int>(point.y())};
}

void CompositorPlatform::onSurfaceSizeChanged(const QSizeF &size)
{
    const QSizeF area = (size / m_videoWindow->devicePixelRatio());
    m_pendingSize = QSize{static_cast<int>(std::ceil(area.width())), static_cast<int>(std::ceil(area.height()))};
}
