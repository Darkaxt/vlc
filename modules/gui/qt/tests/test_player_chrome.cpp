// SPDX-License-Identifier: GPL-2.0-or-later
#include <QTest>
#include <QQmlComponent>
#include <QQmlEngine>
#include <QFileInfo>
#include <QDir>
#include <QEventLoop>
#include <QtPlugin>
#include <memory>
#include "widgets/native/settings_svg_icon.hpp"

#ifdef QT_STATIC
Q_IMPORT_PLUGIN(QtQmlPlugin)
Q_IMPORT_PLUGIN(QtQmlModelsPlugin)
Q_IMPORT_PLUGIN(QtQmlWorkerScriptPlugin)
#endif

class TestPlayerChrome : public QObject
{
    Q_OBJECT
private slots:
    void settingsIconsUseRequestedResolution()
    {
        const auto configured=qEnvironmentVariable("VLC_TEST_SETTINGS_SVG_ROOT");
        const QString info=configured.isEmpty()
            ? QFINDTESTDATA("../pixmaps/redesign/settings-info.svg")
            : QDir(configured).filePath(QStringLiteral("settings-info.svg"));
        const QDir svgRoot=QFileInfo(info).dir();
        const auto selected=svgRoot.filePath(QStringLiteral("settings-general-active.svg"));
        QVERIFY(QFileInfo::exists(info));
        QVERIFY(QFileInfo::exists(selected));
        const auto pixels=[](const QPixmap &pixmap) {
            auto image=pixmap.toImage().convertToFormat(QImage::Format_ARGB32_Premultiplied);
            image.setDevicePixelRatio(1);
            return image;
        };
        // Independent oracle: render the original vector directly into native
        // physical pixels, then apply the same requested foreground color.
        const auto original=[](const QString &path,const QColor &color,const QSize &size,qreal dpr) {
            QPixmap result(size*dpr);
            result.fill(Qt::transparent);
            {
                QPainter painter(&result);
                QSvgRenderer svg(path);
                const QRectF nativeBounds(0,0,size.width()*dpr,size.height()*dpr);
                svg.render(&painter,nativeBounds);
                painter.setCompositionMode(QPainter::CompositionMode_SourceIn);
                painter.fillRect(nativeBounds,color);
            }
            result.setDevicePixelRatio(dpr);
            return result;
        };
        const QColor foreground("#969696"),accent("#8e42ff");
        bool rejectedLegacyInfo18=false;
        for(const char *name:{"settings-info.svg","search.svg"})
        {
            const auto path=svgRoot.filePath(QString::fromLatin1(name));
            QVERIFY(QFileInfo::exists(path));
            const auto icon=settingsSvgIcon(path,foreground,selected,accent);
            for(qreal dpr:{qreal(1),qreal(1.5),qreal(2)})
                for(int edge:{16,18,24})
                {
                    const QSize size(edge,edge);
                    const auto expected=original(path,foreground,size,dpr);
                    const auto actual=icon.pixmap(size,dpr,QIcon::Normal);
                    const auto legacy=QIcon(original(path,foreground,QSize(24,24),dpr)).pixmap(size,dpr);
                    const auto evidence=qEnvironmentVariable("VLC_TEST_SETTINGS_ICON_EVIDENCE");
                    if(!evidence.isEmpty() && edge==18 && QString::fromLatin1(name)==QStringLiteral("settings-info.svg"))
                    {
                        const auto base=QDir(evidence).filePath(QStringLiteral("info-18-dpr-%1").arg(qRound(dpr*100)));
                        QVERIFY(expected.save(base+QStringLiteral("-original.png")));
                        QVERIFY(legacy.save(base+QStringLiteral("-old.png")));
                        QVERIFY(actual.save(base+QStringLiteral("-native.png")));
                    }
                    if(QString::fromLatin1(name)==QStringLiteral("settings-info.svg") && edge==18 && dpr==1)
                        rejectedLegacyInfo18=pixels(legacy)!=pixels(expected);
                    if(edge==24)QCOMPARE(pixels(legacy),pixels(expected));
                    QCOMPARE(actual.size(),size*dpr);
                    QCOMPARE(actual.devicePixelRatioF(),dpr);
                    QCOMPARE(pixels(actual),pixels(expected));
                    QCOMPARE(pixels(icon.pixmap(size,dpr,QIcon::Selected)),pixels(original(selected,accent,size,dpr)));
                    QPixmap painted(size*dpr);
                    painted.setDevicePixelRatio(dpr);
                    painted.fill(Qt::transparent);
                    {
                        QPainter painter(&painted);
                        icon.paint(&painter,QRect(QPoint(),size));
                    }
                    QCOMPARE(pixels(painted),pixels(expected));
                }
        }
        QVERIFY2(rejectedLegacyInfo18,"The regression must distinguish the old24-to18 filtered icon from the original vector.");
    }

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
        QVERIFY(visible("topVisible") && visible("bottomVisible"));
        set("idle",true);
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
        set("topHovered",false);
        set("bottomFocused",false);
        set("fullscreen",false);
        QVERIFY(chrome->setProperty("autoHideMode",1));
        set("idle",true);
        QVERIFY(!visible("topVisible") && !visible("bottomVisible"));
        QVERIFY(chrome->setProperty("autoHideMode",2));
        QVERIFY(visible("topVisible") && visible("bottomVisible"));
        set("fullscreen",true);
        set("fullscreenControls",false);
        QVERIFY(visible("topVisible") && !visible("bottomVisible"));
        set("fullscreenControls",true);
        QVERIFY(chrome->setProperty("autoHideMode",0));
        QVERIFY(chrome->setProperty("mouseSensitivity",10));
        const QVariant origin=QPointF(0,0),small=QPointF(3,4),threshold=QPointF(8,6);
        QVERIFY(QMetaObject::invokeMethod(chrome.get(),"pointerMoved",Q_ARG(QVariant,origin)));
        set("idle",true);
        QVERIFY(QMetaObject::invokeMethod(chrome.get(),"pointerMoved",Q_ARG(QVariant,small)));
        QVERIFY(!visible("topVisible") && !visible("bottomVisible"));
        QVERIFY(QMetaObject::invokeMethod(chrome.get(),"pointerMoved",Q_ARG(QVariant,threshold)));
        QVERIFY(visible("topVisible") && visible("bottomVisible"));
        QVERIFY(chrome->setProperty("hideDelay",0));
        QEventLoop idleChanged;
        connect(chrome.get(),SIGNAL(idleChanged()),&idleChanged,SLOT(quit()));
        QVERIFY(QMetaObject::invokeMethod(chrome.get(),"activity"));
        while(!chrome->property("idle").toBool())idleChanged.exec();
        QVERIFY(!visible("topVisible") && !visible("bottomVisible"));
    }
};
QTEST_MAIN(TestPlayerChrome)
#include "test_player_chrome.moc"
