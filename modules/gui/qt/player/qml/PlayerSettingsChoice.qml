// SPDX-License-Identifier: GPL-2.0-or-later
import QtQuick
import QtQuick.Controls.impl
import QtQuick.Templates as T
import VLC.Player

T.ComboBox {
    id: choice
    property string label
    implicitWidth: PlayerStyle.px(150)
    implicitHeight: PlayerStyle.px(32)
    padding: PlayerStyle.px(8)
    rightPadding: PlayerStyle.px(22)
    activeFocusOnTab: true
    focusPolicy: Qt.StrongFocus
    Accessible.name: label
    contentItem: Text {
        text: choice.displayText
        color: choice.enabled ? PlayerStyle.trackForeground : PlayerStyle.sectionForeground
        font.family: PlayerStyle.fontFamily
        font.pixelSize: PlayerStyle.px(14)
        elide: Text.ElideRight
        verticalAlignment: Text.AlignVCenter
    }
    indicator: IconImage {
        x: choice.width - width - PlayerStyle.px(7)
        anchors.verticalCenter: parent.verticalCenter
        source: "qrc:/redesign/icons/chevron-down.svg"
        sourceSize: Qt.size(PlayerStyle.px(12), PlayerStyle.px(12))
        width: PlayerStyle.px(12); height: width
        color: PlayerStyle.sectionForeground
    }
    background: Rectangle {
        color: PlayerStyle.timeline
        radius: PlayerStyle.px(4)
        border.width: choice.visualFocus ? PlayerStyle.px(2) : 0
        border.color: PlayerStyle.accent
    }
    delegate: T.ItemDelegate {
        required property int index
        required property var model
        width: choice.width
        implicitHeight: PlayerStyle.px(34)
        highlighted: choice.highlightedIndex === index
        text: choice.textAt(index)
        Accessible.name: text
        Accessible.onPressAction: clicked()
        contentItem: Text {
            text: choice.textAt(index)
            color: PlayerStyle.trackForeground
            font.family: PlayerStyle.fontFamily
            font.pixelSize: PlayerStyle.px(14)
            elide: Text.ElideRight
            verticalAlignment: Text.AlignVCenter
        }
        padding: PlayerStyle.px(8)
        background: Rectangle { color: parent.highlighted ? PlayerStyle.hover : PlayerStyle.panel }
    }
    popup: T.Popup {
        y: choice.height
        width: choice.width
        height: Math.min(contentItem.implicitHeight + 2, PlayerStyle.px(240))
        padding: PlayerStyle.px(1)
        closePolicy: T.Popup.CloseOnEscape | T.Popup.CloseOnPressOutsideParent
        contentItem: ListView {
            clip: true
            implicitHeight: contentHeight
            model: choice.popup.visible ? choice.delegateModel : null
            currentIndex: choice.highlightedIndex
            boundsBehavior: Flickable.StopAtBounds
            T.ScrollBar.vertical: T.ScrollBar { }
        }
        background: Rectangle { color: PlayerStyle.panel; radius: PlayerStyle.px(4); border.color: PlayerStyle.sectionForeground }
    }
}
