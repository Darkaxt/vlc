// SPDX-License-Identifier: GPL-2.0-or-later
import QtQuick
import QtQuick.Window
import QtQuick.Layouts
import QtQuick.Templates as T
import QtQuick.Controls.impl
import VLC.Player
import VLC.MainInterface
import VLC.MediaLibrary
import VLC.Util
import VLC.Widgets as Widgets

Flickable {
    id: root
    property bool compact: false
    readonly property bool ready: (!MainCtx.historyEnabled || (videoShelf.ready && audioShelf.ready && frequentFolders.ready))
    signal browse(string section)
    signal visitPin(var pin)
    clip: true
    contentHeight: shelves.height
    Accessible.name: qsTr("Library home")
    AccessibleCompat.id: "libraryHome"
    function keepFocusVisible() {
        const item = root.Window.window ? root.Window.window.activeFocusItem : null
        if (!item) return
        let ancestor = item.parent
        while (ancestor && ancestor !== root.contentItem) ancestor = ancestor.parent
        if (!ancestor) return
        const rect = item.mapToItem(root.contentItem,Qt.rect(0,0,item.width,item.height))
        if (rect.y < contentY) contentY = Math.max(0,rect.y)
        else if (rect.y+rect.height > contentY+height) contentY = Math.min(Math.max(0,contentHeight-height),rect.y+rect.height-height)
    }
    Connections { target: root.Window.window; function onActiveFocusItemChanged() { root.keepFocusVisible() } }
    onHeightChanged: keepFocusVisible()
    onContentHeightChanged: keepFocusVisible()
    component Label: Text {
        font.family: PlayerStyle.fontFamily
        color: PlayerStyle.dark ? "#969696" : PlayerStyle.foreground
        font.pixelSize: PlayerStyle.px(root.compact ? 14 : 20); textFormat: Text.PlainText; elide: Text.ElideRight
    }
    component Shelf: ColumnLayout {
        id: shelf
        required property string title
        required property var mediaModel
        property bool audio: false
        signal seeAll()
        readonly property int mediaCount: mediaModel ? mediaModel.count : 0
        readonly property bool ready: {
            if (!mediaModel) return !MainCtx.historyEnabled
            if (mediaModel.loading) return false
            for (const child of entries.contentItem.children) if (child.libraryCard && child.pending) return false
            return true
        }
        Layout.fillWidth: true
        spacing: PlayerStyle.px(root.compact ? 10 : 20)
        RowLayout {
            Layout.fillWidth: true
            Label { text: shelf.title }
            PlayerIconButton { implicitWidth: PlayerStyle.px(24); implicitHeight: PlayerStyle.px(24); glyph: "forward"; description: qsTr("See all %1").arg(shelf.title); onClicked: shelf.seeAll() }
            Item { Layout.fillWidth: true }
        }
        ListView {
            id: entries
            Layout.fillWidth: true
            implicitHeight: shelf.mediaCount === 0 ? 0 : root.compact ? Math.min(3,shelf.mediaCount)*PlayerStyle.px(42) : PlayerStyle.px(shelf.audio ? 268 : 216.75)
            orientation: root.compact ? ListView.Vertical : ListView.Horizontal; spacing: root.compact ? 0 : PlayerStyle.px(20)
            model: shelf.mediaModel
            clip: true; focus: true
            delegate: T.Button {
                id: card
                required property int index
                required property var model
                readonly property bool libraryCard: true
                readonly property bool pending: !model.id || cover.status === Image.Loading
                width: root.compact ? entries.width : PlayerStyle.px(shelf.audio ? 200 : 316)
                height: root.compact ? PlayerStyle.px(42) : entries.height
                padding: 0; hoverEnabled: true; activeFocusOnTab: true
                Accessible.name: model.title || model.name || qsTr("Untitled")
                AccessibleCompat.id: "libraryHomeItem_" + (model.id ? model.id.toString() : "loading_"+index)
                Accessible.onPressAction: clicked()
                onActiveFocusChanged: if (activeFocus) { entries.currentIndex = index; entries.positionViewAtIndex(index,ListView.Contain) }
                onClicked: {
                    if (!model.id) return
                    MediaLib.addAndPlay(model.id)
                    if (!shelf.audio) MainCtx.playerView = true
                }
                background: Rectangle { radius: PlayerStyle.px(8); color: card.hovered ? PlayerStyle.hover : "transparent"; border.color: PlayerStyle.accent; border.width: card.visualFocus ? PlayerStyle.px(2) : 0 }
                contentItem: Item {
                    Item {
                        id: artwork
                        x: 0; y: root.compact ? PlayerStyle.px(5) : 0
                        width: root.compact ? PlayerStyle.px(32) : parent.width
                        height: root.compact ? width : shelf.audio ? width : width * 9/16
                        Rectangle { anchors.fill: parent; radius: PlayerStyle.px(root.compact ? 2 : 12); color: PlayerStyle.hover }
                        Widgets.ImageExt { id: cover; anchors.fill: parent; source: card.model.small_cover || card.model.cover || card.model.thumbnail || ""; radius: PlayerStyle.px(root.compact ? 2 : 12); fillMode: Image.PreserveAspectCrop; asynchronous: true }
                        Rectangle { visible: !shelf.audio; anchors.left: parent.left; anchors.bottom: parent.bottom; height: PlayerStyle.px(3); width: parent.width * Math.max(0,Math.min(1,card.model.progress || 0)); color: PlayerStyle.accent }
                    }
                    Label {
                        x: root.compact ? PlayerStyle.px(42) : 0
                        y: root.compact ? PlayerStyle.px(12) : artwork.height + PlayerStyle.px(20)
                        width: parent.width-x
                        color: PlayerStyle.foreground
                        text: card.Accessible.name + (root.compact && shelf.audio && card.model.main_artist ? " - " + card.model.main_artist : "")
                        font.pixelSize: PlayerStyle.px(root.compact ? 14 : 16)
                    }
                    Label { visible: shelf.audio && !root.compact; width: parent.width; y: artwork.height + PlayerStyle.px(50); text: card.model.main_artist || qsTr("Unknown artist"); font.pixelSize: PlayerStyle.px(14); color: PlayerStyle.sectionForeground }
                }
            }
            T.ScrollBar.horizontal: T.ScrollBar {}
        }
        Label { visible: shelf.mediaModel && shelf.mediaCount === 0 && !shelf.mediaModel.loading; text: qsTr("No recent media"); font.pixelSize: PlayerStyle.px(14); Layout.fillWidth: true }
    }
    Loader {
        id: videoHistory
        active: MainCtx.historyEnabled
        visible: false
        sourceComponent: MLRecentVideoModel { ml: MediaLib; limit: root.compact ? 3 : 12 }
    }
    Loader {
        id: audioHistory
        active: MainCtx.historyEnabled
        visible: false
        sourceComponent: MLAudioModel { ml: MediaLib; historyOnly: true; limit: root.compact ? 3 : 12 }
    }
    Loader {
        id: folderHistory
        active: MainCtx.historyEnabled
        visible: false
        sourceComponent: MLVideoFoldersModel { ml: MediaLib; frequentOnly: true; limit: root.compact ? 3 : 12 }
    }
    ColumnLayout {
        id: shelves
        width: root.width
        spacing: PlayerStyle.px(root.compact ? 30 : 77)
        Shelf {
            id: videoShelf
            title: qsTr("Continue Watching")
            visible: MainCtx.historyEnabled
            mediaModel: videoHistory.item
            onSeeAll: root.browse("recent")
        }
        Shelf {
            id: audioShelf
            title: qsTr("Listen Again")
            visible: MainCtx.historyEnabled
            audio: true
            mediaModel: audioHistory.item
            onSeeAll: root.browse("songs")
        }
        Label { visible: !MainCtx.historyEnabled; text: qsTr("Playback history is disabled."); Layout.fillWidth: true; font.pixelSize: PlayerStyle.px(14) }
        ColumnLayout {
            visible: MainCtx.historyEnabled
            Layout.fillWidth: true
            spacing: PlayerStyle.px(root.compact ? 10 : 20)
            Label { text: qsTr("Frequently Visited Folders"); Layout.fillWidth: true }
            ListView {
                id: frequentFolders
                readonly property bool ready: {
                    if (!folderHistory.item || folderHistory.item.loading) return false
                    for (const child of contentItem.children) if (child.folderCard && child.pending) return false
                    return true
                }
                Layout.fillWidth: true
                implicitHeight: !folderHistory.item || !folderHistory.item.count ? 0 : root.compact ? Math.min(3,folderHistory.item.count)*PlayerStyle.px(42) : PlayerStyle.px(239)
                orientation: root.compact ? ListView.Vertical : ListView.Horizontal
                spacing: root.compact ? 0 : PlayerStyle.px(20)
                model: folderHistory.item
                clip: true
                delegate: T.Button {
                    id: folder
                    required property int index
                    required property var model
                    readonly property bool folderCard: true
                    readonly property bool pending: !model.id || folderCover.status === Image.Loading
                    width: root.compact ? frequentFolders.width : PlayerStyle.px(200)
                    height: root.compact ? PlayerStyle.px(42) : PlayerStyle.px(239)
                    padding: 0; hoverEnabled: true; activeFocusOnTab: true
                    Accessible.name: model.title || qsTr("Folder")
                    AccessibleCompat.id: "libraryFrequentFolder_" + (model.id ? model.id.toString() : "loading")
                    Accessible.onPressAction: clicked()
                    onActiveFocusChanged: if (activeFocus) { frequentFolders.currentIndex = index; frequentFolders.positionViewAtIndex(index,ListView.Contain) }
                    onClicked: if (model.id) root.visitPin({id:model.id.toString(),title:model.title,section:"folders"})
                    background: Rectangle { radius: PlayerStyle.px(12); color: folder.hovered ? PlayerStyle.hover : "transparent"; border.width: folder.visualFocus ? PlayerStyle.px(2) : 0; border.color: PlayerStyle.accent }
                    contentItem: Item {
                        Rectangle {
                            y: root.compact ? PlayerStyle.px(5) : 0
                            width: root.compact ? PlayerStyle.px(32) : parent.width; height: width
                            radius: PlayerStyle.px(root.compact ? 2 : 12); color: PlayerStyle.chrome
                            Widgets.ImageExt { id: folderCover; anchors.fill: parent; source: folder.model.thumbnail || ""; radius: PlayerStyle.px(root.compact ? 2 : 12); fillMode: Image.PreserveAspectCrop; asynchronous: true; visible: status === Image.Ready }
                            IconImage { visible: folderCover.status !== Image.Ready; anchors.centerIn: parent; width: PlayerStyle.px(root.compact ? 24 : 48); height: width; sourceSize: Qt.size(width,height); source: "qrc:/redesign/icons/folder.svg"; color: PlayerStyle.foreground }
                        }
                        Label {
                            x: root.compact ? PlayerStyle.px(42) : 0
                            y: PlayerStyle.px(root.compact ? 12 : 220)
                            width: parent.width-x; text: folder.Accessible.name
                            color: PlayerStyle.foreground; font.pixelSize: PlayerStyle.px(root.compact ? 14 : 16)
                        }
                    }
                }
                T.ScrollBar.horizontal: T.ScrollBar {}
            }
            Label { visible: folderHistory.item && !folderHistory.item.loading && !folderHistory.item.count; text: qsTr("No folders in playback history"); Layout.fillWidth: true; font.pixelSize: PlayerStyle.px(14) }
        }
    }
    T.ScrollBar.vertical: T.ScrollBar {}
}
