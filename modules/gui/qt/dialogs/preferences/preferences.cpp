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
#include <QApplication>
#include <QAbstractSpinBox>
#include <QCheckBox>
#include <QComboBox>
#include <QColorDialog>
#include <QButtonGroup>
#include <QPainter>
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
#include <QSizeGrip>
#include <QStackedWidget>
#include <QToolButton>
#include <QTreeWidget>
#include <QTransform>
#include <QWindow>
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

  protected:
    void paintEvent(QPaintEvent *) override
    {
        QPainter p(this);
        p.setRenderHint(QPainter::Antialiasing);
        const bool on = isChecked();
        p.setPen(Qt::NoPen);
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
                                      N_("Playback Defaults"),
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
struct Basic
{
    const char *key;
    int category;
    const char *group;
};
const Basic basicOptions[] = {{"qt-accent-color", 0, N_("Appearance")},
                              {"interact", 0, N_("Startup")},
                              {"qt-updates-notif", 0, N_("Startup")},
                              {"qt-verbose", 0, N_("Diagnostics")},
                              {"file-logging", 0, N_("Diagnostics")},
                              {"logfile", 0, N_("Diagnostics")},
                              {"log-verbose", 0, N_("Diagnostics")},
                              {"qt-system-tray", 1, N_("Window")},
                              {"qt-close-to-system-tray", 1, N_("Window")},
                              {"qt-start-minimized", 1, N_("Startup")},
                              {"qt-video-autoresize", 1, N_("Window")},
                              {"qt-auto-raise", 1, N_("Window")},
                              {"qt-name-in-title", 1, N_("Window")},
                              {"qt-pause-minimized", 1, N_("Window")},
                              {"qt-notification", 1, N_("Notifications")},
                              {"save-recentplay", 2, N_("History")},
                              {"metadata-network-access", 2, N_("Network Access")},
                              {"qt-updates-days", 2, N_("Network Access")},
                              {"extrashort-jump-size", 3, N_("Skip Amounts")},
                              {"short-jump-size", 3, N_("Skip Amounts")},
                              {"medium-jump-size", 3, N_("Skip Amounts")},
                              {"long-jump-size", 3, N_("Skip Amounts")},
                              {"mouse-pause-policy", 3, N_("Mouse")},
                              {"hotkeys-mousewheel-mode", 3, N_("Mouse")},
                              {"hotkeys-x-wheel-mode", 3, N_("Mouse")},
                              {"qt-disable-volume-keys", 3, N_("Keyboard")},
                              {"restore-playback-pos", 4, N_("Resume")},
                              {"start-paused", 4, N_("Playback")},
                              {"play-and-pause", 4, N_("Playback")},
                              {"play-and-stop", 4, N_("Playback")},
                              {"play-and-exit", 4, N_("Playback")},
                              {"repeat", 4, N_("Playback")},
                              {"loop", 4, N_("Playback")},
                              {"random", 4, N_("Playback")},
                              {"rate", 4, N_("Playback")},
                              {"video", 5, N_("Output")},
                              {"vout", 5, N_("Output")},
                              {"fullscreen", 5, N_("Window")},
                              {"video-on-top", 5, N_("Window")},
                              {"video-wallpaper", 5, N_("Window")},
                              {"video-title-show", 5, N_("On-Screen Messages")},
                              {"video-title-timeout", 5, N_("On-Screen Messages")},
                              {"snapshot-path", 5, N_("Snapshots")},
                              {"snapshot-format", 5, N_("Snapshots")},
                              {"audio", 6, N_("Output")},
                              {"aout", 6, N_("Output")},
                              {"stereo-mode", 6, N_("Output")},
                              {"qt-max-volume", 6, N_("Volume")},
                              {"volume-save", 6, N_("Volume")},
                              {"audio-language", 6, N_("Tracks & Languages")},
                              {"audio-time-stretch", 6, N_("Playback")},
                              {"audio-replay-gain-mode", 6, N_("Replay Gain")},
                              {"audio-replay-gain-preamp", 6, N_("Replay Gain")},
                              {"audio-replay-gain-peak-protection", 6, N_("Replay Gain")},
                              {"spu", 7, N_("Tracks & Languages")},
                              {"sub-language", 7, N_("Tracks & Languages")},
                              {"subsdec-encoding", 7, N_("Tracks & Languages")},
                              {"sub-autodetect-file", 7, N_("Loading Subtitles")},
                              {"sub-autodetect-fuzzy", 7, N_("Loading Subtitles")},
                              {"freetype-font", 7, N_("Appearance")},
                              {"freetype-rel-fontsize", 7, N_("Appearance")},
                              {"freetype-fontsize", 7, N_("Appearance")},
                              {"freetype-bold", 7, N_("Appearance")},
                              {"freetype-color", 7, N_("Appearance")},
                              {"freetype-opacity", 7, N_("Appearance")},
                              {"freetype-outline-thickness", 7, N_("Appearance")},
                              {"freetype-outline-color", 7, N_("Appearance")},
                              {"freetype-shadow-opacity", 7, N_("Appearance")},
                              {"osd", 7, N_("On-Screen Messages")},
                              {"qt-shortcut-feedback", 7, N_("On-Screen Messages")},
                              {"qt-shortcut-feedback-key", 7, N_("On-Screen Messages")},
                              {"qt-shortcut-feedback-duration", 7, N_("On-Screen Messages")},
                              {"one-instance", 8, N_("Opening Files")},
                              {"one-instance-when-started-from-file", 8, N_("Opening Files")},
                              {"playlist-enqueue", 8, N_("Opening Files")},
                              {"recursive", 8, N_("Opening Files")},
                              {"show-hiddenfiles", 8, N_("Opening Files")},
                              {"media-library", 8, N_("Metadata & Artwork")},
                              {"file-caching", 9, N_("Buffering")},
                              {"disc-caching", 9, N_("Buffering")},
                              {"network-caching", 9, N_("Buffering")},
                              {"live-caching", 9, N_("Buffering")},
                              {"http-proxy", 9, N_("Proxy")},
                              {"http-proxy-pwd", 9, N_("Proxy")},
                              {"gnutls-system-trust", 9, N_("Security")},
                              {"gnutls-priorities", 9, N_("Security")},
                              {"avcodec-hw", 10, N_("Decoding")},
                              {"postproc-q", 10, N_("Decoding")},
                              {"avcodec-skiploopfilter", 10, N_("Decoding")},
                              {"avcodec-threads", 10, N_("Decoding")},
                              {"drop-late-frames", 10, N_("Smooth Playback")},
                              {"high-priority", 10, N_("Smooth Playback")},
                              {"input-record-path", 11, N_("Recording")},
                              {"input-record-native", 11, N_("Recording")},
                              {"sout-display", 11, N_("Streaming")},
                              {"sout-audio", 11, N_("Streaming")},
                              {"sout-video", 11, N_("Streaming")},
                              {"sout-spu", 11, N_("Streaming")},
                              {"sout-x264-preset", 11, N_("Streaming")},
                              {"sout-x264-tune", 11, N_("Streaming")},
                              {"qt-autoload-extensions", 12, N_("Add-ons")}};
const Basic *basicFor(const QString &key)
{
    for (const auto &basic : basicOptions)
        if (key == QLatin1String(basic.key))
            return &basic;
    return nullptr;
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
    setStyleSheet(styleSheet() + "PrefsDialog#redesignPreferences { background:transparent; }");
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
                                       devicePixelRatioF())), QLineEdit::LeadingPosition);
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
    closeButton->setStyleSheet("padding:4px");
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
    for (int i = 0; i < 13; ++i)
    {
        if (i == 0 || i == 4 || i == 9)
        {
            auto *section = new QListWidgetItem(qtr(i == 0   ? "App"
                                                    : i == 4 ? "Media"
                                                             : "System"),
                                                categories);
            section->setFlags(Qt::NoItemFlags);
            if (i == 0) section->setSizeHint(QSize(188, 30));
            section->setData(Qt::UserRole, -1);
        }
        auto *item = new QListWidgetItem(qtr(i == 7 ? "Subtitles" : i == 11 ? "Recording" : categoryNames[i]), categories);
        item->setToolTip(qtr(categoryNames[i]));
        item->setData(Qt::UserRole, i);
        QIcon icon;
        const QString path = ":/redesign/icons/" + QString::fromLatin1(icons[i]) + ".svg";
        icon.addPixmap(
            sourceMask(path, property("figmaDark").toBool() ? QColor("#8f8f8f") : QColor("#2e2e2e"),
                       devicePixelRatioF()),
            QIcon::Normal);
        icon.addPixmap(sourceMask(path, palette().color(QPalette::Highlight), devicePixelRatioF()),
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
    auto *footer = new QHBoxLayout;
    footer->setContentsMargins(24, 0, 16, 0);
    auto *resetButton = new QPushButton(qtr("Reset Preferences"), this);
    resetButton->setObjectName("preferencesReset");
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
    layout->addLayout(footer, 2, 1, 1, 2);
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
}
void PrefsDialog::resizeEvent(QResizeEvent *event)
{
    QVLCDialog::resizeEvent(event);
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
        grid->setColumnStretch(10, compact || accent ? 0 : 318);
        row->setProperty("compactPreference", compact);
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
void PrefsDialog::addOption(QVBoxLayout *parent, const Option &o)
{
    const QString key = qfu(o.config->psz_name);
    const QColor accent = p_intf->p_mi ? p_intf->p_mi->getRedesignAccent() : QColor("#d37918");
    auto *row = new QWidget(this);
    row->setObjectName("preference-" + key);
    row->setFocusPolicy(Qt::StrongFocus);
    auto *grid = new QGridLayout(row);
    grid->setContentsMargins(0, 4, 0, 4);
    // Native controls use column 10. Empty legacy columns must not each add
    // another gap; retain one deliberate label/value gutter.
    grid->setHorizontalSpacing(0);
    grid->setColumnMinimumWidth(1, 12);
    grid->setColumnStretch(0, 454);
    grid->setColumnStretch(10, 318);
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
    else if (o.config->i_type == CONFIG_ITEM_BOOL)
    {
        grid->setColumnStretch(0, 1);
        grid->setColumnStretch(10, 0);
        auto *label = new QLabel(optionLabel(o.config), row);
        label->setWordWrap(true);
        grid->addWidget(label, 0, 0);
        auto *toggle = new SettingsSwitch(row, property("figmaDark").toBool(),
                                          accent);
        toggle->setAccessibleName(label->text());
        toggle->setObjectName("value-" + key);
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
    grid->setColumnMinimumWidth(1, 12);
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
        group->setObjectName("editor-" + key);
        group->setProperty("preferenceEditorGroup", true);
        group->setLayout(editorLayout);
        for (auto *button : group->findChildren<QPushButton *>()) button->setFixedHeight(34);
        if (auto *line = group->findChild<QLineEdit *>())
            line->setObjectName("value-" + key);
        grid->addWidget(group, 0, 10);
    }
    if (auto *item = grid->itemAtPosition(0, 10); item && item->widget() &&
        o.config->i_type != CONFIG_ITEM_BOOL && key != "qt-accent-color")
    {
        auto *editor = item->widget();
        if (!editor->property("preferenceEditorGroup").toBool())
            editor->setObjectName("value-" + key);
        if (editor->property("preferenceEditorGroup").toBool() ||
            qobject_cast<QLineEdit *>(editor) || qobject_cast<QComboBox *>(editor) ||
            qobject_cast<QAbstractSpinBox *>(editor))
            editor->setFixedHeight(34);
        grid->setAlignment(editor, Qt::Alignment());
        editor->setSizePolicy(QSizePolicy::Expanding, QSizePolicy::Fixed);
    }
    control->setParent(row);
    controls.push_back(control);
    auto *help = new QToolButton(row);
    help->setIcon(QIcon(sourceMask(":/redesign/icons/settings-info.svg", palette().text().color(),
                                   devicePixelRatioF())));
    help->setIconSize(QSize(24, 24));
    help->setStyleSheet("padding:0;background:transparent");
    help->setObjectName("help-" + key);
    help->setAccessibleName(qtr("Help for %1").arg(optionLabel(o.config)));
    help->setFixedSize(24, 24);
    if (auto *label = qobject_cast<QLabel *>(
            grid->itemAtPosition(0, 0) ? grid->itemAtPosition(0, 0)->widget() : nullptr))
    {
        label->setText(optionLabel(o.config));
        grid->removeWidget(label);
        auto *labelGroup = new QWidget(row);
        auto *labelLayout = new QHBoxLayout(labelGroup);
        labelLayout->setContentsMargins(0, 0, 0, 0);
        labelLayout->setSpacing(12);
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
    auto *description = new QLabel(text, row);
    description->setObjectName("description-" + key);
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
}
QWidget *PrefsDialog::createCategory(int category)
{
    auto *page = new QWidget(this);
    auto *outer = new QVBoxLayout(page);
    outer->setContentsMargins(32, 12, 0, 4);
    auto *scroll = new QScrollArea(page);
    scroll->setWidgetResizable(true);
    auto *body = new QWidget;
    auto *form = new QVBoxLayout(body);
    form->setContentsMargins(0, 0, 16, 20);
    form->setSpacing(8);
    scroll->setWidget(body);
    scroll->viewport()->setAutoFillBackground(false);
    body->setAutoFillBackground(false);
    outer->addWidget(scroll);
    auto action = [form, this](const QString &text, const char *name, auto callback)
    {
        auto *button = new QPushButton(text, this);
        button->setObjectName(name);
        connect(button, &QPushButton::clicked, this, callback);
        form->addWidget(button, 0, Qt::AlignLeft);
    };
    if (category == 3)
        action(qtr("Edit Keyboard Shortcuts"), "openKeyboardShortcuts",
               [this]() { showShortcuts(); });

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
        form->addLayout(toolbar);
        auto *extensions = new ExtensionTab(p_intf);
        extensions->setParent(this);
        extensions->layout()->setContentsMargins(0, 0, 0, 0);
        auto *filter = new QSortFilterProxyModel(extensions->extList);
        filter->setSourceModel(extensions->extList->model());
        filter->setFilterCaseSensitivity(Qt::CaseInsensitive);
        auto *oldSelection = extensions->extList->selectionModel();
        extensions->extList->setModel(filter);
        delete oldSelection;
        connect(extensions->extList->selectionModel(), &QItemSelectionModel::selectionChanged,
                extensions, &ExtensionTab::updateButtons);
        connect(extensionSearch, &QLineEdit::textChanged,
                filter, &QSortFilterProxyModel::setFilterFixedString);
        extensions->setMinimumHeight(260);
        form->addWidget(extensions);
        auto *explain = new QLabel(
            qtr("Use the add-on manager to install or remove supported packages. Internal decoder, "
                "output and filter modules remain in their media category's advanced options."), this);
        explain->setWordWrap(true);
        form->addWidget(explain);
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
        language->setMaximumWidth(318);
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
            themeOptions->setMaximumWidth(318);
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
                    [this](int index) { selectedTheme = index; });
            themeRow->addWidget(themeOptions, 1);
            form->addLayout(themeRow);
        }
    }
    QString group = category == 0 ? qtr("Appearance") : QString();
    for (const auto &o : options)
    {
        if (o.category != category || !o.basic)
            continue;
        if (o.group != group)
        {
            group = o.group;
            auto *label = new QLabel(group, this);
            label->setProperty("redesignSection", true);
            QFont font = label->font();
            font.setPixelSize(16);
            font.setWeight(QFont::Medium);
            label->setFont(font);
            label->setStyleSheet("font-size:16px;font-weight:500;");
            label->setContentsMargins(0, 20, 0, 8);
            form->addWidget(label);
        }
        addOption(form, o);
    }
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
    connect(advanced, &QToolButton::toggled, this,
            [this, advanced, advancedBody, advancedForm, category, disclosure](bool open)
            {
                advanced->setIcon(QIcon(open ? disclosure.transformed(QTransform().rotate(180)) : disclosure));
                if (open && !advancedBody->property("built").toBool())
                {
                    QMap<QString, QVector<int>> modules;
                    for (int i = 0; i < options.size(); ++i)
                        if (options[i].category == category && !options[i].basic)
                            modules[options[i].module].push_back(i);
                    for (auto it = modules.cbegin(); it != modules.cend(); ++it)
                    {
                        auto *toggle = new QToolButton;
                        toggle->setObjectName("preferencesModule-" + it.key());
                        toggle->setText(it.key());
                        toggle->setCheckable(true);
                        toggle->setArrowType(Qt::RightArrow);
                        toggle->setToolButtonStyle(Qt::ToolButtonTextBesideIcon);
                        advancedForm->addWidget(toggle);
                        auto *moduleBody = new QWidget;
                        auto *moduleForm = new QVBoxLayout(moduleBody);
                        moduleForm->setContentsMargins(8, 0, 0, 8);
                        moduleBody->hide();
                        advancedForm->addWidget(moduleBody);
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
                                });
                    }
                    advancedBody->setProperty("built", true);
                }
                advancedBody->setVisible(open);
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
    if (!o.basic)
    {
        if (auto *advanced = categoryPages[o.category]->findChild<QPushButton *>(
                "preferencesAdvanced" + QString::number(o.category)))
            advanced->setChecked(true);
        if (auto *module = categoryPages[o.category]->findChild<QToolButton *>(
                "preferencesModule-" + o.module))
            module->setChecked(true);
    }
    if (auto *row = categoryPages[o.category]->findChild<QWidget *>(
            QString("preference-") + qfu(o.config->psz_name)))
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
    auto *grid = qobject_cast<QGridLayout *>(layout());
    grid->removeWidget(pages);
    grid->addWidget(pages, 1, 0, 1, 3);
    grid->setRowMinimumHeight(2, 64);
    pages->setCurrentWidget(shortcutsPage);
    heading->setText(qtr("Keyboard Shortcuts"));
    resize(width(), qMin(height(), 800));
}
void PrefsDialog::save()
{
    // ConfigControl applies to VLC's in-memory configuration before the native
    // atomic file save. Restore that memory on failure; keep staged editors for
    // retry, and keep Cancel from later leaking a failed save into another one.
    const auto previous = captureConfigValues(property("optionKeys").toStringList());
    for (auto *control : controls)
        control->doApply();
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
void PrefsDialog::reset()
{
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
