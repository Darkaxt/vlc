/* Copyright (C) 2026 VLC authors and VideoLAN
 * SPDX-License-Identifier: GPL-2.0-or-later
 */
#ifdef HAVE_CONFIG_H
# include "config.h"
#endif
#include "mpv_playback.hpp"
#include "mpv/client.h"
#include "mpv/render.h"
#include "mpv/render_d3d11.h"
#if defined(_WIN32) && defined(VLC_MPV_RUNTIME_IDENTITY)
#include "mpv_runtime_identity.hpp"
#endif
#include <QCoreApplication>
#include <QCryptographicHash>
#include <QDir>
#include <QFile>
#include <QThread>
#include <QMutex>
#include <QMutexLocker>
#include <QSize>
#include <QUrl>
#include <atomic>
#include <algorithm>
#include <cassert>
#include <utility>
#include <vector>
#include <vlc_actions.h>
#include <vlc_mouse.h>
#include <vlc_player.h>
#include <vlc_aout.h>
#include <vlc_iso_lang.h>

#ifdef _WIN32
#include <vlc_window.h>
#include <d3d11.h>
#include <dxgi1_2.h>
#include <dcomp.h>
#include <wrl/client.h>
#endif

namespace {
struct Api {
#ifdef _WIN32
    HMODULE library = nullptr;
    ~Api() { if (library) FreeLibrary(library); }
#endif
#define MPV_API(name) decltype(&mpv_##name) name = nullptr
    MPV_API(create); MPV_API(initialize); MPV_API(set_option_string);
    MPV_API(command_async); MPV_API(set_property_async); MPV_API(observe_property);
    MPV_API(get_property_async); MPV_API(request_log_messages);
    MPV_API(wait_event); MPV_API(terminate_destroy); MPV_API(error_string);
    MPV_API(render_context_create); MPV_API(render_context_free);
    MPV_API(render_context_set_update_callback); MPV_API(render_context_update);
    MPV_API(render_context_render); MPV_API(render_context_report_swap);
#undef MPV_API

