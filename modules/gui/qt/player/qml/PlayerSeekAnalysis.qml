// SPDX-License-Identifier: GPL-2.0-or-later
import QtQuick
import QtQuick.Templates as T
import VLC.Player

Item {
    id: analysis
    required property Item overlayParent
    property real hoverPosition: 0
    anchors.fill: parent
    function positionPreview() {
        const point = analysis.mapToItem(analysis.overlayParent, analysis.width * analysis.hoverPosition, 0)
        preview.x = Math.max(PlayerStyle.px(20), Math.min(analysis.overlayParent.width - preview.width - PlayerStyle.px(20), point.x - preview.width / 2))
        preview.y = Math.max(PlayerStyle.px(40), point.y - preview.height - PlayerStyle.px(12))
    }
    Connections {
        target: analysis.overlayParent
        function onWidthChanged() { if (hover.hovered) analysis.positionPreview() }
        function onHeightChanged() { if (hover.hovered) analysis.positionPreview() }
    }
    PlayerAnalysisStrip {
        objectName: "audioWaveformStrip"
        anchors.fill: parent
        visible: MediaTools.waveformVisible && MediaAnalysis.waveform.length > 0
        opacity: 0.65
        color: PlayerStyle.accent
        samples: MediaAnalysis.waveform
    }
    Item {
        objectName: "subtitleCueStrip"
        width: parent.width
        height: PlayerStyle.px(8)
        visible: MediaTools.timelineVisible && MediaTools.cues.length > 0
        PlayerAnalysisStrip {
            anchors.fill: parent
            color: PlayerStyle.accent
            cues: MediaTools.cues
            durationMS: MediaAnalysis.durationMS
            timeScale: MediaTools.subtitleTimeScale
            delayMS: Player.subtitleDelayMS
        }
        MouseArea {
            id: offset
            anchors.fill: parent
            property real startX: 0
            property int startDelay: 0
            onPressed: mouse => { startX = mouse.x; startDelay = Player.subtitleDelayMS }
            onPositionChanged: mouse => { if (pressed && width > 0) Player.subtitleDelayMS = Math.round(startDelay + (mouse.x - startX) / width * MediaAnalysis.durationMS) }
            cursorShape: Qt.SizeHorCursor
        }
        Accessible.name: qsTr("Subtitle timeline offset")
        Accessible.description: qsTr("Drag the cue strip to adjust the subtitle delay. Current delay: %1 milliseconds.").arg(Player.subtitleDelayMS)
        activeFocusOnTab: true
        readonly property bool visualFocus: activeFocus
        Rectangle { anchors.fill: parent; color: "transparent"; border.color: PlayerStyle.trackForeground; border.width: parent.visualFocus ? 1 : 0 }
        Keys.onLeftPressed: Player.subtitleDelayMS -= 50
        Keys.onRightPressed: Player.subtitleDelayMS += 50
    }
    HoverHandler {
        id: hover
        onHoveredChanged: {
            if (hovered) { analysis.hoverPosition = Math.max(0, Math.min(1, point.position.x / analysis.width)); analysis.positionPreview(); preview.open(); MediaAnalysis.requestPreview(analysis.hoverPosition) }
            else { preview.close(); MediaAnalysis.hidePreview() }
        }
        onPointChanged: if (hovered) {
            analysis.hoverPosition = Math.max(0, Math.min(1, point.position.x / analysis.width))
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
