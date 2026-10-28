// SPDX-License-Identifier: GPL-2.0-or-later
import QtQuick
import QtQuick.Templates as T

T.Button {
    id: button
    property bool primary: false
    property bool tinted: false
    property int fontPixelSize: 14
    property int fontWeight: Font.DemiBold
    implicitWidth: Math.max(PlayerStyle.px(100),implicitContentWidth+PlayerStyle.px(24))
    implicitHeight: PlayerStyle.px(32)
    padding: PlayerStyle.px(8)
    activeFocusOnTab: true; hoverEnabled: true
    Accessible.name: text
    Accessible.onPressAction: clicked()
    contentItem: Text {
        text: button.text; textFormat: Text.PlainText
        color: button.tinted?PlayerStyle.accent:button.primary?(PlayerStyle.accent.toString()==="#d37918"?"#161616":PlayerStyle.accentForeground):PlayerStyle.foreground
        opacity: button.enabled?1:0.45
        font.family: PlayerStyle.fontFamily; font.pixelSize: PlayerStyle.px(button.fontPixelSize)
        font.weight: button.fontWeight
        horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
    }
    background: Rectangle {
        radius: PlayerStyle.px(6)
        color: button.tinted?PlayerStyle.accentWell:button.primary?PlayerStyle.accent:button.hovered?PlayerStyle.hover:PlayerStyle.chrome
        border.width: button.visualFocus?PlayerStyle.px(2):0; border.color: PlayerStyle.accent
    }
}
