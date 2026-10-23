// SPDX-License-Identifier: GPL-2.0-or-later
// Library layout from Juxtopposed's VLC Redesign (CC BY 4.0).
import QtQuick
import QtQuick.Layouts
import QtQuick.Window
import QtQuick.Templates as T
import QtQuick.Controls.impl
import QtQml.Models
import VLC.MainInterface
import VLC.MediaLibrary
import VLC.Player
import VLC.Playlist
import VLC.Dialogs
import VLC.Util
import VLC.Style
import VLC.Widgets as Widgets

FocusScope {
    id: root
    property bool compact: false
    property string section: "home"
    property var path: []
    property var forwardPath: []
    property string filter: "all"
    property var selectedRows: []
    property var dragRows: []
    property int selectionRevision: 0
    readonly property bool selectionHasVideo: {
        selectionRevision
        return activeModel instanceof MLMediaModel && selectedRows.some(row => !!activeModel.getDataAt(row).isVideo)
    }
    property alias currentRow: items.currentIndex
    property int selectionAnchor: -1
    property string status: ""
    property int addressGeneration: 0
    property bool addressPending: false
    property bool editingAddress: false
    readonly property string category: path.length ? path[path.length - 1].section : section === "videos" ? "folders" : section === "allVideos" ? "videos" : section
    readonly property string heading: path.length ? path[path.length - 1].title : ({home:qsTr("Home"),videos:qsTr("Videos"),folders:qsTr("Folders"),allVideos:qsTr("Videos"),music:qsTr("Music"),songs:qsTr("Songs"),albums:qsTr("Albums"),artists:qsTr("Artists"),genres:qsTr("Genres"),network:qsTr("Network"),playlists:qsTr("Playlists"),recent:qsTr("Recent")})[section]
    readonly property bool historyView: ["home","recent","network"].includes(category)
    readonly property bool containers: ["music", "folders", "albums", "artists", "genres", "playlists"].includes(category)
    readonly property var activeModel: modelLoader.item
    readonly property bool indexing: MediaLib.discoveryPending || !MediaLib.idle
    readonly property bool ready: {
        if (addressPending || !activeModel || MediaLib.discoveryPending) return false
        if (historyView && !MainCtx.historyEnabled) return category !== "home" || (homeLoader.item !== null && homeLoader.item.ready)
        if (activeModel.loading) return false
        if (category === "home") return homeLoader.item !== null && homeLoader.item.ready
        if (category === "folderMedia" && (!childFolderLoader.item || !childFolderLoader.item.ready)) return false
        for (const child of items.contentItem.children) {
            if (child.libraryEntry && child.y + child.height >= items.contentY && child.y <= items.contentY+items.height && child.pending) return false
        }
        return true
    }
    readonly property int itemCount: historyView && !MainCtx.historyEnabled ? 0 : (activeModel ? activeModel.count : 0) + (category === "folderMedia" && childFolderLoader.item ? childFolderLoader.item.folderCount : 0)
    readonly property bool gridMode: LibraryState.viewMode === "grid"
    signal expandRequested()
    signal closeRequested()
    Accessible.role: Accessible.Pane
    Accessible.name: qsTr("Media library")
    AccessibleCompat.id: compact ? "compactLibrary" : "fullLibrary"

    function navigate(next) {
        addressGeneration++; addressPending = false; editingAddress = false; status = ""
        section = next; path = []; forwardPath = []; filter = "all"; search.text = ""; fullSearch.text = ""
        selectedRows = []; currentRow = -1
    }
    function descend(next, title, id, address = "") {
        addressGeneration++; addressPending = false; editingAddress = false; status = ""
        path = [...path, {section: next, title: title, id: id.toString(), address: address.toString()}]
        forwardPath = []; selectedRows = []; currentRow = -1; search.text = ""; fullSearch.text = ""
    }
    function back() {
        addressGeneration++; addressPending = false; editingAddress = false; status = ""
        if (path.length) { forwardPath = [path[path.length - 1], ...forwardPath]; path = path.slice(0, -1) }
        else if (section !== "home") navigate("home")
    }
    function forward() {
        addressGeneration++; addressPending = false; editingAddress = false; status = ""
        if (!forwardPath.length) return
        path = [...path, forwardPath[0]]; forwardPath = forwardPath.slice(1)
    }
    function activate(row) {
        if (row < 0 || !activeModel || row >= activeModel.count) return
        if (category === "music") { navigate(["songs", "albums", "artists", "genres"][row]); return }
        const data = activeModel.getDataAt(row)
        if (category === "network") { activeModel.addAndPlay(data.url); return }
        if (!data.id) return
        const title = data.title || data.name || qsTr("Untitled")
        if (category === "folders") descend("folderMedia", title, data.id, data.mrl)
        else if (["albums", "artists", "genres"].includes(category)) descend("songs", title, data.id)
        else if (category === "playlists") descend("playlistMedia", title, data.id)
        else {
            // Keep the asynchronous request on the interface's long-lived owner
            // when video navigation destroys this view/model.
            MediaLib.addAndPlay(data.id)
            if (data.isVideo) MainCtx.playerView = true
        }
    }
    function choose(row, modifiers) {
        if (row < 0 || !activeModel || row >= activeModel.count) return
        if (modifiers & Qt.ShiftModifier && selectionAnchor >= 0) {
            const from = Math.min(row, selectionAnchor), to = Math.max(row, selectionAnchor)
            selectedRows = Array.from({length: to - from + 1}, (_, i) => from + i)
        } else if (modifiers & Qt.ControlModifier) {
            selectedRows = selectedRows.includes(row) ? selectedRows.filter(r => r !== row) : [...selectedRows, row]
        } else { selectedRows = [row]; selectionAnchor = row }
        currentRow = row
    }
    function selectedIds() {
        if (category === "music" || !selectedRows.length) return Promise.resolve([])
        const source = activeModel
        const rows = selectedRows.slice()
        return new Promise(resolve => source.getDataFlat(rows, data => resolve(data.map(item => item.id).filter(id => !!id))))
    }
    function enqueue() {
        selectedIds().then(ids => { if (ids.length) { MediaLib.addToPlaylist(ids); status = qsTr("Added to queue") } })
    }
    function setSelectionWatched(played) {
        for (const row of selectedRows) activeModel.setItemPlayed(activeModel.index(row,0),played)
    }
    function pin(row) {
        const data = activeModel.getDataAt(row)
        if (data.id) LibraryState.togglePin(data.id.toString(), data.title || data.name || qsTr("Untitled"), category)
    }
    function visitPin(pin) {
        const request = ++addressGeneration
        addressPending = true; status = ""
        const source = pin.section === "folders" ? allFolders : allPlaylists
        source.getDataById(MediaLib.deserializeMlItemIdFromString(pin.id)).then(data => {
            if (request !== addressGeneration) return
            if (pin.section === "folders") {
                if (!data.mrl || !data.mrl.toString()) { addressPending = false; status = qsTr("The pinned folder is unavailable."); return }
                root.openAddress(data.mrl.toString()); return
            }
            section = pin.section === "folders" ? "videos" : pin.section
            path = [{section: pin.section === "folders" ? "folderMedia" : "playlistMedia", title: data.title || data.name, id: pin.id, address: data.mrl ? data.mrl.toString() : ""}]
            selectedRows = []; currentRow = -1; search.text = ""; fullSearch.text = ""
            addressPending = false
        }).catch(() => { if (request === addressGeneration) { addressPending = false; status = qsTr("The pinned item is no longer in the library.") } })
    }
    function openAddress(value) {
        editingAddress = false
        const request = ++addressGeneration
        addressPending = true; status = ""
        const normalized = MainCtx.directoryUrl(value)
        allFolders.resolveAddress(normalized, (id,title,address,nativePath) => {
            if (request !== addressGeneration) return
            if (!id) { addressPending = false; status = qsTr("This folder is not indexed or is unavailable. Use Add item to index it."); return }
            section = "videos"; filter = "all"; path = Array.from(nativePath)
            selectedRows = []; currentRow = -1; search.text = ""; fullSearch.text = ""
            addressPending = false
        })
    }
    function clearSelection() { selectedRows = []; currentRow = -1; selectionAnchor = -1 }
    Connections {
        target: root.activeModel
        ignoreUnknownSignals: true
        function onDataChanged() { root.selectionRevision++ }
        function onModelAboutToBeReset() { root.clearSelection() }
        function onRowsAboutToBeRemoved() { root.clearSelection() }
        function onRowsAboutToBeInserted() { root.clearSelection() }
        function onRowsAboutToBeMoved() { root.clearSelection() }
    }
    Keys.onPressed: event => {
        if ((event.modifiers & Qt.AltModifier) && event.key === Qt.Key_D) {
            editingAddress = true; address.forceActiveFocus(); address.selectAll(); event.accepted = true
        }
        else if (event.key === Qt.Key_Escape) { if (editingAddress) editingAddress = false; else if (path.length || section !== "home") back(); else closeRequested(); event.accepted = true }
        else if ((event.modifiers & Qt.ControlModifier) && event.key === Qt.Key_A) {
            selectedRows = Array.from({length: activeModel ? activeModel.count : 0}, (_, i) => i); event.accepted = true
        }
    }
    Rectangle { anchors.fill: parent; color: PlayerStyle.panel }
    component Label: Text {
        color: PlayerStyle.foreground
        font.family: PlayerStyle.fontFamily
        font.pixelSize: PlayerStyle.px(14)
        textFormat: Text.PlainText
        elide: Text.ElideRight
    }
    component LibraryIcon: PlayerIconButton {
        implicitWidth: PlayerStyle.px(24)
        implicitHeight: PlayerStyle.px(24)
    }
    component Action: T.Button {
        id: action
        font.family: PlayerStyle.fontFamily
        font.pixelSize: PlayerStyle.px(14)
        padding: PlayerStyle.px(8)
        implicitHeight: PlayerStyle.px(34)
        implicitWidth: contentItem.implicitWidth + padding * 2
        hoverEnabled: true
        activeFocusOnTab: true
        Accessible.name: text
        Accessible.onPressAction: clicked()
        background: Rectangle {
            radius: PlayerStyle.px(4)
            color: action.down || action.hovered || action.checked ? PlayerStyle.hover : "transparent"
            border.color: PlayerStyle.accent; border.width: action.visualFocus ? PlayerStyle.px(2) : 0
        }
        contentItem: Label { text: action.text; font: action.font; verticalAlignment: Text.AlignVCenter; opacity: action.enabled ? 1 : 0.4 }
    }
    component LibraryMenu: T.Popup {
        id: menu
        property bool ready: true
        default property alias actions: menuColumn.children
        implicitWidth: Math.min(PlayerStyle.px(265),root.width-PlayerStyle.px(16))
        implicitHeight: Math.min(menuColumn.implicitHeight + padding * 2,root.height-PlayerStyle.px(24))
        padding: PlayerStyle.px(8)
        focus: true
        function keepFocusVisible() {
            const item = menu.contentItem.Window.window ? menu.contentItem.Window.window.activeFocusItem : null
            if (!item) return
            let ancestor = item.parent
            while (ancestor && ancestor !== menuColumn) ancestor = ancestor.parent
            if (!ancestor) return
            const rect = item.mapToItem(menuViewport.contentItem,Qt.rect(0,0,item.width,item.height))
            if (rect.y < menuViewport.contentY) menuViewport.contentY = Math.max(0,rect.y)
            else if (rect.y+rect.height > menuViewport.contentY+menuViewport.height)
                menuViewport.contentY = Math.min(Math.max(0,menuViewport.contentHeight-menuViewport.height),rect.y+rect.height-menuViewport.height)
        }
        onOpened: { menuViewport.contentY = 0; keepFocusVisible() }
        background: Rectangle {
            // Sorting Options 856:2215: solid fill, 10px corners, 4/13.8px shadow.
            color: PlayerStyle.dark ? "#191919" : "#d5d5d5"; radius: PlayerStyle.px(10)
            Widgets.RoundedRectangleShadow { color: Qt.rgba(0,0,0,0.35); yOffset: PlayerStyle.px(4); blurRadius: PlayerStyle.px(13.8); hollow: true }
        }
        contentItem: Flickable {
            id: menuViewport
            readonly property bool ready: menu.ready
            clip: true
            contentHeight: menuColumn.implicitHeight
            Connections { target: menuViewport.Window.window; function onActiveFocusItemChanged() { if (menu.opened) menu.keepFocusVisible() } }
            ColumnLayout { id: menuColumn; width: menuViewport.width; spacing: PlayerStyle.px(2) }
            T.ScrollBar.vertical: T.ScrollBar {}
        }
    }
    component MenuAction: Action {
        Layout.fillWidth: true
        Layout.minimumWidth: 0
        leftPadding: PlayerStyle.px(6)
        rightPadding: PlayerStyle.px(6)
    }
    readonly property var navigation: [
        {key:"home", title:qsTr("Home"), glyph:"home"},
        {key:"videos", title:qsTr("Videos"), glyph:"library-videos"},
        {key:"music", title:qsTr("Music"), glyph:"library-music"},
        {key:"network", title:qsTr("Network"), glyph:"network"},
        {key:"playlists", title:qsTr("Playlists"), glyph:"library-playlists"},
        {key:"recent", title:qsTr("Recent"), glyph:"recent"}
    ]
    Rectangle {
        id: rail
        x: compact ? 0 : PlayerStyle.px(8)
        y: compact ? 0 : PlayerStyle.px(8)
        width: PlayerStyle.px(compact ? 50 : 200)
        height: parent.height - (compact ? 0 : PlayerStyle.px(16))
        radius: compact ? 0 : PlayerStyle.px(6)
        color: PlayerStyle.dark ? "#1b1b1b" : "#d5d5d5"
        Flickable {
            anchors.fill: parent
            contentHeight: navigationColumn.height
            clip: true
            Column {
                id: navigationColumn
                y: PlayerStyle.px(root.compact ? 1 : 5)
                width: parent.width
                Repeater {
                    model: root.navigation
                    delegate: T.Button {
                        id: nav
                        required property var modelData
                        width: rail.width
                        height: PlayerStyle.px(46)
                        hoverEnabled: true; activeFocusOnTab: true
                        Accessible.name: modelData.title
                        AccessibleCompat.id: "libraryNav_" + modelData.key
                        Accessible.onPressAction: clicked()
                        onClicked: root.navigate(modelData.key)
                        background: Rectangle {
                            color: nav.hovered || nav.visualFocus ? PlayerStyle.hover : "transparent"
                            border.width: nav.visualFocus ? PlayerStyle.px(2) : 0; border.color: PlayerStyle.accent
                        }
                        readonly property bool current: root.section === modelData.key || (modelData.key === "videos" && root.section === "allVideos") || (modelData.key === "music" && ["songs","albums","artists","genres"].includes(root.section))
                        contentItem: Item {
                            IconImage {
                                x: PlayerStyle.px(root.compact ? 13 : 19); anchors.verticalCenter: parent.verticalCenter
                                width: PlayerStyle.px(24); height: width
                                sourceSize: Qt.size(width,height)
                                source: "qrc:/redesign/icons/" + nav.modelData.glyph + (nav.current && nav.modelData.key !== "recent" ? "-active" : "") + ".svg"
                                color: nav.current ? PlayerStyle.accent : PlayerStyle.foreground
                            }
                            Label {
                                visible: !root.compact; x: PlayerStyle.px(54); width: parent.width - x - PlayerStyle.px(8)
                                anchors.verticalCenter: parent.verticalCenter; text: nav.modelData.title
                                color: nav.current ? (PlayerStyle.dark ? "#c6c6c6" : PlayerStyle.foreground) : PlayerStyle.foreground
                            }
                        }
                    }
                }
                Action {
                    id: addItem
                    text: qsTr("Add item")
                    padding: 0
                    width: parent.width
                    implicitHeight: PlayerStyle.px(46)
                    AccessibleCompat.id: "libraryAddItem"
                    onClicked: openMenu.open()
                    contentItem: Item {
                        IconImage { x: PlayerStyle.px(root.compact ? 13 : 19); anchors.verticalCenter: parent.verticalCenter; width: PlayerStyle.px(24); height: width; sourceSize: Qt.size(width,height); source: "qrc:/redesign/icons/add.svg"; color: PlayerStyle.foreground }
                        Label { visible: !root.compact; x: PlayerStyle.px(54); width: parent.width-x-PlayerStyle.px(8); anchors.verticalCenter: parent.verticalCenter; text: addItem.text }
                    }
                }
                Repeater {
                    model: root.compact ? [] : LibraryState.pins
                    delegate: Action {
                        required property var modelData
                        text: modelData.title; width: parent.width
                        onClicked: root.visitPin(modelData)
                        onPressAndHold: LibraryState.togglePin(modelData.id, modelData.title, modelData.section)
                    }
                }
            }
        }
    }
    ColumnLayout {
        id: content
        anchors { left: rail.right; right: parent.right; top: parent.top; bottom: parent.bottom; leftMargin: PlayerStyle.px(compact ? 20 : 29); rightMargin: PlayerStyle.px(20); topMargin: PlayerStyle.px(20); bottomMargin: PlayerStyle.px(12) }
        spacing: PlayerStyle.px(16)
        RowLayout {
            Layout.fillWidth: true; spacing: PlayerStyle.px(12)
            LibraryIcon { glyph: "back"; description: qsTr("Back"); AccessibleCompat.id: "libraryBack"; onClicked: root.back() }
            LibraryIcon { glyph: "forward"; description: qsTr("Forward"); enabled: root.forwardPath.length > 0; onClicked: root.forward() }
            Flickable {
                id: breadcrumbViewport
                Layout.fillWidth: true
                Layout.minimumWidth: 0
                Layout.leftMargin: PlayerStyle.px(-2)
                implicitHeight: PlayerStyle.px(root.compact ? 24 : 34)
                clip: true
                contentWidth: crumbs.width; contentHeight: height
                flickableDirection: Flickable.HorizontalFlick
                function keepFocusVisible() {
                    const item = breadcrumbViewport.Window.window ? breadcrumbViewport.Window.window.activeFocusItem : null
                    if (!item) return false
                    let ancestor = item.parent
                    while (ancestor && ancestor !== crumbs) ancestor = ancestor.parent
                    if (!ancestor) return false
                    const rect = item.mapToItem(contentItem,Qt.rect(0,0,item.width,item.height))
                    if (rect.x < contentX) contentX = Math.max(0,rect.x)
                    else if (rect.x+rect.width > contentX+width) contentX = Math.min(Math.max(0,contentWidth-width),rect.x+rect.width-width)
                    return true
                }
                function followFocusOrEnd() { if (!keepFocusVisible()) contentX = Math.max(0,contentWidth-width) }
                onContentWidthChanged: followFocusOrEnd()
                onWidthChanged: followFocusOrEnd()
                Connections { target: breadcrumbViewport.Window.window; function onActiveFocusItemChanged() { breadcrumbViewport.keepFocusVisible() } }
                Row {
                    id: crumbs
                    spacing: PlayerStyle.px(4)
                    Action { padding: 0; implicitHeight: PlayerStyle.px(root.compact ? 24 : 34); font.pixelSize: PlayerStyle.px(16); text: ({home:qsTr("Home"),videos:qsTr("Videos"),folders:qsTr("Folders"),allVideos:qsTr("Videos"),music:qsTr("Music"),network:qsTr("Network"),playlists:qsTr("Playlists"),recent:qsTr("Recent")})[root.section] || root.heading; onClicked: { root.addressGeneration++; root.addressPending = false; root.path = [] } }
                    Repeater {
                        model: root.path
                        delegate: Action {
                            required property int index; required property var modelData
                            padding: 0; implicitHeight: PlayerStyle.px(root.compact ? 24 : 34); font.pixelSize: PlayerStyle.px(16)
                            text: "›  " + modelData.title
                            width: Math.max(0,Math.min(implicitWidth,PlayerStyle.px(root.compact ? 130 : 200),breadcrumbViewport.width))
                            onClicked: { root.addressGeneration++; root.addressPending = false; root.path = root.path.slice(0,index+1) }
                        }
                    }
                }
            }
            Label { visible: !root.compact; text: qsTr("%1 items").arg(root.itemCount); color: PlayerStyle.sectionForeground }
            LibraryIcon { visible: !root.compact; glyph: "sort"; description: qsTr("Sort library"); enabled: !["music","home","network"].includes(root.category); onClicked: sortMenu.open() }
            LibraryIcon { visible: !root.compact; glyph: root.gridMode ? "grid" : "list"; description: qsTr("Change library view"); enabled: LibraryState.writable; onClicked: viewMenu.open() }
            T.TextField {
                id: fullSearch
                visible: !root.compact
                Layout.preferredWidth: Math.min(PlayerStyle.px(325),root.width * 0.22)
                implicitHeight: PlayerStyle.px(34)
                padding: PlayerStyle.px(8); color: PlayerStyle.foreground
                font.family: PlayerStyle.fontFamily; font.pixelSize: PlayerStyle.px(14)
                placeholderText: qsTr("Search"); selectByMouse: true
                Accessible.name: qsTr("Search library"); AccessibleCompat.id: "libraryFullSearch"
                onTextEdited: search.text = text
                background: Rectangle { radius: PlayerStyle.px(6); color: PlayerStyle.dark ? "#171717" : "#dedede"; border.color: PlayerStyle.accent; border.width: fullSearch.activeFocus ? 1 : 0 }
            }
            LibraryIcon { glyph: "more"; description: qsTr("Open media"); onClicked: openMenu.open() }
            LibraryIcon { visible: root.compact; glyph: "expand-library"; description: qsTr("Expand media library"); AccessibleCompat.id: "expandLibrary"; onClicked: root.expandRequested() }
        }
        RowLayout {
            visible: root.compact
            Layout.topMargin: PlayerStyle.px(4)
            Layout.fillWidth: true; spacing: PlayerStyle.px(8)
            Label { text: qsTr("%1 items").arg(root.itemCount); color: PlayerStyle.sectionForeground; Layout.fillWidth: true }
            LibraryIcon { glyph: "sort"; description: qsTr("Sort library"); AccessibleCompat.id: "librarySort"; enabled: !["music","home","network"].includes(root.category); onClicked: sortMenu.open() }
            LibraryIcon { glyph: root.gridMode ? "grid" : "list"; description: qsTr("Change library view"); AccessibleCompat.id: "libraryViewMode"; enabled: LibraryState.writable; onClicked: viewMenu.open() }
            LibraryIcon { visible: root.compact; glyph: "search"; description: qsTr("Search library"); onClicked: { search.visible = !search.visible; if (search.visible) search.forceActiveFocus() } }
        }
        T.TextField {
            id: search
            visible: false
            Layout.fillWidth: true; implicitHeight: PlayerStyle.px(34)
            padding: PlayerStyle.px(8); color: PlayerStyle.foreground
            font.family: PlayerStyle.fontFamily; font.pixelSize: PlayerStyle.px(14)
            placeholderText: qsTr("Search"); placeholderTextColor: PlayerStyle.sectionForeground
            selectByMouse: true; Accessible.name: qsTr("Search library"); AccessibleCompat.id: "librarySearch"
            background: Rectangle { radius: PlayerStyle.px(6); color: PlayerStyle.dark ? "#171717" : "#dedede"; border.color: PlayerStyle.accent; border.width: search.activeFocus ? PlayerStyle.px(1) : 0 }
        }
        T.TextField {
            id: address
            visible: root.editingAddress
            Layout.fillWidth: true; implicitHeight: PlayerStyle.px(34)
            text: root.path.length ? root.path[root.path.length-1].address || "" : ""
            placeholderText: qsTr("Folder address")
            padding: PlayerStyle.px(8); color: PlayerStyle.foreground
            font.family: PlayerStyle.fontFamily; font.pixelSize: PlayerStyle.px(14)
            selectByMouse: true; Accessible.name: qsTr("Folder address"); AccessibleCompat.id: "libraryFolderAddress"
            background: Rectangle { color: PlayerStyle.chrome; radius: PlayerStyle.px(4); border.color: PlayerStyle.accent; border.width: address.activeFocus ? 1 : 0 }
            onAccepted: root.openAddress(text.trim())
        }
        Rectangle { Layout.fillWidth: true; implicitHeight: PlayerStyle.px(1); color: PlayerStyle.hover; opacity: 0.3 }
        Flow {
            visible: root.selectedRows.length > 0 && root.category !== "music"
            Layout.fillWidth: true
            Layout.preferredHeight: childrenRect.height
            spacing: PlayerStyle.px(8)
            Action { text: qsTr("Enqueue"); onClicked: root.enqueue(); AccessibleCompat.id: "libraryEnqueue" }
            Action { text: qsTr("Add to playlist"); onClicked: playlistPicker.open(); AccessibleCompat.id: "libraryAddToPlaylist" }
            Action { visible: ["folders", "playlists"].includes(root.category); text: qsTr("Pin / unpin"); enabled: LibraryState.writable; onClicked: root.pin(root.currentRow) }
            Action { visible: root.selectionHasVideo; text: qsTr("Mark as watched"); onClicked: root.setSelectionWatched(true) }
            Action { visible: root.selectionHasVideo; text: qsTr("Mark as unwatched"); onClicked: root.setSelectionWatched(false) }
            Action { visible: root.category === "playlists"; text: qsTr("Rename"); onClicked: root.activeModel.showDialogRename(root.activeModel.index(root.currentRow,0)) }
            Action { visible: root.category === "playlists"; text: qsTr("Delete playlist"); onClicked: deleteDialog.open() }
            Action { visible: root.category === "playlistMedia"; text: qsTr("Remove from playlist"); onClicked: root.activeModel.remove(root.selectedRows.map(row => root.activeModel.index(row,0))) }
        }
        Loader {
            id: modelLoader
            visible: false
            sourceComponent: {
                if (root.historyView && !MainCtx.historyEnabled) return noHistory
                switch(root.category) {
                case "music": return musicCategories
                case "home": case "recent": return recents
                case "folders": return folders
                case "playlists": return playlists
                case "folderMedia": return root.filter === "unwatched" ? videos : folderItems
                case "playlistMedia": return playlistItems
                case "albums": return albums
                case "artists": return artists
                case "genres": return genres
                case "songs": return songs
                case "network": return streams
                default: return videos
                }
            }
            onLoaded: { root.selectedRows = []; root.currentRow = -1 }
        }
        Loader {
            id: homeLoader
            active: root.category === "home"
            visible: active
            Layout.fillWidth: true; Layout.fillHeight: true
            Layout.topMargin: root.compact ? 0 : PlayerStyle.px(21)
            sourceComponent: PlayerLibraryHome {
                compact: root.compact
                onBrowse: section => root.navigate(section)
                onVisitPin: pin => root.visitPin(pin)
            }
        }
        Loader {
            id: childFolderLoader
            active: root.category === "folderMedia"
            visible: active && item && item.folderCount > 0
            Layout.fillWidth: true
            Layout.fillHeight: root.activeModel && root.activeModel.count === 0
            Layout.preferredHeight: item ? item.contentHeight : 0
            Layout.maximumHeight: root.activeModel && root.activeModel.count > 0 ? root.height * 0.35 : Infinity
            sourceComponent: GridView {
                id: childFolders
                readonly property int folderCount: model.count
                readonly property bool ready: {
                    if (model.loading) return false
                    for (const child of contentItem.children) if (child.folderEntry && child.pending) return false
                    return true
                }
                clip: true
                cellWidth: root.compact ? width : Math.max(PlayerStyle.px(250),width / Math.max(1,Math.floor(width/PlayerStyle.px(400))))
                cellHeight: PlayerStyle.px(42)
                model: MLVideoFoldersModel {
                    ml: MediaLib; hierarchical: true
                    parentId: MediaLib.deserializeMlItemIdFromString(root.path[root.path.length-1].id)
                    searchPattern: search.text
                }
                delegate: T.Button {
                    id: folderButton
                    required property int index
                    required property var model
                    readonly property bool folderEntry: true
                    readonly property bool pending: !model.id
                    width: childFolders.cellWidth; height: childFolders.cellHeight
                    padding: 0; hoverEnabled: true; activeFocusOnTab: true
                    Accessible.name: model.title || qsTr("Folder")
                    AccessibleCompat.id: "libraryChildFolder_" + (model.id ? model.id.toString() : "loading_"+index)
                    Accessible.onPressAction: clicked()
                    onClicked: root.descend("folderMedia",model.title,model.id,model.mrl)
                    onActiveFocusChanged: if (activeFocus) childFolders.positionViewAtIndex(index,GridView.Contain)
                    background: Rectangle { color: folderButton.hovered ? PlayerStyle.hover : "transparent"; radius: PlayerStyle.px(4); border.color: PlayerStyle.accent; border.width: folderButton.visualFocus ? PlayerStyle.px(1) : 0 }
                    contentItem: Item {
                        IconImage { x: PlayerStyle.px(4); anchors.verticalCenter: parent.verticalCenter; width: PlayerStyle.px(24); height: width; sourceSize: Qt.size(width,height); source: "qrc:/redesign/icons/folder.svg"; color: PlayerStyle.foreground }
                        Label { x: PlayerStyle.px(42); anchors.verticalCenter: parent.verticalCenter; width: parent.width-x-PlayerStyle.px(8); text: folderButton.Accessible.name }
                    }
                }
                T.ScrollBar.vertical: T.ScrollBar {}
            }
        }
        GridView {
            id: items
            visible: root.category !== "home" && !(root.category === "folderMedia" && root.activeModel && root.activeModel.count === 0 && childFolderLoader.item && childFolderLoader.item.folderCount > 0)
            Layout.fillWidth: true; Layout.fillHeight: true
            Layout.topMargin: root.compact ? 0 : PlayerStyle.px(4)
            clip: true; focus: true
            model: (root.historyView && !MainCtx.historyEnabled) ? null : root.category === "music" ? [ {name:qsTr("Songs")}, {name:qsTr("Albums")}, {name:qsTr("Artists")}, {name:qsTr("Genres")} ] : root.activeModel
            readonly property bool cards: root.gridMode
            readonly property bool videoCards: ["videos","folderMedia","recent","playlistMedia","network"].includes(root.category)
            Layout.rightMargin: cards ? -PlayerStyle.px(20) : 0
            cellWidth: cards ? Math.min(width, PlayerStyle.px(videoCards ? 336 : 220)) : root.compact || LibraryState.viewMode === "detail" ? width : Math.max(PlayerStyle.px(250), width / Math.max(1, Math.floor(width / PlayerStyle.px(400))))
            cellHeight: PlayerStyle.px(cards ? (videoCards ? 257 : 288) : LibraryState.viewMode === "detail" ? 64 : 42)
            Accessible.name: qsTr("Library items"); AccessibleCompat.id: "libraryItems"
            currentIndex: -1
            Keys.onPressed: event => {
                const columns = Math.max(1,Math.floor(width/cellWidth))
                const delta = event.key === Qt.Key_Right ? 1 : event.key === Qt.Key_Left ? -1 : event.key === Qt.Key_Down ? columns : event.key === Qt.Key_Up ? -columns : 0
                if (delta) {
                    const row = Math.max(0,Math.min(count-1,currentIndex < 0 ? 0 : currentIndex+delta))
                    root.choose(row,event.modifiers); positionViewAtIndex(row,GridView.Contain); event.accepted = true
                }
                else if (event.key === Qt.Key_Return || event.key === Qt.Key_Enter) { root.activate(currentIndex); event.accepted = true }
                else if (event.key === Qt.Key_Space) { root.choose(currentIndex, Qt.ControlModifier); event.accepted = true }
            }
            delegate: Item {
                id: entry
                required property int index
                required property var model
                readonly property url url: model.mrl || model.url || ""
                readonly property bool libraryEntry: true
                readonly property bool pending: (root.category !== "music" && !model.id) || coverImage.status === Image.Loading
                readonly property string title: model.title || model.name || model.url || (root.category === "music" ? model.modelData.name : qsTr("Untitled"))
                readonly property bool selected: root.selectedRows.includes(index)
                readonly property string cover: (model.small_cover || model.thumbnail || model.cover || "").toString()
                width: items.cellWidth; height: items.cellHeight
                Accessible.name: title
                Accessible.role: Accessible.ListItem
                Accessible.selected: selected
                AccessibleCompat.id: "libraryItem_" + (root.category === "music" ? index : model.id ? model.id.toString() : "loading_"+index)
                Accessible.onPressAction: { root.choose(index,Qt.NoModifier); root.activate(index) }
                Rectangle { anchors.fill: parent; anchors.rightMargin: PlayerStyle.px(10); radius: PlayerStyle.px(4); color: entry.selected || mouse.containsMouse ? PlayerStyle.hover : "transparent"; opacity: entry.selected ? 0.75 : 0.35; border.width: entry.selected && items.activeFocus ? PlayerStyle.px(1) : 0; border.color: PlayerStyle.accent }
                Item {
                    id: artwork
                    x: 0; y: items.cards ? 0 : PlayerStyle.px(3)
                    width: items.cards ? parent.width - PlayerStyle.px(20) : PlayerStyle.px(32)
                    height: items.cards ? (items.videoCards ? width*9/16 : width) : PlayerStyle.px(32)
                    Rectangle { anchors.fill: parent; radius: PlayerStyle.px(items.cards ? 8 : 2); color: PlayerStyle.hover }
                    Widgets.ImageExt { id: coverImage; anchors.fill: parent; source: entry.cover; radius: PlayerStyle.px(items.cards ? 12 : 2); fillMode: Image.PreserveAspectCrop; asynchronous: true; visible: status === Image.Ready }
                    IconImage { anchors.centerIn: parent; width: PlayerStyle.px(24); height: width; sourceSize: Qt.size(width,height); visible: !entry.cover; source: "qrc:/redesign/icons/" + (root.category === "music" ? ["music","albums","artists","genres"][entry.index] : root.containers ? "folder" : "play") + ".svg"; color: PlayerStyle.foreground }
                    Rectangle { anchors.left: parent.left; anchors.bottom: parent.bottom; width: parent.width * Math.max(0, Math.min(1, model.progress || 0)); height: PlayerStyle.px(3); color: PlayerStyle.accent }
                }
                Label {
                    x: items.cards ? 0 : PlayerStyle.px(42); y: items.cards ? artwork.height + PlayerStyle.px(20) : PlayerStyle.px(10)
                    font.pixelSize: PlayerStyle.px(items.cards ? 16 : 14)
                    width: parent.width - x - PlayerStyle.px(16); text: entry.title
                    color: model.mrl && model.mrl.toString() === Player.url.toString() ? PlayerStyle.accent : PlayerStyle.foreground
                }
                Label {
                    visible: (items.cards && root.category === "songs") || LibraryState.viewMode === "detail"
                    x: items.cards ? 0 : PlayerStyle.px(42); y: items.cards ? artwork.height + PlayerStyle.px(50) : PlayerStyle.px(33)
                    width: parent.width - x - PlayerStyle.px(16)
                    text: model.main_artist || model.album_title || model.display_mrl || model.fileName || ""
                    color: PlayerStyle.sectionForeground; font.pixelSize: PlayerStyle.px(12)
                }
                MouseArea {
                    id: mouse
                    anchors.fill: parent; hoverEnabled: true; acceptedButtons: Qt.LeftButton | Qt.RightButton
                    onClicked: event => {
                        root.choose(entry.index,event.modifiers); items.forceActiveFocus()
                        if (event.button === Qt.RightButton) {
                            const point = mapToItem(root,event.x,event.y)
                            itemMenu.x = Math.max(PlayerStyle.px(8),Math.min(point.x,root.width-itemMenu.width-PlayerStyle.px(8)))
                            itemMenu.y = Math.max(PlayerStyle.px(8),Math.min(point.y,root.height-itemMenu.height-PlayerStyle.px(8)))
                            itemMenu.open()
                        }
                    }
                    onDoubleClicked: root.activate(entry.index)
                    // Keep selection toolbar layout changes out of the held gesture.
                    // Ordinary clicks commit selection on release; drag payloads
                    // use the pressed row or the existing multi-selection.
                    onPressed: root.dragRows = entry.selected ? root.selectedRows.slice() : [entry.index]
                    drag.target: root.category === "music" ? null : dragProxy
                    onPositionChanged: event => {
                        if (drag.active) { dragPreview.x = mapToItem(dragPreview.parent,event.x,event.y).x; dragPreview.y = mapToItem(dragPreview.parent,event.x,event.y).y }
                    }
                    onReleased: { if (dragPreview.Drag.active) dragPreview.Drag.drop() }
                    Item { id: dragProxy }
                }
                Binding { target: dragPreview.Drag; property: "active"; when: mouse.drag.active; value: true; restoreMode: Binding.RestoreBindingOrValue }
            }
            T.ScrollBar.vertical: T.ScrollBar { }
        }
        Label {
            visible: root.category !== "home" && root.ready && !root.indexing && !root.itemCount
            text: root.historyView && !MainCtx.historyEnabled ? qsTr("Playback history is disabled.") : search.text ? qsTr("No matching items") : root.filter === "unwatched" ? qsTr("No unwatched videos") : qsTr("No items yet. Use Add item to open media or index a folder.")
            wrapMode: Text.WordWrap; elide: Text.ElideNone; Layout.fillWidth: true
        }
        Label { visible: !root.ready || root.indexing; text: root.indexing ? qsTr("Indexing media… %1%").arg(MediaLib.parsingProgress) : qsTr("Loading library…"); Layout.fillWidth: true }
        Label { visible: LibraryState.error !== "" || LibraryState.saveError !== "" || root.status !== ""; text: LibraryState.error || LibraryState.saveError || root.status; wrapMode: Text.WordWrap; elide: Text.ElideNone; Layout.fillWidth: true }
        Action { visible: root.category === "playlists"; text: qsTr("New playlist"); AccessibleCompat.id: "libraryNewPlaylist"; onClicked: newPlaylist.open() }
        Action { visible: root.category === "recent"; text: qsTr("Clear history"); onClicked: root.activeModel.clearHistory() }
    }
    MLDragItem {
        id: dragPreview
        parent: root
        nativeDragEnabled: false
        readonly property bool ready: Drag.active && !!_inputItems && _inputItems.length > 0
        AccessibleCompat.id: "libraryDragPreview"
        z: 10
        view: items; indexesFlat: true; indexes: root.dragRows
        coverRole: "small_cover"
    }
    Component { id: videos; MLVideoModel { ml: MediaLib; unwatchedOnly: root.filter === "unwatched"; searchPattern: search.text; parentId: root.path.length ? MediaLib.deserializeMlItemIdFromString(root.path[root.path.length-1].id) : MediaLib.deserializeMlItemIdFromString("") } }
    Component { id: folderItems; MLMediaModel { ml: MediaLib; searchPattern: search.text; parentId: MediaLib.deserializeMlItemIdFromString(root.path[root.path.length-1].id) } }
    Component { id: folders; MLVideoFoldersModel { ml: MediaLib; hierarchical: true; searchPattern: search.text } }
    Component { id: playlists; MLPlaylistListModel { ml: MediaLib; searchPattern: search.text } }
    Component { id: playlistItems; MLPlaylistModel { ml: MediaLib; parentId: MediaLib.deserializeMlItemIdFromString(root.path[root.path.length-1].id); searchPattern: search.text } }
    Component { id: songs; MLAudioModel { ml: MediaLib; searchPattern: search.text; parentId: root.path.length ? MediaLib.deserializeMlItemIdFromString(root.path[root.path.length-1].id) : MediaLib.deserializeMlItemIdFromString("") } }
    Component { id: albums; MLAlbumModel { ml: MediaLib; searchPattern: search.text } }
    Component { id: artists; MLArtistModel { ml: MediaLib; searchPattern: search.text } }
    Component { id: genres; MLGenreModel { ml: MediaLib; searchPattern: search.text } }
    Component { id: recents; MLRecentMediaModel { ml: MediaLib; searchPattern: search.text } }
    Component { id: streams; MLUrlModel { ml: MediaLib; searchPattern: search.text } }
    Component { id: noHistory; QtObject { readonly property bool loading: false; readonly property int count: 0 } }
    Component { id: musicCategories; QtObject { readonly property bool loading: false; readonly property int count: 4 } }
    LibraryMenu {
        id: openMenu
        x: Math.max(PlayerStyle.px(8),Math.min(rail.x+rail.width,root.width-width-PlayerStyle.px(8))); y: PlayerStyle.px(12)
        MenuAction { visible: root.category === "folderMedia"; text: qsTr("Pin / unpin current folder"); enabled: LibraryState.writable; onClicked: { const folder = root.path[root.path.length-1]; LibraryState.togglePin(folder.id,folder.title,"folders"); openMenu.close() } }
        MenuAction { text: qsTr("Go to folder address…"); onClicked: { openMenu.close(); root.editingAddress = true; address.forceActiveFocus(); address.selectAll() } }
        Repeater {
            model: root.compact ? LibraryState.pins : []
            delegate: MenuAction {
                required property var modelData
                text: modelData.title
                onClicked: { openMenu.close(); root.visitPin(modelData) }
            }
        }
        MenuAction { text: qsTr("Reset library layout"); enabled: LibraryState.writable; onClicked: { openMenu.close(); LibraryState.reset() } }
        MenuAction { text: qsTr("All videos"); onClicked: { openMenu.close(); root.navigate("allVideos") } }
        MenuAction { text: qsTr("Video folders"); onClicked: { openMenu.close(); root.navigate("videos") } }
        MenuAction { text: qsTr("Open file…"); onClicked: { openMenu.close(); DialogsProvider.simpleOpenDialog() } }
        MenuAction { text: qsTr("Open folder…"); onClicked: { openMenu.close(); DialogsProvider.PLOpenDir() } }
        MenuAction { text: qsTr("Index library folder…"); enabled: MainCtx.mediaLibraryAvailable; onClicked: { openMenu.close(); folderDialog.open() } }
        MenuAction { text: qsTr("Open disc…"); onClicked: { openMenu.close(); DialogsProvider.openDiscDialog() } }
        MenuAction { text: qsTr("Open network stream or playlist…"); onClicked: { openMenu.close(); networkDialog.open() } }
        MenuAction { text: qsTr("Open capture device…"); onClicked: { openMenu.close(); DialogsProvider.openCaptureDialog() } }
        MenuAction { text: qsTr("Open clipboard URL…"); onClicked: { openMenu.close(); DialogsProvider.openUrlDialog() } }
    }
    LibraryMenu {
        id: sortMenu
        x: Math.max(PlayerStyle.px(8),root.width-width-PlayerStyle.px(20)); y: Math.max(PlayerStyle.px(8),Math.min(PlayerStyle.px(84),root.height-height-PlayerStyle.px(8)))
        MenuAction { visible: root.activeModel instanceof MLVideoModel || root.category === "folderMedia"; text: root.filter === "unwatched" ? (root.category === "folderMedia" ? qsTr("Show all media") : qsTr("Show all videos")) : qsTr("Show unwatched videos"); onClicked: { root.filter = root.filter === "unwatched" ? "all" : "unwatched"; sortMenu.close() } }
        Repeater {
            model: {
                const named = ["artists","genres","playlists"].includes(root.category)
                const choices = [{text:qsTr("Title"),criteria:named ? "name" : "title"}]
                if (!["artists","genres"].includes(root.category)) choices.push({text:qsTr("Duration"),criteria:"duration"})
                if (["videos","folderMedia","songs","recent"].includes(root.category)) choices.push({text:qsTr("Recently added"),criteria:"insertion"})
                if (root.activeModel instanceof MLMediaModel || root.category === "playlistMedia") choices.push({text:qsTr("Watched"),criteria:"playcount"})
                return choices
            }
            delegate: MenuAction { required property var modelData; text: modelData.text; onClicked: { root.activeModel.sortCriteria = modelData.criteria; sortMenu.close() } }
        }
        MenuAction { text: qsTr("Ascending"); onClicked: { root.activeModel.sortOrder = Qt.AscendingOrder; sortMenu.close() } }
        MenuAction { text: qsTr("Descending"); onClicked: { root.activeModel.sortOrder = Qt.DescendingOrder; sortMenu.close() } }
    }
    LibraryMenu {
        id: viewMenu
        x: Math.max(PlayerStyle.px(8),root.width-width-PlayerStyle.px(20)); y: Math.max(PlayerStyle.px(8),Math.min(PlayerStyle.px(84),root.height-height-PlayerStyle.px(8)))
        MenuAction { text: qsTr("Grid"); onClicked: { LibraryState.setView("grid"); viewMenu.close() } }
        MenuAction { text: qsTr("List"); onClicked: { LibraryState.setView("list"); viewMenu.close() } }
        MenuAction { text: qsTr("Details"); onClicked: { LibraryState.setView("detail"); viewMenu.close() } }
    }
    LibraryMenu {
        id: itemMenu
        ready: !opened || background.ready
        background: LibraryGlass {
            backgroundSource: root; active: itemMenu.opened; radius: PlayerStyle.px(10)
            color: PlayerStyle.dark ? Qt.rgba(25/255,25/255,25/255,0.95) : Qt.rgba(213/255,213/255,213/255,0.95)
        }
        MenuAction { text: qsTr("Play"); onClicked: { root.activate(root.currentRow); itemMenu.close() } }
        MenuAction { text: qsTr("Enqueue"); onClicked: { root.enqueue(); itemMenu.close() } }
        MenuAction { text: qsTr("Add to playlist"); onClicked: { itemMenu.close(); playlistPicker.open() } }
        MenuAction { text: qsTr("Pin / unpin"); visible: ["folders","playlists"].includes(root.category); onClicked: { root.pin(root.currentRow); itemMenu.close() } }
    }
    PlayerLibraryNetworkDialog { id: networkDialog; parent: MainCtx.intfMainWindow.contentItem; backgroundSource: root }
    MLFolderModel { id: indexedFolders; ctx: MainCtx; onOperationFailed: (op,url) => root.status = qsTr("Could not update library folder: %1").arg(url) }
    PlayerLibraryTextDialog {
        id: folderDialog
        parent: root
        title: qsTr("Index library folder")
        hint: qsTr("Enter the full folder path or file URL. Existing files remain unchanged.")
        acceptedText: qsTr("Index folder")
        onSubmitted: value => indexedFolders.add(MainCtx.directoryUrl(value))
    }
    MLVideoFoldersModel { id: allFolders; ml: MediaLib }
    MLPlaylistListModel { id: allPlaylists; ml: MediaLib }
    PlayerLibraryTextDialog {
        id: newPlaylist
        parent: root
        title: qsTr("New playlist"); hint: qsTr("Playlist name"); acceptedText: qsTr("Create")
        onSubmitted: value => allPlaylists.create(value, [])
    }
    T.Popup {
        id: playlistPicker
        parent: root
        x: Math.max(0, (root.width-width)/2); y: PlayerStyle.px(100)
        width: Math.min(root.width,PlayerStyle.px(320)); height: Math.min(root.height-y,PlayerStyle.px(400))
        padding: PlayerStyle.px(12); modal: true; focus: true
        background: Rectangle { color: PlayerStyle.chrome; radius: PlayerStyle.px(8); border.width: 1; border.color: PlayerStyle.hover }
        contentItem: ColumnLayout {
            Label { text: qsTr("Add selection to playlist"); Layout.fillWidth: true }
            ListView {
                Layout.fillWidth: true; Layout.fillHeight: true; clip: true; model: allPlaylists
                delegate: Action { required property string name; required property var model; width: ListView.view.width; text: name; onClicked: { const target = model.id; root.selectedIds().then(ids => { if (ids.length) allPlaylists.append(target,ids) }); playlistPicker.close(); root.status = qsTr("Adding to playlist…") } }
            }
            Action { text: qsTr("Cancel"); onClicked: playlistPicker.close() }
        }
    }
    T.Popup {
        id: deleteDialog
        parent: root; x: Math.max(0,(root.width-width)/2); y: PlayerStyle.px(100)
        width: Math.min(root.width,PlayerStyle.px(320)); height: contentItem.implicitHeight + padding*2
        modal: true; focus: true; padding: PlayerStyle.px(16)
        background: Rectangle { color: PlayerStyle.chrome; radius: PlayerStyle.px(8) }
        contentItem: ColumnLayout {
            Label { text: qsTr("Delete selected stored playlists? Media files and the playback queue are kept."); wrapMode: Text.WordWrap; elide: Text.ElideNone; Layout.fillWidth: true }
            Action { text: qsTr("Delete playlists"); onClicked: { root.selectedIds().then(ids => { if (ids.length) allPlaylists.deletePlaylists(ids) }); deleteDialog.close(); root.selectedRows = [] } }
            Action { text: qsTr("Cancel"); onClicked: deleteDialog.close() }
        }
    }
}
