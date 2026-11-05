/*****************************************************************************
 * Copyright (C) 2020 VLC authors and VideoLAN
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * ( at your option ) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston MA 02110-1301, USA.
 *****************************************************************************/
import QtQuick

import VLC.MainInterface
import VLC.Dialogs

Item {

    ShortcutExt{ context: Qt.WindowShortcut; sequences:MainCtx.interfaceShortcutSequences("Ctrl+O"); onActivated: DialogsProvider.simpleOpenDialog(); }
    ShortcutExt{ sequences:MainCtx.interfaceShortcutSequences("Ctrl+Shift+O"); onActivated: DialogsProvider.openFileDialog(); }
    ShortcutExt{ context: Qt.WindowShortcut; sequences:MainCtx.interfaceShortcutSequences("Ctrl+F"); onActivated: DialogsProvider.PLOpenDir(); }
    ShortcutExt{ sequences:MainCtx.interfaceShortcutSequences("Ctrl+D"); onActivated: DialogsProvider.openDiscDialog(); }
    ShortcutExt{ sequences:MainCtx.interfaceShortcutSequences("Ctrl+N"); onActivated: DialogsProvider.openNetDialog(); }
    ShortcutExt{ sequences:MainCtx.interfaceShortcutSequences("Ctrl+C"); onActivated: DialogsProvider.openCaptureDialog(); }
    ShortcutExt{ sequences:MainCtx.interfaceShortcutSequences("Ctrl+V"); onActivated: MainCtx.pasteFromClipboard(); }
    ShortcutExt{ context: Qt.WindowShortcut; sequences:MainCtx.interfaceShortcutSequences("Ctrl+Y"); onActivated: DialogsProvider.savePlayingToPlaylist(); }
    ShortcutExt{ sequences:MainCtx.interfaceShortcutSequences("Ctrl+R"); onActivated: DialogsProvider.openAndTranscodingDialogs(); }
    ShortcutExt{ sequences:MainCtx.interfaceShortcutSequences("Ctrl+S"); onActivated: DialogsProvider.openAndStreamingDialogs(); }
    ShortcutExt{ sequences:MainCtx.interfaceShortcutSequences("Ctrl+Q"); onActivated: DialogsProvider.quit(); }
    ShortcutExt{ sequences:MainCtx.interfaceShortcutSequences("Ctrl+E"); onActivated: DialogsProvider.extendedDialog(); }
    ShortcutExt{ sequences:MainCtx.interfaceShortcutSequences("Ctrl+I"); onActivated: DialogsProvider.mediaInfoDialog(); }
    ShortcutExt{ sequences:MainCtx.interfaceShortcutSequences("Ctrl+J"); onActivated: DialogsProvider.mediaCodecDialog(); }
    ShortcutExt{ sequences:MainCtx.interfaceShortcutSequences("Ctrl+M"); onActivated: DialogsProvider.messagesDialog(); }
    ShortcutExt{ sequences:MainCtx.interfaceShortcutSequences("Ctrl+P"); onActivated: DialogsProvider.prefsDialog(); }
    ShortcutExt{ sequences:MainCtx.interfaceShortcutSequences("Ctrl+T"); onActivated: DialogsProvider.gotoTimeDialog(); }

    ShortcutExt{ sequences:MainCtx.interfaceShortcutSequences("Ctrl+Shift+W"); onActivated: DialogsProvider.vlmDialog(); }

    ShortcutExt{ sequences:MainCtx.queueShortcutSequences(); onActivated: MainCtx.playqueuePanel.visible = !MainCtx.playqueuePanel.visible; }

    ShortcutExt{ sequences:MainCtx.interfaceShortcutSequences("F1"); onActivated: DialogsProvider.helpDialog() }
    ShortcutExt{ sequences:MainCtx.interfaceShortcutSequences("Shift+F1"); onActivated: DialogsProvider.aboutDialog() }
    ShortcutExt{ sequences:MainCtx.interfaceShortcutSequences("F10"); onActivated: MainCtx.toggleToolbarMenu() }
    ShortcutExt{ sequences:MainCtx.interfaceShortcutSequences("F11"); onActivated: MainCtx.toggleInterfaceFullScreen() }
    ShortcutExt{ sequences:MainCtx.interfaceShortcutSequences("Ctrl+H"); onActivated: MainCtx.minimalView = !MainCtx.minimalView; }

    ShortcutExt{ sequences:MainCtx.interfaceShortcutSequences("Ctrl+="); onActivated: MainCtx.incrementIntfUserScaleFactor(true) }
    ShortcutExt{ sequences:MainCtx.interfaceShortcutSequences("Ctrl+Shift+-"); onActivated: MainCtx.incrementIntfUserScaleFactor(false) }

    Loader {
        active: MainCtx.mediaLibraryAvailable
        source: "qrc:///qt/qml/VLC/MediaLibrary/MLGlobalShortcuts.qml"
    }
}
