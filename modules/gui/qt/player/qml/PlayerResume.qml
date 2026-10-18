// SPDX-License-Identifier: GPL-2.0-or-later
import QtQuick
import QtQuick.Layouts
import QtQuick.Templates as T
import VLC.Player
import VLC.Util

T.Pane {
    id: resume
    visible: Player.canRestorePlayback
    enabled: visible
    leftPadding: PlayerStyle.px(20)
    rightPadding: PlayerStyle.px(10)
    topPadding: PlayerStyle.px(10)
    bottomPadding: PlayerStyle.px(10)
    implicitHeight: contentItem.implicitHeight + topPadding + bottomPadding
    Accessible.name: qsTr("Resume playback")
    Accessible.description: qsTr("Press Escape to dismiss the resume suggestion")
    Accessible.role: Accessible.Dialog
    background: Rectangle {
        objectName: "playerVideoBackdrop"
        readonly property real backgroundBlurRadius: PlayerStyle.px(50)
        color: Qt.rgba(0.0966796875, 0.0966796875, 0.0966796875, 0.95)
        radius: PlayerStyle.px(16)
    }
    Shortcut {
        sequence: "Escape"
        enabled: resume.visible
        onActivated: Player.acknowledgeRestoreCallback()
    }
    contentItem: RowLayout {
        spacing: PlayerStyle.px(12)
        Text {
            Layout.fillWidth: true
            text: qsTr("Continue watching where you left off?")
            textFormat: Text.PlainText
            wrapMode: Text.Wrap
            font.family: PlayerStyle.fontFamily
            font.pixelSize: PlayerStyle.px(16)
            color: "#c6c6c6"
        }
        T.Button {
            id: continueButton
            text: qsTr("Continue watching")
            implicitWidth: PlayerStyle.px(146)
            implicitHeight: PlayerStyle.px(32)
            padding: 0
            activeFocusOnTab: true
            Accessible.name: text
            AccessibleCompat.id: "resumeContinueButton"
            Accessible.onPressAction: clicked()
            contentItem: Text {
                text: continueButton.text
                font.family: PlayerStyle.fontFamily
                font.pixelSize: PlayerStyle.px(14)
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
                color: "#2e2e2e"
            }
            background: Rectangle {
                color: PlayerStyle.accent
                radius: PlayerStyle.px(6)
                border.color: PlayerStyle.foreground
                border.width: continueButton.visualFocus ? PlayerStyle.px(2) : 0
            }
            onClicked: { Player.restorePlaybackPos(); Player.acknowledgeRestoreCallback() }
        }

    }
}