    bool load(QString &error)
    {
#ifndef _WIN32
        error = QObject::tr("The MPV engine is available in this Windows build only.");
        return false;
#elif !defined(VLC_MPV_RUNTIME_IDENTITY)
        error = QObject::tr("This build does not include the MPV runtime. Select VLC or use the complete MPV-enabled portable package.");
        return false;
#else
        const QDir directory(QCoreApplication::applicationDirPath());
        for (const auto &payload : MpvRuntimeIdentity::files) {
            QFile file(directory.filePath(QString::fromUtf8(payload.name)));
            if (!file.open(QIODevice::ReadOnly)) {
                error = QObject::tr("The application's MPV runtime is incomplete. Select VLC or restore the complete portable package.");
                return false;
            }
            QCryptographicHash hash(QCryptographicHash::Sha256);
            if (!hash.addData(&file) || hash.result().toHex() != QByteArray(payload.sha256)) {
                error = QObject::tr("The application's MPV runtime does not match this release. Select VLC or restore the complete portable package.");
                return false;
            }
        }
        const QString path = directory.filePath(QStringLiteral("libmpv-2.dll"));
        // winvlc restricts the process-wide DLL search to System32. Include
        // only this verified payload's directory for its bundled dependencies;
        // never add the current directory or change the process-wide policy.
        library = LoadLibraryExW(reinterpret_cast<LPCWSTR>(QDir::toNativeSeparators(path).utf16()),
            nullptr, LOAD_LIBRARY_SEARCH_DLL_LOAD_DIR | LOAD_LIBRARY_SEARCH_SYSTEM32);
        if (!library) {
            error = QObject::tr("Windows could not load the application's MPV runtime (error %1). Restore the complete portable package and check that the graphics driver includes the Vulkan runtime.").arg(GetLastError());
            return false;
        }
#define RESOLVE(name) name = reinterpret_cast<decltype(name)>(GetProcAddress(library,"mpv_" #name)); if (!name) { error = QObject::tr("The MPV library has an incompatible API."); return false; }
        RESOLVE(create); RESOLVE(initialize); RESOLVE(set_option_string);
        RESOLVE(command_async); RESOLVE(set_property_async); RESOLVE(observe_property);
        RESOLVE(get_property_async); RESOLVE(request_log_messages);
        RESOLVE(wait_event); RESOLVE(terminate_destroy); RESOLVE(error_string);
        RESOLVE(render_context_create); RESOLVE(render_context_free);
        RESOLVE(render_context_set_update_callback); RESOLVE(render_context_update);
        RESOLVE(render_context_render); RESOLVE(render_context_report_swap);
#undef RESOLVE
        return true;
#endif
    }
};

QVariant nodeValue(const mpv_node &node)
{
    switch (node.format) {
    case MPV_FORMAT_STRING: return QString::fromUtf8(node.u.string);
    case MPV_FORMAT_FLAG: return bool(node.u.flag);
    case MPV_FORMAT_INT64: return qlonglong(node.u.int64);
    case MPV_FORMAT_DOUBLE: return node.u.double_;
    case MPV_FORMAT_NODE_ARRAY: {
        QVariantList values;
        for (int i = 0; i < node.u.list->num; ++i) values.append(nodeValue(node.u.list->values[i]));
        return values;
    }
    case MPV_FORMAT_NODE_MAP: {
        QVariantMap values;
        for (int i = 0; i < node.u.list->num; ++i)
            values.insert(QString::fromUtf8(node.u.list->keys[i]), nodeValue(node.u.list->values[i]));
        return values;
    }
    default: return {};
    }
}

struct Event {
    int type = MPV_EVENT_NONE, error = 0, reason = -1;
    quint64 request = 0;
    qint64 entry = -1;
    QString name;
    QVariant value;
};

class Events final : public QThread {
public:
    std::shared_ptr<Api> api;
    mpv_handle *player;
    QObject *owner;
    std::function<void(Event)> receive;
    Events(std::shared_ptr<Api> api, mpv_handle *player, QObject *owner, std::function<void(Event)> receive)
        : api(std::move(api)), player(player), owner(owner), receive(std::move(receive)) { }
    void run() override
    {
        for (;;) {
            const auto raw = api->wait_event(player, -1); // Real native event, no polling deadline.
            Event event;
            event.type = raw->event_id; event.error = raw->error; event.request = raw->reply_userdata;
            if (event.type == MPV_EVENT_SHUTDOWN) break;
            if (event.type == MPV_EVENT_LOG_MESSAGE) {
                const auto message = static_cast<mpv_event_log_message *>(raw->data);
                event.name = QString::fromUtf8(message->prefix);
                event.value = QString::fromUtf8(message->text).trimmed();
                event.reason = message->log_level;
            } else if (event.type == MPV_EVENT_PROPERTY_CHANGE || event.type == MPV_EVENT_GET_PROPERTY_REPLY) {
                const auto property = static_cast<mpv_event_property *>(raw->data);
                event.name = QString::fromUtf8(property->name);
                if (property->format == MPV_FORMAT_NODE && property->data)
                    event.value = nodeValue(*static_cast<mpv_node *>(property->data));
            } else if (event.type == MPV_EVENT_START_FILE) {
                event.entry = static_cast<mpv_event_start_file *>(raw->data)->playlist_entry_id;
            } else if (event.type == MPV_EVENT_END_FILE) {
                const auto end = static_cast<mpv_event_end_file *>(raw->data);
                event.error = end->error; event.reason = end->reason; event.entry = end->playlist_entry_id;
            }
            QMetaObject::invokeMethod(owner, [deliver = receive, event] { deliver(event); }, Qt::QueuedConnection);
        }
    }
};

#ifdef _WIN32
template<class T> using ComPtr = Microsoft::WRL::ComPtr<T>;

class Surface final : public QObject {
    std::shared_ptr<Api> api;
    mpv_handle *player;
    qt_intf_t *intf;
    QObject *owner;
    std::function<void(QString)> ready;
    mpv_render_context *render = nullptr;
    vlc_window_t *window = nullptr;
    bool enabled = false, closing = false, firstPresented = false;
    QMutex sizeLock;
    std::atomic_bool updatePending{false};
    ComPtr<ID3D11Device> device;
    ComPtr<ID3D11DeviceContext> deviceContext;
    ComPtr<IDXGISwapChain1> swapchain;
    ComPtr<ID3D11Texture2D> target;
    ComPtr<IDCompositionVisual> visual;
    ComPtr<IDCompositionDevice> composition;
    QSize size{640, 360};
    QSize pendingSize{640, 360};

