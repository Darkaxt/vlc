// SPDX-License-Identifier: GPL-2.0-or-later
#include <QTest>
#include <QQmlComponent>
#include <QQmlEngine>
#include <QFileInfo>
#include <QtPlugin>
#include <memory>

#ifdef QT_STATIC
Q_IMPORT_PLUGIN(QtQmlPlugin)
Q_IMPORT_PLUGIN(QtQmlModelsPlugin)
Q_IMPORT_PLUGIN(QtQmlWorkerScriptPlugin)
#endif

class TestPlayerChrome : public QObject
{
    Q_OBJECT
private slots:
    void visibilityFollowsInputState()
    {
        const auto configured = qEnvironmentVariable("VLC_TEST_PLAYER_CHROME_QML");
        const auto source = configured.isEmpty()
            ? QFINDTESTDATA("../player/qml/PlayerChromeState.qml") : configured;
        QVERIFY(QFileInfo::exists(source));
        QQmlEngine engine;
        QQmlComponent component(&engine, QUrl::fromLocalFile(source));
        QVERIFY2(!component.isError(), qPrintable(component.errorString()));
        std::unique_ptr<QObject> chrome(component.create());
        QVERIFY2(chrome, qPrintable(component.errorString()));
        const auto visible = [&](const char *name) { return chrome->property(name).toBool(); };
        const auto set = [&](const char *name, bool value) { QVERIFY(chrome->setProperty(name, value)); };

        QVERIFY(visible("topVisible") && visible("bottomVisible"));
        set("fullscreen", true);
        QVERIFY(!visible("topVisible") && !visible("bottomVisible"));
        set("topHovered", true);
        QVERIFY(visible("topVisible") && !visible("bottomVisible"));
        set("topHovered", false);
        set("bottomHovered", true);
        QVERIFY(!visible("topVisible") && visible("bottomVisible"));
        set("bottomHovered", false);
        QVERIFY(!visible("topVisible") && !visible("bottomVisible"));

        for (const auto property : {"topFocused", "topMenuOpen"})
        {
            set(property, true);
            QVERIFY(visible("topVisible") && !visible("bottomVisible"));
            set(property, false);
            QVERIFY(!visible("topVisible"));
        }
        for (const auto property : {"bottomFocused", "bottomMenuOpen"})
        {
            set(property, true);
            QVERIFY(!visible("topVisible") && visible("bottomVisible"));
            set(property, false);
            QVERIFY(!visible("bottomVisible"));
        }
        set("topHovered", true);
        set("bottomFocused", true);
        QVERIFY(QMetaObject::invokeMethod(chrome.get(), "toggleHidden"));
        QVERIFY(!visible("topVisible") && !visible("bottomVisible"));
        QVERIFY(QMetaObject::invokeMethod(chrome.get(), "toggleHidden"));
        QVERIFY(visible("topVisible") && visible("bottomVisible"));
    }
};
QTEST_GUILESS_MAIN(TestPlayerChrome)
#include "test_player_chrome.moc"
