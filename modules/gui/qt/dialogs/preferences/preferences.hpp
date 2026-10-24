/*****************************************************************************
 * preferences.hpp : Preferences
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

#ifndef QVLC_PREFS_DIALOG_H_
#define QVLC_PREFS_DIALOG_H_ 1
#include "widgets/native/qvlcframe.hpp"
#include <QVector>
#include <QSet>
class QComboBox;
class ConfigControl;
class KeySelectorControl;
class QStackedWidget;
class QListWidget;
class QLineEdit;
class QLabel;
class QVBoxLayout;
class QTreeWidget;
class QTreeWidgetItem;
struct WindowEffectsModule;
class PrefsDialog : public QVLCDialog
{
    Q_OBJECT
  public:
    PrefsDialog(QWindow *, qt_intf_t *);
    ~PrefsDialog() override;
    void showShortcuts();

  protected:
    bool eventFilter(QObject *, QEvent *) override;
    void showEvent(QShowEvent *) override;
    void hideEvent(QHideEvent *) override;
    void paintEvent(QPaintEvent *) override;
    void resizeEvent(QResizeEvent *) override;

  private:
    struct Option
    {
        module_config_t *config;
        QString module;
        QString group;
        int category;
        bool basic;
    };
    QVector<module_config_t *> configs;
    QVector<Option> options;
    QVector<ConfigControl *> controls;
    QStackedWidget *pages = nullptr;
    QListWidget *categories = nullptr;
    QWidget *categoryContainer;
    QLineEdit *search;
    QTreeWidget *results;
    QLabel *heading;
    QWidget *categoryPages[13] = {};
    QComboBox *language = nullptr;
    int selectedTheme = -1;
    QString originalLanguage;
    QWidget *shortcutsPage = nullptr;
    KeySelectorControl *shortcuts = nullptr;
    WindowEffectsModule *windowEffects = nullptr;
    bool blurBehind = false;
    void inventory();
    QWidget *createCategory(int);
    void addOption(QVBoxLayout *, const Option &);
    void selectCategory(int);
    void filter(const QString &);
    void openResult(QTreeWidgetItem *);
    void save();
    void reset();
    void resetPreferences();
    void updateResponsiveLayout();
};
#endif
