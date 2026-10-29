/*****************************************************************************
 * main_interface.cpp : Main interface
 ****************************************************************************
 * Copyright (C) 2006-2011 VideoLAN and AUTHORS
 *
 * Authors: Clément Stenac <zorglub@videolan.org>
 *          Jean-Baptiste Kempf <jb@videolan.org>
 *          Ilkka Ollakka <ileoo@videolan.org>
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
 * along with this program; if not, write to the Free Software Foundation, Inc.,
 * 51 Franklin Street, Fifth Floor, Boston MA 02110-1301, USA.
 *****************************************************************************/

#ifdef HAVE_CONFIG_H
# include "config.h"
#endif

#include "qt.hpp"

#include <QQmlEngine>
#include <QJSEngine>

#include "mainctx.hpp"
#include "legacy_font_setup.hpp"
#include "mainctx_submodels.hpp"
#include "medialibrary/mlhelper.hpp"
#include "medialibrary/mlbookmarkmodel.hpp"
#include <vlc_actions.h>
#include <vlc_modules.h>
#include <vlc_plugin.h>

#include "compositor.hpp"
#include "util/renderer_manager.hpp"
#include "util/csdbuttonmodel.hpp"

#include "util/vlchotkeyconverter.hpp"
#include "util/qt_dirs.hpp"                     // toNativeSeparators

#include "util/color_scheme_model.hpp"

#include "widgets/native/interface_widgets.hpp"     // bgWidget, videoWidget

#include "playlist/playlist_controller.hpp"
#include "player/player_controller.hpp"

#include "dialogs/dialogs_provider.hpp"
#include "dialogs/systray/systray.hpp"

#include "videosurface.hpp"

#include "menus/menus.hpp"                            // Menu creation

#include "dialogs/toolbar/controlbar_profile_model.hpp"
#include "dialogs/help/help.hpp"

#include <QKeyEvent>
#include <QPalette>
#include <QSettings>
#include <QJsonDocument>
#include <QFileDialog>
#include <QFileInfo>

#include <QUrl>
#include <QDate>
#include <QMimeData>
#include <QClipboard>
#include <QInputDialog>
#include <QMenu>
#include <QPointer>
#include <cmath>

#include <QQmlProperty>

#include <QWindow>
#include <QScreen>

#include <QOperatingSystemVersion>

#if QT_VERSION >= QT_VERSION_CHECK(6, 8, 0)
#include <QStyleHints>
#endif

#ifdef _WIN32
#include <QFileInfo>
#endif

#include <vlc_interface.h>
#include <vlc_preparser.h>

#define VLC_REFERENCE_SCALE_FACTOR 96.

using  namespace vlc::playlist;

struct MainCtx::OnboardingFolderRequest
{
    MainCtx *owner;
    quint64 revision;
    QString url;
    QVariantMap values;
    vlc_ml_event_callback_t *callback=nullptr;
};

static bool onboardingFolderMatches(const QString &first,const QString &second,bool descendants=false)
{
    const auto normalized=[](const QString &value){
        return QUrl(value).adjusted(QUrl::StripTrailingSlash|QUrl::NormalizePathSegments).toString(QUrl::FullyEncoded);
    };
#ifdef _WIN32
    const auto sensitivity=Qt::CaseInsensitive;
#else
    const auto sensitivity=Qt::CaseSensitive;
#endif
    const auto target=normalized(first), candidate=normalized(second);
    return target.compare(candidate,sensitivity)==0||(descendants&&target.startsWith(candidate+QLatin1Char('/'),sensitivity));
}

static int HotkeyFeedbackCB(vlc_object_t *, const char *, vlc_value_t,
                            vlc_value_t value, void *opaque)
{
    auto *ctx=static_cast<MainCtx *>(opaque);
    QMetaObject::invokeMethod(ctx, [ctx,key=int(value.i_int)]() {
        // Runs on the Qt owner; no OS input, synchronous core work or timer.
        ctx->dispatchShortcutFeedback(key);
    }, Qt::QueuedConnection);
    return VLC_SUCCESS;
}

// #define DEBUG_INTF

/* Callback prototypes */
static int PopupMenuCB( vlc_object_t *p_this, const char *psz_variable,
                        vlc_value_t old_val, vlc_value_t new_val, void *param );
static int IntfShowCB( vlc_object_t *p_this, const char *psz_variable,
                       vlc_value_t old_val, vlc_value_t new_val, void *param );
static int IntfBossCB( vlc_object_t *p_this, const char *psz_variable,
                       vlc_value_t old_val, vlc_value_t new_val, void *param );
static int IntfRaiseMainCB( vlc_object_t *p_this, const char *psz_variable,
                           vlc_value_t old_val, vlc_value_t new_val,
                           void *param );

const QEvent::Type MainCtx::ToolbarsNeedRebuild =
        (QEvent::Type)QEvent::registerEventType();

namespace
{

template <typename T>
T loadVLCOption(vlc_object_t *obj, const char *name);

template <>
int loadVLCOption<int>(vlc_object_t *obj, const char *name)
{
    return var_InheritInteger(obj, name);
}

template <>
float loadVLCOption<float>(vlc_object_t *obj, const char *name)
{
    return var_InheritFloat(obj, name);
}

template <>
bool loadVLCOption<bool>(vlc_object_t *obj, const char *name)
{
    return var_InheritBool(obj, name);
}

}

