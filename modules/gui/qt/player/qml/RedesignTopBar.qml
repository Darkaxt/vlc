// SPDX-License-Identifier: GPL-2.0-or-later
import QtQuick
import QtQuick.Layouts
import QtQuick.Window
import QtQuick.Templates as T
import QtQuick.Controls.impl
import QtQml.Models
import VLC.MainInterface
import VLC.Player
import VLC.Dialogs
import VLC.MediaLibrary
import VLC.Widgets as Widgets
import VLC.Util

T.Pane {
    id:header
    property string title
    property bool showCSD:false
    property bool libraryContext:false
    property var checkedControls:({})
    readonly property var activeControls:Object.assign({},checkedControls,{more:mainMenu.shown||!!checkedControls.more})
    readonly property bool menuOpen:mainMenu.shown||PlayerCustomization.editing
    signal backRequested()
    signal browseRequested()
    signal browseFolderRequested()
    signal queueRequested()
    signal hideChromeRequested()
    signal actionRequested(string key,var invoker)
    signal forceUnlock()
    onForceUnlock:mainMenu.close()
    padding:0;implicitHeight:PlayerStyle.px(40);hoverEnabled:true;enabled:visible
    Accessible.name:qsTr("Player title bar");AccessibleCompat.id:"playerTopBar"
    background:Rectangle{objectName:"playerVideoBackdrop";readonly property real backgroundBlurRadius:PlayerStyle.px(50);color:PlayerStyle.chrome}
    Loader{anchors.fill:parent;active:header.showCSD&&!PlayerCustomization.editing;source:"qrc:///qt/qml/VLC/Widgets/CSDTitlebarTapNDrapHandler.qml"}
    RowLayout {
        id:left;x:PlayerStyle.px(6);height:parent.height;spacing:PlayerStyle.px(7)
        PlayerIconButton{glyph:"vlc";description:qsTr("Back to media");foreground:PlayerStyle.accent;implicitWidth:PlayerStyle.px(38);implicitHeight:PlayerStyle.px(28);onClicked:header.backRequested()}
        PlayerIconButton{visible:header.libraryContext;glyph:"more";description:qsTr("Main menu");onClicked:header.showMainMenu(this)}
        PlayerIconButton{visible:header.libraryContext;glyph:"queue";description:qsTr("Show playback queue");AccessibleCompat.id:"libraryQueueButton";onClicked:header.queueRequested()}
        PlayerLayoutStrip {
            visible:!header.libraryContext;zone:"topLeft";popupParent:header.parent;compact:header.width<PlayerStyle.px(760)
            checkedControls:header.activeControls
            Layout.preferredWidth:Math.min(implicitWidth,header.width*0.4);Layout.preferredHeight:PlayerStyle.px(32)
            onActionRequested:(key,invoker)=>{if(key==="more")header.showMainMenu(invoker);else header.actionRequested(key,invoker)}
        }
    }
    PlayerLayoutStrip {
        visible:!header.libraryContext;zone:"topCenter";popupParent:header.parent;compact:header.width<PlayerStyle.px(760)
        checkedControls:header.activeControls
        anchors.centerIn:parent;width:Math.max(0,parent.width-2*Math.max(left.width+left.x,right.width+PlayerStyle.px(6)));height:PlayerStyle.px(32)
        onActionRequested:(key,invoker)=>header.actionRequested(key,invoker)
    }
    Text {
        visible:header.libraryContext;anchors.centerIn:parent;width:Math.max(0,parent.width-2*Math.max(left.width+left.x,right.width+PlayerStyle.px(6)))
        text:header.title;textFormat:Text.PlainText;horizontalAlignment:Text.AlignHCenter;elide:Text.ElideRight;color:PlayerStyle.foreground;font.family:PlayerStyle.fontFamily;font.pixelSize:PlayerStyle.px(14);Accessible.name:text
    }
    RowLayout {
        id:right;anchors.right:parent.right;anchors.rightMargin:PlayerStyle.px(6);height:parent.height;spacing:0
        PlayerIconButton{visible:header.showCSD;implicitWidth:PlayerStyle.px(36);implicitHeight:PlayerStyle.px(24);glyph:"minimize";description:qsTr("Minimize");onClicked:MainCtx.requestInterfaceMinimized()}
        PlayerIconButton{visible:header.showCSD;implicitWidth:PlayerStyle.px(36);implicitHeight:PlayerStyle.px(24);glyph:"maximize";description:MainCtx.intfMainWindow.visibility===Window.Maximized?qsTr("Restore window"):qsTr("Maximize");onClicked:{if(MainCtx.intfMainWindow.visibility===Window.Maximized)MainCtx.requestInterfaceNormal();else MainCtx.requestInterfaceMaximized()}}
        PlayerLayoutStrip{visible:!header.libraryContext;zone:"topRight";popupParent:header.parent;compact:header.width<PlayerStyle.px(760);checkedControls:header.activeControls;Layout.preferredWidth:Math.min(implicitWidth,header.width*0.3);Layout.preferredHeight:PlayerStyle.px(32);onActionRequested:(key,invoker)=>header.actionRequested(key,invoker)}
        PlayerIconButton{visible:header.libraryContext;implicitWidth:PlayerStyle.px(36);implicitHeight:PlayerStyle.px(24);glyph:"fullscreen";description:Player.fullscreen?qsTr("Leave fullscreen"):qsTr("Fullscreen");onClicked:Player.toggleFullscreen()}
        PlayerIconButton{visible:header.showCSD;implicitWidth:PlayerStyle.px(36);implicitHeight:PlayerStyle.px(24);glyph:"close";description:qsTr("Close");onClicked:MainCtx.intfMainWindow.close()}
    }
    function showMainMenu(invoker) {
        const point=invoker.mapToItem(mainMenu.parent,0,invoker.height)
        mainMenu.x=Math.max(PlayerStyle.px(8),Math.min(point.x+invoker.width/2-PlayerStyle.px(32),mainMenu.parent.width-mainMenu.width-PlayerStyle.px(8)))
        mainMenu.y=header.mapToItem(mainMenu.parent,0,header.height).y+PlayerStyle.px(4)
        mainMenu.open()
    }
    Loader {
        id: recentSource
        visible: false
        active: MainCtx.historyEnabled && MainCtx.mediaLibraryAvailable
        // Media-library types are registered only when that backend exists.
        // Resolve this component only while the guarded Loader is active.
        source: "PlayerRecentMenuModel.qml"
    }
    component MenuRow: T.MenuItem {
        id: row
        property string glyph: ""
        property string shortcutText: ""
        implicitWidth: PlayerStyle.px(367)
        implicitHeight: PlayerStyle.px(48)
        leftPadding: PlayerStyle.px(14)
        rightPadding: PlayerStyle.px(row.subMenu ? 44 : 18)
        spacing: PlayerStyle.px(10)
        hoverEnabled: true
        activeFocusOnTab: true
        Accessible.name: text
        Accessible.onPressAction: triggered()
        contentItem: RowLayout {
            spacing: PlayerStyle.px(10)
            Image {
                visible: row.glyph.length>0
                smooth: false
                source: row.glyph.length ? "qrc:/redesign/icons/menu-"+row.glyph+".svg" : ""
                sourceSize: Qt.size(PlayerStyle.px(24),PlayerStyle.px(24))
                Layout.preferredWidth: PlayerStyle.px(24)
                Layout.preferredHeight: PlayerStyle.px(24)
            }
            Text {
                text: row.text
                Layout.fillWidth: true
                color: PlayerStyle.foreground
                opacity: row.enabled ? 1 : 0.5
                font.family: PlayerStyle.fontFamily
                font.pixelSize: PlayerStyle.px(14)
                elide: Text.ElideRight
                textFormat: Text.PlainText
            }
            Text {
                text: row.shortcutText
                color: PlayerStyle.sectionForeground
                font.family: PlayerStyle.fontFamily
                font.pixelSize: PlayerStyle.px(14)
                textFormat: Text.PlainText
                visible: !row.subMenu
            }
        }
        arrow: IconImage {
            visible: !!row.subMenu
            x: row.width-width-PlayerStyle.px(18)
            y: (row.height-height)/2
            width: PlayerStyle.px(16); height: width
            sourceSize: Qt.size(width,height)
            source: "qrc:/redesign/icons/chevron-down.svg"
            rotation: -90
            smooth: false
            color: PlayerStyle.foreground
        }
        background: Rectangle {
            radius: PlayerStyle.px(6)
            color: row.highlighted ? PlayerStyle.hover : "transparent"
            border.width: row.visualFocus ? PlayerStyle.px(1) : 0
            border.color: PlayerStyle.accent
        }
    }
    component PlayerMenu: T.Menu {
        id: menu
        width: Math.max(0,Math.min(PlayerStyle.px(375),header.parent.width-PlayerStyle.px(16)))
        implicitHeight: contentItem.implicitHeight + topPadding + bottomPadding
        height: Math.min(implicitHeight,Math.max(0,header.parent.height-PlayerStyle.px(16)))
        focus: true
        padding: PlayerStyle.px(4)
        margins: PlayerStyle.px(8)
        overlap: PlayerStyle.px(4)
        delegate: MenuRow {}
        background: Rectangle {
            radius: PlayerStyle.px(10)
            color: PlayerStyle.dark ? "#191919" : "#eeeeee"
            Widgets.RoundedRectangleShadow { color: Qt.rgba(0,0,0,0.4); yOffset: PlayerStyle.px(8); blurRadius: PlayerStyle.px(20); hollow: true }
        }
        contentItem: ListView {
            implicitHeight: contentHeight
            model: menu.contentModel
            currentIndex: menu.currentIndex
            spacing: 0
            clip: true
            interactive: contentHeight>height
            boundsBehavior: Flickable.StopAtBounds
            T.ScrollBar.vertical: T.ScrollBar {}
        }
    }
    PlayerMenu {
        id: mainMenu
        parent: header.parent
        objectName: "redesignMainMenu"
        readonly property bool shown: visible
        MenuRow { text: qsTr("Open File(s)"); glyph: "file"; shortcutText: "Ctrl + O"; onTriggered: DialogsProvider.simpleOpenDialog() }
        MenuRow { text: qsTr("Open Folder"); glyph: "folder"; shortcutText: "Ctrl + F"; onTriggered: DialogsProvider.PLOpenDir() }
        MenuRow { text: qsTr("Open Network Stream"); glyph: "network"; shortcutText: "Ctrl + N"; onTriggered: DialogsProvider.openNetDialog() }
        MenuRow { text: qsTr("Open Disc"); glyph: "disc"; shortcutText: "Ctrl + D"; onTriggered: DialogsProvider.openDiscDialog() }
        MenuRow { text: qsTr("Open Capture Device"); glyph: "capture"; shortcutText: "Ctrl + C"; onTriggered: DialogsProvider.openCaptureDialog() }
        MenuRow { text: qsTr("Convert"); glyph: "convert"; shortcutText: "Ctrl + R"; onTriggered: DialogsProvider.openAndTranscodingDialogs() }
        PlayerMenu {
            id: recentMenu
            title: qsTr("Open Recent")
            enabled: MainCtx.historyEnabled && MainCtx.mediaLibraryAvailable
            delegate: MenuRow { glyph: "recent" }
            Instantiator {
                model: recentSource.item
                delegate: MenuRow {
                    required property var model
                    text: model.title || model.name || qsTr("Untitled")
                    onTriggered: if(model.id)MediaLib.addAndPlay(model.id)
                }
                onObjectAdded: (index,object)=>recentMenu.insertItem(index,object)
                onObjectRemoved: (index,object)=>recentMenu.removeItem(object)
            }
            MenuRow { visible: !recentSource.item || recentSource.item.count===0; height: visible?implicitHeight:0; text: qsTr("No recent media"); enabled: false }
        }
        T.MenuSeparator {
            implicitHeight: PlayerStyle.px(1)
            contentItem: Rectangle { implicitHeight: PlayerStyle.px(1); color: PlayerStyle.foreground; opacity: 0.08 }
        }
        PlayerMenu {
            id: profilesMenu
            title: PlayerCustomization.selected ? qsTr("Profile (%1)").arg(PlayerCustomization.selected) : qsTr("Profile")
            Instantiator {
                model: PlayerCustomization.profiles
                delegate: MenuRow {
                    required property var modelData
                    text: (modelData.name===PlayerCustomization.selected ? "✓  " : "")+modelData.name
                    enabled: PlayerCustomization.writable && !PlayerCustomization.editing
                    onTriggered: PlayerCustomization.chooseProfile(modelData.name)
                }
                onObjectAdded: (index,object)=>profilesMenu.insertItem(index,object)
                onObjectRemoved: (index,object)=>profilesMenu.removeItem(object)
            }
            MenuRow { text: qsTr("New / Manage Profiles…"); onTriggered: PlayerCustomization.profilesVisible=true }
            MenuRow { text: qsTr("Save Current Profile"); enabled: PlayerCustomization.writable && PlayerCustomization.selected.length>0; onTriggered: PlayerCustomization.saveProfile() }
            MenuRow { text: qsTr("Restore Saved Profile"); enabled: PlayerCustomization.writable && !PlayerCustomization.editing && PlayerCustomization.selected.length>0; onTriggered: PlayerCustomization.chooseProfile(PlayerCustomization.selected) }
        }
        MenuRow { text: qsTr("Keyboard Shortcuts"); glyph: "shortcuts"; onTriggered: DialogsProvider.shortcutsDialog() }
        MenuRow { text: qsTr("Customize Player"); glyph: "customize"; onTriggered: { MainCtx.playerView=true;PlayerCustomization.begin() } }
        MenuRow { text: qsTr("Settings"); glyph: "settings"; shortcutText: "Ctrl + P"; AccessibleCompat.id: "mainMenuGlobalSettings"; onTriggered: DialogsProvider.prefsDialog() }
        MenuRow { text: qsTr("About VLC"); glyph: "info"; shortcutText: "Shift + F1"; onTriggered: DialogsProvider.aboutDialog() }
        onAboutToShow: {
            // Menu-generated parent rows keep the same original icon treatment.
            itemAt(6).glyph="recent"
            itemAt(8).glyph="profile"
        }
    }
}
