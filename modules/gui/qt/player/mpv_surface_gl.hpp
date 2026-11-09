/* Copyright (C) 2026 VLC authors and VideoLAN
 * SPDX-License-Identifier: GPL-2.0-or-later
 * Included by mpv_playback.cpp after Api, inside its private namespace.
 */

// A single native OpenGL view follows the compositor's video window. MPV's
// render context is created, used and destroyed on that view's Qt GUI thread;
// native VLC window operations remain on Surface's worker because they call
// back into the GUI synchronously. All core commands use MPV's async API.
class GlView final : public QWindow {
    std::shared_ptr<Api> api;
    mpv_handle *player;
    mpv_render_context *render = nullptr;
    QOpenGLContext context;
    QOffscreenSurface cleanupSurface;
    std::function<void(QString)> report;
    std::atomic_bool updatePending{false};
    bool transferringWindow = false;

    static void *getProcAddress(void *, const char *name) {
        return reinterpret_cast<void *>(QOpenGLContext::currentContext()->getProcAddress(name));
    }
    static void updated(void *opaque) {
        auto self = static_cast<GlView *>(opaque);
        if (!self->updatePending.exchange(true))
            QMetaObject::invokeMethod(self, [self] {
                self->updatePending = false;
                self->draw();
            }, Qt::QueuedConnection);
    }
    void draw() {
        if (!render || transferringWindow || !isExposed() || !width() || !height()) return;
        if (!context.makeCurrent(this)) { report(tr("The native MPV OpenGL view could not be made current.")); return; }
        api->render_context_update(render);
        const qreal dpr = devicePixelRatio();
        mpv_opengl_fbo fbo{int(context.defaultFramebufferObject()),
            qRound(width() * dpr), qRound(height() * dpr), 0};
        int flip = 1;
        int blockForTargetTime = 0; // The GUI owns this context; never wait for a presentation deadline here.
        mpv_render_param params[] = {{MPV_RENDER_PARAM_OPENGL_FBO, &fbo},
            {MPV_RENDER_PARAM_FLIP_Y, &flip}, {MPV_RENDER_PARAM_BLOCK_FOR_TARGET_TIME, &blockForTargetTime},
            {MPV_RENDER_PARAM_INVALID, nullptr}};
        const int code = api->render_context_render(render, params);
        if (code < 0) report(QString::fromUtf8(api->error_string(code)));
#ifdef VLC_PLAYER_DIAGNOSTICS
        // Observe the actual rendered buffer separately from X11 composition.
        // This is test-only and never changes normal rendering or readiness.
        QByteArray samples;
        for (int column = 1; column < 8; ++column) {
            unsigned char rgba[4]{};
            context.functions()->glReadPixels(fbo.w * column / 8, fbo.h / 2,
                1, 1, GL_RGBA, GL_UNSIGNED_BYTE, rgba);
            samples.append(reinterpret_cast<const char *>(rgba), 4);
        }
        setProperty("mpvRenderSamples", QString::fromLatin1(samples.toHex()));
        setProperty("mpvRenderCode", code);
        setProperty("mpvRenderCount", property("mpvRenderCount").toULongLong() + 1);
#endif
        context.swapBuffers(this);
        api->render_context_report_swap(render);
        context.doneCurrent();
    }
protected:
    void exposeEvent(QExposeEvent *) override { draw(); }
    void resizeEvent(QResizeEvent *) override { draw(); }
public:
    GlView(std::shared_ptr<Api> api, mpv_handle *player,
           std::function<void(QString)> report)
        : api(std::move(api)), player(player), report(std::move(report)) {
        setObjectName(QStringLiteral("mpvOpenGLVideo"));
        setSurfaceType(QSurface::OpenGLSurface);
        QSurfaceFormat format;
        format.setRenderableType(QSurfaceFormat::OpenGL);
        format.setVersion(3, 2);
        format.setProfile(QSurfaceFormat::CoreProfile);
        setFormat(format);
    }
    void initializeRenderContext() {
        create();
        context.setFormat(format());
        context.setScreen(screen());
        if (!context.create()) { report(tr("Qt could not create the native MPV OpenGL context.")); return; }
        // Initialize before a loaded file exposes its video surface. Waiting
        // for expose/paint here would deadlock first-file loading at Ready.
        // The same offscreen surface owns teardown even after a native reparent.
        cleanupSurface.setFormat(context.format());
        cleanupSurface.setScreen(screen());
        cleanupSurface.create();
        if (!context.makeCurrent(&cleanupSurface)) {
            report(tr("Qt could not initialize the native MPV OpenGL surface.")); return;
        }
        mpv_opengl_init_params init{getProcAddress, nullptr};
        mpv_render_param params[] = {
            {MPV_RENDER_PARAM_API_TYPE, const_cast<char *>(MPV_RENDER_API_TYPE_OPENGL)},
            {MPV_RENDER_PARAM_OPENGL_INIT_PARAMS, &init},
            {MPV_RENDER_PARAM_INVALID, nullptr}};
        const int code = api->render_context_create(&render, player, params);
        if (code < 0) { context.doneCurrent(); report(QString::fromUtf8(api->error_string(code))); return; }
        api->render_context_set_update_callback(render, updated, this);
        context.doneCurrent();
        report({});
    }
    void update() { draw(); }
    bool prepareWindowTransfer() {
        Q_ASSERT(QThread::currentThread() == thread());
        transferringWindow = true;
        if (!render) return true;
        if (!context.makeCurrent(&cleanupSurface)) {
            transferringWindow = false;
            report(tr("The native MPV render surface could not be prepared for transfer."));
            return false;
        }
        // A timing query in the next frame can flush the previous scene.
        // Complete that scene while its old X11 drawable/redirection exists.
        context.functions()->glFinish();
        context.doneCurrent();
        return true;
    }
    void finishWindowTransfer() { transferringWindow = false; draw(); }
    void releaseRenderContext() {
        if (!render) return;
        const bool current = context.makeCurrent(&cleanupSurface);
        Q_ASSERT(current);
        if (!current) { report(tr("The native MPV render context could not be released.")); return; }
        api->render_context_set_update_callback(render, nullptr, nullptr);
        api->render_context_free(render);
        render = nullptr;
        context.doneCurrent();
    }
    ~GlView() override { Q_ASSERT(!render); }
};

