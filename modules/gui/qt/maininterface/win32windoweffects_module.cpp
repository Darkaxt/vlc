/*****************************************************************************
 * Copyright (C) 2024 VLC authors and VideoLAN
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * ( at your option ) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
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

#include "win32windoweffects_module.hpp"
#include "windoweffects_module.hpp"

#include <QOperatingSystemVersion>
#include <QWindow>
#include <QRegion>
#include <QVariant>
#include <QWidget>
#include <QBackingStore>
#include <QPointer>
#include <QEvent>
#include <QStyle>
#include <QPlatformSurfaceEvent>
#include <QtGui/qpa/qplatformbackingstore.h>
#include <QtGui/private/qrhid3d11_p.h>

// Reuse the same source-window thumbnail ABI as the upstream DComp compositor.
#include "compositor_dcomp_acrylicsurface.hpp"

#include <cassert>

#include <dwmapi.h>
#include <winuser.h>

namespace {
constexpr LONG_PTR noRedirectionBitmap = 0x00200000L;

DwmpCreateSharedThumbnailVisual thumbnailFunction()
{
    // dwmapi is already linked and remains loaded for the interface lifetime.
    return reinterpret_cast<DwmpCreateSharedThumbnailVisual>(
        GetProcAddress(GetModuleHandleW(L"dwmapi.dll"), MAKEINTRESOURCEA(147)));
}

// One native menu/dialog, one Qt-owned swapchain. The live source is exclusively
// an application window, never the desktop. No frame capture, CPU readback,
// second decoder, extra HWND, opacity animation or system acrylic tint is used.
class ContentBackdrop final : public QObject
{
    template<class T> using ComPtr = Microsoft::WRL::ComPtr<T>;
    QPointer<QWindow> m_window, m_source;
    QPointer<QWidget> m_widget;
    QRhi *m_rhi = nullptr;
    ComPtr<IDCompositionDevice> m_device;
    ComPtr<IDCompositionTarget> m_target;
    ComPtr<IDCompositionVisual> m_ui, m_root, m_thumbnailVisual;
    ComPtr<IDCompositionRectangleClip> m_clip;
    ComPtr<IDCompositionGaussianBlurEffect> m_blur;
    HTHUMBNAIL m_thumbnail = nullptr;
    bool m_queued = false, m_enabled = false, m_uiReparented = false;

    void release(bool restore)
    {
        // DirectComposition forbids a visual from being a target root and a
        // child at once. Undo the parenting before restoring Qt's root.
        if (m_uiReparented && m_root && m_ui) m_root->RemoveVisual(m_ui.Get());
        m_uiReparented = false;
        if (restore && m_target && m_ui) {
            m_target->SetRoot(m_ui.Get());
            m_device->Commit();
        }
        if (m_thumbnail) DwmUnregisterThumbnail(m_thumbnail);
        m_thumbnail = nullptr;
        m_blur.Reset(); m_clip.Reset(); m_thumbnailVisual.Reset();
        m_root.Reset(); m_ui.Reset(); m_target.Reset(); m_device.Reset();
        if (m_rhi) m_rhi->removeCleanupCallback(this);
        m_rhi = nullptr;
        if (m_window) {
            m_window->setProperty("redesignContentBackdropReady", false);
        }
        if (m_widget && m_widget->property("redesignNativeClip").toBool()) {
            m_widget->setProperty("redesignNativeClip", false);
            if (m_widget->isVisible()) {
                m_widget->style()->unpolish(m_widget);
                m_widget->style()->polish(m_widget);
                m_widget->update();
            }
        }
    }

    void schedule()
    {
        if (m_queued || !m_enabled) return;
        m_queued = true;
        // UpdateRequest/Paint arrive before Qt flushes. Run after that dispatch,
        // when the real swapchain exists; no guessed delay or repeated polling.
        QMetaObject::invokeMethod(this, [this] { m_queued = false; synchronize(); }, Qt::QueuedConnection);
    }

    void synchronize()
    {
        if (!m_enabled || !m_window || !m_widget || !m_widget->isVisible()) return;
        if (!m_source || !m_source->isVisible()) { release(true); return; }
        DWORD sourcePid = 0;
        GetWindowThreadProcessId(reinterpret_cast<HWND>(m_source->winId()), &sourcePid);
        if (sourcePid != GetCurrentProcessId()) {
            qWarning("Refusing a content backdrop from another process");
            m_enabled = false;
            m_window->setProperty("redesignContentBackdropError", QStringLiteral("source_not_owned"));
            release(true);
            return;
        }
        auto *store = m_widget->backingStore();
        auto *platform = store ? store->handle() : nullptr;
        auto *rhi = platform ? platform->rhi(m_window) : nullptr;
        if (!rhi) return;
        if (rhi->backend() != QRhi::D3D11) {
            m_enabled = false;
            m_window->setProperty("redesignContentBackdropError", QStringLiteral("unsupported_rhi_backend"));
            return;
        }
        const auto native=m_window->property("_vlc_widget_rhi").toMap();
        if (native.value(QStringLiteral("rhi")).value<QRhi *>() != rhi) return;
        auto *swapchain = static_cast<QD3D11SwapChain *>(native.value(QStringLiteral("swapchain")).value<QRhiSwapChain *>());
        if (!swapchain || !swapchain->dcompTarget || !swapchain->dcompVisual) return;
        HRESULT hr = S_OK;
        const char *operation = "create_native_graph";
        if (m_target.Get() != swapchain->dcompTarget || m_ui.Get() != swapchain->dcompVisual) {
            release(true);
            m_rhi = rhi;
            m_rhi->addCleanupCallback(this, [this](QRhi *) {
                // The old swapchain/target may be retiring. Do not restore it.
                m_rhi = nullptr;
                if(m_window) m_window->setProperty("_vlc_widget_rhi", QVariant());
                release(false);
            });
            m_device = static_cast<QRhiD3D11 *>(rhi->implementation())->dcompDevice;
            m_target = swapchain->dcompTarget;
            m_ui = swapchain->dcompVisual;
            ComPtr<IDCompositionDevice3> effects;
            hr = m_device->QueryInterface(IID_PPV_ARGS(&effects));
            if (SUCCEEDED(hr)) hr = m_device->CreateVisual(&m_root);
            if (SUCCEEDED(hr)) hr = m_device->CreateRectangleClip(&m_clip);
            if (SUCCEEDED(hr)) hr = effects->CreateGaussianBlurEffect(&m_blur);
            RECT sourceRect{};
            const auto source = reinterpret_cast<HWND>(m_source->winId());
            GetClientRect(source, &sourceRect);
            DWM_THUMBNAIL_PROPERTIES properties{};
            properties.dwFlags = DWM_TNP_SOURCECLIENTAREAONLY | DWM_TNP_VISIBLE |
                DWM_TNP_RECTDESTINATION | DWM_TNP_RECTSOURCE | DWM_TNP_OPACITY | DWM_TNP_ENABLE3D;
            properties.opacity = 255;
            properties.fVisible = TRUE;
            properties.fSourceClientAreaOnly = TRUE;
            properties.rcSource = properties.rcDestination = sourceRect;
            if (SUCCEEDED(hr)) {
                operation = "create_shared_thumbnail";
                hr = thumbnailFunction()(reinterpret_cast<HWND>(m_window->winId()),
                    source, 2, &properties, effects.Get(),
                    reinterpret_cast<void **>(m_thumbnailVisual.GetAddressOf()), &m_thumbnail);
            }
            if (SUCCEEDED(hr)) operation = "configure_shared_thumbnail";
            if (SUCCEEDED(hr)) hr = m_thumbnailVisual->SetEffect(m_blur.Get());
            if (SUCCEEDED(hr)) hr = m_blur->SetBorderMode(D2D1_BORDER_MODE_HARD);
            if (SUCCEEDED(hr)) hr = m_root->SetClip(m_clip.Get());
            if (SUCCEEDED(hr)) hr = m_root->AddVisual(m_thumbnailVisual.Get(), FALSE, nullptr);
            if (SUCCEEDED(hr)) {
                // These commands are committed together with the new root;
                // the displayed tree has no intermediate empty frame.
                operation = "detach_qt_root";
                hr = m_target->SetRoot(nullptr);
                if (SUCCEEDED(hr)) {
                    operation = "parent_qt_visual";
                    hr = m_root->AddVisual(m_ui.Get(), TRUE, m_thumbnailVisual.Get());
                    m_uiReparented = SUCCEEDED(hr);
                }
            }
        }
        if (SUCCEEDED(hr) && m_root) {
            const auto destination = reinterpret_cast<HWND>(m_window->winId());
            const auto source = reinterpret_cast<HWND>(m_source->winId());
            RECT rect{}, sourceRect{};
            POINT sourceOrigin{}, targetOrigin{};
            GetClientRect(destination, &rect); GetClientRect(source, &sourceRect);
            ClientToScreen(source, &sourceOrigin); ClientToScreen(destination, &targetOrigin);
            DWM_THUMBNAIL_PROPERTIES properties{};
            // Shared DComp thumbnails require ENABLE3D on updates as well as
            // creation; omitting it selects the incompatible legacy API path.
            properties.dwFlags = DWM_TNP_RECTDESTINATION | DWM_TNP_RECTSOURCE | DWM_TNP_ENABLE3D;
            properties.rcSource = properties.rcDestination = sourceRect;
            operation = "update_shared_thumbnail";
            hr = DwmUpdateThumbnailProperties(m_thumbnail, &properties);
            if (SUCCEEDED(hr)) operation = "update_content_clip";
            const float dpr = float(m_window->devicePixelRatio());
            const float radius = m_window->property("redesignBackdropRadius").toFloat() * dpr;
            if (SUCCEEDED(hr)) hr = m_thumbnailVisual->SetOffsetX(float(sourceOrigin.x-targetOrigin.x));
            if (SUCCEEDED(hr)) hr = m_thumbnailVisual->SetOffsetY(float(sourceOrigin.y-targetOrigin.y));
            if (SUCCEEDED(hr)) hr = m_blur->SetStandardDeviation(25.f*dpr);
            if (SUCCEEDED(hr)) hr = m_clip->SetLeft(0.f);
            if (SUCCEEDED(hr)) hr = m_clip->SetTop(0.f);
            if (SUCCEEDED(hr)) hr = m_clip->SetRight(float(rect.right));
            if (SUCCEEDED(hr)) hr = m_clip->SetBottom(float(rect.bottom));
            if (SUCCEEDED(hr)) hr = m_clip->SetTopLeftRadiusX(radius);
            if (SUCCEEDED(hr)) hr = m_clip->SetTopLeftRadiusY(radius);
            if (SUCCEEDED(hr)) hr = m_clip->SetTopRightRadiusX(radius);
            if (SUCCEEDED(hr)) hr = m_clip->SetTopRightRadiusY(radius);
            if (SUCCEEDED(hr)) hr = m_clip->SetBottomLeftRadiusX(radius);
            if (SUCCEEDED(hr)) hr = m_clip->SetBottomLeftRadiusY(radius);
            if (SUCCEEDED(hr)) hr = m_clip->SetBottomRightRadiusX(radius);
            if (SUCCEEDED(hr)) hr = m_clip->SetBottomRightRadiusY(radius);
            // Qt can rebind its root while recreating a resized swapchain.
            if (SUCCEEDED(hr)) operation = "commit_native_graph";
            if (SUCCEEDED(hr)) hr = m_target->SetRoot(m_root.Get());
            if (SUCCEEDED(hr)) hr = m_device->Commit();
#ifdef VLC_PLAYER_DIAGNOSTICS
            m_window->setProperty("redesignContentBackdropState", QVariantMap{
                {QStringLiteral("source_pid"), quint32(sourcePid)},
                {QStringLiteral("source_native_id"), QString::number(quintptr(source),16)},
                {QStringLiteral("source_class"), QString::fromLatin1(m_source->metaObject()->className())},
                {QStringLiteral("sigma_px"),25.f*dpr},
                {QStringLiteral("radius_px"),radius},
                {QStringLiteral("width_px"),int(rect.right)},{QStringLiteral("height_px"),int(rect.bottom)},
                {QStringLiteral("hresult"),quint32(hr)},
                {QStringLiteral("live_window_content"),true}});
#endif
        }
        if (FAILED(hr)) {
            qWarning("Application content backdrop %s failed: 0x%08lx", operation, static_cast<unsigned long>(hr));
            m_enabled = false;
            const QString failure = QString::fromLatin1(operation) + QLatin1Char(':') + QString::number(quint32(hr),16);
            m_window->setProperty("redesignContentBackdropError", failure);
            release(true);
        } else if (m_root && !m_window->property("redesignContentBackdropReady").toBool()) {
            m_window->setProperty("redesignContentBackdropReady", true);
            m_widget->setProperty("redesignNativeClip", true);
            m_widget->style()->unpolish(m_widget);
            m_widget->style()->polish(m_widget);
            m_widget->clearMask();
            m_widget->update();
        }
    }

public:
    explicit ContentBackdrop(QWindow *window) : QObject(window), m_window(window),
        m_widget(QWidget::find(window->winId()))
    {
        setObjectName("redesignContentBackdrop");
        window->installEventFilter(this);
        window->setProperty("_vlc_content_backdrop", true);
        if (m_widget) m_widget->installEventFilter(this);
    }
    ~ContentBackdrop() override {
        release(true);
        if(m_window) {
            m_window->setProperty("_vlc_content_backdrop", false);
            m_window->setProperty("_vlc_widget_rhi", QVariant());
        }
    }

    void setEnabled(bool enabled)
    {
        m_enabled = enabled;
        if (m_source) m_source->removeEventFilter(this);
        auto *source = m_window->property("redesignBackdropSource").value<QWindow *>();
        if (source != m_source) release(true);
        m_source = source;
        if (m_source) m_source->installEventFilter(this);
        m_window->setProperty("redesignBackdropRequested", enabled);
        if (enabled) m_window->setProperty("redesignContentBackdropError", QString());
        if (enabled) schedule(); else {
            release(true);
            if (m_widget && m_widget->property("redesignNativeClip").toBool()) {
                m_widget->setProperty("redesignNativeClip", false);
                m_widget->style()->unpolish(m_widget);
                m_widget->style()->polish(m_widget);
            }
        }
    }

    bool eventFilter(QObject *, QEvent *event) override
    {
        switch (event->type()) {
        case QEvent::UpdateRequest: case QEvent::Paint: case QEvent::Expose:
        case QEvent::Move: case QEvent::Resize: case QEvent::Show:
        case QEvent::ScreenChangeInternal: schedule(); break;
        case QEvent::Hide: release(true); break;
        case QEvent::PlatformSurface:
            if (static_cast<QPlatformSurfaceEvent *>(event)->surfaceEventType() == QPlatformSurfaceEvent::SurfaceAboutToBeDestroyed) {
                if(m_window) m_window->setProperty("_vlc_widget_rhi", QVariant());
                release(false);
            }
            break;
        default: break;
        }
        return false;
    }
};
}

static bool isEffectAvailable(const QWindow* window, const WindowEffectsModule::Effect effect)
{
    // Version check is done on module open, no need to re-do it here.
    switch (effect)
    {
    case WindowEffectsModule::BlurBehind:
        // A translucent raster QWidget uses UpdateLayeredWindowIndirect.
        // DWM accepting an attribute on that bitmap is not backdrop support.
        if (window->surfaceType() != QSurface::Direct3DSurface)
            return false;
        // Windows fixes this bit at CreateWindowEx time. SetWindowLongPtr,
        // including WM_STYLECHANGING, cannot add it to an existing HWND.
        if (!(GetWindowLongPtr(reinterpret_cast<HWND>(window->winId()), GWL_EXSTYLE)
              & noRedirectionBitmap))
            return false;
        return thumbnailFunction() && window->property("redesignBackdropSource").value<QWindow *>();
    default:
        return false;
    };
}

static void setBlurBehind(QWindow* const window, const bool enable, const QRegion& region)
{
    Q_UNUSED(region);

    assert(window);
    assert(window->winId()); // use QWindow::create() before calling this function

    const auto hwnd = reinterpret_cast<HWND>(window->winId());
    if (enable)
    {
        assert(window->surfaceType() == QSurface::Direct3DSurface);
        // QRhi presents alpha through DirectComposition. A legacy layered
        // bitmap or integer window region suppresses DWM's smooth corners and
        // backdrop. The swapchain owns alpha; DWM owns the outer native clip.
        auto style = GetWindowLongPtr(hwnd, GWL_EXSTYLE);
        assert(style & noRedirectionBitmap);
        SetWindowLongPtr(hwnd, GWL_EXSTYLE, style & ~WS_EX_LAYERED);
        const MARGINS margins{0, 0, 0, 0};
        DwmExtendFrameIntoClientArea(hwnd, &margins);
        // One exact DPR-scaled DComp clip owns every layer. The system's
        // independently rounded frame/border must not sit outside that clip.
        const DWORD corners = 1; // DWMWCP_DONOTROUND
        DwmSetWindowAttribute(hwnd, 33 /* DWMWA_WINDOW_CORNER_PREFERENCE */,
                              &corners, sizeof(corners));
        const COLORREF border = 0xfffffffe; // DWMWA_COLOR_NONE
        DwmSetWindowAttribute(hwnd, 34 /* DWMWA_BORDER_COLOR */, &border, sizeof(border));
    }

    enum BackdropType
    {
        DWMSBT_NONE = 1
    } backdropType = DWMSBT_NONE;

    const auto result = DwmSetWindowAttribute(hwnd,
                          38 /* DWMWA_SYSTEMBACKDROP_TYPE */,
                          &backdropType,
                          sizeof(backdropType));
    if (FAILED(result))
        qWarning("Could not set the native backdrop: 0x%08lx", static_cast<unsigned long>(result));
    auto *backdrop = static_cast<ContentBackdrop *>(window->findChild<QObject *>(
        QStringLiteral("redesignContentBackdrop"), Qt::FindDirectChildrenOnly));
    if (!backdrop && enable) backdrop = new ContentBackdrop(window);
    if (backdrop) backdrop->setEnabled(enable);
}

int QtWin32WindowEffectsOpen(vlc_object_t* p_this)
{
    assert(p_this);

    if (QOperatingSystemVersion::current()
        < QOperatingSystemVersion(QOperatingSystemVersion::Windows, 10, 0, 22621))
        return VLC_EGENERIC;

    const auto obj = reinterpret_cast<WindowEffectsModule*>(p_this);

    obj->setBlurBehind = setBlurBehind;
    obj->isEffectAvailable = isEffectAvailable;

    return VLC_SUCCESS;
}