    void report(QString error) {
        QMetaObject::invokeMethod(owner, [callback = ready, error] { callback(error); }, Qt::QueuedConnection);
    }
    void check(HRESULT hr) {
        if (FAILED(hr)) throw QStringLiteral("Direct3D error 0x%1").arg(quint32(hr), 8, 16, QLatin1Char('0'));
    }
    static void updated(void *opaque) {
        auto self = static_cast<Surface *>(opaque);
        if (!self->updatePending.exchange(true))
            QMetaObject::invokeMethod(self, [self] { self->updatePending = false; self->draw(); }, Qt::QueuedConnection);
    }
    static void resized(vlc_window_t *wnd, unsigned width, unsigned height, vlc_window_ack_cb ack, void *opaque) {
        auto self = static_cast<Surface *>(wnd->owner.sys);
        {
            // Serialize acknowledgement with actual use of the old target.
            // Do not retain an opaque native acknowledgement past this call.
            QMutexLocker lock(&self->sizeLock);
            if (!self->closing && width && height)
                self->pendingSize = QSize(int(width), int(height));
            if (ack) ack(wnd, width, height, opaque);
        }
        QMetaObject::invokeMethod(self, [self] { self->draw(true); }, Qt::QueuedConnection);
    }
    void draw(bool force = false) {
        QMutexLocker lock(&sizeLock);
        if (closing || !render || !target) return;
        if (pendingSize != size) {
            try {
                target.Reset(); deviceContext->ClearState();
                check(swapchain->ResizeBuffers(0, pendingSize.width(), pendingSize.height(), DXGI_FORMAT_UNKNOWN, 0));
                size = pendingSize;
                check(swapchain->GetBuffer(0, IID_PPV_ARGS(&target)));
                force = true;
            } catch (const QString &error) { report(error); return; }
        }
        const auto flags = api->render_context_update(render);
        if (!force && !(flags & MPV_RENDER_UPDATE_FRAME)) return;
        mpv_d3d11_fbo fbo{target.Get()};
        mpv_render_param params[] = {{MPV_RENDER_PARAM_D3D11_FBO, &fbo}, {MPV_RENDER_PARAM_INVALID, nullptr}};
        deviceContext->ClearState();
        const int code = api->render_context_render(render, params);
        if (code < 0) { report(QString::fromUtf8(api->error_string(code))); return; }
        const auto hr = swapchain->Present(1, 0);
        if (FAILED(hr)) { report(QStringLiteral("Video presentation failed: 0x%1").arg(quint32(hr), 8, 16, QLatin1Char('0'))); return; }
        api->render_context_report_swap(render);
        if (!firstPresented && enabled && (flags & MPV_RENDER_UPDATE_FRAME) && hr == S_OK) {
            firstPresented = true;
            msg_Dbg(intf, "MPV picture presented");
        }
    }
public:
    Surface(std::shared_ptr<Api> api, mpv_handle *player, qt_intf_t *intf, QObject *owner,
            std::function<void(QString)> ready)
        : api(std::move(api)), player(player), intf(intf), owner(owner), ready(std::move(ready)) { }
    void setVideoActive(bool active) {
        if (closing || !window || active == enabled) return;
        if (active) {
            if (vlc_window_Enable(window) != VLC_SUCCESS) { report(tr("The embedded MPV video surface could not be enabled.")); return; }
            enabled = true;
            draw(true);
        } else { vlc_window_Disable(window); enabled = false; firstPresented = false; }
    }
    void initialize() {
        try {
            D3D_FEATURE_LEVEL level;
            check(D3D11CreateDevice(nullptr, D3D_DRIVER_TYPE_HARDWARE, nullptr, D3D11_CREATE_DEVICE_BGRA_SUPPORT,
                nullptr, 0, D3D11_SDK_VERSION, &device, &level, &deviceContext));
            mpv_d3d11_init_params init{device.Get()};
            int advanced = 1;
            mpv_render_param params[] = {{MPV_RENDER_PARAM_API_TYPE, const_cast<char *>(MPV_RENDER_API_TYPE_D3D11)},
                {MPV_RENDER_PARAM_D3D11_INIT_PARAMS, &init}, {MPV_RENDER_PARAM_ADVANCED_CONTROL, &advanced}, {MPV_RENDER_PARAM_INVALID, nullptr}};
            const int code = api->render_context_create(&render, player, params);
            if (code < 0) throw QString::fromUtf8(api->error_string(code));
            static const vlc_window_callbacks callbacks = [] {
                vlc_window_callbacks value{};
                value.resized = resized;
                value.keyboard_event = [](vlc_window_t *wnd, unsigned key) {
                    // The same Qt video surface forwards keys and wheel actions
                    // through the native hotkey owner in either engine.
                    var_SetInteger(vlc_object_instance(wnd), "key-pressed", key);
                };
                value.mouse_event = [](vlc_window_t *wnd, const vlc_window_mouse_event_t *event) {
                    if (event->type == VLC_WINDOW_MOUSE_DOUBLE_CLICK && event->button_mask == MOUSE_BUTTON_LEFT)
                        var_SetInteger(vlc_object_instance(wnd), "qt-mpv-action", ACTIONID_TOGGLE_FULLSCREEN);
                };
                return value;
            }();
            const vlc_window_owner_t windowOwner{&callbacks, this};
            vlc_window_cfg_t cfg{}; cfg.width = 640; cfg.height = 360;
            window = vlc_window_New(VLC_OBJECT(intf), "qt", &windowOwner, &cfg);
            if (!window || window->type != VLC_WINDOW_TYPE_DCOMP)
                throw tr("MPV requires this player's DirectComposition video surface. Select VLC for another compositor.");
            visual = static_cast<IDCompositionVisual *>(window->handle.dcomp_visual);
            composition = static_cast<IDCompositionDevice *>(window->display.dcomp_device);
            ComPtr<IDXGIDevice> dxgi;
            ComPtr<IDXGIAdapter> adapter;
            ComPtr<IDXGIFactory2> factory;
            check(device.As(&dxgi)); check(dxgi->GetAdapter(&adapter)); check(adapter->GetParent(IID_PPV_ARGS(&factory)));
            DXGI_SWAP_CHAIN_DESC1 desc{};
            desc.Width = 640; desc.Height = 360; desc.Format = DXGI_FORMAT_B8G8R8A8_UNORM;
            desc.SampleDesc.Count = 1; desc.BufferUsage = DXGI_USAGE_RENDER_TARGET_OUTPUT;
            desc.BufferCount = 2; desc.SwapEffect = DXGI_SWAP_EFFECT_FLIP_SEQUENTIAL;
            desc.Scaling = DXGI_SCALING_STRETCH; desc.AlphaMode = DXGI_ALPHA_MODE_IGNORE;
            check(factory->CreateSwapChainForComposition(device.Get(), &desc, nullptr, &swapchain));
            check(swapchain->GetBuffer(0, IID_PPV_ARGS(&target)));
            check(visual->SetContent(swapchain.Get())); check(composition->Commit());
            api->render_context_set_update_callback(render, updated, this);
            report({});
        } catch (const QString &error) { close(); report(error); }
    }
    void close() {
        {
            QMutexLocker lock(&sizeLock);
            if (closing) return;
            closing = true;
        }
        if (render) {
            api->render_context_set_update_callback(render, nullptr, nullptr);
            api->render_context_free(render); render = nullptr;
        }
        if (visual) { visual->SetContent(nullptr); composition->Commit(); }
        target.Reset(); swapchain.Reset(); visual.Reset(); composition.Reset();
        if (enabled) { vlc_window_Disable(window); enabled = false; }
        if (window) { vlc_window_Delete(window); window = nullptr; }
        deviceContext.Reset(); device.Reset();
    }
};
#endif
} // namespace