class Surface final : public QObject {
    std::shared_ptr<Api> api;
    mpv_handle *player;
    qt_intf_t *intf;
    QObject *owner;
    std::function<void(QString)> ready;
    vlc_window_t *window = nullptr;
    QPointer<GlView> view;
    bool enabled = false, closing = false;

    void report(const QString &error) {
        QMetaObject::invokeMethod(owner, [callback = ready, error] { callback(error); }, Qt::QueuedConnection);
    }
    static void resized(vlc_window_t *wnd, unsigned width, unsigned height,
                        vlc_window_ack_cb ack, void *opaque) {
        QPointer<Surface> self = static_cast<Surface *>(wnd->owner.sys);
        // The callback can arrive on the GUI thread. Never synchronously
        // invoke that thread from itself or retain VLC's acknowledgement.
        QMetaObject::invokeMethod(self->owner, [self, width, height] {
            if (self && self->view && width && height) {
                const auto dpr = self->view->devicePixelRatio();
                self->view->resize(int(std::ceil(width / dpr)), int(std::ceil(height / dpr)));
                self->view->update();
            }
        }, Qt::QueuedConnection);
        if (ack) ack(wnd, width, height, opaque);
    }
public:
    Surface(std::shared_ptr<Api> api, mpv_handle *player, qt_intf_t *intf, QObject *owner,
            std::function<void(QString)> ready)
        : api(std::move(api)), player(player), intf(intf), owner(owner), ready(std::move(ready)) { }
    void initialize() {
        static const vlc_window_callbacks callbacks = [] {
            vlc_window_callbacks value{};
            value.resized = resized;
            value.keyboard_event = [](vlc_window_t *wnd, unsigned key) {
                var_SetInteger(vlc_object_instance(wnd), "key-pressed", key);
            };
            value.mouse_event = [](vlc_window_t *wnd, const vlc_window_mouse_event_t *event) {
                if (event->button_mask == MOUSE_BUTTON_RIGHT &&
                    (event->type == VLC_WINDOW_MOUSE_PRESSED || event->type == VLC_WINDOW_MOUSE_RELEASED))
                    var_SetBool(vlc_object_instance(wnd), "intf-popupmenu", event->type == VLC_WINDOW_MOUSE_RELEASED);
                else if (event->type == VLC_WINDOW_MOUSE_DOUBLE_CLICK && event->button_mask == MOUSE_BUTTON_LEFT)
                    var_SetInteger(vlc_object_instance(wnd), "qt-mpv-action", ACTIONID_TOGGLE_FULLSCREEN);
                else if (event->type == VLC_WINDOW_MOUSE_RELEASED && event->button_mask == MOUSE_BUTTON_LEFT) {
                    char *policy = var_InheritString(wnd, "mouse-pause-policy");
                    const bool pause = !policy || strcmp(policy, "disabled");
                    free(policy);
                    if (pause) var_SetInteger(vlc_object_instance(wnd), "qt-mpv-action", ACTIONID_PLAY_PAUSE);
                }
            };
            return value;
        }();
        const vlc_window_owner_t windowOwner{&callbacks, this};
        vlc_window_cfg_t cfg{}; cfg.width = 640; cfg.height = 360;
        window = vlc_window_New(VLC_OBJECT(intf), "qt", &windowOwner, &cfg);
        WId handle = 0;
        if (window) {
#ifdef __APPLE__
            if (window->type == VLC_WINDOW_TYPE_NSOBJECT) handle = WId(window->handle.nsobject);
#else
            if (window->type == VLC_WINDOW_TYPE_XID) handle = WId(window->handle.xid);
#endif
        }
        if (!handle) { report(tr("MPV requires the native Qt video compositor (Cocoa or X11/XWayland).")); return; }
        if (vlc_window_Enable(window) != VLC_SUCCESS) {
            report(tr("The embedded MPV video surface could not be enabled.")); return;
        }
        enabled = true;
        QMetaObject::invokeMethod(owner, [this, handle] {
            // The qt window provider already owns this QWindow. Wrapping its
            // NSView/XID as a second foreign QWindow loses its Qt visibility
            // and exposure hierarchy, leaving the initial paused frame hidden.
            QWindow *parent = nullptr;
            for (auto candidate : QGuiApplication::allWindows())
                if (candidate->handle() && candidate->winId() == handle) {
                    parent = candidate;
                    break;
                }
            if (!parent) { report(tr("Qt could not attach the native MPV video view.")); return; }
            view = new GlView(api, player, [this](const QString &error) { report(error); });
#ifdef QT_HAS_X11_COMPOSITOR
            auto provider = intf->p_mi->getVideoSurfaceProvider();
            QObject::connect(provider, &VideoSurfaceProvider::windowAboutToTransfer, view,
                [this](bool& ready) { ready = view->prepareWindowTransfer() && ready; }, Qt::DirectConnection);
            QObject::connect(provider, &VideoSurfaceProvider::windowTransferred, view,
                [this] { view->finishWindowTransfer(); }, Qt::DirectConnection);
#endif
            view->setParent(parent);
            view->resize(640, 360);
            view->initializeRenderContext();
            view->show();
        }, Qt::BlockingQueuedConnection);
    }
    void setVideoActive(bool active) {
        if (closing || !window || active == enabled) return;
        if (active) {
            if (vlc_window_Enable(window) != VLC_SUCCESS) {
                report(tr("The embedded MPV video surface could not be enabled.")); return;
            }
            enabled = true;
        } else { vlc_window_Disable(window); enabled = false; }
    }
    void close() {
        if (closing) return;
        closing = true;
        QMetaObject::invokeMethod(owner, [this] {
            if (view) { view->releaseRenderContext(); delete view; }
        }, Qt::BlockingQueuedConnection);
        if (enabled) { vlc_window_Disable(window); enabled = false; }
        if (window) { vlc_window_Delete(window); window = nullptr; }
    }
};
