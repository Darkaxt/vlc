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
        // Layout strips scroll and clip their delegates. Like the preview,
        // this separate row belongs to the player's overlay coordinate space.
        parent: analysis.overlayParent
        z: 3
        objectName: "subtitleCueStrip"
        // A compact seek target can be only60px wide. Four24px buttons plus
        // gaps cannot share that width; expand this separate row within the
        // player while retaining the source alignment at larger sizes.
        width: Math.min(Math.max(analysis.width,PlayerStyle.px(240)),
                        Math.max(0,analysis.overlayParent.width-PlayerStyle.px(40)))
        x: {
            analysis.overlayParent.width
            const point=analysis.mapToItem(analysis.overlayParent,0,0)
            const left=Math.max(PlayerStyle.px(20),Math.min(analysis.overlayParent.width-width-PlayerStyle.px(20),
                                                          point.x+(analysis.width-width)/2))
            return left
        }
        height: PlayerStyle.px(24)
        visible: analysis.visible && MediaTools.timelineVisible && MediaTools.cues.length > 0
        // Leave the ordinary playback slider intact. A customized top-area
        // seek control places its timeline below instead of outside the window.
        y: {
            visible
            analysis.overlayParent.height
            analysis.width
            const point = analysis.mapToItem(analysis.overlayParent,0,0)
            return point.y < PlayerStyle.px(60) ? point.y+analysis.height+PlayerStyle.px(6) : point.y-height-PlayerStyle.px(6)
        }
        CueButton {
            id: previousCue
            text: "‹"
            Accessible.name: qsTr("Previous subtitle cue")
            AccessibleCompat.id: "previousSubtitleCue"
            onClicked: MediaTools.seekSubtitleCue(false)
        }
        CueButton {
            id: earlierCue
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
            color: PlayerStyle.timeline
            clip: true
            PlayerAnalysisStrip {
                anchors.fill: parent
                color: PlayerStyle.accent
                opacity: 0.45
                cues: MediaTools.cues
                durationMS: MediaAnalysis.durationMS
                timeScale: MediaTools.subtitleTimeScale
                delayMS: Player.subtitleDelayMS
            }
            Rectangle {
                width: PlayerStyle.px(3)
                height: parent.height
                x: Math.min(parent.width-width,Math.max(0,Player.position*parent.width))
                radius: width/2
                color: PlayerStyle.accent
            }
            MouseArea {
                id: offset
                anchors.fill: parent
                property real startX: 0
                property int startDelay: 0
                onPressed: mouse => { startX = mouse.x; startDelay = Player.subtitleDelayMS }
                onPositionChanged: mouse => {
                    if(pressed && width>0)
                        Player.subtitleDelayMS = Math.max(-600000,Math.min(600000,Math.round(startDelay+(mouse.x-startX)/width*MediaAnalysis.durationMS)))
                }
                cursorShape: Qt.SizeHorCursor
            }
            Accessible.name: qsTr("Subtitle timeline offset")
            Accessible.description: qsTr("Drag to adjust subtitle timing. Current delay: %1 milliseconds.").arg(Player.subtitleDelayMS)
            AccessibleCompat.id: "subtitleTimelineOffset"
            activeFocusOnTab: true
            Rectangle { anchors.fill: parent; color: "transparent"; border.color: PlayerStyle.trackForeground; border.width: parent.activeFocus?1:0 }
            Keys.onLeftPressed: Player.subtitleDelayMS = Math.max(-600000,Player.subtitleDelayMS-50)
            Keys.onRightPressed: Player.subtitleDelayMS = Math.min(600000,Player.subtitleDelayMS+50)
        }
        CueButton {
            id: laterCue
            anchors.right: nextCue.left
            anchors.rightMargin: PlayerStyle.px(2)
            text: "+"
            Accessible.name: qsTr("Show subtitles 50 milliseconds later")
            AccessibleCompat.id: "subtitleDelayLater"
            onClicked: Player.subtitleDelayMS = Math.min(600000,Player.subtitleDelayMS+50)
        }
        CueButton {
            id: nextCue
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