MainCtx::MainCtx(qt_intf_t *_p_intf)
    : p_intf(_p_intf)
    , m_csdButtonModel {std::make_unique<CSDButtonModel>(this, this)}
{
    // If `playlist-autostart` is set, and there are initial files
    // we don't bother loading main display just to unload it
    // immediately after. Instead, we directly load the player
    // page:
    if (var_InheritBool(p_intf, "playlist-autostart"))
    {
        // We can not use `vlc_playlist_GetCurrentIndex()`, because
        // playlist starts playing after the interface is added.
        // We also can not use the playlist controller because it
        // is not updated yet.
        vlc_playlist_locker lock(p_intf->p_playlist);

        if (vlc_playlist_Count(p_intf->p_playlist) > 0)
        {
            m_mainInterfaceModes |= MAININTERFACE_MODE_PLAYER;
        }
    }

    /**
     *  Configuration and settings
     *  Pre-building of interface
     **/

    settings = getSettings();
    m_legacyFont = new LegacyFontSetup(this);
    m_colorScheme = new ColorSchemeModel(this);
    connect(qGuiApp,&QGuiApplication::paletteChanged,this,&MainCtx::redesignAccentChanged);

#if QT_VERSION >= QT_VERSION_CHECK(6, 8, 0)
    connect(m_colorScheme, &ColorSchemeModel::currentChanged, qGuiApp, [colorScheme = m_colorScheme]() {
        QStyleHints *const styleHints = qGuiApp->styleHints();
        if (unlikely(!styleHints))
            return;

        Qt::ColorScheme scheme;
        switch (colorScheme->currentScheme())
        {
        case ColorSchemeModel::ColorScheme::Day:
            scheme = Qt::ColorScheme::Light;
            break;
        case ColorSchemeModel::ColorScheme::Night:
            scheme = Qt::ColorScheme::Dark;
            break;
        case ColorSchemeModel::ColorScheme::System:
        default:
            styleHints->unsetColorScheme();
            return;
        }

        styleHints->setColorScheme(scheme);
    });
#endif

    m_sort = new SortCtx(this);
    m_search = new SearchCtx(this);
    m_playqueuePanel = new SidePanelCtx(this);
    m_navigationPanel = new SidePanelCtx(this);

    // getOSInfo();
    QOperatingSystemVersion currentOS = QOperatingSystemVersion::current();
    switch (currentOS.type()) {
    case QOperatingSystemVersion::OSType::Windows:
        m_osName = Windows;
        break;

    default:
        m_osName = Unknown;
        break;
    }
    m_osVersion = (currentOS.majorVersion());

    loadPrefs(false);
    loadFromSettingsImpl(false);

    /* Get the available interfaces */
    m_extraInterfaces = new VLCVarChoiceModel(VLC_OBJECT(p_intf->intf), "intf-add", this);

    vlc_medialibrary_t* ml = vlc_ml_instance_get( p_intf );
    b_hasMedialibrary = (ml != NULL);
    if (b_hasMedialibrary) {
        m_medialib = new MediaLib(p_intf, p_intf->p_mainPlaylistController);
    }

    /* Controlbar Profile Model Creation */
    m_controlbarProfileModel = new ControlbarProfileModel(p_intf->mainSettings, this);

    const QUrl homeUrl = QUrl::fromLocalFile(QVLCUserDir( VLC_HOME_DIR ));
    m_dialogFilepath = getSettings()->value( "filedialog-path", homeUrl ).toUrl();

    QString platformName = QGuiApplication::platformName();

    b_hasWayland = platformName.startsWith(QLatin1String("wayland"), Qt::CaseInsensitive);

    /*********************************
     * Create the Systray Management *
     *********************************/
    //postpone systray initialisation to speedup starting time
    QMetaObject::invokeMethod(this, &MainCtx::initSystray, Qt::QueuedConnection);

    /*************************************************************
     * Connect the input manager to the GUI elements it manages  *
     * Beware initSystray did some connects on input manager too *
     *************************************************************/
    /**
     * Connects on nameChanged()
     * Those connects are different because options can impeach them to trigger.
     **/
    /* Main Interface statusbar */
    /* and title of the Main Interface*/
    connect( THEMIM, &PlayerController::inputChanged, this, &MainCtx::onInputChanged );
    connect( THEMIM, &PlayerController::hasVideoOutputChanged, this, &MainCtx::onVOutChanged );

    /* END CONNECTS ON IM */

    /* VideoWidget connects for asynchronous calls */
    connect( this, &MainCtx::askToQuit, THEDP, &DialogsProvider::quit, Qt::QueuedConnection  );
    connect(this, &MainCtx::onboardingRequestedChanged, THEDP, &DialogsProvider::firstRunDialogVisibleChanged);

    /** END of CONNECTS**/


    /************
     * Callbacks
     ************/
    libvlc_int_t* libvlc = vlc_object_instance(p_intf);
    var_AddCallback( libvlc, "intf-toggle-fscontrol", IntfShowCB, p_intf );
    var_AddCallback( libvlc, "intf-boss", IntfBossCB, p_intf );
    var_AddCallback( libvlc, "intf-show", IntfRaiseMainCB, p_intf );

    /* Register callback for the intf-popupmenu variable */
    var_AddCallback( libvlc, "intf-popupmenu", PopupMenuCB, p_intf );

    if( var_InheritBool( p_intf, "qt-privacy-ask") )
    {
        //postpone dialog call, as composition might not be ready yet
        QMetaObject::invokeMethod(this, [](){
            THEDP->firstRunDialog();
        }, Qt::QueuedConnection);
    }
    else if (m_medialib)
    {
        QMetaObject::invokeMethod(m_medialib, &MediaLib::reload, Qt::QueuedConnection);
    }

    const struct vlc_preparser_cfg cfg = []{
        struct vlc_preparser_cfg cfg{};
        cfg.types = VLC_PREPARSER_TYPE_PARSE;
        cfg.max_parser_threads = 1;
        cfg.timeout = 0;
        cfg.external_process = false;
        return cfg;
    }();
    m_network_preparser = vlc_preparser_New(VLC_OBJECT(libvlc), &cfg);

#ifdef UPDATE_CHECK
    /* Checking for VLC updates */
    if( var_InheritBool( p_intf, "qt-updates-notif" ) &&
        !var_InheritBool( p_intf, "qt-privacy-ask" ) )
    {
        int interval = var_InheritInteger( p_intf, "qt-updates-days" );
        if( QDate::currentDate() >
            getSettings()->value( "updatedate" ).toDate().addDays( interval ) )
        {
            /* check for update at startup */
            getUpdateModel()->checkUpdate();
            getSettings()->setValue( "updatedate", QDate::currentDate() );
        }
    }
#endif

    m_threadRunner = new ThreadRunner();

    m_initialEffectiveMainInterfaceMode = getEffectiveMainInterfaceMode();
    getBookmarks();
    initializeHotkeyFeedback();
    var_AddCallback(libvlc,"key-pressed",HotkeyFeedbackCB,this);
}

void MainCtx::trackPlayerMenu(QMenu *menu)
{
    const auto update = [this, menu](bool open) {
        const bool wasOpen = isPlayerMenuOpen();
        if (open)
            m_playerMenus.insert(menu);
        else
            m_playerMenus.remove(menu);
        if (wasOpen != isPlayerMenuOpen())
            emit playerMenuOpenChanged();
    };
    connect(menu, &QMenu::aboutToShow, this, [update] { update(true); });
    connect(menu, &QMenu::aboutToHide, this, [update] { update(false); });
    connect(menu, &QObject::destroyed, this, [update] { update(false); });
}

void MainCtx::closePlayerMenus()
{
    QList<QPointer<QMenu>> menus;
    for (auto *menu : m_playerMenus)
        menus.append(QPointer<QMenu>(menu));
    for (const auto &menu : menus)
        if (menu)
            menu->close();
}

MainCtx::~MainCtx()
{
    if(m_onboardingFolderRequest){
        if(m_onboardingFolderRequest->callback)
            m_medialib->unregisterEventListener(m_onboardingFolderRequest->callback);
        m_onboardingFolderRequest.reset();
    }
    /* Save states */

    // An app close during onboarding must not persist an unfinished preview.
    if(m_beforePreviewTheme>=0)m_colorScheme->setCurrentIndex(m_beforePreviewTheme);

    var_DelCallback(vlc_object_instance(p_intf),"key-pressed",HotkeyFeedbackCB,this);
    m_threadRunner->destroy();

    if ( !p_intf->preferencesResetPending)
    {
        settings->beginGroup("MainWindow");
        settings->setValue( "ShowRemainingTime", m_showRemainingTime );
        settings->setValue( "interface-scale", QString::number( m_intfUserScaleFactor ) );

        /* Save playlist state */
        settings->setValue( "playqueue-panel-docked", m_playqueuePanel->m_docked );
        settings->setValue( "playqueue-panel-visible", m_playqueuePanel->m_visible );
        settings->setValue( "playqueue-panel-width", QString::number( m_playqueuePanel->m_width ) );

        settings->setValue( "navigation-panel-visible", m_navigationPanel->m_visible );
        settings->setValue( "navigation-panel-width", QString::number( m_navigationPanel->m_width ) );

        settings->setValue( "player-playlist-width", QString::number( m_playerPlaylistWidth ) );
        settings->setValue( "artist-albums-width", QString::number( m_artistAlbumsWidth ) );

        settings->setValue( "grid-view", m_gridView );
        settings->setValue( "grouping", m_grouping );

        settings->setValue( "color-scheme-index", m_colorScheme->currentIndex() );

        settings->setValue( "album-sections", m_albumSections );

        settings->setValue( "lyrics-mode", m_lyricsMode );

        /* Save the stackCentralW sizes */
        settings->endGroup();
    }
    else
    {
        settings->remove("MainWindow");
    }

    if( !p_intf->preferencesResetPending && var_InheritBool( p_intf, "save-recentplay" ) )
        getSettings()->setValue( "filedialog-path", m_dialogFilepath );
    else
        getSettings()->remove( "filedialog-path" );

    /* Unregister callbacks */
    libvlc_int_t* libvlc = vlc_object_instance(p_intf);
    var_DelCallback( libvlc, "intf-boss", IntfBossCB, p_intf );
    var_DelCallback( libvlc, "intf-show", IntfRaiseMainCB, p_intf );
    var_DelCallback( libvlc, "intf-toggle-fscontrol", IntfShowCB, p_intf );
    var_DelCallback( libvlc, "intf-popupmenu", PopupMenuCB, p_intf );

    delete m_bookmarks;
    if (m_medialib)
        delete m_medialib;

    if (m_network_preparser)
        vlc_preparser_Delete(m_network_preparser);

    p_intf->p_mi = NULL;
}

