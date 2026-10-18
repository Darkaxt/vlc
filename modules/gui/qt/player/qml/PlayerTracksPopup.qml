// SPDX-License-Identifier: GPL-2.0-or-later
import QtQuick
import QtQuick.Controls.impl
import QtQuick.Templates as T
import QtQuick.Layouts
import VLC.MainInterface
import VLC.Player
import VLC.Style
import VLC.Dialogs
import VLC.Util

T.Popup {
    id: popup
    required property bool subtitles
    property int currentPage: subtitles ? 2 : 1
    readonly property var tracks: currentPage === 0 ? Player.videoTracks : currentPage === 1 ? Player.audioTracks : Player.subtitleTracks
    width: Math.max(0, Math.min(PlayerStyle.px(400), parent.width - PlayerStyle.px(40)))
    height: Math.max(0, Math.min(PlayerStyle.px(524), parent.height - PlayerStyle.px(134)))
    padding: 0
    focus: true
    closePolicy: T.Popup.CloseOnEscape | T.Popup.CloseOnPressOutside
    onAboutToShow: currentPage = subtitles ? 2 : 1
    background: Rectangle { color: PlayerStyle.panel; radius: PlayerStyle.px(10) }

    function addTrackFile() {
        popup.close()
        if (currentPage === 2) DialogsProvider.loadSubtitlesFile()
        else DialogsProvider.loadAudioFile()
    }

    component Choice: T.ItemDelegate {
        id: choice
        property bool selected: false
        property bool radio: true
        property bool exclusive: true
        width: body.width - PlayerStyle.px(40)
        implicitHeight: PlayerStyle.px(32)
        padding: 0
        activeFocusOnTab: true
        hoverEnabled: true
        Accessible.name: text
        Accessible.role: radio ? (exclusive ? Accessible.RadioButton : Accessible.CheckBox) : Accessible.Button
        Accessible.checked: selected
        Accessible.onPressAction: clicked()
        T.ToolTip.visible: hovered && label.truncated
        T.ToolTip.text: text
        T.ToolTip.delay: VLCStyle.delayToolTipAppear
        background: Rectangle {
            radius: PlayerStyle.px(4)
            color: choice.hovered ? PlayerStyle.hover : "transparent"
            border.width: choice.visualFocus ? PlayerStyle.px(2) : 0
            border.color: PlayerStyle.accent
        }
        contentItem: RowLayout {
            spacing: PlayerStyle.px(10)
            IconImage {
                source: "qrc:/redesign/icons/" + (choice.radio ? (choice.selected ? "choice-selected" : "choice-empty") : "add") + ".svg"
                color: choice.selected ? PlayerStyle.accent : PlayerStyle.trackForeground
                sourceSize: Qt.size(PlayerStyle.px(32), PlayerStyle.px(32))
                Layout.preferredWidth: PlayerStyle.px(32)
                Layout.preferredHeight: PlayerStyle.px(32)
            }
            Text {
                id: label
                Layout.fillWidth: true
                text: choice.text
                color: PlayerStyle.trackForeground
                font.family: PlayerStyle.fontFamily
                font.pixelSize: PlayerStyle.px(14)
                elide: Text.ElideRight
                textFormat: Text.PlainText
            }
        }
    }
    component Section: Item {
        id: section
        property string text
        property bool allowAdd: false
        signal addRequested()
        width: body.width
        height: PlayerStyle.px(60)
        Text {
            x: PlayerStyle.px(28)
            anchors.verticalCenter: parent.verticalCenter
            width: parent.width - PlayerStyle.px(section.allowAdd ? 92 : 56)
            text: section.text
            font.family: PlayerStyle.fontFamily
            font.pixelSize: PlayerStyle.px(14)
            color: PlayerStyle.sectionForeground
            elide: Text.ElideRight
        }
        PlayerIconButton {
            visible: section.allowAdd
            x: parent.width - PlayerStyle.px(52)
            anchors.verticalCenter: parent.verticalCenter
            implicitWidth: PlayerStyle.px(24)
            implicitHeight: PlayerStyle.px(24)
            glyph: "add"
            description: popup.currentPage === 2 ? qsTr("Add subtitle file") : qsTr("Add audio file")
            onClicked: section.addRequested()
        }
    }
    contentItem: Item {
        Accessible.name: [qsTr("Video"), qsTr("Audio"), qsTr("Subtitles")][popup.currentPage]
        Accessible.role: Accessible.Pane
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
            x: PlayerStyle.px(6)
            width: parent.width - PlayerStyle.px(12)
            height: PlayerStyle.px(50)
            spacing: PlayerStyle.px(1)
            Repeater {
                model: [qsTr("Video"), qsTr("Audio"), qsTr("Subtitles")]
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
                    checked: popup.currentPage === index
                    activeFocusOnTab: true
                    Accessible.name: modelData
                    Accessible.role: Accessible.PageTab
                    Accessible.onPressAction: clicked()
                    onClicked: popup.currentPage = index
                    background: Item {
                        Rectangle {
                            x: PlayerStyle.px(8)
                            width: parent.width - PlayerStyle.px(16)
                            anchors.bottom: parent.bottom
                            height: PlayerStyle.px(2)
                            color: tab.checked ? PlayerStyle.accent : "transparent"
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
                            source: "qrc:/redesign/icons/" + ["video", "audio", "subtitles"][tab.index] + ".svg"
                            color: tab.checked ? PlayerStyle.foreground : PlayerStyle.sectionForeground
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
                            color: tab.checked ? PlayerStyle.foreground : PlayerStyle.sectionForeground
                            elide: Text.ElideRight
                        }
                        Item { Layout.fillWidth: true }
                    }
                }
            }
        }
        Flickable {
            id: body
            objectName: popup.subtitles ? "subtitleTracksBody" : "audioTracksBody"
            y: PlayerStyle.px(51)
            width: parent.width
            height: Math.max(0, parent.height - y - PlayerStyle.px(72))
            clip: true
            contentWidth: width
            contentHeight: sections.height
            boundsBehavior: Flickable.StopAtBounds
            Column {
                id: sections
                width: parent.width
                Section {
                    // VLC's existing model includes embedded and added tracks.
                    // Do not label an external track as embedded.
                    text: qsTr("Tracks")
                    allowAdd: popup.currentPage === 1
                    onAddRequested: popup.addTrackFile()
                }
                Item { width: 1; height: PlayerStyle.px(1) }
                Item {
                    width: parent.width
                    height: Math.max(PlayerStyle.px(138), trackList.height + PlayerStyle.px(18))
                    Column {
                        id: trackList
                        x: PlayerStyle.px(20)
                        spacing: PlayerStyle.px(12)
                        Choice {
                            text: qsTr("None")
                            enabled: popup.tracks.count > 0
                            selected: {
                                for (let i = 0; i < trackRows.count; i++)
                                    if (trackRows.itemAt(i)?.selected) return false
                                return true
                            }
                            onClicked: {
                                for (let i = 0; i < popup.tracks.count; i++)
                                    popup.tracks.setData(popup.tracks.index(i, 0), false, Qt.CheckStateRole)
                            }
                        }
                        Repeater {
                            id: trackRows
                            model: popup.tracks
                            delegate: Choice {
                                required property var model
                                exclusive: popup.currentPage !== 0 && !popup.tracks.multiSelect
                                text: model.display
                                selected: model.checked
                                onClicked: model.checked = exclusive ? true : !model.checked
                            }
                        }
                        Text {
                            visible: popup.tracks.count === 0
                            width: body.width - PlayerStyle.px(40)
                            text: popup.currentPage === 2 ? qsTr("No subtitle tracks") : popup.currentPage === 1 ? qsTr("No audio tracks") : qsTr("No video tracks")
                            color: PlayerStyle.trackForeground
                            font.family: PlayerStyle.fontFamily
                            font.pixelSize: PlayerStyle.px(14)
                            wrapMode: Text.Wrap
                        }
                    }
                }
                Rectangle {
                    width: parent.width
                    height: PlayerStyle.px(2)
                    color: PlayerStyle.timeline
                }
                Section {
                    visible: popup.currentPage !== 0
                    text: popup.currentPage === 1 ? qsTr("Output Device") : qsTr("External Tracks")
                    allowAdd: popup.currentPage === 2
                    onAddRequested: popup.addTrackFile()
                }
                Item { width: 1; height: PlayerStyle.px(1) }
                Column {
                    x: PlayerStyle.px(20)
                    width: parent.width - PlayerStyle.px(40)
                    spacing: PlayerStyle.px(12)
                    Repeater {
                        id: devices
                        model: popup.currentPage === 1 ? Player.audioDevices : null
                        delegate: Choice {
                            required property var model
                            text: model.display
                            selected: model.checked
                            onClicked: model.checked = true
                        }
                    }
                    Choice {
                        visible: popup.currentPage === 2
                        radio: false
                        text: qsTr("Add subtitle file…")
                        onClicked: popup.addTrackFile()
                    }
                    Text {
                        visible: popup.currentPage === 1 && devices.count === 0
                        width: parent.width
                        text: qsTr("No output device available")
                        color: PlayerStyle.trackForeground
                        font.family: PlayerStyle.fontFamily
                        font.pixelSize: PlayerStyle.px(14)
                        wrapMode: Text.Wrap
                    }
                }
            }
        }
        T.Button {
            id: preferences
            x: PlayerStyle.px(20)
            y: parent.height - PlayerStyle.px(52)
            width: parent.width - PlayerStyle.px(40)
            height: PlayerStyle.px(32)
            activeFocusOnTab: true
            hoverEnabled: true
            Accessible.name: qsTr("Show Preferences")
            Accessible.onPressAction: clicked()
            background: Rectangle {
                radius: PlayerStyle.px(4)
                color: preferences.hovered ? PlayerStyle.hover : PlayerStyle.timeline
                border.width: preferences.visualFocus ? PlayerStyle.px(2) : 0
                border.color: PlayerStyle.accent
            }
            contentItem: Text {
                text: qsTr("Show Preferences")
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
                color: PlayerStyle.sectionForeground
                font.family: PlayerStyle.fontFamily
                font.pixelSize: PlayerStyle.px(14)
            }
            onClicked: { popup.close(); DialogsProvider.prefsDialog() }
        }
    }
}
