// SPDX-License-Identifier: GPL-2.0-or-later
// Shared Figma styling for the S5 native preference/open/convert/stream/add-on boundary.
#pragma once
#include "maininterface/mainctx.hpp"
#include "util/color_scheme_model.hpp"
#include <QWidget>
#include <QApplication>
#include <QFontDatabase>
#include <QPalette>
inline void applyRedesignDialogStyle(QWidget *widget, qt_intf_t *intf)
{
    if(intf->p_mi && !widget->property("redesignStyleBound").toBool()){
        widget->setProperty("redesignStyleBound",true);
        QObject::connect(intf->p_mi,&MainCtx::redesignAccentChanged,widget,
                         [widget,intf](){applyRedesignDialogStyle(widget,intf);});
        QObject::connect(intf->p_mi->getColorScheme(),&ColorSchemeModel::currentChanged,widget,
                         [widget,intf](){applyRedesignDialogStyle(widget,intf);});
    }
    // Qt's stylesheet repolish restores its cached pre-stylesheet palette.
    // Unpolish the previous sheet before installing the new native palette,
    // so an existing window cannot restore the old theme/accent underneath it.
    widget->setStyleSheet(QString());
    static const int fontId =
        QFontDatabase::addApplicationFont(":/redesign/fonts/InterVariable.ttf");
    static const auto families = QFontDatabase::applicationFontFamilies(fontId);
    QFont f(families.isEmpty() ? widget->font().family() : families.front());
    f.setPixelSize(14);
    widget->setFont(f);
    const auto scheme =
        intf->p_mi ? intf->p_mi->getColorScheme()->currentScheme() : ColorSchemeModel::System;
    const bool dark = scheme == ColorSchemeModel::Night ||
                      (scheme == ColorSchemeModel::System &&
                       QApplication::palette().color(QPalette::Window).lightness() < 128);
    const QString bg = dark ? "#0e0e0e" : "#e7e7e7", fg = dark ? "#8f8f8f" : "#2e2e2e";
    const QColor accent = intf->p_mi ? intf->p_mi->getRedesignAccent() : QColor("#d37918");
    QPalette palette = widget->palette();
    palette.setColor(QPalette::Window, QColor(bg));
    palette.setColor(QPalette::Base, QColor(bg));
    palette.setColor(QPalette::Button, QColor(dark ? "#1b1b1b" : "#d5d5d5"));
    palette.setColor(QPalette::AlternateBase, QColor(dark ? "#1b1b1b" : "#d5d5d5"));
    palette.setColor(QPalette::Text, QColor(fg));
    palette.setColor(QPalette::WindowText, QColor(fg));
    palette.setColor(QPalette::ButtonText, QColor(fg));
    palette.setColor(QPalette::Highlight, accent);
    palette.setColor(QPalette::HighlightedText, intf->p_mi ? intf->p_mi->getRedesignAccentText() : QColor("#2e2e2e"));
    palette.setColor(QPalette::PlaceholderText, QColor(dark ? "#3f3f3f" : "#676767"));
    widget->setPalette(palette);
    widget->setAutoFillBackground(true);
    const QString field = dark ? "#191919" : "#d5d5d5", hover = dark ? "#222222" : "#c5c5c5";
    widget->setProperty("figmaDark", dark);
    widget->setStyleSheet(QString(R"(
        QDialog { background:%1; color:%2; border-radius:14px; }
        QWidget { color:%2; font-family:"%6"; font-size:14px; }
        QLabel { background:transparent; }
        QLabel#preferencesHeading { color:%7; }
        QLabel[redesignSection="true"] { color:%8; }
        QMenu { background:%1; color:%2; border:0; border-radius:10px; padding:8px; }
        QMenu::item { padding:8px 20px; border-radius:4px; }
        QMenu::item:selected { background:%4; }
        QMenu::separator { height:1px; background:%4; margin:8px 12px; }
        QLineEdit,QComboBox,QSpinBox,QDoubleSpinBox,QFontComboBox { background:%3; border:1px solid %4; border-radius:4px; padding:7px 12px; min-height:18px; }
        QLineEdit:focus,QComboBox:focus,QSpinBox:focus,QDoubleSpinBox:focus { border:1px solid %5; }
        QComboBox { padding-right:28px; }
        QComboBox::drop-down { subcontrol-origin:padding; subcontrol-position:top right; width:24px; border:0; background:transparent; }
        QComboBox::down-arrow { image:url(:/redesign/icons/native-chevron-down-%9.svg); width:24px; height:24px; }
        QSpinBox,QDoubleSpinBox { padding-right:24px; }
        QSpinBox::up-button,QDoubleSpinBox::up-button { subcontrol-origin:padding; subcontrol-position:top right; width:20px; height:16px; border:0; background:transparent; }
        QSpinBox::down-button,QDoubleSpinBox::down-button { subcontrol-origin:padding; subcontrol-position:bottom right; width:20px; height:16px; border:0; background:transparent; }
        QSpinBox::up-arrow,QDoubleSpinBox::up-arrow { image:url(:/redesign/icons/native-chevron-up-%9.svg); width:12px; height:12px; }
        QSpinBox::down-arrow,QDoubleSpinBox::down-arrow { image:url(:/redesign/icons/native-chevron-down-%9.svg); width:12px; height:12px; }
        QPushButton,QToolButton { background:%3; border:0; border-radius:4px; padding:7px 12px; }
        QPushButton:hover,QToolButton:hover { background:%4; }
        QPushButton:focus,QToolButton:focus { border:1px solid %5; }
        QCheckBox { spacing:10px; min-height:32px; }
        QCheckBox::indicator { width:24px; height:24px; border:1px solid %4; border-radius:4px; background:%3; }
        QCheckBox::indicator:checked { background:%5; image:url(:/redesign/icons/choice-selected.svg); }
        QListWidget { background:%3; border:0; border-radius:6px; padding:6px; outline:0; }
        QListWidget::item { padding:8px 10px; min-height:16px; border-radius:3px; }
        QListWidget::item:selected { background:%4; color:%5; }
        QListWidget::item:focus { border:1px solid %5; }
        QListView { background:%3; alternate-background-color:%1; border:0; border-radius:6px; outline:0; }
        QListView::item:selected { background:%4; }
        QListView::item:focus { border:1px solid %5; }
        QTabWidget::pane { border:0; background:transparent; }
        QTabBar::tab { background:%3; color:%2; padding:8px 14px; }
        QTabBar::tab:selected { color:%5; background:%4; }
        QScrollArea { border:0; background:transparent; }
        QTreeWidget { background:%1; border:0; alternate-background-color:%3; }
        QHeaderView::section { background:%3; color:%2; border:0; padding:8px; }
        QScrollBar:vertical { background:%1; width:8px; }
        QScrollBar::handle:vertical { background:%4; border-radius:4px; min-height:24px; }
    )")
                              .arg(bg, fg, field, hover, accent.name(), f.family(),
                                   dark ? "#969696" : "#2e2e2e", dark ? "#c6c6c6" : "#2e2e2e", dark ? "dark" : "light"));
}
