// SPDX-License-Identifier: GPL-2.0-or-later
// Dimensions/colors from Juxtopposed's VLC Redesign, CC BY 4.0.
pragma Singleton
import QtQuick
import VLC.Style
import VLC.MainInterface

QtObject {
    readonly property bool dark: VLCStyle.palette.isDark
    readonly property color chrome: dark ? "#1b1b1b" : Qt.rgba(0.8369140625, 0.8369140625, 0.8369140625, 0.75)
    readonly property color panel: dark ? "#0e0e0e" : "#e7e7e7"
    readonly property color foreground: dark ? "#8f8f8f" : "#2e2e2e"
    readonly property color trackForeground: dark ? "#969696" : "#2e2e2e"
    readonly property color sectionForeground: dark ? "#6b6b6b" : "#676767"
    readonly property color accent: MainCtx.redesignAccent
    readonly property color accentWell: Qt.colorEqual(accent,"#d37918") ? "#371f06" : Qt.darker(accent,4)
    readonly property color accentKnob: Qt.colorEqual(accent,"#d37918") ? "#ab6314" : Qt.darker(accent,1.25)
    readonly property color timeline: dark ? "#090909" : "#dedede"
    readonly property color hover: dark ? "#3b3b3b" : "#c5c5c5"
    readonly property FontLoader inter: FontLoader { source: "qrc:/redesign/fonts/InterVariable.ttf" }
    readonly property string fontFamily: inter.name
    function px(value) { return VLCStyle.dp(value, VLCStyle.scale) }
}
