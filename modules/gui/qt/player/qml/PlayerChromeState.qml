// SPDX-License-Identifier: GPL-2.0-or-later
import QtQml

QtObject {
    property bool fullscreen: false
    property bool hidden: false
    property bool topHovered: false
    property bool bottomHovered: false
    property bool topFocused: false
    property bool bottomFocused: false
    property bool topMenuOpen: false
    property bool bottomMenuOpen: false
    property int autoHideMode: 0
    property int hideDelay: 1000
    property bool fullscreenControls: true
    property real mouseSensitivity: 3
    property point lastPointer: Qt.point(NaN,NaN)
    property bool idle: false
    readonly property bool autoHide: autoHideMode === 1 || (autoHideMode === 0 && fullscreen)
    readonly property bool topVisible: !hidden && (!autoHide || !idle || topHovered || topFocused || topMenuOpen)
    readonly property bool bottomVisible: !hidden && (!fullscreen || fullscreenControls) && (!autoHide || !idle || bottomHovered || bottomFocused || bottomMenuOpen)
    property Timer hideTimer: Timer { interval: Math.max(0,hideDelay); onTriggered: idle = true }
    onAutoHideChanged: activity()
    Component.onCompleted: activity()
    function activity() { idle = false; if (!hideTimer) return; if (autoHide) hideTimer.restart(); else hideTimer.stop() }
    function pointerMoved(point) {
        if (!fullscreen || !isFinite(lastPointer.x) ||
                Math.hypot(point.x-lastPointer.x,point.y-lastPointer.y) >= mouseSensitivity) {
            lastPointer=point
            activity()
        }
    }
    function toggleHidden() { hidden = !hidden }
}
