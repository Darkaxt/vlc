// SPDX-License-Identifier: GPL-2.0-or-later
import QtQuick
import QtQuick.Layouts
import QtQuick.Templates as T
import VLC.Player

T.Popup {
    id: dialog
    property bool online: false
    property bool showSaved: false
    width: Math.max(0, Math.min(PlayerStyle.px(1048), parent.width - PlayerStyle.px(40)))
    height: Math.max(0, Math.min(PlayerStyle.px(800), parent.height - PlayerStyle.px(80)))
    padding: PlayerStyle.px(20)
    modal: true
    focus: true
    closePolicy: T.Popup.CloseOnEscape
    onClosed: RemoteSubtitles.cancel()
    onAboutToShow: {
        if (!query.text.length) query.text = Player.title
        if (!online && MediaTools.matches.length === 0) MediaTools.prepareMatches([Player.url], [])
    }
    background: Rectangle { color: PlayerStyle.panel; radius: PlayerStyle.px(10) }
    component Label: Text {
        color: PlayerStyle.trackForeground
        font.family: PlayerStyle.fontFamily
        font.pixelSize: PlayerStyle.px(14)
        textFormat: Text.PlainText
        wrapMode: Text.Wrap
    }
    component Button: T.Button {
        id: button
        implicitWidth: Math.max(PlayerStyle.px(140), implicitContentWidth + leftPadding + rightPadding)
        implicitHeight: PlayerStyle.px(32)
        padding: PlayerStyle.px(8)
        activeFocusOnTab: true
        hoverEnabled: true
        Accessible.name: text
        Accessible.onPressAction: clicked()
        contentItem: Label { text: button.text; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter; elide: Text.ElideRight; wrapMode: Text.NoWrap }
        background: Rectangle { color: button.hovered ? PlayerStyle.hover : PlayerStyle.timeline; radius: PlayerStyle.px(4); border.color: PlayerStyle.accent; border.width: button.visualFocus ? PlayerStyle.px(2) : 0 }
    }
    component Field: T.TextField {
        id: field
        implicitHeight: PlayerStyle.px(34)
        color: PlayerStyle.trackForeground
        placeholderTextColor: PlayerStyle.sectionForeground
        font.family: PlayerStyle.fontFamily
        font.pixelSize: PlayerStyle.px(14)
        padding: PlayerStyle.px(8)
        selectByMouse: true
        maximumLength: 256
        Accessible.name: placeholderText
        background: Rectangle { color: PlayerStyle.timeline; radius: PlayerStyle.px(4); border.color: PlayerStyle.accent; border.width: field.activeFocus ? PlayerStyle.px(2) : 0 }
    }
    contentItem: ColumnLayout {
        spacing: PlayerStyle.px(12)
        RowLayout {
            Layout.fillWidth: true
            Label { text: qsTr("Add Subtitles"); font.pixelSize: PlayerStyle.px(24); Layout.fillWidth: true }
            PlayerIconButton { glyph: "close"; description: qsTr("Close subtitle dialog"); onClicked: dialog.close() }
        }
        RowLayout {
            Layout.fillWidth: true
            Button { text: qsTr("From Computer"); checked: !dialog.online; onClicked: { RemoteSubtitles.cancel(); dialog.online = false } }
            Button { text: qsTr("Find Online"); checked: dialog.online; onClicked: dialog.online = true }
            Item { Layout.fillWidth: true }
        }
        ColumnLayout {
            visible: !dialog.online
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: PlayerStyle.px(12)
            RowLayout {
                Layout.fillWidth: true
                Button { Layout.fillWidth: true; Layout.preferredWidth: 0; text: qsTr("To This File…"); onClicked: MediaTools.browseSubtitle() }
                Button { Layout.fillWidth: true; Layout.preferredWidth: 0; text: qsTr("To This Folder…"); onClicked: MediaTools.browseSubtitleFolder() }
                Button { Layout.fillWidth: true; Layout.preferredWidth: 0; text: qsTr("To Current Queue…"); onClicked: MediaTools.browseQueueSubtitles() }
                Item { Layout.fillWidth: true }
            }
            Label { Layout.fillWidth: true; text: qsTr("Automatic matches are suggestions. Choose ambiguous or unmatched files manually. Unmatched media stays unchanged."); color: PlayerStyle.sectionForeground; font.pixelSize: PlayerStyle.px(12) }
            ListView {
                id: matches
                visible: !dialog.showSaved
                objectName: "subtitleMatches"
                Layout.fillWidth: true
                Layout.fillHeight: true
                model: MediaTools.matches
                clip: true
                boundsBehavior: Flickable.StopAtBounds
                spacing: PlayerStyle.px(8)
                delegate: RowLayout {
                    id: matchRow
                    required property int index
                    required property var modelData
                    width: matches.width
                    height: PlayerStyle.px(60)
                    spacing: PlayerStyle.px(12)
                    Column {
                        Layout.fillWidth: true
                        Layout.preferredWidth: 0
                        Label { width: parent.width; text: modelData.title; wrapMode: Text.NoWrap; elide: Text.ElideMiddle }
                        Label { width: parent.width; text: modelData.state; color: PlayerStyle.sectionForeground; font.pixelSize: PlayerStyle.px(12); wrapMode: Text.NoWrap; elide: Text.ElideRight }
                    }
                    PlayerSettingsChoice {
                        Layout.fillWidth: true
                        Layout.preferredWidth: 0
                        label: qsTr("Subtitle for %1").arg(modelData.title)
                        textRole: "text"
                        valueRole: "value"
                        model: modelData.choices.map(url => ({text: decodeURIComponent(String(url).split('/').pop()), value: url}))
                        displayText: String(modelData.subtitle).length ? decodeURIComponent(String(modelData.subtitle).split('/').pop()) : qsTr("Choose a subtitle")
                        onActivated: MediaTools.chooseMatch(matchRow.index, currentValue)
                    }
                    Button { Layout.preferredWidth: PlayerStyle.px(100); text: qsTr("Browse…"); Accessible.name: qsTr("Choose subtitle for %1").arg(modelData.title); onClicked: MediaTools.browseSubtitle(matchRow.index) }
                }
            }
            ListView {
                visible: dialog.showSaved
                Layout.fillWidth: true; Layout.fillHeight: true
                model: MediaTools.associations
                clip: true
                spacing: PlayerStyle.px(8)
                delegate: RowLayout {
                    required property var modelData
                    width: ListView.view.width; height: PlayerStyle.px(60)
                    Label { Layout.fillWidth: true; Layout.preferredWidth: 0; text: decodeURIComponent(String(modelData.media)) + "\n" + decodeURIComponent(String(modelData.subtitle)); font.pixelSize: PlayerStyle.px(12); elide: Text.ElideMiddle; maximumLineCount: 2 }
                    Button { text: qsTr("Remove"); Layout.preferredWidth: PlayerStyle.px(80); Accessible.name: qsTr("Remove association for %1").arg(String(modelData.media)); onClicked: MediaTools.forgetAssociation(modelData.media) }
                }
            }
            Button { text: dialog.showSaved ? qsTr("Show Matches") : qsTr("Saved Associations"); onClicked: dialog.showSaved = !dialog.showSaved }
            Label { objectName: "subtitleAssociationStatus"; Layout.fillWidth: true; text: MediaTools.status; color: PlayerStyle.sectionForeground; font.pixelSize: PlayerStyle.px(12) }
            RowLayout {
                Layout.fillWidth: true
                Item { Layout.fillWidth: true }
                Button { text: qsTr("Cancel"); onClicked: dialog.close() }
                Button { text: qsTr("Save"); enabled: MediaTools.matches.length > 0; onClicked: if (MediaTools.saveMatches()) dialog.close() }
            }
        }
        ColumnLayout {
            visible: dialog.online
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: PlayerStyle.px(12)
            RowLayout {
                Layout.fillWidth: true
                PlayerSettingsChoice {
                    label: qsTr("Subtitle provider")
                    model: ["OpenSubtitles.com", "SubDL", "SubSource"]
                    currentIndex: RemoteSubtitles.provider
                    onActivated: { RemoteSubtitles.provider = currentIndex; apiKey.clear(); password.clear() }
                }
                Field { id: apiKey; objectName: "subtitleProviderApiKey"; Layout.fillWidth: true; placeholderText: RemoteSubtitles.configured ? qsTr("API key configured for this session") : qsTr("Provider API key"); echoMode: TextInput.Password; maximumLength: 1024 }
                Button { text: qsTr("Use Key"); onClicked: { RemoteSubtitles.setCredentials(apiKey.text); apiKey.clear() } }
            }
            RowLayout {
                visible: RemoteSubtitles.provider === 0
                Layout.fillWidth: true
                Field { id: username; Layout.fillWidth: true; placeholderText: qsTr("OpenSubtitles username (optional)") }
                Field { id: password; objectName: "subtitleProviderPassword"; Layout.fillWidth: true; placeholderText: qsTr("Account password"); echoMode: TextInput.Password; maximumLength: 1024 }
                Button { text: qsTr("Sign In"); enabled: RemoteSubtitles.configured && !RemoteSubtitles.busy; onClicked: { RemoteSubtitles.login(username.text, password.text); password.clear() } }
            }
            RowLayout {
                Layout.fillWidth: true
                Field { id: query; objectName: "remoteSubtitleQuery"; Layout.fillWidth: true; placeholderText: qsTr("Title"); onAccepted: if (!RemoteSubtitles.busy) RemoteSubtitles.search(text, language.text) }
                Field { id: language; Layout.preferredWidth: PlayerStyle.px(90); placeholderText: qsTr("Language"); text: "en"; maximumLength: 8 }
                Button { objectName: "remoteSubtitleSearch"; text: qsTr("Search"); enabled: RemoteSubtitles.configured && !RemoteSubtitles.busy && query.text.length >= 2; onClicked: RemoteSubtitles.search(query.text, language.text) }
            }
            Label { objectName: "remoteSubtitleStatus"; Layout.fillWidth: true; text: RemoteSubtitles.status; color: PlayerStyle.sectionForeground; font.pixelSize: PlayerStyle.px(12) }
            ListView {
                id: results
                objectName: "remoteSubtitleResults"
                Layout.fillWidth: true
                Layout.fillHeight: true
                model: RemoteSubtitles.results
                clip: true
                spacing: PlayerStyle.px(8)
                boundsBehavior: Flickable.StopAtBounds
                delegate: RowLayout {
                    required property int index
                    required property var modelData
                    width: results.width
                    height: PlayerStyle.px(64)
                    spacing: PlayerStyle.px(12)
                    Column {
                        Layout.fillWidth: true
                        Label { width: parent.width; text: modelData.provider + " #" + modelData.reference + " · " + modelData.title; wrapMode: Text.NoWrap; elide: Text.ElideRight }
                        Label { width: parent.width; text: modelData.language + "  " + modelData.release; font.pixelSize: PlayerStyle.px(12); color: PlayerStyle.sectionForeground; maximumLineCount: 2; elide: Text.ElideRight }
                    }
                    HoverHandler { id: resultHover }
                    T.ToolTip.visible: resultHover.hovered
                    T.ToolTip.text: modelData.provider + " #" + modelData.reference + "\n" + modelData.title + "\n" + modelData.language + " · " + modelData.release
                    Button { objectName: "remoteSubtitleResult_" + index; text: modelData.kind === "title" ? qsTr("Show Subtitles") : qsTr("Download and Add"); enabled: !RemoteSubtitles.busy; onClicked: RemoteSubtitles.select(index) }
                }
            }
            RowLayout {
                visible: RemoteSubtitles.archiveFiles.length > 1
                Layout.fillWidth: true
                PlayerSettingsChoice { id: archive; Layout.fillWidth: true; label: qsTr("File inside subtitle archive"); model: RemoteSubtitles.archiveFiles }
                Button { text: qsTr("Add Selected File"); onClicked: RemoteSubtitles.associateArchiveFile(archive.currentIndex) }
            }
            RowLayout {
                Layout.fillWidth: true
                Item { Layout.fillWidth: true }
                Button { text: RemoteSubtitles.busy ? qsTr("Cancel Request") : qsTr("Close"); onClicked: { if (RemoteSubtitles.busy) RemoteSubtitles.cancel(); else dialog.close() } }
            }
        }
    }
}