bool MainCtx::hasVLM() const {
#ifdef ENABLE_VLM
    return true;
#else
    return false;
#endif
}

bool MainCtx::useClientSideDecoration() const
{
    //don't show CSD when interface is fullscreen
    return !m_windowTitlebar;
}

bool MainCtx::hasFirstrun() const {
    return var_InheritBool(p_intf,  "qt-privacy-ask" );
}

void MainCtx::setUseGlobalShortcuts( bool useShortcuts )
{
    if (m_useGlobalShortcuts == useShortcuts)
        return;
    m_useGlobalShortcuts = useShortcuts;
    emit useGlobalShortcutsChanged(m_useGlobalShortcuts);
}

void MainCtx::setWindowSuportExtendedFrame(bool support) {
    if (m_windowSuportExtendedFrame == support)
        return;
    m_windowSuportExtendedFrame = support;
    emit windowSuportExtendedFrameChanged();
}

void MainCtx::setWindowExtendedMargin(unsigned int margin) {
    if (margin == m_windowExtendedMargin)
        return;
    m_windowExtendedMargin = margin;
    emit windowExtendedMarginChanged(margin);
}

/*****************************
 *   Main UI handling        *
 *****************************/

void MainCtx::loadPrefs(const bool callSignals)
{
    const auto loadFromVLCOption = [this, callSignals](auto &variable, const char *name
            , const std::function<void(MainCtx *)> signal)
    {
        using variableType = std::remove_reference_t<decltype(variable)>;

        const auto value =  loadVLCOption<variableType>(VLC_OBJECT(p_intf), name);
        if (value == variable)
            return;

        variable = value;
        if (callSignals && signal)
            signal(this);
    };

    bool minimalMode = false;
    /* Are we in the enhanced always-video mode or not ? */
    loadFromVLCOption(minimalMode, "qt-minimal-view", nullptr);
    setMinimalView(minimalMode);

    loadFromVLCOption(m_bgCone, "qt-bgcone", &MainCtx::bgConeToggled);

    /* Should the UI stays on top of other windows */
    loadFromVLCOption(b_interfaceOnTop, "video-on-top", [this](MainCtx *)
    {
        emit interfaceAlwaysOnTopChanged(b_interfaceOnTop);
    });

    loadFromVLCOption(m_hasToolbarMenu, "qt-menubar", &MainCtx::hasToolbarMenuChanged);

    loadFromVLCOption(m_windowTitlebar, "qt-titlebar" , &MainCtx::useClientSideDecorationChanged);

    loadFromVLCOption(m_smoothScroll, "qt-smooth-scrolling", &MainCtx::smoothScrollChanged);

    loadFromVLCOption(m_maxVolume, "qt-max-volume", &MainCtx::maxVolumeChanged);

    loadFromVLCOption(m_pinVideoControls, "qt-pin-controls", &MainCtx::pinVideoControlsChanged);

    loadFromVLCOption(m_pinOpacity, "qt-fs-opacity", &MainCtx::pinOpacityChanged);

    loadFromVLCOption(m_safeArea, "qt-safe-area", &MainCtx::safeAreaChanged);

    loadFromVLCOption(m_mouseHideTimeout, "mouse-hide-timeout", &MainCtx::mouseHideTimeoutChanged);
}

void MainCtx::loadFromSettingsImpl(const bool callSignals)
{
    const auto loadFromSettings = [this, callSignals](auto &variable, const char *name
            , const auto defaultValue, auto obj,  auto signal)
    {
        using variableType = std::remove_reference_t<decltype(variable)>;

        const auto value = getSettings()->value(name, defaultValue).template value<variableType>();
        if (value == variable)
            return;

        variable = value;
        if (obj && callSignals && signal)
            (obj->*signal)(variable);
    };

    loadFromSettings(m_playqueuePanel->m_docked, "MainWindow/playqueue-panel-docked", true, m_playqueuePanel, &SidePanelCtx::dockedChanged);
    loadFromSettings(m_playqueuePanel->m_visible, "MainWindow/playqueue-panel-visible", false, m_playqueuePanel, &SidePanelCtx::visibleChanged);
    loadFromSettings(m_playqueuePanel->m_width, "MainWindow/playqueue-panel-width", 120, m_playqueuePanel, &SidePanelCtx::widthChanged);

    loadFromSettings(m_navigationPanel->m_visible, "MainWindow/navigation-panel-visible", true, m_navigationPanel, &SidePanelCtx::visibleChanged);
    loadFromSettings(m_navigationPanel->m_width, "MainWindow/navigation-panel-width", 120, m_navigationPanel, &SidePanelCtx::widthChanged);

    loadFromSettings(m_playerPlaylistWidth, "MainWindow/player-playlist-width", 120, this, &MainCtx::playerPlaylistWidthChanged);
    loadFromSettings(m_artistAlbumsWidth, "MainWindow/artist-albums-width", 120, this,  &MainCtx::artistAlbumsWidthChanged);

    loadFromSettings(m_gridView, "MainWindow/grid-view", true, this, &MainCtx::gridViewChanged);

    loadFromSettings(m_grouping, "MainWindow/grouping", GROUPING_NONE, this, &MainCtx::groupingChanged);

    loadFromSettings(m_showRemainingTime, "MainWindow/ShowRemainingTime", false, this, &MainCtx::showRemainingTimeChanged);

    loadFromSettings(m_albumSections, "MainWindow/album-sections", true, this, &MainCtx::albumSectionsChanged);

    loadFromSettings(m_lyricsMode, "MainWindow/lyrics-mode", true, this, &MainCtx::lyricsModeChanged);

    const auto colorSchemeIndex = getSettings()->value( "MainWindow/color-scheme-index", 0 ).toInt();
    m_colorScheme->setCurrentIndex(colorSchemeIndex);

    /* user interface scale factor */
    auto userIntfScaleFactor = var_InheritFloat(p_intf, "qt-interface-scale");
    if (userIntfScaleFactor == -1)
        userIntfScaleFactor = getSettings()->value( "MainWindow/interface-scale", 1.0).toDouble();
    if (m_intfUserScaleFactor != userIntfScaleFactor)
    {
        m_intfUserScaleFactor = userIntfScaleFactor;
        updateIntfScaleFactor();
    }
}

void MainCtx::reloadPrefs()
{
    loadPrefs(true);
    emit redesignAccentChanged();
}

void MainCtx::onInputChanged( bool hasInput )
{
    if( hasInput == false )
        return;
    int autoRaise = var_InheritInteger( p_intf, "qt-auto-raise" );
    if ( autoRaise == MainCtx::RAISE_NEVER )
        return;
    if( THEMIM->hasVideoOutput() == true )
    {
        if( ( autoRaise & MainCtx::RAISE_VIDEO ) == 0 )
            return;
    }
    else if ( ( autoRaise & MainCtx::RAISE_AUDIO ) == 0 )
        return;
    emit askRaise();
}

void MainCtx::onVOutChanged( bool video )
{
    int autoRaise = var_InheritInteger( p_intf, "qt-auto-raise" );
    if ( video && ( autoRaise & MainCtx::RAISE_VIDEO ) )
        emit askRaise();
}

#ifdef KeyPress
#undef KeyPress
#endif
void MainCtx::sendHotkey(Qt::Key key , Qt::KeyboardModifiers modifiers)
{
    QKeyEvent event(QEvent::KeyPress, key, modifiers );
    int vlckey = qtEventToVLCKey(&event);
    sendVLCHotkey(vlckey);
}

