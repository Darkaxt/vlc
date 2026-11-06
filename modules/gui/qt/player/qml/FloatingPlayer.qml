// SPDX-License-Identifier: GPL-2.0-or-later
// Compact/expanded miniplayer from Juxtopposed's VLC Redesign, CC BY 4.0.
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
    objectName: "floatingPlayer"
    AccessibleCompat.id: "floatingPlayer"
    Accessible.name: qsTr("Miniplayer")
    focus: true
    width: 360
    property int availableHeight: 1024
    property bool queueExpanded: false
    property bool ready: false // set after the native video visual is attached
    readonly property bool moving: windowMove.active
    property string displayName: ""
    property string displayArtist: ""
    property url displayFolder: ""
    readonly property real margin: PlayerStyle.px(8)
    readonly property real videoHeight: (width - margin*2)*9/16
    readonly property real cardHeight: videoHeight + PlayerStyle.px(94)
    readonly property real queueHeight: queueExpanded ? Math.min(PlayerStyle.px(280), Math.max(0, availableHeight-cardHeight)) : 0
    implicitHeight: cardHeight + queueHeight
    function rememberMedia() {
        if (Player.name.length) displayName = Player.name
        if (Player.url.toString().length) displayFolder = MainCtx.folderMRL(Player.url)
        displayArtist = Player.artist
    }
    Component.onCompleted: rememberMedia()
    Connections {
        target: Player
        function onNameChanged() { root.rememberMedia() }
        function onCurrentMetaChanged() { if (Player.isStarted) root.rememberMedia() }
    }
    Connections {
        target: MainCtx
        function onFloatingPlayerChanged() { if (MainCtx.floatingPlayer) root.rememberMedia() }
    }
    PlaylistListModel { id: queueModel; playlist: MainPlaylistController.playlist }
    // One drag owner covers the card and expanded queue. Interactive children
    // retain their grabs (notably the seekbar); ordinary text/background can move.
    DragHandler {
        id: windowMove
        target: null
        onActiveChanged: if (active) root.Window.window.startSystemMove()
    }
    Rectangle {
        anchors.fill: parent
        radius: PlayerStyle.px(14)
        color: PlayerStyle.dark ? Qt.rgba(27/255,27/255,27/255,0.95) : Qt.rgba(231/255,231/255,231/255,0.95)
        antialiasing: true
    }
    Item {
        id: queue
        width: parent.width; height: root.queueHeight
        visible: root.queueExpanded; clip: true
        Item {
            id: queueHeader
            AccessibleCompat.id: "floatingQueueHeader"
            Accessible.name: qsTr("Move miniplayer")
            readonly property bool moving: root.moving
            width: parent.width; height: PlayerStyle.px(44)
            Rectangle { anchors.fill: parent; color: PlayerStyle.timeline; radius: PlayerStyle.px(14) }
            Text {
                anchors.fill: parent
                text: qsTr("Queue"); horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter
                font.family: PlayerStyle.fontFamily; font.pixelSize: PlayerStyle.px(14); color: PlayerStyle.foreground
            }
            HoverHandler { cursorShape: root.moving ? Qt.ClosedHandCursor : Qt.OpenHandCursor }
        }
        RowLayout {
            x: PlayerStyle.px(16); y: PlayerStyle.px(48); width: parent.width-x*2; height: PlayerStyle.px(32)
            Text {
                Layout.fillWidth: true; elide: Text.ElideRight
                text: qsTr("%1 items · %2").arg(queueModel.count).arg(queueModel.duration.formatHMS(0))
                font.family: PlayerStyle.fontFamily; font.pixelSize: PlayerStyle.px(12); color: PlayerStyle.sectionForeground
            }
            PlayerIconButton {
                glyph: "sort"; description: qsTr("Sort queue by title")
                glyphSize: PlayerStyle.px(16); foreground: PlayerStyle.sectionForeground
                AccessibleCompat.id: "floatingQueueSort"
                onClicked: MainPlaylistController.sort(PlaylistController.SORT_KEY_TITLE,
                    MainPlaylistController.sortOrder===PlaylistController.SORT_ORDER_ASC ? PlaylistController.SORT_ORDER_DESC : PlaylistController.SORT_ORDER_ASC)
            }
            PlayerIconButton {
                glyph: "remove"; description: qsTr("Remove selected queue item")
                glyphSize: PlayerStyle.px(16); foreground: PlayerStyle.sectionForeground
                enabled: queueList.currentIndex >= 0
                AccessibleCompat.id: "floatingQueueRemove"
                onClicked: queueModel.removeItems([queueList.currentIndex])
            }
            PlayerIconButton {
                glyph: "add"; description: qsTr("Add media to queue")
                glyphSize: PlayerStyle.px(16); foreground: PlayerStyle.sectionForeground
                AccessibleCompat.id: "floatingQueueAdd"
                onClicked: DialogsProvider.simpleOpenDialog(false)
            }
        }
        ListView {
            id: queueList
            objectName: "floatingQueueList"
            AccessibleCompat.id: "floatingQueueList"
            x: PlayerStyle.px(16); y: PlayerStyle.px(84)
            width: parent.width-x*2; height: Math.max(0,parent.height-y-PlayerStyle.px(12))
            clip: true; model: queueModel
            interactive: contentHeight > height
            currentIndex: queueModel.currentIndex
            delegate: T.ItemDelegate {
                id: entry
                required property int index
                required property string title
                required property var duration
                required property bool isCurrent
                width: queueList.width; height: PlayerStyle.px(40)
                hoverEnabled: true; activeFocusOnTab: true
                Accessible.name: title
                AccessibleCompat.id: "floatingQueueItem"+index
                background: Rectangle {
                    radius: PlayerStyle.px(4)
                    color: entry.isCurrent ? PlayerStyle.accentWell : entry.hovered ? PlayerStyle.hover : "transparent"
                    border.width: entry.visualFocus ? 1 : 0; border.color: PlayerStyle.accent
                }
                contentItem: RowLayout {
                    spacing: PlayerStyle.px(12)
                    Item {
                        width: PlayerStyle.px(10); height: PlayerStyle.px(8)
                        Rectangle { width: parent.width; height: PlayerStyle.px(1); color: PlayerStyle.foreground }
                        Rectangle { y: PlayerStyle.px(4); width: parent.width; height: PlayerStyle.px(1); color: PlayerStyle.foreground }
                    }
                    Text {
                        Layout.fillWidth: true; text: entry.title; textFormat: Text.PlainText; elide: Text.ElideRight
                        font.family: PlayerStyle.fontFamily; font.pixelSize: PlayerStyle.px(12); color: PlayerStyle.foreground
                    }
                    Text {
                        text: entry.duration.formatHMS(0)
                        font.family: PlayerStyle.fontFamily; font.pixelSize: PlayerStyle.px(12); color: PlayerStyle.sectionForeground
                    }
                }
                onClicked: MainPlaylistController.goTo(index,true)
            }
        }
    }
    Item {
        id: card
        y: root.queueHeight; width: parent.width; height: root.cardHeight
        Rectangle {
            id: picture
            x: root.margin; y: root.margin; width: parent.width-root.margin*2; height: root.videoHeight
            color: "black"; radius: PlayerStyle.px(4); clip: true
            VideoSurface {
                anchors.fill: parent
                objectName: "floatingVideoSurface"
                videoSurfaceProvider: MainCtx.floatingPlayer ? MainCtx.videoSurfaceProvider : null
                visible: MainCtx.hasEmbededVideo
            }
            MouseArea {
                anchors.fill: parent
                onClicked: MainPlaylistController.togglePlayPause()
                onDoubleClicked: MainCtx.restoreFloatingPlayer()
            }
            HoverHandler { id: pictureHover }
            Item {
                anchors.fill: parent
                opacity: pictureHover.hovered || miniClose.visualFocus || miniRestore.visualFocus || miniPrevious.visualFocus || miniPlay.visualFocus || miniNext.visualFocus || MainCtx.usingTouch ? 1 : 0
                Rectangle { anchors.fill: parent; color: "#66000000" }
                PlayerIconButton {
                    id: miniClose
                    x: PlayerStyle.px(4); y: PlayerStyle.px(4)
                    glyph: "close"; description: qsTr("Close miniplayer and stop playback")
                    AccessibleCompat.id: "floatingClose"
                    onClicked: MainCtx.dismissFloatingPlayer()
                }
                PlayerIconButton {
                    id: miniRestore
                    anchors.right: parent.right; anchors.top: parent.top; anchors.margins: PlayerStyle.px(4)
                    glyph: "expand-library"; description: qsTr("Restore player")
                    AccessibleCompat.id: "floatingRestore"
                    onClicked: MainCtx.restoreFloatingPlayer()
                }
                Row {
                    anchors.centerIn: parent; spacing: PlayerStyle.px(24)
                    PlayerIconButton {
                        id: miniPrevious
                        glyph: "previous"; description: qsTr("Previous item"); enabled: MainPlaylistController.hasPrev
                        AccessibleCompat.id: "floatingPrevious"; onClicked: MainPlaylistController.prev()
                    }
                    PlayerIconButton {
                        id: miniPlay
                        glyph: !Player.isStarted ? "replay" : Player.playingState===Player.PLAYING_STATE_PLAYING ? "pause" : "play"
                        description: !Player.isStarted ? qsTr("Replay") : qsTr("Play or pause")
                        AccessibleCompat.id: "floatingPlay"
                        onClicked: MainPlaylistController.togglePlayPause()
                    }
                    PlayerIconButton {
                        id: miniNext
                        glyph: "next"; description: qsTr("Next item"); enabled: MainPlaylistController.hasNext
                        AccessibleCompat.id: "floatingNext"; onClicked: MainPlaylistController.next()
                    }
                }
            }
        }
        T.Slider {
            id: seek
            Accessible.name: qsTr("Miniplayer position"); AccessibleCompat.id: "floatingSeek"
            x: root.margin; y: picture.y+picture.height+PlayerStyle.px(5)
            width: picture.width; height: PlayerStyle.px(10)
            from: 0; to: 1; enabled: Player.seekable; activeFocusOnTab: true
            Binding on value { when: !seek.pressed; value: Player.position; restoreMode: Binding.RestoreNone }
            onMoved: Player.position=value
            background: Rectangle {
                anchors.fill: parent; color: PlayerStyle.timeline; radius: PlayerStyle.px(4)
                Rectangle { width: parent.width*seek.visualPosition; height: parent.height; radius: parent.radius; color: PlayerStyle.accentWell }
                border.width: seek.visualFocus ? 1 : 0; border.color: PlayerStyle.accent
            }
            handle: Rectangle {
                x: seek.leftPadding+seek.visualPosition*(seek.availableWidth-width); y: (seek.height-height)/2
                width: PlayerStyle.px(5); height: PlayerStyle.px(10); radius: PlayerStyle.px(3); color: PlayerStyle.accent
            }
        }
        Text {
            AccessibleCompat.id: "floatingMediaName"
            readonly property bool moving: root.moving
            x: PlayerStyle.px(14); y: seek.y+seek.height+PlayerStyle.px(13); width: parent.width-x*2
            text: root.displayName; textFormat: Text.PlainText; elide: Text.ElideRight
            font.family: PlayerStyle.fontFamily; font.pixelSize: PlayerStyle.px(12); color: PlayerStyle.foreground
        }
        RowLayout {
            anchors.bottom: parent.bottom; anchors.left: parent.left; anchors.right: parent.right; anchors.margins: PlayerStyle.px(10)
            spacing: PlayerStyle.px(6)
            PlayerIconButton {
                glyph: "folder"; description: qsTr("Browse media in player")
                AccessibleCompat.id: "floatingFolder"
                onClicked: { MainCtx.playerView=false; MainCtx.restoreFloatingPlayer() }
            }
            Text {
                Layout.fillWidth: true
                text: decodeURIComponent(root.displayFolder.toString().replace(/\/$/,"").split("/").pop() || "")
                textFormat: Text.PlainText; elide: Text.ElideRight
                font.family: PlayerStyle.fontFamily; font.pixelSize: PlayerStyle.px(11); color: PlayerStyle.foreground
            }
            Text {
                visible: root.displayArtist.length>0; Layout.maximumWidth: root.width/3
                text: root.displayArtist; elide: Text.ElideRight; textFormat: Text.PlainText
                font.family: PlayerStyle.fontFamily; font.pixelSize: PlayerStyle.px(11); color: PlayerStyle.foreground
            }
            PlayerIconButton {
                glyph: "queue"; description: qsTr("Show queue"); checkable: true; checked: root.queueExpanded
                AccessibleCompat.id: "floatingQueueToggle"
                onClicked: root.queueExpanded=!root.queueExpanded
            }
        }
    }
    MouseArea {
        anchors.bottom: parent.bottom; anchors.right: parent.right
        width: PlayerStyle.px(8); height: width; cursorShape: Qt.SizeFDiagCursor
        onPressed: root.Window.window.startSystemResize(Qt.RightEdge | Qt.BottomEdge)
    }
    Keys.onEscapePressed: MainCtx.restoreFloatingPlayer()
}
