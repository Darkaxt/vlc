/*****************************************************************************
 * qvlcframe.cpp : A few helpers
 *****************************************************************************
 * Copyright (C) 2006-2007 the VideoLAN team
 *
 * Authors: Clément Stenac <zorglub@videolan.org>
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

#include <QWindow>
#include <QScreen>
#include <QApplication>
#include <QKeyEvent>
#include <QStyle>
#include <QMenu>
#include <QAbstractItemView>
#include <vlc_modules.h>

#include "qvlcframe.hpp"
#include "maininterface/compositor.hpp"
#include "maininterface/mainctx.hpp"
#include "maininterface/windoweffects_module.hpp"

namespace {
// QMenu also creates plain QMenu children for native VLC subcommands. Observe
// their real lifecycle in one place, before polishing creates their HWNDs.
class MenuBackdrops final : public QObject
{
    qt_intf_t *m_intf;
    WindowEffectsModule *m_effects = nullptr;
public:
    explicit MenuBackdrops(qt_intf_t *intf) : QObject(intf->p_mi), m_intf(intf)
    {
        qApp->installEventFilter(this);
    }
    ~MenuBackdrops() override
    {
        if (m_effects) {
            if (m_effects->p_module) module_unneed(m_effects, m_effects->p_module);
            vlc_object_delete(m_effects);
        }
    }
    bool eventFilter(QObject *object, QEvent *event) override
    {
        auto *menu = qobject_cast<QWidget *>(object);
        if (!menu || menu->windowType() != Qt::Popup ||
            !var_InheritBool(m_intf, "qt-backdrop-blur"))
            return false;
        if (event->type() == QEvent::Polish) {
            menu->setWindowFlag(Qt::FramelessWindowHint);
            menu->setAttribute(Qt::WA_TranslucentBackground);
            menu->setAutoFillBackground(false);
        } else if (event->type() == QEvent::Show) {
            if (!m_effects) {
                m_effects = vlc_object_create<WindowEffectsModule>(m_intf);
                if (m_effects)
                    m_effects->p_module = module_need(m_effects, "qtwindoweffects", nullptr, false);
            }
            auto *window = menu->windowHandle();
            const bool available = m_effects && m_effects->p_module && window &&
                m_effects->isEffectAvailable(window, WindowEffectsModule::BlurBehind);
            menu->setProperty("redesignGlassMenu", available);
            // Re-polish this menu only; existing native menu models, commands,
            // focus and submenu ownership remain unchanged.
            menu->style()->unpolish(menu);
            menu->style()->polish(menu);
            menu->setAutoFillBackground(false);
            menu->clearMask();
            for (auto *view : menu->findChildren<QAbstractItemView *>()) {
                view->style()->unpolish(view);
                view->style()->polish(view);
                view->viewport()->setAutoFillBackground(false);
            }
            if (available) m_effects->setBlurBehind(window, true, {});
        } else if (event->type() == QEvent::Hide && m_effects && m_effects->p_module &&
                   menu->property("redesignGlassMenu").toBool() && menu->windowHandle()) {
            m_effects->setBlurBehind(menu->windowHandle(), false, {});
        }
        return false;
    }
};
}

void QVLCTools::installMenuBackdrops(qt_intf_t *intf)
{
    if (intf->p_mi && !intf->p_mi->property("menuBackdropsInstalled").toBool()) {
        intf->p_mi->setProperty("menuBackdropsInstalled", true);
        new MenuBackdrops(intf);
    }
}

void QVLCTools::saveWidgetPosition(QSettings *settings, QWidget *widget)
{
    settings->setValue("geometry", widget->saveGeometry());
}

void QVLCTools::saveWindowPosition(QSettings *settings, QWindow *window)
{
    //no standard way to do it, mimic what qt is doing internally
    QByteArray array;
    QDataStream serialized(&array, QIODevice::WriteOnly);
    serialized.setVersion(QDataStream::Qt_4_0);

    //we use a different magic number than Qt
    const quint32 magicNumber = 0x1D94200;
    serialized << magicNumber
        << quint8(1) //version major
        << quint8(0) //version minor
        << window->screen()->name()
        << window->screen()->devicePixelRatio()
        << window->screen()->geometry()
        << window->position()
        << window->geometry()
        << quint8(window->windowStates() & Qt::WindowMaximized)
        << quint8(window->windowStates() & Qt::WindowFullScreen);
    settings->setValue("geometry", array);
}

static bool restoreWindowPositionImpl(QSettings *settings, QWindow *window)
{
    //no standard way to do it, mimic what qt is doing internally
    auto raw = settings->value("geometry").toByteArray();

    if (raw.length() < 4)
        return false;

    QDataStream serialized(raw);
    serialized.setVersion(QDataStream::Qt_4_0);
    quint32 magicNumber;
    quint8 versionMajor;
    quint8 versionMinor;

    serialized
        >> magicNumber
        >> versionMajor
        >> versionMinor;

    if (magicNumber != 0x1D94200 || versionMajor != 1)
        return false;

    QString screenName;
    qreal screenDRP;
    QRect screenGeometry;

    QPoint position;
    QRect geometry;
    quint8 maximized;
    quint8 fullscreen;

    serialized
        >> screenName
        >> screenDRP
        >> screenGeometry
        >> position
        >> geometry
        >> maximized
        >> fullscreen;

    if (screenName.isNull() || screenGeometry.isNull())
        return false;

    if (geometry.isNull())
        return false;

    bool screenFound = false;
    for (auto screen: QGuiApplication::screens())
    {
        if (screen->name() == screenName)
        {
            if (screen->geometry() != screenGeometry
                || screen->devicePixelRatio() != screenDRP)
            {
                //same screen but its property has changed, don't restore the position
                break;
            }
            window->setScreen(screen);
            screenFound = true;
            break;
        }
    }
    if (!screenFound)
        return false;

    window->setPosition(position);
    window->setGeometry(geometry);

    if (maximized || fullscreen)
    {
        Qt::WindowStates state = window->windowStates();
        if (maximized)
            state |= Qt::WindowMaximized;
        if (fullscreen)
            state |= Qt::WindowFullScreen;
        window->setWindowStates(state);
    }
    else
    {
        window->setWindowStates(window->windowStates() & ~(Qt::WindowMaximized | Qt::WindowFullScreen));
    }

    return true;
}

void QVLCTools::restoreWindowPosition(QSettings *settings, QWindow *window, QSize defSize, QPoint defPos)
{
    bool ret = restoreWindowPositionImpl(settings, window);
    if (ret)
        return;

    window->resize(defSize);
    if (defPos.isNull())
    {
        window->setGeometry(QStyle::alignedRect(Qt::LeftToRight, Qt::AlignCenter, window->size(), QGuiApplication::primaryScreen()->availableGeometry()));
    }
    else
    {
        window->setPosition(defPos);
    }
}


void QVLCTools::saveWidgetPosition(qt_intf_t *p_intf,
                                   const QString& configName,
                                   QWidget *widget)
{
    getSettings()->beginGroup(configName);
    QVLCTools::saveWidgetPosition(getSettings(), widget);
    getSettings()->endGroup();
}

bool QVLCTools::restoreWidgetPosition(QSettings *settings, QWidget *widget,
                                      QSize defSize, QPoint defPos)
{
    if (!widget->restoreGeometry(settings->value("geometry").toByteArray()))
    {
        widget->move(defPos);
        widget->resize(defSize);

        if (defPos.x() == 0 && defPos.y()==0)
            widget->setGeometry(QStyle::alignedRect(Qt::LeftToRight, Qt::AlignCenter, widget->size(), qApp->primaryScreen()->availableGeometry()));
        return true;
    }
    return false;
}

bool QVLCTools::restoreWidgetPosition(qt_intf_t *p_intf,
                                      const QString& configName,
                                      QWidget *widget, QSize defSize,
                                      QPoint defPos)
{
    getSettings()->beginGroup(configName);
    bool defaultUsed =
        QVLCTools::restoreWidgetPosition(getSettings(), widget, defSize, defPos);
    getSettings()->endGroup();

    return defaultUsed;
}

QVLCFrame::QVLCFrame(qt_intf_t *_p_intf) : QWidget( NULL ), p_intf( _p_intf )
{
    assert(_p_intf);

    if (isWindow())
    {
        // If window, set the transient parent:
        QVLCDialog::setWindowTransientParent(this, nullptr, p_intf);
    }
}

void QVLCFrame::keyPressEvent(QKeyEvent *keyEvent)
{
    if (keyEvent->key() == Qt::Key_Escape)
    {
        this->cancel();
    }
    else if (keyEvent->key() == Qt::Key_Return ||
             keyEvent->key() == Qt::Key_Enter)
    {
        this->close();
    }
}

void QVLCDialog::setWindowTransientParent(QWidget* widget, QWindow* parent, qt_intf_t* p_intf)
{
    assert(widget);
    assert(widget->isWindow()); // Do not call this method if widget is not a window.

    if (!parent && p_intf && !p_intf->b_isDialogProvider)
    {
        assert(p_intf->p_compositor);
        parent = p_intf->p_compositor->interfaceMainWindow();
    }
    if (!parent)
        return;

    widget->ensurePolished();
    widget->createWinId();
    QWindow* handle  = widget->windowHandle();
    handle->setTransientParent(parent);
}


QVLCDialog::QVLCDialog(QWindow *parent, qt_intf_t *_p_intf, bool translucent)
    : QDialog(),
      p_intf( _p_intf )
{
    auto flags = Qt::Dialog|Qt::WindowMinMaxButtonsHint|
                 Qt::WindowSystemMenuHint|Qt::WindowCloseButtonHint;
    if (translucent)
        flags |= Qt::FramelessWindowHint;
    setWindowFlags(flags);
    // setWindowTransientParent() creates the native handle. Qt6.8 cannot
    // change its alpha format afterwards, even when a QWidget-only capture
    // contains transparent pixels. Configure the actual surface first.
    if (translucent)
        setAttribute(Qt::WA_TranslucentBackground);

    setWindowTransientParent(this, parent, p_intf);
}
