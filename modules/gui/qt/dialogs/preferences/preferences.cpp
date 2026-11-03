/*****************************************************************************
 * preferences.cpp : Preferences
 *****************************************************************************
 * Copyright (C) 2006-2007 the VideoLAN team
 *
 * Authors: Clément Stenac <zorglub@videolan.org>
 *          Jean-Baptiste Kempf <jb@videolan.org>
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

#ifdef HAVE_CONFIG_H
#include "config.h"
#endif
#include "preferences.hpp"
#include "preferences_widgets.hpp"
#include "preferences_languages.hpp"
#include "preferences_catalog.hpp"
#ifdef _WIN32
#include "util/registry.hpp"
#endif
#include "widgets/native/redesign_style.hpp"
#include "dialogs/plugins/plugins.hpp"
#include <QTabWidget>
#include "dialogs/dialogs_provider.hpp"
#include "maininterface/mainctx.hpp"
#include "maininterface/windoweffects_module.hpp"
#include "util/color_scheme_model.hpp"
#include <vlc_config_cat.h>
#include <vlc_modules.h>
#include <vlc_saved_options.h>
#include <QApplication>
#include <QAbstractSpinBox>
#include <QSpinBox>
#include <QDoubleSpinBox>
#include <QCheckBox>
#include <QComboBox>
#include <QColorDialog>
#include <QButtonGroup>
#include <QPainter>
#include <QPainterPath>
#include <QRegion>
#include <QSlider>
#include <QStyle>
#include <QStyleOptionSlider>
#include <QPixmap>
#include <QSettings>
#include <QSignalBlocker>
#include <QSvgRenderer>
#include <QDialogButtonBox>
#include <QFontDatabase>
#include <QFontComboBox>
#include <QFontMetrics>
#include <QKeyEvent>
#include <QtMath>
#include <QGridLayout>
#include <QGuiApplication>
#include <QLabel>
#include <QLineEdit>
#include <QListWidget>
#include <QListView>
#include <QSortFilterProxyModel>
#include <QMessageBox>
#include <QMouseEvent>
#include <QPushButton>
#include <QScreen>
#include <QScrollArea>
#include <QScrollBar>
#include <QSizeGrip>
#include <QStackedWidget>
#include <QToolButton>
#include <QTreeWidget>
#include <QTransform>
#include <QWindow>
#include <QDesktopServices>
#include <QUrl>
#include "medialibrary/medialib.hpp"
#include "medialibrary/mlrecentmediamodel.hpp"
#include "menus/menus.hpp"
#include "network/addonsmodel.hpp"
#include "../../../../audio_filter/equalizer_presets.h"
#include <QFileDialog>
#include <QProcess>
#include <QPersistentModelIndex>
#include <algorithm>

namespace
{
class SettingsLabel final : public QLabel
{
  public:
    SettingsLabel(const QString &text, QWidget *parent) : QLabel(text, parent)
    {
        setWordWrap(true);
    }
    QSize sizeHint() const override
    {
        // Prefer the unwrapped source label. QLabel's wrapped preferred width
        // otherwise squeezes short labels despite ample space in their row.
        return QSize(qCeil(QFontMetricsF(font()).horizontalAdvance(text())) + 1, fontMetrics().height());
    }
};
// Keep Qt's native input, focus, accessibility and DPR rasterization. The
// reference puts short tick marks inside the track, rather than below it.
class SettingsSlider final : public QSlider
{
  public:
    explicit SettingsSlider(QWidget *parent,Qt::Orientation direction=Qt::Horizontal) : QSlider(direction,parent) {}
    int referenceTickInterval=0;
  protected:
    void paintEvent(QPaintEvent *event) override
    {
        QSlider::paintEvent(event);
        if(referenceTickInterval<=0)return;
        QStyleOptionSlider option;
        initStyleOption(&option);
        const auto groove=style()->subControlRect(QStyle::CC_Slider,&option,QStyle::SC_SliderGroove,this);
        const auto handle=style()->subControlRect(QStyle::CC_Slider,&option,QStyle::SC_SliderHandle,this);
        QPainter painter(this);
        painter.setRenderHint(QPainter::Antialiasing);
        painter.setPen(Qt::NoPen);
        painter.setOpacity(isEnabled() ? 0.18 : 0.08);
        painter.setBrush(palette().text());
        for(int tick=minimum()+referenceTickInterval;tick<maximum();tick+=referenceTickInterval)
        {
            if(orientation()==Qt::Horizontal)
            {
                const int x=groove.left()+handle.width()/2+QStyle::sliderPositionFromValue(
                    minimum(),maximum(),tick,groove.width()-handle.width(),option.upsideDown);
                if(!handle.adjusted(-2,0,2,0).contains(QPoint(x,handle.center().y())))
                    painter.drawRoundedRect(QRectF(x-1,groove.center().y()-3,2,6),1,1);
            }
            else
            {
                const int y=groove.top()+handle.height()/2+QStyle::sliderPositionFromValue(
                    minimum(),maximum(),tick,groove.height()-handle.height(),option.upsideDown);
                if(!handle.adjusted(0,-2,0,2).contains(QPoint(handle.center().x(),y)))
                    painter.drawRoundedRect(QRectF(groove.center().x()-3,y-1,6,2),1,1);
            }
        }
    }
};
// Figma 3046:9282 and its category variants. Labels are product-facing;
// option identities and all value metadata continue to come from native VLC.
class SettingsSwitch : public QCheckBox
{
  public:
    SettingsSwitch(QWidget *parent, bool dark, const QColor &accent)
        : QCheckBox(parent), dark(dark), accent(accent)
    {
        setFixedSize(68, 32);
    }
    void setAppearance(bool isDark, const QColor &color)
    {
        dark=isDark;
        accent=color;
        update();
    }

  protected:
    void paintEvent(QPaintEvent *) override
    {
        QPainter p(this);
        p.setRenderHint(QPainter::Antialiasing);
        if (!isEnabled()) p.setOpacity(0.45);
        const bool on = isChecked();
        p.setPen(Qt::NoPen);
        p.setBrush(QColor(dark ? "#070707" : "#b9b9b9"));
        p.drawRoundedRect(QRectF(rect()), 5, 5);
        p.setBrush(on ? (accent == QColor("#d37918") ? QColor("#371f06") : accent.darker(400))
                      : QColor(dark ? "#191919" : "#c5c5c5"));
        p.drawRoundedRect(QRectF(on ? 3 : 32, 3, 33, 26), 3, 3);
        p.setBrush(on ? (accent == QColor("#d37918") ? QColor("#ab6314") : accent.darker(125))
                      : QColor(dark ? "#404040" : "#969696"));
        p.drawRoundedRect(QRectF(on ? 39 : 3, 3, 26, 26), 3, 3);
        QFont f = font();
        f.setPixelSize(12);
        p.setFont(f);
        p.setPen(on ? accent : QColor(dark ? "#6b6b6b" : "#676767"));
        p.drawText(QRect(on ? 10 : 36, 9, on ? 19 : 24, 15), Qt::AlignCenter,
                   on ? qtr("ON") : qtr("OFF"));
        if (hasFocus())
        {
            p.setBrush(Qt::NoBrush);
            p.setPen(QPen(accent, 2));
            p.drawRoundedRect(QRectF(1, 1, 66, 30), 4, 4);
        }
    }
    bool hitButton(const QPoint &point) const override
    {
        return rect().contains(point);
    }

  private:
    bool dark;
    QColor accent;
};
const char *const categoryNames[] = {
    N_("General"),   N_("Interface"), N_("Privacy"),     N_("Controls"),
    N_("Playback"),  N_("Video"),     N_("Audio"),       N_("Subtitles and OSD"),
    N_("Library"),   N_("Network"),   N_("Performance"), N_("Recording / Streaming"),
    N_("Extensions")};
const char *const categoryTitles[] = {N_("Global Settings"),
                                      N_("Interface Settings"),
                                      N_("Privacy Settings"),
                                      N_("Mouse, Keyboard & Remote Controls"),
                                      N_("Playback Preferences"),
                                      N_("Video Defaults"),
                                      N_("Audio Defaults"),
                                      N_("Subtitle Defaults"),
                                      N_("Playlists, Folders & Files"),
                                      N_("Network Connections & Security"),
                                      N_("Performance Settings"),
                                      N_("Recording, Casting & Streaming Out"),
                                      N_("Add-ons & Scripts")};
QPixmap sourceMask(const QString &path, const QColor &color, qreal dpr)
{
    QPixmap pixmap(QSize(24, 24) * dpr);
    pixmap.setDevicePixelRatio(dpr);
    pixmap.fill(Qt::transparent);
    QPainter painter(&pixmap);
    QSvgRenderer svg(path);
    svg.render(&painter, QRectF(0, 0, 24, 24));
    painter.setCompositionMode(QPainter::CompositionMode_SourceIn);
    painter.fillRect(QRectF(0, 0, 24, 24), color);
    return pixmap;
}
using Basic = PreferencesCatalog::Row;
constexpr auto &basicOptions = PreferencesCatalog::rows;
QString optionKey(const Basic &row)
{
    return QString::fromLatin1(row.key).section(QLatin1Char('/'), 0, 0);
}
const Basic *basicFor(const QString &key)
{
    for (const auto &basic : basicOptions)
        if (!QLatin1String(basic.key).startsWith(QLatin1Char('@')) && key == optionKey(basic))
            return &basic;
    return nullptr;
}
QString playbackScope(const QString &key)
{
    const auto *row=basicFor(key);
    if(!row || row->category<5 || row->category>7)return {};
    if(QStringList{"audio","spu","audio-language","sub-language","audio-desync","sub-delay",
                   "mmdevice-volume","mmdevice-audio-device","qt-max-volume","volume-save",
                   "sub-ass-style-override"}.contains(key))return {};
    return qtr("\n\nApplies to VLC playback. MPV uses separate rendering, filters and subtitle appearance.");
}
int categoryFor(const QString &key, int subcat, const QString &module)
{
    if (const auto *basic = basicFor(key))
        return basic->category;
    if (key == "qt-error-dialogs" || key == "logmode" || key == "stats")
        return 0;
    if (key.startsWith("key-") || key.startsWith("global-key-") ||
        subcat == SUBCAT_INTERFACE_HOTKEYS)
        return 3;
    if (key.startsWith("sout-") || key.startsWith("input-record-") || subcat / 100 == CAT_SOUT)
        return 11;
    if (key.contains("caching") || key.startsWith("http-") || key.startsWith("gnutls-") ||
        subcat == SUBCAT_ADVANCED_NETWORK || subcat == SUBCAT_INPUT_ACCESS ||
        subcat == SUBCAT_INPUT_STREAM_FILTER)
        return 9;
    if (subcat == SUBCAT_VIDEO_SUBPIC || subcat == SUBCAT_INPUT_SCODEC || module == "freetype")
        return 7;
    if (subcat / 100 == CAT_AUDIO || subcat == SUBCAT_INPUT_ACODEC)
        return 6;
    if (subcat / 100 == CAT_VIDEO)
        return 5;
    if (subcat / 100 == CAT_PLAYLIST || module == "medialibrary")
        return 8;
    if (subcat == SUBCAT_INPUT_VCODEC || subcat / 100 == CAT_ADVANCED)
        return 10;
    if (subcat / 100 == CAT_INPUT)
        return 4;
    if (key.startsWith("qt-") || subcat / 100 == CAT_INTERFACE)
        return 1;
    return 0; // Every public option has an owner, even modules without a subcategory.
}
QString defaultText(const module_config_t *c)
{
    if (c->i_type == CONFIG_ITEM_PASSWORD)
        return qtr("Hidden");
    if (CONFIG_CLASS(c->i_type) == CONFIG_ITEM_BOOL)
        return c->orig.i ? qtr("On") : qtr("Off");
    if (CONFIG_CLASS(c->i_type) == CONFIG_ITEM_FLOAT)
        return QString::number(c->orig.f);
    if (CONFIG_CLASS(c->i_type) == CONFIG_ITEM_INTEGER)
        return QString::number(c->orig.i);
    return c->orig.psz && *c->orig.psz ? qfu(c->orig.psz) : qtr("Automatic / empty");
}
QString optionLabel(const module_config_t *config)
{
    const QString key = qfu(config->psz_name);
    if (const auto *source = basicFor(key); source && !strchr(source->key, '/'))
        return qtr(source->label);
    if (key == "interact") return qtr("Show confirmation and error dialogs");
    if (key == "qt-updates-notif") return qtr("Check for updates automatically");
    // The source's developer toggle maps to Qt's existing diagnostic messages,
    // not an invented global development/debug mode. Native help explains it.
    if (key == "qt-verbose") return qtr("Developer messages");
    if (key == "file-logging") return qtr("Save a log");
    if (key == "logfile") return qtr("Log file");
    if (key == "log-verbose") return qtr("Log details");
    if (key == "qt-error-dialogs") return qtr("Show minor warnings");
    if (key == "stats") return qtr("Collect playback statistics");
    return qfut(config->psz_text);
}
struct PreviousConfigValue
{
    QString key;
    int type;
    QVariant value;
};
using ConfigValues = QVector<PreviousConfigValue>;
ConfigValues captureConfigValues(const QStringList &keys)
{
    ConfigValues previous;
    for (const auto &key : keys)
        if (auto *c = config_FindConfig(qtu(key)))
        {
            QVariant value;
            const int type = CONFIG_CLASS(c->i_type);
            if (type == CONFIG_ITEM_STRING)
            {
                char *text = config_GetPsz(qtu(key));
                if (text)
                    value = qfu(text);
                free(text);
            }
            else if (type == CONFIG_ITEM_FLOAT)
                value = config_GetFloat(qtu(key));
            else
                value = QVariant::fromValue<qlonglong>(config_GetInt(qtu(key)));
            previous.push_back({key, type, value});
        }
    return previous;
}
void restoreConfigValues(const ConfigValues &previous)
{
    for (const auto &p : previous)
    {
        if (p.type == CONFIG_ITEM_STRING)
            config_PutPsz(qtu(p.key), p.value.isValid() ? qtu(p.value.toString()) : nullptr);
        else if (p.type == CONFIG_ITEM_FLOAT)
            config_PutFloat(qtu(p.key), p.value.toFloat());
        else
            config_PutInt(qtu(p.key), p.value.toLongLong());
    }
}
} // namespace

PrefsDialog::PrefsDialog(QWindow *parent, qt_intf_t *intf) : QVLCDialog(parent, intf)
{
    setObjectName("redesignPreferences");
    setWindowTitle(qtr("VLC Settings"));
    setWindowRole("vlc-preferences");
    setWindowModality(Qt::WindowModal);
    setAttribute(Qt::WA_DeleteOnClose);
    setWindowFlags(windowFlags() | Qt::FramelessWindowHint);
    setAttribute(Qt::WA_TranslucentBackground);
    setMinimumSize(620, 420);
    applyRedesignDialogStyle(this, intf);
    setAutoFillBackground(false);
    applySettingsStyle();
    auto *layout = new QGridLayout(this);
    layout->setContentsMargins(8, 8, 8, 8);
    layout->setHorizontalSpacing(0);
    layout->setVerticalSpacing(8);
    search = new QLineEdit(this);
    search->setObjectName("preferencesSearch");
    search->setPlaceholderText(qtr("Search"));
    search->setAccessibleName(qtr("Search all settings"));
    search->setClearButtonEnabled(true);
    search->installEventFilter(this);
    search->addAction(QIcon(sourceMask(":/redesign/icons/search.svg", palette().text().color(),
                                       devicePixelRatioF())), QLineEdit::LeadingPosition)->setObjectName("preferencesSearchIcon");
    search->setFixedWidth(200);
    layout->addWidget(search, 0, 0);
    heading = new QLabel(qtr(categoryTitles[0]), this);
    heading->setObjectName("preferencesHeading");
    QFont headingFont = heading->font();
    headingFont.setPixelSize(16);
    heading->setFont(headingFont);
    heading->setWordWrap(true);
    heading->setSizePolicy(QSizePolicy::Ignored, QSizePolicy::Preferred);
    heading->setMaximumHeight(40);
    heading->setStyleSheet("font-size:16px;font-weight:400;");
    heading->setContentsMargins(32, 0, 0, 0);
    heading->installEventFilter(this);
    layout->addWidget(heading, 0, 1);
    auto *closeButton = new QPushButton(this);
    closeButton->setObjectName("preferencesClose");
    closeButton->setAccessibleName(qtr("Close settings without saving"));
    closeButton->setFixedSize(32, 32);
    closeButton->setStyleSheet("QPushButton{padding:4px;background:transparent;}QPushButton:hover{background:#222222;}");
    closeButton->setIconSize(QSize(24, 24));
    closeButton->setIcon(QIcon(
        sourceMask(":/redesign/icons/close.svg", palette().text().color(), devicePixelRatioF())));
    connect(closeButton, &QPushButton::clicked, this, &QDialog::reject);
    layout->addWidget(closeButton, 0, 2);
    categories = new QListWidget(this);
    categories->setObjectName("preferencesCategories");
    categories->setFixedWidth(200);
    categories->setHorizontalScrollBarPolicy(Qt::ScrollBarAlwaysOff);
    categories->setIconSize(QSize(24, 24));
    categories->setSpacing(4);
    categories->setStyleSheet(
        "QListWidget#preferencesCategories{padding:5px 2px;}"
        "QListWidget#preferencesCategories::item{padding:6px 10px;}"
        + QString("QListWidget#preferencesCategories::item:selected{color:%1;}"
                  "QListWidget#preferencesCategories::item:disabled{color:%2;}")
            .arg(property("figmaDark").toBool() ? "#eaeaea" : "#2e2e2e",
                 property("figmaDark").toBool() ? "#6b6b6b" : "#676767"));
    const char *icons[] = {"settings-general",
                           "settings-interface",
                           "settings-privacy",
                           "settings-controls",
                           "playback",
                           "video",
                           "audio",
                           "subtitles",
                           "folder",
                           "network",
                           "settings-general",
                           "settings-recording",
                           "settings-extensions"};
    const char *activeIcons[] = {"settings-general-active","settings-interface-active",
        "settings-privacy-active","settings-controls-active","settings-playback-active",
        "settings-video-active","settings-audio-active","settings-subtitles-active",
        "settings-library-active","settings-network-active","settings-general-active",
        "settings-recording-active","settings-extensions-active"};
    for (int i = 0; i < 13; ++i)
    {
        if (i == 0 || i == 4 || i == 9)
        {
            auto *section = new QListWidgetItem(qtr(i == 0   ? "App"
                                                    : i == 4 ? "Media"
                                                             : "System"),
                                                categories);
            section->setFlags(Qt::NoItemFlags);
            section->setSizeHint(QSize(188, 30));
            section->setData(Qt::UserRole, -1);
        }
        auto *item = new QListWidgetItem(qtr(i == 7 ? "Subtitles" : i == 11 ? "Recording" : categoryNames[i]), categories);
        item->setToolTip(qtr(categoryNames[i]));
        item->setSizeHint(QSize(188,40));
        item->setData(Qt::UserRole, i);
        QIcon icon;
        const QString path = ":/redesign/icons/" + QString::fromLatin1(icons[i]) + ".svg";
        const QString activePath = ":/redesign/icons/" + QString::fromLatin1(activeIcons[i]) + ".svg";
        item->setData(Qt::UserRole+1,path);
        item->setData(Qt::UserRole+2,activePath);
        icon.addPixmap(
            sourceMask(path, property("figmaDark").toBool() ? QColor("#8f8f8f") : QColor("#2e2e2e"),
                       devicePixelRatioF()),
            QIcon::Normal);
        icon.addPixmap(sourceMask(activePath, palette().color(QPalette::Highlight), devicePixelRatioF()),
                       QIcon::Selected);
        item->setIcon(icon);
    }
    categoryContainer = new QWidget(this);
    auto *navLayout = new QVBoxLayout(categoryContainer);
    navLayout->setContentsMargins(0, 8, 0, 0);
    navLayout->addWidget(categories);
    layout->addWidget(categoryContainer, 1, 0, 2, 1);
    pages = new QStackedWidget(this);
    pages->setObjectName("preferencesPages");
    layout->addWidget(pages, 1, 1, 1, 2);
    layout->setRowStretch(1, 1);
    layout->setRowMinimumHeight(0, 34);
    layout->setColumnStretch(1, 1);
    editFooter = new QWidget(this);
    editFooter->setObjectName("preferencesEditFooter");
    auto *footer = new QHBoxLayout(editFooter);
    footer->setContentsMargins(24, 0, 16, 0);
    auto *resetButton = new QPushButton(qtr("Reset Preferences"), this);
    resetButton->setObjectName("preferencesReset");
    resetButton->hide();
    connect(resetButton, &QPushButton::clicked, this, &PrefsDialog::reset);
    footer->addWidget(resetButton);
    footer->addStretch();
    auto *hint = new QLabel(qtr("Restart VLC to apply input, output and shortcut changes."), this);
    hint->setObjectName("preferencesRestartHint");
    hint->setWordWrap(true);
    hint->setMaximumHeight(36);
    hint->setSizePolicy(QSizePolicy::Ignored, QSizePolicy::Preferred);
    footer->addWidget(hint, 1);
    auto *buttons = new QDialogButtonBox(QDialogButtonBox::Save | QDialogButtonBox::Cancel, this);
    buttons->button(QDialogButtonBox::Save)->setObjectName("preferencesSave");
    buttons->button(QDialogButtonBox::Cancel)->setObjectName("preferencesCancel");
    connect(buttons, &QDialogButtonBox::accepted, this, &PrefsDialog::save);
    connect(buttons, &QDialogButtonBox::rejected, this, &QDialog::reject);
    footer->addWidget(buttons);
    footer->addWidget(new QSizeGrip(this));
    layout->addWidget(editFooter, 2, 1, 1, 2);
    editFooter->hide();
    connect(this,&PrefsDialog::draftChanged,this,&PrefsDialog::markEdited);
    connect(this,&PrefsDialog::draftChanged,this,&PrefsDialog::updateReferenceDependencies);
    inventory();
    results = new QTreeWidget(this);
    results->setObjectName("preferencesResults");
    results->installEventFilter(this);
    results->setHeaderLabels({qtr("Setting"), qtr("Category"), qtr("Module")});
    results->setRootIsDecorated(false);
    pages->addWidget(results);
    for (int i = 0; i < options.size(); ++i)
    {
        const auto &o = options[i];
        auto *r = new QTreeWidgetItem(
            results, {optionLabel(o.config), qtr(categoryNames[o.category]), o.module});
        r->setData(0, Qt::UserRole, i);
        r->setToolTip(0, qfu(o.config->psz_name));
    }
    connect(results, &QTreeWidget::itemActivated, this,
            [this](QTreeWidgetItem *item, int) { openResult(item); });
    connect(search, &QLineEdit::textChanged, this, &PrefsDialog::filter);
    connect(categories, &QListWidget::currentItemChanged, this,
            [this](QListWidgetItem *current, QListWidgetItem *)
            {
                if (current && current->data(Qt::UserRole).toInt() >= 0)
                {
                    search->clear();
                    selectCategory(current->data(Qt::UserRole).toInt());
                }
            });
    categories->setCurrentRow(1);
    const int initial = config_GetInt("qt-initial-prefs-view");
    if (initial == 1)
    {
        if (auto *advanced = categoryPages[0]->findChild<QPushButton *>("preferencesAdvanced0"))
            advanced->setChecked(true);
    }
    else if (initial == 2)
    {
        pages->setCurrentWidget(results);
        heading->setText(qtr("All settings"));
    }
    const QSize available = screen()->availableGeometry().size() - QSize(40, 40);
    resize(QSize(1048, 865).boundedTo(available));
    if(intf->p_mi){
        connect(intf->p_mi,&MainCtx::redesignAccentChanged,this,&PrefsDialog::refreshAppearance);
        connect(intf->p_mi->getColorScheme(),&ColorSchemeModel::currentChanged,this,&PrefsDialog::refreshAppearance);
    }
#ifdef VLC_PLAYER_DIAGNOSTICS
    if (!qEnvironmentVariableIsEmpty("VLC_PLAYER_DIAGNOSTICS_DIR") &&
        qEnvironmentVariableIntValue("VLC_PLAYER_DIAGNOSTICS_OFFSCREEN") == 1)
    {
        QRect desktopBounds;
        for (auto *display : QGuiApplication::screens()) desktopBounds |= display->geometry();
        setAttribute(Qt::WA_ShowWithoutActivating);
        setWindowFlag(Qt::WindowDoesNotAcceptFocus);
        move(desktopBounds.right() + 512, desktopBounds.top() + 64);
    }
#endif
}

PrefsDialog::~PrefsDialog()
{
    if(pluginScan)
    {
        // Application shutdown can bypass the dialog's close guard. Preserve
        // the exact cache writer through its real exit instead of allowing
        // QProcess destruction to kill it midway through the cache update.
        disconnect(pluginScan,nullptr,this,nullptr);
        if(pluginScan->state()!=QProcess::NotRunning)pluginScan->waitForFinished(-1);
    }
    if (windowEffects)
    {
        if (windowEffects->p_module)
            module_unneed(windowEffects, windowEffects->p_module);
        vlc_object_delete(windowEffects);
    }
    qDeleteAll(controls);
    // Controls use config metadata until their destruction; arrays own metadata,
    // while values are owned by VLC and are never overwritten in this dialog.
    for (auto *config : configs)
        module_config_free(config);
}
void PrefsDialog::refreshAppearance()
{
    // Repaint existing editors without rebuilding them or losing unsaved values.
    const bool dark=property("figmaDark").toBool();
    const QColor foreground=palette().text().color(), accent=palette().color(QPalette::Highlight);
    setAutoFillBackground(false);
    applySettingsStyle();
    categories->setStyleSheet(
        "QListWidget#preferencesCategories{padding:5px 2px;}"
        "QListWidget#preferencesCategories::item{padding:6px 10px;}"
        +QString("QListWidget#preferencesCategories::item:selected{color:%1;}"
                 "QListWidget#preferencesCategories::item:disabled{color:%2;}")
             .arg(dark?"#eaeaea":"#2e2e2e",dark?"#6b6b6b":"#676767"));
    for(int i=0;i<categories->count();++i){
        auto *item=categories->item(i);
        const auto path=item->data(Qt::UserRole+1).toString();
        if(path.isEmpty())continue;
        QIcon icon;
        icon.addPixmap(sourceMask(path,foreground,devicePixelRatioF()),QIcon::Normal);
        icon.addPixmap(sourceMask(item->data(Qt::UserRole+2).toString(),accent,devicePixelRatioF()),QIcon::Selected);
        item->setIcon(icon);
    }
    if(auto *icon=search->findChild<QAction *>("preferencesSearchIcon"))
        icon->setIcon(QIcon(sourceMask(":/redesign/icons/search.svg",foreground,devicePixelRatioF())));
    if(auto *close=findChild<QPushButton *>("preferencesClose"))
        close->setIcon(QIcon(sourceMask(":/redesign/icons/close.svg",foreground,devicePixelRatioF())));
    for(auto *check:findChildren<QCheckBox *>())
        if(auto *toggle=dynamic_cast<SettingsSwitch *>(check))toggle->setAppearance(dark,accent);
    for(auto *button:findChildren<QToolButton *>()){
        if(!button->property("redesignAccentSwatch").toBool())continue;
        button->setStyleSheet(QString("QToolButton{background:transparent;padding:0;border:0;}"
            "QToolButton:checked{background:%1;}QToolButton:focus{border:1px solid %2;}")
            .arg(accent.darker(400).name(),accent.name()));
    }
    for(auto *button:findChildren<QPushButton *>()){
        if(!button->objectName().startsWith("preferencesTheme"))continue;
        button->setStyleSheet(QString("QPushButton:checked{background:%1;color:%2;}")
            .arg(accent.darker(400).name(),accent.name()));
    }
    update();
}
void PrefsDialog::applySettingsStyle()
{
    const bool dark=property("figmaDark").toBool();
    const auto accent=palette().color(QPalette::Highlight);
    setStyleSheet(styleSheet()+QString(
        "PrefsDialog#redesignPreferences{background:transparent;}"
        "PrefsDialog#redesignPreferences QLineEdit{background:%1;border:2px solid %2;padding:6px 12px;}"
        "PrefsDialog#redesignPreferences QLineEdit#preferencesSearch{background:%2;border:0;}"
        "PrefsDialog#redesignPreferences QComboBox{border:2px solid %1;padding-top:6px;padding-bottom:6px;}"
        "PrefsDialog#redesignPreferences QAbstractSpinBox QLineEdit,PrefsDialog#redesignPreferences QComboBox QLineEdit{border:0;background:transparent;padding:0;min-height:0;}"
        "PrefsDialog#redesignPreferences QSlider::groove:horizontal{height:14px;background:%1;border-radius:4px;}"
        "PrefsDialog#redesignPreferences QSlider::sub-page:horizontal{background:%3;border-radius:4px;}"
        "PrefsDialog#redesignPreferences QSlider::handle:horizontal{width:8px;background:%4;border-radius:4px;margin:-3px 0;}"
        "PrefsDialog#redesignPreferences QSlider::groove:vertical{width:14px;background:%1;border-radius:4px;}"
        "PrefsDialog#redesignPreferences QSlider::sub-page:vertical{background:%3;border-radius:4px;}"
        "PrefsDialog#redesignPreferences QSlider::handle:vertical{height:8px;background:%4;border-radius:4px;margin:0 -5px;}"
        "PrefsDialog#redesignPreferences QPushButton:checked{background:%3;color:%4;}"
        ).arg(dark?"#070707":"#eeeeee",dark?"#191919":"#d5d5d5",accent.darker(400).name(),accent.name()));
}
void PrefsDialog::showEvent(QShowEvent *event)
{
    QVLCDialog::showEvent(event);
    if (!windowEffects && var_InheritBool(p_intf, "qt-backdrop-blur"))
    {
        windowEffects = vlc_object_create<WindowEffectsModule>(p_intf);
        if (windowEffects)
            windowEffects->p_module = module_need(windowEffects, "qtwindoweffects", nullptr, false);
    }
    blurBehind = windowEffects && windowEffects->p_module && windowHandle() &&
                 windowEffects->isEffectAvailable(windowHandle(), WindowEffectsModule::BlurBehind);
    if (blurBehind)
        windowEffects->setBlurBehind(windowHandle(), true, {});
    update();
}
void PrefsDialog::hideEvent(QHideEvent *event)
{
    if (blurBehind && windowHandle())
        windowEffects->setBlurBehind(windowHandle(), false, {});
    blurBehind = false;
    QVLCDialog::hideEvent(event);
}
void PrefsDialog::paintEvent(QPaintEvent *)
{
    QPainter painter(this);
    painter.setCompositionMode(QPainter::CompositionMode_Source);
    painter.fillRect(rect(), Qt::transparent);
    painter.setCompositionMode(QPainter::CompositionMode_SourceOver);
    painter.setRenderHint(QPainter::Antialiasing);
    painter.setPen(Qt::NoPen);
    // The transparent root style intentionally clears QPalette::Window. Keep
    // the measured source tint independent of that style-engine palette role.
    QColor fill(property("figmaDark").toBool() ? "#0e0e0e" : "#e7e7e7");
    // Figma's 95% surface has a native blur backdrop where the platform offers
    // one. Unsupported/disabled effects keep an opaque, readable surface.
    if (blurBehind) fill.setAlphaF(0.95);
    painter.setBrush(fill);
    painter.drawRoundedRect(QRectF(rect()), 14, 14);
    QPainterPath shape;
    shape.addRoundedRect(QRectF(rect()), 14, 14);
    painter.setClipPath(shape);
    painter.fillRect(QRect(0, 0, width(), 50),
                     property("figmaDark").toBool() ? QColor("#070707") : QColor("#d5d5d5"));
}
void PrefsDialog::updateDialogShape()
{
#ifdef _WIN32
    // The Windows11 backdrop ignores the effect module's QRegion. Clip the
    // native window as well as the paint, so acrylic cannot fill its corners.
    QPainterPath shape;
    shape.addRoundedRect(QRectF(rect()), 14, 14);
    setMask(QRegion(shape.toFillPolygon().toPolygon()));
#endif
}
void PrefsDialog::resizeEvent(QResizeEvent *event)
{
    QVLCDialog::resizeEvent(event);
    updateDialogShape();
    updateResponsiveLayout();
}
void PrefsDialog::updateResponsiveLayout()
{
    if (!categories || !pages) return;
    const bool compact = width() < 900;
    if (auto *hint = findChild<QLabel *>("preferencesRestartHint"))
        hint->setVisible(!compact);
    // Keep the reference layout at its normal size. In a narrow window the
    // real native value editor goes below its label instead of forcing the
    // whole page wider than the scroll viewport. Boolean switches still fit.
    for (auto *row : findChildren<QWidget *>())
    {
        if (!row->objectName().startsWith("preference-")) continue;
        const bool stacked = row->property("compactPreference").toBool();
        if (stacked == compact) continue;
        auto *grid = qobject_cast<QGridLayout *>(row->layout());
        if (!grid) continue;
        auto *item = grid->itemAtPosition(stacked ? 1 : 0, stacked ? 0 : 10);
        if (!item || !item->widget() || qobject_cast<QCheckBox *>(item->widget())) continue;
        QWidget *editor = item->widget();
        auto *help = grid->itemAtPosition(stacked ? 2 : 1, 0);
        QWidget *description = help ? help->widget() : nullptr;
        const bool accent = row->objectName() == "preference-qt-accent-color";
        if (accent)
        {
            auto *custom = row->findChild<QLineEdit *>("value-qt-accent-color");
            grid->removeWidget(custom);
            grid->addWidget(custom, compact ? 3 : 2, 0, 1, 12);
        }
        grid->removeWidget(editor);
        if (description) grid->removeWidget(description);
        grid->addWidget(editor, compact ? 1 : 0, compact ? 0 : 10, 1,
                        compact ? 12 : 1, Qt::AlignRight);
        if (description) grid->addWidget(description, compact ? 2 : 1, 0, 1, 12);
        grid->setColumnStretch(0, compact || accent ? 1 : 454);
        grid->setColumnStretch(10, compact || accent ? 0 : 320);
        row->setProperty("compactPreference", compact);
    }
    if (auto *bands=findChild<QWidget *>("preferencesEqualizerBands"))
    {
        auto *grid=qobject_cast<QGridLayout *>(bands->layout());
        const int columns=compact ? 5 : 11;
        for(int i=0;i<11;++i)grid->setColumnStretch(i,i<columns ? 1 : 0);
        for(int row=0;row<18;++row)grid->setRowMinimumHeight(row,0);
        for(int group=0;group<(11+columns-1)/columns;++group)
        {
            const int base=6*group;
            grid->setRowMinimumHeight(base+1,33);
            grid->setRowMinimumHeight(base+3,12);
            if(group+1<(11+columns-1)/columns)grid->setRowMinimumHeight(base+5,24);
        }
        for(int i=-1;i<10;++i)
        {
            const QString suffix=i<0 ? QStringLiteral("Preamp") : QString::number(i);
            auto *label=bands->findChild<QLabel *>("equalizerFrequency"+suffix);
            auto *slider=bands->findChild<QSlider *>(i<0 ? "preferencesEqualizerPreamp" : "preferencesEqualizerBand"+suffix);
            auto *value=bands->findChild<QDoubleSpinBox *>("equalizerValue"+suffix);
            grid->removeWidget(label);grid->removeWidget(slider);grid->removeWidget(value);
            const int column=(i+1)%columns,base=6*((i+1)/columns);
            grid->addWidget(slider,base,column,Qt::AlignHCenter);
            grid->addWidget(label,base+2,column);
            grid->addWidget(value,base+4,column);
        }
    }
}
void PrefsDialog::inventory()
{
    size_t count = 0;
    module_t **modules = module_list_get(&count);
    QSet<QString> keys;
    for (size_t i = 0; i < count; ++i)
    {
        unsigned n = 0;
        auto *cfg = module_config_get(modules[i], &n);
        configs.push_back(cfg);
        int subcat = SUBCAT_UNKNOWN;
        QString group = qfut(module_GetShortName(modules[i]));
        const QString module = qfu(module_get_object(modules[i]));
        for (unsigned j = 0; j < n; ++j)
        {
            auto *c = cfg + j;
            if (c->i_type == CONFIG_SUBCATEGORY)
            {
                subcat = c->value.i;
                continue;
            }
            if (c->i_type == CONFIG_SECTION)
            {
                group = qfut(c->psz_text);
                continue;
            }
            if (!CONFIG_ITEM(c->i_type) || !c->psz_name || keys.contains(qfu(c->psz_name)))
                continue;
            keys.insert(qfu(c->psz_name));
            if (c->i_type == CONFIG_ITEM_KEY)
                continue;
            const auto *basic = basicFor(qfu(c->psz_name));
            options.push_back({c, module, basic ? qtr(basic->group) : group,
                               categoryFor(qfu(c->psz_name), subcat, module), basic != nullptr});
        }
    }
    module_list_free(modules);
    std::stable_sort(options.begin(), options.end(),
                     [](const Option &a, const Option &b)
                     {
                         const auto *aa = basicFor(qfu(a.config->psz_name)),
                                    *bb = basicFor(qfu(b.config->psz_name));
                         if (aa && bb)
                             return aa < bb;
                         if (aa || bb)
                             return aa != nullptr;
                         const int group = a.group.compare(b.group, Qt::CaseInsensitive);
                         return group ? group < 0
                                      : QString::compare(qfut(a.config->psz_text),
                                                         qfut(b.config->psz_text),
                                                         Qt::CaseInsensitive) < 0;
                     });
    QStringList inventory = keys.values();
    inventory.sort();
    setProperty("optionKeys", inventory);
    setProperty("optionCount", inventory.size());
}
QVariant PrefsDialog::draftValue(const QString &key)
{
    if (draftValues.contains(key)) return draftValues.value(key);
    const auto *config = config_FindConfig(qtu(key));
    if (!config) return {};
    QVariant value;
    switch (CONFIG_CLASS(config->i_type))
    {
        case CONFIG_ITEM_STRING:
        {
            char *text = config_GetPsz(qtu(key));
            value = text ? qfu(text) : QString();
            free(text);
            break;
        }
        case CONFIG_ITEM_FLOAT: value = config_GetFloat(qtu(key)); break;
        default: value = QVariant::fromValue<qlonglong>(config_GetInt(qtu(key))); break;
    }
    draftValues.insert(key, value);
    return value;
}
void PrefsDialog::stageValue(const QString &key, const QVariant &value)
{
    if (!config_FindConfig(qtu(key)) || draftValue(key) == value) return;
    draftValues.insert(key, value);
    emit draftChanged(key, value);
    if (key == "equalizer-preset")
        for (const auto &preset : eqz_preset_10b)
            if (value.toString() == QLatin1String(preset.psz_name))
            {
                QStringList bands;
                for (int i=0;i<preset.i_band;++i) bands.append(QString::number(preset.f_amp[i],'f',7));
                stageValue("equalizer-bands",bands.join(' '));
                stageValue("equalizer-preamp",preset.f_preamp);
                break;
            }
    if (QStringList{"hue","brightness","contrast","saturation","gamma"}.contains(key))
    {
        auto filters=draftValue("video-filter").toString().split(':',Qt::SkipEmptyParts);
        if (!filters.contains("adjust")) { filters.append("adjust");stageValue("video-filter",filters.join(':')); }
    }
    if (key == "pitch-shift" && value.toDouble()!=0)
    {
        auto filters=draftValue("audio-filter").toString().split(':',Qt::SkipEmptyParts);
        if (!filters.contains("scaletempo_pitch")) { filters.append("scaletempo_pitch");stageValue("audio-filter",filters.join(':')); }
    }
}
void PrefsDialog::markEdited()
{
    if (editFooter) editFooter->show();
}
void PrefsDialog::updateReferenceDependencies()
{
    auto enabled = [this](const QString &key,bool on) {
        for (auto *row : findChildren<QWidget *>())
            if (row->property("preferenceKey").toString()==key)
            if (auto *value=row->findChild<QWidget *>(row->property("valueId").toString()))
            {
                auto *group=row->findChild<QWidget *>(row->property("editorId").toString());
                (group ? group : value)->setEnabled(on);
            }
    };
    const bool logging=draftValue("file-logging").toBool();
    for (const auto *key : {"logfile","log-verbose","logmode"})enabled(key,logging);
    const auto interfaces=draftValue("extraintf").toString().split(':',Qt::SkipEmptyParts);
    for (const auto *key : {"lastfm-username","lastfm-password","scrobbler-url"})enabled(key,interfaces.contains("audioscrobbler"));
    enabled("http-port",interfaces.contains("http"));
    enabled("skins2-last",draftValue("intf").toString().contains("skins2"));
    const bool tray=draftValue("qt-system-tray").toBool();
    enabled("qt-start-minimized",tray);
    enabled("qt-notification-duration",tray && draftValue("qt-notification").toInt()!=NOTIFICATION_NEVER);
    enabled("mouse-hide-timeout",draftValue("qt-controls-visibility").toInt()!=2);
    enabled("qt-fs-sensitivity",draftValue("qt-fs-controller").toBool());
    enabled("mmdevice-volume",!draftValue("volume-save").toBool());
    enabled("effect-width",!draftValue("qt-visualization-fit").toBool());
    enabled("effect-height",!draftValue("qt-visualization-fit").toBool());
    enabled("norm-max-level",draftValue("audio-filter").toString().split(':').contains("normvol"));
    const bool background=draftValue("freetype-background-opacity").toInt()>0;
    enabled("freetype-background-color",background);
    // The background selector stays enabled even when its opacity is zero.
    for (auto *row : findChildren<QWidget *>("preference-freetype-background-opacity"))
        if (row->property("referenceView").toString()=="freetype-background-opacity")
            if (auto *editor=row->findChild<QWidget *>("editor-freetype-background-opacity"))editor->setEnabled(background);
}
void PrefsDialog::addEqualizer(QVBoxLayout *form)
{
    auto *bandsWidget=new QWidget(this);
    bandsWidget->setObjectName("preferencesEqualizerBands");
    auto *grid=new QGridLayout(bandsWidget);
    // Original 784px reference: eleven 60px columns, 8px gutters and
    // 22px exterior margins. Wrapped groups keep each slider/label/value
    // together without changing the native equalizer's band identities.
    grid->setContentsMargins(22,12,22,20);
    grid->setHorizontalSpacing(8);
    grid->setVerticalSpacing(0);
    const char *frequencies[]={"60 Hz","170 Hz","310 Hz","600 Hz","1 kHz","3 kHz","6 kHz","12 kHz","14 kHz","16 kHz"};
    for(int i=-1;i<10;++i)
    {
        const QString suffix=i<0 ? QStringLiteral("Preamp") : QString::number(i);
        auto *slider=new SettingsSlider(bandsWidget,Qt::Vertical);
        slider->setObjectName(i<0 ? "preferencesEqualizerPreamp" : "preferencesEqualizerBand"+suffix);
        slider->setAccessibleName(i<0 ? qtr("Equalizer preamp") : qtr("Equalizer %1").arg(frequencies[i]));
        slider->setRange(-200,200);
        slider->setFixedHeight(320);
        slider->setTickPosition(QSlider::NoTicks);
        slider->referenceTickInterval=50;
        auto *name=new QLabel(i<0 ? qtr("Preamp") : QString::fromLatin1(frequencies[i]),bandsWidget);
        name->setObjectName("equalizerFrequency"+suffix);
        name->setAlignment(Qt::AlignCenter);
        name->setFixedHeight(17);
        name->setStyleSheet("font-size:14px;");
        auto *value=new QDoubleSpinBox(bandsWidget);
        value->setObjectName("equalizerValue"+suffix);
        value->setAccessibleName(slider->accessibleName());
        value->setRange(-20,20);
        value->setDecimals(1);
        value->setSuffix(qtr(" dB"));
        value->setButtonSymbols(QAbstractSpinBox::NoButtons);
        value->setStyleSheet("padding:2px;font-size:12px;");
        value->setMinimumWidth(0);
        value->setFixedHeight(34);
        value->setSizePolicy(QSizePolicy::Ignored,QSizePolicy::Fixed);
        grid->addWidget(slider,0,i+1,Qt::AlignHCenter);
        grid->addWidget(name,2,i+1);
        grid->addWidget(value,4,i+1);
        grid->setColumnStretch(i+1,1);
        auto sync=[this,i,slider,value](const QString &key,const QVariant &) {
            if(key!=(i<0 ? "equalizer-preamp" : "equalizer-bands"))return;
            const auto bands=draftValue(key).toString().simplified().split(' ',Qt::SkipEmptyParts);
            const double gain=i<0 ? draftValue(key).toDouble() : i<bands.size() ? bands[i].toDouble() : 0;
            const QSignalBlocker a(slider),b(value);
            slider->setValue(qRound(gain*10));value->setValue(gain);
        };
        sync(i<0 ? "equalizer-preamp" : "equalizer-bands",{});
        connect(this,&PrefsDialog::draftChanged,bandsWidget,sync);
        connect(slider,&QSlider::valueChanged,value,[value](int gain){value->setValue(gain/10.0);});
        connect(value,&QDoubleSpinBox::valueChanged,bandsWidget,[this,i](double gain){
            if(i<0) { stageValue("equalizer-preamp",gain);return; }
            auto bands=draftValue("equalizer-bands").toString().simplified().split(' ',Qt::SkipEmptyParts);
            while(bands.size()<10)bands.append("0");
            bands[i]=QString::number(gain,'f',1);
            stageValue("equalizer-bands",bands.join(' '));
        });
    }
    form->addWidget(bandsWidget);
    updateResponsiveLayout();
}
void PrefsDialog::addOption(QVBoxLayout *parent, const Option &o,
                          const PreferencesCatalog::Row *presentation)
{
    const QString key = qfu(o.config->psz_name);
    const QString viewKey = presentation ? QString::fromLatin1(presentation->key).replace('/','-') : "native-" + key;
    const QString labelText = presentation ? qtr(presentation->label) : optionLabel(o.config);
    const QColor accent = p_intf->p_mi ? p_intf->p_mi->getRedesignAccent() : QColor("#d37918");
    auto *row = new QWidget(this);
    row->setObjectName("preference-" + viewKey);
    row->setProperty("preferenceKey",key);
    row->setProperty("valueId","value-"+viewKey);
    row->setProperty("editorId","editor-"+viewKey);
    row->setFocusPolicy(Qt::StrongFocus);
    auto *grid = new QGridLayout(row);
    grid->setContentsMargins(0, 0, 0, 0);
    grid->setRowMinimumHeight(0,34);
    // Native controls use column 10. Empty legacy columns must not each add
    // another gap; retain one deliberate label/value gutter.
    grid->setHorizontalSpacing(0);
    grid->setColumnMinimumWidth(1, 10);
    grid->setColumnStretch(0, 454);
    grid->setColumnStretch(10, 320);
    ConfigControl *control = nullptr;
    if (key == "qt-accent-color")
    {
        grid->setColumnStretch(0, 1);
        grid->setColumnStretch(10, 0);
        auto *label = new QLabel(qtr("Accent color"), row);
        grid->addWidget(label, 0, 0);
        auto *value = new QLineEdit(row);
        value->setObjectName("value-qt-accent-color");
        value->setAccessibleName(qtr("Custom accent color or system / default"));
        value->hide();
        grid->addWidget(value, 2, 0, 1, 12);
        control = new StringConfigControl(o.config, label, value);
        auto *palette = new QWidget(row);
        auto *swatches = new QHBoxLayout(palette);
        swatches->setContentsMargins(0, 0, 0, 0);
        swatches->setSpacing(4);
        auto *selection = new QButtonGroup(row);
        for (const char *color : {"#d37918", "#a4381f", "#8d7c16", "#167329", "#0e7d95", "#1b4e9d",
                                  "#7633a8", "#a4347f", "#808080"})
        {
            auto *button = new QToolButton(palette);
            button->setProperty("redesignAccentSwatch",true);
            button->setFixedSize(32, 34);
            button->setCheckable(true);
            button->setAccessibleName(qtr("Accent color %1").arg(color));
            QPixmap square(20, 20);
            square.fill(QColor(color));
            button->setIcon(QIcon(square));
            button->setIconSize(QSize(20, 20));
            button->setStyleSheet(
                QString("QToolButton{background:transparent;padding:0;border:0;}"
                        "QToolButton:checked{background:%1;}"
                        "QToolButton:focus{border:1px solid %2;}")
                    .arg(accent.darker(400).name(), accent.name()));
            selection->addButton(button);
            button->setChecked(QColor(color) == accent);
            connect(button, &QToolButton::clicked, row,
                    [value, color]() { value->setText(QString::fromLatin1(color)); });
            swatches->addWidget(button);
        }
        grid->addWidget(palette, 0, 10, Qt::AlignRight);
    }
    else if (o.config->i_type == CONFIG_ITEM_MODULE_LIST || o.config->i_type == CONFIG_ITEM_MODULE_LIST_CAT)
    {
        auto *label=new QLabel(labelText,row);
        auto *line=new QLineEdit(row);
        control=new StringConfigControl(o.config,label,line);
        grid->addWidget(label,0,0);
        grid->addWidget(line,0,10);
    }
    else if (key == "mmdevice-audio-device")
    {
        auto *label=new QLabel(labelText,row);
        auto *combo=new QComboBox(row);
        control=new StringListConfigControl(o.config,label,combo);
        grid->addWidget(label,0,0);
        grid->addWidget(combo,0,10);
    }
    else if (o.config->i_type == CONFIG_ITEM_BOOL)
    {
        grid->setColumnStretch(0, 1);
        grid->setColumnStretch(10, 0);
        auto *label = new QLabel(labelText, row);
        label->setWordWrap(true);
        grid->addWidget(label, 0, 0);
        auto *toggle = new SettingsSwitch(row, property("figmaDark").toBool(),
                                          accent);
        toggle->setAccessibleName(label->text());
        toggle->setObjectName("value-" + viewKey);
        grid->addWidget(toggle, 0, 10, Qt::AlignRight);
        control = new BoolConfigControl(o.config, label, toggle);
    }
    else
        control = ConfigControl::createControl(o.config, row, grid, 0);
    if (!control)
    {
        delete row;
        return;
    }
    grid->setColumnMinimumWidth(1, 10);
    if (o.config->i_type == CONFIG_ITEM_FONT)
        if (auto *font = row->findChild<QFontComboBox *>())
        {
            grid->removeWidget(font);
            grid->addWidget(font, 0, 10);
        }
    if (auto *item = grid->itemAtPosition(0, 10); item && item->layout())
    {
        // Native file/directory editors group the line edit and Browse button
        // in a layout. Give that existing group a widget boundary so it can
        // move below its label together in the narrow preferences layout.
        auto *editorLayout = item->layout();
        grid->removeItem(editorLayout);
        editorLayout->setParent(nullptr);
        auto *group = new QWidget(row);
        group->setObjectName("editor-" + viewKey);
        group->setProperty("preferenceEditorGroup", true);
        group->setLayout(editorLayout);
        for (auto *button : group->findChildren<QPushButton *>()) button->setFixedHeight(34);
        if (auto *line = group->findChild<QLineEdit *>())
            line->setObjectName("value-" + viewKey);
        grid->addWidget(group, 0, 10);
    }
    if (auto *item = grid->itemAtPosition(0, 10); item && item->widget() &&
        o.config->i_type != CONFIG_ITEM_BOOL && key != "qt-accent-color")
    {
        auto *editor = item->widget();
        if (!editor->property("preferenceEditorGroup").toBool())
            editor->setObjectName("value-" + viewKey);
        if (editor->property("preferenceEditorGroup").toBool() ||
            qobject_cast<QLineEdit *>(editor) || qobject_cast<QComboBox *>(editor) ||
            qobject_cast<QAbstractSpinBox *>(editor))
            editor->setFixedHeight(34);
        grid->setAlignment(editor, Qt::Alignment());
        editor->setSizePolicy(QSizePolicy::Expanding, QSizePolicy::Fixed);
    }
    control->setParent(row);
    if (auto *spin=row->findChild<QSpinBox *>())
    {
        if (key.endsWith("-jump-size")) spin->setSuffix(qtr(" s"));
        else if (key.endsWith("-caching") || key=="clock-jitter") spin->setSuffix(qtr(" ms"));
    }
    controls.push_back(control);
    connect(control,&ConfigControl::changed,this,&PrefsDialog::markEdited);
    {
        stagedControls.insert(control);
        auto value = [control]() -> QVariant {
            if (auto *integer = dynamic_cast<VIntConfigControl *>(control))
                return QVariant::fromValue<qlonglong>(integer->getValue());
            if (auto *real = dynamic_cast<VFloatConfigControl *>(control)) return real->getValue();
            if (auto *string = dynamic_cast<VStringConfigControl *>(control)) return string->getValue();
            return {};
        };
        auto changed = [this, key, value]() { stageValue(key, value()); };
        for (auto *line : row->findChildren<QLineEdit *>())
            connect(line, &QLineEdit::textChanged, row, changed);
        for (auto *combo : row->findChildren<QComboBox *>())
            connect(combo, &QComboBox::currentIndexChanged, row, changed);
        for (auto *spin : row->findChildren<QSpinBox *>())
            connect(spin, &QSpinBox::valueChanged, row, changed);
        for (auto *spin : row->findChildren<QDoubleSpinBox *>())
            connect(spin, &QDoubleSpinBox::valueChanged, row, changed);
        for (auto *button : row->findChildren<QAbstractButton *>())
        {
            if (button->isCheckable()) connect(button, &QAbstractButton::toggled, row, changed);
            else if (o.config->i_type == CONFIG_ITEM_RGB)
                connect(button, &QAbstractButton::clicked, row, changed);
        }
        QWidget *editor = row->findChild<QWidget *>("value-" + viewKey);
        auto sync = [editor, key](const QString &updated, const QVariant &value) {
            if (!editor || updated != key) return;
            const QSignalBlocker blocker(editor);
            if (auto *font = qobject_cast<QFontComboBox *>(editor)) font->setCurrentFont(QFont(value.toString()));
            else if (auto *combo = qobject_cast<QComboBox *>(editor))
            {
                int index = combo->findData(value);
                if (index < 0) index = combo->findText(value.toString());
                if (index < 0) { combo->addItem(value.toString(), value); index = combo->count()-1; }
                combo->setCurrentIndex(index);
            }
            else if (auto *spin = qobject_cast<QSpinBox *>(editor)) spin->setValue(value.toInt());
            else if (auto *spin = qobject_cast<QDoubleSpinBox *>(editor)) spin->setValue(value.toDouble());
            else if (auto *button = qobject_cast<QAbstractButton *>(editor); button && button->isCheckable())
                button->setChecked(value.toBool());
            else if (auto *line = qobject_cast<QLineEdit *>(editor)) line->setText(value.toString());
        };
        sync(key, draftValue(key));
        connect(this, &PrefsDialog::draftChanged, row, sync);
    }
    auto *help = new QToolButton(row);
    help->setIcon(QIcon(sourceMask(":/redesign/icons/settings-info.svg", palette().text().color(),
                                   devicePixelRatioF())));
    help->setIconSize(QSize(16, 16));
    help->setStyleSheet("padding:0;background:transparent");
    help->setObjectName("help-" + viewKey);
    help->setAccessibleName(qtr("Help for %1").arg(optionLabel(o.config)));
    help->setFixedSize(16, 16);
    if (auto *label = qobject_cast<QLabel *>(
            grid->itemAtPosition(0, 0) ? grid->itemAtPosition(0, 0)->widget() : nullptr))
    {
        label->setText(labelText);
        grid->removeWidget(label);
        auto *labelGroup = new QWidget(row);
        auto *labelLayout = new QHBoxLayout(labelGroup);
        labelLayout->setContentsMargins(0, 0, 0, 0);
        labelLayout->setSpacing(8);
        auto *sourceLabel = new SettingsLabel(label->text(), row);
        sourceLabel->setToolTip(label->toolTip());
        sourceLabel->setBuddy(label->buddy());
        label->hide();
        labelLayout->addWidget(sourceLabel);
        labelLayout->addWidget(help);
        labelLayout->addStretch();
        grid->addWidget(labelGroup, 0, 0);
    }
    else
        grid->addWidget(help, 0, 11, Qt::AlignTop);
    QString text = qfut(o.config->psz_longtext ? o.config->psz_longtext : o.config->psz_text);
    text += qtr("\n\nDefault: %1").arg(defaultText(o.config));
    if ((CONFIG_CLASS(o.config->i_type) == CONFIG_ITEM_INTEGER ||
         CONFIG_CLASS(o.config->i_type) == CONFIG_ITEM_FLOAT) &&
        o.config->i_type != CONFIG_ITEM_BOOL)
    {
        if (CONFIG_CLASS(o.config->i_type) == CONFIG_ITEM_INTEGER &&
            (o.config->min.i || o.config->max.i))
            text += qtr("\nRange: %1 to %2").arg(o.config->min.i).arg(o.config->max.i);
        if (CONFIG_CLASS(o.config->i_type) == CONFIG_ITEM_FLOAT &&
            (o.config->min.f || o.config->max.f))
            text += qtr("\nRange: %1 to %2").arg(o.config->min.f).arg(o.config->max.f);
    }
    text += qtr("\n\nOption: %1\nModule: %2\nSaved in VLC preferences. Input, output and module "
                "changes take effect after restarting playback or VLC; shortcut changes require "
                "restarting VLC.")
                .arg(key, o.module);
    text += playbackScope(key);
    auto *description = new QLabel(text, row);
    description->setObjectName("description-" + viewKey);
    description->setTextFormat(Qt::PlainText);
    description->setWordWrap(true);
    description->setTextInteractionFlags(Qt::TextSelectableByMouse);
    description->hide();
    grid->addWidget(description, 1, 0, 1, 12);
    connect(help, &QToolButton::clicked, description,
            [description, row, key]()
            {
                const bool visible = !description->isVisible();
                description->setVisible(visible);
                if (key == "qt-accent-color")
                    row->findChild<QLineEdit *>("value-qt-accent-color")->setVisible(visible);
            });
    parent->addWidget(row);
    updateReferenceDependencies();
}
void PrefsDialog::addReferenceRows(QVBoxLayout *form, int category, bool advanced)
{
    QString group = !advanced && (category==0 || category==12) ? qtr(category==0 ? "Appearance" : "Add-ons") : QString();
    for (const auto &entry : PreferencesCatalog::rows)
    {
        if (entry.category != category || entry.advanced != advanced) continue;
        if (group != qtr(entry.group) && (!advanced ||
            (category==0 && qtr(entry.group)==qtr("Developer Options")) || category==10 ||
            qtr(entry.group)==qtr("Playback engine")))
        {
            group = qtr(entry.group);
            auto *title = new QLabel(group, this);
            title->setProperty("redesignSection", true);
            title->setStyleSheet("font-size:16px;font-weight:500;");
            title->setContentsMargins(0, 20, 0, 8);
            form->addWidget(title);
        }
        if (entry.editor == PreferencesCatalog::Editor::Action) addReferenceAction(form, entry);
        else addReferenceRow(form, entry);
    }
}
void PrefsDialog::addReferenceRow(QVBoxLayout *form, const PreferencesCatalog::Row &entry)
{
    using Editor = PreferencesCatalog::Editor;
    const QString key = optionKey(entry);
    const QString viewKey = QString::fromLatin1(entry.key).replace('/','-');
    const auto found = std::find_if(options.cbegin(), options.cend(), [&key](const Option &o) {
        return key == qfu(o.config->psz_name);
    });
    if (found != options.cend() && entry.editor == Editor::Native)
    {
        addOption(form, *found, &entry);
        return;
    }
    auto *row = new QWidget(this);
    row->setObjectName("preference-" + viewKey);
    row->setProperty("preferenceKey",key);
    row->setProperty("valueId","value-"+viewKey);
    row->setProperty("editorId","editor-"+viewKey);
    row->setProperty("referenceView", QString::fromLatin1(entry.key));
    auto *grid = new QGridLayout(row);
    grid->setContentsMargins(0, 0, 0, 0);
    grid->setRowMinimumHeight(0,34);
    grid->setHorizontalSpacing(0);
    grid->setColumnMinimumWidth(1,10);
    grid->setColumnStretch(0, 454);
    grid->setColumnStretch(10, 320);
    auto *labelGroup = new QWidget(row);
    auto *labels = new QHBoxLayout(labelGroup);
    labels->setContentsMargins(0,0,0,0);
    labels->setSpacing(8);
    auto *label = new SettingsLabel(qtr(entry.label), labelGroup);
    labels->addWidget(label);
    auto *help = new QToolButton(labelGroup);
    help->setObjectName("help-" + viewKey);
    help->setFixedSize(16,16);
    help->setIcon(QIcon(sourceMask(":/redesign/icons/settings-info.svg", palette().text().color(), devicePixelRatioF())));
    help->setIconSize(QSize(16,16));
    help->setStyleSheet("padding:0;background:transparent");
    help->setAccessibleName(qtr("Help for %1").arg(label->text()));
    labels->addWidget(help);
    labels->addStretch();
    grid->addWidget(labelGroup,0,0);
    auto *description = new QLabel(row);
    description->setWordWrap(true);
    description->setTextFormat(Qt::PlainText);
    description->setText(found == options.cend() ? qtr("This capability is not available in this build.")
        : qfut(found->config->psz_longtext ? found->config->psz_longtext : found->config->psz_text));
    description->setText(description->text()+playbackScope(key));
    if(entry.editor==Editor::Slider)
    {
        help->hide();
        label->setToolTip(description->text());
        label->setAccessibleDescription(description->text());
    }
    description->hide();
    grid->addWidget(description,2,0,1,12);
    connect(help,&QToolButton::clicked,description,[description]{ description->setVisible(!description->isVisible()); });
    if (found == options.cend())
    {
        auto *unavailable = new QLabel(qtr("Unavailable in this build"),row);
        unavailable->setEnabled(false);
        unavailable->setAccessibleName(label->text() + ": " + unavailable->text());
        grid->addWidget(unavailable,0,10,Qt::AlignRight);
        form->addWidget(row);
        return;
    }
    const QColor accent = palette().color(QPalette::Highlight);
    const QString mode = QString::fromLatin1(entry.choices ? entry.choices : "");
    auto *config = found->config;
    if (mode == "startup-volume")
    {
        auto *editor=new QWidget(row);
        editor->setObjectName("editor-"+viewKey);
        editor->setProperty("preferenceEditorGroup",true);
        auto *layout=new QVBoxLayout(editor);
        layout->setContentsMargins(0,0,0,0);
        layout->setSpacing(3);
        auto *remember=new QPushButton(qtr("Remember last volume"),editor);
        remember->setObjectName("value-"+viewKey);
        remember->setCheckable(true);
        remember->setFixedHeight(34);
        auto *fixed=new QPushButton(qtr("Always starts at:"),editor);
        fixed->setObjectName("preferencesStartupVolumeFixed");
        fixed->setCheckable(true);
        fixed->setFixedHeight(34);
        auto *group=new QButtonGroup(editor);
        group->addButton(remember,1);
        group->addButton(fixed,0);
        for(auto *button : {remember,fixed})
            button->setStyleSheet(QString("QPushButton{text-align:left;}QPushButton:checked{background:%1;color:%2;}")
                .arg(accent.darker(400).name(),accent.name()));
        layout->addWidget(remember);
        auto *fixedRow=new QHBoxLayout;
        fixedRow->setSpacing(0);
        fixedRow->addWidget(fixed);
        auto *amount=new QDoubleSpinBox(editor);
        amount->setObjectName("value-mmdevice-volume");
        amount->setAccessibleName(qtr("Startup volume in percent"));
        amount->setRange(0,300);
        amount->setDecimals(0);
        amount->setSuffix(qtr(" %"));
        amount->setFixedHeight(34);
        amount->setMaximumWidth(140);
        fixedRow->addWidget(amount,1);
        layout->addLayout(fixedRow);
        grid->addWidget(editor,0,10);
        auto sync=[this,key,remember,fixed,amount](const QString &,const QVariant &){
            const QSignalBlocker a(remember),b(fixed),c(amount);
            const bool saved=draftValue(key).toBool();
            remember->setChecked(saved);
            fixed->setChecked(!saved);
            const bool supported=config_FindConfig("mmdevice-volume")!=nullptr;
            amount->setValue(draftValue("mmdevice-volume").toDouble()*100);
            amount->setEnabled(!saved && supported);
            fixed->setEnabled(supported);
            if(!supported)amount->setToolTip(qtr("Startup volume is unavailable for this audio output."));
        };
        sync(key,{});
        connect(this,&PrefsDialog::draftChanged,row,sync);
        connect(group,&QButtonGroup::idClicked,row,[this,key](int id){stageValue(key,qlonglong(id));});
        connect(amount,&QDoubleSpinBox::valueChanged,row,[this](double value){stageValue("mmdevice-volume",value/100);});
    }
    else if (mode == "font-size-mode")
    {
        auto *editor=new QWidget(row);
        editor->setObjectName("value-"+viewKey);
        auto *layout=new QHBoxLayout(editor);
        layout->setContentsMargins(0,0,0,0);
        layout->setSpacing(2);
        auto *group=new QButtonGroup(editor);
        for(int i=0;i<2;++i)
        {
            auto *button=new QPushButton(i ? qtr("Pixels") : qtr("Relative"),editor);
            button->setCheckable(true);
            button->setFixedHeight(34);
            button->setAccessibleName(qtr("Subtitle size in %1").arg(button->text()));
            group->addButton(button,i);
            layout->addWidget(button,1);
        }
        auto sync=[group,key](const QString &updated,const QVariant &value){
            if(updated!=key)return;
            group->button(value.toInt()>0 ? 1 : 0)->setChecked(true);
        };
        sync(key,draftValue(key));
        connect(this,&PrefsDialog::draftChanged,row,sync);
        connect(group,&QButtonGroup::idClicked,row,[this,key](int id){
            stageValue(key,qlonglong(id ? qMax(20,draftValue(key).toInt()) : 0));
        });
        grid->addWidget(editor,0,10);
    }
    else if (mode == "font-size")
    {
        auto *value = new QSpinBox(row);
        value->setObjectName("value-" + viewKey);
        value->setAccessibleName(label->text());
        value->setFixedHeight(34);
        grid->addWidget(value,0,10);
        auto sync = [this,value,key](const QString &,const QVariant &) {
            const QSignalBlocker blocker(value);
            const int pixels = draftValue("freetype-absolute-fontsize").toInt();
            value->setRange(pixels ? 1 : 10,pixels ? 1024 : 500);
            value->setSuffix(pixels ? qtr(" px") : qtr(" %"));
            value->setValue(pixels ? pixels : draftValue(key).toInt());
        };
        sync(key,{});
        connect(this,&PrefsDialog::draftChanged,row,sync);
        connect(value,&QSpinBox::valueChanged,row,[this,key](int v){
            stageValue(draftValue("freetype-absolute-fontsize").toInt() ? "freetype-absolute-fontsize" : key,qlonglong(v));
        });
    }
    else if (entry.editor == Editor::Slider)
    {
        auto *editor = new QWidget(row);
        editor->setObjectName("editor-" + viewKey);
        editor->setProperty("preferenceEditorGroup", true);
        auto *layout = new QVBoxLayout(editor);
        layout->setContentsMargins(0,0,0,0);
        layout->setSpacing(3);
        const bool real = CONFIG_CLASS(config->i_type) == CONFIG_ITEM_FLOAT;
        const double scale = key == "sub-delay" ? 0.1 :
            key == "qt-opacity" || key == "qt-fs-opacity" || key == "mmdevice-volume" ? 100.0 :
            key == "freetype-opacity" || key == "freetype-background-opacity" ? 100.0/255.0 :
            key == "mouse-hide-timeout" || key == "qt-notification-duration" ||
            key == "qt-shortcut-feedback-duration" || key == "video-title-timeout" ? 0.001 : 1.0;
        const QString suffix = scale==0.1 || scale==0.001 ? qtr(" s") :
            scale!=1 || key=="qt-max-volume" ? qtr(" %") : QString();
        auto *slider = new SettingsSlider(editor);
        slider->setObjectName("value-" + viewKey);
        slider->setAccessibleName(label->text());
        slider->setRange(0,1000);
        const bool picture=entry.category==5 && QLatin1String(entry.group)==QLatin1String("Picture");
        slider->setTickPosition(QSlider::NoTicks);
        double interval=key=="gamma" ? 1 : key=="qt-max-volume" ? 25 : entry.step;
        if(picture && key!="gamma" && key!="saturation")interval=0;
        slider->referenceTickInterval=interval>0 ? qMax(1,qRound(1000*interval/(entry.maximum-entry.minimum))) : 0;
        slider->setSingleStep(qMax(1,real ? 10 : qRound(1000/(entry.maximum-entry.minimum))));
        slider->setFixedHeight(picture ? 28 : 24);
        layout->addWidget(slider);
        if (!picture)
        {
            auto *ticks = new QHBoxLayout;
            QStringList labels;
            if (key=="rate") labels={"0.25","0.5","0.75","1","1.25","1.5","1.75","2"};
            else if (key=="qt-fs-sensitivity") labels={qtr("Low"),qtr("Medium"),qtr("High")};
            else
            {
                labels.append(QString::number(entry.minimum*scale)+suffix);
                if (key!="qt-opacity" && key!="qt-fs-opacity" &&
                    key!="qt-shortcut-feedback-duration" && key!="video-title-timeout")
                    labels.append(QString::number((entry.minimum+entry.maximum)*scale/2)+suffix);
                labels.append(QString::number(entry.maximum*scale)+suffix);
            }
            for (const auto &label : labels)
            {
                if (ticks->count()) ticks->addStretch();
                auto *text = new QLabel(label,editor);
                text->setStyleSheet("font-size:12px;");
                ticks->addWidget(text);
            }
            layout->addLayout(ticks);
        }
        grid->addWidget(editor,0,10);
        auto sync = [slider,key,entry,scale,suffix](const QString &updated,const QVariant &v) {
            if (updated != key) return;
            const QSignalBlocker blocker(slider);
            slider->setValue(qRound(1000*(v.toDouble()-entry.minimum)/(entry.maximum-entry.minimum)));
            slider->setToolTip(QString::number(v.toDouble()*scale,'g',6)+suffix);
        };
        sync(key,draftValue(key));
        connect(this,&PrefsDialog::draftChanged,row,sync);
        connect(slider,&QSlider::valueChanged,row,[this,key,entry,real](int v){
            const double native=entry.minimum+(entry.maximum-entry.minimum)*v/1000;
            stageValue(key,real ? QVariant(native) : QVariant::fromValue<qlonglong>(qRound64(native)));
        });
    }
    else if (entry.editor == Editor::Filter || entry.editor == Editor::Inverse || entry.editor == Editor::Toggle)
    {
        auto *toggle = new SettingsSwitch(row,property("figmaDark").toBool(),accent);
        toggle->setObjectName("value-" + viewKey);
        toggle->setAccessibleName(label->text());
        grid->addWidget(toggle,0,10,Qt::AlignRight);
        auto enabled = [this,entry,mode](const QVariant &v) {
            if (entry.editor == Editor::Inverse) return !v.toBool();
            if (entry.editor != Editor::Filter) return v.toLongLong() != 0;
            const auto modules = v.toString().split(':',Qt::SkipEmptyParts);
            if (mode == "spatial") return modules.contains("spatializer") || modules.contains("headphone");
            if (mode == "night") return modules.contains("compressor") &&
                qFuzzyCompare(draftValue("compressor-threshold").toDouble(),-30.0) &&
                qFuzzyCompare(draftValue("compressor-ratio").toDouble(),8.0) &&
                qFuzzyCompare(draftValue("compressor-makeup-gain").toDouble(),12.0);
            return modules.contains(mode == "night" ? "compressor" : mode);
        };
        auto sync = [this,toggle,key,mode,enabled](const QString &updated,const QVariant &) {
            if (updated != key && !(mode == "night" && updated.startsWith("compressor-"))) return;
            const QSignalBlocker blocker(toggle);
            toggle->setChecked(enabled(draftValue(key)));
        };
        sync(key,draftValue(key));
        connect(this,&PrefsDialog::draftChanged,row,sync);
        connect(toggle,&QCheckBox::toggled,row,[this,key,entry,mode,config](bool on) {
            if (entry.editor == Editor::Filter)
            {
                if (mode == "skins2") { stageValue(key,on ? "skins2" : "qt"); return; }
                auto modules = draftValue(key).toString().split(':',Qt::SkipEmptyParts);
                const QString module = mode == "night" ? "compressor" : mode == "spatial" ? "headphone" : mode;
                modules.removeAll(module);
                if (mode == "spatial") modules.removeAll("spatializer");
                if (on) modules.append(module);
                if (on && mode == "night")
                {
                    stageValue("compressor-threshold",-30.0);
                    stageValue("compressor-ratio",8.0);
                    stageValue("compressor-makeup-gain",12.0);
                }
                stageValue(key,modules.join(':'));
            }
            else if (entry.editor == Editor::Inverse) stageValue(key,qlonglong(!on));
            else stageValue(key,qlonglong(on ? (config->orig.i ? config->orig.i : 1) : 0));
        });
    }
    else
    {
        auto *combo = new QComboBox(row);
        combo->setObjectName("value-" + viewKey);
        combo->setAccessibleName(label->text());
        combo->setFixedHeight(34);
        combo->setSizeAdjustPolicy(QComboBox::AdjustToMinimumContentsLengthWithIcon);
        combo->setMinimumContentsLength(8);
        combo->setSizePolicy(QSizePolicy::Expanding,QSizePolicy::Fixed);
        grid->addWidget(combo,0,10);
        if (entry.editor == Editor::Policy)
        {
            const auto labels = mode.split('|');
            for (int i=0; i<labels.size(); ++i) combo->addItem(qtr(qtu(labels[i])),i);
        }
        else if (mode == "repeat-policy")
        { combo->addItem(qtr("Off"),0);combo->addItem(qtr("One item"),1);combo->addItem(qtr("All items"),2); }
        else if (mode == "finish-policy")
        { combo->addItem(qtr("Continue"),0);combo->addItem(qtr("Stop"),1);combo->addItem(qtr("Quit VLC"),2); }
        else if (mode == "snapshot-size")
        { combo->addItem(qtr("Original size"),0);combo->addItem("1920 × 1080",1920);combo->addItem("1280 × 720",1280);combo->addItem("640 × 360",640); }
        else if (mode == "startup-volume")
        { combo->addItem(qtr("Remember last volume"),1);combo->addItem(qtr("Always start at the selected volume"),0); }
        else if (mode == "fullscreen-screen")
        {
            combo->addItem(qtr("Current screen"),-1);
            const auto screens=QGuiApplication::screens();
            for(int i=0;i<screens.size();++i)combo->addItem(screens[i]->name(),i);
        }
        else if (mode == "timeshift-size")
        { combo->addItem(qtr("Automatic"),-1);combo->addItem(qtr("Small (16 MiB)"),16*1024*1024);combo->addItem(qtr("Medium (50 MiB)"),50*1024*1024);combo->addItem(qtr("Large (256 MiB)"),256*1024*1024); }
        else if (mode == "aspect-ratio" || mode == "crop-ratio")
        {
            combo->setEditable(true);
            combo->addItem(mode == "crop-ratio" ? qtr("None") : qtr("Automatic"),"");
            for(const auto *ratio : {"16:9","4:3","1:1","16:10","2.21:1","2.35:1","2.39:1"})combo->addItem(ratio,ratio);
        }
        else if (mode == "zoom")
        { combo->addItem(qtr("Fit"),1.0);combo->addItem("0.25×",0.25);combo->addItem("0.5×",0.5);combo->addItem("2×",2.0); }
        else if (mode == "spatial-mode")
        { combo->addItem(qtr("Speakers"),"spatializer");combo->addItem(qtr("Headphones"),"headphone"); }
        else if (mode == "font-size-mode")
        { combo->addItem(qtr("Relative"),0);combo->addItem(qtr("Pixels"),20); }
        else if (mode == "font-size")
        { combo->addItem(qtr("Smaller"),30);combo->addItem(qtr("Small"),22);combo->addItem(qtr("Normal"),16);combo->addItem(qtr("Large"),12);combo->addItem(qtr("Larger"),6); }
        else if (mode == "background-mode")
        { combo->addItem(qtr("None"),0);combo->addItem(qtr("Solid"),255);combo->addItem(qtr("Translucent"),128); }
        else if (mode == "artwork-policy")
        { combo->addItem(qtr("From the file only"),0);combo->addItem(qtr("Allow internet access"),1); }
        else if (mode == "buffering-preset")
        { combo->addItem(qtr("Custom"),-1);combo->addItem(qtr("Low latency"),300);combo->addItem(qtr("Balanced"),1000);combo->addItem(qtr("High reliability"),3000); }
        else if (mode == "cipher-policy")
        { combo->addItem(qtr("Balanced"),"NORMAL");combo->addItem(qtr("Performance"),"PERFORMANCE");combo->addItem(qtr("Secure 128-bit"),"SECURE128");combo->addItem(qtr("Secure 256-bit"),"SECURE256"); }
        else if (mode == "postproc")
        { combo->addItem(qtr("Off"),0);for(int i=1;i<=6;++i)combo->addItem(QString::number(i),i); }
        else if (mode == "subtitle-match")
        { combo->addItem(qtr("No automatic matching"),0);combo->addItem(qtr("Any subtitle file"),1);combo->addItem(qtr("Contains the movie name"),2);combo->addItem(qtr("Title with extra characters"),3);combo->addItem(qtr("Exact movie name"),4); }
        else if (mode == "outline-thickness")
        { combo->addItem(qtr("None"),0);combo->addItem(qtr("Thin"),1);combo->addItem(qtr("Normal"),2);combo->addItem(qtr("Thick"),4); }
        else if (mode == "shadow-distance")
        { combo->addItem(qtr("None"),0.0);combo->addItem(qtr("Small"),0.06);combo->addItem(qtr("Medium"),0.12);combo->addItem(qtr("Large"),0.2); }
        auto current = [this,key,mode]() -> QVariant {
            if (mode == "font-size-mode") return draftValue(key).toInt() > 0 ? 20 : 0;
            if (mode == "postproc" && !draftValue("video-filter").toString().split(':').contains("postproc"))return 0;
            if (mode == "repeat-policy") return draftValue("repeat").toBool() ? 1 : draftValue("loop").toBool() ? 2 : 0;
            if (mode == "finish-policy") return draftValue("play-and-exit").toBool() ? 2 : draftValue(key).toBool() ? 1 : 0;
            if (mode == "spatial-mode") return draftValue(key).toString().split(':').contains("spatializer") ? "spatializer" : "headphone";
            if (mode == "buffering-preset")
            {
                const auto amount=draftValue("network-caching");
                for (const auto *cache : {"file-caching","disc-caching","live-caching"})
                    if(draftValue(cache)!=amount)return -1;
                return amount;
            }
            if (mode == "snapshot-size")
            {
                const int width=draftValue(key).toInt(),height=draftValue("snapshot-height").toInt();
                if ((width==0 && height==0) || (width>0 && height==width*9/16))return width;
                return QString::number(width)+QStringLiteral(" × ")+QString::number(height);
            }
            return draftValue(key);
        };
        auto sync = [combo,current](const QString &,const QVariant &) {
            const QSignalBlocker blocker(combo);
            auto value = current();
            int index = combo->findData(value);
            if (index < 0) { combo->addItem(qtr("Custom (%1)").arg(value.toString()),value); index=combo->count()-1; }
            combo->setCurrentIndex(index);
        };
        sync(key,{});
        connect(this,&PrefsDialog::draftChanged,row,sync);
        if (combo->isEditable()) connect(combo->lineEdit(),&QLineEdit::editingFinished,row,[this,combo,key]{
            if (combo->currentIndex()<0 || combo->currentText()!=combo->itemText(combo->currentIndex())) stageValue(key,combo->currentText());
        });
        connect(combo,&QComboBox::activated,row,[this,combo,key,mode](int index){
            const auto value = combo->itemData(index);
            // An existing custom size is a display of the two native fields,
            // not a preset that may reset them through QString::toInt().
            if (mode=="snapshot-size" && value.metaType().id()==QMetaType::QString)return;
            if (mode == "repeat-policy") { stageValue("repeat",qlonglong(value.toInt()==1));stageValue("loop",qlonglong(value.toInt()==2)); }
            else if (mode == "finish-policy") { stageValue("play-and-stop",qlonglong(value.toInt()==1));stageValue("play-and-exit",qlonglong(value.toInt()==2)); }
            else if (mode == "spatial-mode")
            {
                auto filters = draftValue(key).toString().split(':',Qt::SkipEmptyParts);
                filters.removeAll("spatializer");filters.removeAll("headphone");
                filters.append(value.toString());
                stageValue(key,filters.join(':'));
            }
            else if (mode == "buffering-preset")
            {
                if (value.toInt() >= 0)
                    for (const auto *cache : {"file-caching","disc-caching","network-caching","live-caching"}) stageValue(cache,value);
            }
            else if (mode == "postproc")
            {
                auto filters=draftValue("video-filter").toString().split(':',Qt::SkipEmptyParts);
                filters.removeAll("postproc");
                if(value.toInt()>0)filters.append("postproc");
                stageValue("video-filter",filters.join(':'));
                if(value.toInt()>0)stageValue(key,value);
            }
            else
            {
                if (mode == "font-size-mode" && value.toInt() && draftValue(key).toInt()) return;
                stageValue(key,value);
                if (mode == "snapshot-size") stageValue("snapshot-height",value.toInt()*9/16);
            }
        });
    }
    form->addWidget(row);
    updateReferenceDependencies();
}
void PrefsDialog::addReferenceAction(QVBoxLayout *form,const PreferencesCatalog::Row &entry)
{
    auto *row = new QWidget(this);
    auto *layout = new QHBoxLayout(row);
    layout->setContentsMargins(0,0,0,0);
    if(*entry.label)layout->addWidget(new SettingsLabel(qtr(entry.label),row),1);
    auto *button = new QPushButton(qtr(entry.choices),row);
    const QString action = QString::fromLatin1(entry.key).mid(1);
    button->setObjectName("preferencesAction-" + action);
    button->setFixedHeight(34);
    button->setMinimumWidth(100);
    layout->addWidget(button);
    if(action=="equalizer")
    {
        button->setCheckable(true);
        button->setSizePolicy(QSizePolicy::Expanding,QSizePolicy::Fixed);
        button->setStyleSheet(QString("QPushButton{background:%1;border:0;}")
            .arg(property("figmaDark").toBool() ? "#070707" : "#eeeeee"));
        const auto disclosure=sourceMask(":/redesign/icons/chevron-down.svg",palette().text().color(),devicePixelRatioF());
        button->setIcon(QIcon(disclosure));
        button->setIconSize(QSize(24,24));
        button->setLayoutDirection(Qt::RightToLeft);
        auto *editor=new QWidget(this);
        editor->setObjectName("preferencesEqualizer");
        auto *body=new QVBoxLayout(editor);
        body->setContentsMargins(0,0,0,0);
        editor->hide();
        form->addWidget(row);
        form->addWidget(editor);
        connect(button,&QPushButton::toggled,this,[this,editor,body,button,disclosure](bool open){
            if(open && !editor->property("built").toBool()) { addEqualizer(body);editor->setProperty("built",true); }
            button->setText(open ? qtr("Close Equalizer") : qtr("Open Equalizer"));
            button->setIcon(QIcon(open ? disclosure.transformed(QTransform().rotate(180)) : disclosure));
            editor->setVisible(open);
            updateResponsiveLayout();
        });
        return;
    }
    connect(button,&QPushButton::clicked,this,[this,action,button]{
        if (action == "config-folder")
        {
            char *path = config_GetUserDir(VLC_CONFIG_DIR);
            if (path) { QDesktopServices::openUrl(QUrl::fromLocalFile(qfu(path)));free(path); }
        }
        else if (action == "reset-preferences") reset();
        else if (action == "shortcuts") showShortcuts();
        else if (action == "reset-shortcuts") { showShortcuts(); reset(); }
        else if (action == "clear-history")
        {
            auto *question = new QMessageBox(QMessageBox::Question,qtr("Clear history"),
                qtr("Clear playback history? Your media files and playlists are retained."),QMessageBox::Yes|QMessageBox::Cancel,this);
            question->setDefaultButton(QMessageBox::Cancel);
            question->setAttribute(Qt::WA_DeleteOnClose);
            applyRedesignDialogStyle(question,p_intf);
            connect(question,&QDialog::finished,this,[this](int result){
                if (result != QMessageBox::Yes || !p_intf->p_mi || !p_intf->p_mi->getMediaLibrary()) return;
                auto *recent = new MLRecentMediaModel(this);
                recent->setMl(p_intf->p_mi->getMediaLibrary());
                recent->clearHistory();
            });
            question->open();
        }
        else if (action == "reset-picture")
        {
            for (const auto *key : {"hue","brightness","contrast","saturation","gamma"})
            {
                const auto *config = config_FindConfig(key);
                if (config) stageValue(key,config->orig.f);
            }
        }
        else if (action == "vlc-commands") showVlcCommands(button);
        else if (action == "rescan-plugins")
        {
            if (pluginScan) return;
            pluginScan = new QProcess(this);
            emit pluginScanChanged();
            button->setEnabled(false);
            button->setText(qtr("Rescanning…"));
            auto restore = [this,button] {
                button->setEnabled(true);
                button->setText(qtr("Rescan"));
                pluginScan->deleteLater();
                pluginScan = nullptr;
                emit pluginScanChanged();
            };
            connect(pluginScan,&QProcess::errorOccurred,this,[this,restore](QProcess::ProcessError error){
                if (error != QProcess::FailedToStart) return;
                const auto detail = pluginScan->errorString();
                restore();
                QMessageBox::warning(this,qtr("Cannot rescan plugins"),detail);
            });
            connect(pluginScan,&QProcess::finished,this,[this,restore](int code,QProcess::ExitStatus status){
                const auto detail = QString::fromUtf8(pluginScan->readAllStandardError());
                restore();
                if (code || status != QProcess::NormalExit)
                    QMessageBox::warning(this,qtr("Cannot rescan plugins"),detail);
                else QMessageBox::information(this,qtr("Plugins rescanned"),qtr("The plugin cache has been rebuilt. Restart VLC to load newly discovered modules."));
            });
            pluginScan->setProgram(QCoreApplication::applicationDirPath()+"/vlc-cache-gen"
#ifdef _WIN32
                                  ".exe"
#endif
                                  );
            char *plugins = config_GetSysPath(VLC_PKG_LIB_DIR,"plugins");
            pluginScan->setArguments({plugins ? qfu(plugins) : QCoreApplication::applicationDirPath()+"/plugins"});
            free(plugins);
            pluginScan->start();
        }
    });
    if (action == "clear-history") button->setEnabled(p_intf->p_mi && p_intf->p_mi->getMediaLibrary());
    form->addWidget(row);
}
void PrefsDialog::showVlcCommands(QWidget *anchor)
{
    auto *menu = new QMenu(this);
    menu->setObjectName("preferencesVlcCommands");
    menu->setAttribute(Qt::WA_DeleteOnClose);
    menu->setWindowFlag(Qt::FramelessWindowHint);
    menu->setAttribute(Qt::WA_TranslucentBackground);
    applyRedesignDialogStyle(menu,p_intf);
    const struct { const char *label; void (*build)(qt_intf_t *,QMenu *); } groups[] = {
        {N_("Media"),VLCMenuBar::FileMenu},{N_("Playback"),VLCMenuBar::NavigMenu},
        {N_("Audio"),VLCMenuBar::AudioMenu},{N_("Video"),VLCMenuBar::VideoMenu},
        {N_("Tools"),VLCMenuBar::ToolsMenu},{N_("View"),VLCMenuBar::ViewMenu},
        {N_("Help"),VLCMenuBar::HelpMenu}
    };
    for (const auto &group : groups)
    {
        auto *child = menu->addMenu(qtr(group.label));
        group.build(p_intf,child);
    }
    auto *subtitles = menu->addMenu(qtr("Subtitles"));
    VLCMenuBar::SubtitleMenu(p_intf,subtitles);
    menu->popup(anchor->mapToGlobal(QPoint(0,anchor->height())));
}
QWidget *PrefsDialog::createCategory(int category)
{
    auto *page = new QWidget(this);
    auto *outer = new QVBoxLayout(page);
    outer->setContentsMargins(32, 10, 0, 4);
    auto *scroll = new QScrollArea(page);
    scroll->setObjectName("preferencesScroll"+QString::number(category));
    scroll->setWidgetResizable(true);
    auto *body = new QWidget;
    auto *form = new QVBoxLayout(body);
    form->setContentsMargins(0, 0, 16, 20);
    form->setSpacing(8);
    scroll->setWidget(body);
    // The reference reserves sixteen pixels to the card edge. Let the native
    // scrollbar occupy that reserve without moving every value field left.
    connect(scroll->verticalScrollBar(),&QScrollBar::rangeChanged,body,[scroll,form](int minimum,int maximum){
        const int extent=maximum>minimum ? scroll->verticalScrollBar()->sizeHint().width() : 0;
        form->setContentsMargins(0,0,16-extent,20);
    });
    scroll->viewport()->setAutoFillBackground(false);
    body->setAutoFillBackground(false);
    outer->addWidget(scroll);
    if (category == 12)
    {
        auto *title = new QLabel(qtr("Add-ons"), this);
        title->setProperty("redesignSection", true);
        title->setStyleSheet("font-size:16px;font-weight:500;");
        form->addWidget(title);
        auto *toolbar = new QHBoxLayout;
        auto *extensionSearch = new QLineEdit(this);
        extensionSearch->setObjectName("preferencesExtensionSearch");
        extensionSearch->setAccessibleName(qtr("Search installed extensions"));
        extensionSearch->setPlaceholderText(qtr("Search"));
        extensionSearch->setClearButtonEnabled(true);
        toolbar->addWidget(extensionSearch, 1);
        auto *findMore = new QPushButton(qtr("Find more extensions"), this);
        findMore->setObjectName("preferencesFindExtensions");
        connect(findMore, &QPushButton::clicked, this, [this] {
            DialogsProvider::getInstance(p_intf)->pluginDialog();
        });
        toolbar->addWidget(findMore);
        // Keep the native catalogue, delegate and install/remove owner. Only
        // its view is embedded here; the source manager still owns its model.
        auto *addons = new AddonsTab(p_intf);
        addons->setParent(page);
        addons->hide();
        auto *list = addons->addonsView;
        list->setParent(page);
        list->setObjectName("installedExtensionsList");
        list->setAccessibleName(qtr("Installed add-ons"));
        list->setFixedHeight(192);
        list->show();
        list->setAlternatingRowColors(false);
        addons->m_model->setStateFilter(AddonsModel::State::STATE_INSTALLED);
        form->addWidget(list);
        extensionSearch->setFixedWidth(140);
        toolbar->setSpacing(6);
        toolbar->insertStretch(1);
        auto *add = new QPushButton(qtr("Add"),page);
        add->setObjectName("preferencesAddExtension");
        auto *remove = new QPushButton(qtr("Remove"),page);
        remove->setObjectName("preferencesRemoveExtension");
        remove->setEnabled(false);
        toolbar->addWidget(add);
        toolbar->addWidget(remove);
        form->addLayout(toolbar);
        connect(extensionSearch,&QLineEdit::textChanged,addons->m_model.get(),&AddonsModel::setSearchPattern);
        disconnect(findMore,nullptr,this,nullptr);
        connect(findMore,&QPushButton::clicked,addons,[addons]{
            addons->m_model->setStateFilter(AddonsModel::State::STATE_NONE);
            addons->reposync();
        });
        connect(add,&QPushButton::clicked,this,[this,addons]{
            const auto file = QFileDialog::getOpenFileName(this,qtr("Add an extension package"),QString(),qtr("VLC extension packages (*.vlp)"));
            if (file.isEmpty()) return;
            addons->m_model->setStateFilter(AddonsModel::State::STATE_NONE);
            addons->m_model->loadFromExternalRepository(QUrl::fromLocalFile(file));
        });
        auto selected = [list] { return list->currentIndex(); };
        auto updateRemove=[remove,selected]{
            const auto item=selected();
            remove->setEnabled(item.isValid() && item.data(AddonsModel::MANAGEABLE).toBool() &&
                item.data(AddonsModel::STATE).value<AddonsModel::State>()==AddonsModel::State::STATE_INSTALLED);
        };
        connect(list->selectionModel(),&QItemSelectionModel::currentChanged,remove,updateRemove);
        connect(list->model(),&QAbstractItemModel::dataChanged,remove,updateRemove);
        connect(list->model(),&QAbstractItemModel::modelReset,remove,updateRemove);
        connect(list->model(),&QAbstractItemModel::rowsRemoved,remove,updateRemove);
        connect(remove,&QPushButton::clicked,this,[this,addons,selected]{
            const QPersistentModelIndex item(selected());
            auto removable=[&item]{return item.isValid() && item.data(AddonsModel::MANAGEABLE).toBool() &&
                item.data(AddonsModel::STATE).value<AddonsModel::State>()==AddonsModel::State::STATE_INSTALLED;};
            if (!removable()) return;
            if (QMessageBox::question(this,qtr("Remove add-on"),qtr("Remove %1?").arg(item.data(AddonsModel::NAME).toString()),
                                      QMessageBox::Yes|QMessageBox::Cancel,QMessageBox::Cancel)==QMessageBox::Yes && removable())
                addons->m_model->removeService(item.row());
        });
    }
    if (category == 0)
    {
        auto *title = new QLabel(qtr("Appearance"), this);
        title->setProperty("redesignSection", true);
        QFont f = title->font();
        f.setPixelSize(16);
        f.setWeight(QFont::Medium);
        title->setFont(f);
        title->setStyleSheet("font-size:16px;font-weight:500;");
        title->setContentsMargins(0, 20, 0, 8);
        form->addWidget(title);
#ifdef _WIN32
        auto *languageRow = new QHBoxLayout;
        languageRow->addWidget(new QLabel(qtr("Interface language"), this), 1);
        language = new QComboBox(this);
        language->setSizeAdjustPolicy(QComboBox::AdjustToMinimumContentsLengthWithIcon);
        language->setMinimumContentsLength(10);
        language->setMaximumWidth(320);
        language->setObjectName("preferencesLanguage");
        language->setAccessibleName(qtr("Interface language"));
        for (const auto &entry : language_map)
            language->addItem(qfut(entry.name), qfu(entry.iso));
        // QSettings' native Windows backend opens/creates its key even for a
        // read. Preserve an absent installer override when merely viewing this
        // page, using the existing registry reader before opening that owner.
        originalLanguage = QStringLiteral("auto");
        QVLCRegistry nativeRegistry(HKEY_CURRENT_USER);
        if (nativeRegistry.RegistryValueExists("Software\\VideoLAN\\VLC", "Lang"))
        {
            QSettings registry("HKEY_CURRENT_USER\\Software\\VideoLAN\\VLC", QSettings::NativeFormat);
            originalLanguage = registry.value("Lang").toString();
        }
        int languageIndex = language->findData(originalLanguage);
        if (languageIndex < 0)
        {
            language->addItem(qtr("Unavailable language (%1)").arg(originalLanguage), originalLanguage);
            languageIndex = language->count() - 1;
        }
        language->setCurrentIndex(languageIndex);
        connect(language,&QComboBox::activated,this,&PrefsDialog::markEdited);
        language->setToolTip(qtr("Applies after restarting VLC. Uses VLC's existing Windows "
                                 "interface-language preference."));
        languageRow->addWidget(language, 1);
        form->addLayout(languageRow);
#endif
        if (p_intf->p_mi)
        {
            auto *themeRow = new QHBoxLayout;
            themeRow->addWidget(new QLabel(qtr("Theme"), this), 1);
            auto *themeOptions = new QWidget(this);
            themeOptions->setMaximumWidth(320);
            themeOptions->setSizePolicy(QSizePolicy::Expanding, QSizePolicy::Preferred);
            auto *themeChoices = new QHBoxLayout(themeOptions);
            themeChoices->setContentsMargins(0, 0, 0, 0);
            themeChoices->setSpacing(2);
            auto *buttons = new QButtonGroup(this);
            const auto schemes = p_intf->p_mi->getColorScheme()->getSchemes();
            selectedTheme = p_intf->p_mi->getColorScheme()->currentIndex();
            for (const auto choice :
                 {ColorSchemeModel::Night, ColorSchemeModel::Day, ColorSchemeModel::System})
                for (int i = 0; i < schemes.size(); ++i)
                    if (schemes[i].scheme == choice)
                    {
                        auto *button =
                            new QPushButton(qtr(choice == ColorSchemeModel::Night ? "Dark"
                                                : choice == ColorSchemeModel::Day ? "Light"
                                                                                  : "System"),
                                            this);
                        button->setCheckable(true);
                        button->setFixedHeight(34);
                        const QColor accent = palette().color(QPalette::Highlight);
                        button->setStyleSheet(
                            QString("QPushButton:checked{background:%1;color:%2;}")
                                .arg(accent.darker(400).name(), accent.name()));
                        button->setObjectName("preferencesTheme" + QString::number(choice));
                        buttons->addButton(button, i);
                        button->setChecked(i == selectedTheme);
                        themeChoices->addWidget(button, 1);
                    }
            connect(buttons, &QButtonGroup::idClicked, this,
                    [this](int index) { selectedTheme = index; markEdited(); });
            themeRow->addWidget(themeOptions, 1);
            form->addLayout(themeRow);
        }
    }
    addReferenceRows(form, category, false);
    auto *advanced = new QPushButton(this);
    advanced->setObjectName("preferencesAdvanced" + QString::number(category));
    advanced->setText(qtr("Advanced Options"));
    advanced->setCheckable(true);
    const QPixmap disclosure = sourceMask(":/redesign/icons/chevron-down.svg", palette().text().color(), devicePixelRatioF());
    advanced->setIcon(QIcon(disclosure));
    advanced->setIconSize(QSize(24,24));
    advanced->setLayoutDirection(Qt::RightToLeft);
    advanced->setFixedHeight(38);
    advanced->setSizePolicy(QSizePolicy::Expanding, QSizePolicy::Fixed);
    form->addWidget(advanced);
    auto *advancedBody = new QWidget;
    auto *advancedForm = new QVBoxLayout(advancedBody);
    advancedForm->setContentsMargins(0, 0, 0, 0);
    advancedBody->hide();
    form->addWidget(advancedBody);
    // Build once on demand and retain editors, so unsaved edits survive navigation.
    connect(advanced, &QPushButton::toggled, this,
            [this, advanced, advancedBody, advancedForm, category, disclosure](bool open)
            {
                advanced->setIcon(QIcon(open ? disclosure.transformed(QTransform().rotate(180)) : disclosure));
                if (open && !advancedBody->property("built").toBool())
                {
                    addReferenceRows(advancedForm,category,true);
                    auto *allOptions = new QToolButton(advancedBody);
                    allOptions->setObjectName("preferencesAllOptions"+QString::number(category));
                    allOptions->setText(qtr("All VLC options"));
                    allOptions->setCheckable(true);
                    allOptions->setArrowType(Qt::RightArrow);
                    allOptions->setToolButtonStyle(Qt::ToolButtonTextBesideIcon);
                    advancedForm->addWidget(allOptions);
                    auto *allBody=new QWidget(advancedBody);
                    auto *allForm=new QVBoxLayout(allBody);
                    allForm->setContentsMargins(0,0,0,0);
                    allBody->hide();
                    advancedForm->addWidget(allBody);
                    connect(allOptions,&QToolButton::toggled,allBody,[allOptions,allBody](bool open){
                        allOptions->setArrowType(open ? Qt::DownArrow : Qt::RightArrow);
                        allBody->setVisible(open);
                    });
                    QMap<QString, QVector<int>> modules;
                    for (int i = 0; i < options.size(); ++i)
                        if (options[i].category == category &&
                            (!options[i].basic || basicFor(qfu(options[i].config->psz_name))->editor!=PreferencesCatalog::Editor::Native))
                            modules[options[i].module].push_back(i);
                    for (auto it = modules.cbegin(); it != modules.cend(); ++it)
                    {
                        auto *toggle = new QToolButton;
                        toggle->setObjectName("preferencesModule-" + QString::number(category) + "-" + it.key());
                        toggle->setText(it.key());
                        toggle->setCheckable(true);
                        toggle->setArrowType(Qt::RightArrow);
                        toggle->setToolButtonStyle(Qt::ToolButtonTextBesideIcon);
                        allForm->addWidget(toggle);
                        auto *moduleBody = new QWidget;
                        auto *moduleForm = new QVBoxLayout(moduleBody);
                        moduleForm->setContentsMargins(8, 0, 0, 8);
                        moduleBody->hide();
                        allForm->addWidget(moduleBody);
                        const auto indices = it.value();
                        connect(toggle, &QToolButton::toggled, this,
                                [this, toggle, moduleBody, moduleForm, indices](bool expanded)
                                {
                                    toggle->setArrowType(expanded ? Qt::DownArrow : Qt::RightArrow);
                                    if (expanded && !moduleBody->property("built").toBool())
                                    {
                                        for (int i : indices)
                                            addOption(moduleForm, options[i]);
                                        moduleBody->setProperty("built", true);
                                    }
                                    moduleBody->setVisible(expanded);
                                    updateResponsiveLayout();
                                });
                    }
                    advancedBody->setProperty("built", true);
                }
                advancedBody->setVisible(open);
                updateResponsiveLayout();
            });
    form->addStretch();
    return page;
}
void PrefsDialog::selectCategory(int category)
{
    const QSignalBlocker selection(categories);
    for (int row = 0; row < categories->count(); ++row)
        if (categories->item(row)->data(Qt::UserRole).toInt() == category)
        {
            categories->setCurrentRow(row);
            break;
        }

    if (category < 0 || category >= 13)
        return;
    if (!categoryPages[category])
    {
        categoryPages[category] = createCategory(category);
        pages->addWidget(categoryPages[category]);
    }
    const QSignalBlocker blocker(categories);
    for (int i = 0; i < categories->count(); ++i)
        if (categories->item(i)->data(Qt::UserRole).toInt() == category)
            categories->setCurrentRow(i);
    categoryContainer->show();
    categories->show();
    search->show();
    heading->setContentsMargins(32, 0, 0, 0);
    findChild<QPushButton *>("preferencesReset")->setText(qtr("Reset Preferences"));
    findChild<QPushButton *>("preferencesReset")->hide();
    auto *grid = qobject_cast<QGridLayout *>(layout());
    grid->removeWidget(pages);
    grid->addWidget(pages, 1, 1, 1, 2);
    pages->setCurrentWidget(categoryPages[category]);
    heading->setText(qtr(categoryTitles[category]));
    updateResponsiveLayout();
}
void PrefsDialog::openResult(QTreeWidgetItem *item)
{
    if (!item) return;
    const auto &o = options[item->data(0, Qt::UserRole).toInt()];
    search->clear();
    selectCategory(o.category);
    const auto *reference = basicFor(qfu(o.config->psz_name));
    const bool raw = reference && strchr(reference->key,'/');
    if (!o.basic || raw || (reference && reference->advanced))
    {
        if (auto *advanced = categoryPages[o.category]->findChild<QPushButton *>(
                "preferencesAdvanced" + QString::number(o.category)))
            advanced->setChecked(true);
        if (!o.basic || raw)
            if (auto *all=categoryPages[o.category]->findChild<QToolButton *>("preferencesAllOptions"+QString::number(o.category)))
                all->setChecked(true);
        if (auto *module = categoryPages[o.category]->findChild<QToolButton *>(
                "preferencesModule-" + QString::number(o.category) + "-" + o.module))
            module->setChecked(true);
    }
    QWidget *target = nullptr;
    for (auto *candidate : categoryPages[o.category]->findChildren<QWidget *>())
        if (candidate->property("preferenceKey").toString()==qfu(o.config->psz_name) &&
            (!raw || candidate->objectName().startsWith("preference-native-")))
        { target=candidate;break; }
    if (auto *row = target)
    {
        row->show();
        if (auto *scroll = categoryPages[o.category]->findChild<QScrollArea *>())
        {
            // Expanding a lazy module changes several nested layouts. Resolve
            // their geometry before asking the scroll area to reveal the row;
            // otherwise ensureWidgetVisible sees its pre-expansion position.
            for (QWidget *parent = row; parent && parent != scroll; parent = parent->parentWidget())
                if (parent->layout()) parent->layout()->activate();
            scroll->widget()->adjustSize();
            scroll->ensureWidgetVisible(row);
        }
        row->setFocus(Qt::OtherFocusReason);
    }
}
void PrefsDialog::filter(const QString &text)
{
    if (text.isEmpty())
    {
        if (auto *item = categories->currentItem())
            selectCategory(item->data(Qt::UserRole).toInt());
        return;
    }
    for (int i = 0; i < results->topLevelItemCount(); ++i)
    {
        auto *row = results->topLevelItem(i);
        const auto &o = options[row->data(0, Qt::UserRole).toInt()];
        const QString searchable = qfu(o.config->psz_name) + optionLabel(o.config) + qfut(o.config->psz_text) +
                                   qfut(o.config->psz_longtext) + o.module +
                                   qtr(categoryNames[o.category]);
        row->setHidden(!searchable.contains(text, Qt::CaseInsensitive));
    }
    results->resizeColumnToContents(0);
    pages->setCurrentWidget(results);
    heading->setText(qtr("Search all settings"));
}
void PrefsDialog::showShortcuts()
{
    if (!shortcutsPage)
    {
        shortcutsPage = new QWidget(this);
        auto *layout = new QGridLayout(shortcutsPage);
        layout->setContentsMargins(0, 4, 0, 0);
        layout->setSpacing(8);
        shortcutsPage->setProperty("redesignShortcutEditor", true);
        shortcuts = new KeySelectorControl(shortcutsPage);
        controls.push_back(shortcuts);
        shortcuts->insertInto(layout);
        pages->addWidget(shortcutsPage);
    }
    categoryContainer->hide();
    categories->hide();
    search->hide();
    heading->setContentsMargins(10, 0, 0, 0);
    QFont shortcutHeadingFont = heading->font();
    shortcutHeadingFont.setPixelSize(14);
    heading->setFont(shortcutHeadingFont);
    heading->setStyleSheet("font-size:14px;font-weight:400;");
    findChild<QPushButton *>("preferencesReset")->setText(qtr("Reset shortcuts"));
    findChild<QPushButton *>("preferencesReset")->show();
    markEdited();
    auto *grid = qobject_cast<QGridLayout *>(layout());
    grid->removeWidget(pages);
    grid->addWidget(pages, 1, 0, 1, 3);
    grid->setRowMinimumHeight(2, 64);
    pages->setCurrentWidget(shortcutsPage);
    heading->setText(qtr("Keyboard Shortcuts"));
    resize(width(), qMin(height(), 800));
}
void PrefsDialog::editShortcut(const QString &option)
{
    showShortcuts();
    shortcuts->editShortcut(option);
}

void PrefsDialog::save()
{
    if (pluginScan) return;
    if (draftValues.contains("extra-options"))
    {
        char *error = nullptr;
        const int result = config_ValidateSavedOptions(qtu(draftValues.value("extra-options").toString()),&error);
        const auto detail = error ? qfu(error) : qtr("quoting or option syntax");
        free(error);
        if (result != VLC_SUCCESS)
        {
            QMessageBox::warning(this,qtr("Invalid additional options"),qtr("Check %1. Use --name=value or boolean --name/--no-name. Launch-only options and media paths cannot be saved here.").arg(detail));
            return;
        }
    }
    // ConfigControl applies to VLC's in-memory configuration before the native
    // atomic file save. Restore that memory on failure; keep staged editors for
    // retry, and keep Cancel from later leaking a failed save into another one.
    QStringList keys = property("optionKeys").toStringList();
    for (auto it=draftValues.cbegin(); it!=draftValues.cend(); ++it)
        if (!keys.contains(it.key())) keys.push_back(it.key());
    const auto previous = captureConfigValues(keys);
    for (auto *control : controls)
        if (!stagedControls.contains(control)) control->doApply();
    for (auto it=draftValues.cbegin(); it!=draftValues.cend(); ++it)
    {
        const auto *config = config_FindConfig(qtu(it.key()));
        if (!config) continue;
        switch (CONFIG_CLASS(config->i_type))
        {
            case CONFIG_ITEM_STRING: config_PutPsz(qtu(it.key()), qtu(it.value().toString())); break;
            case CONFIG_ITEM_FLOAT: config_PutFloat(qtu(it.key()), it.value().toFloat()); break;
            default: config_PutInt(qtu(it.key()), it.value().toLongLong()); break;
        }
    }
    if (config_SaveConfigFile(p_intf) != 0)
    {
        restoreConfigValues(previous);
        QMessageBox::warning(
            this, qtr("Cannot save preferences"),
            qtr("The preferences file could not be saved. Check its permissions and available disk "
                "space. Your staged edits remain available to retry."));
        return;
    }
#ifdef _WIN32
    if (language && language->currentData().toString() != originalLanguage)
    {
        QSettings registry("HKEY_CURRENT_USER\\Software\\VideoLAN\\VLC", QSettings::NativeFormat);
        if (language->currentData().toString() == "auto")
        {
            if (registry.contains("Lang"))
                registry.remove("Lang");
        }
        else
            registry.setValue("Lang", language->currentData());
        registry.sync();
        if (registry.status() != QSettings::NoError)
        {
            QMessageBox::warning(this, qtr("Cannot save interface language"),
                                 qtr("VLC preferences were saved, but Windows could not save the "
                                     "interface language. Other changes remain saved."));
            return;
        }
    }
#endif
    if (p_intf->p_mi)
    {
        if (selectedTheme >= 0)
            p_intf->p_mi->getColorScheme()->setCurrentIndex(selectedTheme);
        p_intf->p_mi->reloadPrefs();
    }
    accept();
}
void PrefsDialog::reject()
{
    if (pluginScan) return;
    QVLCDialog::reject();
}
void PrefsDialog::reset()
{
    if (pluginScan) return;
    const bool shortcutsOnly = shortcuts && pages->currentWidget() == shortcutsPage;
    auto *question = new QMessageBox(QMessageBox::Question,
        shortcutsOnly ? qtr("Reset shortcuts") : qtr("Reset Preferences"),
        shortcutsOnly ? qtr("Restore the default keyboard shortcuts? Choose Save to keep this change.")
            : qtr("Reset VLC preferences to their defaults? Saved media, bookmarks and subtitle files are retained. Restart VLC after resetting."),
        QMessageBox::Reset | QMessageBox::Cancel, this);
    question->setAttribute(Qt::WA_DeleteOnClose);
    question->setDefaultButton(QMessageBox::Cancel);
    applyRedesignDialogStyle(question, p_intf);
    connect(question, &QDialog::finished, this, [this, shortcutsOnly](int result) {
        if (result != QMessageBox::Reset) return;
        if (shortcutsOnly) shortcuts->resetToDefaults();
        else resetPreferences();
    });
    question->open();
}
void PrefsDialog::resetPreferences()
{
    const auto previous = captureConfigValues(property("optionKeys").toStringList());
    config_ResetAll();
    if (config_SaveConfigFile(p_intf) != 0)
    {
        restoreConfigValues(previous);
        QMessageBox::warning(this, qtr("Cannot save preferences"),
                             qtr("The reset could not be saved. Existing preferences are retained."));
        return;
    }
    getSettings()->clear();
    p_intf->preferencesResetPending = true;
#ifdef _WIN32
    // Checking/removing an absent language override must not create its key.
    QVLCRegistry nativeRegistry(HKEY_CURRENT_USER);
    if (nativeRegistry.RegistryValueExists("Software\\VideoLAN\\VLC", "Lang"))
    {
        QSettings registry("HKEY_CURRENT_USER\\Software\\VideoLAN\\VLC", QSettings::NativeFormat);
        registry.remove("Lang");
    }
#endif
    if (p_intf->p_mi)
    {
        p_intf->p_mi->reloadPrefs();
        p_intf->p_mi->reloadFromSettings();
    }
    accept();
}
bool PrefsDialog::eventFilter(QObject *object, QEvent *event)
{
    if ((object == search || object == results) && event->type() == QEvent::KeyPress)
    {
        const auto *key = static_cast<QKeyEvent *>(event);
        if (key->key() == Qt::Key_Return || key->key() == Qt::Key_Enter)
        {
            QTreeWidgetItem *item = object == results ? results->currentItem() : nullptr;
            if (!search->text().isEmpty() || object == results)
            {
                if (!item || item->isHidden())
                    for (int row = 0; row < results->topLevelItemCount(); ++row)
                        if (!results->topLevelItem(row)->isHidden())
                        { item = results->topLevelItem(row); break; }
                openResult(item);
            }
            event->accept();
            return true;
        }
    }

    if (object == heading && event->type() == QEvent::MouseButtonPress)
    {
        auto *mouse = static_cast<QMouseEvent *>(event);
        if (mouse->button() == Qt::LeftButton && windowHandle())
            return windowHandle()->startSystemMove();
    }
    return QVLCDialog::eventFilter(object, event);
}
