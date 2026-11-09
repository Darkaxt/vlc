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
#include <QImage>
#include <QSysInfo>
#include "compositor_x11_renderclient.hpp"
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
    QVariantMap diagnosticDrawable(xcb_drawable_t drawable) const {
        QVariantMap result{{QStringLiteral("drawable"), drawable}};
        if (!drawable) return result;
        xcb_generic_error_t* error = nullptr;
        auto geometry = xcb_get_geometry_reply(m_conn, xcb_get_geometry(m_conn, drawable), &error);
        if (!geometry || error) {
            result.insert(QStringLiteral("geometry_error"), error ? error->error_code : -1);
            free(error); free(geometry);
            return result;
        }
        const int width = geometry->width, height = geometry->height, depth = geometry->depth;
        const auto root = geometry->root;
        result.insert(QStringLiteral("width"), width);
        result.insert(QStringLiteral("height"), height);
        result.insert(QStringLiteral("depth"), depth);
        free(geometry);
        const auto setup = xcb_get_setup(m_conn);
        const auto nativeOrder = QSysInfo::ByteOrder == QSysInfo::LittleEndian
            ? XCB_IMAGE_ORDER_LSB_FIRST : XCB_IMAGE_ORDER_MSB_FIRST;
        bool rgb32 = false;
        for (auto formats = xcb_setup_pixmap_formats_iterator(setup); formats.rem; xcb_format_next(&formats))
            if (formats.data->depth == depth && formats.data->bits_per_pixel == 32) rgb32 = true;
        if (!rgb32 || setup->image_byte_order != nativeOrder || width <= 0 || height <= 0
            || width > 4096 || height > 4096) {
            result.insert(QStringLiteral("pixels_not_read"), QStringLiteral("unsupported image layout or extent"));
            return result;
        }
        // Queue native window facts immediately before GetImage on this same
        // connection. Later GUI snapshots cannot establish viewability at the
        // failed protocol boundary. Pixmap sources have no window attributes.
        xcb_get_window_attributes_cookie_t attributesCookie{};
        xcb_translate_coordinates_cookie_t coordinatesCookie{};
        if (drawable == m_wid) {
            attributesCookie = xcb_get_window_attributes(m_conn, drawable);
            coordinatesCookie = xcb_translate_coordinates(m_conn, drawable, root, 0, 0);
        }
        const auto imageCookie = xcb_get_image(m_conn, XCB_IMAGE_FORMAT_Z_PIXMAP,
            drawable, 0, 0, width, height, ~uint32_t(0));
        if (drawable == m_wid) {
            xcb_generic_error_t* attributesError = nullptr;
            auto attributes = xcb_get_window_attributes_reply(m_conn, attributesCookie, &attributesError);
            if (attributes) result.insert(QStringLiteral("map_state_before_image"), attributes->map_state);
            if (attributesError) result.insert(QStringLiteral("attributes_error"), attributesError->error_code);
            free(attributes); free(attributesError);
            auto coordinates = xcb_translate_coordinates_reply(m_conn, coordinatesCookie, nullptr);
            if (coordinates) {
                result.insert(QStringLiteral("root_x_before_image"), coordinates->dst_x);
                result.insert(QStringLiteral("root_y_before_image"), coordinates->dst_y);
                result.insert(QStringLiteral("same_screen_before_image"), coordinates->same_screen);
            }
            free(coordinates);
            for (auto screens = xcb_setup_roots_iterator(setup); screens.rem; xcb_screen_next(&screens)) {
                if (screens.data->root != root) continue;
                result.insert(QStringLiteral("screen_width"), screens.data->width_in_pixels);
                result.insert(QStringLiteral("screen_height"), screens.data->height_in_pixels);
            }
        }
        auto image = xcb_get_image_reply(m_conn, imageCookie, &error);
        if (!image || error || xcb_get_image_data_length(image) != width * height * 4) {
            result.insert(QStringLiteral("image_error"), error ? error->error_code : -1);
            if (error) {
                result.insert(QStringLiteral("image_error_resource"), error->resource_id);
                result.insert(QStringLiteral("image_error_major"), error->major_code);
                result.insert(QStringLiteral("image_error_minor"), error->minor_code);
            }
            free(error); free(image);
            return result;
        }
        const QImage pixels(xcb_get_image_data(image), width, height, width * 4, QImage::Format_RGB32);
        int nonblack = 0, chromatic = 0;
        for (int y = 0; y < height; ++y) {
            const auto row = reinterpret_cast<const QRgb*>(pixels.constScanLine(y));
            for (int x = 0; x < width; ++x) {
                const int high = qMax(qRed(row[x]), qMax(qGreen(row[x]), qBlue(row[x])));
                const int low = qMin(qRed(row[x]), qMin(qGreen(row[x]), qBlue(row[x])));
                if (high) ++nonblack;
                if (high >= 100 && high - low >= 80) ++chromatic;
            }
        }
        result.insert(QStringLiteral("nonblack_pixels"), nonblack);
        result.insert(QStringLiteral("chromatic_pixels"), chromatic);
        free(image);
        return result;
    }
    QVariantMap diagnosticClient(const CompositorX11RenderClient* client) const {
        if (!client) return {};
        auto result = diagnosticDrawable(client->diagnosticPixmap());
        result.insert(QStringLiteral("window"), client->getWindowXid());
        result.insert(QStringLiteral("picture"), client->diagnosticPicture());
        return result;
    }
    QVariantMap diagnosticState() const {
        QMutexLocker lock(&m_pictureLock);
        // Observe the output before reading either source. Extra diagnostic
        // roundtrips must not make a later screenshot stand for this boundary.
        const auto output = diagnosticDrawable(m_wid);
        const auto video = diagnosticClient(m_videoClient);
        const auto interface = diagnosticClient(m_interfaceClient);
        return {{QStringLiteral("visible"), m_visible},
                {QStringLiteral("request_id"), m_refreshRequestId},
                {QStringLiteral("window_id"), m_wid},
                {QStringLiteral("drawing_picture"), m_drawingarea.get()},
                {QStringLiteral("resize_pending"), m_resizeRequested},
                {QStringLiteral("video_embedded"), m_videoEmbed},
                {QStringLiteral("video_client"), m_videoClient != nullptr},
                {QStringLiteral("interface_client"), m_interfaceClient != nullptr},
                {QStringLiteral("output_before_sources"), output},
                {QStringLiteral("video_source"), video},
                {QStringLiteral("interface_source"), interface},
                {QStringLiteral("video_x"), m_videoPosition.x()},
                {QStringLiteral("video_y"), m_videoPosition.y()},
                {QStringLiteral("video_width"), m_videoPosition.width()},
                {QStringLiteral("video_height"), m_videoPosition.height()},
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