struct MpvPlayback::Private {
    MpvPlayback *q;
    qt_intf_t *intf;
    std::shared_ptr<Api> api = std::make_shared<Api>();
    mpv_handle *player = nullptr;
    std::unique_ptr<Events> events;
    QVariantMap properties;
    QHash<quint64, QString> requests;
    QHash<quint64, qint64> fileQueries;
    QHash<QString, QStringList> languagePreferences;
    QString error;
    quint64 nextRequest = 1;
    bool closing = false, ready = false;
    bool completed = false;
    bool replacing = false;
    bool loadStarting = false, stopping = false;
    bool loaded = false;
    qint64 activeEntry = -1;
    QUrl pending;
    bool pendingPaused = false;
    std::vector<std::function<void()>> completions;
#ifdef _WIN32
    QThread renderThread;
    Surface *surface = nullptr;
#endif

    Private(MpvPlayback *q, qt_intf_t *intf) : q(q), intf(intf) { }
    static QString languageCode(const QString &value) {
        const auto *language = vlc_find_iso639(value.trimmed().toUtf8().constData(), true);
        return language ? QString::fromUtf8(language->psz_iso639_2T) : QString();
    }
    void prepareLanguages() {
        languagePreferences.clear();
        for (const auto &entry : {std::pair{"audio-language", "aid"}, std::pair{"sub-language", "sid"}}) {
            const QString property = QString::fromLatin1(entry.second);
            char *raw = var_InheritString(intf, entry.first);
            const auto configured = QString::fromUtf8(raw ? raw : "");
            free(raw);
            QStringList preferences;
            for (const auto &value : configured.split(QLatin1Char(','), Qt::SkipEmptyParts)) {
                const auto token = value.trimmed().toLower();
                if (token == QStringLiteral("any") || token == QStringLiteral("none")) {
                    preferences.push_back(token);
                    break;
                }
                const auto code = languageCode(token);
                if (!code.isEmpty()) preferences.push_back(code);
            }
            const bool audio = property == QStringLiteral("aid");
            if (!var_InheritBool(intf, audio ? "audio" : "spu")) preferences = {QStringLiteral("none")};
            // Keep audio-only inputs loadable: MPV rejects an input with no
            // selected streams before FILE_LOADED. Supply its native language
            // preference first, then resolve VLC's fallback rules on real tracks.
            q->set(audio ? QStringLiteral("alang") : QStringLiteral("slang"), preferences.join(QLatin1Char(',')));
            q->set(property, var_InheritBool(intf, audio ? "audio" : "spu") ? QStringLiteral("auto") : QStringLiteral("no"));
            if (!preferences.isEmpty()) languagePreferences.insert(property, preferences);
        }
    }
    void finishFileLoad() {
        loaded = true;
        const auto tracks = properties.value(QStringLiteral("track-list")).toList();
        for (auto preference = languagePreferences.cbegin(); preference != languagePreferences.cend(); ++preference) {
            const bool audio = preference.key() == QStringLiteral("aid");
            QVariantMap selected;
            const auto choose = [&](const QString &language) {
                QVariantMap choice;
                for (const auto &value : tracks) {
                    const auto track = value.toMap();
                    if (track.value(QStringLiteral("type")).toString() != (audio ? QStringLiteral("audio") : QStringLiteral("sub"))) continue;
                    if (language != QStringLiteral("any") && languageCode(track.value(QStringLiteral("lang")).toString()) != language) continue;
                    if (choice.isEmpty() || (!choice.value(QStringLiteral("default")).toBool() && track.value(QStringLiteral("default")).toBool())) choice = track;
                }
                return choice;
            };
            for (const auto &language : preference.value()) {
                if (language == QStringLiteral("none")) break;
                selected = choose(language);
                if (!selected.isEmpty()) break;
            }
            // VLC permits audio fallback unless its explicit 'none' sentinel
            // forbids it. Subtitles use the configured 'any' fallback instead.
            if (selected.isEmpty() && audio && preference.value().last() != QStringLiteral("none"))
                selected = choose(QStringLiteral("any"));
            q->set(preference.key(), selected.isEmpty() ? QVariant(QStringLiteral("no")) : selected.value(QStringLiteral("id")));
        }
        emit q->fileLoaded();
    }
    void deliverProperty(const QString &name, const QVariant &value) {
        properties[name] = value;
#ifdef _WIN32
        if (surface && name == QStringLiteral("video-params")) {
            const bool active = !value.toMap().isEmpty();
            QMetaObject::invokeMethod(surface, [this, active] { surface->setVideoActive(active); }, Qt::QueuedConnection);
        }
#endif
        emit q->changed(name, value);
    }
    void receive(const Event &event) {
        if (closing) return;
        if (event.type == MPV_EVENT_LOG_MESSAGE) {
            const auto prefix = event.name.toUtf8(), text = event.value.toString().toUtf8();
            if (event.reason <= MPV_LOG_LEVEL_ERROR) msg_Err(intf, "mpv/%s: %s", prefix.constData(), text.constData());
            else if (event.reason <= MPV_LOG_LEVEL_WARN) msg_Warn(intf, "mpv/%s: %s", prefix.constData(), text.constData());
            else msg_Dbg(intf, "mpv/%s: %s", prefix.constData(), text.constData());
        } else if (event.type == MPV_EVENT_START_FILE) {
            activeEntry = event.entry;
            loadStarting = false;
            if (!pending.isEmpty()) { q->load(pending, pendingPaused); return; }
            replacing = false;
        } else if (event.type == MPV_EVENT_PROPERTY_CHANGE) {
            if (replacing && (event.name == QStringLiteral("time-pos") || event.name == QStringLiteral("duration")
                || event.name == QStringLiteral("track-list") || event.name == QStringLiteral("metadata")
                || event.name == QStringLiteral("media-title") || event.name == QStringLiteral("path")
                || event.name == QStringLiteral("video-params") || event.name == QStringLiteral("video-out-params") || event.name == QStringLiteral("chapter-list"))) return;
            deliverProperty(event.name, event.value);
        } else if (event.type == MPV_EVENT_FILE_LOADED && !replacing && !stopping) {
            // Observers may coalesce equal values across two inputs. Read a
            // fresh file snapshot before announcing the incoming input ready.
            fileQueries.clear();
            for (const auto *name : {"duration", "time-pos", "seekable", "pause", "track-list", "metadata", "video-params", "video-out-params", "chapter-list", "chapter", "media-title", "path"}) {
                const auto request = nextRequest++;
                const int code = api->get_property_async(player, request, name, MPV_FORMAT_NODE);
                if (code < 0) {
                    fileQueries.clear();
                    q->command({QStringLiteral("stop")});
                    emit q->failed(QObject::tr("MPV could not inspect the loaded input: %1")
                        .arg(QString::fromUtf8(api->error_string(code))));
                    return;
                }
                fileQueries[request] = activeEntry;
            }
            if (fileQueries.isEmpty()) finishFileLoad();
        } else if (event.type == MPV_EVENT_GET_PROPERTY_REPLY && fileQueries.contains(event.request)) {
            const auto entry = fileQueries.take(event.request);
            if (entry != activeEntry || replacing || stopping) return;
            deliverProperty(event.name, event.value);
            if (fileQueries.isEmpty()) finishFileLoad();
        }
        else if (event.type == MPV_EVENT_GET_PROPERTY_REPLY && requests.contains(event.request)) {
            const auto name = requests.take(event.request);
            if (event.error < 0)
                deliverProperty(QStringLiteral("audio-session-query-error"), event.error);
            else deliverProperty(name, event.value);
        }
        else if (event.type == MPV_EVENT_END_FILE && !replacing && event.entry == activeEntry) {
            if (event.reason == MPV_END_FILE_REASON_EOF) msg_Dbg(intf, "MPV natural EOF reached");
            loaded = false;
            stopping = false; fileQueries.clear();
#ifdef _WIN32
            if (surface) QMetaObject::invokeMethod(surface, [this] { surface->setVideoActive(false); }, Qt::QueuedConnection);
#endif
            emit q->ended(event.reason == MPV_END_FILE_REASON_EOF,
                event.error < 0 ? QString::fromUtf8(api->error_string(event.error)) : QString());
        }
        else if (event.type == MPV_EVENT_SEEK && !replacing) emit q->seekStarted();
        else if (event.type == MPV_EVENT_PLAYBACK_RESTART && !replacing) emit q->playbackRestarted();
        else if (event.type == MPV_EVENT_COMMAND_REPLY || event.type == MPV_EVENT_SET_PROPERTY_REPLY) {
            const auto action = requests.take(event.request);
            if (event.error < 0 && action == QStringLiteral("loadfile")) {
                loadStarting = false; replacing = false;
                if (!pending.isEmpty()) q->load(pending, pendingPaused);
                else emit q->ended(false, QString::fromUtf8(api->error_string(event.error)));
                return;
            }
            if (event.error < 0) emit q->failed(QObject::tr("MPV could not apply %1: %2").arg(action, QString::fromUtf8(api->error_string(event.error))));
        }
    }
    void finishCore() {
        if (!player) { complete(); return; }
        if (!events || !events->isRunning()) { complete(); return; }
        const char *args[] = {"quit", nullptr};
        api->command_async(player, 0, args);
    }
    void complete() {
        // A finished signal precedes final QThread/TLS exit. The event reader
        // has returned and cannot request UI work now, so this join is safe.
        if (events) events->wait();
        if (player) { api->terminate_destroy(player); player = nullptr; }
        msg_Dbg(intf, "MPV native resources released");
        completed = true;
        const auto callbacks = std::move(completions);
        for (const auto &callback : callbacks) callback();
    }
};

