// SPDX-License-Identifier: GPL-2.0-or-later
import QtQuick
import QtQuick.Templates as T
import QtQuick.Layouts
import VLC.MainInterface
import VLC.Player
import VLC.Playlist
import VLC.Menus as Menus
import VLC.Util

T.Pane {
    id:bar
    property Item popupParent:parent
    property Item lastInvoker:null
    property bool queueVisible:false
    readonly property var checkedControls:({audio:audio.visible,subtitles:subtitles.visible,tools:settings.visible,queue:queueVisible,more:playbackMenu.shown})
    readonly property bool compact:width<PlayerStyle.px(760)
    readonly property bool menuOpen:subtitles.visible||audio.visible||settings.visible||subtitleMatching.visible||playbackMenu.shown||PlayerCustomization.editing
    readonly property real sliderY:(height-PlayerStyle.px(28))/2
    signal toggleQueue()
    signal hideChromeRequested()
    signal externalActionRequested(string key,var invoker)
    signal forceUnlock()
    onForceUnlock:{subtitles.close();audio.close();settings.close();subtitleMatching.close();playbackMenu.close()}
    implicitHeight:PlayerStyle.px(54);padding:0;hoverEnabled:true;enabled:visible
    Accessible.name:qsTr("Player controls");AccessibleCompat.id:"playerControlBar"
    background:Rectangle{objectName:"playerVideoBackdrop";readonly property real backgroundBlurRadius:PlayerStyle.px(50);color:PlayerStyle.chrome}
    function restoreFocus(){if(lastInvoker)lastInvoker.forceActiveFocus(Qt.PopupFocusReason)}
    function activate(key,invoker){
        lastInvoker=invoker
        switch(key){
        case "audio":subtitles.close();audio.open();break
        case "subtitles":audio.close();subtitles.open();break
        case "tools":audio.close();subtitles.close();settings.showPage(0);break
        case "speed":settings.showPage(0);break
        case "zoom":settings.showPage(1);break
        case "more":playbackMenu.popup(invoker.mapToGlobal(0,invoker.height));break
        case "queue":bar.toggleQueue();break
        case "showQueue":if(!queueVisible)bar.toggleQueue();break
        default:externalActionRequested(key,invoker)
        }
    }
    T.Pane {
        parent:bar.popupParent;x:PlayerStyle.px(20);y:PlayerStyle.px(60)
        width:Math.min(PlayerStyle.px(400),parent.width-PlayerStyle.px(40));padding:PlayerStyle.px(16)
        visible:MediaTools.statisticsVisible;z:1
        background:Rectangle{color:PlayerStyle.panel;radius:PlayerStyle.px(8);opacity:0.9}
        contentItem:Text{text:MediaTools.statisticsText;textFormat:Text.PlainText;color:PlayerStyle.trackForeground;font.family:PlayerStyle.fontFamily;font.pixelSize:PlayerStyle.px(14);wrapMode:Text.Wrap}
        Accessible.name:qsTr("Playback statistics")
    }
    RowLayout {
        anchors.fill:parent;anchors.leftMargin:PlayerStyle.px(bar.compact?12:20);anchors.rightMargin:anchors.leftMargin
        spacing:PlayerStyle.px(bar.compact?12:20)
        PlayerLayoutStrip{zone:"bottomLeft";compact:bar.compact;popupParent:bar.popupParent;checkedControls:bar.checkedControls;Layout.preferredWidth:Math.min(implicitWidth,bar.width*0.3);Layout.fillHeight:true;onActionRequested:(key,invoker)=>bar.activate(key,invoker)}
        PlayerLayoutStrip{zone:"bottomCenter";compact:bar.compact;popupParent:bar.popupParent;checkedControls:bar.checkedControls;Layout.fillWidth:true;Layout.minimumWidth:PlayerStyle.px(24);Layout.fillHeight:true;onActionRequested:(key,invoker)=>bar.activate(key,invoker)}
        PlayerLayoutStrip{zone:"bottomRight";compact:bar.compact;popupParent:bar.popupParent;checkedControls:bar.checkedControls;Layout.preferredWidth:Math.min(implicitWidth,bar.width*0.5);Layout.fillHeight:true;onActionRequested:(key,invoker)=>bar.activate(key,invoker)}
    }
    PlayerTracksPopup{id:subtitles;parent:bar.popupParent;subtitles:true;onSettingsRequested:page=>settings.showPage(page);x:parent.width-width-PlayerStyle.px(20);y:bar.y-height-PlayerStyle.px(20);onClosed:bar.restoreFocus()}
    PlayerTracksPopup{id:audio;parent:bar.popupParent;subtitles:false;onSettingsRequested:page=>settings.showPage(page);x:parent.width-width-PlayerStyle.px(20);y:bar.y-height-PlayerStyle.px(20);onClosed:bar.restoreFocus()}
    PlayerSettingsPopup{id:settings;parent:bar.popupParent;x:Math.max(PlayerStyle.px(20),parent.width-width-PlayerStyle.px(20));y:bar.y-height-PlayerStyle.px(20)
        onMatchSubtitlesRequested:{subtitleMatching.online=false;subtitleMatching.open()}
        onRemoteSubtitlesRequested:{subtitleMatching.online=true;subtitleMatching.open()}
        onClosed:bar.restoreFocus()}
    PlayerSubtitleDialog{id:subtitleMatching;parent:bar.popupParent;x:(parent.width-width)/2;y:(parent.height-height)/2}
    Menus.QmlGlobalMenu{id:playbackMenu;ctx:MainCtx;playerChromeCommand:true;onHidePlayerChromeRequested:bar.hideChromeRequested()}
}
