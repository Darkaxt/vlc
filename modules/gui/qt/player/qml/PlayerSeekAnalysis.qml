// SPDX-License-Identifier: GPL-2.0-or-later
import QtQuick
import QtQuick.Templates as T
import VLC.Util
import VLC.Player
import VLC.MainInterface

Item {
    id: analysis
    required property Item overlayParent
    property real hoverPosition: 0
    property real playedWidth: 0
    readonly property bool subtitleTimelineVisible: !Player.stillImagePreview && MediaTools.timelineVisible && MediaTools.cues.length > 0
    readonly property real cueControlsWidth: subtitleTimelineVisible ? PlayerStyle.px(52) : 0
    readonly property real graphWidth: Math.max(1, width - 2 * cueControlsWidth)
    anchors.fill: parent
    function positionPreview() {
        const point = analysis.mapToItem(analysis.overlayParent, cueControlsWidth + graphWidth * analysis.hoverPosition, 0)
        preview.x = Math.max(PlayerStyle.px(20), Math.min(analysis.overlayParent.width - preview.width - PlayerStyle.px(20), point.x - preview.width / 2))
        preview.y = Math.max(PlayerStyle.px(40), point.y - preview.height - PlayerStyle.px(12))
    }
    Connections {
        target: analysis.overlayParent
        function onWidthChanged() { if (hover.hovered) analysis.positionPreview() }
        function onHeightChanged() { if (hover.hovered) analysis.positionPreview() }
    }
    PlayerAnalysisStrip {
        objectName: "liveAudioVisualizerStrip"
        anchors.fill: parent
        anchors.leftMargin: analysis.cueControlsWidth
        anchors.rightMargin: analysis.cueControlsWidth
        visible: MediaAnalysis.visualizer.active
        renderMode: MediaAnalysis.visualizer.mode
        samples: MediaAnalysis.visualizer.samples
        color: PlayerStyle.accent
        playedWidth: analysis.playedWidth - analysis.cueControlsWidth
        // Paint only: slider pointer, keyboard and handle ownership stay intact.
    }
    PlayerAnalysisStrip {
        objectName: "audioWaveformStrip"
        anchors.fill: parent
        anchors.leftMargin: analysis.cueControlsWidth
        anchors.rightMargin: analysis.cueControlsWidth
        visible: !MediaAnalysis.visualizer.active && MediaTools.waveformVisible && MediaAnalysis.waveform.length > 0
        opacity: 0.65
        color: PlayerStyle.accent
        samples: MediaAnalysis.waveform
    }
    component CueButton: T.Button {
        implicitWidth: PlayerStyle.px(24)
        implicitHeight: PlayerStyle.px(24)
        padding: 0
        activeFocusOnTab: true
        contentItem: Text {
            text: parent.text
            color: PlayerStyle.accentForeground
            font.family: PlayerStyle.fontFamily
            font.pixelSize: PlayerStyle.px(20)
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
        }
        background: Rectangle {
            color: parent.hovered ? Qt.lighter(PlayerStyle.accent,1.15) : PlayerStyle.accent
            radius: PlayerStyle.px(4)
            border.color: PlayerStyle.trackForeground
            border.width: parent.visualFocus ? PlayerStyle.px(2) : 0
        }
    }
    Item {
        id: cueTimeline
        z: 3
        objectName: "subtitleCueStrip"
        anchors.fill: parent
        visible: analysis.subtitleTimelineVisible
        CueButton {
            id: previousCue
            anchors.verticalCenter: parent.verticalCenter
            text: "‹"
            Accessible.name: qsTr("Previous subtitle cue")
            AccessibleCompat.id: "previousSubtitleCue"
            onClicked: MediaTools.seekSubtitleCue(false)
        }
        CueButton {
            id: earlierCue
            anchors.verticalCenter: parent.verticalCenter
            anchors.left: previousCue.right
            anchors.leftMargin: PlayerStyle.px(2)
            text: "−"
            Accessible.name: qsTr("Show subtitles 50 milliseconds earlier")
            AccessibleCompat.id: "subtitleDelayEarlier"
            onClicked: Player.subtitleDelayMS = Math.max(-600000,Player.subtitleDelayMS-50)
        }
        Rectangle {
            id: cueGraph
            anchors.left: earlierCue.right
            anchors.right: laterCue.left
            anchors.leftMargin: PlayerStyle.px(2)
            anchors.rightMargin: PlayerStyle.px(2)
            height: parent.height
            color: "transparent"
            clip: true
            PlayerAnalysisStrip {
                anchors.fill: parent
                color: PlayerStyle.foreground
                opacity: 0.35
                cues: MediaTools.cues
                durationMS: MediaAnalysis.durationMS
                timeScale: MediaTools.subtitleTimeScale
                delayMS: Player.subtitleDelayMS
            }
            MouseArea {
                id: offset
                anchors.fill: parent
                preventStealing: true
                property real startX: 0
                property int startDelay: 0
                property bool adjusting: false
                function hitsCue(x) {
                    const time = x / width * MediaAnalysis.durationMS
                    return MediaTools.cues.some(cue => {
                        const start = cue.start * MediaTools.subtitleTimeScale + Player.subtitleDelayMS
                        const end = cue.end * MediaTools.subtitleTimeScale + Player.subtitleDelayMS
                        return time >= start && time <= end
                    })
                }
                onPressed: mouse => {
                    // Empty track and the topmost handle keep ordinary seeking.
                    if (!hitsCue(mouse.x) || Math.abs(mouse.x - Player.position * width) < PlayerStyle.px(8)) {
                        mouse.accepted = false
                        return
                    }
                    startX = mouse.x
                    startDelay = Player.subtitleDelayMS
                    adjusting = false
                    cueGraph.forceActiveFocus(Qt.MouseFocusReason)
                }
                onPositionChanged: mouse => {
                    if (pressed && Math.abs(mouse.x-startX) >= Qt.styleHints.startDragDistance)
                        adjusting = true
                    if (pressed && adjusting && width > 0)
                        Player.subtitleDelayMS = Math.max(-600000, Math.min(600000,
                            Math.round(startDelay+(mouse.x-startX)/width*MediaAnalysis.durationMS)))
                }
                onReleased: mouse => {
                    if (!adjusting) Player.position = Math.max(0, Math.min(1, mouse.x / width))
                }
                onCanceled: adjusting = false
                cursorShape: Qt.SizeHorCursor
            }
            Accessible.name: qsTr("Subtitle timeline offset")
            Accessible.description: qsTr("Click to seek. Drag a subtitle cue to adjust timing; use the playback handle or empty track to seek. Left and Right adjust timing by 50 milliseconds. Current delay: %1 milliseconds.").arg(Player.subtitleDelayMS)
            AccessibleCompat.id: "subtitleTimelineOffset"
            activeFocusOnTab: true
            Rectangle { anchors.fill: parent; color: "transparent"; border.color: PlayerStyle.trackForeground; border.width: parent.activeFocus?1:0 }
            Keys.onLeftPressed: Player.subtitleDelayMS = Math.max(-600000,Player.subtitleDelayMS-50)
            Keys.onRightPressed: Player.subtitleDelayMS = Math.min(600000,Player.subtitleDelayMS+50)
        }
        CueButton {
            id: laterCue
            anchors.verticalCenter: parent.verticalCenter
            anchors.right: nextCue.left
            anchors.rightMargin: PlayerStyle.px(2)
            text: "+"
            Accessible.name: qsTr("Show subtitles 50 milliseconds later")
            AccessibleCompat.id: "subtitleDelayLater"
            onClicked: Player.subtitleDelayMS = Math.min(600000,Player.subtitleDelayMS+50)
        }
        CueButton {
            id: nextCue
            anchors.verticalCenter: parent.verticalCenter
            anchors.right: parent.right
            text: "›"
            Accessible.name: qsTr("Next subtitle cue")
            AccessibleCompat.id: "nextSubtitleCue"
            onClicked: MediaTools.seekSubtitleCue(true)
        }
    }
    HoverHandler {
        id: hover
        enabled: MainCtx.seekPreviewEnabled
        onHoveredChanged: {
            if (hovered) { analysis.hoverPosition = Math.max(0, Math.min(1, (point.position.x-analysis.cueControlsWidth) / analysis.graphWidth)); analysis.positionPreview(); preview.open(); MediaAnalysis.requestPreview(analysis.hoverPosition) }
            else { preview.close(); MediaAnalysis.hidePreview() }
        }
        onPointChanged: if (hovered) {
            analysis.hoverPosition = Math.max(0, Math.min(1, (point.position.x-analysis.cueControlsWidth) / analysis.graphWidth))
            analysis.positionPreview()
            MediaAnalysis.requestPreview(analysis.hoverPosition)
        }
    }
    T.Popup {
        id: preview
        parent: analysis.overlayParent
        width: Math.min(PlayerStyle.px(320), parent.width - PlayerStyle.px(40))
        height: PlayerStyle.px(210)
        padding: PlayerStyle.px(8)
        focus: false
        closePolicy: T.Popup.NoAutoClose
        background: Rectangle { color: PlayerStyle.panel; radius: PlayerStyle.px(8) }
        contentItem: Item {
            Image {
                objectName: "seekPreviewImage"
                anchors.top: parent.top
                width: parent.width
                height: parent.height - PlayerStyle.px(24)
                source: MediaAnalysis.previewSource
                cache: false
                fillMode: Image.PreserveAspectFit
                visible: source.toString().length > 0 && MediaAnalysis.previewStatus.length === 0
            }
            Text {
                anchors.fill: parent
                visible: MediaAnalysis.previewStatus.length > 0
                text: MediaAnalysis.previewStatus
                font.family: PlayerStyle.fontFamily
                font.pixelSize: PlayerStyle.px(12)
                color: PlayerStyle.sectionForeground
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
                wrapMode: Text.Wrap
            }
            Text {
                anchors.bottom: parent.bottom
                width: parent.width
                text: {
                    const seconds = Math.floor(MediaAnalysis.previewPosition * Math.max(0, MediaAnalysis.durationMS) / 1000)
                    return Math.floor(seconds / 60) + ":" + String(seconds % 60).padStart(2, "0")
                }
                color: PlayerStyle.trackForeground
                font.family: PlayerStyle.fontFamily
                font.pixelSize: PlayerStyle.px(12)
                horizontalAlignment: Text.AlignHCenter
            }
        }
    }
}
