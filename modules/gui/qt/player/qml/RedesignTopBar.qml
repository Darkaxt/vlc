// SPDX-License-Identifier: GPL-2.0-or-later
import QtQuick
import QtQuick.Layouts
import QtQuick.Window
import QtQuick.Templates as T
import VLC.MainInterface
import VLC.Player
import VLC.Menus as Menus
import VLC.Dialogs
import VLC.Util

T.Pane {
    id: header
    property string title
    property bool showCSD: false
    property bool libraryContext: false
    readonly property bool menuOpen: mainMenu.shown
    signal backRequested()
    signal browseRequested()
    signal browseFolderRequested()
    signal queueRequested()
    signal hideChromeRequested()
    signal forceUnlock()
    onForceUnlock: mainMenu.close()
    padding: 0
    implicitHeight: PlayerStyle.px(40)
    hoverEnabled: true
    enabled: visible
    Accessible.name: qsTr("Player title bar")
    AccessibleCompat.id: "playerTopBar"
    background: Rectangle {
        objectName: "playerVideoBackdrop"
        readonly property real backgroundBlurRadius: PlayerStyle.px(50)
        color: PlayerStyle.chrome
    }

    Loader {
        anchors.fill: parent
        active: header.showCSD
        source: "qrc:///qt/qml/VLC/Widgets/CSDTitlebarTapNDrapHandler.qml"
    }
    RowLayout {
        id: left
        x: PlayerStyle.px(6)
        height: parent.height
        spacing: PlayerStyle.px(7)
        PlayerIconButton {
            glyph: "vlc"
            description: qsTr("Back to media")
            foreground: PlayerStyle.accent
            implicitWidth: PlayerStyle.px(38)
            implicitHeight: PlayerStyle.px(28)
            onClicked: header.backRequested()
        }
        PlayerIconButton {
            visible: header.libraryContext
            glyph: "more"
            description: qsTr("Main menu")
            onClicked: mainMenu.popup(mapToGlobal(0,height))
        }
        PlayerIconButton {
            visible: header.libraryContext
            glyph: "queue"
            description: qsTr("Show playback queue")
            AccessibleCompat.id: "libraryQueueButton"
            onClicked: header.queueRequested()
        }
        RowLayout {
            visible: !header.libraryContext
            spacing: 0
            PlayerIconButton {
                glyph: "more"
                description: qsTr("Main menu")
                implicitWidth: PlayerStyle.px(28)
                implicitHeight: PlayerStyle.px(28)
                Layout.rightMargin: PlayerStyle.px(10)
                AccessibleCompat.id: "topBarMenuButton"
                checked: mainMenu.shown
                onClicked: mainMenu.popup(mapToGlobal(0, height))
            }
            PlayerIconButton {
                glyph: "sidebar"
                description: qsTr("Media browser")
                AccessibleCompat.id: "mediaBrowserButton"
                implicitWidth: PlayerStyle.px(28)
                implicitHeight: PlayerStyle.px(28)
                onClicked: header.browseRequested()
            }
            Item {
                implicitWidth: PlayerStyle.px(24)
                implicitHeight: PlayerStyle.px(28)
                Rectangle {
                    anchors.centerIn: parent
                    width: PlayerStyle.px(1)
                    height: PlayerStyle.px(20)
                    color: PlayerStyle.foreground
                    opacity: 0.3
                }
            }
            RowLayout {
                spacing: PlayerStyle.px(4)
                PlayerIconButton {
                    glyph: "folder"
                    description: qsTr("Browse current media folder")
                    implicitWidth: PlayerStyle.px(28)
                    implicitHeight: PlayerStyle.px(28)
                    AccessibleCompat.id: "openFileButton"
                    onClicked: header.browseFolderRequested()
                }
                T.Button {
                    id: sourceTitle
                    implicitWidth: Math.min(PlayerStyle.px(110),contentItem.implicitWidth)
                    implicitHeight: PlayerStyle.px(28)
                    padding: 0
                    Layout.maximumWidth: PlayerStyle.px(110)
                    visible: !header.libraryContext && header.width >= PlayerStyle.px(760)
                    activeFocusOnTab: true
                    onClicked: header.browseFolderRequested()
                    Accessible.name: qsTr("Browse current media folder")
                    background: Item {}
                    contentItem: Text {
                    text: Player.sourceLocationName
                    elide: Text.ElideRight
                    color: PlayerStyle.foreground
                    font.family: PlayerStyle.fontFamily
                    font.pixelSize: PlayerStyle.px(14)
                    }
                }
            }
        }
    }
    Text {
        AccessibleCompat.id: "playerMediaTitle"
        anchors.centerIn: parent
        width: Math.max(0, parent.width - 2 * Math.max(left.width + left.x, right.width + PlayerStyle.px(6)))
        text: header.title
        textFormat: Text.PlainText
        horizontalAlignment: Text.AlignHCenter
        elide: Text.ElideRight
        color: PlayerStyle.foreground
        font.family: PlayerStyle.fontFamily
        font.pixelSize: PlayerStyle.px(14)
        Accessible.name: text
    }
    RowLayout {
        id: right
        anchors.right: parent.right
        anchors.rightMargin: PlayerStyle.px(6)
        height: parent.height
        spacing: 0
        PlayerIconButton {
            visible: header.showCSD
            implicitWidth: PlayerStyle.px(36)
            implicitHeight: PlayerStyle.px(24)
            glyph: "minimize"
            description: qsTr("Minimize")
            onClicked: MainCtx.requestInterfaceMinimized()
        }
        PlayerIconButton {
            visible: header.showCSD
            implicitWidth: PlayerStyle.px(36)
            implicitHeight: PlayerStyle.px(24)
            glyph: "maximize"
            description: MainCtx.intfMainWindow.visibility === Window.Maximized ? qsTr("Restore window") : qsTr("Maximize")
            onClicked: {
                if (MainCtx.intfMainWindow.visibility === Window.Maximized) MainCtx.requestInterfaceNormal()
                else MainCtx.requestInterfaceMaximized()
            }
        }
        PlayerIconButton {
            implicitWidth: PlayerStyle.px(36)
            implicitHeight: PlayerStyle.px(24)
            glyph: "fullscreen"
            description: Player.fullscreen ? qsTr("Leave fullscreen") : qsTr("Fullscreen")
            AccessibleCompat.id: "fullscreenButton"
            onClicked: Player.toggleFullscreen()
        }
        PlayerIconButton {
            visible: header.showCSD
            implicitWidth: PlayerStyle.px(36)
            implicitHeight: PlayerStyle.px(24)
            glyph: "close"
            description: qsTr("Close")
            onClicked: MainCtx.intfMainWindow.close()
        }
    }
    Menus.QmlGlobalMenu {
        id: mainMenu
        ctx: MainCtx
        playerChromeCommand: true
        onHidePlayerChromeRequested: header.hideChromeRequested()
    }
}