void MainCtx::sendVLCHotkey(int vlcHotkey)
{
    var_SetInteger(vlc_object_instance(p_intf), "key-pressed", vlcHotkey);
}

QColor MainCtx::getRedesignAccent() const
{
    char *raw=var_InheritString(p_intf,"qt-accent-color");const QString value=qfu(raw).trimmed();free(raw);
    const QString effective=m_previewAccent.isNull()?value:m_previewAccent;
    if(effective==QStringLiteral("system")) {
#if QT_VERSION >= QT_VERSION_CHECK(6,6,0)
        return QGuiApplication::palette().color(QPalette::Accent);
#else
        return QGuiApplication::palette().color(QPalette::Highlight);
#endif
    }
    if(effective.isEmpty() || effective==QStringLiteral("default"))return QColor(QStringLiteral("#d37918"));
    const QColor color(effective);return color.isValid()?color:QColor(QStringLiteral("#d37918"));
}

QColor MainCtx::getRedesignAccentText() const
{
    const QColor accent=getRedesignAccent(), dark(Qt::black);
    // Preserve the original Figma glyph on orange. Other accents use the
    // higher-contrast black/white endpoint, including small primary labels.
    if(accent==QColor(QStringLiteral("#d37918")))return QColor(QStringLiteral("#2e2e2e"));
    const auto luminance=[](const QColor &color){
        const auto channel=[](double value){return value<=0.04045?value/12.92:std::pow((value+0.055)/1.055,2.4);};
        return 0.2126*channel(color.redF())+0.7152*channel(color.greenF())+0.0722*channel(color.blueF());
    };
    const double value=luminance(accent), foreground=luminance(dark);
    const double darkContrast=(std::max(value,foreground)+0.05)/(std::min(value,foreground)+0.05);
    return darkContrast>=1.05/(value+0.05)?dark:QColor(Qt::white);
}

QVariantMap MainCtx::presentationSettings() const
{
    char *raw=var_InheritString(p_intf,"qt-accent-color");
    QString accent=qfu(raw).trimmed();free(raw);
    if(accent.isEmpty())accent=QStringLiteral("default");
    if(accent!=QStringLiteral("system") && accent!=QStringLiteral("default"))
        accent=QColor(accent).isValid()?QColor(accent).name():QStringLiteral("default");
    return {{QStringLiteral("theme"),m_colorScheme->currentIndex()},
            {QStringLiteral("accent"),accent},{QStringLiteral("grid"),m_gridView},
            {QStringLiteral("remaining"),m_showRemainingTime}};
}

bool MainCtx::previewAppearance(int theme,const QString &accent)
{
    if(theme<0||theme>2||(accent!=QStringLiteral("system")&&accent!=QStringLiteral("default")&&!QColor(accent).isValid()))return false;
    if(m_previewAccent.isNull())m_beforePreviewTheme=m_colorScheme->currentIndex();
    m_previewAccent=accent;
    m_colorScheme->setCurrentIndex(theme);
    emit redesignAccentChanged();
    return true;
}

QString MainCtx::saveCustomization(const QString &encoded,const QVariantMap &values)
{
    return saveCustomizationImpl(encoded,values,false);
}

QString MainCtx::saveCustomizationImpl(const QString &encoded,const QVariantMap &values,bool dismissOnboarding)
{
    // One explicit, current presentation contract; never enumerate arbitrary
    // VLC options or import credentials/media into profile snapshots.
    if(!encoded.isEmpty()&&(encoded.size()>262144||!QJsonDocument::fromJson(encoded.toUtf8()).isObject()))
        return qtr("The saved player customization is invalid.");
    const bool apply=!values.isEmpty();
    const int theme=values.value(QStringLiteral("theme")).toInt();
    const QString accent=values.value(QStringLiteral("accent")).toString();
    if(apply&&(values.size()!=4||!values.contains(QStringLiteral("theme"))||!values.contains(QStringLiteral("accent"))||theme<0||theme>2||values.value(QStringLiteral("theme")).toDouble()!=theme
            ||values.value(QStringLiteral("grid")).metaType().id()!=QMetaType::Bool
            ||values.value(QStringLiteral("remaining")).metaType().id()!=QMetaType::Bool
            ||(accent!=QStringLiteral("system")&&accent!=QStringLiteral("default")&&!QColor(accent).isValid())))
        return qtr("The profile's appearance settings are invalid.");
    char *oldRaw=config_GetPsz("qt-accent-color");
    const QByteArray oldAccent=oldRaw?QByteArray(oldRaw):QByteArray();free(oldRaw);
    const auto oldAsk=config_GetInt("qt-privacy-ask");
    const bool saveCore=apply||dismissOnboarding;
    const auto restoreCore=[&](){
        if(apply)config_PutPsz("qt-accent-color",oldAccent.constData());
        if(dismissOnboarding)config_PutInt("qt-privacy-ask",oldAsk);
    };
    if(apply)config_PutPsz("qt-accent-color",qtu(accent));
    if(dismissOnboarding)config_PutInt("qt-privacy-ask",0);
    if(saveCore&&config_SaveConfigFile(p_intf)!=0){
        restoreCore();
        return qtr("VLC settings could not be saved. Your accepted player layout is unchanged.");
    }
    if(encoded.isEmpty()&&!apply)return {};
    const QString key=QStringLiteral("redesign/customization-v1");
    const QStringList keys={key,QStringLiteral("MainWindow/color-scheme-index"),QStringLiteral("MainWindow/grid-view"),QStringLiteral("MainWindow/ShowRemainingTime")};
    // QSettings retains its first error for the object's lifetime. A fresh
    // writer to the same native file permits a real retry after a write failure;
    // Qt shares this file's value cache with the existing settings owner.
    QSettings writer(settings->fileName(),settings->format());
    QVariantList old;for(const auto &k:keys)old.push_back(writer.value(k));
    if(!encoded.isEmpty())writer.setValue(key,encoded);
    if(apply){
        writer.setValue(keys[1],theme);
        writer.setValue(keys[2],values.value(QStringLiteral("grid")));
        writer.setValue(keys[3],values.value(QStringLiteral("remaining")));
    }
    writer.sync();
    if(writer.status()!=QSettings::NoError){
        for(int i=0;i<keys.size();++i){if(old[i].isValid())writer.setValue(keys[i],old[i]);else writer.remove(keys[i]);}
        writer.sync();
        restoreCore();
        if(saveCore&&config_SaveConfigFile(p_intf)!=0)
            return qtr("Interface settings could not be written, and the prior VLC preferences could not be restored on disk. Your accepted layout is unchanged. Restore write access before retrying.");
        return qtr("Interface settings could not be written. The accepted layout was preserved; check that the settings file is writable.");
    }
    if(apply){
        m_previewAccent=QString();
        m_beforePreviewTheme=-1;
        m_colorScheme->setCurrentIndex(theme);
        setGridView(values.value(QStringLiteral("grid")).toBool());
        setShowRemainingTime(values.value(QStringLiteral("remaining")).toBool());
        emit redesignAccentChanged();
    }
    return {};
}

QString MainCtx::chooseOnboardingFolder(const QString &current)
{
    return QFileDialog::getExistingDirectory(nullptr,qtr("Choose a Media Folder"),current);
}

QObject *MainCtx::legacyFont() const
{
    return m_legacyFont;
}

QString MainCtx::shortcutLabel(const QString &option) const
{
    const auto *parameter=config_FindConfig(qtu(option));
    if(!parameter||parameter->i_type!=CONFIG_ITEM_KEY)return qtr("Unassigned");
    char *raw=var_InheritString(p_intf,qtu(option));
    const QString text=qfu(raw);free(raw);
    QStringList result;
    for(const auto &key:text.split('\t',Qt::SkipEmptyParts))result.push_back(key);
    return result.isEmpty()?qtr("Unassigned"):result.join(QStringLiteral(" / "));
}

