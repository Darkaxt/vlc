// SPDX-License-Identifier: GPL-2.0-or-later
// Explicitly compiled test instrumentation. No listener, input injection into
// Windows, activation request, arbitrary evaluation or backend setters.
#ifndef VLC_PLAYER_DIAGNOSTICS_HPP
#define VLC_PLAYER_DIAGNOSTICS_HPP
#ifdef VLC_PLAYER_DIAGNOSTICS
#include <QAccessible>
#include <QApplication>
#include <QDir>
#include <QElapsedTimer>
#include <QFile>
#include <QFileSystemWatcher>
#include <QJsonArray>
#include <QJsonDocument>
#include <QJsonObject>
#include <QKeyEvent>
#include <QMouseEvent>
#include <QWheelEvent>
#include <QMenu>
#include <QMap>
#include <QMimeData>
#include <QDragEnterEvent>
#include <QDragMoveEvent>
#include <QDragLeaveEvent>
#include <QDropEvent>
#include <QWidget>
#ifdef QT_GUI_PRIVATE
#include <qpa/qwindowsysteminterface.h>
#include <QtGui/private/qhighdpiscaling_p.h>
#endif
#include <QPointer>
#include <QPixmap>
#include <QQuickItemGrabResult>
#include <QQuickWindow>
#include <QQmlContext>
#include <QQmlEngine>
#include <QQmlExpression>
#include <QRegularExpression>
#include <QSaveFile>
#include <QSet>
#include <QScreen>
#include <memory>
#include <cmath>
#include <utility>
#include "util/accessible_compat_attached.hpp"
#include "player/player_controller.hpp"
#include "player/player_media_tools.hpp"
#include "player/player_media_analysis.hpp"

class PlayerDiagnostics final : public QObject
{
public:
    static void attach(QQuickItem *root, QQmlEngine *engine, PlayerController *player)
    {
        const QString directory = qEnvironmentVariable("VLC_PLAYER_DIAGNOSTICS_DIR");
        const QString token = qEnvironmentVariable("VLC_PLAYER_DIAGNOSTICS_TOKEN");
        if (root && QDir::isAbsolutePath(directory) && QDir(directory).exists() && token.size() >= 32)
            new PlayerDiagnostics(root, engine, player, directory, token);
    }

private:
    QQuickItem *m_root;
    QPointer<PlayerController> m_player;
    QString m_directory, m_token, m_pendingId;
    QSet<QString> m_received;
    QPointer<QQmlExpression> m_waitExpression;
    QFileSystemWatcher m_watcher;
    QElapsedTimer m_clock;
    QJsonArray m_errors;
    QJsonArray m_pointerTrace;
    QList<QPointer<QQuickItem>> m_items;
    QList<QPointer<QWidget>> m_widgets;
    quint64 m_revision = 0;
    bool m_busy = false;

    PlayerDiagnostics(QQuickItem *root, QQmlEngine *engine, PlayerController *player, const QString &directory, const QString &token)
        : QObject(root), m_root(root), m_player(player), m_directory(directory), m_token(token)
    {
        m_clock.start();
        connect(engine, &QQmlEngine::warnings, this, [this](const QList<QQmlError> &errors) {
            for (const auto &error : errors)
                if (m_errors.size() < 100) m_errors.append(error.toString());
        });
        // Changes are file-system events, not a polling/timer synchronization loop.
        m_watcher.addPath(directory);
        connect(&m_watcher, &QFileSystemWatcher::directoryChanged, this, [this] { receive(); });
        QMetaObject::invokeMethod(this, [this] { receive(); }, Qt::QueuedConnection);
    }

    void write(const QString &name, const QJsonObject &value)
    {
        QSaveFile file(QDir(m_directory).filePath(name));
        if (file.open(QIODevice::WriteOnly)) {
            file.write(QJsonDocument(value).toJson());
            file.commit();
        }
    }

    void respond(const QString &id, const QJsonObject &value)
    {
        // Close the payload's final Windows handle before exposing completion.
        // A directory notification for rename may precede that close.
        write(id + QStringLiteral(".json"), value);
        write(id + QStringLiteral(".ready"), {{QStringLiteral("id"), id}});
        if (id == m_pendingId) {
            if (m_waitExpression) m_waitExpression->deleteLater();
            m_waitExpression = nullptr;
            m_pendingId.clear();
            m_busy = false;
        }
    }

    QString stableId(QQuickItem *item) const
    {
        const auto attached = qobject_cast<AccessibleCompatAttached *>(
            qmlAttachedPropertiesObject<AccessibleCompatAttached>(item, false));
        if (attached && !attached->getId().isEmpty()) return attached->getId();
        if (!item->objectName().isEmpty()) return item->objectName();
        const auto context = qmlContext(item);
        return context ? context->nameForObject(item) : QString();
    }

