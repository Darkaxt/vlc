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

#if !defined(_WIN32_WINNT) || _WIN32_WINNT < 0x0603
# undef _WIN32_WINNT
# define _WIN32_WINNT 0x0603
#endif

#ifdef HAVE_CONFIG_H
# include "config.h"
#endif

#include "compositor_dcomp.hpp"
#include "player_video_backdrop.hpp"

#include "maininterface/mainctx_win32.hpp"

#include <vlc_window.h>

#ifndef QT_GUI_PRIVATE
#warning "QRhiD3D11 and QRhi headers are required for DirectComposition compositor."
#endif

#include <QtGui/qpa/qplatformnativeinterface.h>

#if __has_include(<d3d11_1.h>)
#define QRhiD3D11_ACTIVE
#include <QtGui/private/qrhid3d11_p.h>
#endif

#if __has_include(<d3d12.h>) && __has_include(<d3d12sdklayers.h>)
#include <QtGui/private/qrhid3d12_p.h>
#ifdef QRHI_D3D12_AVAILABLE
#define QRhiD3D12_ACTIVE
#endif
#endif

#if !defined(QRhiD3D11_ACTIVE) && !defined(QRhiD3D12_ACTIVE)
#warning "Neither D3D11 nor D3D12 headers are available. compositor_dcomp will not work."
#endif

#include "compositor_dcomp_acrylicsurface.hpp"
#include "maininterface/interface_window_handler.hpp"

#include <memory>
#include <type_traits>
#include <QScreen>
#include <QQmlContext>
#include "videosurface.hpp"
#include "player/player_controller.hpp"
#include "playlist/playlist_controller.hpp"
#include "windoweffects_module.hpp"
#include <algorithm>