void MainCtx::completeRedesignOnboarding(bool finish,const QVariantMap &values,const QString &error,bool folderAdded)
{
    if(!error.isEmpty()){emit playerOnboardingFinished(error);return;}
    auto failure=saveCustomizationImpl({},finish?values:QVariantMap{},true);
    if(!failure.isEmpty()&&folderAdded)
        failure+=qtr(" The selected media folder was added, but setup has not finished. Restore write access and retry, or skip setup.");
    if(failure.isEmpty()&&!finish){
        previewAppearance(values.value(QStringLiteral("theme")).toInt(),values.value(QStringLiteral("accent")).toString());
        m_previewAccent=QString();m_beforePreviewTheme=-1;emit redesignAccentChanged();
    }
    if(failure.isEmpty()&&m_onboardingRequested){
        m_onboardingRequested=false;
        emit onboardingRequestedChanged();
    }
    emit playerOnboardingFinished(failure);
}

void MainCtx::resolveOnboardingFolder(quint64 revision,const QString &error,bool folderAdded)
{
    if(!m_onboardingFolderRequest||m_onboardingFolderRequest->revision!=revision)return;
    auto request=std::move(m_onboardingFolderRequest);
    m_medialib->unregisterEventListener(request->callback);
    completeRedesignOnboarding(true,request->values,error,folderAdded);
}

void MainCtx::finishRedesignOnboarding(bool finish,const QVariantMap &values,const QString &folder)
{
    // Keep the original request pending; the QML form is disabled until its
    // actual root-added/failure result, not until discovery has merely queued.
    if(m_onboardingFolderRequest)return;
    if(!finish||folder.isEmpty()){completeRedesignOnboarding(finish,values,{});return;}
    const QFileInfo entry(folder);
    if(!entry.exists()||!entry.isDir()||!m_medialib){completeRedesignOnboarding(finish,values,qtr("Choose an existing media folder with the media library enabled, or leave the folder blank."));return;}
    struct FolderResult{bool ok=false;bool existing=false;bool banned=false;};
    const auto url=QUrl::fromLocalFile(entry.absoluteFilePath()).toString(QUrl::FullyEncoded);
    const auto revision=++m_onboardingFolderRevision;
    m_onboardingFolderRequest=std::make_unique<OnboardingFolderRequest>(OnboardingFolderRequest{this,revision,url,values});
    m_onboardingFolderRequest->callback=m_medialib->registerEventListener([](void *data,const vlc_ml_event_t *event){
        if(event->i_type!=VLC_ML_EVENT_ENTRY_POINT_ADDED&&event->i_type!=VLC_ML_EVENT_DISCOVERY_FAILED)return;
        const auto *request=static_cast<OnboardingFolderRequest *>(data);
        const QString observed=QUrl::fromEncoded(event->i_type==VLC_ML_EVENT_ENTRY_POINT_ADDED?
            event->entry_point_added.psz_entry_point:event->discovery_failed.psz_entry_point).toString(QUrl::FullyEncoded);
        if(!onboardingFolderMatches(request->url,observed))return;
        const bool success=event->i_type==VLC_ML_EVENT_ENTRY_POINT_ADDED&&event->entry_point_added.b_success;
        QMetaObject::invokeMethod(request->owner,[owner=request->owner,revision=request->revision,success](){
            owner->resolveOnboardingFolder(revision,success?QString():qtr("The media library could not add that folder. Your other settings have not been changed."),success);
        },Qt::QueuedConnection);
    },m_onboardingFolderRequest.get());
    if(!m_onboardingFolderRequest->callback){
        m_onboardingFolderRequest.reset();
        completeRedesignOnboarding(true,values,qtr("The media library could not observe the folder operation. Your other settings have not been changed."));
        return;
    }
    m_medialib->runOnMLThread<FolderResult>(this,
        [url](vlc_medialibrary_t *ml,FolderResult &result){
            ml_unique_ptr<vlc_ml_folder_list_t> list(vlc_ml_list_entry_points(ml,nullptr));
            if(!list)return;
            for(const auto &folder:ml_range_iterate<vlc_ml_folder_t>(list)){
                if(!folder.psz_mrl)continue;
                if(onboardingFolderMatches(url,QUrl::fromEncoded(folder.psz_mrl).toString(QUrl::FullyEncoded))){result.existing=true;result.ok=true;return;}
            }
            ml_unique_ptr<vlc_ml_folder_list_t> banned(vlc_ml_list_banned_entry_points(ml,nullptr));
            if(!banned)return;
            for(const auto &folder:ml_range_iterate<vlc_ml_folder_t>(banned)){
                if(folder.psz_mrl&&onboardingFolderMatches(url,QUrl::fromEncoded(folder.psz_mrl).toString(QUrl::FullyEncoded),true)){
                    result.existing=true;result.banned=true;return;
                }
            }
            result.ok=vlc_ml_add_folder(ml,qtu(url))==VLC_SUCCESS;
        },
        [this,revision](quint64,FolderResult &result){
            if(result.existing||!result.ok)
                resolveOnboardingFolder(revision,result.banned?qtr("That folder is excluded in your existing library settings. Change the exclusion explicitly or leave this folder blank."):
                    result.ok?QString():qtr("The media library could not add that folder. Your other settings have not been changed."),false);
        });
}

MLBookmarkModel *MainCtx::getBookmarks()
{
    if (!m_medialib) return nullptr;
    if (!m_bookmarks) {
        m_bookmarks = new MLBookmarkModel(this);
        m_bookmarks->setPlayer(p_intf->p_mainPlayerController);
        m_bookmarks->setMl(m_medialib);
    }
    return m_bookmarks;
}
void MainCtx::addBookmark()
{
    if (auto *model = getBookmarks()) model->add();
}
void MainCtx::initializeHotkeyFeedback()
{
    // Bind feedback to this session's actual startup mappings. Core hotkeys also
    // take effect on restart; editing configuration cannot mislabel an old map.
    unsigned n=0;auto *config=module_config_get(module_get_main(),&n);
    for(unsigned i=0;i<n;++i){const auto &option=config[i];
        if(option.i_type!=CONFIG_ITEM_KEY || !option.psz_name || strncmp(option.psz_name,"global-",7)==0)continue;
        char *keys=var_InheritString(p_intf,option.psz_name);
        for(const auto &key:qfu(keys).split('	',Qt::SkipEmptyParts))
            m_shortcutActions.insert(vlc_str2keycode(qtu(key)),qfut(option.psz_text));
        free(keys);
    }
    module_config_free(config);
    char *add=var_InheritString(p_intf,"qt-key-add-bookmark");
    for(const auto &key:qfu(add).split('	',Qt::SkipEmptyParts)) {
        const int code=vlc_str2keycode(qtu(key));
        // Preserve conflicting prior core bindings rather than shadowing them.
        if(!m_shortcutActions.contains(code))m_bookmarkKeys.insert(code);
    }
    free(add);
}
void MainCtx::dispatchShortcutFeedback(int key)
{
    if(m_bookmarkKeys.contains(key)) {
        auto *model=getBookmarks();
        if(model && model->available() && p_intf->p_mainPlayerController->isSeekable()) {
            model->add();
            if(var_InheritBool(p_intf,"qt-shortcut-feedback"))
                emit hotkeyFeedback(qtr("Add bookmark"),var_InheritBool(p_intf,"qt-shortcut-feedback-key")?VLCKeyToString(key,true):QString(),var_InheritInteger(p_intf,"qt-shortcut-feedback-duration"));
        }
        return;
    }
    feedbackForHotkey(key);
}
void MainCtx::feedbackForHotkey(int key)
{
    if(var_InheritBool(p_intf,"qt-shortcut-feedback")&&m_shortcutActions.contains(key))
        emit hotkeyFeedback(m_shortcutActions.value(key),var_InheritBool(p_intf,"qt-shortcut-feedback-key")?VLCKeyToString(key,true):QString(),var_InheritInteger(p_intf,"qt-shortcut-feedback-duration"));
}

