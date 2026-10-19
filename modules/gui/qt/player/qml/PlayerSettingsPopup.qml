// SPDX-License-Identifier: GPL-2.0-or-later
import QtQuick
import QtQuick.Controls.impl
import QtQuick.Templates as T
import QtQuick.Layouts
import VLC.MainInterface
import VLC.Player
import VLC.Dialogs

T.Popup {
    id: settingsPopup
    property int page: 0
    property string expanded: ""
    property bool pixelSizes: false
    property int settingsRevision: 0
    Connections { target: MediaTools; function onChanged() { settingsPopup.settingsRevision++ } }
    function filterEnabled(module) { const revision = settingsRevision; return MediaTools.filterEnabled(module) }
    property var presetFolder: ""
    function keepFocusVisible() {
        const item = settingsPopup.contentItem.Window.window ? settingsPopup.contentItem.Window.window.activeFocusItem : null
        if (!item) return
        let ancestor = item.parent
        while (ancestor && ancestor !== body.contentItem) ancestor = ancestor.parent
        if (!ancestor) return
        const rect = item.mapToItem(body.contentItem, Qt.rect(0, 0, item.width, item.height))
        if (rect.y < body.contentY) body.contentY = Math.max(0, rect.y)
        else if (rect.y + rect.height > body.contentY + body.height) body.contentY = Math.min(Math.max(0, body.contentHeight - body.height), rect.y + rect.height - body.height)
    }
    Connections { target: settingsPopup.contentItem.Window.window; function onActiveFocusItemChanged() { settingsPopup.keepFocusVisible() } }
    signal matchSubtitlesRequested()
    signal remoteSubtitlesRequested()
    width: Math.max(0, Math.min(PlayerStyle.px(400), parent.width - PlayerStyle.px(40)))
    height: Math.max(0, Math.min(PlayerStyle.px(946), parent.height - PlayerStyle.px(134)))
    padding: 0
    focus: true
    closePolicy: T.Popup.CloseOnEscape | T.Popup.CloseOnPressOutside
    background: Rectangle { color: PlayerStyle.panel; radius: PlayerStyle.px(10) }
    function showPage(index) { page = index; expanded = ""; open() }
    onOpened: pixelSizes = Number(MediaTools.value("freetype-absolute-fontsize")) > 0
    onPageChanged: body.contentY = 0

    component Label: Text {
        color: PlayerStyle.trackForeground
        font.family: PlayerStyle.fontFamily
        font.pixelSize: PlayerStyle.px(14)
        textFormat: Text.PlainText
        wrapMode: Text.Wrap
    }
    component Button: T.Button {
        id: button
        implicitWidth: Math.max(PlayerStyle.px(64), implicitContentWidth + leftPadding + rightPadding)
        implicitHeight: PlayerStyle.px(32)
        padding: PlayerStyle.px(8)
        activeFocusOnTab: true
        hoverEnabled: true
        Accessible.name: text
        Accessible.onPressAction: clicked()
        contentItem: Label {
            text: button.text
            color: button.checked ? PlayerStyle.accent : PlayerStyle.trackForeground
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
            elide: Text.ElideRight
            wrapMode: Text.NoWrap
        }
        background: Rectangle {
            color: button.hovered ? PlayerStyle.hover : PlayerStyle.timeline
            radius: PlayerStyle.px(4)
            border.color: PlayerStyle.accent
            border.width: button.visualFocus || button.checked ? PlayerStyle.px(2) : 0
        }
    }
    component Section: Item {
        property string text
        width: body.width
        height: PlayerStyle.px(39)
        Label { x: PlayerStyle.px(24); anchors.bottom: parent.bottom; text: parent.text; color: PlayerStyle.trackForeground; font.pixelSize: PlayerStyle.px(16) }
    }
    component Toggle: RowLayout {
        property string text
        property bool checked: false
        property bool available: true
        signal toggled(bool enabled)
        width: body.width - PlayerStyle.px(40)
        height: PlayerStyle.px(52)
        x: PlayerStyle.px(20)
        Label { Layout.fillWidth: true; text: parent.text; opacity: parent.available ? 1 : 0.5 }
        PlayerSettingsSwitch {
            Layout.preferredWidth: PlayerStyle.px(68)
            value: parent.checked
            enabled: parent.available
            Accessible.name: parent.text
            onClicked: parent.toggled(!parent.checked)
        }
    }
    component Effect: Column {
        id: effect
        property string title
        property string module
        property string section
        width: body.width
        topPadding: PlayerStyle.px(10)
        bottomPadding: PlayerStyle.px(20)
        spacing: PlayerStyle.px(10)
        RowLayout {
            x: PlayerStyle.px(20)
            width: parent.width - PlayerStyle.px(40)
            height: PlayerStyle.px(37)
            Label { Layout.fillWidth: true; Layout.leftMargin: PlayerStyle.px(4); text: effect.title }
            PlayerSettingsSwitch {
                visible: effect.module.length > 0
                Layout.preferredWidth: PlayerStyle.px(68)
                value: settingsPopup.filterEnabled(effect.module)
                Accessible.name: effect.title
                onClicked: MediaTools.enableFilter(effect.module, !value)
            }
        }
        Button {
            x: PlayerStyle.px(20)
            width: parent.width - PlayerStyle.px(40)
            id: expandEffect
            implicitHeight: PlayerStyle.px(48)
            padding: PlayerStyle.px(16)
            rightPadding: PlayerStyle.px(42)
            text: settingsPopup.expanded === effect.section ? qsTr("Collapse Settings") : qsTr("Expand Settings")
            Accessible.name: effect.title + ": " + text
            contentItem: Label { text: expandEffect.text; verticalAlignment: Text.AlignVCenter; wrapMode: Text.NoWrap; elide: Text.ElideRight }
            IconImage {
                anchors.right: parent.right; anchors.rightMargin: PlayerStyle.px(10); anchors.verticalCenter: parent.verticalCenter
                width: PlayerStyle.px(24); height: width
                sourceSize: Qt.size(width, height)
                source: "qrc:/redesign/icons/chevron-down.svg"
                color: PlayerStyle.trackForeground
                rotation: settingsPopup.expanded === effect.section ? 180 : 0
            }
            onClicked: settingsPopup.expanded = settingsPopup.expanded === effect.section ? "" : effect.section
        }
        Column {
            x: PlayerStyle.px(20)
            width: parent.width - PlayerStyle.px(40)
            visible: settingsPopup.expanded === effect.section
            Repeater {
                model: effect.section === "crop" ? ["crop-top", "crop-bottom", "crop-left", "crop-right"] : MediaTools.options(effect.section)
                PlayerSettingRow {
                    required property var modelData
                    option: {
                        const revision = settingsPopup.settingsRevision
                        return effect.section === "crop" ? MediaTools.options("crop").find(option => option.key === modelData) : modelData
                    }
                    slider: true
                }
            }
            Button { width: parent.width; text: qsTr("Reset %1").arg(effect.title); onClicked: MediaTools.resetSection(effect.section) }
        }
    }
    component ChoiceRow: RowLayout {
        id: choiceRow
        property string text
        property var choices
        width: body.width - PlayerStyle.px(40)
        height: PlayerStyle.px(48)
        x: PlayerStyle.px(20)
        Label { Layout.fillWidth: true; text: parent.text }
        PlayerSettingsChoice {
            id: trackChoice
            Layout.preferredWidth: PlayerStyle.px(140)
            label: parent.text
            model: parent.choices
            textRole: "display"
            displayText: currentIndex < 0 ? qsTr("None") : currentText
            delegate: T.ItemDelegate {
                required property var model
                width: parent ? parent.width : PlayerStyle.px(152)
                implicitHeight: PlayerStyle.px(34)
                text: model.display
                padding: PlayerStyle.px(8)
                onClicked: model.checked = true
                contentItem: Label { text: parent.text }
                background: Rectangle { color: parent.hovered ? PlayerStyle.hover : PlayerStyle.panel }
            }
            function refreshSelection() {
                const source = choiceRow.choices
                const count = source ? source.rowCount() : 0
                let selected = -1
                for (let i = 0; i < count; i++) if (source.data(source.index(i, 0), Qt.CheckStateRole)) { selected = i; break }
                currentIndex = selected
            }
            Component.onCompleted: refreshSelection()
            onModelChanged: refreshSelection()
            Connections {
                target: choiceRow.choices
                function onDataChanged() { trackChoice.refreshSelection() }
                function onModelReset() { trackChoice.refreshSelection() }
                function onRowsInserted() { trackChoice.refreshSelection() }
                function onRowsRemoved() { trackChoice.refreshSelection() }
            }
            onActivated: if (parent.choices) parent.choices.setData(parent.choices.index(currentIndex, 0), true, Qt.CheckStateRole)
        }
    }
    component TimingRow: Column {
        id: timing
        property string text
        property string editorName: ""
        property string unit: ""
        property real value: 0
        property real minimum: -10
        property real maximum: 10
        property real step: 0.1
        property bool rangeLabels: true
        signal edited(real number)
        x: PlayerStyle.px(20)
        width: body.width - PlayerStyle.px(40)
        height: PlayerStyle.px(rangeLabels ? 115 : 90)
        RowLayout {
            width: parent.width; height: PlayerStyle.px(56)
            Label { text: timing.text; Layout.fillWidth: true }
            T.TextField {
                objectName: timing.editorName
                Layout.preferredWidth: PlayerStyle.px(140); implicitHeight: PlayerStyle.px(36)
                text: Number(timing.value).toFixed(3) + (timing.unit.length ? " " + timing.unit : "")
                color: PlayerStyle.trackForeground; font.family: PlayerStyle.fontFamily; font.pixelSize: PlayerStyle.px(14)
                padding: PlayerStyle.px(8); selectByMouse: true
                Accessible.name: timing.text
                onEditingFinished: { const number = Number(text.replace(timing.unit, "").trim()); if (isFinite(number)) timing.edited(number) }
                background: Rectangle { color: PlayerStyle.timeline; radius: PlayerStyle.px(4); border.width: parent.activeFocus ? PlayerStyle.px(2) : 0; border.color: PlayerStyle.accent }
            }
        }
        Item { width: 1; height: PlayerStyle.px(5) }
        T.Slider {
            id: timeSlider
            width: parent.width; height: PlayerStyle.px(24)
            from: timing.minimum; to: timing.maximum; value: timing.value; stepSize: timing.step
            activeFocusOnTab: true; Accessible.name: timing.text
            onMoved: timing.edited(value)
            background: Rectangle { x: timeSlider.leftPadding; y: (timeSlider.height - height)/2; width: timeSlider.availableWidth; height: PlayerStyle.px(12); radius: height/2; color: PlayerStyle.timeline; Rectangle { width: parent.width * timeSlider.visualPosition; height: parent.height; radius: parent.radius; color: PlayerStyle.accent; opacity: 0.45 } }
            handle: Rectangle { x: timeSlider.leftPadding + timeSlider.visualPosition * (timeSlider.availableWidth - width); y: (timeSlider.height-height)/2; width: PlayerStyle.px(8); height: PlayerStyle.px(24); radius: width/2; color: PlayerStyle.accent; border.width: timeSlider.visualFocus ? 1 : 0; border.color: PlayerStyle.trackForeground }
        }
        RowLayout {
            visible: timing.rangeLabels
            width: parent.width; height: PlayerStyle.px(25)
            Label { text: String(timing.minimum) + (timing.unit.length ? " " + timing.unit : ""); font.pixelSize: PlayerStyle.px(12); color: PlayerStyle.sectionForeground }
            Item { Layout.fillWidth: true }
            Label { text: "0" + (timing.unit.length ? " " + timing.unit : ""); font.pixelSize: PlayerStyle.px(12); color: PlayerStyle.sectionForeground }
            Item { Layout.fillWidth: true }
            Label { text: "+" + String(timing.maximum) + (timing.unit.length ? " " + timing.unit : ""); font.pixelSize: PlayerStyle.px(12); color: PlayerStyle.sectionForeground }
        }
        Item { width: 1; height: PlayerStyle.px(5) }
    }
    component LanguageRow: RowLayout {
        id: languageRow
        property bool subtitle: false
        width: body.width - PlayerStyle.px(40); height: PlayerStyle.px(48); x: PlayerStyle.px(20)
        Label { Layout.fillWidth: true; text: parent.subtitle ? qsTr("Subtitle Language") : qsTr("Audio Language") }
        PlayerSettingsChoice {
            id: languageChoice
            Layout.preferredWidth: PlayerStyle.px(140)
            label: parent.subtitle ? qsTr("Subtitle language") : qsTr("Audio language")
            textRole: "text"; valueRole: "value"
            model: { const revision = settingsPopup.settingsRevision; return MediaTools.trackLanguages(languageRow.subtitle) }
            displayText: currentIndex < 0 ? qsTr("Unspecified") : currentText
            function refreshSelection() { currentIndex = indexOfValue(MediaTools.selectedLanguage(languageRow.subtitle)) }
            Component.onCompleted: refreshSelection()
            onModelChanged: refreshSelection()
            onCountChanged: refreshSelection()
            Connections { target: MediaTools; function onChanged() { languageChoice.refreshSelection() } }
            onActivated: MediaTools.setPreferredTrack(languageRow.subtitle, currentValue, -1)
        }
    }
    contentItem: Item {
        Accessible.name: qsTr("Playback and media settings")
        Accessible.role: Accessible.Pane
        Rectangle { width: parent.width; height: PlayerStyle.px(50); color: PlayerStyle.timeline; radius: PlayerStyle.px(10) }
        RowLayout {
            width: parent.width
            height: PlayerStyle.px(50)
            spacing: 0
            Repeater {
                model: [qsTr("Playback"), qsTr("Video"), qsTr("Audio"), qsTr("Subtitles")]
                T.Button {
                    required property int index
                    required property string modelData
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    Layout.preferredWidth: 0
                    padding: PlayerStyle.px(4)
                    activeFocusOnTab: true
                    Accessible.name: modelData
                    Accessible.role: Accessible.PageTab
                    Accessible.onPressAction: clicked()
                    onClicked: { settingsPopup.page = index; settingsPopup.expanded = "" }
                    contentItem: RowLayout {
                        spacing: PlayerStyle.px(4)
                        IconImage { source: "qrc:/redesign/icons/" + ["playback","video","audio","subtitles"][parent.parent.index] + ".svg"; sourceSize: Qt.size(PlayerStyle.px(20), PlayerStyle.px(20)); Layout.preferredWidth: PlayerStyle.px(20); Layout.preferredHeight: PlayerStyle.px(20); color: settingsPopup.page === parent.parent.index ? PlayerStyle.trackForeground : PlayerStyle.sectionForeground }
                        Label { text: parent.parent.modelData; font.pixelSize: PlayerStyle.px(12); Layout.fillWidth: true; verticalAlignment: Text.AlignVCenter; wrapMode: Text.NoWrap; elide: Text.ElideRight }
                    }
                    background: Item {
                        Rectangle { anchors.bottom: parent.bottom; width: parent.width - PlayerStyle.px(16); x: PlayerStyle.px(8); height: PlayerStyle.px(2); color: settingsPopup.page === parent.parent.index ? PlayerStyle.accent : "transparent" }
                        Rectangle { anchors.fill: parent; color: "transparent"; border.width: parent.parent.visualFocus ? PlayerStyle.px(2) : 0; border.color: PlayerStyle.accent }
                    }
                }
            }
        }
        Flickable {
            id: body
            objectName: "mediaSettingsBody"
            y: PlayerStyle.px(51)
            width: parent.width
            height: Math.max(0, parent.height - y - PlayerStyle.px(126))
            contentWidth: width
            contentHeight: pages.implicitHeight
            clip: true
            boundsBehavior: Flickable.StopAtBounds
            Column {
                id: pages
                width: parent.width
                Button {
                    visible: settingsPopup.page !== 0
                    x: PlayerStyle.px(20)
                    width: parent.width - PlayerStyle.px(40)
                    text: qsTr("Defaults")
                    implicitHeight: PlayerStyle.px(39)
                    Accessible.name: qsTr("Reset this page to defaults")
                    contentItem: Label { text: qsTr("Defaults"); font.pixelSize: PlayerStyle.px(16); verticalAlignment: Text.AlignBottom }
                    background: Rectangle { color: "transparent"; border.color: PlayerStyle.accent; border.width: parent.visualFocus ? 1 : 0 }
                    onClicked: {
                        if (settingsPopup.page === 3) MediaTools.resetSection("subtitle")
                        else if (settingsPopup.page === 2) for (const section of ["equalizer", "compressor", "spatializer", "stereo_widen", "pitch"]) MediaTools.resetSection(section)
                        else {
                            for (const section of ["essential", "crop", "colors", "geometry"]) MediaTools.resetSection(section)
                            MediaTools.enableFilter("invert", false)
                        }
                    }
                }
                Column {
                    visible: settingsPopup.page === 0
                    width: parent.width
                    Toggle { text: qsTr("Show Subtitle Timeline on Seekbar"); checked: MediaTools.timelineVisible; onToggled: enabled => MediaTools.timelineVisible = enabled }
                    Toggle { text: qsTr("Show Statistics"); checked: MediaTools.statisticsVisible; onToggled: enabled => MediaTools.statisticsVisible = enabled }
                    Toggle { text: qsTr("Show Audio Waveform"); checked: MediaTools.waveformVisible; onToggled: enabled => MediaTools.waveformVisible = enabled }
                    Label { x: PlayerStyle.px(20); width: parent.width - PlayerStyle.px(40); text: MediaTools.waveformVisible ? MediaAnalysis.waveformStatus : MediaAnalysis.previewStatus; font.pixelSize: PlayerStyle.px(12); color: PlayerStyle.sectionForeground }
                    Toggle { text: qsTr("Reverse"); checked: Player.rate < 0; available: Player.rewindable; onToggled: enabled => { if (enabled !== (Player.rate < 0)) Player.reverse() } }
                    Label { x: PlayerStyle.px(20); width: parent.width - PlayerStyle.px(40); visible: !Player.rewindable; text: qsTr("Reverse is unavailable for this input."); color: PlayerStyle.sectionForeground }
                    Section { text: qsTr("Sleep Timer") }
                    RowLayout {
                        x: PlayerStyle.px(20); width: parent.width - PlayerStyle.px(40)
                        PlayerSettingsChoice { id: sleep; Layout.fillWidth: true; label: qsTr("Sleep timer"); model: [qsTr("Off"), qsTr("1 minute"), qsTr("15 minutes"), qsTr("30 minutes"), qsTr("60 minutes"), qsTr("90 minutes")]; onActivated: MediaTools.armSleep([0,1,15,30,60,90][currentIndex]) }
                        Button { text: qsTr("Cancel"); enabled: MediaTools.sleepMinutes > 0; onClicked: { MediaTools.cancelSleep(); sleep.currentIndex = 0 } }
                    }
                    Label { x: PlayerStyle.px(20); width: parent.width - PlayerStyle.px(40); text: MediaTools.sleepStatus; font.pixelSize: PlayerStyle.px(12); color: PlayerStyle.sectionForeground }
                    Section { text: qsTr("Speed") }
                    RowLayout {
                        x: PlayerStyle.px(20); width: parent.width - PlayerStyle.px(40)
                        PlayerSettingsChoice { Layout.fillWidth: true; label: qsTr("Playback speed"); model: ["0.25×", "0.5×", "0.75×", "1×", "1.25×", "1.5×", "1.75×", "2×"]; currentIndex: [0.25,0.5,0.75,1,1.25,1.5,1.75,2].indexOf(Math.abs(Player.rate)); enabled: Player.ratechangable; onActivated: Player.rate = [0.25,0.5,0.75,1,1.25,1.5,1.75,2][currentIndex] }
                        Label { text: Number(Player.rate).toFixed(2) + "×" }
                    }
                    ChoiceRow { text: qsTr("Audio Visualizer"); choices: Player.audioVisualization }
                    Section { text: qsTr("Metadata") }
                    Label { x: PlayerStyle.px(20); width: parent.width - PlayerStyle.px(40); text: qsTr("Title: %1\nArtist: %2\nAlbum: %3\nLocation: %4").arg(Player.title).arg(Player.artist).arg(Player.album).arg(Player.url); font.pixelSize: PlayerStyle.px(12) }
                }
                Column {
                    visible: settingsPopup.page === 1
                    width: parent.width
                    RowLayout {
                        x: PlayerStyle.px(20); width: parent.width - PlayerStyle.px(40); height: PlayerStyle.px(53)
                        Label { text: qsTr("Flip"); Layout.fillWidth: true }
                        PlayerSettingsChoice {
                            Layout.preferredWidth: PlayerStyle.px(138)
                            label: qsTr("Flip video")
                            model: [qsTr("None"), qsTr("Horizontal"), qsTr("Vertical")]
                            currentIndex: { const revision = settingsPopup.settingsRevision; return !MediaTools.filterEnabled("transform") ? 0 : ["", "hflip", "vflip"].indexOf(String(MediaTools.value("transform-type"))) }
                            displayText: currentIndex < 0 ? qsTr("Custom transform") : currentText
                            onActivated: { if (currentIndex === 0) MediaTools.enableFilter("transform",false); else if (MediaTools.setValue("transform-type",["", "hflip", "vflip"][currentIndex])) MediaTools.enableFilter("transform",true) }
                        }
                    }
                    RowLayout {
                        x: PlayerStyle.px(20); width: parent.width - PlayerStyle.px(40); height: PlayerStyle.px(53)
                        Label { text: qsTr("Rotate"); Layout.fillWidth: true }
                        T.TextField {
                            Layout.preferredWidth: PlayerStyle.px(138); implicitHeight: PlayerStyle.px(36)
                            text: { const revision = settingsPopup.settingsRevision; return (MediaTools.filterEnabled("rotate") ? Number(MediaTools.value("rotate-angle")) : 0).toFixed(1) }
                            color: PlayerStyle.trackForeground; font.family: PlayerStyle.fontFamily; padding: PlayerStyle.px(8); selectByMouse: true
                            Accessible.name: qsTr("Video rotation in degrees")
                            onEditingFinished: { const angle = Number(text); if (isFinite(angle) && MediaTools.setValue("rotate-angle",angle)) MediaTools.enableFilter("rotate",angle !== 0) }
                            background: Rectangle { color: PlayerStyle.timeline; radius: PlayerStyle.px(4); border.width: parent.activeFocus ? 1 : 0; border.color: PlayerStyle.accent }
                        }
                    }
                    ChoiceRow { text: qsTr("Zoom"); choices: Player.zoom }
                    RowLayout { x: PlayerStyle.px(20); width: parent.width - PlayerStyle.px(40); height: PlayerStyle.px(53); Label { text: qsTr("HDR"); Layout.fillWidth: true } Label { text: MediaTools.videoInfo.hdr; color: PlayerStyle.sectionForeground; font.pixelSize: PlayerStyle.px(12); Layout.preferredWidth: PlayerStyle.px(138) } }
                    RowLayout { x: PlayerStyle.px(20); width: parent.width - PlayerStyle.px(40); height: PlayerStyle.px(53); Label { text: qsTr("Resolution"); Layout.fillWidth: true } Label { text: MediaTools.videoInfo.resolution; color: PlayerStyle.sectionForeground; Layout.preferredWidth: PlayerStyle.px(138) } }
                    ChoiceRow { text: qsTr("Aspect Ratio"); choices: Player.aspectRatio }
                    ChoiceRow { text: qsTr("Crop"); choices: Player.crop }
                    ChoiceRow { text: qsTr("Deinterlace"); choices: Player.deinterlace }
                    ChoiceRow { text: qsTr("Deinterlace Mode"); choices: Player.deinterlaceMode }
                    Label { x: PlayerStyle.px(20); width: parent.width - PlayerStyle.px(40); text: qsTr("HDR and resolution describe the source. Output follows VLC's renderer and display; forced conversion and display-mode changes are unavailable here."); font.pixelSize: PlayerStyle.px(12); color: PlayerStyle.sectionForeground }
                    Section { text: qsTr("Filters") }
                    Effect { title: qsTr("Essential"); module: "adjust"; section: "essential" }
                    Effect { title: qsTr("Crop"); module: ""; section: "crop" }
                    Effect { title: qsTr("Colors"); module: "colorthres"; section: "colors" }
                    Effect { title: qsTr("Geometry"); module: "transform"; section: "geometry" }
                    Toggle { text: qsTr("Negate Colors"); checked: settingsPopup.filterEnabled("invert"); onToggled: enabled => MediaTools.enableFilter("invert", enabled) }
                }
                Column {
                    visible: settingsPopup.page === 2
                    width: parent.width
                    ChoiceRow { text: qsTr("Audio Track"); choices: Player.audioTracks }
                    LanguageRow { }
                    ChoiceRow { text: qsTr("Stereo Mode"); choices: Player.audioStereoMode }
                    Section { text: qsTr("Synchronization") }
                    TimingRow { text: qsTr("Audio Track Delay"); unit: "s"; value: Player.audioDelayMS / 1000; onEdited: number => Player.audioDelayMS = Math.round(Math.max(-600,Math.min(600,number))*1000) }
                    Section { text: qsTr("Filters") }
                    Effect { title: qsTr("Equalizer"); module: "equalizer"; section: "equalizer" }
                    Effect { title: qsTr("Compressor"); module: "compressor"; section: "compressor" }
                    Effect { title: qsTr("Spatializer"); module: "spatializer"; section: "spatializer" }
                    Effect { title: qsTr("Stereo Widener"); module: "stereo_widen"; section: "stereo_widen" }
                    Effect { title: qsTr("Adjust Pitch"); module: "scaletempo_pitch"; section: "pitch" }
                }
                Column {
                    visible: settingsPopup.page === 3
                    width: parent.width
                    Column {
                        width: parent.width
                        topPadding: PlayerStyle.px(10)
                        bottomPadding: PlayerStyle.px(10)
                        spacing: PlayerStyle.px(5)
                        ChoiceRow { text: qsTr("Subtitle Track"); choices: Player.subtitleTracks }
                        LanguageRow { subtitle: true }
                    }
                    Section { text: qsTr("Synchronization") }
                    Column {
                        width: parent.width
                        topPadding: PlayerStyle.px(10)
                        bottomPadding: PlayerStyle.px(15)
                        TimingRow { text: qsTr("Subtitle Track Delay"); editorName: "subtitleDelayEditor"; unit: "s"; value: Player.subtitleDelayMS / 1000; onEdited: number => Player.subtitleDelayMS = Math.round(Math.max(-600,Math.min(600,number))*1000) }
                        TimingRow { text: qsTr("Subtitle Speed"); enabled: MediaTools.subtitleFPSSupported; opacity: enabled ? 1 : 0.5; rangeLabels: false; unit: "fps"; minimum: 0; maximum: 120; value: Player.subtitleFPS; onEdited: number => { if (number >= 0 && number <= 1000) Player.subtitleFPS = number } }
                        Label { width: parent.width; visible: !MediaTools.subtitleFPSSupported; text: qsTr("FPS correction applies to added SRT, ASS and SSA tracks. This track uses its original timing."); font.pixelSize: PlayerStyle.px(12); color: PlayerStyle.sectionForeground }
                        TimingRow { text: qsTr("Subtitle Duration Factor"); rangeLabels: false; minimum: 0; maximum: 20; value: { const revision = settingsPopup.settingsRevision; return settingsPopup.filterEnabled("subsdelay") ? Number(MediaTools.value("subsdelay-factor")) : 0 } onEdited: number => { if (MediaTools.setValue("subsdelay-factor",number)) MediaTools.enableFilter("subsdelay",number > 0) } }
                    }
                    Section { text: qsTr("Appearance") }
                    Column {
                        x: PlayerStyle.px(20); width: parent.width - PlayerStyle.px(40)
                        topPadding: PlayerStyle.px(10); bottomPadding: PlayerStyle.px(10); spacing: PlayerStyle.px(5)
                        RowLayout {
                            width: parent.width; height: PlayerStyle.px(48)
                            Label { text: qsTr("Embedded Sub Format"); Layout.fillWidth: true }
                            Label { text: qsTr("Track authored"); font.pixelSize: PlayerStyle.px(12); color: PlayerStyle.sectionForeground }
                            HoverHandler { id: authoredHover }
                            T.ToolTip.visible: authoredHover.hovered
                            T.ToolTip.text: qsTr("Authored ASS styles and image subtitles retain their own formatting. Appearance controls apply where the text renderer supports them.")
                        }
                        Repeater { model: MediaTools.options("subtitle").filter(option => ["freetype-font", "freetype-color", "freetype-outline-color", "sub-margin"].indexOf(option.key) >= 0); PlayerSettingRow {
                            required property var modelData; option: modelData
                            topPadding: PlayerStyle.px(6); bottomPadding: PlayerStyle.px(6)
                            controlHeight: 36; valueWidth: 140
                        } }
                        RowLayout {
                            width: parent.width; height: PlayerStyle.px(50)
                            Label { text: qsTr("Size Values"); Layout.fillWidth: true }
                            Button { Layout.preferredWidth: PlayerStyle.px(87); text: qsTr("Relative"); checked: !settingsPopup.pixelSizes; onClicked: { settingsPopup.pixelSizes = false; MediaTools.setValue("freetype-absolute-fontsize",0) } }
                            Button { Layout.preferredWidth: PlayerStyle.px(87); text: qsTr("Pixels"); checked: settingsPopup.pixelSizes; onClicked: settingsPopup.pixelSizes = true }
                        }
                        Repeater { model: MediaTools.options("subtitle").filter(option => option.key === "freetype-outline-thickness" || option.key === "freetype-background-opacity" || (settingsPopup.pixelSizes ? option.key === "freetype-absolute-fontsize" : option.key === "sub-text-scale")); PlayerSettingRow {
                            required property var modelData
                            option: modelData.key === "sub-text-scale" || modelData.key === "freetype-absolute-fontsize" ? Object.assign({}, modelData, {label: qsTr("Font Size")}) : modelData
                            slider: true; controlHeight: 37; rangeHeight: 24; spacing: PlayerStyle.px(5)
                            valueWidth: 140
                        } }
                    }
                    Label { x: PlayerStyle.px(20); width: parent.width - PlayerStyle.px(40); text: MediaTools.timelineStatus; font.pixelSize: PlayerStyle.px(12); color: PlayerStyle.sectionForeground }
                    Section { text: qsTr("Subtitle Files") }
                    RowLayout {
                        x: PlayerStyle.px(20); width: parent.width - PlayerStyle.px(40); height: PlayerStyle.px(52)
                        Button { text: qsTr("Add File…"); Layout.fillWidth: true; onClicked: MediaTools.browseSubtitle() }
                        Button { text: qsTr("Folder / Queue…"); Layout.fillWidth: true; onClicked: settingsPopup.matchSubtitlesRequested() }
                    }
                    Button { x: PlayerStyle.px(20); width: parent.width - PlayerStyle.px(40); text: qsTr("Find Subtitles Online…"); onClicked: settingsPopup.remoteSubtitlesRequested() }
                    Section { text: qsTr("Show Presets") }
                    Label { x: PlayerStyle.px(20); width: parent.width - PlayerStyle.px(40); text: qsTr("Global defaults → matching show folder → manual changes for this input. The most specific folder wins."); font.pixelSize: PlayerStyle.px(12); color: PlayerStyle.sectionForeground }
                    RowLayout {
                        x: PlayerStyle.px(20); width: parent.width - PlayerStyle.px(40)
                        T.TextField { id: presetName; placeholderText: qsTr("Preset name"); Layout.fillWidth: true; implicitHeight: PlayerStyle.px(32); maximumLength: 80; padding: PlayerStyle.px(6); color: PlayerStyle.trackForeground; font.family: PlayerStyle.fontFamily; Accessible.name: qsTr("Preset name"); background: Rectangle { color: PlayerStyle.timeline; radius: PlayerStyle.px(4) } }
                        Button { text: qsTr("Show Folder…"); onClicked: settingsPopup.presetFolder = MediaTools.browsePresetFolder() }
                    }
                    Label { x: PlayerStyle.px(20); width: parent.width - PlayerStyle.px(40); text: String(settingsPopup.presetFolder); font.pixelSize: PlayerStyle.px(12); elide: Text.ElideMiddle; wrapMode: Text.NoWrap }
                    Button { x: PlayerStyle.px(20); width: parent.width - PlayerStyle.px(40); text: qsTr("Save Show Preset"); onClicked: MediaTools.savePreset(presetName.text, settingsPopup.presetFolder) }
                    Button { x: PlayerStyle.px(20); width: parent.width - PlayerStyle.px(40); text: qsTr("Remove %1").arg(MediaTools.activePreset || qsTr("Preset")); enabled: MediaTools.activePreset.length > 0; onClicked: MediaTools.removePreset(MediaTools.activePreset) }
                }
                Label { x: PlayerStyle.px(20); width: parent.width - PlayerStyle.px(40); text: MediaTools.status; visible: text.length > 0; font.pixelSize: PlayerStyle.px(12); color: PlayerStyle.sectionForeground }
            }
        }
        Column {
            x: PlayerStyle.px(20)
            y: parent.height - PlayerStyle.px(104)
            width: parent.width - PlayerStyle.px(40)
            spacing: PlayerStyle.px(10)
            PlayerSettingsChoice { width: parent.width; height: PlayerStyle.px(42); label: qsTr("Show preset"); model: MediaTools.presets; displayText: MediaTools.activePreset || qsTr("Default Preset"); onActivated: { MediaTools.applyPreset(currentText); settingsPopup.pixelSizes = Number(MediaTools.value("freetype-absolute-fontsize")) > 0 } }
            Button { width: parent.width; text: qsTr("Open Advanced Settings"); onClicked: { settingsPopup.close(); DialogsProvider.extendedDialog() } }
        }
    }
}