namespace vlc {

Microsoft::WRL::ComPtr<PlayerVideoBackdrop> CompositorDirectComposition::playerBackdrop() const
{
    QMutexLocker lock(&m_playerBackdropLock);
    return m_playerBackdrop;
}

int CompositorDirectComposition::windowEnable(const vlc_window_cfg_t *)
{
    assert(m_dcompDevice);
    assert(m_rootVisual);
    assert(m_videoVisual);
    assert(m_uiVisual);

    commonWindowEnable();

    const auto backdrop = playerBackdrop();
    // The blur copies already exist when vout is enabled. Insert the unfiltered
    // video below them, otherwise it covers their output beneath Qt's tint.
    const bool floating = m_floatingRoot && m_mainCtx->floatingPlayer();
    const auto ret = floating ? m_floatingRoot->AddVisual(m_videoVisual.Get(), FALSE, m_floatingUiVisual)
        : m_rootVisual->AddVisual(m_videoVisual.Get(), FALSE, backdrop ? backdrop->bottomVisual() : m_uiVisual);
    if (backdrop) backdrop->setEnabled(!floating);
    m_videoInFloating = floating && SUCCEEDED(ret);
    m_dcompDevice->Commit();
    if (floating) m_floatingDevice->Commit();

    if (ret == S_OK)
        return VLC_SUCCESS;
    else
        return VLC_EGENERIC;
}

void CompositorDirectComposition::windowDisable()
{
    assert(m_dcompDevice);
    assert(m_rootVisual);
    assert(m_videoVisual);

    commonWindowDisable();
    if (auto backdrop = playerBackdrop()) backdrop->setEnabled(false);

    auto parent = m_videoInFloating ? m_floatingRoot.Get() : m_rootVisual.Get();
    const auto ret = parent->RemoveVisual(m_videoVisual.Get());
    m_videoInFloating = false;
    assert(ret == S_OK);
    m_dcompDevice->Commit();
    if (parent == m_floatingRoot.Get()) m_floatingDevice->Commit();
}

void CompositorDirectComposition::windowDestroy()
{
    {
        QMutexLocker lock(&m_playerBackdropLock);
        m_playerBackdrop.Reset();
    }
    m_videoVisual.Reset();
    CompositorVideo::windowDestroy();
}

CompositorDirectComposition::CompositorDirectComposition( qt_intf_t* p_intf,  QObject *parent)
    : CompositorVideo(p_intf, parent)
{
}

CompositorDirectComposition::~CompositorDirectComposition()
{
    cleanup();

    //m_acrylicSurface should be released before the RHI context is destroyed
    assert(!m_acrylicSurface);
}

bool CompositorDirectComposition::init()
{
#if !defined(QRhiD3D11_ACTIVE) && !defined(QRhiD3D12_ACTIVE)
    msg_Warn(m_intf, "compositor_dcomp was not built with D3D11 or D3D12 headers. It will not work.");
    return false;
#endif

    {
        const QString& platformName = qApp->platformName();
        if (!(platformName == QLatin1String("windows") || platformName == QLatin1String("direct2d")))
            return false;
    }

    QString sceneGraphBackend = qEnvironmentVariable("QT_QUICK_BACKEND");
    if (!sceneGraphBackend.isEmpty() /* if empty, RHI is used */ &&
        sceneGraphBackend != QLatin1String("rhi"))
    {
        // No RHI means no D3D11 or D3D12, the graphics API check
        // below is only relevant when RHI is in use.
        // If QT_QUICK_BACKEND is set to software or openvg, then
        // `QQuickWindow::graphicsApi()` might still report D3D11 or
        // D3D12 until the scene graph is initialized.
        // Unlike `QQuickWindow::graphicsApi()`, `sceneGraphBackend()`
        // is only valid after the window is constructed, so instead
        // of using `QQuickWindow::sceneGraphBackend()`, simply probe
        // the environment variable.
        return false;
    }
    else
    {
        // If `QQuickWindow::setGraphicsApi()` is used with a non-RHI
        // mode such as `software`, Qt at the moment adjusts the scene
        // graph backend but not the `QQuickWindow::graphicsApi()`.
        // Until Qt does that, we need to check it here additionally:
        sceneGraphBackend = QQuickWindow::sceneGraphBackend();
        if (!sceneGraphBackend.isEmpty() && sceneGraphBackend != QLatin1String("rhi"))
            return false;
    }

    const auto graphicsApi = QQuickWindow::graphicsApi();
    if (graphicsApi != QSGRendererInterface::Direct3D11 &&
        graphicsApi != QSGRendererInterface::Direct3D12)
        return false;

    if (Q_UNLIKELY(qEnvironmentVariableIntValue("QT_D3D_NO_FLIP")))
    {
        // Qt does not use Direct Composition with the legacy swapchain model.
        return false;
    }

    std::unique_ptr<std::remove_pointer_t<HMODULE>, BOOL WINAPI (*)(HMODULE)>
        dcomplib(::LoadLibraryEx(TEXT("dcomp.dll"), nullptr, LOAD_LIBRARY_SEARCH_SYSTEM32), ::FreeLibrary);

    typedef HRESULT (__stdcall *DCompositionCreateDeviceFuncPtr)(
        _In_opt_ IDXGIDevice *dxgiDevice,
        _In_ REFIID iid,
        _Outptr_ void **dcompositionDevice);
    DCompositionCreateDeviceFuncPtr func = nullptr;
    if (dcomplib)
    {
        func = reinterpret_cast<DCompositionCreateDeviceFuncPtr>(
            GetProcAddress(dcomplib.get(), "DCompositionCreateDevice"));
    }

    Microsoft::WRL::ComPtr<IDCompositionDevice> device;
    if (!func || FAILED(func(nullptr, IID_PPV_ARGS(&device))))
    {
        msg_Warn(m_intf, "Can not create DCompositionDevice. CompositorDirectComposition will not work.");
        return false;
    }

    return true;
}

bool CompositorDirectComposition::setup()
{
    // WARNING: This lock is released explicitly as soon as we are ready to signal readiness:
    QMutexLocker lock(&m_setupStateLock);

    switch (m_setupState)
    {
    /* [[unlikely]] */ case SetupState::Fail:
        return false;
    /* [[unlikely]] */ case SetupState::Success:
        return true; // Already called
    /* [[likely]] */ default:
        break;
    }

    //Setup shouldn't be called once we are shutting down
    assert(m_mainCtx);
    assert(m_quickView);
    const auto rhi = m_quickView->rhi();
    assert(rhi);

    QRhiImplementation* const rhiImplementation = rhi->implementation();
    assert(rhiImplementation);
    QRhiSwapChain* const rhiSwapChain = m_quickView->swapChain();
    assert(rhiSwapChain);

    assert(m_quickView->rhi()->backend() == QRhi::D3D11 || m_quickView->rhi()->backend() == QRhi::D3D12);

    IDCompositionTarget* dcompTarget;
    if (rhi->backend() == QRhi::D3D11)
    {
#ifdef QRhiD3D11_ACTIVE
        m_dcompDevice = static_cast<QRhiD3D11*>(rhiImplementation)->dcompDevice;
        auto qswapchain = static_cast<QD3D11SwapChain*>(rhiSwapChain);
        dcompTarget = qswapchain->dcompTarget;
        m_uiVisual = qswapchain->dcompVisual;
#endif
    }
    else if (rhi->backend() == QRhi::D3D12)
    {
#ifdef QRhiD3D12_ACTIVE
        m_dcompDevice = static_cast<QRhiD3D12*>(rhiImplementation)->dcompDevice;
        auto qswapchain = static_cast<QD3D12SwapChain*>(rhiSwapChain);
        dcompTarget = qswapchain->dcompTarget;
        m_uiVisual = qswapchain->dcompVisual;
#endif
    }
    else
        Q_UNREACHABLE();

    assert(m_dcompDevice);
    assert(dcompTarget);
    assert(m_uiVisual);

    HRESULT res;
    res = m_dcompDevice->CreateVisual(&m_rootVisual);
    assert(res == S_OK);

    res = dcompTarget->SetRoot(m_rootVisual.Get());
    assert(res == S_OK);

    res = m_rootVisual->AddVisual(m_uiVisual, FALSE, NULL);
    assert(res == S_OK);

    m_setupState = SetupState::Success;
    m_setupStateCond.notify_all();
    lock.unlock();

    m_dcompDevice->Commit();

    if (!m_mainCtx->hasAcrylicSurface())
    {
        if (var_InheritBool(m_intf, "qt-backdrop-blur"))
        {
            QMetaObject::invokeMethod(this, [this]() {
                if (Q_UNLIKELY(!m_dcompDevice || !interfaceMainWindow()))
                    return;

                try
                {
                    m_acrylicSurface = std::make_unique<CompositorDCompositionAcrylicSurface>(m_intf, this, m_mainCtx, m_dcompDevice);
                }
                catch (const std::exception& exception)
                {
                    if (const auto what = exception.what())
                        msg_Warn(m_intf, "%s", what);
                }
            }, Qt::QueuedConnection);
        }
    }

    return true;
}

void CompositorDirectComposition::cleanup()
{
    destroyFloatingPlayer();
    {
        QMutexLocker lock(&m_playerBackdropLock);
        m_playerBackdrop.Reset();
    }
    m_videoVisual.Reset();
    m_acrylicSurface.reset();

    if (m_rootVisual && m_uiVisual)
    {
        // Just in case root visual deletes its children
        // when it is deleted: (Qt's UI visual should be
        // deleted by Qt itself)
        m_rootVisual->RemoveVisual(m_uiVisual);
    }

    m_rootVisual.Reset();

    // When the window receives the event `SurfaceAboutToBeDestroyed`,
    // the RHI and the RHI swap chain are going to be destroyed.
    // It should be noted that event filters receive events
    // before the watched object receives them.
    // Since these objects belong to Qt, we should clear them
    // in order to prevent potential dangling pointer dereference:
    m_dcompDevice = nullptr;
    m_uiVisual = nullptr;
}

bool CompositorDirectComposition::makeMainInterface(MainCtx* mainCtx, std::function<void(QQuickWindow*)> aboutToShowQuickWindowCallback)
{
    assert(mainCtx);
    m_mainCtx = mainCtx;

    m_quickView = std::make_unique<QQuickView>();
    const auto quickViewPtr = m_quickView.get();
    connect(quickViewPtr, &QWindow::windowStateChanged, this, [this](Qt::WindowState state) {
        if (state != Qt::WindowMinimized) hideFloatingPlayer();
    });

    m_quickView->setResizeMode(QQuickView::SizeRootObjectToView);
    m_quickView->setColor(Qt::transparent);

    m_quickView->installEventFilter(this);

    connect(quickViewPtr, &QQuickWindow::beforeSynchronizing, this, [this] {
        QVariantMap state;
        // QML is blocked here. Publish only the count across to the vout
        // owner, which must not traverse GUI objects when binding its surface.
        m_declaredBackdrops = size_t(m_quickView->contentItem()->findChildren<QQuickItem *>(
            QStringLiteral("playerVideoBackdrop")).size());
        if (auto backdrop = playerBackdrop(); backdrop && m_quickView->rootObject())
            state = backdrop->synchronize(m_quickView->rootObject(), m_quickView->devicePixelRatio());
#ifdef VLC_PLAYER_DIAGNOSTICS
        auto window = m_quickView.get();
        QMetaObject::invokeMethod(window, [window, state] {
            window->setProperty("playerVideoBackdropState", state);
        }, Qt::QueuedConnection);
#else
        Q_UNUSED(state);
#endif
    }, Qt::DirectConnection);

    connect(quickViewPtr,
            &QQuickWindow::frameSwapped, // At this stage, we can be sure that QRhi and QRhiSwapChain are valid.
            this,
            [this]() {
                if (!setup())
                {
                    // Similar to `QQuickWindow::sceneGraphError()` handling:
                    if (m_mainCtx)
                        m_mainCtx->askToQuit();
                }
            },
            Qt::SingleShotConnection);

    const bool noRedirectionSurface = MainCtxWin32::createWindowWithoutRedirectionSurfaceImpl(m_quickView.get());
    if (!noRedirectionSurface)
        qDebug() << "MainCtxWin32::createWindowWithoutRedirectionSurfaceImpl() returned false for window" << m_quickView.get();

    const bool ret = commonGUICreate(quickViewPtr, quickViewPtr, CompositorVideo::CAN_SHOW_PIP | CompositorVideo::HAS_ACRYLIC);

    if (!ret)
        return false;

    connect(quickViewPtr,
            &QQuickWindow::sceneGraphError,
            this,
            [this](QQuickWindow::SceneGraphError error, const QString &message) {
                qWarning() << "CompositorDComp: Scene Graph Error: " << error << ", Message: " << message;
                QMutexLocker lock(&m_setupStateLock);
                m_setupState = SetupState::Fail;
                m_setupStateCond.notify_all();
            }, static_cast<Qt::ConnectionType>(Qt::SingleShotConnection | Qt::DirectConnection));

    // Qt "terminates the application" by default if there is no connection made to the signal
    // QQuickWindow::sceneGraphError(). We need to do the same, because by the time the error
    // is reported, it will likely be too late (`makeMainInterface()` already returned true,
    // which is the latest point recovery is still possible) to recover from that error and
    // the interface will remain unfunctional. It was proposed to wait here until the scene
    // graph is done, but that was not changed in order not to slow down the application
    // start up.
    connect(quickViewPtr,
            &QQuickWindow::sceneGraphError,
            m_mainCtx,
            &MainCtx::askToQuit);

    if (aboutToShowQuickWindowCallback)
        aboutToShowQuickWindowCallback(quickViewPtr);

#ifdef VLC_PLAYER_DIAGNOSTICS
    // Optional composed-window capture needs DWM's input desktop. Keep this
    // diagnostic instance beyond every screen and prevent native activation.
    // Interactive/fullscreen audits continue to use an inactive desktop.
    if (!qEnvironmentVariableIsEmpty("VLC_PLAYER_DIAGNOSTICS_DIR")
        && qEnvironmentVariableIntValue("VLC_PLAYER_DIAGNOSTICS_OFFSCREEN") == 1) {
        QRect desktopBounds;
        for (auto screen : QGuiApplication::screens()) desktopBounds |= screen->geometry();
        m_quickView->setFlag(Qt::WindowDoesNotAcceptFocus);
        m_quickView->setProperty("_q_showWithoutActivating", true);
        m_quickView->setWindowState(Qt::WindowNoState);
        m_quickView->setPosition(desktopBounds.right() + 256, desktopBounds.top());
    }
#endif
    m_quickView->setVisible(true);
    return true;
}

void CompositorDirectComposition::onSurfacePositionChanged(const QPointF& position)
{
    assert(m_videoVisual);
    assert(m_dcompDevice);

    m_videoVisual->SetOffsetX(position.x());
    m_videoVisual->SetOffsetY(position.y());
    if (auto backdrop = playerBackdrop()) backdrop->setVideoPosition(position);
#ifdef VLC_PLAYER_DIAGNOSTICS
    auto view = m_quickView.get();
    QMetaObject::invokeMethod(view, [view, position] { view->setProperty("reportedVideoPosition", position); }, Qt::QueuedConnection);
#endif

    // WARNING: Commit is requested explicitly through `::commitSurface()` after size
    //          and position changes are applied.
}

void CompositorDirectComposition::onSurfaceSizeChanged(const QSizeF& size)
{
#ifdef VLC_PLAYER_DIAGNOSTICS
    auto view = m_quickView.get();
    QMetaObject::invokeMethod(view, [view, size] { view->setProperty("reportedVideoSize", size); }, Qt::QueuedConnection);
#else
    Q_UNUSED(size);
#endif
}

void CompositorDirectComposition::destroyMainInterface()
{
    if (m_videoVisual)
        msg_Err(m_intf, "video surface still active while destroying main interface");

    commonIntfDestroy();

    // We still need to call this explicitly, as it seems Qt does not send
    // the `QPlatformSurfaceEvent::SurfaceAboutToBeDestroyed` event if we
    // delete the window ourselves:
    cleanup();

    m_quickView.reset();

    // These can no longer be assumed to be valid anymore, since they are
    // managed by Qt and the window is already gone:
    assert(!m_dcompDevice);
    assert(!m_uiVisual);
}

void CompositorDirectComposition::unloadGUI()
{
    destroyFloatingPlayer();
    m_acrylicSurface.reset();
    m_interfaceWindowHandler.reset();

    {
        QMutexLocker lock(&m_setupStateLock);
        if (m_quickView) {
            disconnect(m_quickView.get(), &QQuickWindow::frameSwapped,
                       this, nullptr);
        }
        m_setupState = SetupState::Fail;
        m_setupStateCond.notify_all();
    }

    //at this point we need to unload the QML content but the window still need to
    //be valid as it may still be used by the vout window.
    //we cant' just delete the qmlEngine as the QmlView as the root item is parented to the QmlView
    //setSource() to nothing will effectively destroy the root item
    if (Q_LIKELY(m_quickView))
        m_quickView->setSource(QUrl());

    commonGUIDestroy();
}

bool CompositorDirectComposition::setupVoutWindow(vlc_window_t *p_wnd, VoutDestroyCb destroyCb)
{
    if (m_wnd)
        return false;

    {
        QMutexLocker lock(&m_setupStateLock);
        while (m_setupState == SetupState::Uninitialized)
        {
            const bool ret = m_setupStateCond.wait(&m_setupStateLock);
            if (!ret)
                return false;
        }
        if (m_setupState != SetupState::Success)
        {
            return false;
        }
    }

    assert(m_dcompDevice);

    const HRESULT hr = m_dcompDevice->CreateVisual(&m_videoVisual);

    if (FAILED(hr))
    {
        msg_Err(p_wnd, "create to create DComp video visual");
        return false;
    }

    commonSetupVoutWindow(p_wnd, destroyCb);
    p_wnd->type = VLC_WINDOW_TYPE_DCOMP;

    p_wnd->display.dcomp_device = m_dcompDevice;
    p_wnd->handle.dcomp_visual = m_videoVisual.Get();

    Microsoft::WRL::ComPtr<PlayerVideoBackdrop> backdrop;
    backdrop.Attach(new (std::nothrow) PlayerVideoBackdrop);
    const auto backdropResult = backdrop ? backdrop->initialize(m_dcompDevice, m_videoVisual.Get(), m_rootVisual.Get(), m_uiVisual, m_declaredBackdrops.load()) : E_OUTOFMEMORY;
    if (SUCCEEDED(backdropResult)) {
        p_wnd->handle.dcomp_visual = backdrop.Get();
        QMutexLocker lock(&m_playerBackdropLock);
        m_playerBackdrop = std::move(backdrop);
    } else {
        msg_Err(p_wnd, "Player video backdrop initialization failed (0x%lx)", static_cast<unsigned long>(backdropResult));
    }

    return true;
}

QWindow *CompositorDirectComposition::interfaceMainWindow() const
{
    return m_quickView.get();
}

Compositor::Type CompositorDirectComposition::type() const
{
    return Compositor::DirectCompositionCompositor;
}

void CompositorDirectComposition::addVisual(IDCompositionVisual *visual)
{
    assert(visual);
    assert(m_rootVisual);
    assert(m_dcompDevice);

    HRESULT hr = m_rootVisual->AddVisual(visual, TRUE, NULL);
    if (FAILED(hr))
        msg_Err(m_intf, "failed to add visual, code: 0x%lX", hr);

    m_dcompDevice->Commit();
}

void CompositorDirectComposition::removeVisual(IDCompositionVisual *visual)
{
    assert(visual);
	assert(m_rootVisual);
	assert(m_dcompDevice);

    auto hr = m_rootVisual->RemoveVisual(visual);
    if (FAILED(hr))
        msg_Err(m_intf, "failed to remove visual, code: 0x%lX", hr);

    m_dcompDevice->Commit();
}

QQuickItem * CompositorDirectComposition::activeFocusItem() const /* override */
{
    if (m_floatingView && m_floatingView->isActive()) return m_floatingView->activeFocusItem();
    return m_quickView->activeFocusItem();
}

bool CompositorDirectComposition::showFloatingPlayer(Qt::WindowStates previousState)
{
    if (!m_videoVisual || !m_videoSurfaceProvider->isEnabled()) return false;
    if (m_mainCtx->floatingPlayer()) return true;
    m_mainStateBeforeFloating = previousState & ~Qt::WindowMinimized;
    if (!m_floatingView) {
        // Reuse the engine's registered singleton controllers; this creates no
        // new player, decoder, media library or playback session.
        m_floatingView = std::make_unique<QQuickView>(m_quickView->engine(), nullptr);
        auto view = m_floatingView.get();
        view->setObjectName(QStringLiteral("floatingPlayerWindow"));
        view->setFlags(Qt::Tool | Qt::FramelessWindowHint | Qt::WindowStaysOnTopHint);
        view->setProperty("_q_showWithoutActivating", true);
        view->setColor(Qt::transparent);
        view->setPersistentGraphics(true);
        view->setPersistentSceneGraph(true);
        view->setResizeMode(QQuickView::SizeRootObjectToView);
        if (!MainCtxWin32::createWindowWithoutRedirectionSurfaceImpl(view)) {
            m_floatingView.reset();
            return false;
        }
        if (m_windowEffectsModule && m_windowEffectsModule->isEffectAvailable(view, WindowEffectsModule::BlurBehind))
            m_windowEffectsModule->setBlurBehind(view, m_mainCtx->backdropBlurRequested(), {});
        view->installEventFilter(this);
        connect(view, &QQuickWindow::frameSwapped, this, &CompositorDirectComposition::setupFloatingPlayer);
        connect(view, &QWindow::xChanged, this, &CompositorDirectComposition::constrainFloatingPlayer);
        connect(view, &QWindow::yChanged, this, &CompositorDirectComposition::constrainFloatingPlayer);
        connect(view, &QWindow::widthChanged, this, &CompositorDirectComposition::constrainFloatingPlayer);
        connect(view, &QWindow::heightChanged, this, &CompositorDirectComposition::constrainFloatingPlayer);
        connect(view, &QWindow::screenChanged, this, &CompositorDirectComposition::constrainFloatingPlayer);
        const auto identity = [this] {
            m_floatingView->setTitle(m_quickView->title() + QStringLiteral(" — ") + qtr("Miniplayer"));
            m_floatingView->setIcon(m_mainCtx->getRedesignWindowIcon());
        };
        connect(m_quickView.get(), &QWindow::windowTitleChanged, view, identity);
        connect(m_mainCtx, &MainCtx::redesignAccentChanged, view, identity);
        identity();
        view->setSource(QUrl(QStringLiteral("qrc:/qt/qml/VLC/Player/FloatingPlayer.qml")));
        if (view->status() != QQuickView::Ready || !view->rootObject()) {
            msg_Err(m_intf, "Floating player QML failed to load");
            m_floatingView.reset();
            return false;
        }
        connect(view->rootObject(), &QQuickItem::implicitHeightChanged, view, [this] {
            const int bottom = m_floatingView->y() + m_floatingView->height();
            m_floatingView->resize(m_floatingView->width(), qCeil(m_floatingView->rootObject()->implicitHeight()));
            m_floatingView->setY(bottom - m_floatingView->height());
            constrainFloatingPlayer();
        });
    }
    const auto area = m_quickView->screen()->availableGeometry();
    m_floatingView->setScreen(m_quickView->screen());
    const int width = std::min(360, area.width() - 32);
    m_floatingView->resize(width, qCeil(m_floatingView->rootObject()->implicitHeight()));
    m_floatingView->setPosition(area.right() + 1 - width - 16, area.bottom() + 1 - m_floatingView->height() - 16);
    m_mainCtx->setFloatingPlayer(true);
    constrainFloatingPlayer();
    // A hidden window retains its existing Qt target. Reattach the live video
    // on subsequent opens rather than waiting for a target-creation callback.
    if (m_floatingRoot) setupFloatingPlayer();
    m_floatingView->show();
    return true;
}

void CompositorDirectComposition::setupFloatingPlayer()
{
    if (!m_mainCtx->floatingPlayer() || m_videoInFloating) return;
    if (m_floatingRoot) {
        if (m_videoVisual && m_videoSurfaceProvider->isEnabled()) {
            const HRESULT removed = m_rootVisual->RemoveVisual(m_videoVisual.Get());
            HRESULT result = removed;
            if (SUCCEEDED(result)) result = m_floatingRoot->AddVisual(m_videoVisual.Get(), FALSE, m_floatingUiVisual);
            if (FAILED(result)) {
                if (SUCCEEDED(removed)) {
                    const auto backdrop = playerBackdrop();
                    m_rootVisual->AddVisual(m_videoVisual.Get(), FALSE, backdrop ? backdrop->bottomVisual() : m_uiVisual);
                    m_dcompDevice->Commit();
                }
                msg_Err(m_intf, "Could not move video into miniplayer (0x%lx)", static_cast<unsigned long>(result));
                restoreFloatingPlayer();
                return;
            }
            m_videoInFloating = true;
            if (auto backdrop = playerBackdrop()) backdrop->setEnabled(false);
            m_dcompDevice->Commit();
            m_floatingDevice->Commit();
        }
        m_floatingView->setProperty("floatingVideoCompositionReady", true);
        m_floatingView->rootObject()->setProperty("ready", true);
        return;
    }
    auto rhi = m_floatingView->rhi();
    auto swapchain = m_floatingView->swapChain();
    if (!rhi || !swapchain) return; // first frame supplies the real native target
    IDCompositionTarget *target = nullptr;
#ifdef QRhiD3D11_ACTIVE
    if (rhi->backend() == QRhi::D3D11) {
        auto chain = static_cast<QD3D11SwapChain *>(swapchain);
        target = chain->dcompTarget;
        m_floatingUiVisual = chain->dcompVisual;
        m_floatingDevice = static_cast<QRhiD3D11 *>(rhi->implementation())->dcompDevice;
    }
#endif
#ifdef QRhiD3D12_ACTIVE
    if (rhi->backend() == QRhi::D3D12) {
        auto chain = static_cast<QD3D12SwapChain *>(swapchain);
        target = chain->dcompTarget;
        m_floatingUiVisual = chain->dcompVisual;
        m_floatingDevice = static_cast<QRhiD3D12 *>(rhi->implementation())->dcompDevice;
    }
#endif
    // The target and its root must belong to the same device. Cross-device
    // composition is supported for child visuals (the existing video below),
    // not for installing another device's root on this Qt swapchain target.
    const char *step = "create root";
    HRESULT result = target && m_floatingUiVisual ? m_floatingDevice->CreateVisual(&m_floatingRoot) : E_NOINTERFACE;
    if (SUCCEEDED(result)) { step = "set root"; result = target->SetRoot(m_floatingRoot.Get()); }
    if (SUCCEEDED(result)) { step = "attach UI"; result = m_floatingRoot->AddVisual(m_floatingUiVisual, FALSE, nullptr); }
    if (FAILED(result)) {
        if (target && m_floatingUiVisual) target->SetRoot(m_floatingUiVisual);
        if (m_floatingDevice) m_floatingDevice->Commit();
        if (m_floatingRoot && m_floatingUiVisual) m_floatingRoot->RemoveVisual(m_floatingUiVisual);
        m_floatingRoot.Reset();
        msg_Err(m_intf, "Floating video composition failed at %s (0x%lx)", step, static_cast<unsigned long>(result));
        restoreFloatingPlayer();
        return;
    }
    // The target belongs to Qt's other RHI device; each device must commit its
    // own mutations when visuals from different devices share a tree.
    m_floatingDevice->Commit();
    setupFloatingPlayer();
}

void CompositorDirectComposition::hideFloatingPlayer()
{
    if (!m_floatingView || !m_mainCtx || !m_mainCtx->floatingPlayer()) return;
    if (m_videoInFloating && m_videoVisual && m_videoSurfaceProvider && m_videoSurfaceProvider->isEnabled()) {
        m_floatingRoot->RemoveVisual(m_videoVisual.Get());
        const auto backdrop = playerBackdrop();
        m_rootVisual->AddVisual(m_videoVisual.Get(), FALSE, backdrop ? backdrop->bottomVisual() : m_uiVisual);
        if (backdrop) backdrop->setEnabled(true);
        m_floatingDevice->Commit();
        m_dcompDevice->Commit();
    }
    m_videoInFloating = false;
    if (m_mainCtx) m_mainCtx->setFloatingPlayer(false);
    m_floatingView->hide();
    // The hidden Qt window retains its graphics resources. Its root remains
    // installed until native window teardown; later opens use the same tree.
    m_floatingView->setProperty("floatingVideoCompositionReady", false);
    if (m_floatingView->rootObject()) m_floatingView->rootObject()->setProperty("ready", false);
}

void CompositorDirectComposition::destroyFloatingPlayer()
{
    hideFloatingPlayer();
    if (m_floatingRoot && m_floatingUiVisual) m_floatingRoot->RemoveVisual(m_floatingUiVisual);
    m_floatingRoot.Reset();
    m_floatingUiVisual = nullptr;
    m_floatingView.reset();
    m_floatingDevice.Reset();
}

void CompositorDirectComposition::restoreFloatingPlayer()
{
    hideFloatingPlayer();
    if (!m_quickView) return;
    m_quickView->setWindowStates(m_mainStateBeforeFloating);
    m_quickView->show();
    m_quickView->raise();
    m_quickView->requestActivate();
}

void CompositorDirectComposition::dismissFloatingPlayer()
{
    hideFloatingPlayer();
    // No visibility/state callback reopens it. Only a later explicit minimize
    // of a playing video can start another floating-player lifecycle.
    m_intf->p_mainPlaylistController->stop();
}

void CompositorDirectComposition::constrainFloatingPlayer()
{
    if (!m_floatingView || !m_floatingView->rootObject() || m_constrainingFloating) return;
    m_constrainingFloating = true;
    const auto screen = m_floatingView->screen();
    if (screen) {
        const auto area = screen->availableGeometry().adjusted(8, 8, -8, -8);
        auto view = m_floatingView.get();
        if (auto root = view->rootObject()) root->setProperty("availableHeight", area.height());
        const int maxWidth = std::max(1, std::min({640, area.width(), int((area.height() - 100) * 16 / 9)}));
        view->setMinimumSize(QSize(std::min(260, maxWidth), 1));
        view->setMaximumSize(QSize(maxWidth, area.height()));
        const int width = std::clamp(view->width(), std::min(260, maxWidth), maxWidth);
        const int height = std::min(area.height(), qCeil(view->rootObject()->implicitHeight()));
        view->resize(width, height);
        view->setPosition(std::clamp(view->x(), area.left(), area.right()+1-width),
                          std::clamp(view->y(), area.top(), area.bottom()+1-height));
    }
    m_constrainingFloating = false;
}

bool CompositorDirectComposition::eventFilter(QObject *watched, QEvent *event)
{
    if (watched == m_floatingView.get() && event->type() == QEvent::Close) {
        event->ignore();
        dismissFloatingPlayer();
        return true;
    }
    switch (event->type())
    {
    case QEvent::PlatformSurface:
        if (watched == m_quickView.get() &&
            static_cast<QPlatformSurfaceEvent *>(event)->surfaceEventType() == QPlatformSurfaceEvent::SurfaceAboutToBeDestroyed)
        {
            cleanup();
        }
        break;
    default:
        break;
    }

    return QObject::eventFilter(watched, event);
}

void CompositorDirectComposition::commitSurface()
{
    assert(m_dcompDevice);
    m_dcompDevice->Commit();
}

}