void MainCtx::updateIntfScaleFactor()
{
    auto newValue = m_intfUserScaleFactor;
    if (QWindow* window = p_intf->p_compositor ? p_intf->p_compositor->interfaceMainWindow() : nullptr)
    {
        QScreen* screen = window->screen();
        if (screen)
        {
            qreal dpi = screen->logicalDotsPerInch();
            newValue = m_intfUserScaleFactor * dpi / VLC_REFERENCE_SCALE_FACTOR;
        }
    }

    const int FACTOR_RESOLUTION = 100;
    if ( static_cast<int>(m_intfScaleFactor * FACTOR_RESOLUTION)
         == static_cast<int>(newValue * FACTOR_RESOLUTION) ) return;

    m_intfScaleFactor = newValue;
    emit intfScaleFactorChanged();
}

void MainCtx::onWindowVisibilityChanged(QWindow::Visibility visibility)
{
    m_windowVisibility = visibility;
}

void MainCtx::setHasAcrylicSurface(const bool v)
{
    if (m_hasAcrylicSurface == v)
        return;

    m_hasAcrylicSurface = v;
    emit hasAcrylicSurfaceChanged(v);
}

void MainCtx::incrementIntfUserScaleFactor(bool increment)
{
    if (increment)
        setIntfUserScaleFactor(m_intfUserScaleFactor + 0.1);
    else
        setIntfUserScaleFactor(m_intfUserScaleFactor - 0.1);
}

void MainCtx::setIntfUserScaleFactor(double newValue)
{
    const auto value = qBound(getMinIntfUserScaleFactor(), newValue, getMaxIntfUserScaleFactor());
    if (qFuzzyCompare(value, m_intfUserScaleFactor))
        return;
    m_intfUserScaleFactor = value;
    updateIntfScaleFactor();
}

void MainCtx::setHasToolbarMenu( bool hasToolbarMenu )
{
    if (m_hasToolbarMenu == hasToolbarMenu)
        return;

    m_hasToolbarMenu = hasToolbarMenu;

    config_PutInt("qt-menubar", (int) hasToolbarMenu);

    emit hasToolbarMenuChanged();
}

void MainCtx::setPinVideoControls(bool pinVideoControls)
{
    if (m_pinVideoControls == pinVideoControls)
        return;

    m_pinVideoControls = pinVideoControls;
    emit pinVideoControlsChanged();
}

void MainCtx::setPinOpacity(float pinOpacity)
{
    if (m_pinOpacity == pinOpacity)
        return;

    m_pinOpacity = pinOpacity;

    emit pinOpacityChanged();
}

inline void MainCtx::initSystray()
{
    bool b_systrayAvailable = QSystemTrayIcon::isSystemTrayAvailable();
    bool b_systrayWanted = var_InheritBool( p_intf, "qt-system-tray" );

    if( var_InheritBool( p_intf, "qt-start-minimized") )
    {
        if( b_systrayAvailable )
        {
            b_systrayWanted = true;
            b_hideAfterCreation = true;
        }
        else
            msg_Err( p_intf, "cannot start minimized without system tray bar" );
    }

    if( b_systrayAvailable && b_systrayWanted )
        m_systray = std::make_unique<VLCSystray>(this);
}

ThreadRunner* MainCtx::threadRunner() const
{
    return m_threadRunner;
}

QUrl MainCtx::folderMRL(const QString &fileMRL) const
{
    return folderMRL(QUrl::fromUserInput(fileMRL));
}

QUrl MainCtx::folderMRL(const QUrl &fileMRL) const
{
    if (fileMRL.isLocalFile())
    {
        const QString f = fileMRL.toLocalFile();
        return QUrl::fromLocalFile(QFileInfo(f).absoluteDir().absolutePath());
    }

    return {};
}

QString MainCtx::displayMRL(const QUrl &mrl) const
{
    return urlToDisplayString(mrl);
}

void MainCtx::setPlayerPlaylistWidth( double factor )
{
    if (factor > 0.0)
    {
        m_playerPlaylistWidth = factor;
        emit playerPlaylistWidthChanged(factor);
    }
}

void MainCtx::setbgCone(bool bgCone)
{
    if (m_bgCone == bgCone)
        return;

    m_bgCone = bgCone;

    emit bgConeToggled();
}

void MainCtx::setMinimalView(bool enable)
{
    if (m_mainInterfaceModes.testFlag(MAININTERFACE_MODE_MINIMAL) == enable)
        return;

    m_mainInterfaceModes.setFlag(MAININTERFACE_MODE_MINIMAL, enable);
    emit mainInterfaceModesChanged(m_mainInterfaceModes);
}

void MainCtx::setPlayerView(bool enable)
{
    if (m_mainInterfaceModes.testFlag(MAININTERFACE_MODE_PLAYER) == enable)
        return;

    m_mainInterfaceModes.setFlag(MAININTERFACE_MODE_PLAYER, enable);
    emit mainInterfaceModesChanged(m_mainInterfaceModes);
}

void MainCtx::setShowRemainingTime( bool show )
{
    m_showRemainingTime = show;
    emit showRemainingTimeChanged(show);
}

void MainCtx::setGridView(bool asGrid)
{
    m_gridView = asGrid;
    emit gridViewChanged( asGrid );
}

void MainCtx::setGrouping(Grouping grouping)
{
    m_grouping = grouping;

    emit groupingChanged(grouping);
}

void MainCtx::setAlbumSections(bool enabled)
{
    if (m_albumSections == enabled)
        return;

    m_albumSections = enabled;
    emit albumSectionsChanged(enabled);
}

void MainCtx::setLyricsMode(bool enabled)
{
    if (m_lyricsMode == enabled)
        return;

    m_lyricsMode = enabled;
    emit lyricsModeChanged(enabled);
}

void MainCtx::setInterfaceAlwaysOnTop( bool on_top )
{
    if (b_interfaceOnTop == on_top)
        return;

    b_interfaceOnTop = on_top;
    emit interfaceAlwaysOnTopChanged(on_top);
}

bool MainCtx::hasEmbededVideo() const
{
    return m_videoSurfaceProvider && m_videoSurfaceProvider->hasVideoEmbed();
}

void MainCtx::setVideoSurfaceProvider(VideoSurfaceProvider* videoSurfaceProvider)
{
    if (m_videoSurfaceProvider)
        disconnect(m_videoSurfaceProvider, &VideoSurfaceProvider::hasVideoEmbedChanged, this, &MainCtx::hasEmbededVideoChanged);
    m_videoSurfaceProvider = videoSurfaceProvider;
    if (m_videoSurfaceProvider)
        connect(m_videoSurfaceProvider, &VideoSurfaceProvider::hasVideoEmbedChanged,
                this, &MainCtx::hasEmbededVideoChanged,
                Qt::QueuedConnection);
    emit hasEmbededVideoChanged(m_videoSurfaceProvider && m_videoSurfaceProvider->hasVideoEmbed());
}

