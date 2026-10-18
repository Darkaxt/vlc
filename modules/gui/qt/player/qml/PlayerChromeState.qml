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
    readonly property bool topVisible: !hidden && (!fullscreen || topHovered || topFocused || topMenuOpen)
    readonly property bool bottomVisible: !hidden && (!fullscreen || bottomHovered || bottomFocused || bottomMenuOpen)
    function toggleHidden() { hidden = !hidden }
}