MpvPlayback::MpvPlayback(qt_intf_t *intf, QObject *parent) : QObject(parent), d(std::make_unique<Private>(this, intf))
{
    if (!d->api->load(d->error)) return;
    d->player = d->api->create();
    if (!d->player) { d->error = tr("The MPV player could not be created."); return; }
    const std::pair<const char *, const char *> options[] = {{"config", "no"}, {"vo", "libmpv"},
        {"terminal", "no"}, {"input-default-bindings", "no"},
        {"idle", "yes"}, {"demuxer", "lavf"}, {"ao", "wasapi"},
        {"audio-exclusive", "no"}, {"wasapi-device-role", "console"},
        // Direct D3D11 hardware frames lost DV correction at the FFmpeg filter
        // boundary in the pinned build. Explicit copy-back retains metadata;
        // its rendered Profile 5 pixels match the software reference.
        {"input-vo-keyboard", "no"}, {"input-media-keys", "no"}, {"hwdec", "d3d11va-copy"},
        {"gpu-shader-cache", "no"},
        // libmpv's D3D11 render API uses the legacy gl_video renderer, which
        // restores base-layer mapping and cannot reshape Dolby Vision itself.
        // Apply the frame-associated RPU with the pinned FFmpeg/libplacebo
        // filter first, with an explicit BT.709/sRGB full-range RGB output.
        // This avoids guessing an unset base-layer matrix or tone-mapping the
        // result again in the legacy presentation renderer.
        {"vf", "lavfi=[libplacebo=apply_dolbyvision=1:colorspace=bt709:color_primaries=bt709:color_trc=iec61966-2-1:range=pc:format=rgba]"},
        {"target-prim", "bt.709"}, {"target-trc", "srgb"}, {"target-peak", "100"}};
    int code = 0;
    const double maximumUiVolume = std::max(1., var_InheritInteger(intf, "qt-max-volume") / 100.);
    const auto maximumVolume = QByteArray::number(100. * maximumUiVolume * maximumUiVolume * maximumUiVolume);
    code = d->api->set_option_string(d->player, "volume-max", maximumVolume.constData());
    if (code < 0) d->error = tr("MPV could not apply the configured volume limit.");
    // Reuse mmdevice's existing persisted Windows session, or its nonpersistent
    // default session when volume-save is disabled. No second settings owner.
    const char *session = var_InheritBool(intf, "volume-save")
        ? "{4533f59d-59ee-00c6-adb2-c68b501a6655}" : "";
    if (code >= 0) code = d->api->set_option_string(d->player, "wasapi-session-id", session);
    if (code < 0 && d->error.isEmpty()) d->error = tr("MPV could not join the player's Windows audio session.");
    if (code >= 0) {
        // A previously selected native endpoint and the volume owner must refer
        // to the same device. An empty id retains default eConsole routing.
        auto *audio = vlc_player_aout_Hold(intf->p_player);
        if (audio) {
            auto *device = aout_DeviceGet(audio);
            if (device && *device) {
                const QByteArray selected = QByteArrayLiteral("wasapi/") + device;
                code = d->api->set_option_string(d->player, "audio-device", selected.constData());
                if (code < 0) d->error = tr("MPV could not select the player's Windows audio device.");
            }
            free(device);
            aout_Release(audio);
        }
    }
    for (const auto &[name, value] : options) {
        if (code < 0) break;
        code = d->api->set_option_string(d->player, name, value);
        if (code < 0) { d->error = tr("MPV initialization option %1 failed: %2").arg(QString::fromUtf8(name), QString::fromUtf8(d->api->error_string(code))); break; }
    }
    if (code >= 0) code = d->api->request_log_messages(d->player,
#ifdef VLC_PLAYER_DIAGNOSTICS
        "v"
#else
        "warn"
#endif
    );
    if (code >= 0) code = d->api->initialize(d->player);
    if (code < 0) {
        if (d->error.isEmpty()) d->error = QString::fromUtf8(d->api->error_string(code));
        d->api->terminate_destroy(d->player); d->player = nullptr; return;
    }
    const char *properties[] = {"pause", "idle-active", "time-pos", "duration", "speed", "volume", "mute",
        "track-list", "metadata", "video-params", "video-out-params", "seekable", "audio-delay", "sub-delay", "secondary-sub-delay",
        "sid", "aid", "vid", "secondary-sid", "chapter-list", "chapter", "media-title", "path", "paused-for-cache",
        "vf", "hwdec-current", "current-ao", "audio-params", "audio-out-params"};
    for (const auto name : properties) d->api->observe_property(d->player, 0, name, MPV_FORMAT_NODE);
    d->events = std::make_unique<Events>(d->api, d->player, this, [this](const Event &event) { d->receive(event); });
    connect(d->events.get(), &QThread::finished, this, [this] {
        if (!d->closing) {
            emit ended(false, tr("The native MPV player stopped unexpectedly."));
            prepareToClose([] {});
            return;
        }
#ifdef _WIN32
        if (d->surface) return; // Render teardown still owns the player handle.
#endif
        d->complete();
    });
    // Startup failure before Qt's event loop begins must not leave an event
    // reader that depends on that never-started loop for its completion.
    QMetaObject::invokeMethod(this, [this] {
        if (!d->closing) d->events->start();
    }, Qt::QueuedConnection);
}

