// SPDX-License-Identifier: GPL-2.0-or-later
// Figma node 6216:13614; original geometry, native editable controls.
import QtQuick
import QtQuick.Window
import QtQuick.Layouts
import QtQuick.Templates as T
import VLC.MainInterface
import VLC.Player
import VLC.MediaLibrary
import VLC.Util

T.Popup {
    id: dialog
    property string error: ""
    required property Item backgroundSource
    width: Math.min(parent.width-PlayerStyle.px(24),PlayerStyle.px(1048))
    height: Math.min(parent.height-PlayerStyle.px(24),PlayerStyle.px(631))
    x: Math.max(0,(parent.width-width)/2); y: Math.max(0,(parent.height-height)/2)
    modal: true; focus: true; padding: 0
    onOpened: { error = ""; urls.forceActiveFocus() }
    function keepFocusVisible() {
        const viewport = networkForm.contentItem
        const item = contentItem.Window.window ? contentItem.Window.window.activeFocusItem : null
        if (!viewport || !item) return
        let ancestor = item.parent
        while (ancestor && ancestor !== fields) ancestor = ancestor.parent
        if (!ancestor) return
        const rect = item.mapToItem(viewport.contentItem,Qt.rect(0,0,item.width,item.height))
        if (rect.y < viewport.contentY) viewport.contentY = Math.max(0,rect.y)
        else if (rect.y+rect.height > viewport.contentY+viewport.height) viewport.contentY = Math.min(Math.max(0,viewport.contentHeight-viewport.height),rect.y+rect.height-viewport.height)
    }
    Connections { target: dialog.contentItem.Window.window; function onActiveFocusItemChanged() { if (dialog.opened) dialog.keepFocusVisible() } }
    background: LibraryGlass { id: glass; backgroundSource: dialog.backgroundSource; active: dialog.opened }
    MLPlaylistListModel { id: savedPlaylists; ml: MediaLib }
    component Label: Text {
        color: PlayerStyle.foreground; font.family: PlayerStyle.fontFamily
        font.pixelSize: PlayerStyle.px(16); textFormat: Text.PlainText
        wrapMode: Text.WordWrap
    }
    component Button: T.Button {
        id: button
        padding: PlayerStyle.px(10)
        implicitWidth: Math.max(PlayerStyle.px(100),contentItem.implicitWidth+padding*2)
        implicitHeight: PlayerStyle.px(34)
        hoverEnabled: true; activeFocusOnTab: true
        property bool primary: false
        Accessible.name: text; Accessible.onPressAction: clicked()
        contentItem: Label { text: button.text; horizontalAlignment: Text.AlignHCenter; font.pixelSize: PlayerStyle.px(14); color: button.primary ? "#2e2e2e" : PlayerStyle.foreground }
        background: Rectangle { opacity: button.enabled ? 1 : 0.25; radius: PlayerStyle.px(6); color: button.primary ? PlayerStyle.accent : button.hovered ? PlayerStyle.hover : "transparent"; border.width: button.visualFocus ? PlayerStyle.px(2) : 0; border.color: PlayerStyle.accent }
    }
    contentItem: ColumnLayout {
        readonly property bool ready: glass.ready
        Accessible.role: Accessible.Dialog
        Accessible.name: qsTr("Open network stream")
        AccessibleCompat.id: "networkStreamDialog"
        spacing: 0
        Rectangle {
            Layout.fillWidth: true; implicitHeight: PlayerStyle.px(50)
            topLeftRadius: PlayerStyle.px(14); topRightRadius: PlayerStyle.px(14)
            color: PlayerStyle.timeline
            Label { x: PlayerStyle.px(20); anchors.verticalCenter: parent.verticalCenter; text: qsTr("Open Network Stream"); font.pixelSize: PlayerStyle.px(14) }
            PlayerIconButton { anchors.right: parent.right; anchors.rightMargin: PlayerStyle.px(16); anchors.verticalCenter: parent.verticalCenter; glyph: "close"; description: qsTr("Close network dialog"); onClicked: dialog.close() }
        }
        T.ScrollView {
            id: networkForm
            Layout.fillWidth: true; Layout.fillHeight: true
            clip: true
            contentWidth: availableWidth
            ColumnLayout {
                id: fields
                width: parent.width
                spacing: PlayerStyle.px(20)
                Label { text: qsTr("Network URL"); Layout.fillWidth: true; Layout.leftMargin: PlayerStyle.px(20); Layout.topMargin: PlayerStyle.px(26) }
                Label { text: qsTr("You can enter multiple links to load, one per line."); color: PlayerStyle.sectionForeground; font.pixelSize: PlayerStyle.px(14); Layout.fillWidth: true; Layout.leftMargin: PlayerStyle.px(20) }
                T.TextArea {
                    id: urls
                    Layout.fillWidth: true; Layout.leftMargin: PlayerStyle.px(20); Layout.rightMargin: PlayerStyle.px(20)
                    Layout.preferredHeight: PlayerStyle.px(190)
                    padding: PlayerStyle.px(12); color: PlayerStyle.foreground
                    font.family: PlayerStyle.fontFamily; font.pixelSize: PlayerStyle.px(14)
                    placeholderText: qsTr("e.g., https://www.example.com/stream.avi")
                    selectByMouse: true; wrapMode: TextEdit.Wrap
                    Accessible.name: qsTr("Network URLs"); AccessibleCompat.id: "networkUrlsInput"
                    background: Rectangle { radius: PlayerStyle.px(4); color: PlayerStyle.timeline; border.width: urls.activeFocus ? 1 : 0; border.color: PlayerStyle.accent }
                }
                Rectangle { Layout.fillWidth: true; Layout.leftMargin: PlayerStyle.px(20); Layout.rightMargin: PlayerStyle.px(20); implicitHeight: PlayerStyle.px(1); color: PlayerStyle.hover; opacity: 0.3 }
                Label { text: qsTr("Playlist Name (optional)"); Layout.fillWidth: true; Layout.leftMargin: PlayerStyle.px(20) }
                Label { text: qsTr("The playlist will be saved and displayed with this title."); color: PlayerStyle.sectionForeground; font.pixelSize: PlayerStyle.px(14); Layout.fillWidth: true; Layout.leftMargin: PlayerStyle.px(20) }
                T.TextField {
                    id: playlistName
                    Layout.fillWidth: true; Layout.leftMargin: PlayerStyle.px(20); Layout.rightMargin: PlayerStyle.px(20)
                    implicitHeight: PlayerStyle.px(34); padding: PlayerStyle.px(12)
                    color: PlayerStyle.foreground; font.family: PlayerStyle.fontFamily; font.pixelSize: PlayerStyle.px(14)
                    placeholderText: qsTr("e.g., Favorite TV Channels"); selectByMouse: true
                    Accessible.name: qsTr("Network playlist name"); AccessibleCompat.id: "networkPlaylistName"
                    background: Rectangle { radius: PlayerStyle.px(4); color: PlayerStyle.timeline; border.width: playlistName.activeFocus ? 1 : 0; border.color: PlayerStyle.accent }
                }
                Label { visible: dialog.error !== ""; text: dialog.error; Layout.fillWidth: true; Layout.margins: PlayerStyle.px(20) }
            }
        }
        RowLayout {
            Layout.fillWidth: true; Layout.margins: PlayerStyle.px(20)
            Button { text: qsTr("Cancel"); onClicked: dialog.close() }
            Item { Layout.fillWidth: true }
            Button {
                text: qsTr("Save"); primary: true
                enabled: urls.text.trim() !== "" && !savedPlaylists.transactionPending
                AccessibleCompat.id: "networkStreamSave"
                onClicked: {
                    // Materialize plain URL strings at the QML/native list boundary.
                    const entries = Array.from(MainCtx.networkUrls(urls.text), url => url.toString())
                    if (!entries.length) { dialog.error = qsTr("Enter a complete network URL on each line."); return }
                    if (playlistName.text.trim()) savedPlaylists.create(playlistName.text.trim(),entries)
                    else MediaLib.addAndPlay(entries)
                    dialog.close()
                }
            }
        }
    }
}