    void visit(QQuickItem *item, int parent, QJsonArray &tree, QJsonObject &images)
    {
        if (m_items.size() >= 8000) return;
        const int index = m_items.size();
        m_items.append(item);
        const QRectF rect = item->mapRectToScene(QRectF(0, 0, item->width(), item->height()));
        QJsonObject node{{QStringLiteral("node"), index}, {QStringLiteral("parent"), parent},
            {QStringLiteral("id"), stableId(item)},
            {QStringLiteral("type"), QString::fromLatin1(item->metaObject()->className())},
            {QStringLiteral("x"), rect.x()}, {QStringLiteral("y"), rect.y()},
            {QStringLiteral("width"), rect.width()}, {QStringLiteral("height"), rect.height()},
            {QStringLiteral("visible"), item->isVisible()}, {QStringLiteral("enabled"), item->isEnabled()},
            {QStringLiteral("opacity"), item->opacity()}, {QStringLiteral("z"), item->z()},
            {QStringLiteral("focused"), item->hasActiveFocus()}};
        const bool secret = item->metaObject()->indexOfProperty("echoMode") >= 0 && item->property("echoMode").toInt() != 0;
        for (const char *property : {"index", "text", "checked", "selected", "isCurrent", "url", "value", "from", "to", "pressed", "hovered", "font", "color", "source", "status", "contentY", "contentHeight", "moving", "count", "currentIndex", "currentText", "highlightedIndex", "live", "position"}) {
            if (secret && (qstrcmp(property, "text") == 0 || qstrcmp(property, "value") == 0)) { node.insert(QString::fromLatin1(property), QStringLiteral("[redacted]")); continue; }
            const QVariant value = item->property(property);
            if (value.isValid()) node.insert(QString::fromLatin1(property), QJsonValue::fromVariant(value));
        }
        if (auto accessible = QAccessible::queryAccessibleInterface(item)) {
            node.insert(QStringLiteral("name"), accessible->text(QAccessible::Name));
            node.insert(QStringLiteral("role"), int(accessible->role()));
            if (auto actions = accessible->actionInterface())
                node.insert(QStringLiteral("actions"), QJsonArray::fromStringList(actions->actionNames()));
        }
        const QUrl source = item->property("source").toUrl();
        if (source.isValid() && !source.isEmpty() && item->metaObject()->indexOfProperty("sourceSize") >= 0
            && item->metaObject()->indexOfProperty("status") >= 0) {
            const int status = item->property("status").toInt();
            const QString key = status == 1 ? QStringLiteral("resolved") : status == 2 ? QStringLiteral("pending") : status == 3 ? QStringLiteral("failed") : QStringLiteral("unresolved");
            images[key] = images.value(key).toInt() + 1;
        }
        tree.append(node);
        for (auto child : item->childItems()) visit(child, index, tree, images);
    }

    QJsonObject coreSnapshot() const
    {
        if (!m_player) return {};
        auto player = m_player->getPlayer();
        vlc_player_locker lock{player};
        QJsonObject core{{QStringLiteral("state"), int(vlc_player_GetState(player))},
            {QStringLiteral("position"), vlc_player_GetPosition(player)},
            {QStringLiteral("seekable"), vlc_player_CanSeek(player)}};
        for (const auto &entry : {std::pair{"time_seconds", vlc_player_GetTime(player)},
                                  std::pair{"length_seconds", vlc_player_GetLength(player)}})
            core.insert(QString::fromLatin1(entry.first), entry.second == VLC_TICK_INVALID
                ? QJsonValue(QJsonValue::Null) : QJsonValue(double(entry.second) / CLOCK_FREQ));
        core[QStringLiteral("rate")] = vlc_player_GetRate(player);
        core[QStringLiteral("audio_delay_ms")] = double(vlc_player_GetCategoryDelay(player, AUDIO_ES)) / 1000.;
        core[QStringLiteral("subtitle_delay_ms")] = double(vlc_player_GetCategoryDelay(player, SPU_ES)) / 1000.;
        core[QStringLiteral("subtitle_fps")] = vlc_player_GetAssociatedSubsFPS(player);
        core[QStringLiteral("reverse_supported")] = vlc_player_CanRewind(player);
        for (const auto cat : {VIDEO_ES, AUDIO_ES, SPU_ES}) {
            QJsonArray tracks;
            for (size_t i = 0; i < vlc_player_GetTrackCount(player, cat); ++i) {
                const auto *track = vlc_player_GetTrackAt(player, cat, i);
                tracks.append(QJsonObject{{QStringLiteral("id"), QString::fromUtf8(vlc_es_id_GetStrId(track->es_id))},
                    {QStringLiteral("name"), QString::fromUtf8(track->name ? track->name : "")},
                    {QStringLiteral("language"), QString::fromUtf8(track->fmt.psz_language ? track->fmt.psz_language : "")},
                    {QStringLiteral("selected"), track->selected}});
            }
            core[cat == VIDEO_ES ? QStringLiteral("video_tracks") : cat == AUDIO_ES ? QStringLiteral("audio_tracks") : QStringLiteral("subtitle_tracks")] = tracks;
        }
        auto media = vlc_player_GetCurrentMedia(player);
        auto uri = media ? vlc::wrap_cptr(input_item_GetURI(media)) : vlc::wrap_cptr<char>(nullptr);
        core.insert(QStringLiteral("url"), uri ? QUrl(QString::fromUtf8(uri.get())).toString(QUrl::FullyEncoded) : QString());
        return core;
    }

    QVariant observationValue(const QJsonObject &command)
    {
        // Evaluate even for core observations, to subscribe to the matching
        // controller's real notify signal. The value itself is read under
        // VLC's player lock, rather than from the UI's interpolated seek timer.
        const QVariant ui = m_waitExpression ? m_waitExpression->evaluate() : QVariant();
        const QString property = command.value(QStringLiteral("await_core")).toString();
        return property.isEmpty() ? ui : coreSnapshot().value(property).toVariant();
    }

    static bool observationMatches(const QVariant &actual, const QJsonObject &command)
    {
        if (!actual.isValid() || actual.isNull()) return false;
        const QVariant expected = command.value(QStringLiteral("await_value")).toVariant();
        const QString comparison = command.value(QStringLiteral("await_comparison")).toString(QStringLiteral("equal"));
        bool actualNumber = false, expectedNumber = false;
        const double a = actual.toDouble(&actualNumber), e = expected.toDouble(&expectedNumber);
        if (comparison == QStringLiteral("at_least")) return actualNumber && expectedNumber && a >= e;
        if (comparison == QStringLiteral("at_most")) return actualNumber && expectedNumber && a <= e;
        const double tolerance = command.value(QStringLiteral("await_tolerance")).toDouble();
        return actual == expected || (tolerance > 0 && actualNumber && expectedNumber && std::abs(a - e) <= tolerance);
    }

