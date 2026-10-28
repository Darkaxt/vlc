// SPDX-License-Identifier: GPL-2.0-or-later
import QtQuick
import QtQuick.Layouts
import VLC.Util

Item {
    id:strip
    required property string zone
    property bool compact:false
    property var checkedControls:({})
    property Item popupParent:parent
    property string alignment:"left"
    signal actionRequested(string key,var invoker)
    readonly property var controls:PlayerCustomization.layout[zone]
    function placeDropped(from,index,to,position){PlayerCustomization.insert(from,index,to,position)}
    implicitWidth:Math.max(PlayerCustomization.editing?PlayerStyle.px(60):0,row.implicitWidth)
    implicitHeight:PlayerStyle.px(32)
    Accessible.name:qsTr("Player layout area %1").arg(zone);AccessibleCompat.id:"layoutArea-"+zone
    Flickable {
        id:viewport;anchors.fill:parent;contentWidth:Math.max(width,row.implicitWidth);contentHeight:height;clip:true;interactive:contentWidth>width&&!PlayerCustomization.editing
        function reveal(item){const point=item.mapToItem(contentItem,0,0);if(point.x<contentX)contentX=Math.max(0,point.x);else if(point.x+item.width>contentX+width)contentX=Math.max(0,Math.min(contentWidth-width,point.x+item.width-width))}
        RowLayout {
            id:row;height:parent.height;width:Math.max(viewport.width,implicitWidth);spacing:PlayerStyle.px(strip.zone.startsWith("top")?0:8)
            Repeater {
                id:items;model:strip.controls
                delegate:PlayerLayoutDrag {
                    id:delegate;required property int index;required property string modelData
                    zone:strip.zone;controlIndex:index;controlKey:modelData;label:action.label;overlayParent:strip.popupParent
                    onFocusEntered:viewport.reveal(delegate)
                    visible:!action.hidden||PlayerCustomization.editing
                    Layout.fillWidth:action.expands||(strip.zone==="topCenter"&&modelData==="filename")
                    Layout.minimumWidth:PlayerStyle.px(action.expands?24:8)
                    Layout.preferredWidth:action.implicitWidth;Layout.maximumWidth:action.expands||strip.zone==="topCenter"?Infinity:action.implicitWidth
                    Layout.preferredHeight:PlayerStyle.px(28)
                    Layout.rightMargin:PlayerStyle.px(strip.zone.startsWith("top")?(modelData==="more"?10:0):strip.zone==="bottomRight"?modelData==="volume"||modelData==="audio"?12:modelData==="tools"||modelData==="subtitles"?4:0:0)
                    PlayerLayoutControl{id:action;anchors.fill:parent;controlKey:delegate.modelData;compact:strip.compact;topBar:strip.zone.startsWith("top");checkedControls:strip.checkedControls;popupParent:strip.popupParent;onActionRequested:(key,invoker)=>strip.actionRequested(key,invoker)}
                }
            }
        }
    }
    Rectangle{anchors.fill:parent;visible:PlayerCustomization.editing;color:"transparent";border.width:PlayerStyle.px(1);border.color:PlayerStyle.foreground;opacity:0.5}
    DropArea {
        id:target;anchors.fill:parent;enabled:PlayerCustomization.editing;keys:["vlc-customization"]
        property int insertion:0
        function locate(x){for(let i=0;i<items.count;i++){const item=items.itemAt(i);if(x+viewport.contentX<item.x+item.width/2)return i}return items.count}
        onEntered:drag=>insertion=locate(drag.x)
        onPositionChanged:drag=>insertion=locate(drag.x)
        onDropped:drop=>{Qt.callLater(strip.placeDropped,drop.source.zone,drop.source.controlIndex,strip.zone,insertion);drop.acceptProposedAction()}
    }
    Rectangle {
        visible:target.containsDrag;width:PlayerStyle.px(3);height:parent.height;color:PlayerStyle.accent
        x:target.insertion<items.count?items.itemAt(target.insertion).x-viewport.contentX:row.width-viewport.contentX-width
    }
}
