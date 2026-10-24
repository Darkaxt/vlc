// SPDX-License-Identifier: GPL-2.0-or-later
// Native bookmark storage and embedded chapters; source 6320:13784 / 6321:14045.
import QtQuick
import QtQuick.Templates as T
import QtQuick.Layouts
import VLC.MainInterface
import VLC.Player
import VLC.Util

ColumnLayout {
    id: root
    property bool chapters: false
    readonly property var bookmarks: MainCtx.bookmarks
    property double selectedBookmarkTimestamp: -1
    spacing: 0
    AccessibleCompat.id: "playerPositions"
    Accessible.name: chapters ? qsTr("Embedded chapters") : qsTr("Saved bookmarks")
    RowLayout {
        Layout.fillWidth: true
        Layout.leftMargin: PlayerStyle.px(28)
        Layout.rightMargin: PlayerStyle.px(20)
        Layout.preferredHeight: PlayerStyle.px(64)
        Text {
            Layout.fillWidth: true
            text: root.chapters ? qsTr("%1 Chapters").arg(Player.chapters.count) : qsTr("%1 Bookmarks").arg(root.bookmarks?.count ?? 0)
            font.family: PlayerStyle.fontFamily; font.pixelSize: PlayerStyle.px(14)
            color: PlayerStyle.sectionForeground; textFormat: Text.PlainText
        }
        PlayerIconButton {
            visible: !root.chapters; glyph: "add"; description: qsTr("Add bookmark at current position")
            AccessibleCompat.id: "addPositionBookmark"
            enabled: (root.bookmarks?.available ?? false) && Player.seekable
            onClicked: MainCtx.addBookmark()
        }
    }
    Text {
        visible: !root.chapters && text !== ""
        text: root.bookmarks?.error ?? ""
        Layout.fillWidth: true; Layout.margins: PlayerStyle.px(20)
        wrapMode: Text.WordWrap; color: PlayerStyle.foreground
        font.family: PlayerStyle.fontFamily; font.pixelSize: PlayerStyle.px(14)
        Accessible.name: text
    }
    ListView {
        id: positions
        Layout.fillWidth: true; Layout.fillHeight: true
        Layout.leftMargin: PlayerStyle.px(20); Layout.rightMargin: PlayerStyle.px(20)
        clip: true; spacing: PlayerStyle.px(12)
        model: root.chapters ? Player.chapters : root.bookmarks
        currentIndex: -1
        readonly property int itemCount: count
        AccessibleCompat.id: "positionList"
        onModelChanged: currentIndex = -1
        onHeightChanged: if (currentIndex >= 0 && currentIndex < count)
            positionViewAtIndex(currentIndex, ListView.Contain)
        T.ScrollBar.vertical: T.ScrollBar { policy: T.ScrollBar.AsNeeded }
        delegate: T.Button {
            id: row
            required property int index
            required property var model
            width: positions.width; height: PlayerStyle.px(32)
            readonly property string title: root.chapters ? model.display : model.name
            readonly property string timeLabel: root.chapters ? model.time.formatHMS(0) : model.time
            enabled: root.chapters || Player.seekable
            activeFocusOnTab: true; hoverEnabled: true
            AccessibleCompat.id: "positionRow" + index
            Accessible.name: title + ", " + timeLabel
            onClicked: {
                positions.currentIndex = index
                if (root.chapters) Player.chapters.selectChapter(index)
                else {
                    root.selectedBookmarkTimestamp = model.timestamp
                    root.bookmarks.select(root.bookmarks.index(index,0))
                }
            }
            background: Rectangle {
                radius: PlayerStyle.px(4)
                color: row.hovered || positions.currentIndex === row.index ? PlayerStyle.hover : "transparent"
                border.width: row.visualFocus ? PlayerStyle.px(2) : 0; border.color: PlayerStyle.accent
            }
            contentItem: RowLayout {
                spacing: PlayerStyle.px(8)
                Text { visible: root.chapters; text: row.index + 1; color: PlayerStyle.sectionForeground; font.family: PlayerStyle.fontFamily; font.pixelSize: PlayerStyle.px(14); Layout.preferredWidth: PlayerStyle.px(34) }
                Text { text: row.title; Layout.fillWidth: true; Layout.minimumWidth: 0; elide: Text.ElideRight; color: PlayerStyle.foreground; font.family: PlayerStyle.fontFamily; font.pixelSize: PlayerStyle.px(14); textFormat: Text.PlainText }
                Text { text: row.timeLabel; color: PlayerStyle.foreground; font.family: PlayerStyle.fontFamily; font.pixelSize: PlayerStyle.px(14) }
            }
        }
        Text {
            anchors.centerIn: parent; width: parent.width - PlayerStyle.px(16)
            visible: positions.count === 0
            text: root.chapters ? qsTr("This media has no embedded chapters.") : !MainCtx.mediaLibraryAvailable ? qsTr("Enable the media library to save bookmarks.") : (!(root.bookmarks?.available ?? false) || !Player.seekable) ? qsTr("Open seekable media to add a bookmark.") : qsTr("Add a bookmark to return to this position.")
            wrapMode: Text.WordWrap; horizontalAlignment: Text.AlignHCenter
            font.family: PlayerStyle.fontFamily; font.pixelSize: PlayerStyle.px(14); color: PlayerStyle.foreground
        }
    }
    RowLayout {
        visible: !root.chapters && positions.currentIndex >= 0 && positions.currentIndex < positions.count
        Layout.fillWidth: true; Layout.margins: PlayerStyle.px(20)
        T.TextField {
            id: rename
            Layout.fillWidth: true; Layout.minimumWidth: 0
            implicitHeight: PlayerStyle.px(34); padding: PlayerStyle.px(8)
            placeholderText: qsTr("Rename selected bookmark")
            color: PlayerStyle.foreground; font.family: PlayerStyle.fontFamily; font.pixelSize: PlayerStyle.px(14)
            selectByMouse: true; Accessible.name: placeholderText; AccessibleCompat.id: "bookmarkRename"
            background: Rectangle { color: PlayerStyle.timeline; radius: PlayerStyle.px(4); border.width: rename.activeFocus ? 2 : 0; border.color: PlayerStyle.accent }
            onAccepted: if(text.trim()) { root.bookmarks.renameRow(positions.currentIndex,text); text = "" }
        }
        PlayerIconButton { glyph: "choice-selected"; description: qsTr("Rename bookmark"); enabled: rename.text.trim() !== ""; AccessibleCompat.id: "bookmarkRenameAccept"; onClicked: { root.bookmarks.renameRow(positions.currentIndex,rename.text); rename.text = "" } }
        PlayerIconButton { glyph: "remove"; description: qsTr("Remove bookmark"); AccessibleCompat.id: "removePositionBookmark"; onClicked: { root.bookmarks.removeRow(positions.currentIndex); root.selectedBookmarkTimestamp = -1; positions.currentIndex = -1 } }
    }
    Connections {
        target: root.bookmarks
        function onModelReset() {
            if (root.chapters) return
            const row = root.selectedBookmarkTimestamp >= 0
                ? root.bookmarks.rowForTimestamp(root.selectedBookmarkTimestamp) : -1
            positions.currentIndex = row
            if (row < 0) { root.selectedBookmarkTimestamp = -1; rename.text = "" }
        }
    }
    Connections {
        target: Player
        function onCurrentMediaChanged() {
            root.selectedBookmarkTimestamp = -1
            positions.currentIndex = -1
            rename.text = ""
        }
    }
    Connections {
        target: root
        function onChaptersChanged() {
            root.selectedBookmarkTimestamp = -1
            positions.currentIndex = -1
            rename.text = ""
        }
    }
}