    QJsonObject snapshot()
    {
        m_items.clear();
        QJsonArray tree;
        QJsonObject images{{QStringLiteral("resolved"), 0}, {QStringLiteral("pending"), 0},
                          {QStringLiteral("failed"), 0}, {QStringLiteral("unresolved"), 0}};
        auto window = m_root->window();
        visit(window ? window->contentItem() : m_root, -1, tree, images);
        QJsonObject result{{QStringLiteral("revision"), qint64(++m_revision)},
            {QStringLiteral("core"), coreSnapshot()},
            {QStringLiteral("pointer_trace"), m_pointerTrace},
            {QStringLiteral("seek_requests"), m_player ? QJsonArray::fromVariantList(m_player->property("redesignSeekRequests").toList()) : QJsonArray()},
            {QStringLiteral("video_backdrop"), QJsonValue::fromVariant(m_root->window()->property("playerVideoBackdropState"))},
            {QStringLiteral("pid"), QCoreApplication::applicationPid()},
            {QStringLiteral("qt"), QString::fromLatin1(qVersion())},
            {QStringLiteral("build"), qEnvironmentVariable("VLC_PLAYER_DIAGNOSTICS_BUILD")},
            {QStringLiteral("elapsed_ms"), m_clock.elapsed()}, {QStringLiteral("units"), QStringLiteral("Qt logical pixels")},
            {QStringLiteral("tree"), tree}, {QStringLiteral("images"), images},
            {QStringLiteral("qml_errors"), m_errors}, {QStringLiteral("truncated"), m_items.size() >= 8000},
            {QStringLiteral("coverage"), QStringLiteral("Instantiated Qt Quick items; native menus/video surfaces are separate. Capture is app-rendered UI, not desktop presentation.")}};
        if (m_player) {
            QJsonObject services;
            for (const auto &entry : {std::pair{"redesignMediaTools", QStringList{QStringLiteral("status"), QStringLiteral("matches"), QStringLiteral("cues"), QStringLiteral("timelineStatus"), QStringLiteral("subtitleLoaded"), QStringLiteral("subtitleTimeScale"), QStringLiteral("subtitleFPSSupported"), QStringLiteral("statisticsVisible"), QStringLiteral("statisticsText"), QStringLiteral("presets"), QStringLiteral("activePreset"), QStringLiteral("timelineVisible"), QStringLiteral("waveformVisible"), QStringLiteral("sleepMinutes"), QStringLiteral("sleepStatus"), QStringLiteral("videoInfo")}},
                    std::pair{"redesignMediaAnalysis", QStringList{QStringLiteral("previewSource"), QStringLiteral("previewStatus"), QStringLiteral("previewPosition"), QStringLiteral("waveform"), QStringLiteral("waveformStatus"), QStringLiteral("waveformBusy")}},
                    std::pair{"redesignSubtitleSearch", QStringList{QStringLiteral("provider"), QStringLiteral("configured"), QStringLiteral("busy"), QStringLiteral("status"), QStringLiteral("results"), QStringLiteral("archiveFiles")}}}) {
                if (const auto service = m_player->findChild<QObject *>(QString::fromLatin1(entry.first))) {
                    QJsonObject values;
                    for (const auto &property : entry.second) values[property] = QJsonValue::fromVariant(service->property(property.toUtf8().constData()));
                    services[QString::fromLatin1(entry.first)] = values;
                }
            }
            if (const auto tools = m_player->findChild<PlayerMediaTools *>(QStringLiteral("redesignMediaTools"))) {
                QJsonObject options, filters;
                for (const auto section : {"subtitle", "subtitleTiming", "equalizer", "compressor", "spatializer", "stereo_widen", "pitch", "essential", "crop", "colors", "geometry"})
                    for (const auto &option : tools->options(QString::fromLatin1(section))) {
                        const auto row = option.toMap(); const auto key = row.value(QStringLiteral("key")).toString();
                        options[key] = QJsonValue::fromVariant(tools->value(key));
                        const auto module = row.value(QStringLiteral("module")).toString();
                        if (!module.isEmpty()) filters[module] = tools->filterEnabled(module);
                    }
                filters[QStringLiteral("invert")] = tools->filterEnabled(QStringLiteral("invert"));
                services[QStringLiteral("track_languages")] = QJsonObject{
                    {QStringLiteral("audio"), QJsonArray::fromVariantList(tools->trackLanguages(false))},
                    {QStringLiteral("subtitles"), QJsonArray::fromVariantList(tools->trackLanguages(true))},
                    {QStringLiteral("selected_audio"), tools->selectedLanguage(false)},
                    {QStringLiteral("selected_subtitle"), tools->selectedLanguage(true)}};
                services[QStringLiteral("options")] = options; services[QStringLiteral("filters")] = filters;
            }
            result.insert(QStringLiteral("media_tools"), services);
        }
        if (window) {
            result.insert(QStringLiteral("window"), QJsonObject{{QStringLiteral("width"), window->width()},
                {QStringLiteral("x"), window->x()}, {QStringLiteral("y"), window->y()},
                {QStringLiteral("native_id_hex"), QString::number(qulonglong(window->winId()), 16)},
                {QStringLiteral("height"), window->height()}, {QStringLiteral("dpr"), window->devicePixelRatio()},
                {QStringLiteral("minimum_width"), window->minimumWidth()}, {QStringLiteral("minimum_height"), window->minimumHeight()},
                {QStringLiteral("visible"), window->isVisible()}, {QStringLiteral("active"), window->isActive()},
                {QStringLiteral("flags"), QString::number(quint64(window->flags()), 16)},
                {QStringLiteral("visibility"), int(window->visibility())}});
        }
        QJsonArray windows;
        for (auto candidate : QGuiApplication::allWindows()) {
            if (windows.size() >= 100) break;
            QJsonArray texts;
            if (auto quick = qobject_cast<QQuickWindow *>(candidate))
                for (auto item : quick->contentItem()->findChildren<QQuickItem *>()) {
                    if (item->metaObject()->indexOfProperty("echoMode") >= 0 && item->property("echoMode").toInt() != 0) continue;
                    const auto text = item->property("text").toString();
                    if (item->isVisible() && !text.isEmpty() && texts.size() < 20) texts.append(text.left(512));
                }
            windows.append(QJsonObject{{QStringLiteral("type"), QString::fromLatin1(candidate->metaObject()->className())},
                {QStringLiteral("window_type"), int(candidate->type())}, {QStringLiteral("visible"), candidate->isVisible()},
                {QStringLiteral("active"), candidate->isActive()}, {QStringLiteral("width"), candidate->width()},
                {QStringLiteral("height"), candidate->height()}, {QStringLiteral("main"), candidate == window},
                {QStringLiteral("visible_text"), texts}});
        }
        result.insert(QStringLiteral("windows"), windows);
        m_widgets.clear();
        QJsonArray widgets;
        const auto visitWidget = [this, &widgets](auto &&self, QWidget *widget, int parent) -> void {
            if (!widget->isVisible() || m_widgets.size() >= 2000) return;
            const int index = m_widgets.size();
            m_widgets.append(widget);
            QJsonObject row{{QStringLiteral("node"), index}, {QStringLiteral("parent"), parent},
                {QStringLiteral("id"), widget->objectName()}, {QStringLiteral("type"), QString::fromLatin1(widget->metaObject()->className())},
                {QStringLiteral("width"), widget->width()}, {QStringLiteral("height"), widget->height()},
                {QStringLiteral("enabled"), widget->isEnabled()}, {QStringLiteral("focused"), widget->hasFocus()}};
            if (auto accessible = QAccessible::queryAccessibleInterface(widget)) row.insert(QStringLiteral("name"), accessible->text(QAccessible::Name));
            if (widget->property("text").isValid()) row.insert(QStringLiteral("text"),
                widget->metaObject()->indexOfProperty("echoMode") >= 0 && widget->property("echoMode").toInt() != 0
                    ? QStringLiteral("[redacted]") : widget->property("text").toString());
            if (auto menu = qobject_cast<QMenu *>(widget)) {
                QJsonArray actions;
                for (auto action : menu->actions()) {
                    const QRect rect = menu->actionGeometry(action);
                    actions.append(QJsonObject{{QStringLiteral("text"), action->text()}, {QStringLiteral("enabled"), action->isEnabled()},
                        {QStringLiteral("checked"), action->isChecked()}, {QStringLiteral("x"), rect.x()}, {QStringLiteral("y"), rect.y()},
                        {QStringLiteral("width"), rect.width()}, {QStringLiteral("height"), rect.height()}});
                }
                row.insert(QStringLiteral("actions"), actions);
            }
            widgets.append(row);
            for (auto child : widget->findChildren<QWidget *>(QString(), Qt::FindDirectChildrenOnly)) self(self, child, index);
        };
        for (auto widget : QApplication::topLevelWidgets()) if (widget->isWindow()) visitWidget(visitWidget, widget, -1);
        result.insert(QStringLiteral("widgets"), widgets);
        QStringList missing;
        for (const auto &required : {QStringLiteral("playButton"), QStringLiteral("progressSlider"), QStringLiteral("muteButton"), QStringLiteral("volumeSlider"), QStringLiteral("subtitleButton"), QStringLiteral("audioButton"), QStringLiteral("playqueueToggle")}) {
            bool found = false;
            for (auto item : m_items) if (item && stableId(item) == required && item->width() > 0 && item->height() > 0) { found = true; break; }
            if (!found) missing.append(required);
        }
        result.insert(QStringLiteral("player_ready"), missing.isEmpty() && m_errors.isEmpty() && images.value(QStringLiteral("pending")).toInt() == 0 && images.value(QStringLiteral("failed")).toInt() == 0);
        result.insert(QStringLiteral("missing_required_items"), QJsonArray::fromStringList(missing));
        return result;
    }

