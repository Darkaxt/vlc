// SPDX-License-Identifier: GPL-2.0-or-later
import QtQuick
import QtQuick.Layouts
import QtQuick.Templates as T
import VLC.MainInterface
import VLC.Util

T.Popup {
    id: dialog
    width: Math.min(PlayerStyle.px(520),parent.width-PlayerStyle.px(40))
    height: Math.min(PlayerStyle.px(610),parent.height-PlayerStyle.px(40))
    x: (parent.width-width)/2; y: (parent.height-height)/2
    modal: true; focus: true; padding: PlayerStyle.px(20)
    visible: PlayerCustomization.profilesVisible
    onClosed: PlayerCustomization.profilesVisible=false
    background: Rectangle { color: PlayerStyle.panel; radius: PlayerStyle.px(14) }
    contentItem: ColumnLayout {
        spacing: PlayerStyle.px(16)
        RowLayout {
            Layout.fillWidth: true
            Text { text: qsTr("Profiles"); color: PlayerStyle.foreground; font.family: PlayerStyle.fontFamily; font.pixelSize: PlayerStyle.px(20); Layout.fillWidth: true }
            PlayerIconButton { glyph:"close";description:qsTr("Close profiles");onClicked:dialog.close() }
        }
        Text { text: qsTr("Save your player layout, theme, accent, Grid/List view and time display. Media and credentials are not included.");textFormat:Text.PlainText;wrapMode:Text.WordWrap;color:PlayerStyle.foreground;font.family:PlayerStyle.fontFamily;font.pixelSize:PlayerStyle.px(14);Layout.fillWidth:true }
        ListView {
            id: list
            Layout.fillWidth: true;Layout.fillHeight:true;clip:true;spacing:PlayerStyle.px(4)
            model:PlayerCustomization.profiles
            delegate: PlayerSetupButton {
                required property var modelData
                width:list.width;text:modelData.name;checked:PlayerCustomization.selected===modelData.name
                AccessibleCompat.id:"profile-"+modelData.name
                onClicked:PlayerCustomization.chooseProfile(modelData.name)
                background:Rectangle{color:parent.checked?PlayerStyle.hover:PlayerStyle.chrome;radius:PlayerStyle.px(6);border.width:parent.visualFocus?2:0;border.color:PlayerStyle.accent}
            }
            Text { visible:list.count===0;anchors.centerIn:parent;text:qsTr("No saved profiles yet");color:PlayerStyle.foreground;font.family:PlayerStyle.fontFamily;font.pixelSize:PlayerStyle.px(14) }
        }
        T.TextField {
            id:name
            Layout.fillWidth:true;implicitHeight:PlayerStyle.px(36);padding:PlayerStyle.px(8);selectByMouse:true
            placeholderText:qsTr("Profile name");color:PlayerStyle.foreground;placeholderTextColor:PlayerStyle.sectionForeground
            font.family:PlayerStyle.fontFamily;font.pixelSize:PlayerStyle.px(14);maximumLength:128
            Accessible.name:qsTr("Profile name");AccessibleCompat.id:"profileName"
            background:Rectangle{color:PlayerStyle.timeline;radius:PlayerStyle.px(4);border.width:name.activeFocus?2:1;border.color:PlayerStyle.accent}
            onAccepted:PlayerCustomization.createProfile(text)
        }
        Flow {
            Layout.fillWidth:true;spacing:PlayerStyle.px(8)
            PlayerSetupButton{text:qsTr("New");primary:true;enabled:PlayerCustomization.writable&&name.text.trim()!=="";AccessibleCompat.id:"profileNew";onClicked:PlayerCustomization.createProfile(name.text)}
            PlayerSetupButton{text:qsTr("Save Profile");enabled:!!PlayerCustomization.selected;AccessibleCompat.id:"profileSave";onClicked:PlayerCustomization.saveProfile()}
            PlayerSetupButton{text:qsTr("Restore");enabled:!!PlayerCustomization.selected;AccessibleCompat.id:"profileRestore";onClicked:PlayerCustomization.chooseProfile(PlayerCustomization.selected)}
            PlayerSetupButton{text:qsTr("Rename");enabled:!!PlayerCustomization.selected&&name.text.trim()!=="";AccessibleCompat.id:"profileRename";onClicked:PlayerCustomization.renameProfile(name.text)}
            PlayerSetupButton{text:qsTr("Delete");enabled:!!PlayerCustomization.selected;AccessibleCompat.id:"profileDelete";onClicked:PlayerCustomization.deleteProfile()}
        }
        Text { Layout.fillWidth:true;visible:text!=="";text:PlayerCustomization.error||PlayerCustomization.saveError;color:PlayerStyle.foreground;font.family:PlayerStyle.fontFamily;font.pixelSize:PlayerStyle.px(14);wrapMode:Text.WordWrap;AccessibleCompat.id:"profileStatus" }
    }
}
