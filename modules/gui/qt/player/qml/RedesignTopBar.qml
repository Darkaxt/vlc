// SPDX-License-Identifier: GPL-2.0-or-later
import QtQuick
import QtQuick.Layouts
import QtQuick.Window
import QtQuick.Templates as T
import VLC.MainInterface
import VLC.Player
import VLC.Menus as Menus
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
        PlayerIconButton{visible:header.libraryContext;glyph:"more";description:qsTr("Main menu");onClicked:mainMenu.popup(mapToGlobal(0,height))}
        PlayerIconButton{visible:header.libraryContext;glyph:"queue";description:qsTr("Show playback queue");AccessibleCompat.id:"libraryQueueButton";onClicked:header.queueRequested()}
        PlayerLayoutStrip {
            visible:!header.libraryContext;zone:"topLeft";popupParent:header.parent;compact:header.width<PlayerStyle.px(760)
            checkedControls:header.activeControls
            Layout.preferredWidth:Math.min(implicitWidth,header.width*0.4);Layout.preferredHeight:PlayerStyle.px(32)
            onActionRequested:(key,invoker)=>{if(key==="more")mainMenu.popup(invoker.mapToGlobal(0,invoker.height));else header.actionRequested(key,invoker)}
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
    Menus.QmlGlobalMenu{id:mainMenu;ctx:MainCtx;playerChromeCommand:true;onHidePlayerChromeRequested:header.hideChromeRequested()}
}
