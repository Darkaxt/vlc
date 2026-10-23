// SPDX-License-Identifier: GPL-2.0-or-later
import QtQuick
import QtQuick.Layouts
import QtQuick.Templates as T
import VLC.Player
import VLC.Util

T.Popup {
    id: dialog
    property string title
    property string hint
    property string acceptedText
    signal submitted(string value)
    x: Math.max(0,(parent.width-width)/2)
    y: Math.max(0,(parent.height-height)/2)
    width: Math.min(parent.width-PlayerStyle.px(24),PlayerStyle.px(500))
    height: contentItem.implicitHeight + padding*2
    padding: PlayerStyle.px(20)
    modal: true; focus: true
    onOpened: { field.text = ""; field.forceActiveFocus() }
    background: Rectangle { color: PlayerStyle.panel; radius: PlayerStyle.px(10); border.width: 1; border.color: PlayerStyle.hover }
    contentItem: ColumnLayout {
        spacing: PlayerStyle.px(16)
        Text { text: dialog.title; font.family: PlayerStyle.fontFamily; font.pixelSize: PlayerStyle.px(18); color: PlayerStyle.foreground; Layout.fillWidth: true; textFormat: Text.PlainText }
        Text { text: dialog.hint; font.family: PlayerStyle.fontFamily; font.pixelSize: PlayerStyle.px(14); color: PlayerStyle.foreground; wrapMode: Text.WordWrap; Layout.fillWidth: true; textFormat: Text.PlainText }
        T.TextField {
            id: field
            Layout.fillWidth: true; implicitHeight: PlayerStyle.px(36)
            padding: PlayerStyle.px(8); color: PlayerStyle.foreground
            font.family: PlayerStyle.fontFamily; font.pixelSize: PlayerStyle.px(14)
            selectByMouse: true; Accessible.name: dialog.title; AccessibleCompat.id: "libraryDialogInput"
            background: Rectangle { radius: PlayerStyle.px(4); color: PlayerStyle.chrome; border.width: field.activeFocus ? 2 : 1; border.color: PlayerStyle.accent }
            onAccepted: { if (text.trim()) { dialog.submitted(text.trim()); dialog.close() } }
        }
        RowLayout {
            Layout.alignment: Qt.AlignRight
            PlayerIconButton { glyph: "close"; description: qsTr("Cancel"); onClicked: dialog.close() }
            PlayerIconButton { glyph: "choice-selected"; description: dialog.acceptedText; enabled: field.text.trim() !== ""; AccessibleCompat.id: "libraryDialogSubmit"; onClicked: { dialog.submitted(field.text.trim()); dialog.close() } }
        }
    }
}