QJSValue MainCtx::urlListToMimeData(const QJSValue &array) {
    // NOTE: Due to a Qt regression since 17318c4
    //       (Nov 11, 2022), it is not possible to
    //       use RFC-2483 compliant string here.
    //       This regression was later corrected by
    //       c25f53b (Jul 31, 2024).
    // NOTE: Qt starts supporting string list since
    //       17318c4, so starting from 6.5.0 a string
    //       list can be used which is not affected
    //       by the said issue. For Qt versions below
    //       6.5.0, use byte array which is used as is
    //       by Qt.
    assert(array.property("length").toInt() > 0);

    QJSEngine* const engine = qjsEngine(this);
    assert(engine);

    QJSValue data;
#if QT_VERSION < QT_VERSION_CHECK(6, 5, 0)
    QString string;
    for (int i = 0; i < array.property(QStringLiteral("length")).toInt(); ++i)
    {
        QString decodedUrl;
        const QJSValue element = array.property(i);
        if (element.isUrl())
            // QJSValue does not have `toUrl()`
            decodedUrl = QJSManagedValue(element, engine).toUrl().toString(QUrl::FullyEncoded);
        else if (element.isString())
            // If the element is string, we assume it is already encoded
            decodedUrl = element.toString();
        else if (element.isVariant())
        {
            const QVariant variant = element.toVariant();
            if (variant.typeId() == QMetaType::QUrl)
                decodedUrl = variant.toUrl().toString(QUrl::FullyEncoded);
            else if (variant.typeId() == QMetaType::QString)
                decodedUrl = variant.toString();
            else
                Q_UNREACHABLE();
        }
        else
            Q_UNREACHABLE(); // Assertion failure in debug builds
        string += decodedUrl + QStringLiteral("\r\n");
    }
    string.chop(2);
    data = engine->toScriptValue(string);
#else
    data = array;
#endif
    QJSValue ret = engine->newObject();
    ret.setProperty(QStringLiteral("text/uri-list"), data);
    return ret;
}

VideoSurfaceProvider* MainCtx::getVideoSurfaceProvider() const
{
    return m_videoSurfaceProvider;
}

/************************************************************************
 * Events stuff
 ************************************************************************/

void MainCtx::onWindowClose( QWindow* )
{
    PlaylistController* playlistController = p_intf->p_mainPlaylistController;
    PlayerController* playerController = p_intf->p_mainPlayerController;

    if (m_videoSurfaceProvider)
        m_videoSurfaceProvider->onWindowClosed();
    //We need to make sure that noting is playing anymore otherwise the vout will be closed
    //after the main interface, and it requires (at least with OpenGL) that the OpenGL context
    //from the main window is still valid.
    //vlc_window_ReportClose is currently stubbed
    if (playerController && playerController->hasVideoOutput()) {
        connect(playerController, &PlayerController::playingStateChanged, [this](PlayerController::PlayingState state){
            if (state == PlayerController::PLAYING_STATE_STOPPED) {
                emit askToQuit();
            }
        });
        playlistController->stop();
    }
    else
    {
        emit askToQuit(); /* ask THEDP to quit, so we have a unique method */
    }
}

void MainCtx::toggleToolbarMenu()
{
    setHasToolbarMenu(!m_hasToolbarMenu);
}

void MainCtx::toggleInterfaceFullScreen()
{
    emit setInterfaceFullScreen( m_windowVisibility != QWindow::FullScreen );
}

void MainCtx::emitBoss()
{
    emit askBoss();
}

void MainCtx::emitShow()
{
    emit askShow();
}

void MainCtx::emitRaise()
{
    emit askRaise();
}

VLCVarChoiceModel* MainCtx::getExtraInterfaces()
{
    return m_extraInterfaces;
}

bool MainCtx::pasteFromClipboard()
{
    assert(qApp);
    const QClipboard *const clipboard = qApp->clipboard();
    if (Q_UNLIKELY(!clipboard))
        return false;
    const QMimeData *mimeData = clipboard->mimeData(QClipboard::Selection);
    if (!mimeData || !mimeData->hasUrls())
        mimeData = clipboard->mimeData(QClipboard::Clipboard);

    if (Q_UNLIKELY(!mimeData))
        return false;

    QList<QUrl> urlList = mimeData->urls();
    QString text = mimeData->text();

    if (urlList.count() > 1 || text.contains('\n'))
    {
        // NOTE: The reason that mime data for `text/uri-list` is not used
        //       directly as the placeholder of the input dialog instead of
        //       re-constructing is to decode the urls in the list.
        QString placeholder;

        if (urlList.isEmpty())
        {
            placeholder = std::move(text);
        }
        else
        {
            for (const auto& i : urlList)
                placeholder += i.toString(QUrl::PrettyDecoded) + '\n';
            placeholder.chop(1);
        }

        bool ok = false;
        const QString ret = QInputDialog::getMultiLineText(nullptr,
                                                           qtr("Paste from clipboard"),
                                                           qtr("Do you want to enqueue the following URLs into the play queue?"),
                                                           placeholder,
                                                           &ok);
        if (!ok)
            return false;

        for (const auto& i : QStringView(ret).split('\n'))
        {
            if (i.length() > 0)
                THEMPL->append(i.trimmed().toString(), false);
        }

        return true;
    }
    else if ((urlList.count() == 1) || mimeData->hasText())
    {
        THEDP->openUrlDialog();
        return true;
    }

    return false;
}

/*****************************************************************************
 * PopupMenuCB: callback triggered by the intf-popupmenu playlist variable.
 *  We don't show the menu directly here because we don't want the
 *  caller to block for a too long time.
 *****************************************************************************/
static int PopupMenuCB( vlc_object_t *, const char *,
                        vlc_value_t, vlc_value_t new_val, void *param )
{
    qt_intf_t *p_intf = (qt_intf_t *)param;

    if( p_intf->pf_show_dialog )
    {
        p_intf->pf_show_dialog( p_intf->intf, INTF_DIALOG_POPUPMENU,
                                new_val.b_bool, NULL );
    }

    return VLC_SUCCESS;
}

/*****************************************************************************
 * IntfShowCB: callback triggered by the intf-toggle-fscontrol libvlc variable.
 *****************************************************************************/
static int IntfShowCB( vlc_object_t *, const char *,
                       vlc_value_t, vlc_value_t, void *param )
{
    qt_intf_t *p_intf = (qt_intf_t *)param;
    p_intf->p_mi->emitShow();

    return VLC_SUCCESS;
}

/*****************************************************************************
 * IntfRaiseMainCB: callback triggered by the intf-show-main libvlc variable.
 *****************************************************************************/
static int IntfRaiseMainCB( vlc_object_t *, const char *,
                            vlc_value_t, vlc_value_t, void *param )
{
    qt_intf_t *p_intf = (qt_intf_t *)param;
    p_intf->p_mi->emitRaise();

    return VLC_SUCCESS;
}

/*****************************************************************************
 * IntfBossCB: callback triggered by the intf-boss libvlc variable.
 *****************************************************************************/
static int IntfBossCB( vlc_object_t *, const char *,
                       vlc_value_t, vlc_value_t, void *param )
{
    qt_intf_t *p_intf = (qt_intf_t *)param;
    p_intf->p_mi->emitBoss();

    return VLC_SUCCESS;
}

bool MainCtx::acrylicActive() const
{
    return m_acrylicActive;
}

void MainCtx::setAcrylicActive(bool newAcrylicActive)
{
    if (m_acrylicActive == newAcrylicActive)
        return;

    m_acrylicActive = newAcrylicActive;
    emit acrylicActiveChanged();
}

bool MainCtx::preferHotkeys() const
{
    return m_preferHotkeys;
}

void MainCtx::setPreferHotkeys(bool enable)
{
    if (m_preferHotkeys == enable)
        return;

    m_preferHotkeys = enable;

    emit preferHotkeysChanged();
}

QWindow *MainCtx::intfMainWindow() const
{
    if (p_intf->p_compositor)
        return p_intf->p_compositor->interfaceMainWindow();
    else
        return nullptr;
}

QVariant MainCtx::settingValue(const QString &key, const QVariant &defaultValue) const
{
    return settings->value(key, defaultValue);
}

bool MainCtx::hasSetting(const QString &key) const
{
    return settings->contains(key);
}

void MainCtx::setSettingValue(const QString &key, const QVariant &value)
{
    settings->setValue(key, value);
}