MpvPlayback::~MpvPlayback()
{
    // prepareToClose must finish while the UI can service window callbacks.
    // Before the event loop has ever run, no render surface exists and the
    // native core can be destroyed directly on the constructor's owner thread.
    if (d->player && d->events && !d->events->isRunning()) {
#ifdef _WIN32
        assert(!d->surface);
#endif
        d->api->terminate_destroy(d->player); d->player = nullptr;
    }
    assert(!d->player);
    assert(!d->events || !d->events->isRunning());
}
bool MpvPlayback::isAvailable() const { return d->player && d->error.isEmpty() && !d->closing; }
bool MpvPlayback::isMediaLoaded() const { return isAvailable() && d->loaded; }
QString MpvPlayback::error() const { return d->error; }
QVariant MpvPlayback::value(const QString &name) const { return d->properties.value(name); }

void MpvPlayback::requestAudioSessionState()
{
    // Read-only evidence for the owned native test bridge. The actual session
    // is queried asynchronously; the GUI must never wait on MPV's core thread.
    if (!isAvailable() || d->closing) {
        d->deliverProperty(QStringLiteral("audio-session-query-error"), MPV_ERROR_UNINITIALIZED);
        return;
    }
    for (const auto &pending : d->requests)
        if (pending == QStringLiteral("ao-volume") || pending == QStringLiteral("ao-mute")) return;
    d->properties.remove(QStringLiteral("ao-volume"));
    d->properties.remove(QStringLiteral("ao-mute"));
    d->properties[QStringLiteral("audio-session-query-error")] = 0;
    for (const auto *name : {"ao-volume", "ao-mute"}) {
        const auto request = d->nextRequest++;
        const int code = d->api->get_property_async(d->player, request, name, MPV_FORMAT_NODE);
        if (code < 0) {
            d->deliverProperty(QStringLiteral("audio-session-query-error"), code);
            return;
        }
        d->requests[request] = QString::fromLatin1(name);
    }
}