    void tracePointer(const QPointer<QQuickItem> &item, QEvent::Type type, const QPointF &point)
    {
        if (!item) return;
        if (m_pointerTrace.size() >= 16) m_pointerTrace.removeFirst();
        m_pointerTrace.append(QJsonObject{{QStringLiteral("event_type"), int(type)},
            {QStringLiteral("x"), point.x()}, {QStringLiteral("y"), point.y()},
            {QStringLiteral("pressed"), item->property("pressed").toBool()},
            {QStringLiteral("value"), QJsonValue::fromVariant(item->property("value"))}});
    }

    void mouse(QQuickWindow *window, QEvent::Type type, const QPointF &point, Qt::MouseButton button, Qt::MouseButtons buttons, QPointer<QQuickItem> traceItem = {})
    {
        // QPA constructs each QMouseEvent at delivery, after the preceding
        // event updated its device's persistent point/grabber state. Creating
        // a whole press/release sequence before posting loses that state.
#ifdef QT_GUI_PRIVATE
        QMetaObject::invokeMethod(window, [this, window, type, point, button, buttons, traceItem] {
            if (!window->isActive())
                QWindowSystemInterface::handleFocusWindowChanged<QWindowSystemInterface::SynchronousDelivery>(window, Qt::OtherFocusReason);
            QWindowSystemInterface::handleMouseEvent<QWindowSystemInterface::SynchronousDelivery>(
                window, ulong(m_clock.elapsed()), QHighDpi::toNativeLocalPosition(point, window),
                QHighDpi::toNativeGlobalPosition(window->mapToGlobal(point), window), buttons, button, type);
            tracePointer(traceItem, type, point);
        }, Qt::QueuedConnection);
#else
        QMetaObject::invokeMethod(window, [this, window, type, point, button, buttons, traceItem] {
            QMouseEvent event(type, point, point, window->mapToGlobal(point), button, buttons, Qt::NoModifier);
            event.setTimestamp(ulong(m_clock.elapsed()));
            QCoreApplication::sendEvent(window, &event);
            tracePointer(traceItem, type, point);
        }, Qt::QueuedConnection);
#endif
    }

