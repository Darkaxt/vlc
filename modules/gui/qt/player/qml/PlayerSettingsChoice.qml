// SPDX-License-Identifier: GPL-2.0-or-later
import QtQuick
import QtQuick.Controls.impl
import QtQuick.Templates as T
import QtQuick.Layouts
import VLC.Player

T.ComboBox {
    id: choice
    property string label
    property bool outlined: false
    property bool inputStyle: false
    property bool expandUp: false
    // Native values, never translated labels, identify the original artwork.
    property var optionIcons: ({})
    readonly property bool referenceOptions: Object.keys(optionIcons).length > 0
    // The popup is reparented to Qt's overlay. Capture the scene/panel below
    // that overlay, never the overlay itself or this popup recursively.
    readonly property Item backdropSource: {
        let item = choice
        const window = choice.Window.window
        while (item.parent && item.parent !== T.Overlay.overlay &&
               (!window || item.parent !== window.contentItem)) item = item.parent
        return item
    }
    implicitWidth: PlayerStyle.px(150)
    implicitHeight: PlayerStyle.px(32)
    padding: PlayerStyle.px(outlined ? 16 : 8)
    rightPadding: PlayerStyle.px(inputStyle ? 12 : 42)
    activeFocusOnTab: true
    focusPolicy: Qt.StrongFocus
    Accessible.name: label
    contentItem: Text {
        text: choice.displayText
        color: choice.enabled ? PlayerStyle.foreground : PlayerStyle.sectionForeground
        font.family: PlayerStyle.fontFamily
        font.pixelSize: PlayerStyle.px(14)
        elide: Text.ElideRight
        verticalAlignment: Text.AlignVCenter
    }
    indicator: IconImage {
        visible: !choice.inputStyle
        smooth: false
        x: choice.width - width - PlayerStyle.px(10)
        anchors.verticalCenter: parent.verticalCenter
        source: "qrc:/redesign/icons/chevron-down.svg"
        sourceSize: Qt.size(width,height)
        width: PlayerStyle.px(24); height: width
        color: PlayerStyle.foreground
        rotation: choice.expandUp && !choice.popup.visible ? 180 : 0
    }
    background: Rectangle {
        color: choice.inputStyle ? PlayerStyle.timeline : choice.outlined ? PlayerStyle.chrome : PlayerStyle.timeline
        radius: PlayerStyle.px(4)
        border.width: choice.visualFocus || choice.outlined || choice.inputStyle ? PlayerStyle.px(2) : 0
        border.color: choice.visualFocus ? PlayerStyle.accent : choice.inputStyle ? PlayerStyle.chrome : PlayerStyle.timeline
    }
    delegate: T.ItemDelegate {
        required property int index
        required property var model
        width: choice.width
        implicitHeight: PlayerStyle.px(choice.referenceOptions ? 44 : 34)
        highlighted: choice.highlightedIndex === index
        text: choice.textAt(index)
        Accessible.name: text
        Accessible.onPressAction: clicked()
        contentItem: RowLayout {
            spacing: PlayerStyle.px(8)
            Image {
                readonly property string glyph: choice.optionIcons[String(choice.valueAt(index))] || ""
                visible: glyph.length > 0
                Layout.preferredWidth: PlayerStyle.px(24)
                Layout.preferredHeight: PlayerStyle.px(24)
                source: visible ? PlayerStyle.themedIcon("qrc:/redesign/icons/" + glyph + ".svg") : ""
                sourceSize: Qt.size(width,height)
                smooth: false
            }
            Text {
                Layout.fillWidth: true
                text: choice.textAt(index)
                color: PlayerStyle.trackForeground
                font.family: PlayerStyle.fontFamily
                font.pixelSize: PlayerStyle.px(14)
                elide: Text.ElideRight
                verticalAlignment: Text.AlignVCenter
            }
            IconImage {
                visible: choice.referenceOptions && choice.currentIndex === index
                Layout.preferredWidth: PlayerStyle.px(24)
                Layout.preferredHeight: PlayerStyle.px(24)
                source: "qrc:/redesign/icons/choice-selected.svg"
                sourceSize: Qt.size(width,height)
                color: PlayerStyle.accent
                smooth: false
            }
        }
        padding: PlayerStyle.px(8)
        background: Rectangle { color: parent.highlighted ? PlayerStyle.hover : "transparent" }
    }
    readonly property T.Popup retainedPopup: popup
    popup: T.Popup {
        readonly property Item retainedBackdrop: background
        y: choice.expandUp ? -height : choice.height
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
        background: LibraryGlass { backgroundSource: choice.backdropSource; active: choice.popup.opened; radius: PlayerStyle.px(4) }
    }
}
