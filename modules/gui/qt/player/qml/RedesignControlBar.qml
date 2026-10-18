// SPDX-License-Identifier: GPL-2.0-or-later
import QtQuick
import QtQuick.Templates as T
import QtQuick.Layouts
import QtQuick.Controls.impl
import VLC.MainInterface
import VLC.Player
import VLC.Playlist
import VLC.Menus as Menus
import VLC.Style
import VLC.Util

T.Pane {
    id: bar
    property Item popupParent: parent
    property bool queueVisible: false
    readonly property bool compact: width < PlayerStyle.px(760)
    readonly property bool menuOpen: subtitles.visible || audio.visible || playbackMenu.shown
    readonly property real sliderY: (height - seek.height) / 2
    signal toggleQueue()
    signal forceUnlock()
    onForceUnlock: { subtitles.close(); audio.close(); playbackMenu.close() }
    implicitHeight: PlayerStyle.px(54)
    padding: 0
    hoverEnabled: true
    enabled: visible
    Accessible.name: qsTr("Player controls")
    AccessibleCompat.id: "playerControlBar"
    background: Rectangle {
        objectName: "playerVideoBackdrop"
        readonly property real backgroundBlurRadius: PlayerStyle.px(50)
        color: PlayerStyle.chrome
    }

    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: PlayerStyle.px(bar.compact ? 12 : 20)
        anchors.rightMargin: anchors.leftMargin
        spacing: PlayerStyle.px(bar.compact ? 12 : 20)

        RowLayout {
            Layout.fillWidth: false
            Layout.minimumWidth: implicitWidth
            Layout.maximumWidth: implicitWidth
            spacing: PlayerStyle.px(8)
            PlayerIconButton {
                glyph: "previous"
                description: qsTr("Previous")
                enabled: MainPlaylistController.hasPrev
                implicitHeight: PlayerStyle.px(28)
                AccessibleCompat.id: "previousButton"
                onClicked: MainPlaylistController.prev()
            }
            PlayerIconButton {
                glyph: Player.playingState === Player.PLAYING_STATE_PLAYING ? "pause" : "play"
                description: Player.playingState === Player.PLAYING_STATE_PLAYING ? qsTr("Pause") : qsTr("Play")
                accented: true
                implicitWidth: PlayerStyle.px(bar.compact ? 40 : 54)
                implicitHeight: PlayerStyle.px(28)
                enabled: !MainPlaylistController.empty
                AccessibleCompat.id: "playButton"
                onClicked: MainPlaylistController.togglePlayPause()
            }
            PlayerIconButton {
                glyph: "next"
                description: qsTr("Next")
                enabled: MainPlaylistController.hasNext
                implicitHeight: PlayerStyle.px(28)
                AccessibleCompat.id: "nextButton"
                onClicked: MainPlaylistController.next()
            }
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: PlayerStyle.px(8)
            Text {
                AccessibleCompat.id: "playerElapsedTime"
                Layout.preferredWidth: PlayerStyle.px(76)
                visible: !bar.compact
                text: Player.time.formatHMS(0)
                color: PlayerStyle.foreground
                font.family: PlayerStyle.fontFamily
                font.pixelSize: PlayerStyle.px(14)
                horizontalAlignment: Text.AlignHCenter
            }
            T.Slider {
                id: seek
                Layout.fillWidth: true
                Layout.minimumWidth: PlayerStyle.px(60)
                implicitHeight: PlayerStyle.px(28)
                padding: PlayerStyle.px(2)
                from: 0; to: 1
                enabled: Player.seekable
                activeFocusOnTab: true
                Accessible.name: qsTr("Playback position")
                Accessible.description: Player.time.formatHMS(0) + " / " + Player.length.formatHMS(0)
                AccessibleCompat.id: "progressSlider"
                Binding on value { when: !seek.pressed; value: Player.position }
                onMoved: Player.position = value
                background: Rectangle {
                    color: PlayerStyle.timeline
                    radius: PlayerStyle.px(6)
                    Rectangle {
                        x: PlayerStyle.px(2); y: PlayerStyle.px(2)
                        width: Math.max(0, (parent.width - PlayerStyle.px(4)) * seek.visualPosition)
                        height: parent.height - PlayerStyle.px(4)
                        color: PlayerStyle.accent
                        opacity: 0.24
                        radius: PlayerStyle.px(4)
                    }
                    border.width: seek.visualFocus ? PlayerStyle.px(2) : 0
                    border.color: PlayerStyle.accent
                }
                handle: Rectangle {
                    x: seek.leftPadding + seek.visualPosition * (seek.availableWidth - width)
                    y: seek.topPadding
                    width: PlayerStyle.px(8)
                    height: seek.availableHeight
                    radius: PlayerStyle.px(4)
                    color: PlayerStyle.accent
                }
            }
            Text {
                Layout.preferredWidth: PlayerStyle.px(76)
                visible: !bar.compact
                text: Player.length.valid() ? Player.length.formatHMS(0) : "—:—"
                color: PlayerStyle.foreground
                font.family: PlayerStyle.fontFamily
                font.pixelSize: PlayerStyle.px(14)
                horizontalAlignment: Text.AlignHCenter
            }
        }

        RowLayout {
            Layout.fillWidth: false
            Layout.minimumWidth: implicitWidth
            Layout.maximumWidth: implicitWidth
            spacing: PlayerStyle.px(8)
            PlayerIconButton {
                glyph: Player.muted ? "muted" : "volume"
                description: Player.muted ? qsTr("Unmute") : qsTr("Mute")
                implicitWidth: PlayerStyle.px(24)
                implicitHeight: PlayerStyle.px(28)
                AccessibleCompat.id: "muteButton"
                onClicked: Player.muted = !Player.muted
            }
            T.Slider {
                id: volume
                implicitWidth: PlayerStyle.px(bar.compact ? 48 : 88)
                implicitHeight: PlayerStyle.px(28)
                padding: 0
                from: 0; to: MainCtx.maxVolume / 100
                stepSize: 0.05
                activeFocusOnTab: true
                Accessible.name: qsTr("Volume")
                Accessible.description: qsTr("%1 percent").arg(Math.round(Player.volume * 100))
                AccessibleCompat.id: "volumeSlider"
                Binding on value { when: !volume.pressed; value: Player.volume }
                onMoved: { Player.volume = value; Player.muted = false }
                handle: Item {}
                background: Item {
                    clip: true
                    opacity: Player.muted ? 0.45 : 1
                    // Original Figma vectors, using VLC's existing SVG plugin.
                    IconImage {
                        width: volume.width * 89 / 88; height: volume.height
                        sourceSize: Qt.size(width, height)
                        source: "qrc:/redesign/icons/volume-cone.svg"
                        color: PlayerStyle.dark ? "#090909" : "#888888"
                    }
                    Item {
                        width: parent.width * volume.position
                        height: parent.height
                        clip: true
                        Image {
                            width: volume.width * 89 / 88; height: volume.height
                            sourceSize: Qt.size(width, height)
                            source: "qrc:/redesign/icons/volume-level.svg"
                        }
                    }
                    Rectangle {
                        anchors.fill: parent
                        color: "transparent"
                        border.color: PlayerStyle.accent
                        border.width: volume.visualFocus ? PlayerStyle.px(2) : 0
                        radius: PlayerStyle.px(4)
                    }
                }
            }
        }
        RowLayout {
            Layout.fillWidth: false
            Layout.minimumWidth: implicitWidth
            Layout.maximumWidth: implicitWidth
            spacing: PlayerStyle.px(12)
            PlayerIconButton {
                id: toolsButton
                glyph: "tools"
                description: qsTr("Playback, video tracks and tools")
                onClicked: playbackMenu.popup(mapToGlobal(0, 0))
            }
            PlayerIconButton {
                id: subtitleButton
                glyph: "subtitles"
                description: qsTr("Subtitles")
                checked: subtitles.visible
                AccessibleCompat.id: "subtitleButton"
                onClicked: { audio.close(); subtitles.open() }
            }
            PlayerIconButton {
                id: audioButton
                glyph: "audio"
                description: qsTr("Audio and output device")
                checked: audio.visible
                AccessibleCompat.id: "audioButton"
                onClicked: { subtitles.close(); audio.open() }
            }
        }
        PlayerIconButton {
            glyph: "queue"
            description: qsTr("Current playback queue")
            checked: bar.queueVisible
            AccessibleCompat.id: "playqueueToggle"
            onClicked: bar.toggleQueue()
            DropArea {
                anchors.fill: parent
                onEntered: drag => {
                    if (drag.hasUrls && !bar.queueVisible) bar.toggleQueue()
                }
                onDropped: drop => {
                    if (drop.hasUrls) {
                        MainPlaylistController.append(drop.urls, false)
                        drop.acceptProposedAction()
                    }
                }
            }
        }
    }
    PlayerTracksPopup {
        id: subtitles
        parent: bar.popupParent
        subtitles: true
        x: parent.width - width - PlayerStyle.px(20)
        y: bar.y - height - PlayerStyle.px(20)
        onClosed: subtitleButton.forceActiveFocus(Qt.PopupFocusReason)
    }
    PlayerTracksPopup {
        id: audio
        parent: bar.popupParent
        subtitles: false
        x: parent.width - width - PlayerStyle.px(20)
        y: bar.y - height - PlayerStyle.px(20)
        onClosed: audioButton.forceActiveFocus(Qt.PopupFocusReason)
    }
    Menus.QmlGlobalMenu { id: playbackMenu; ctx: MainCtx }
}
