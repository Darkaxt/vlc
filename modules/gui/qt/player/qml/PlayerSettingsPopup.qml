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
    property bool metadataExpanded: false
    property int settingsRevision: 0
    required property Item layoutRoot
    // Materialize the declared background before the first video presentation.
    readonly property Item retainedBackdrop: background
    readonly property bool vlcToolsAvailable: Player.playbackEngine === "vlc" && !Player.engineSwitching
    readonly property string vlcToolsHint: qsTr("Requires VLC playback. Track selection and timing work with either engine.")
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
    width: Math.max(0, Math.min(PlayerStyle.px(400), layoutRoot.width - PlayerStyle.px(40)))
    height: Math.max(0, Math.min(PlayerStyle.px(946), layoutRoot.height - PlayerStyle.px(134)))
    padding: 0
    focus: true
    closePolicy: T.Popup.CloseOnEscape | T.Popup.CloseOnPressOutsideParent
    background: LibraryGlass { backgroundSource: settingsPopup.layoutRoot; active: settingsPopup.opened; radius: PlayerStyle.px(10) }
    function showPage(index) { page = index; expanded = ""; open() }
    onOpened: pixelSizes = Number(MediaTools.value("freetype-absolute-fontsize")) > 0
    onPageChanged: body.contentY = 0

    component Label: Text {
        color: PlayerStyle.sectionForeground
        font.family: PlayerStyle.fontFamily
        font.pixelSize: PlayerStyle.px(14)
        textFormat: Text.PlainText
        wrapMode: Text.Wrap
    }
    component Button: T.Button {
        id: button
        property bool segmented: false
        property bool plain: false
        implicitWidth: Math.max(PlayerStyle.px(64), implicitContentWidth + leftPadding + rightPadding)
        implicitHeight: PlayerStyle.px(32)
        padding: PlayerStyle.px(8)
        activeFocusOnTab: true
        hoverEnabled: true
        Accessible.name: text
        Accessible.onPressAction: clicked()
        contentItem: Label {
            text: button.text
            color: button.checked ? (!button.segmented && Player.playbackEngine==="mpv" ? PlayerStyle.accentForeground : PlayerStyle.accent) : PlayerStyle.sectionForeground
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
            elide: Text.ElideRight
            wrapMode: Text.NoWrap
        }
        background: Rectangle {
            color: button.checked ? (!button.segmented && Player.playbackEngine==="mpv" ? PlayerStyle.accent : PlayerStyle.accentWell) : button.hovered ? PlayerStyle.hover : button.plain ? "transparent" : button.segmented ? PlayerStyle.chrome : PlayerStyle.timeline
            radius: PlayerStyle.px(4)
            border.color: PlayerStyle.accent
            border.width: button.visualFocus ? PlayerStyle.px(2) : 0
        }
    }
    component Divider: Item {
        width: body.width
        height: PlayerStyle.px(1)
        Rectangle { anchors.fill: parent; color: PlayerStyle.foreground; opacity: 0.12 }
    }
    component Section: Item {
        property string text
        width: body.width
        height: PlayerStyle.px(60)
        Label { x: PlayerStyle.px(24); anchors.verticalCenter: parent.verticalCenter; text: parent.text; color: PlayerStyle.trackForeground; font.pixelSize: PlayerStyle.px(16) }
    }
    component Toggle: RowLayout {
        property string text
        property bool checked: false
        property bool available: true
        property bool requiresVlc: false
        property string unavailableReason: ""
        readonly property string displayLabel: text
        signal toggled(bool enabled)
        width: body.width - PlayerStyle.px(40)
        height: PlayerStyle.px(52)
        x: PlayerStyle.px(20)
        Label { Layout.fillWidth: true; text: parent.displayLabel; opacity: parent.available ? 1 : 0.5 }
        PlayerSettingsSwitch {
            Layout.preferredWidth: PlayerStyle.px(68)
            value: parent.checked
            enabled: parent.available && !Player.engineSwitching && (!parent.requiresVlc || Player.playbackEngine === "vlc")
            Accessible.name: parent.displayLabel
            Accessible.description: parent.unavailableReason.length ? parent.unavailableReason : value ? qsTr("On") : qsTr("Off")
            onClicked: parent.toggled(!parent.checked)
        }
        HoverHandler { id: reasonHover }
        T.ToolTip.visible: reasonHover.hovered && (unavailableReason.length>0 || (requiresVlc && !settingsPopup.vlcToolsAvailable))
        T.ToolTip.text: unavailableReason.length ? unavailableReason : settingsPopup.vlcToolsHint
    }
    component Effect: Column {
        id: effect
        property string title
        property string module
        property string section
        property var excludedKeys: []
        property bool showToggle: true
        property bool showDivider: true
        width: body.width
        topPadding: 0
        bottomPadding: PlayerStyle.px(20)
        spacing: PlayerStyle.px(10)
        Divider { visible: effect.showDivider }
        RowLayout {
            x: PlayerStyle.px(20)
            width: parent.width - PlayerStyle.px(40)
            visible: effect.title.length>0
            height: visible ? PlayerStyle.px(37) : 0
            Label { Layout.fillWidth: true; Layout.leftMargin: PlayerStyle.px(4); text: effect.title }
            PlayerSettingsSwitch {
                visible: effect.showToggle && effect.module.length > 0
                enabled: Player.playbackEngine === "vlc" && !Player.engineSwitching
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
            Accessible.name: (effect.title.length ? effect.title : qsTr("Equalizer")) + ": " + text
            contentItem: Label { text: expandEffect.text; verticalAlignment: Text.AlignVCenter; wrapMode: Text.NoWrap; elide: Text.ElideRight }
            IconImage {
                smooth: false
                anchors.right: parent.right; anchors.rightMargin: PlayerStyle.px(10); anchors.verticalCenter: parent.verticalCenter
                width: PlayerStyle.px(24); height: width
                sourceSize: Qt.size(width, height)
                source: "qrc:/redesign/icons/chevron-right.svg"
                color: PlayerStyle.trackForeground
                rotation: settingsPopup.expanded === effect.section ? 90 : 0
            }
            onClicked: settingsPopup.expanded = settingsPopup.expanded === effect.section ? "" : effect.section
        }
        Column {
            x: PlayerStyle.px(20)
            width: parent.width - PlayerStyle.px(40)
            visible: settingsPopup.expanded === effect.section
            Repeater {
                model: { const revision=settingsPopup.settingsRevision; return MediaTools.options(effect.section).filter(option => effect.excludedKeys.indexOf(option.key)<0) }
                PlayerSettingRow {
                    required property var modelData
                    option: modelData
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
        property bool requiresVlc: true
        property bool referenceControl: true
        property bool fullWidth: false
        property var optionIcons: ({})
        readonly property string displayLabel: text
        width: body.width - PlayerStyle.px(40)
        height: PlayerStyle.px(referenceControl ? 68 : 48)
        x: PlayerStyle.px(20)
        Label { visible: !choiceRow.fullWidth; Layout.fillWidth: true; text: parent.displayLabel }
        PlayerSettingsChoice {
            id: trackChoice
            objectName: "playerChoice_" + choiceRow.text
            Layout.fillWidth: choiceRow.fullWidth
            Layout.preferredWidth: PlayerStyle.px(choiceRow.referenceControl ? 220 : 140)
            Layout.preferredHeight: PlayerStyle.px(choiceRow.referenceControl ? 48 : 32)
            outlined: choiceRow.referenceControl
            label: parent.displayLabel
            enabled: !Player.engineSwitching && (!choiceRow.requiresVlc || Player.playbackEngine === "vlc")
            model: parent.choices
            textRole: "display"
            valueRole: "value"
            optionIcons: choiceRow.optionIcons
            displayText: currentIndex < 0 ? qsTr("None") : currentText
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
        HoverHandler { id: choiceHover }
        T.ToolTip.visible: choiceHover.hovered && choiceRow.requiresVlc && !settingsPopup.vlcToolsAvailable
        T.ToolTip.text: settingsPopup.vlcToolsHint
    }
    component ReadoutRow: RowLayout {
        property string text
        property string value
        property string hint: ""
        width: body.width-PlayerStyle.px(40); height: PlayerStyle.px(68); x: PlayerStyle.px(20)
        Label { Layout.fillWidth: true; text: parent.text }
        T.TextField {
            Layout.preferredWidth: PlayerStyle.px(220); Layout.preferredHeight: PlayerStyle.px(48)
            text: parent.value; readOnly: true; selectByMouse: true
            padding: PlayerStyle.px(16)
            font.family: PlayerStyle.fontFamily; font.pixelSize: PlayerStyle.px(14)
            color: PlayerStyle.foreground
            Accessible.name: parent.text; Accessible.description: parent.hint
            background: Rectangle { color: PlayerStyle.chrome; radius: PlayerStyle.px(4); border.color: PlayerStyle.timeline; border.width: PlayerStyle.px(2) }
        }
        HoverHandler { id: readoutHover }
        T.ToolTip.visible: readoutHover.hovered && hint.length>0
        T.ToolTip.text: value+"\n"+hint
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
        property string hint: ""
        property bool available: true
        opacity: available ? 1 : 0.5
        signal edited(real number)
        x: PlayerStyle.px(20)
        width: body.width - PlayerStyle.px(40)
        height: PlayerStyle.px(rangeLabels ? 115 : 90)
        RowLayout {
            width: parent.width; height: PlayerStyle.px(56)
            Label { text: timing.text; Layout.fillWidth: true }
            T.TextField {
                objectName: timing.editorName
                enabled: timing.available
                Layout.preferredWidth: PlayerStyle.px(140); implicitHeight: PlayerStyle.px(36)
                text: Number(timing.value).toFixed(3) + (timing.unit.length ? " " + timing.unit : "")
                color: PlayerStyle.foreground; font.family: PlayerStyle.fontFamily; font.pixelSize: PlayerStyle.px(14)
                padding: PlayerStyle.px(12); selectByMouse: true
                Accessible.name: timing.text
                onEditingFinished: { const number = Number(text.replace(timing.unit, "").trim()); if (isFinite(number)) timing.edited(number) }
                background: Rectangle { color: PlayerStyle.timeline; radius: PlayerStyle.px(6); border.width: PlayerStyle.px(2); border.color: parent.activeFocus ? PlayerStyle.accent : PlayerStyle.chrome }
            }
        }
        Item { width: 1; height: PlayerStyle.px(5) }
        HoverHandler { id: timingHover }
        T.ToolTip.visible: timingHover.hovered && timing.hint.length>0
        T.ToolTip.text: timing.hint
        T.Slider {
            id: timeSlider
            enabled: timing.available
            width: parent.width; height: PlayerStyle.px(24)
            from: timing.minimum; to: timing.maximum; value: timing.value; stepSize: timing.step
            padding: 0
            activeFocusOnTab: true; Accessible.name: timing.text
            onMoved: timing.edited(value)
            background: Rectangle {
                y: (timeSlider.height-height)/2; width: timeSlider.availableWidth; height: PlayerStyle.px(16); radius: PlayerStyle.px(6); color: PlayerStyle.timeline
                Rectangle {
                    readonly property real origin: timing.minimum<0 && timing.maximum>0 ? -timing.minimum/(timing.maximum-timing.minimum) : 0
                    x: parent.width*Math.min(origin,timeSlider.position)
                    width: parent.width*Math.abs(timeSlider.position-origin)
                    height: parent.height; radius: parent.radius; color: PlayerStyle.accentWell
                }
            }
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
        width: body.width - PlayerStyle.px(40); height: PlayerStyle.px(62); x: PlayerStyle.px(20)
        Label { Layout.fillWidth: true; text: parent.subtitle ? qsTr("Subtitle Language") : qsTr("Audio Language") }
        PlayerSettingsChoice {
            id: languageChoice
            Layout.preferredWidth: PlayerStyle.px(140)
            Layout.preferredHeight: PlayerStyle.px(36)
            inputStyle: true
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
            x: PlayerStyle.px(6)
            width: parent.width-PlayerStyle.px(12)
            height: PlayerStyle.px(50)
            spacing: PlayerStyle.px(1)
            Repeater {
                model: [qsTr("Playback"), qsTr("Video"), qsTr("Audio"), qsTr("Subtitles")]
                T.Button {
                    id: tabButton
                    objectName: "playerSettingsTab_"+index
                    required property int index
                    required property string modelData
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    Layout.preferredWidth: PlayerStyle.px(index===0 || index===3 ? 107.5 : 85)
                    padding: PlayerStyle.px(4)
                    activeFocusOnTab: true
                    Accessible.name: modelData
                    Accessible.role: Accessible.PageTab
                    Accessible.onPressAction: clicked()
                    onClicked: { settingsPopup.page = index; settingsPopup.expanded = "" }
                    contentItem: RowLayout {
                        spacing: PlayerStyle.px(4)
                        Item {
                            Layout.preferredWidth: PlayerStyle.px(20); Layout.preferredHeight: PlayerStyle.px(20)
                            readonly property string artwork: "qrc:/redesign/icons/tab-"+["playback","video","audio","subtitles"][tabButton.index]+".svg"
                            Image {
                                objectName: tabButton.index===0 ? "playerPlaybackTabIcon" : "playerTabIcon_"+tabButton.index
                                visible: settingsPopup.page===tabButton.index
                                anchors.fill: parent; smooth: false
                                source: PlayerStyle.themedIcon(parent.artwork); sourceSize: Qt.size(width,height)
                            }
                            IconImage {
                                objectName: "playerTabNeutral_"+tabButton.index
                                visible: settingsPopup.page!==tabButton.index
                                anchors.fill: parent; smooth: false
                                source: parent.artwork; sourceSize: Qt.size(width,height)
                                color: PlayerStyle.dark ? "#404040" : PlayerStyle.sectionForeground
                            }
                        }
                        Label { text: parent.parent.modelData; font.pixelSize: PlayerStyle.px(14); color: settingsPopup.page===parent.parent.index ? PlayerStyle.foreground : PlayerStyle.sectionForeground; Layout.fillWidth: true; verticalAlignment: Text.AlignVCenter; wrapMode: Text.NoWrap; elide: Text.ElideRight }
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
            height: Math.max(0, parent.height - y - (settingsPopup.page===0 ? 0 : PlayerStyle.px(126)))
            contentWidth: width
            contentHeight: pages.implicitHeight
            clip: true
            boundsBehavior: Flickable.StopAtBounds
            Column {
                id: pages
                width: parent.width
                Column {
                    visible: settingsPopup.page === 0
                    width: parent.width
                    topPadding: PlayerStyle.px(10)
                    Toggle { text: qsTr("Show Subtitle Timeline on Seekbar"); checked: MediaTools.timelineVisible; onToggled: enabled => MediaTools.timelineVisible = enabled }
                    Toggle { text: qsTr("Show Statistics"); requiresVlc: true; checked: MediaTools.statisticsVisible; onToggled: enabled => MediaTools.statisticsVisible = enabled }
                    Toggle { text: qsTr("Reverse"); checked: Player.rate < 0; available: Player.rewindable; unavailableReason: available ? "" : qsTr("Reverse is unavailable for this input."); onToggled: enabled => { if (enabled !== (Player.rate < 0)) Player.reverse() } }
                    RowLayout {
                        x: PlayerStyle.px(20); width: parent.width - PlayerStyle.px(40); height: PlayerStyle.px(68)
                        Label { text: qsTr("Sleep Timer"); Layout.fillWidth: true }
                        PlayerSettingsChoice {
                            id: sleep
                            Layout.preferredWidth: PlayerStyle.px(220); Layout.preferredHeight: PlayerStyle.px(48)
                            outlined: true
                            label: qsTr("Sleep timer")
                            hoverEnabled: true
                            Accessible.description: MediaTools.sleepStatus
                            model: [qsTr("Off"), qsTr("1 minute"), qsTr("15 minutes"), qsTr("30 minutes"), qsTr("60 minutes"), qsTr("90 minutes")]
                            currentIndex: [0,1,15,30,60,90].indexOf(MediaTools.sleepMinutes)
                            displayText: MediaTools.sleepMinutes>0 ? qsTr("%1 minutes").arg(MediaTools.sleepMinutes) : qsTr("Off")
                            onActivated: if(currentIndex===0)MediaTools.cancelSleep();else MediaTools.armSleep([0,1,15,30,60,90][currentIndex])
                            T.ToolTip.visible: hovered && MediaTools.sleepMinutes>0
                            T.ToolTip.text: MediaTools.sleepStatus
                        }
                    }
                    RowLayout {
                        x: PlayerStyle.px(20); width: parent.width-PlayerStyle.px(40); height: PlayerStyle.px(68)
                        Label { text: qsTr("Audio Visualizer"); Layout.fillWidth: true }
                        PlayerSettingsChoice {
                            objectName: "seekbarVisualizerChoice"
                            Layout.preferredWidth: PlayerStyle.px(220); Layout.preferredHeight: PlayerStyle.px(48)
                            outlined: true
                            label: qsTr("Audio visualizer in progress bar")
                            enabled: MediaAnalysis.visualizer.available && !Player.engineSwitching
                            textRole: "text"; valueRole: "value"
                            model: [{text:qsTr("Disabled"),value:""}, {text:qsTr("Spectrometer"),value:"spectrometer"},
                                    {text:qsTr("Scope"),value:"scope"}, {text:qsTr("Spectrum"),value:"spectrum"},
                                    {text:qsTr("Waveform"),value:"waveform"}]
                            currentIndex: ["","spectrometer","scope","spectrum","waveform"].indexOf(MediaAnalysis.visualizer.mode)
                            optionIcons: ({spectrometer:"visualizer-spectrometer", scope:"visualizer-scope", spectrum:"visualizer-spectrum", waveform:"visualizer-waveform"})
                            onActivated: MediaAnalysis.visualizer.mode = currentValue
                            Accessible.description: MediaAnalysis.visualizer.status
                        }
                    }
                    Text {
                        x: PlayerStyle.px(20); width: parent.width-PlayerStyle.px(40)
                        visible: text.length>0
                        text: MediaAnalysis.visualizer.status
                        font.family: PlayerStyle.fontFamily; font.pixelSize: PlayerStyle.px(12)
                        color: PlayerStyle.sectionForeground; wrapMode: Text.Wrap
                    }
                    Item { width: 1; height: PlayerStyle.px(8) }
                    RowLayout {
                        x: PlayerStyle.px(20); width: parent.width - PlayerStyle.px(40); height: PlayerStyle.px(52)
                        Label { text: qsTr("Speed"); Layout.fillWidth: true }
                        T.TextField {
                            Layout.preferredWidth: PlayerStyle.px(140); Layout.preferredHeight: PlayerStyle.px(32)
                            padding: PlayerStyle.px(10)
                            text: (Math.round(Math.abs(Player.rate)*100)/100)+"x"
                            selectByMouse: true
                            enabled: Player.ratechangable && !Player.engineSwitching
                            color: PlayerStyle.trackForeground; font.family: PlayerStyle.fontFamily; font.pixelSize: PlayerStyle.px(14)
                            Accessible.name: qsTr("Playback speed value")
                            onEditingFinished: {
                                const value=Number(text.replace(/[x×]/g,""))
                                if(isFinite(value)&&value>0)Player.rate=(Player.rate<0?-1:1)*value
                                text=Qt.binding(()=>(Math.round(Math.abs(Player.rate)*100)/100)+"x")
                            }
                            background: Rectangle { color: PlayerStyle.timeline; radius: PlayerStyle.px(6); border.color: PlayerStyle.accent; border.width: parent.activeFocus ? PlayerStyle.px(1) : 0 }
                        }
                    }
                    T.Slider {
                        id: speedSlider
                        x: PlayerStyle.px(20); width: parent.width-PlayerStyle.px(40); height: PlayerStyle.px(32)
                        from: 0.25; to: 2; stepSize: 0.01; padding: 0
                        enabled: Player.ratechangable && !Player.engineSwitching
                        Accessible.name: qsTr("Playback speed")
                        Accessible.description: qsTr("%1 times").arg(Math.abs(Player.rate))
                        Binding on value { when: !speedSlider.pressed; value: Math.max(0.25,Math.min(2,Math.abs(Player.rate))); restoreMode: Binding.RestoreNone }
                        onMoved: Player.rate=(Player.rate<0?-1:1)*value
                        background: Rectangle {
                            y: (speedSlider.height-height)/2; width: speedSlider.width; height: PlayerStyle.px(15); radius: PlayerStyle.px(6); color: PlayerStyle.timeline
                            Rectangle { width: parent.width*speedSlider.visualPosition; height: parent.height; radius: parent.radius; color: PlayerStyle.accentWell }
                            Repeater { model: 8; Rectangle { required property int index; x: (parent.width-PlayerStyle.px(4))*index/7; y: PlayerStyle.px(4); width: PlayerStyle.px(2); height: PlayerStyle.px(7); color: PlayerStyle.foreground; opacity: 0.18 } }
                        }
                        handle: Rectangle { x: speedSlider.visualPosition*(speedSlider.availableWidth-width); y: (speedSlider.height-height)/2; width: PlayerStyle.px(8); height: PlayerStyle.px(24); radius: PlayerStyle.px(4); color: PlayerStyle.accent }
                    }
                    Item {
                        x: PlayerStyle.px(20); width: parent.width-PlayerStyle.px(40); height: PlayerStyle.px(32)
                        Repeater {
                            model: [0.25,0.5,0.75,1,1.25,1.5,1.75,2]
                            Label {
                                required property int index
                                required property var modelData
                                x: Math.max(0,Math.min(parent.width-width,PlayerStyle.px(4)+(parent.width-PlayerStyle.px(8))*index/7-width/2))
                                text: modelData; font.pixelSize: PlayerStyle.px(12); color: PlayerStyle.sectionForeground
                            }
                        }
                    }
                    Section { text: qsTr("Playback engine") }
                    RowLayout {
                        x: PlayerStyle.px(20); width: parent.width-PlayerStyle.px(40); height: PlayerStyle.px(48)
                        Button { Layout.fillWidth: true; text: "VLC"; checked: Player.playbackEngine==="vlc"; enabled: !Player.engineSwitching; onClicked: Player.switchPlaybackEngine("vlc") }
                        Button { Layout.fillWidth: true; text: "MPV"; checked: Player.playbackEngine==="mpv"; enabled: !Player.engineSwitching; onClicked: Player.switchPlaybackEngine("mpv") }
                    }
                    Label { visible: Player.engineSwitching; x: PlayerStyle.px(20); width: parent.width-PlayerStyle.px(40); text: qsTr("Switching engines… Playback will resume at the same position."); font.pixelSize: PlayerStyle.px(12); color: PlayerStyle.sectionForeground }
                    Toggle { text: qsTr("Show Audio Waveform"); checked: MediaTools.waveformVisible; onToggled: enabled => MediaTools.waveformVisible=enabled }
                    Label { x: PlayerStyle.px(20); width: parent.width-PlayerStyle.px(40); text: MediaTools.waveformVisible ? MediaAnalysis.waveformStatus : MediaAnalysis.previewStatus; visible: text.length>0; font.pixelSize: PlayerStyle.px(12); color: PlayerStyle.sectionForeground }
                    Button { x: PlayerStyle.px(20); width: parent.width-PlayerStyle.px(40); text: qsTr("Media Information"); onClicked: settingsPopup.metadataExpanded=!settingsPopup.metadataExpanded }
                    Label { visible: settingsPopup.metadataExpanded; x: PlayerStyle.px(20); width: parent.width-PlayerStyle.px(40); text: qsTr("Title: %1\nArtist: %2\nAlbum: %3\nLocation: %4").arg(Player.title).arg(Player.artist).arg(Player.album).arg(Player.url); font.pixelSize: PlayerStyle.px(12) }
                }
                Column {
                    visible: settingsPopup.page === 1
                    width: parent.width
                    topPadding: PlayerStyle.px(4)
                    RowLayout {
                        x: PlayerStyle.px(20); width: parent.width - PlayerStyle.px(40); height: PlayerStyle.px(44)
                        spacing: PlayerStyle.px(2)
                        Repeater {
                            model: [qsTr("None"), qsTr("Horizontal"), qsTr("Vertical")]
                            Button {
                                required property int index
                                required property string modelData
                                Layout.fillWidth: true; Layout.preferredWidth: 0; Layout.fillHeight: true
                                text: modelData; segmented: true
                                enabled: settingsPopup.vlcToolsAvailable
                                checked: { const revision=settingsPopup.settingsRevision; return index===(!MediaTools.filterEnabled("transform") ? 0 : ["","hflip","vflip"].indexOf(String(MediaTools.value("transform-type")))) }
                                Accessible.name: qsTr("Flip video: %1").arg(modelData)
                                onClicked: { if (index===0) MediaTools.enableFilter("transform",false); else if(MediaTools.setValue("transform-type",["","hflip","vflip"][index]))MediaTools.enableFilter("transform",true) }
                            }
                        }
                        HoverHandler { id: flipHover }
                        T.ToolTip.visible: flipHover.hovered && !settingsPopup.vlcToolsAvailable
                        T.ToolTip.text: settingsPopup.vlcToolsHint
                    }
                    Item { height: PlayerStyle.px(14); width: 1 }
                    RowLayout {
                        x: PlayerStyle.px(24); width: parent.width - PlayerStyle.px(44); height: PlayerStyle.px(68)
                        Label { text: qsTr("Rotate"); Layout.fillWidth: true }
                        T.TextField {
                            Layout.preferredWidth: PlayerStyle.px(140); implicitHeight: PlayerStyle.px(36)
                            enabled: settingsPopup.vlcToolsAvailable
                            text: { const revision = settingsPopup.settingsRevision; return (MediaTools.filterEnabled("rotate") ? Number(MediaTools.value("rotate-angle")) : 0)+" deg" }
                            color: PlayerStyle.foreground; font.family: PlayerStyle.fontFamily; font.pixelSize: PlayerStyle.px(14); padding: PlayerStyle.px(12); selectByMouse: true
                            Accessible.name: qsTr("Video rotation in degrees")
                            onEditingFinished: { const angle = Number(text.replace(/deg|°/g,"").trim()); if (isFinite(angle) && MediaTools.setValue("rotate-angle",angle)) MediaTools.enableFilter("rotate",angle !== 0) }
                            background: Rectangle { color: PlayerStyle.timeline; radius: PlayerStyle.px(6); border.width: PlayerStyle.px(2); border.color: parent.activeFocus ? PlayerStyle.accent : PlayerStyle.chrome }
                        }
                    }
                    ChoiceRow { text: qsTr("Zoom"); choices: Player.zoom }
                    ReadoutRow { text: qsTr("HDR"); value: MediaTools.videoInfo.hdr; hint: Player.playbackEngine==="mpv" ? qsTr("Source transfer and current SDR output. MPV retains Dolby Vision color processing.") : qsTr("Source transfer. Output follows VLC's renderer and display.") }
                    ReadoutRow { text: qsTr("Resolution"); value: MediaTools.videoInfo.resolution; hint: qsTr("Source video dimensions.") }
                    ChoiceRow { text: qsTr("Aspect Ratio"); choices: Player.aspectRatio }
                    ChoiceRow { text: qsTr("Crop"); choices: Player.crop }
                    RowLayout {
                        x: PlayerStyle.px(20); width: parent.width-PlayerStyle.px(40); height: PlayerStyle.px(68)
                        Label { text: qsTr("Render"); Layout.fillWidth: true }
                        Button {
                            id: rendererButton
                            Layout.preferredWidth: PlayerStyle.px(220); Layout.preferredHeight: PlayerStyle.px(48)
                            enabled: settingsPopup.vlcToolsAvailable
                            text: Player.rendererManager.useRenderer ? qsTr("External renderer") : qsTr("Local")
                            rightPadding: PlayerStyle.px(42); leftPadding: PlayerStyle.px(16)
                            contentItem: Label { text: rendererButton.text; color: PlayerStyle.foreground; verticalAlignment: Text.AlignVCenter }
                            background: Rectangle { color: PlayerStyle.chrome; radius: PlayerStyle.px(4); border.width: PlayerStyle.px(2); border.color: rendererButton.visualFocus ? PlayerStyle.accent : PlayerStyle.timeline }
                            IconImage { anchors.right: parent.right; anchors.rightMargin: PlayerStyle.px(10); anchors.verticalCenter: parent.verticalCenter; width: PlayerStyle.px(24); height: width; sourceSize: Qt.size(width,height); smooth: false; source: "qrc:/redesign/icons/chevron-down.svg"; color: PlayerStyle.foreground }
                            onClicked: rendererMenu.popup(mapToGlobal(0,height),false)
                            QmlRendererMenu { id: rendererMenu; ctx: MainCtx }
                        }
                    }
                    Divider { }
                    Section { text: qsTr("Filters") }
                    Effect { title: qsTr("Essential"); module: "adjust"; section: "essential"; showDivider: false; showToggle: false }
                    Effect { title: qsTr("Crop"); module: ""; section: "crop" }
                    Effect { title: qsTr("Colors"); module: "colorthres"; section: "colors" }
                    Effect { title: qsTr("Geometry"); module: "transform"; section: "geometry" }
                    Toggle { text: qsTr("Negate Colors"); requiresVlc: true; checked: settingsPopup.filterEnabled("invert"); onToggled: enabled => MediaTools.enableFilter("invert", enabled) }
                    ChoiceRow { text: qsTr("Deinterlace"); choices: Player.deinterlace }
                    ChoiceRow { text: qsTr("Deinterlace Mode"); choices: Player.deinterlaceMode }
                }
                Column {
                    visible: settingsPopup.page === 2
                    width: parent.width
                    LanguageRow { }
                    Item { height: PlayerStyle.px(16); width: 1 }
                    Label { x: PlayerStyle.px(24); text: qsTr("Stereo Mode"); height: PlayerStyle.px(32) }
                    ChoiceRow { text: qsTr("Stereo Mode"); choices: Player.audioStereoMode; fullWidth: true }
                    Divider { }
                    Section { text: qsTr("Synchronization") }
                    TimingRow { text: qsTr("Audio Track Delay"); editorName: "audioDelayEditor"; unit: "s"; value: Player.audioDelayMS / 1000; onEdited: number => Player.audioDelayMS = Math.round(Math.max(-600,Math.min(600,number))*1000) }
                    Divider { }
                    Section { text: qsTr("Filters") }
                    Label { x: PlayerStyle.px(24); text: qsTr("Equalizer"); height: PlayerStyle.px(32) }
                    Repeater {
                        model: { const revision=settingsPopup.settingsRevision; return MediaTools.options("equalizer").filter(option=>option.key==="equalizer-preset") }
                        PlayerSettingRow { required property var modelData; option: modelData; fullWidthChoice: true; filterChoice: true; x: PlayerStyle.px(20); width: body.width-PlayerStyle.px(40); controlHeight: 48; valueWidth: 360; topPadding: 0; bottomPadding: PlayerStyle.px(10) }
                    }
                    Effect { title: ""; module: "equalizer"; section: "equalizer"; showDivider: false; showToggle: false; excludedKeys: ["equalizer-preset","equalizer-2pass"] }
                    Toggle { text: qsTr("2 Pass"); requiresVlc: true; checked: { const revision=settingsPopup.settingsRevision; return Boolean(MediaTools.value("equalizer-2pass")) } onToggled: value=>MediaTools.setValue("equalizer-2pass",value) }
                    Effect { title: qsTr("Compressor"); module: "compressor"; section: "compressor" }
                    Effect { title: qsTr("Spatializer"); module: "spatializer"; section: "spatializer" }
                    Effect { title: qsTr("Stereo Widener"); module: "stereo_widen"; section: "stereo_widen" }
                    Effect { title: qsTr("Adjust Pitch"); module: "scaletempo_pitch"; section: "pitch" }
                    ChoiceRow { text: qsTr("Audio Track"); requiresVlc: false; choices: Player.audioTracks }
                }
                Column {
                    visible: settingsPopup.page === 3
                    width: parent.width
                    Column {
                        width: parent.width
                        topPadding: PlayerStyle.px(10)
                        bottomPadding: PlayerStyle.px(10)
                        spacing: PlayerStyle.px(5)
                        LanguageRow { subtitle: true }
                    }
                    Divider { }
                    Section { text: qsTr("Synchronization") }
                    Column {
                        width: parent.width
                        topPadding: PlayerStyle.px(10)
                        bottomPadding: PlayerStyle.px(15)
                        TimingRow { text: qsTr("Subtitle Track Delay"); editorName: "subtitleDelayEditor"; unit: "s"; value: Player.subtitleDelayMS / 1000; onEdited: number => Player.subtitleDelayMS = Math.round(Math.max(-600,Math.min(600,number))*1000) }
                        TimingRow { text: qsTr("Subtitle Speed"); available: MediaTools.subtitleFPSSupported; rangeLabels: false; unit: "fps"; minimum: 0; maximum: 120; value: Player.subtitleFPS; hint: MediaTools.subtitleFPSSupported ? "" : qsTr("FPS correction applies to added SRT, ASS and SSA tracks. This track uses its original timing."); onEdited: number => { if (number >= 0 && number <= 1000) Player.subtitleFPS = number } }
                        TimingRow { text: qsTr("Subtitle Duration Factor"); available: settingsPopup.vlcToolsAvailable; hint: available ? "" : settingsPopup.vlcToolsHint; rangeLabels: false; minimum: 0; maximum: 20; value: { const revision = settingsPopup.settingsRevision; return settingsPopup.filterEnabled("subsdelay") ? Number(MediaTools.value("subsdelay-factor")) : 0 } onEdited: number => { if (MediaTools.setValue("subsdelay-factor",number)) MediaTools.enableFilter("subsdelay",number > 0) } }
                    }
                    Divider { }
                    Section { text: qsTr("Appearance") }
                    Column {
                        x: PlayerStyle.px(20); width: parent.width - PlayerStyle.px(40)
                        topPadding: PlayerStyle.px(10); bottomPadding: PlayerStyle.px(10); spacing: PlayerStyle.px(5)
                        RowLayout {
                            width: parent.width; height: PlayerStyle.px(48)
                            Label { text: qsTr("Embedded Sub Format"); Layout.fillWidth: true }
                            Label { text: qsTr("Track authored"); width: PlayerStyle.px(140); font.pixelSize: PlayerStyle.px(12); color: PlayerStyle.sectionForeground }
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
                            Button { Layout.preferredWidth: PlayerStyle.px(87); segmented: true; enabled: settingsPopup.vlcToolsAvailable; text: qsTr("Relative"); checked: !settingsPopup.pixelSizes; onClicked: { settingsPopup.pixelSizes = false; MediaTools.setValue("freetype-absolute-fontsize",0) } }
                            Button { Layout.preferredWidth: PlayerStyle.px(87); segmented: true; enabled: settingsPopup.vlcToolsAvailable; text: qsTr("Pixels"); checked: settingsPopup.pixelSizes; onClicked: settingsPopup.pixelSizes = true }
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
                    ChoiceRow { text: qsTr("Subtitle Track"); requiresVlc: false; choices: Player.subtitleTracks }
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
                Button {
                    visible: settingsPopup.page!==0
                    enabled: settingsPopup.vlcToolsAvailable
                    x: PlayerStyle.px(20); width: parent.width-PlayerStyle.px(40)
                    text: qsTr("Reset this page to defaults")
                    onClicked: {
                        if(settingsPopup.page===3)MediaTools.resetSection("subtitle")
                        else if(settingsPopup.page===2)for(const section of ["equalizer","compressor","spatializer","stereo_widen","pitch"])MediaTools.resetSection(section)
                        else {for(const section of ["essential","crop","colors","geometry"])MediaTools.resetSection(section);MediaTools.enableFilter("invert",false)}
                    }
                }
            }
        }
        Column {
            visible: settingsPopup.page!==0
            objectName: "mediaSettingsFooter"
            y: parent.height - PlayerStyle.px(124)
            width: parent.width
            spacing: PlayerStyle.px(10)
            Divider { }
            PlayerSettingsChoice { x: PlayerStyle.px(20); width: parent.width-PlayerStyle.px(40); height: PlayerStyle.px(42); expandUp: true; label: qsTr("Show preset"); model: MediaTools.presets; displayText: MediaTools.activePreset || qsTr("Default Preset"); onActivated: { MediaTools.applyPreset(currentText); settingsPopup.pixelSizes = Number(MediaTools.value("freetype-absolute-fontsize")) > 0 } }
            Button {
                id: advancedSettings
                x: PlayerStyle.px(20); width: parent.width-PlayerStyle.px(40); height: PlayerStyle.px(38)
                plain: true
                text: qsTr("Open Advanced Settings")
                contentItem: Item {
                    Row {
                        anchors.centerIn: parent; spacing: PlayerStyle.px(6)
                        IconImage { width: PlayerStyle.px(20); height: width; sourceSize: Qt.size(width,height); smooth: false; source: "qrc:/redesign/icons/menu-settings.svg"; color: PlayerStyle.sectionForeground }
                        Label { text: advancedSettings.text; anchors.verticalCenter: parent.verticalCenter }
                    }
                }
                onClicked: { settingsPopup.close(); DialogsProvider.extendedDialog() }
            }
        }
    }
}
