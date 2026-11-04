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

#include <cassert>

#include <dwmapi.h>
#include <winuser.h>

namespace {
constexpr LONG_PTR noRedirectionBitmap = 0x00200000L;
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
    if (enable)
    {
        assert(window->surfaceType() == QSurface::Direct3DSurface);
        // QRhi presents alpha through DirectComposition. A legacy layered
        // bitmap or integer window region suppresses DWM's smooth corners and
        // backdrop. The swapchain owns alpha; DWM owns the outer native clip.
        auto style = GetWindowLongPtr(hwnd, GWL_EXSTYLE);
        assert(style & noRedirectionBitmap);
        SetWindowLongPtr(hwnd, GWL_EXSTYLE, style & ~WS_EX_LAYERED);
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
