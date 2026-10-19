// SPDX-License-Identifier: GPL-2.0-or-later
import QtQuick
import QtQuick.Templates as T
import VLC.Player

// Figma's 68 x 32 segmented toggle: 26px knob and 33px label well.
T.CheckBox {
    id: toggleSwitch
    property bool value: false
    implicitWidth: PlayerStyle.px(68)
    implicitHeight: PlayerStyle.px(32)
    padding: 0
    checkable: true
    checked: value
    // The setting owner may reject an edit (for example a read-only store).
    // Only its accepted value may change the rendered and accessible state.
    nextCheckState: function() { return value ? Qt.Checked : Qt.Unchecked }
    indicator: null
    activeFocusOnTab: true
    hoverEnabled: true
    Accessible.role: Accessible.CheckBox
    Accessible.checkable: true
    Accessible.checked: value
    Accessible.description: value ? qsTr("On") : qsTr("Off")
    Accessible.onPressAction: clicked()
    contentItem: Item {
        Rectangle {
            x: PlayerStyle.px(toggleSwitch.value ? 3 : 32)
            y: PlayerStyle.px(3)
            width: PlayerStyle.px(33); height: PlayerStyle.px(26)
            radius: PlayerStyle.px(3)
            color: toggleSwitch.value ? "#371f06" : PlayerStyle.dark ? "#191919" : "#c5c5c5"
        }
        Rectangle {
            x: PlayerStyle.px(toggleSwitch.value ? 39 : 3)
            y: PlayerStyle.px(3)
            width: PlayerStyle.px(26); height: width
            radius: PlayerStyle.px(3)
            color: toggleSwitch.value ? "#ab6314" : PlayerStyle.dark ? "#404040" : "#969696"
        }
        Text {
            x: PlayerStyle.px(toggleSwitch.value ? 10 : 36)
            y: PlayerStyle.px(9)
            width: PlayerStyle.px(toggleSwitch.value ? 19 : 24)
            height: PlayerStyle.px(15)
            text: toggleSwitch.value ? qsTr("ON") : qsTr("OFF")
            textFormat: Text.PlainText
            font.family: PlayerStyle.fontFamily
            font.pixelSize: PlayerStyle.px(12)
            color: toggleSwitch.value ? PlayerStyle.accent : PlayerStyle.sectionForeground
        }
    }
    background: Rectangle {
        color: PlayerStyle.timeline
        radius: PlayerStyle.px(6)
        border.color: PlayerStyle.accent
        border.width: toggleSwitch.visualFocus ? PlayerStyle.px(2) : 0
    }
}