    void receive()
    {
        const auto requests = QDir(m_directory).entryList({QStringLiteral("request-*.json")}, QDir::Files, QDir::Name);
        for (const auto &name : requests)
            if (!m_received.contains(name)) receiveRequest(name);
    }

    void receiveRequest(const QString &name)
    {
        QFile input(QDir(m_directory).filePath(name));
        if (!input.open(QIODevice::ReadOnly) || input.size() > 16384) return;
        const auto command = QJsonDocument::fromJson(input.readAll()).object();
        input.close(); // Never retain a Windows input handle across UI actions.
        m_received.insert(name);
        const QString id = command.value(QStringLiteral("id")).toString();
        if (!QRegularExpression(QStringLiteral("^[a-zA-Z0-9-]{1,64}$")).match(id).hasMatch()
            || name != QStringLiteral("request-%1.json").arg(id)
            || command.value(QStringLiteral("token")).toString() != m_token) return;
        const QString op = command.value(QStringLiteral("op")).toString();
        if (qEnvironmentVariableIntValue("VLC_PLAYER_DIAGNOSTICS_OFFSCREEN") == 1
            && op != QStringLiteral("snapshot") && op != QStringLiteral("resize")
            && op != QStringLiteral("cancel") && op != QStringLiteral("quit")) {
            respond(id, {{QStringLiteral("id"), id}, {QStringLiteral("status"), QStringLiteral("failed")},
                {QStringLiteral("error"), QStringLiteral("offscreen_session_is_capture_only")}});
            return;
        }
        if (m_busy && op != QStringLiteral("quit") && op != QStringLiteral("cancel")) {
            if (op == QStringLiteral("snapshot") && !command.value(QStringLiteral("capture")).toBool()
                && !command.contains(QStringLiteral("await_property")) && !command.contains(QStringLiteral("await_core"))) {
                auto state = snapshot();
                state.insert(QStringLiteral("id"), id);
                state.insert(QStringLiteral("status"), QStringLiteral("completed"));
                state.insert(QStringLiteral("observation_boundary"), QStringLiteral("UI dispatcher during pending observation; no new frame awaited"));
                respond(id, state);
                return;
            }
            respond(id, {{QStringLiteral("id"), id}, {QStringLiteral("status"), QStringLiteral("failed")},
                {QStringLiteral("error"), QStringLiteral("observation_in_progress")}});
            return;
        }
        if (op == QStringLiteral("quit") || op == QStringLiteral("cancel")) {
            if (m_waitExpression) { m_waitExpression->deleteLater(); m_waitExpression = nullptr; }
            if (m_busy)
                respond(m_pendingId, {{QStringLiteral("id"), m_pendingId}, {QStringLiteral("status"), QStringLiteral("failed")},
                    {QStringLiteral("error"), QStringLiteral("observation_cancelled_action_not_undone")}});
            m_pendingId = id;
            respond(id, {{QStringLiteral("id"), id}, {QStringLiteral("status"), QStringLiteral("accepted")}});
            // Use the normal window-close path. Quitting QApplication directly
            // can tear down Qt before VLC has finished stopping its inputs.
            if (op == QStringLiteral("quit") && m_root->window()) m_root->window()->close();
            return;
        }
        m_pendingId = id;
        m_busy = true;
        auto window = m_root->window();
        QString error;
        const qint64 before = m_revision;
        QString awaitProperty = command.value(QStringLiteral("await_property")).toString();
        const QString awaitCore = command.value(QStringLiteral("await_core")).toString();
        QPointer<QObject> observed;
        if (!awaitCore.isEmpty()) {
            const QMap<QString, QString> properties{{QStringLiteral("state"), QStringLiteral("playingState")},
                {QStringLiteral("position"), QStringLiteral("position")}, {QStringLiteral("time_seconds"), QStringLiteral("position")},
                {QStringLiteral("length_seconds"), QStringLiteral("length")}, {QStringLiteral("url"), QStringLiteral("url")},
                {QStringLiteral("seekable"), QStringLiteral("seekable")}};
            if (!m_player || !properties.contains(awaitCore)) error = QStringLiteral("invalid_core_observation");
            else { observed = m_player; awaitProperty = properties.value(awaitCore); }
        }
        else if (!command.value(QStringLiteral("await_service")).toString().isEmpty()) {
            const QString name = command.value(QStringLiteral("await_service")).toString();
            const QMap<QString, QStringList> allowed{
                {QStringLiteral("redesignMediaTools"), {QStringLiteral("subtitleLoaded"), QStringLiteral("sleepMinutes"), QStringLiteral("sleepStatus"), QStringLiteral("status")}},
                {QStringLiteral("redesignMediaAnalysis"), {QStringLiteral("waveformBusy"), QStringLiteral("previewSource"), QStringLiteral("previewStatus"), QStringLiteral("waveformStatus")}},
                {QStringLiteral("redesignSubtitleSearch"), {QStringLiteral("busy"), QStringLiteral("status")}}};
            if (m_player && allowed.value(name).contains(awaitProperty))
                observed = m_player->findChild<QObject *>(name);
            if (!observed) error = QStringLiteral("invalid_service_observation_rejected_before_dispatch");
        }
        else if (!awaitProperty.isEmpty()) {
            const int index = command.value(QStringLiteral("await_node")).toInt(command.value(QStringLiteral("node")).toInt(-1));
            const QStringList allowed{QStringLiteral("selected"), QStringLiteral("description"), QStringLiteral("visible"),
                QStringLiteral("checked"), QStringLiteral("text"), QStringLiteral("value"), QStringLiteral("width"), QStringLiteral("height"), QStringLiteral("contentY"), QStringLiteral("moving")};
            if (!allowed.contains(awaitProperty) || index < 0 || index >= m_items.size() || !m_items[index]
                || m_items[index]->metaObject()->indexOfProperty(awaitProperty.toUtf8().constData()) < 0)
                error = QStringLiteral("invalid_observation_rejected_before_dispatch");
            else if (m_items[index]->metaObject()->indexOfProperty("echoMode") >= 0 && m_items[index]->property("echoMode").toInt() != 0)
                error = QStringLiteral("secret_observation_rejected_before_dispatch");
            else observed = m_items[index];
        }
        if (!error.isEmpty()) {}
        else if (op != QStringLiteral("snapshot")
            && command.value(QStringLiteral("revision")).toInteger() != qint64(m_revision))
            error = QStringLiteral("stale_revision_rejected_before_dispatch");
        else if (!window) error = QStringLiteral("window_not_created");
        else if (op == QStringLiteral("snapshot")) {}
        else if (op == QStringLiteral("focus")) {
            const int target = command.value(QStringLiteral("node")).toInt(-1);
            if (target < 0 || target >= m_items.size() || !m_items[target]
                || !m_items[target]->isVisible() || !m_items[target]->isEnabled())
                error = QStringLiteral("target_unavailable_rejected_before_dispatch");
            else {
                const auto accessible = QAccessible::queryAccessibleInterface(m_items[target]);
                const auto actions = accessible ? accessible->actionInterface() : nullptr;
                if (!actions || !actions->actionNames().contains(QAccessibleActionInterface::setFocusAction()))
                    error = QStringLiteral("focus_action_unavailable_rejected_before_dispatch");
                else actions->doAction(QAccessibleActionInterface::setFocusAction());
            }
        }
        else if (op == QStringLiteral("resize")) {
            const int width = command.value(QStringLiteral("width")).toInt();
            const int height = command.value(QStringLiteral("height")).toInt();
            if (width < window->minimumWidth() || width > 3840 || height < window->minimumHeight() || height > 2160) error = QStringLiteral("size_outside_current_window_constraints");
            else window->resize(width, height);
        } else if (op == QStringLiteral("click") || op == QStringLiteral("move") || op == QStringLiteral("drag") || op == QStringLiteral("scroll")) {
            const int target = command.value(QStringLiteral("node")).toInt(-1);
            if (target < 0 || target >= m_items.size() || !m_items[target]
                || !m_items[target]->isVisible() || !m_items[target]->isEnabled())
                error = QStringLiteral("target_unavailable_rejected_before_dispatch");
            else {
                auto item = m_items[target].data();
                QPointF point = item->mapToScene(QPointF(item->width() * command.value(QStringLiteral("fraction_x")).toDouble(0.5), item->height() * command.value(QStringLiteral("fraction_y")).toDouble(0.5)));
                QRectF available(0, 0, window->width(), window->height());
                for (auto ancestor = item->parentItem(); ancestor; ancestor = ancestor->parentItem())
                    if (ancestor->clip()) available = available.intersected(ancestor->mapRectToScene(ancestor->boundingRect()));
                if (!available.contains(point)) error = QStringLiteral("clipped_target_rejected_before_dispatch");
                m_pointerTrace = {};
                const QPointer<QQuickItem> tracedItem = item;
                if (error.isEmpty()) mouse(window, QEvent::MouseMove, point, Qt::NoButton, Qt::NoButton, tracedItem);
                if (error.isEmpty() && op == QStringLiteral("scroll")) {
                    const int delta = command.value(QStringLiteral("delta")).toInt();
                    auto wheel = new QWheelEvent(point, window->mapToGlobal(point), QPoint(), QPoint(0, delta), Qt::NoButton, Qt::NoModifier, Qt::NoScrollPhase, false);
                    // Match the QPA mouse clock. A zero timestamp makes
                    // Flickable fall back to its unrelated local timer and
                    // reject the wheel velocity after a timestamped press.
                    wheel->setTimestamp(ulong(m_clock.elapsed()));
                    QCoreApplication::postEvent(window, wheel);
                } else if (error.isEmpty() && op != QStringLiteral("move")) {
                    const auto button = command.value(QStringLiteral("button")).toString() == QStringLiteral("right") ? Qt::RightButton : Qt::LeftButton;
                    mouse(window, QEvent::MouseButtonPress, point, button, button, tracedItem);
                    if (op == QStringLiteral("drag")) {
                        const QPointF end(command.value(QStringLiteral("end_x")).toDouble(), command.value(QStringLiteral("end_y")).toDouble());
                        for (int step = 1; step <= 12; ++step)
                            mouse(window, QEvent::MouseMove, point + (end - point) * step / 12, Qt::NoButton, Qt::LeftButton, tracedItem);
                        point = end;
                    }
                    mouse(window, QEvent::MouseButtonRelease, point, button, Qt::NoButton, tracedItem);
                }
            }
        } else if (op == QStringLiteral("drop")) {
            const int target = command.value(QStringLiteral("node")).toInt(-1);
            if (target < 0 || target >= m_items.size() || !m_items[target]) error = QStringLiteral("invalid_drop_target");
            else {
                QMimeData mime;
                QList<QUrl> urls;
                for (const auto &url : command.value(QStringLiteral("urls")).toArray()) urls.append(QUrl(url.toString()));
                mime.setUrls(urls);
                const QPoint point = m_items[target]->mapToScene(m_items[target]->boundingRect().center()).toPoint();
                QDragEnterEvent enter(point, Qt::CopyAction, &mime, Qt::LeftButton, Qt::NoModifier);
                QCoreApplication::sendEvent(window, &enter);
                QDragMoveEvent move(point, Qt::CopyAction, &mime, Qt::LeftButton, Qt::NoModifier);
                QCoreApplication::sendEvent(window, &move);
                QDropEvent drop(point, Qt::CopyAction, &mime, Qt::LeftButton, Qt::NoModifier);
                QCoreApplication::sendEvent(window, &drop);
                if (!drop.isAccepted()) {
                    QDragLeaveEvent leave;
                    QCoreApplication::sendEvent(window, &leave);
                    error = QStringLiteral("drop_not_accepted_by_ui");
                }
            }
        } else if (op == QStringLiteral("widget_click") || op == QStringLiteral("widget_key")) {
            const int index = command.value(QStringLiteral("node")).toInt(-1);
            if (index < 0 || index >= m_widgets.size() || !m_widgets[index] || !m_widgets[index]->isEnabled()) error = QStringLiteral("invalid_widget_target");
            else {
                auto widget = m_widgets[index].data();
                if (op == QStringLiteral("widget_click")) {
                    QPointF point = widget->rect().center();
                    const int action = command.value(QStringLiteral("action")).toInt(-1);
                    if (action >= 0) {
                        auto menu = qobject_cast<QMenu *>(widget);
                        if (!menu || action >= menu->actions().size() || !menu->actions()[action]->isEnabled()) error = QStringLiteral("invalid_menu_action");
                        else point = menu->actionGeometry(menu->actions()[action]).center();
                    }
                    if (error.isEmpty()) {
                        QCoreApplication::postEvent(widget, new QMouseEvent(QEvent::MouseButtonPress, point, widget->mapToGlobal(point.toPoint()), Qt::LeftButton, Qt::LeftButton, Qt::NoModifier));
                        QCoreApplication::postEvent(widget, new QMouseEvent(QEvent::MouseButtonRelease, point, widget->mapToGlobal(point.toPoint()), Qt::LeftButton, Qt::NoButton, Qt::NoModifier));
                    }
                } else {
                    const int key = command.value(QStringLiteral("key")).toInt();
                    const auto modifiers = Qt::KeyboardModifiers(command.value(QStringLiteral("modifiers")).toInt());
                    QCoreApplication::postEvent(widget, new QKeyEvent(QEvent::KeyPress, key, modifiers, command.value(QStringLiteral("text")).toString()));
                    QCoreApplication::postEvent(widget, new QKeyEvent(QEvent::KeyRelease, key, modifiers));
                }
            }
        } else if (op == QStringLiteral("key")) {
            const int key = command.value(QStringLiteral("key")).toInt();
            const auto modifiers = Qt::KeyboardModifiers(command.value(QStringLiteral("modifiers")).toInt());
#ifdef QT_GUI_PRIVATE
            // Feed the framework's real shortcut/key path with virtual focus.
            // This updates only Qt's own dispatcher, never OS focus or input.
            const QString text = command.value(QStringLiteral("text")).toString();
            QMetaObject::invokeMethod(window, [window, key, modifiers, text] {
                QWindowSystemInterface::handleFocusWindowChanged<QWindowSystemInterface::SynchronousDelivery>(window, Qt::OtherFocusReason);
                QWindowSystemInterface::handleKeyEvent<QWindowSystemInterface::SynchronousDelivery>(window, QEvent::KeyPress, key, modifiers, text);
                QWindowSystemInterface::handleKeyEvent<QWindowSystemInterface::SynchronousDelivery>(window, QEvent::KeyRelease, key, modifiers);
            }, Qt::QueuedConnection);
#else
            QCoreApplication::postEvent(window, new QKeyEvent(QEvent::KeyPress, key, modifiers, command.value(QStringLiteral("text")).toString()));
            QCoreApplication::postEvent(window, new QKeyEvent(QEvent::KeyRelease, key, modifiers));
#endif
        } else error = QStringLiteral("unsupported_operation_rejected_before_dispatch");

        if (!window) {
            respond(id, {{QStringLiteral("id"), id}, {QStringLiteral("status"), QStringLiteral("failed")},
                         {QStringLiteral("error"), error}});
            return;
        }
        const auto render = [this, window, id, before, error, command] {
            const qint64 predicateObserved = m_clock.elapsed();
            // Await a real rendered frame: a queued invocation alone can run before
            // Qt Quick's deferred polish/positioner pass (notably popup Columns).
            connect(window, &QQuickWindow::frameSwapped, this, [this, id, before, error, command, predicateObserved] {
                if (id != m_pendingId) return;
                const qint64 frameObserved = m_clock.elapsed();
                const auto finish = [this, id, before, error, frameObserved, command, predicateObserved](const QJsonObject &extra) {
                    if (id != m_pendingId) return;
                    // A state assignment may briefly publish an animation's
                    // target before its first frame. Keep observing until the
                    // predicate also holds at the actual capture boundary.
                    if (m_waitExpression) {
                        if (!observationMatches(observationValue(command), command)) return;
                    }
                    auto result = snapshot();
                    result.insert(QStringLiteral("id"), id);
                    result.insert(QStringLiteral("before_revision"), before);
                    result.insert(QStringLiteral("frame_observed_ms"), frameObserved);
                    if (error.isEmpty() && (!command.value(QStringLiteral("await_property")).toString().isEmpty()
                        || !command.value(QStringLiteral("await_core")).toString().isEmpty()))
                        result.insert(QStringLiteral("property_observation"), QJsonObject{
                            {QStringLiteral("property"), command.value(QStringLiteral("await_property"))},
                            {QStringLiteral("core_property"), command.value(QStringLiteral("await_core"))},
                            {QStringLiteral("expected"), command.value(QStringLiteral("await_value"))},
                            {QStringLiteral("satisfied_at_ms"), predicateObserved}});
                    result.insert(QStringLiteral("status"), error.isEmpty() ? QStringLiteral("completed") : QStringLiteral("failed"));
                    if (!error.isEmpty()) result.insert(QStringLiteral("error"), error);
                    for (auto it = extra.begin(); it != extra.end(); ++it) result.insert(it.key(), it.value());
                    if (extra.value(QStringLiteral("capture_saved")).toBool()) {
                        QJsonArray captures;
                        for (int i = 0; i < m_widgets.size(); ++i) {
                            auto widget = m_widgets[i].data();
                            if (widget && widget->isWindow()) {
                                const QString name = id + QStringLiteral("-widget-%1.png").arg(i);
                                captures.append(QJsonObject{{QStringLiteral("widget"), i}, {QStringLiteral("file"), name},
                                    {QStringLiteral("saved"), widget->grab().save(QDir(m_directory).filePath(name))}});
                            }
                        }
                        result.insert(QStringLiteral("widget_captures"), captures);
                    }
                    respond(id, result);
                };
                if (command.value(QStringLiteral("capture")).toBool() && m_root->window()) {
                    auto grab = m_root->window()->contentItem()->grabToImage();
                    if (grab) {
                        connect(grab.data(), &QQuickItemGrabResult::ready, this, [this, grab, id, finish] {
                            finish({{QStringLiteral("capture_saved"), grab->saveToFile(QDir(m_directory).filePath(id + QStringLiteral(".png")))},
                                    {QStringLiteral("capture_elapsed_ms"), m_clock.elapsed()}});
                        });
                        return;
                    }
                    finish({{QStringLiteral("capture_saved"), false}});
                    return;
                }
                finish({});
            }, Qt::ConnectionType(Qt::QueuedConnection | Qt::SingleShotConnection));
            window->update();
        };
        if (!error.isEmpty() || !observed) {
            // Input events were queued first. Observe rendering after their
            // dispatcher turn, including real nested modal-dialog loops.
            QMetaObject::invokeMethod(this, render, Qt::QueuedConnection);
            return;
        }
        // Bind only a whitelisted property, never a caller-supplied expression.
        // QQmlExpression observes its real QML/C++ notify dependencies; there is
        // no timer, fixed delay or repeated synthetic action.
        auto expression = new QQmlExpression(qmlContext(m_root), observed, awaitProperty, this);
        m_waitExpression = expression;
        expression->setNotifyOnValueChanged(true);
        const auto check = [this, expression, command, id, render] {
            if (id != m_pendingId || m_waitExpression != expression) return;
            const QVariant actual = observationValue(command);
            if (expression->hasError()) {
                m_waitExpression = nullptr;
                expression->deleteLater();
                respond(id, {{QStringLiteral("id"), id}, {QStringLiteral("status"), QStringLiteral("failed")},
                    {QStringLiteral("error"), QStringLiteral("property_observation_failed")}});
                return;
            }
            const bool matched = observationMatches(actual, command);
            if (!matched && !command.value(QStringLiteral("await_media_url")).toString().isEmpty()) {
                const auto core = coreSnapshot();
                if (core.value(QStringLiteral("url")) != command.value(QStringLiteral("await_media_url"))
                    || core.value(QStringLiteral("state")).toInt() == VLC_PLAYER_STATE_STOPPED
                    || core.value(QStringLiteral("state")).toInt() == VLC_PLAYER_STATE_STOPPING) {
                    respond(id, {{QStringLiteral("id"), id}, {QStringLiteral("status"), QStringLiteral("failed")},
                        {QStringLiteral("error"), QStringLiteral("input_changed_or_ended_during_observation")},
                        {QStringLiteral("core"), core}});
                    return;
                }
            }
            if (!matched) return;
            render();
        };
        connect(expression, &QQmlExpression::valueChanged, this, check);
        if (!awaitCore.isEmpty()) {
            connect(m_player, &PlayerController::inputChanged, expression, check);
            connect(m_player, &PlayerController::playingStateChanged, expression, check);
        }
        connect(observed, &QObject::destroyed, expression, [this, expression, id] {
            if (id != m_pendingId || m_waitExpression != expression) return;
            m_waitExpression = nullptr;
            expression->deleteLater();
            respond(id, {{QStringLiteral("id"), id}, {QStringLiteral("status"), QStringLiteral("failed")},
                {QStringLiteral("error"), QStringLiteral("observed_item_destroyed")}});
        });
        QMetaObject::invokeMethod(this, check, Qt::QueuedConnection);
    }
};
#endif
#endif
