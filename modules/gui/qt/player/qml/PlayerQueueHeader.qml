// SPDX-License-Identifier: GPL-2.0-or-later
import QtQuick
import QtQuick.Controls.impl
import QtQuick.Templates as T
import QtQuick.Layouts
import VLC.MainInterface
import VLC.Player
import VLC.Playlist
import VLC.Dialogs
import VLC.Menus
import VLC.Widgets as Widgets
import VLC.Util

Item {
    id: header
    required property var queueModel
    property bool hasSelection: false
    signal removeSelection()
    implicitHeight: PlayerStyle.px(120)

    Rectangle {
        width: parent.width
        height: PlayerStyle.px(50)
        radius: PlayerStyle.px(10)
        color: PlayerStyle.timeline
        Rectangle {
            y: PlayerStyle.px(10)
            width: parent.width
            height: parent.height - y
            color: parent.color
        }
    }

    RowLayout {
        width: parent.width - PlayerStyle.px(12)
        x: PlayerStyle.px(6)
        height: PlayerStyle.px(50)
        spacing: PlayerStyle.px(1)
        Repeater {
            model: [qsTr("Queue"), qsTr("Bookmarks"), qsTr("Chapters")]
            delegate: T.Button {
                id: tab
                required property int index
                required property string modelData
                Layout.fillWidth: true
                Layout.minimumWidth: 0
                Layout.preferredWidth: 0
                Layout.fillHeight: true
                padding: PlayerStyle.px(8)
                bottomPadding: PlayerStyle.px(10)
                activeFocusOnTab: true
                hoverEnabled: true
                Accessible.name: modelData
                Accessible.description: index === 0 ? qsTr("Current playback queue") : qsTr("Open existing bookmarks and chapters menu")
                Accessible.onPressAction: clicked()
                onClicked: if (index !== 0) bookmarksMenu.popup(mapToGlobal(0, height))
                background: Item {
                    Rectangle {
                        x: PlayerStyle.px(8)
                        width: parent.width - PlayerStyle.px(16)
                        anchors.bottom: parent.bottom
                        height: PlayerStyle.px(2)
                        color: tab.index === 0 ? PlayerStyle.accent : "transparent"
                    }
                    Rectangle {
                        anchors.fill: parent
                        color: "transparent"
                        border.width: tab.visualFocus ? PlayerStyle.px(2) : 0
                        border.color: PlayerStyle.accent
                    }
                }
                contentItem: RowLayout {
                    spacing: PlayerStyle.px(8)
                    Item { Layout.fillWidth: true }
                    IconImage {
                        source: "qrc:/redesign/icons/" + ["queue-tab", "bookmarks", "chapters"][tab.index] + ".svg"
                        color: tab.index === 0 ? PlayerStyle.foreground : PlayerStyle.sectionForeground
                        sourceSize: Qt.size(PlayerStyle.px(20), PlayerStyle.px(20))
                        Layout.preferredWidth: PlayerStyle.px(20)
                        Layout.preferredHeight: PlayerStyle.px(20)
                    }
                    Text {
                        Layout.minimumWidth: 0
                        Layout.maximumWidth: Math.max(0, tab.availableWidth - PlayerStyle.px(28))
                        text: tab.modelData
                        font.family: PlayerStyle.fontFamily
                        font.pixelSize: PlayerStyle.px(12)
                        color: tab.index === 0 ? PlayerStyle.foreground : PlayerStyle.sectionForeground
                        elide: Text.ElideRight
                    }
                    Item { Layout.fillWidth: true }
                }
            }
        }
    }
    RowLayout {
        x: PlayerStyle.px(28)
        y: PlayerStyle.px(71)
        width: parent.width - x - PlayerStyle.px(20)
        height: PlayerStyle.px(28)
        spacing: PlayerStyle.px(12)
        Text {
            Layout.fillWidth: true
            AccessibleCompat.id: "playqueueSummary"
            text: {
                const count = header.queueModel.count
                const duration = header.queueModel.duration
                const unknown = header.queueModel.unknownDurationCount
                if (count === 0) return qsTr("0 items")
                if (unknown > 0)
                    return duration.valid() ? qsTr("%1 items · %2 known · %3 unknown").arg(count).arg(duration.formatLong()).arg(unknown)
                                            : qsTr("%1 items · duration unknown").arg(count)
                return qsTr("%1 items · %2").arg(count).arg(duration.formatLong())
            }
            elide: Text.ElideRight
            font.family: PlayerStyle.fontFamily
            font.pixelSize: PlayerStyle.px(14)
            color: PlayerStyle.sectionForeground
            Accessible.name: text
        }
        Widgets.SortControl {
            description: qsTr("Sort queue")
            width: PlayerStyle.px(24); height: PlayerStyle.px(24)
            model: MainPlaylistController.sortKeyTitleList
            sortKey: MainPlaylistController.sortKey
            sortOrder: MainPlaylistController.sortOrder === PlaylistController.SORT_ORDER_ASC ? Qt.AscendingOrder : Qt.DescendingOrder
            onSortSelected: key => MainPlaylistController.sortKey = key
            onSortOrderSelected: order => {
                MainPlaylistController.sortOrder = order === Qt.AscendingOrder ? PlaylistController.SORT_ORDER_ASC : PlaylistController.SORT_ORDER_DESC
                MainPlaylistController.sort()
            }
            contentItem: IconImage {
                source: "qrc:/redesign/icons/sort.svg"
                color: PlayerStyle.foreground
                sourceSize: Qt.size(PlayerStyle.px(24), PlayerStyle.px(24))
            }
            background: Rectangle {
                color: "transparent"
                border.width: parent.visualFocus ? PlayerStyle.px(2) : 0
                border.color: PlayerStyle.accent
            }
        }
        PlayerIconButton {
            glyph: "repeat"
            description: qsTr("Repeat queue or current item")
            checked: MainPlaylistController.repeatMode !== PlaylistController.PLAYBACK_REPEAT_NONE
            implicitWidth: PlayerStyle.px(30); implicitHeight: PlayerStyle.px(28)
            onClicked: MainPlaylistController.toggleRepeatMode()
        }
        PlayerIconButton {
            glyph: "shuffle"
            description: qsTr("Shuffle")
            checked: MainPlaylistController.random
            implicitWidth: PlayerStyle.px(30); implicitHeight: PlayerStyle.px(28)
            onClicked: MainPlaylistController.toggleRandom()
        }
        PlayerIconButton {
            glyph: "remove"
            description: qsTr("Remove selected queue items")
            enabled: header.hasSelection
            implicitWidth: PlayerStyle.px(24); implicitHeight: PlayerStyle.px(28)
            onClicked: header.removeSelection()
        }
        PlayerIconButton {
            glyph: "add"
            description: qsTr("Add files to queue")
            implicitWidth: PlayerStyle.px(24); implicitHeight: PlayerStyle.px(28)
            onClicked: DialogsProvider.simpleOpenDialog(false)
        }
    }
    QmlBookmarkMenu { id: bookmarksMenu; ctx: MainCtx; player: Player }
}
