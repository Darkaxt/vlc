// SPDX-License-Identifier: GPL-2.0-or-later
// In-place editor: the actual player controls remain the drag destinations.
import QtQuick
import QtQuick.Layouts
import QtQuick.Templates as T
import QtQuick.Controls.impl
import VLC.MainInterface
import VLC.Util
import "PlayerLayoutRules.js" as Rules

Item {
    id:editor
    visible:PlayerCustomization.editing
    property string selectedControl:"spacer"
    readonly property var paletteText:({speed:qsTr("Playback\nSpeed"),forward10:qsTr("Forward\n10s"),backward10:qsTr("Backward\n10s"),forward15:qsTr("Forward\n15s"),backward15:qsTr("Backward\n15s"),pip:qsTr("Picture in\nPicture"),sidebar:qsTr("Right\nSidebar"),playlistname:qsTr("Playlist\nName")})
    function removeDropped(zone,index){PlayerCustomization.remove(zone,index)}
    readonly property var available:Rules.palette.concat(Rules.controls.filter(key=>Rules.palette.indexOf(key)<0&&!PlayerCustomization.contains(key)))
    PlayerLayoutControl{id:catalog;controlKey:"divider";visible:false}
    Rectangle{anchors.fill:parent;color:"black";opacity:0.25}
    T.Popup {
        id:panel
        readonly property bool wide:width>=PlayerStyle.px(800)
        parent:editor.parent
        visible:PlayerCustomization.editing
        modal:false
        focus:true
        closePolicy:T.Popup.NoAutoClose
        onOpened:PlayerCustomization.dragOverlay=contentItem.parent
        onClosed:PlayerCustomization.dragOverlay=null
        width:Math.min(PlayerStyle.px(1048),parent.width-PlayerStyle.px(40))
        height:Math.min(PlayerStyle.px(655),parent.height-PlayerStyle.px(180))
        x:(parent.width-width)/2
        y:Math.max(PlayerStyle.px(20),(parent.height-height)/2-PlayerStyle.px(23))
        padding:0
        // The popup lives in Qt's window overlay, outside the captured player.
        // This reuses the existing native-video/UI blur without self-capture.
        background:LibraryGlass {
            id:glass
            backgroundSource:editor.parent
            active:panel.opened
            Rectangle {
                width:parent.width;height:heading.height;radius:PlayerStyle.px(14)
                color:PlayerStyle.timeline
                Rectangle{anchors.bottom:parent.bottom;width:parent.width;height:PlayerStyle.px(14);color:parent.color}
            }
            DropArea {
                anchors.fill:parent;keys:["vlc-customization"]
                onDropped:drop=>{if(drop.source.zone!=="palette"){Qt.callLater(editor.removeDropped,drop.source.zone,drop.source.controlIndex);drop.acceptProposedAction()}}
            }
        }
        contentItem:ColumnLayout {
            readonly property bool ready:glass.ready
            Accessible.name:qsTr("Customize Player");AccessibleCompat.id:"playerLayoutEditor"
            Keys.onEscapePressed:event=>{PlayerCustomization.cancel();event.accepted=true}
            spacing:0
            Item {
                id:heading
                Layout.fillWidth:true
                implicitHeight:headingLayout.implicitHeight+PlayerStyle.px(18)
                ColumnLayout {
                    id:headingLayout;anchors.fill:parent;anchors.margins:PlayerStyle.px(9);spacing:PlayerStyle.px(12)
                    RowLayout {
                        Layout.fillWidth:true;Layout.preferredHeight:PlayerStyle.px(32);spacing:0
                        Text{text:qsTr("Customize Player");color:PlayerStyle.foreground;font.family:PlayerStyle.fontFamily;font.pixelSize:PlayerStyle.px(14);Layout.fillWidth:true;Layout.leftMargin:PlayerStyle.px(10)}
                        PlayerIconButton{glyph:"close";implicitWidth:PlayerStyle.px(32);implicitHeight:PlayerStyle.px(32);description:qsTr("Cancel customization");onClicked:PlayerCustomization.cancel()}
                    }
                    Text{Layout.fillWidth:true;Layout.leftMargin:PlayerStyle.px(10);Layout.rightMargin:PlayerStyle.px(10);Layout.preferredHeight:Math.max(PlayerStyle.px(32),implicitHeight);text:qsTr("Drag items around and out of the box below to re-order them. Drag items into the box to remove them from the player.");color:PlayerStyle.foreground;font.family:PlayerStyle.fontFamily;font.pixelSize:PlayerStyle.px(14);wrapMode:Text.WordWrap;verticalAlignment:Text.AlignVCenter}
                }
            }
            Flickable {
                id:palette;Layout.fillWidth:true;Layout.fillHeight:true;Layout.margins:PlayerStyle.px(34);clip:true;contentHeight:grid.implicitHeight
                function reveal(item){const point=item.mapToItem(contentItem,0,0);if(point.y<contentY)contentY=Math.max(0,point.y);else if(point.y+item.height>contentY+height)contentY=Math.max(0,Math.min(contentHeight-height,point.y+item.height-height))}
                GridLayout {
                    id:grid;columns:Math.max(2,Math.floor((palette.width+PlayerStyle.px(24))/PlayerStyle.px(110)));columnSpacing:PlayerStyle.px(24);rowSpacing:PlayerStyle.px(38)
                    Repeater {
                        model:editor.available
                        delegate:PlayerLayoutDrag {
                            id:choice;required property string modelData
                            controlKey:modelData;controlIndex:modelData;zone:"palette";label:modelData==="hdr"?qsTr("HDR"):catalog.labels[modelData]||modelData
                            readonly property bool smallIcon:["forward15","backward15","quit","settings","home","thumbnail","filename","artist","folder","playlistname","properties","replay","chapters","bookmarks"].includes(modelData)
                            readonly property real iconHeight:PlayerStyle.px(smallIcon?28:32)
                            readonly property real iconWidth:PlayerStyle.px(["spacer","divider"].includes(modelData)?24:modelData==="sidebar"?32:smallIcon?28:30)
                            overlayParent:editor.parent;Layout.preferredWidth:PlayerStyle.px(86);Layout.minimumWidth:PlayerStyle.px(86);Layout.maximumWidth:PlayerStyle.px(86);Layout.preferredHeight:tile.implicitHeight;Layout.alignment:Qt.AlignTop
                            onSelected:editor.selectedControl=modelData
                            onFocusEntered:palette.reveal(choice)
                            Column {
                                id:tile;width:parent.width;spacing:PlayerStyle.px(16)
                                Item {
                                    anchors.horizontalCenter:parent.horizontalCenter;width:choice.iconWidth;height:choice.iconHeight
                                    Rectangle{anchors.fill:parent;color:choice.modelData==="thumbnail"?PlayerStyle.hover:"transparent";border.width:PlayerStyle.px(1);border.color:PlayerStyle.sectionForeground}
                                    Rectangle{anchors.centerIn:parent;width:PlayerStyle.px(1);height:PlayerStyle.px(24);color:PlayerStyle.foreground;visible:choice.modelData==="divider"}
                                    IconImage{anchors.centerIn:parent;width:PlayerStyle.px(24);height:width;visible:!["spacer","divider","thumbnail"].includes(choice.modelData);source:"qrc:/redesign/icons/"+(["filename","artist","folder","playlistname"].includes(choice.modelData)?"settings-info":catalog.glyphs[choice.modelData]||"settings-info")+".svg";color:PlayerStyle.foreground;sourceSize:Qt.size(width,height)}
                                }
                                Text{width:parent.width;text:editor.paletteText[choice.modelData]||choice.label;horizontalAlignment:Text.AlignHCenter;color:PlayerStyle.foreground;font.family:PlayerStyle.fontFamily;font.pixelSize:PlayerStyle.px(14);wrapMode:Text.WordWrap;textFormat:Text.PlainText}
                            }
                            Rectangle{anchors.fill:parent;visible:editor.selectedControl===choice.modelData;color:"transparent";border.width:PlayerStyle.px(2);border.color:PlayerStyle.accent;radius:PlayerStyle.px(6)}
                        }
                    }
                }
            }
            Text{Layout.fillWidth:true;Layout.leftMargin:PlayerStyle.px(20);Layout.rightMargin:PlayerStyle.px(20);visible:PlayerCustomization.saveError!=="";text:PlayerCustomization.saveError;color:PlayerStyle.foreground;font.family:PlayerStyle.fontFamily;font.pixelSize:PlayerStyle.px(14);wrapMode:Text.WordWrap;AccessibleCompat.id:"customizationStatus"}
            GridLayout {
                Layout.fillWidth:true;Layout.margins:PlayerStyle.px(20);columnSpacing:PlayerStyle.px(8);rowSpacing:PlayerStyle.px(8)
                columns:panel.wide?6:3
                PlayerSetupButton{Layout.row:0;Layout.column:0;text:qsTr("Cancel");AccessibleCompat.id:"layoutCancel";onClicked:PlayerCustomization.cancel()}
                PlayerSetupButton{Layout.row:0;Layout.column:1;text:qsTr("Reset Layout");AccessibleCompat.id:"layoutReset";onClicked:PlayerCustomization.reset()}
                Item{visible:panel.wide;Layout.row:0;Layout.column:2;Layout.fillWidth:true}
                T.ComboBox {
                    Layout.row:panel.wide?0:1;Layout.column:panel.wide?3:0;Layout.columnSpan:panel.wide?1:2;Layout.fillWidth:!panel.wide
                    id:target;model:[qsTr("Top left"),qsTr("Top center"),qsTr("Top right"),qsTr("Bottom left"),qsTr("Bottom center"),qsTr("Bottom right")];currentIndex:5
                    implicitWidth:PlayerStyle.px(140);implicitHeight:PlayerStyle.px(32);activeFocusOnTab:true
                    Accessible.name:qsTr("Control insertion area");AccessibleCompat.id:"layoutInsertionArea"
                    contentItem:Text{text:target.displayText;color:PlayerStyle.foreground;font.family:PlayerStyle.fontFamily;font.pixelSize:PlayerStyle.px(14);verticalAlignment:Text.AlignVCenter;leftPadding:PlayerStyle.px(8)}
                    background:Rectangle{color:PlayerStyle.chrome;radius:PlayerStyle.px(6);border.width:target.visualFocus?2:0;border.color:PlayerStyle.accent}
                    delegate:T.ItemDelegate{required property string modelData;width:target.width;text:modelData;contentItem:Text{text:parent.text;color:PlayerStyle.foreground;font.family:PlayerStyle.fontFamily;font.pixelSize:PlayerStyle.px(14)} background:Rectangle{color:parent.highlighted?PlayerStyle.hover:PlayerStyle.panel}}
                    popup:T.Popup{y:target.height;width:target.width;implicitHeight:contentItem.implicitHeight;padding:PlayerStyle.px(8);contentItem:ListView{clip:true;implicitHeight:contentHeight;model:target.popup.visible?target.delegateModel:null;currentIndex:target.highlightedIndex} background:Rectangle{color:PlayerStyle.panel;radius:PlayerStyle.px(6)}}
                }
                PlayerSetupButton{Layout.row:panel.wide?0:1;Layout.column:panel.wide?4:2;text:qsTr("Add Selected");AccessibleCompat.id:"layoutAddSelected";onClicked:PlayerCustomization.insert("palette",editor.selectedControl,Rules.zones[target.currentIndex],PlayerCustomization.layout[Rules.zones[target.currentIndex]].length)}
                PlayerSetupButton{Layout.row:0;Layout.column:panel.wide?5:2;text:qsTr("Save");tinted:true;AccessibleCompat.id:"layoutSave";onClicked:PlayerCustomization.save()}
            }
        }
    }
}
