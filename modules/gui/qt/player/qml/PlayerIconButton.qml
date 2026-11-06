// SPDX-License-Identifier: GPL-2.0-or-later
import QtQuick
import QtQuick.Templates as T
import QtQuick.Controls.impl
import VLC.MainInterface
import VLC.Player
import VLC.Util

T.ToolButton {
    id: button
    required property string glyph
    required property string description
    property bool accented: false
    property real glyphRotation: 0
    property color foreground: PlayerStyle.foreground
    implicitWidth: PlayerStyle.px(30)
    implicitHeight: PlayerStyle.px(32)
    padding: 0
    hoverEnabled: true
    activeFocusOnTab: true
    Accessible.name: description
    Accessible.role: Accessible.Button
    Accessible.onPressAction: clicked()
    T.ToolTip.visible: hovered || visualFocus
    T.ToolTip.text: description
    T.ToolTip.delay: 500
    background: Rectangle {
        radius: PlayerStyle.px(6)
        color: button.accented ? PlayerStyle.accent : button.down || button.hovered ? PlayerStyle.hover : "transparent"
        border.width: button.visualFocus ? PlayerStyle.px(2) : 0
        border.color: PlayerStyle.accent
    }
    contentItem: Item {
      IconImage {
        objectName: "playerGlyph-" + button.glyph
        anchors.centerIn: parent
        source: "qrc:/redesign/icons/" + button.glyph + (button.glyph === "mpv" ? ".ico" : ".svg")
        color: button.glyph === "mpv" ? "transparent" : button.accented ? PlayerStyle.accentForeground : button.checked && !["sidebar","more"].includes(button.glyph) ? PlayerStyle.accent : button.foreground
        opacity: button.enabled ? 1 : 0.45
        // Qt selects an ICO frame or rasterizes SVG at the native device ratio.
        // Its SVG edges already contain antialiasing: applying another linear
        // filter at a half-physical-pixel position visibly softens the icon.
        sourceSize: Qt.size(PlayerStyle.px(24), PlayerStyle.px(24))
        smooth: false
        rotation: button.glyphRotation
        width: PlayerStyle.px(24)
        height: PlayerStyle.px(24)
        fillMode: Image.PreserveAspectFit
      }
    }
    Keys.priority: Keys.AfterItem
    Keys.onPressed: event => Navigation.defaultKeyAction(event)
}