void MpvPlayback::command(const QStringList &command)
{
    if (!isAvailable()) { emit failed(d->error); return; }
    if (command.value(0) == QStringLiteral("stop")) {
        d->stopping = true; d->fileQueries.clear(); d->loaded = false;
        const bool pendingOnly = !d->ready && !d->pending.isEmpty();
        d->pending.clear(); d->replacing = false;
        if (pendingOnly) emit ended(false, {});
    }
    std::vector<QByteArray> values;
    for (const auto &value : command) values.push_back(value.toUtf8());
    std::vector<const char *> args;
    for (const auto &value : values) args.push_back(value.constData());
    args.push_back(nullptr);
    const auto request = d->nextRequest++;
    const int code = d->api->command_async(d->player, request, args.data());
    if (code < 0) emit failed(QString::fromUtf8(d->api->error_string(code)));
    else d->requests[request] = command.value(0);
}
void MpvPlayback::set(const QString &name, const QVariant &value)
{
    if (!isAvailable()) { emit failed(d->error); return; }
    mpv_node node{};
    QByteArray string;
    if (value.metaType().id() == QMetaType::Bool) { node.format = MPV_FORMAT_FLAG; node.u.flag = value.toBool(); }
    else if (value.metaType().id() == QMetaType::QString) { string = value.toString().toUtf8(); node.format = MPV_FORMAT_STRING; node.u.string = string.data(); }
    else if (value.metaType().id() == QMetaType::Int || value.metaType().id() == QMetaType::LongLong) {
        node.format = MPV_FORMAT_INT64; node.u.int64 = value.toLongLong();
    }
    else { node.format = MPV_FORMAT_DOUBLE; node.u.double_ = value.toDouble(); }
    const auto request = d->nextRequest++;
    const int code = d->api->set_property_async(d->player, request, name.toUtf8().constData(), MPV_FORMAT_NODE, &node);
    if (code < 0) emit failed(QString::fromUtf8(d->api->error_string(code)));
    else d->requests[request] = name;
}
void MpvPlayback::load(const QUrl &url, bool paused)
{
    if (!isAvailable()) { emit failed(d->error); return; }
    d->loaded = false;
    d->stopping = false; d->fileQueries.clear();
    for (const auto *name : {"time-pos", "duration", "track-list", "metadata", "media-title", "path", "video-params", "video-out-params", "chapter-list", "chapter", "seekable"})
        d->properties.remove(QString::fromUtf8(name));
    d->pending = url; d->pendingPaused = paused;
#ifdef _WIN32
    if (!d->surface) {
        d->surface = new Surface(d->api, d->player, d->intf, this, [this](const QString &error) {
            if (!error.isEmpty()) { d->error = error; emit ended(false, error); return; }
            d->ready = true; emit surfaceReady();
            if (!d->pending.isEmpty()) load(d->pending, d->pendingPaused);
        });
        d->surface->moveToThread(&d->renderThread);
        connect(&d->renderThread, &QThread::started, d->surface, [this] { d->surface->initialize(); });
        connect(&d->renderThread, &QThread::finished, d->surface, &QObject::deleteLater);
        d->renderThread.start();
    }
#endif
    if (!d->ready || d->loadStarting) return;
    d->prepareLanguages();
    d->replacing = true;
    d->loadStarting = true;
    set(QStringLiteral("pause"), paused);
    const QString input = url.isLocalFile() ? QDir::toNativeSeparators(url.toLocalFile()) : url.toString(QUrl::FullyEncoded);
    command({QStringLiteral("loadfile"), input, QStringLiteral("replace")});
    d->pending.clear();
}
void MpvPlayback::prepareToClose(std::function<void()> completion)
{
    if (d->completed) {
        QMetaObject::invokeMethod(this, [completion=std::move(completion)] { completion(); }, Qt::QueuedConnection);
        return;
    }
    d->completions.push_back(std::move(completion));
    if (d->closing) return;
    d->closing = true;
    d->loaded = false;
#ifdef _WIN32
    if (d->surface) {
        connect(&d->renderThread, &QThread::finished, this, [this] {
            // Surface::close has completed every UI-dependent window callback.
            // Join only after finished, before deleting the QThread owner.
            d->renderThread.wait();
            d->surface = nullptr; d->finishCore();
        });
        QMetaObject::invokeMethod(d->surface, [this] { d->surface->close(); d->renderThread.quit(); }, Qt::QueuedConnection);
        return;
    }
#endif
    if (d->player) d->finishCore();
    else QMetaObject::invokeMethod(this, [this] { d->complete(); }, Qt::QueuedConnection);
}
