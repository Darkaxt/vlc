// SPDX-License-Identifier: GPL-2.0-or-later
import QtQuick
import QtQuick.Window
import QtQuick.Layouts
import QtQuick.Templates as T
import VLC.MainInterface
import VLC.Player
import VLC.Playlist
import VLC.Dialogs
import VLC.Util

FocusScope {
    id: root
    Accessible.name: qsTr("Library display")
    AccessibleCompat.id: "libraryDisplay"
    readonly property bool queueVisible: MainCtx.playqueuePanel.visible
    readonly property int positionSliderY: mini.y + miniSeek.y
    readonly property bool hasMiniPlayer: Player.isStarted
    property var pagePrefix: []
    function loadView(path, properties, reason) {
        if (!path || !path.length) return false
        library.navigate(path[0] === "video" ? "videos" : path[0] === "music" ? "music" : path[0] === "network" ? "network" : "home")
        return true
    }
    Rectangle { anchors.fill: parent; color: PlayerStyle.panel }
    RedesignTopBar {
        id: titleBar
        anchors.top: parent.top; anchors.left: parent.left; anchors.right: parent.right
        title: Player.isStarted ? Player.name : qsTr("VLC Media Player")
        showCSD: MainCtx.clientSideDecoration && MainCtx.intfMainWindow.visibility !== Window.FullScreen
        onBackRequested: { if (Player.isStarted) MainCtx.playerView = true }
        onBrowseRequested: library.navigate("home")
        onQueueRequested: MainCtx.playqueuePanel.visible = !MainCtx.playqueuePanel.visible
        libraryContext: true
    }
    PlayerLibrary {
        id: library
        compact: width < PlayerStyle.px(900)
        anchors { top: titleBar.bottom; left: parent.left; right: queueLoader.active ? queueLoader.left : parent.right; bottom: parent.bottom }
        focus: true
        onCloseRequested: { if (Player.isStarted) MainCtx.playerView = true }
    }
    Loader {
        id: queueLoader
        active: root.queueVisible && MainCtx.playqueuePanel.docked
        anchors.top: titleBar.bottom; anchors.right: parent.right; anchors.bottom: parent.bottom
        width: active ? Math.min(PlayerStyle.px(400),root.width/2) : 0
        sourceComponent: PlaylistPane { redesigned: true; useAcrylic: false; padding: 0; wheelEnabled: true }
    }
    Loader {
        active: !MainCtx.playqueuePanel.docked
        sourceComponent: PlaylistDetachedWindow {}
    }
    Rectangle {
        id: mini
        visible: Player.isStarted
        x: PlayerStyle.px(8); y: root.height-height-PlayerStyle.px(8)
        width: Math.max(0,Math.min(PlayerStyle.px(390),root.width-PlayerStyle.px(16),(root.height-titleBar.height-PlayerStyle.px(136))*16/9))
        height: width*9/16 + PlayerStyle.px(120)
        function constrain() {
            x = Math.max(PlayerStyle.px(8),Math.min(x,root.width-width-PlayerStyle.px(8)))
            y = Math.max(titleBar.height+PlayerStyle.px(8),Math.min(y,root.height-height-PlayerStyle.px(8)))
        }
        Connections {
            target: root
            function onWidthChanged() { mini.constrain() }
            function onHeightChanged() { mini.constrain() }
        }
        radius: PlayerStyle.px(16); color: PlayerStyle.chrome
        z: 3
        PIPPlayer {
            visible: MainCtx.hasEmbededVideo && MainCtx.canShowVideoPIP
            x: PlayerStyle.px(8); y: PlayerStyle.px(8)
            width: mini.width - PlayerStyle.px(16); height: width*9/16
            dragTarget: mini
            dragXMin: PlayerStyle.px(8); dragXMax: root.width-mini.width-PlayerStyle.px(8)
            dragYMin: titleBar.height+PlayerStyle.px(8); dragYMax: root.height-mini.height-PlayerStyle.px(8)
        }
        Image {
            visible: !MainCtx.hasEmbededVideo
            x: PlayerStyle.px(8); y: PlayerStyle.px(8)
            width: mini.width - PlayerStyle.px(16); height: width*9/16
            source: Player.artwork; fillMode: Image.PreserveAspectFit
        }
        T.Slider {
            id: miniSeek
            x: PlayerStyle.px(8); y: (mini.width-PlayerStyle.px(16))*9/16+PlayerStyle.px(16)
            width: parent.width-PlayerStyle.px(16); height: PlayerStyle.px(16)
            from: 0; to: 1; enabled: Player.seekable; activeFocusOnTab: true
            Accessible.name: qsTr("Mini player position"); AccessibleCompat.id: "libraryMiniSeek"
            Binding on value { when: !miniSeek.pressed; value: Player.position; restoreMode: Binding.RestoreNone }
            onMoved: Player.position = value
            background: Rectangle {
                anchors.fill: parent; radius: PlayerStyle.px(4); color: PlayerStyle.timeline
                Rectangle { width: parent.width*miniSeek.visualPosition; height: parent.height; radius: parent.radius; color: PlayerStyle.accent; opacity: 0.35 }
                border.color: PlayerStyle.accent; border.width: miniSeek.visualFocus ? PlayerStyle.px(1) : 0
            }
            handle: Item {}
        }
        Text {
            x: PlayerStyle.px(16); y: miniSeek.y+miniSeek.height+PlayerStyle.px(20)
            width: parent.width-PlayerStyle.px(32)
            text: Player.name; textFormat: Text.PlainText; elide: Text.ElideRight
            color: PlayerStyle.foreground; font.family: PlayerStyle.fontFamily; font.pixelSize: PlayerStyle.px(14)
        }
        RowLayout {
            anchors.bottom: parent.bottom; anchors.left: parent.left; anchors.right: parent.right
            anchors.margins: PlayerStyle.px(12)
            spacing: PlayerStyle.px(12)
            PlayerIconButton { glyph: Player.playingState === Player.PLAYING_STATE_PLAYING ? "pause" : "play"; description: qsTr("Mini player play or pause"); onClicked: MainPlaylistController.togglePlayPause() }
            PlayerIconButton { glyph: "folder"; description: qsTr("Browse videos"); onClicked: library.navigate("videos") }
            Item { Layout.fillWidth: true }
            PlayerIconButton { glyph: "queue"; description: qsTr("Show playback queue"); onClicked: MainCtx.playqueuePanel.visible = !MainCtx.playqueuePanel.visible }
            PlayerIconButton { glyph: "expand-library"; description: qsTr("Return to player"); AccessibleCompat.id: "libraryReturnToPlayer"; onClicked: MainCtx.playerView = true }
        }
    }
    Dialogs { z: 10; bgContent: root }
    Keys.onPressed: event => { if (!event.accepted) MainCtx.sendHotkey(event.key,event.modifiers) }
}