void MainCtx::setAttachedToolTip(QObject *toolTip)
{
    // See QQuickToolTipAttachedPrivate::instance(bool create)
    assert(toolTip);

    // Prevent possible invalid down-casting:
    assert(toolTip->inherits("QQuickToolTip"));

    QQmlEngine* const engine = qmlEngine(toolTip);
    assert(engine);
    assert(engine->objectOwnership(toolTip) == QQmlEngine::ObjectOwnership::JavaScriptOwnership);

    // Dynamic internal property:
#if QT_VERSION < QT_VERSION_CHECK(6, 12, 0)
    static const char* const name = "_q_QQuickToolTip";
#else
    static const char* const name = "_q_shared_QQuickToolTip";
#endif

    if (const auto obj = engine->property(name).value<QObject *>())
    {
        if (engine->objectOwnership(obj) == QQmlEngine::ObjectOwnership::CppOwnership)
            obj->deleteLater();
    }

    // setProperty() will return false, so there is no
    // need to check the return value:
    engine->setProperty(name, QVariant::fromValue(toolTip));

    // Check if the attached tooltip is actually the
    // one that is set
#ifndef NDEBUG
    QMetaObject::invokeMethod(toolTip, [toolTip]() {
        const auto engine = qmlEngine(toolTip);
        if (Q_UNLIKELY(!engine)) // Very unlikely, if not impossible
            return;
        QQmlComponent component(engine);
        component.setData(QByteArrayLiteral("import QtQuick; import QtQuick.Templates as T; Item { }"), {});
        QObject* const obj = component.create();
        assert(obj);
        // Consider disabling setting of custom attached
        // tooltip if the following assertion fails:
        if (QQmlProperty::read(obj, QStringLiteral("T.ToolTip.toolTip"), qmlContext(obj)).value<QObject*>() != toolTip)
            qmlWarning(obj) << "Could not set self as custom ToolTip!";
        obj->deleteLater();
    }, Qt::QueuedConnection);
#endif
}

MainCtx::MainInterfaceMode MainCtx::getEffectiveMainInterfaceMode() const {
    //priority applies across modes
    if (m_mainInterfaceModes & MainCtx::MAININTERFACE_MODE_MINIMAL)
        return MAININTERFACE_MODE_MINIMAL;
    else if (m_mainInterfaceModes & MAININTERFACE_MODE_PLAYER)
        return MAININTERFACE_MODE_PLAYER;
    else if (m_mainInterfaceModes & MAININTERFACE_MODE_MAINDISPLAY)
        return MAININTERFACE_MODE_MAINDISPLAY;
    else
        return MAININTERFACE_MODE_INVALID;
}

double MainCtx::dp(const double px, const double scale)
{
    return std::round(px * scale);
}

double MainCtx::dp(const double px) const
{
    return dp(px, m_intfScaleFactor);
}

bool MainCtx::useXmasCone() const
{
    return (QDate::currentDate().dayOfYear() >= QT_XMAS_JOKE_DAY)
            && var_InheritBool( p_intf, "qt-icon-change" );
}

bool WindowStateHolder::holdFullscreen(QWindow *window, Source source, bool hold)
{
    QVariant prop = window->property("__windowFullScreen");
    bool ok = false;
    unsigned fullscreenCounter = prop.toUInt(&ok);
    if (!ok)
        fullscreenCounter = 0;

    if (hold)
        fullscreenCounter |= source;
    else
        fullscreenCounter &= ~source;

    Qt::WindowStates oldflags = window->windowStates();
    Qt::WindowStates newflags;

    if( fullscreenCounter != 0 )
        newflags = oldflags | Qt::WindowFullScreen;
    else
        newflags = oldflags & ~Qt::WindowFullScreen;

    window->setProperty("__windowFullScreen", QVariant::fromValue(fullscreenCounter));

    if( newflags != oldflags )
    {
        window->setWindowStates( newflags );
    }

    return fullscreenCounter != 0;
}

bool WindowStateHolder::holdOnTop(QWindow *window, Source source, bool hold)
{
    QVariant prop = window->property("__windowOnTop");
    bool ok = false;
    unsigned onTopCounter = prop.toUInt(&ok);
    if (!ok)
        onTopCounter = 0;

    if (hold)
        onTopCounter |= source;
    else
        onTopCounter &= ~source;

#ifdef _WIN32
    if (!window->handle()) // do not call hold on top if there is no platform window
        return false;
#endif

    if( onTopCounter != 0 )
    {
#ifdef _WIN32
        // Qt::WindowStaysOnTopHint is broken on Windows: QTBUG-133034, QTBUG-132522.
        // Reported to be fixed by Qt 6.9, but needs additional checking if the solution does not interfere with `CSDWin32EventHandler`.
        SetWindowPos(reinterpret_cast<HWND>(window->winId()), HWND_TOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE);
#else
        window->setFlag(Qt::WindowStaysOnTopHint, true);
#endif
    }
    else
    {
#ifdef _WIN32
        // Qt::WindowStaysOnTopHint is broken on Windows: QTBUG-133034, QTBUG-132522.
        // Reported to be fixed by Qt 6.9, but needs additional checking if the solution does not interfere with `CSDWin32EventHandler`.
        SetWindowPos(reinterpret_cast<HWND>(window->winId()), HWND_NOTOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE);
#else
        window->setFlag(Qt::WindowStaysOnTopHint, false);
#endif
    }

    window->setProperty("__windowOnTop", QVariant::fromValue(onTopCounter));

    return onTopCounter != 0;
}

double MainCtx::artistAlbumsWidth() const
{
    return dp(m_artistAlbumsWidth);
}

void MainCtx::setArtistAlbumsWidth(double newArtistAlbumsWidth)
{
    double unscaledValue = newArtistAlbumsWidth / getIntfScaleFactor();
    if (qFuzzyCompare(m_artistAlbumsWidth, unscaledValue))
        return;

    m_artistAlbumsWidth = unscaledValue;
    emit artistAlbumsWidthChanged( dp(m_artistAlbumsWidth) );
}

#ifdef UPDATE_CHECK
UpdateModel* MainCtx::getUpdateModel() const
{
    if (!m_updateModel)
    {
        m_updateModel = std::make_unique<UpdateModel>(p_intf);

        connect(m_updateModel.get(), &UpdateModel::updateStatusChanged, this, [this](){
            // No-op, modern update pane opens itself automatically when status changes.
            // However, the old update dialog is used as fallback in case for any reason
            // the modern pane is not available.

            const auto openLegacyDialogIfNecessary = [&]() {
                // Fallback:

                if (Q_LIKELY(p_intf &&
                             p_intf->p_compositor &&
                             p_intf->p_compositor->quickWindow() &&
                             p_intf->p_compositor->quickWindow()->contentItem()))
                {
                    const auto target = p_intf->p_compositor->quickWindow()->contentItem();
                    QMetaObject::invokeMethod(target, [target]() {
                        const auto updatePaneLoader = target->findChild<QQuickItem*>(QStringLiteral("updatePaneLoader"));
                        if (!updatePaneLoader || (updatePaneLoader->property("status").toInt() != 1 /* Loader.Ready */))
                        {
                            qDebug("No acknowledgement from the modern update loader, falling back to the old update dialog.");
                            THEDP->updateDialog(DialogsProvider::Show);
                        }
                    }, Qt::QueuedConnection);
                }
                else
                {
                    qDebug("Compositor is not available, falling back to the old update dialog.");
                    THEDP->updateDialog();
                }
            };

            if (m_updateModel->explicitCheck())
            {
                if (m_updateModel->updateStatus() != UpdateModel::Unchecked)
                    openLegacyDialogIfNecessary();
            }
            else
            {
                switch (m_updateModel->updateStatus())
                {
                case UpdateModel::UpToDate:
                case UpdateModel::Unchecked:
                case UpdateModel::Checking:
                    break;
                case UpdateModel::NeedUpdate:
                    qWarning() << "Need update";
                    [[fallthrough]];
                default:
                    openLegacyDialogIfNecessary();
                }
            }
        });
    }

    return m_updateModel.get();
}
#endif
