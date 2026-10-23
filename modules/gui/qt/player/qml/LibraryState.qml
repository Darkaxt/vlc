// SPDX-License-Identifier: GPL-2.0-or-later
pragma Singleton
import QtQuick
import VLC.MainInterface
import VLC.MediaLibrary

QtObject {
    id: state
    // Presentation only. Media, history, watched state and playlists remain in VLC's library.
    property var pins: []
    property bool details: false
    readonly property string viewMode: details ? "detail" : MainCtx.gridView ? "grid" : "list"
    property string error: ""
    property string saveError: ""
    readonly property bool writable: error === ""
    readonly property string settingKey: "redesign/library-v1"

    function save(nextPins, nextMode) {
        if (!writable) return false
        const encoded = JSON.stringify({version: 1, pins: nextPins, details: nextMode === "detail"})
        if (encoded.length > 65536) {
            saveError = qsTr("The library shortcuts are too large to save. Remove a pin before adding another.")
            return false
        }
        MainCtx.setSettingValue(settingKey, encoded)
        saveError = ""
        pins = nextPins
        details = nextMode === "detail"
        if (!details) MainCtx.gridView = nextMode === "grid"
        return true
    }
    function pinned(key) { return pins.some(p => p.id === key) }
    function togglePin(id, title, section) {
        if (pinned(id)) return save(pins.filter(p => p.id !== id), viewMode)
        if (pins.length >= 128) {
            saveError = qsTr("The library supports up to 128 pinned items. Remove a pin before adding another.")
            return false
        }
        // Bound only the cached shortcut label, retaining both ends and the
        // canonical native identity. The actual playlist/folder name is kept in
        // ML and resolved again when opening it. Never write data we reject on
        // restart, or split a UTF-16 surrogate pair while eliding a long label.
        let label = title
        if (label.length > 1024) {
            let first = label.slice(0,511), last = label.slice(-512)
            if (first.charCodeAt(first.length-1) >= 0xD800 && first.charCodeAt(first.length-1) <= 0xDBFF) first = first.slice(0,-1)
            if (last.charCodeAt(0) >= 0xDC00 && last.charCodeAt(0) <= 0xDFFF) last = last.slice(1)
            label = first + "\u2026" + last
        }
        return save([...pins, {id: id, title: label, section: section}], viewMode)
    }
    function setView(mode) { return save(pins, mode) }
    function reset() { return save([], MainCtx.gridView ? "grid" : "list") }
    Component.onCompleted: {
        const raw = MainCtx.settingValue(settingKey, "")
        if (raw === "") return
        try {
            if (typeof raw !== "string" || raw.length > 65536) throw new Error("size")
            const data = JSON.parse(raw)
            if (data.version !== 1 || !Array.isArray(data.pins) || data.pins.length > 128
                    || typeof data.details !== "boolean") throw new Error("version")
            const keys = new Set()
            for (const pin of data.pins) {
                if (typeof pin.id !== "string" || pin.id.length > 128 || typeof pin.title !== "string"
                        || pin.title.length > 1024 || !["folders", "playlists"].includes(pin.section)
                        || keys.has(pin.id)) throw new Error("pin")
                const identity = MediaLib.deserializeMlItemIdFromString(pin.id)
                const type = pin.section === "folders" ? "VLC_ML_PARENT_FOLDER" : "VLC_ML_PARENT_PLAYLIST"
                if (!identity.isValid() || identity.toString() !== pin.id || !pin.id.startsWith(type + " - ")) throw new Error("identity")
                keys.add(pin.id)
            }
            pins = data.pins
            details = data.details
        } catch (_) {
            error = qsTr("Saved library layout could not be read. The original setting has been preserved; pins and layout changes are disabled.")
        }
    }
}
