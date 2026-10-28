// SPDX-License-Identifier: GPL-2.0-or-later
import QtQuick
import QtQuick.Layouts
import QtQuick.Templates as T
import QtQuick.Controls.impl
import VLC.MainInterface
import VLC.Player
import VLC.Playlist
import VLC.Dialogs
import VLC.Util

Loader {
    id:control
    required property string controlKey
    property bool compact:false
    property bool topBar:false
    property var checkedControls:({})
    property Item popupParent:parent
    signal actionRequested(string key,var invoker)
    readonly property var labels:({more:qsTr("Main menu"),browser:qsTr("Media browser"),folder:qsTr("Folder Name"),filename:qsTr("File Name"),artist:qsTr("Artist Name"),playlistname:qsTr("Playlist Name"),previous:qsTr("Previous"),play:qsTr("Play / Pause"),next:qsTr("Next"),elapsed:qsTr("Elapsed time"),duration:qsTr("Duration / remaining time"),seek:qsTr("Playback position"),mute:qsTr("Mute"),volume:qsTr("Volume"),tools:qsTr("Playback, video tracks and tools"),subtitles:qsTr("Subtitles"),audio:qsTr("Audio and output device"),queue:qsTr("Current playback queue"),fullscreen:qsTr("Fullscreen"),speed:qsTr("Playback Speed"),forward10:qsTr("Forward 10s"),backward10:qsTr("Backward 10s"),forward15:qsTr("Forward 15s"),backward15:qsTr("Backward 15s"),stop:qsTr("Stop"),repeat:qsTr("Repeat"),shuffle:qsTr("Shuffle"),record:qsTr("Record"),snapshot:qsTr("Snapshot"),pip:qsTr("Picture in Picture"),hdr:qsTr("HDR — managed by the video output"),zoom:qsTr("Zoom"),sidebar:qsTr("Right Sidebar"),quit:qsTr("Quit VLC"),settings:qsTr("VLC Settings"),home:qsTr("Go Home"),thumbnail:qsTr("Thumbnail"),properties:qsTr("Properties"),replay:qsTr("Replay"),chapters:qsTr("Chapters"),bookmark:qsTr("Bookmark"),bookmarks:qsTr("Bookmarks"),playlists:qsTr("Playlists"),spacer:qsTr("Spacer"),divider:qsTr("Divider")})
    readonly property var glyphs:({more:"more",browser:"sidebar",folder:"folder",previous:"previous",play:Player.playingState===Player.PLAYING_STATE_PLAYING?"pause":"play",next:"next",mute:Player.muted?"muted":"volume",tools:"tools",subtitles:"subtitles",audio:"audio",queue:"queue",fullscreen:"fullscreen",speed:"speed",forward10:"forward10",backward10:"backward10",forward15:"forward15",backward15:"backward15",stop:"stop",repeat:"repeat",shuffle:"shuffle",record:"settings-recording",snapshot:"snapshot",pip:"pip",hdr:"hdr",zoom:"zoom",sidebar:"sidebar",quit:"quit",settings:"tools",home:"home",properties:"settings-info",replay:"replay",chapters:"chapters",bookmark:"bookmark",bookmarks:"bookmarks",playlists:"library-playlists"})
    readonly property var ids:({more:"playerMainMenu",browser:"mediaBrowserButton",folder:"openFileButton",filename:"playerMediaTitle",previous:"previousButton",play:"playButton",next:"nextButton",elapsed:"playerElapsedTime",seek:"progressSlider",mute:"muteButton",volume:"volumeSlider",tools:"toolsButton",subtitles:"subtitleButton",audio:"audioButton",queue:"playqueueToggle",fullscreen:"fullscreenButton"})
    readonly property string label:labels[controlKey]||controlKey
    readonly property string glyph:glyphs[controlKey]||"settings-info"
    readonly property bool expands:controlKey==="seek"||controlKey==="spacer"
    readonly property bool hidden:compact&&(controlKey==="elapsed"||controlKey==="duration"||controlKey==="artist"||controlKey==="playlistname")
    sourceComponent:controlKey==="seek"?seekComponent:controlKey==="volume"?volumeComponent:
        controlKey==="divider"?dividerComponent:controlKey==="spacer"?spacerComponent:
        controlKey==="thumbnail"?artComponent:["elapsed","duration","filename","artist","playlistname"].includes(controlKey)?textComponent:
        controlKey==="folder"?folderComponent:buttonComponent
    function trigger(invoker) {
        switch(controlKey){
        case "previous":MainPlaylistController.prev();break
        case "play":MainPlaylistController.togglePlayPause();break
        case "next":MainPlaylistController.next();break
        case "mute":Player.muted=!Player.muted;break
        case "fullscreen":Player.toggleFullscreen();break
        case "stop":MainPlaylistController.stop();break
        case "shuffle":MainPlaylistController.toggleRandom();break
        case "repeat":MainPlaylistController.toggleRepeatMode();break
        case "record":Player.toggleRecord();break
        case "snapshot":Player.snapshot();break
        case "replay":Player.position=0;break
        case "bookmark":MainCtx.addBookmark();break
        case "quit":DialogsProvider.quit();break
        case "settings":DialogsProvider.prefsDialog();break
        case "properties":DialogsProvider.mediaInfoDialog();break
        case "forward10":case "backward10":case "forward15":case "backward15":
            if(Player.length.valid())Player.position=Math.max(0,Math.min(1,Player.position+(controlKey.startsWith("backward")?-1:1)*(controlKey.endsWith("15")?15:10)/Player.length.toSeconds()));break
        default:actionRequested(controlKey,invoker)
        }
    }
    Component {
        id:buttonComponent
        PlayerIconButton {
            glyph:control.glyph;description:control.controlKey==="play"?(Player.playingState===Player.PLAYING_STATE_PLAYING?qsTr("Pause"):qsTr("Play")):control.controlKey==="mute"?(Player.muted?qsTr("Unmute"):qsTr("Mute")):control.label
            AccessibleCompat.id:control.topBar&&control.controlKey==="more"?"topBarMenuButton":control.ids[control.controlKey]||"layoutAction-"+control.controlKey
            checked:control.controlKey==="shuffle"?MainPlaylistController.random:control.controlKey==="repeat"?MainPlaylistController.repeatMode!==PlaylistController.PLAYBACK_REPEAT_NONE:control.controlKey==="record"?Player.recording:!!control.checkedControls[control.controlKey]
            accented:control.controlKey==="play"
            implicitWidth:PlayerStyle.px(control.controlKey==="play"?(control.compact?40:54):control.controlKey==="fullscreen"?36:control.controlKey==="mute"?24:control.topBar&&["more","browser"].includes(control.controlKey)?28:30)
            implicitHeight:PlayerStyle.px(28)
            enabled:control.controlKey==="previous"?MainPlaylistController.hasPrev:control.controlKey==="next"?MainPlaylistController.hasNext:
                control.controlKey==="play"?!MainPlaylistController.empty:control.controlKey==="hdr"?false:
                control.controlKey==="record"?Player.isStarted:control.controlKey==="bookmark"?(MainCtx.bookmarks?.available??false)&&Player.seekable:
                control.controlKey==="pip"?MainCtx.canShowVideoPIP&&Player.hasVideoOutput:
                control.controlKey==="zoom"||control.controlKey==="snapshot"?Player.hasVideoOutput:
                ["forward10","backward10","forward15","backward15","replay"].includes(control.controlKey)?Player.seekable:true
            onClicked:control.trigger(this)
            DropArea {
                anchors.fill:parent;enabled:control.controlKey==="queue"&&!PlayerCustomization.editing
                onEntered:drag=>{if(drag.hasUrls)control.actionRequested("showQueue",parent)}
                onDropped:drop=>{if(drop.hasUrls){MainPlaylistController.append(drop.urls,false);drop.acceptProposedAction()}}
            }
        }
    }
    Component {
        id:textComponent
        T.Button {
            id:textButton
            implicitWidth:PlayerStyle.px(["elapsed","duration"].includes(control.controlKey)?76:180)
            implicitHeight:PlayerStyle.px(28);padding:0;activeFocusOnTab:control.controlKey==="duration"
            AccessibleCompat.id:control.ids[control.controlKey]||"layoutAction-"+control.controlKey
            text:control.controlKey==="elapsed"?Player.time.formatHMS(0):control.controlKey==="duration"?(MainCtx.showRemainingTime?Player.remainingTime.formatHMS(0):Player.length.valid()?Player.length.formatHMS(0):"—:—"):
                control.controlKey==="artist"?Player.artist:control.controlKey==="playlistname"?qsTr("Play Queue"):Player.name
            Accessible.name:text
            contentItem:Text {
                text:textButton.text
                color:PlayerStyle.foreground;font.family:PlayerStyle.fontFamily;font.pixelSize:PlayerStyle.px(14)
                horizontalAlignment:Text.AlignHCenter;verticalAlignment:Text.AlignVCenter;elide:Text.ElideRight;textFormat:Text.PlainText
            }
            background:Rectangle{color:"transparent";border.width:textButton.visualFocus?2:0;border.color:PlayerStyle.accent;radius:PlayerStyle.px(4)}
            onClicked:if(control.controlKey==="duration")MainCtx.showRemainingTime=!MainCtx.showRemainingTime
        }
    }
    Component {
        id:folderComponent
        T.Button {
            id:folderButton;implicitWidth:PlayerStyle.px(28)+(control.compact?0:PlayerStyle.px(4)+Math.min(PlayerStyle.px(110),folderLabel.implicitWidth));implicitHeight:PlayerStyle.px(28);padding:0;activeFocusOnTab:true
            Accessible.name:qsTr("Browse current media folder");AccessibleCompat.id:"openFileButton"
            contentItem:RowLayout{spacing:PlayerStyle.px(4)
                IconImage{source:"qrc:/redesign/icons/folder.svg";color:PlayerStyle.foreground;sourceSize:Qt.size(PlayerStyle.px(24),PlayerStyle.px(24));Layout.preferredWidth:PlayerStyle.px(28);Layout.preferredHeight:PlayerStyle.px(28)}
                Text{id:folderLabel;visible:!control.compact;Layout.fillWidth:true;text:Player.sourceLocationName;elide:Text.ElideRight;color:PlayerStyle.foreground;font.family:PlayerStyle.fontFamily;font.pixelSize:PlayerStyle.px(14)}
            }
            background:Rectangle{color:"transparent";border.width:folderButton.visualFocus?2:0;border.color:PlayerStyle.accent;radius:PlayerStyle.px(4)}
            onClicked:control.actionRequested("folder",this)
        }
    }
    Component { id:dividerComponent;Item{implicitWidth:PlayerStyle.px(24);implicitHeight:PlayerStyle.px(28);Rectangle{anchors.centerIn:parent;width:PlayerStyle.px(1);height:PlayerStyle.px(20);color:PlayerStyle.foreground;opacity:0.3}} }
    Component { id:spacerComponent;Item{implicitWidth:PlayerStyle.px(40);implicitHeight:PlayerStyle.px(28)} }
    Component { id:artComponent;Item{implicitWidth:PlayerStyle.px(28);implicitHeight:PlayerStyle.px(28);Accessible.name:qsTr("Current media artwork");Image{anchors.fill:parent;source:Player.artwork;fillMode:Image.PreserveAspectFit}} }
    Component {
        id:seekComponent
        T.Slider {
            id:seek;implicitWidth:PlayerStyle.px(80);implicitHeight:PlayerStyle.px(28);padding:PlayerStyle.px(2);from:0;to:1
            enabled:Player.seekable;activeFocusOnTab:true
            Accessible.name:qsTr("Playback position");Accessible.description:Player.time.formatHMS(0)+" / "+Player.length.formatHMS(0);AccessibleCompat.id:"progressSlider"
            Binding on value{when:!seek.pressed;value:Player.position;restoreMode:Binding.RestoreNone}
            onMoved:Player.position=value
            PlayerSeekAnalysis{overlayParent:control.popupParent}
            background:Rectangle{color:PlayerStyle.timeline;radius:PlayerStyle.px(6)
                Rectangle{x:PlayerStyle.px(2);y:x;width:Math.max(0,(parent.width-PlayerStyle.px(4))*seek.visualPosition);height:parent.height-PlayerStyle.px(4);color:PlayerStyle.accent;opacity:0.24;radius:PlayerStyle.px(4)}
                border.width:seek.visualFocus?PlayerStyle.px(2):0;border.color:PlayerStyle.accent}
            handle:Rectangle{x:seek.leftPadding+seek.visualPosition*(seek.availableWidth-width);y:seek.topPadding;width:PlayerStyle.px(8);height:seek.availableHeight;radius:PlayerStyle.px(4);color:PlayerStyle.accent}
        }
    }
    Component {
        id:volumeComponent
        T.Slider {
            id:volume;implicitWidth:PlayerStyle.px(control.compact?48:88);implicitHeight:PlayerStyle.px(28);padding:0;from:0;to:MainCtx.maxVolume/100;stepSize:0.05;activeFocusOnTab:true
            Accessible.name:qsTr("Volume");Accessible.description:qsTr("%1 percent").arg(Math.round(Player.volume*100));AccessibleCompat.id:"volumeSlider"
            Binding on value{when:!volume.pressed;value:Player.volume;restoreMode:Binding.RestoreNone}
            onMoved:{Player.volume=value;Player.muted=false}
            handle:Item{}
            background:Item{clip:true;opacity:Player.muted?0.45:1
                IconImage{width:volume.width*89/88;height:volume.height;sourceSize:Qt.size(width,height);source:"qrc:/redesign/icons/volume-cone.svg";color:PlayerStyle.dark?"#090909":"#888888"}
                Item{width:parent.width*volume.position;height:parent.height;clip:true;Image{width:volume.width*89/88;height:volume.height;sourceSize:Qt.size(width,height);source:"qrc:/redesign/icons/volume-level.svg"}}
                Rectangle{anchors.fill:parent;color:"transparent";border.color:PlayerStyle.accent;border.width:volume.visualFocus?PlayerStyle.px(2):0;radius:PlayerStyle.px(4)}
            }
        }
    }
}
