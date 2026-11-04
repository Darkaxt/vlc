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
#include "win32windoweffects_module.hpp"
#include "windoweffects_module.hpp"

#include <QOperatingSystemVersion>
#include <QWindow>
#include <QRegion>
#include <QVariant>
#include <QAbstractNativeEventFilter>
#include <QCoreApplication>
#include <QHash>
#include <QPointer>
#include <QPlatformSurfaceEvent>
#include <QWidget>

#include <cassert>

#include <dwmapi.h>
#include <winuser.h>

static void setBlurBehind(QWindow *window, bool enable, const QRegion& region);

namespace {
constexpr LONG_PTR noRedirectionBitmap = 0x00200000L;

// Qt regenerates GWL_EXSTYLE when its window flags change. Own only the two
// composition bits for windows using this effect, at that native transition;
// setting them once in QWidget::showEvent is overwritten by Qt afterwards.
class BackdropStyles final : public QObject, public QAbstractNativeEventFilter
{
    QHash<HWND, QPointer<QWindow>> m_windows;
public:
    explicit BackdropStyles(QObject *parent) : QObject(parent)
    {
        QCoreApplication::instance()->installNativeEventFilter(this);
    }
    void watch(QWindow *window, bool enabled)
    {
        window->setProperty("redesignOwnsBackdropStyle", enabled);
        const auto hwnd = reinterpret_cast<HWND>(window->winId());
        if (enabled) {
            m_windows.insert(hwnd, window);
            window->installEventFilter(this);
        } else {
            m_windows.remove(hwnd);
            window->removeEventFilter(this);
        }
    }
    bool nativeEventFilter(const QByteArray&, void *message, qintptr*) override
    {
        auto *event = static_cast<MSG *>(message);
        if (event->message != WM_STYLECHANGING || event->wParam != WPARAM(GWL_EXSTYLE))
            return false;
        auto owner = m_windows.find(event->hwnd);
        if (owner == m_windows.end()) return false;
        if (!owner.value() || !owner.value()->handle() ||
            reinterpret_cast<HWND>(owner.value()->winId()) != event->hwnd ||
            !owner.value()->property("redesignOwnsBackdropStyle").toBool()) {
            m_windows.erase(owner);
            return false;
        }
        auto *style = reinterpret_cast<STYLESTRUCT *>(event->lParam);
        style->styleNew = (style->styleNew & ~WS_EX_LAYERED) | noRedirectionBitmap;
        return false; // Preserve Qt's handling of every other style bit/event.
    }
    bool eventFilter(QObject *object, QEvent *event) override
    {
        auto *window = qobject_cast<QWindow *>(object);
        if (window && event->type() == QEvent::PlatformSurface &&
            static_cast<QPlatformSurfaceEvent *>(event)->surfaceEventType() == QPlatformSurfaceEvent::SurfaceCreated &&
            window->property("redesignOwnsBackdropStyle").toBool())
            setBlurBehind(window, true, {});
        return false;
    }
};

BackdropStyles *backdropStyles()
{
    static QPointer<BackdropStyles> styles;
    if (!styles) styles = new BackdropStyles(QCoreApplication::instance());
    return styles;
}
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
        // NOTE: Qt does not officially support translucent window with frame.
        //       The documentation states that `Qt::FramelessWindowHint` is
        //       required on certain platforms, such as Windows. Otherwise,
        //       The window starts with a white background, which is a widely
        //       known Windows issue regardless of translucency, but the white
        //       background is never cleared if the window clear color is
        //       translucent. In this case, minimizing and restoring the window
        //       makes the background cleared, but this still does not make
        //       it a portable solution.
        // NOTE: See QTBUG-56201, QTBUG-120691. From the reports, it appears
        //       that Nvidia graphics is "fine" with translucent framed window
        //       while Intel graphics is not. However, the said issue above
        //       is still a concern with Nvidia graphics according to my own
        //       experience.
        // TODO: Ideally, we should at least use the frameless window hint
        //       when CSD is in use and use native backdrop effect since
        //       the custom solution has more chance to cause issues.
        if (!window->flags().testFlag(Qt::FramelessWindowHint))
        {
            const auto extendedStyle = GetWindowLong((HWND)window->winId(), GWL_EXSTYLE);
            if (!(extendedStyle & 0x00200000L /* WS_EX_NOREDIRECTIONBITMAP */))
            {
                qDebug("Target window is not frameless and does not use WS_EX_NOREDIRECTIONBITMAP, " \
                       "window can not be translucent for the Windows 11 22H2 native acrylic backdrop effect.");
                return false;
            }
        }
        return true;
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
    // Quick's existing compositor owns its own native style. Keep this repair
    // restricted to accelerated QWidget menus/dialogs, including recreated HWNDs.
    if (window->property("redesignOwnsBackdropStyle").toBool() || QWidget::find(WId(hwnd)))
        backdropStyles()->watch(window, enable);
    if (enable)
    {
        assert(window->surfaceType() == QSurface::Direct3DSurface);
        // QRhi presents alpha through DirectComposition. A legacy layered
        // bitmap or integer window region suppresses DWM's smooth corners and
        // backdrop. The swapchain owns alpha; DWM owns the outer native clip.
        auto style = GetWindowLongPtr(hwnd, GWL_EXSTYLE);
        SetWindowLongPtr(hwnd, GWL_EXSTYLE,
                         (style & ~WS_EX_LAYERED) | noRedirectionBitmap);
        const MARGINS margins{-1, -1, -1, -1};
        DwmExtendFrameIntoClientArea(hwnd, &margins);
        const DWORD corners = 2; // DWMWCP_ROUND
        DwmSetWindowAttribute(hwnd, 33 /* DWMWA_WINDOW_CORNER_PREFERENCE */,
                              &corners, sizeof(corners));
    }

    enum BackdropType
    {
        DWMSBT_NONE = 1,
        DWMSBT_TRANSIENTWINDOW = 3
    } backdropType = enable ? DWMSBT_TRANSIENTWINDOW : DWMSBT_NONE;

    const auto result = DwmSetWindowAttribute(hwnd,
                          38 /* DWMWA_SYSTEMBACKDROP_TYPE */,
                          &backdropType,
                          sizeof(backdropType));
    window->setProperty("redesignBackdropRequested", enable && SUCCEEDED(result));
    if (FAILED(result))
        qWarning("Could not set the native backdrop: 0x%08lx", static_cast<unsigned long>(result));
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
