// SPDX-License-Identifier: GPL-2.0-or-later
import QtQuick
import QtQuick.Templates as T
import QtQuick.Layouts
import VLC.Player

Column {
    id: row
    required property var option
    property bool slider: false
    property int controlHeight: 32
    property int rangeHeight: 22
    property int valueWidth: option.choices && option.choices.length > 0 ? 152 : option.kind === "number" ? 110 : 152
    width: parent.width
    spacing: PlayerStyle.px(8)
    topPadding: PlayerStyle.px(10)
    bottomPadding: PlayerStyle.px(10)
    opacity: option.available ? 1 : 0.5
    enabled: option.available
    property var current: option.value
    function apply(value) {
        if (MediaTools.setValue(option.key, value) && option.module && !MediaTools.filterEnabled(option.module))
            MediaTools.enableFilter(option.module, true)
    }
    function bands() {
        const values = String(current || "").trim().split(/\s+/).map(Number)
        return values.length === 10 && values.every(isFinite) ? values : [0,0,0,0,0,0,0,0,0,0]
    }
    function setBand(index, value) { const values = bands(); values[index] = Number(value.toFixed(1)); apply(values.join(" ")) }
    function displayValue(value) {
        if (option.color) return "#" + Number(value).toString(16).padStart(6, "0").toUpperCase()
        return value === undefined ? "" : String(value)
    }
    function refresh() {
        current = MediaTools.value(option.key)
        if (!editor.activeFocus) editor.text = displayValue(current)
    }
    Component.onCompleted: refresh()
    Connections { target: MediaTools; function onChanged() { row.refresh() } }
    RowLayout {
        width: parent.width
        height: PlayerStyle.px(row.controlHeight)
        spacing: PlayerStyle.px(12)
        Text {
            Layout.fillWidth: true
            text: row.option.label
            color: PlayerStyle.trackForeground
            font.family: PlayerStyle.fontFamily
            font.pixelSize: PlayerStyle.px(14)
            elide: Text.ElideRight
        }
        PlayerSettingsSwitch {
            visible: row.option.kind === "bool"
            value: Boolean(row.current)
            Accessible.name: row.option.label
            onClicked: row.apply(!value)
        }
        PlayerSettingsChoice {
            visible: !row.option.color && row.option.choices && row.option.choices.length > 0
            Layout.preferredWidth: PlayerStyle.px(row.valueWidth)
            label: row.option.label
            model: row.option.choices || []
            textRole: "text"
            valueRole: "value"
            currentIndex: indexOfValue(row.current)
            onActivated: row.apply(currentValue)
        }
        T.TextField {
            id: editor
            objectName: "mediaOption_" + row.option.key
            visible: row.option.key !== "equalizer-bands" && row.option.kind !== "bool" && (row.option.color || !row.option.choices || row.option.choices.length === 0)
            Layout.preferredWidth: PlayerStyle.px(row.valueWidth)
            implicitHeight: PlayerStyle.px(row.controlHeight)
            padding: PlayerStyle.px(6)
            rightPadding: PlayerStyle.px(row.option.color ? 36 : 6)
            color: PlayerStyle.trackForeground
            selectionColor: PlayerStyle.accent
            font.family: PlayerStyle.fontFamily
            font.pixelSize: PlayerStyle.px(14)
            horizontalAlignment: row.slider ? TextInput.AlignRight : TextInput.AlignLeft
            selectByMouse: true
            maximumLength: 512
            Accessible.name: row.option.label
            onEditingFinished: {
                row.apply(row.option.color ? (/^#[0-9a-fA-F]{6}$/.test(text) ? parseInt(text.slice(1),16) : NaN) : row.option.kind === "number" ? Number(text) : text)
                row.refresh()
            }
            background: Rectangle {
                color: row.slider ? "transparent" : PlayerStyle.timeline
                radius: PlayerStyle.px(4)
                border.color: PlayerStyle.accent
                border.width: editor.activeFocus ? PlayerStyle.px(2) : 0
                Rectangle {
                    visible: Boolean(row.option.color)
                    anchors.right: parent.right; anchors.rightMargin: PlayerStyle.px(7)
                    anchors.verticalCenter: parent.verticalCenter
                    width: PlayerStyle.px(22); height: width
                    color: row.option.color ? row.displayValue(row.current) : "transparent"
                    border.color: PlayerStyle.sectionForeground
                    radius: PlayerStyle.px(2)
                }
            }
        }
    }
    RowLayout {
        visible: row.option.key === "equalizer-bands"
        width: parent.width
        height: visible ? PlayerStyle.px(180) : 0
        spacing: PlayerStyle.px(3)
        Repeater {
            model: ["60", "170", "310", "600", "1k", "3k", "6k", "12k", "14k", "16k"]
            ColumnLayout {
                required property int index
                required property string modelData
                Layout.fillWidth: true
                Layout.preferredWidth: 0
                T.Slider {
                    id: band
                    Layout.alignment: Qt.AlignHCenter
                    Layout.preferredHeight: PlayerStyle.px(130)
                    Layout.preferredWidth: PlayerStyle.px(22)
                    orientation: Qt.Vertical
                    from: -20; to: 20; stepSize: 0.1
                    value: row.bands()[parent.index]
                    activeFocusOnTab: true
                    Accessible.name: qsTr("Equalizer %1 hertz").arg(parent.modelData)
                    onMoved: row.setBand(parent.index, value)
                    background: Rectangle { x: (band.width - width) / 2; y: band.topPadding; width: PlayerStyle.px(6); height: band.availableHeight; radius: width/2; color: PlayerStyle.timeline }
                    handle: Rectangle { x: (band.width - width) / 2; y: band.topPadding + band.visualPosition * (band.availableHeight - height); width: PlayerStyle.px(18); height: PlayerStyle.px(8); radius: PlayerStyle.px(3); color: PlayerStyle.accent; border.color: PlayerStyle.trackForeground; border.width: band.visualFocus ? 1 : 0 }
                }
                Text { Layout.fillWidth: true; text: parent.modelData; color: PlayerStyle.sectionForeground; font.family: PlayerStyle.fontFamily; font.pixelSize: PlayerStyle.px(10); horizontalAlignment: Text.AlignHCenter }
                Text { Layout.fillWidth: true; text: Number(row.bands()[parent.index]).toFixed(0); color: PlayerStyle.trackForeground; font.family: PlayerStyle.fontFamily; font.pixelSize: PlayerStyle.px(10); horizontalAlignment: Text.AlignHCenter }
            }
        }
    }
    T.Slider {
        id: range
        visible: row.slider && !row.option.color && row.option.kind === "number" && row.option.maximum > row.option.minimum
        width: parent.width
        height: visible ? PlayerStyle.px(row.rangeHeight) : 0
        from: row.option.minimum || 0
        to: row.option.maximum || 1
        stepSize: row.option.step || 1
        value: Number(row.current) || 0
        activeFocusOnTab: true
        Accessible.name: row.option.label
        onMoved: row.apply(value)
        background: Rectangle {
            x: range.leftPadding
            y: (range.height - height) / 2
            width: range.availableWidth
            height: PlayerStyle.px(12)
            radius: height / 2
            color: PlayerStyle.timeline
            Rectangle { width: parent.width * range.visualPosition; height: parent.height; radius: parent.radius; color: PlayerStyle.accent; opacity: 0.45 }
        }
        handle: Rectangle {
            x: range.leftPadding + range.visualPosition * (range.availableWidth - width)
            y: (range.height - height) / 2
            width: PlayerStyle.px(8)
            height: PlayerStyle.px(24)
            radius: PlayerStyle.px(4)
            color: PlayerStyle.accent
            border.width: range.visualFocus ? PlayerStyle.px(2) : 0
            border.color: PlayerStyle.trackForeground
        }
    }
}
