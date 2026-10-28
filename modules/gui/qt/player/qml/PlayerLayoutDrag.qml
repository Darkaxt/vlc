// SPDX-License-Identifier: GPL-2.0-or-later
import QtQuick
import VLC.Util
import "PlayerLayoutRules.js" as Rules

Item {
    id:root
    default property alias contents:slot.data
    required property string zone
    required property var controlIndex
    required property string controlKey
    property string label:controlKey
    property Item overlayParent:parent
    readonly property Item dragParent:PlayerCustomization.editing&&PlayerCustomization.dragOverlay?PlayerCustomization.dragOverlay:overlayParent
    property bool draggable:PlayerCustomization.editing
    signal selected()
    signal focusEntered()
    onActiveFocusChanged:if(activeFocus)focusEntered()
    function focusSelf(){forceActiveFocus(Qt.TabFocusReason)}
    function moveKeyboard(to,position){
        PlayerCustomization.focusZone=to
        PlayerCustomization.focusIndex=position-(zone===to&&controlIndex<position?1:0)
        if(!PlayerCustomization.insert(zone,controlIndex,to,position)){PlayerCustomization.focusZone="";PlayerCustomization.focusIndex=-1}
    }
    Component.onCompleted:if(PlayerCustomization.editing&&zone===PlayerCustomization.focusZone&&controlIndex===PlayerCustomization.focusIndex)Qt.callLater(focusSelf)
    activeFocusOnTab:draggable
    Accessible.role:Accessible.Button
    Accessible.ignored:!draggable
    Accessible.name:qsTr("Customize %1").arg(label)
    Accessible.description:qsTr("Drag to move, Delete to remove. Control+Left/Right reorders; Control+Up/Down changes area.")
    AccessibleCompat.id:"customize-"+zone+"-"+controlIndex
    Accessible.onPressAction:selected()
    Item{id:slot;anchors.fill:parent;enabled:!root.draggable}
    Rectangle{anchors.fill:parent;visible:root.draggable&&(root.zone!=="palette"||root.activeFocus);color:"transparent";border.width:root.activeFocus?2:1;border.color:root.activeFocus?PlayerStyle.accent:PlayerStyle.foreground;opacity:root.activeFocus?1:0.4}
    Keys.onPressed:event=>{
        if(!draggable)return
        if(event.key===Qt.Key_Return||event.key===Qt.Key_Enter){selected();event.accepted=true;return}
        if(event.key===Qt.Key_Delete&&zone!=="palette"){PlayerCustomization.remove(zone,controlIndex);event.accepted=true}
        else if(event.modifiers&Qt.ControlModifier){
            if(event.key===Qt.Key_Left||event.key===Qt.Key_Right){if(zone!=="palette")moveKeyboard(zone,Math.max(0,Math.min(PlayerCustomization.layout[zone].length,controlIndex+(event.key===Qt.Key_Left?-1:2))));event.accepted=true}
            else if(event.key===Qt.Key_Up||event.key===Qt.Key_Down){const next=(Rules.zones.indexOf(zone)+(event.key===Qt.Key_Up?5:1))%6;moveKeyboard(Rules.zones[next],PlayerCustomization.layout[Rules.zones[next]].length);event.accepted=true}
        }
    }
    TapHandler{enabled:root.draggable;onTapped:root.selected()}
    Rectangle {
        id:proxy;parent:root.dragParent;z:100;visible:dragger.active
        width:Math.max(PlayerStyle.px(100),labelText.implicitWidth+PlayerStyle.px(20));height:PlayerStyle.px(40)
        color:PlayerStyle.panel;radius:PlayerStyle.px(6);border.color:PlayerStyle.accent;border.width:PlayerStyle.px(2)
        Text{id:labelText;anchors.centerIn:parent;text:root.label;color:PlayerStyle.foreground;font.family:PlayerStyle.fontFamily;font.pixelSize:PlayerStyle.px(14)}
        Drag.source:root;Drag.keys:["vlc-customization"];Drag.hotSpot.x:width/2;Drag.hotSpot.y:height/2
    }
    DragHandler {
        id:dragger;enabled:root.draggable;target:proxy
        onActiveChanged:{
            if(active){const point=root.mapToItem(root.dragParent,centroid.position.x,centroid.position.y);proxy.x=point.x-proxy.width/2;proxy.y=point.y-proxy.height/2;PlayerCustomization.dragZone=root.zone;PlayerCustomization.dragIndex=root.controlIndex;PlayerCustomization.dragKey=root.controlKey;PlayerCustomization.dragging=true;proxy.Drag.active=true}
            else{proxy.Drag.drop();proxy.Drag.active=false;PlayerCustomization.dragging=false}
        }
    }
}
