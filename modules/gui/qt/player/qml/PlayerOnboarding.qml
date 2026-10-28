// SPDX-License-Identifier: GPL-2.0-or-later
// Saved Figma frames 1899:3055, 1902:3670 and 1902:6770, CC BY 4.0.
import QtQuick
import QtQuick.Layouts
import QtQuick.Templates as T
import QtQuick.Controls.impl
import VLC.MainInterface
import VLC.Util

T.Popup {
    id: dialog
    property Item previewItem: null
    property int page: 0
    property int theme: 0
    property string accent: "default"
    readonly property var swatches: ["#d37918","#e15032","#c49e23","#19a234","#18aad3","#185dd3","#8e42ff","#f052b3","#afafaf"]
    width: Math.min(PlayerStyle.px(1090), parent.width-PlayerStyle.px(40))
    height: Math.min(PlayerStyle.px(759), parent.height-PlayerStyle.px(40))
    x: (parent.width-width)/2
    y: (parent.height-height)/2
    padding: 0
    modal: true
    focus: true
    closePolicy: T.Popup.NoAutoClose
    visible: PlayerCustomization.onboardingVisible
    enabled: !PlayerCustomization.onboardingSaving
    onOpened: {
        page=0
        theme=PlayerCustomization.onboardingOriginal.theme
        accent=PlayerCustomization.onboardingOriginal.accent
        folder.text=""
    }
    onClosed: {
        if(PlayerCustomization.onboardingVisible&&!PlayerCustomization.onboardingSaving)
            PlayerCustomization.closeOnboarding(false,theme,accent,"")
    }
    background: Rectangle { color: PlayerStyle.panel; radius: PlayerStyle.px(14) }
    component Label: Text {
        color: PlayerStyle.foreground
        font.family: PlayerStyle.fontFamily
        font.pixelSize: PlayerStyle.px(16)
        textFormat: Text.PlainText
        wrapMode: Text.WordWrap
    }
    component SetupButton: PlayerSetupButton { fontPixelSize: 16 }
    contentItem: Item {
        Keys.onEscapePressed: event=>{
            PlayerCustomization.closeOnboarding(false,dialog.theme,dialog.accent,"")
            event.accepted=true
        }
        Flickable {
            id: body
            property Item focusedControl:null
            function reveal(item){
                focusedControl=item
                const point=item.mapToItem(contentItem,0,0)
                if(point.y<contentY)contentY=Math.max(0,point.y)
                else if(point.y+item.height>contentY+height)contentY=Math.max(0,Math.min(contentHeight-height,point.y+item.height-height))
            }
            onHeightChanged:if(focusedControl&&focusedControl.activeFocus)reveal(focusedControl)
            anchors { left: parent.left; right: parent.right; top: parent.top; bottom: footer.top; bottomMargin: PlayerStyle.px(12) }
            clip: true
            contentHeight: Math.max(height, pageContent.implicitHeight)
            Item {
                id: pageContent
                width: body.width
                implicitHeight: dialog.page===0?Math.max(PlayerStyle.px(625),folderGroup.y+folderGroup.implicitHeight+PlayerStyle.px(20)):dialog.page===1?PlayerStyle.px(615):shortcuts.y+shortcuts.implicitHeight+PlayerStyle.px(20)
                height: Math.max(body.height,implicitHeight)
                ShaderEffectSource {
                    visible: dialog.page===1
                    sourceItem: visible?dialog.previewItem:null
                    x: PlayerStyle.px(17); y: PlayerStyle.px(19)
                    width: parent.width-PlayerStyle.px(34); height: PlayerStyle.px(594)
                    live: visible
                    hideSource: false
                }
                Rectangle {
                    visible: dialog.page===1
                    x: PlayerStyle.px(17); y: PlayerStyle.px(19)
                    width: parent.width-PlayerStyle.px(34); height: PlayerStyle.px(594)
                    color: PlayerStyle.panel; opacity: 0.8
                }
                IconImage {
                    visible: dialog.page===0
                    anchors.horizontalCenter: parent.horizontalCenter
                    y: PlayerStyle.px(116)
                    width: PlayerStyle.px(141); height: width
                    sourceSize: Qt.size(width,height)
                    source: "qrc:/redesign/icons/vlc.svg"
                    color: PlayerStyle.accent
                }
                Label {
                    anchors.horizontalCenter: parent.horizontalCenter
                    width: parent.width-PlayerStyle.px(80)
                    y: PlayerStyle.px(dialog.page===0?286:dialog.page===1?173:60)
                    text: dialog.page===0?qsTr("Welcome to VLC!"):dialog.page===1?qsTr("Select your preferred theme and color."):qsTr("Learn the basic keyboard shortcuts.")
                    font.pixelSize: PlayerStyle.px(dialog.page===0?32:24)
                    font.weight: Font.Light
                    color: dialog.page===0&&PlayerStyle.dark?"#eaeaea":PlayerStyle.trackForeground
                    lineHeightMode: Text.FixedHeight
                    lineHeight: PlayerStyle.px(dialog.page===0?39:42)
                    height: Math.max(implicitHeight,PlayerStyle.px(dialog.page===0?39:42))
                    verticalAlignment: Text.AlignVCenter
                    horizontalAlignment: Text.AlignHCenter
                }
                Label {
                    id: introduction
                    visible: dialog.page===0
                    anchors.horizontalCenter: parent.horizontalCenter
                    y: PlayerStyle.px(362)
                    width: Math.min(PlayerStyle.px(595),parent.width-PlayerStyle.px(80))
                    color:PlayerStyle.trackForeground
                    font.weight:Font.Light
                    lineHeightMode:Text.FixedHeight
                    lineHeight:PlayerStyle.px(28)
                    height:Math.max(implicitHeight,lineCount*PlayerStyle.px(28))
                    text: qsTr("VLC is a free and open source cross-platform multimedia player and framework that plays most multimedia files as well as DVDs, Audio CDs, VCDs, and various streaming protocols.")
                }
                ColumnLayout {
                    id: folderGroup
                    visible: dialog.page===0
                    anchors.horizontalCenter: parent.horizontalCenter
                    y: Math.max(PlayerStyle.px(500),introduction.y+introduction.height+PlayerStyle.px(54))
                    width: Math.min(PlayerStyle.px(595),parent.width-PlayerStyle.px(80))
                    spacing: PlayerStyle.px(17)
                    Label { Layout.fillWidth: true; font.pixelSize: PlayerStyle.px(14); text: qsTr("Choose a Media Folder to get started with") }
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: PlayerStyle.px(10)
                        T.TextField {
                            id: folder
                            Layout.fillWidth: true
                            implicitHeight: PlayerStyle.px(35)
                            padding: PlayerStyle.px(8)
                            selectByMouse: true
                            color: PlayerStyle.foreground
                            placeholderTextColor: PlayerStyle.sectionForeground
                            placeholderText: qsTr("Optional media folder")
                            font.family: PlayerStyle.fontFamily
                            font.pixelSize: PlayerStyle.px(16)
                            Accessible.name: qsTr("Media folder")
                            AccessibleCompat.id: "onboardingFolder"
                            onActiveFocusChanged:if(activeFocus)body.reveal(folder)
                            background: Rectangle {
                                color: PlayerStyle.timeline; radius: PlayerStyle.px(4)
                                border.width: folder.activeFocus?2:1
                                border.color: folder.activeFocus?PlayerStyle.accent:PlayerStyle.hover
                            }
                        }
                        SetupButton {
                            id:browse
                            fontWeight:Font.Normal
                            Layout.preferredWidth:PlayerStyle.px(114)
                            implicitHeight:PlayerStyle.px(35)
                            text: qsTr("Browse")
                            onActiveFocusChanged:if(activeFocus)body.reveal(browse)
                            onClicked: { const choice=MainCtx.chooseOnboardingFolder(folder.text); if(choice)folder.text=choice }
                        }
                    }
                    Label {
                        Layout.fillWidth: true
                        font.pixelSize: PlayerStyle.px(12)
                        text: qsTr("No folder is scanned unless you choose one. Your existing network metadata and privacy choices stay unchanged.")
                    }
                }
                RowLayout {
                    visible: dialog.page===1
                    anchors.horizontalCenter: parent.horizontalCenter
                    y: PlayerStyle.px(286)
                    spacing: PlayerStyle.px(dialog.width>=PlayerStyle.px(600)?40:12)
                    Repeater {
                        model: [{label:qsTr("Light"),value:1,color:"#b0b0b0"},{label:qsTr("Dark"),value:2,color:"#222222"},{label:qsTr("System"),value:0,color:"#222222"}]
                        delegate: T.Button {
                            id: themeButton
                            required property var modelData
                            implicitWidth: PlayerStyle.px(116)
                            implicitHeight: PlayerStyle.px(157)
                            activeFocusOnTab: true
                            Accessible.name: modelData.label
                            AccessibleCompat.id: "onboardingTheme"+modelData.value
                            onActiveFocusChanged:if(activeFocus)body.reveal(themeButton)
                            contentItem: Item {
                                Rectangle {
                                    width: PlayerStyle.px(116); height: width
                                    radius: PlayerStyle.px(20)
                                    color: "transparent"
                                    border.width: dialog.theme===themeButton.modelData.value||themeButton.visualFocus?PlayerStyle.px(4):0
                                    border.color: PlayerStyle.accent
                                    Rectangle {
                                        id: tile
                                        anchors.fill: parent; anchors.margins: PlayerStyle.px(8)
                                        radius: PlayerStyle.px(12); color: themeButton.modelData.color
                                        Image {
                                            anchors.fill: parent
                                            visible: themeButton.modelData.value===0
                                            sourceSize:Qt.size(width,height)
                                            // The pinned QtQuick build omits Canvas. These two
                                            // half-corner arcs follow the source's 100px tile,
                                            // 12px corners and top-right diagonal light fill.
                                            source:"data:image/svg+xml,"+encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><path fill="#b0b0b0" d="M3.5147186 3.5147186A12 12 0 0 1 12 0H88A12 12 0 0 1 100 12V88A12 12 0 0 1 96.4852814 96.4852814Z"/></svg>')
                                        }
                                    }
                                }
                                Label { y: PlayerStyle.px(138); width: parent.width; text: themeButton.modelData.label; horizontalAlignment: Text.AlignHCenter }
                            }
                            background: Item {}
                            onClicked: { dialog.theme=modelData.value; MainCtx.previewAppearance(dialog.theme,dialog.accent) }
                        }
                    }
                }
                GridLayout {
                    id: shortcuts
                    visible: dialog.page===2
                    x: PlayerStyle.px(62); y: PlayerStyle.px(154)
                    width: parent.width-PlayerStyle.px(124)
                    columns: dialog.width>=PlayerStyle.px(800)?2:1
                    columnSpacing: PlayerStyle.px(100)
                    rowSpacing: PlayerStyle.px(38)
                    Repeater {
                        model: [{label:qsTr("Play / Pause"),key:"key-play-pause"},{label:qsTr("Toggle Fullscreen"),key:"key-fullscreen"},
                            {label:qsTr("Seek Backward / Forward"),key:"key-jump-short",pair:"key-jump+short"},{label:qsTr("Increase / Decrease Volume"),key:"key-vol-up",pair:"key-vol-down"},
                            {label:qsTr("Previous / Next Item"),key:"key-prev",pair:"key-next"},{label:qsTr("Show / Hide Queue"),key:"key-toggle-playlist"},
                            {label:qsTr("Previous / Next Frame"),key:"key-frame-previous",pair:"key-frame-next"},{label:qsTr("Show / Hide File Browser"),key:"redesign-browser"},
                            {label:qsTr("Cycle Subtitle Track"),key:"key-subtitle-track"},{label:qsTr("Take a Snapshot"),key:"key-snapshot"},
                            {label:qsTr("Cycle Audio Track"),key:"key-audio-track"},{label:qsTr("Record"),key:"key-record"}]
                        delegate: RowLayout {
                            required property var modelData
                            Layout.fillWidth: true
                            spacing: PlayerStyle.px(24)
                            Label { Layout.fillWidth: true; text: modelData.label }
                            Rectangle {
                                implicitWidth: Math.min(PlayerStyle.px(180),keyLabel.implicitWidth+PlayerStyle.px(28))
                                implicitHeight: PlayerStyle.px(44)
                                radius: PlayerStyle.px(12)
                                color: PlayerStyle.chrome; border.width: PlayerStyle.px(3); border.color: PlayerStyle.hover
                                Label {
                                    id: keyLabel
                                    anchors.fill: parent; anchors.margins: PlayerStyle.px(6)
                                    horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter
                                    elide: Text.ElideRight; wrapMode: Text.NoWrap
                                    text: MainCtx.shortcutLabel(modelData.key)+(modelData.pair?" / "+MainCtx.shortcutLabel(modelData.pair):"")
                                    Accessible.name: text
                                }
                            }
                        }
                    }
                }
            }
        }
        ColumnLayout {
            id: footer
            anchors { left: parent.left; right: parent.right; bottom: parent.bottom; leftMargin: PlayerStyle.px(dialog.page===1?41:62); rightMargin: PlayerStyle.px(62); bottomMargin: PlayerStyle.px(dialog.page===1?40:56) }
            spacing: PlayerStyle.px(10)
            Label { Layout.fillWidth: true; visible: PlayerCustomization.saveError!==""; text: PlayerCustomization.saveError; font.pixelSize: PlayerStyle.px(14); AccessibleCompat.id: "onboardingStatus" }
            RowLayout {
                Layout.fillWidth: true
                spacing:PlayerStyle.px(8)
                Flickable {
                id:colorViewport
                visible: dialog.page===1
                Layout.fillWidth: true
                implicitHeight:PlayerStyle.px(64)
                contentHeight:height
                contentWidth:colorRow.implicitWidth
                clip:true
                interactive:contentWidth>width
                function reveal(item){const point=item.mapToItem(contentItem,0,0);if(point.x<contentX)contentX=Math.max(0,point.x);else if(point.x+item.width>contentX+width)contentX=Math.max(0,Math.min(contentWidth-width,point.x+item.width-width))}
                Row {
                id:colorRow
                spacing: PlayerStyle.px(16)
                Repeater {
                    model: dialog.swatches
                    delegate: T.Button {
                        id: swatch
                        required property string modelData
                        implicitWidth: PlayerStyle.px(64); implicitHeight: PlayerStyle.px(64)
                        padding:PlayerStyle.px(12)
                        activeFocusOnTab: true
                        onActiveFocusChanged:if(activeFocus)colorViewport.reveal(swatch)
                        Accessible.name: qsTr("Accent %1").arg(modelData)
                        AccessibleCompat.id: "onboardingAccent"+modelData.slice(1)
                        contentItem: Rectangle { radius: width/2; color: swatch.modelData;opacity:dialog.accent===swatch.modelData||(dialog.accent==="default"&&swatch.modelData==="#d37918")?1:0.5 }
                        background: Rectangle {
                            color: "transparent"; radius: width/2
                            border.width: swatch.visualFocus||dialog.accent===swatch.modelData||(dialog.accent==="default"&&swatch.modelData==="#d37918")?PlayerStyle.px(4):0
                            border.color: swatch.visualFocus?PlayerStyle.accent:Qt.rgba(PlayerStyle.accent.r,PlayerStyle.accent.g,PlayerStyle.accent.b,0.3)
                        }
                        onClicked: { dialog.accent=modelData; MainCtx.previewAppearance(dialog.theme,dialog.accent) }
                    }
                }
                }
                }
                Label { visible: dialog.page===2; Layout.fillWidth: true; text: qsTr("Find the full list in the menu.") }
                Item { visible:dialog.page===0;Layout.fillWidth: true }
                SetupButton { visible: dialog.page>0; text: qsTr("Back"); onClicked: { dialog.page--; body.contentY=0 } }
                SetupButton {
                    text: dialog.page===2?qsTr("Finish"):qsTr("Next")
                    primary: true
                    AccessibleCompat.id: "onboardingNext"
                    onClicked: {
                        if(dialog.page<2){dialog.page++;body.contentY=0}
                        else PlayerCustomization.closeOnboarding(true,dialog.theme,dialog.accent,folder.text.trim())
                    }
                }
            }
        }
        Row {
            x:PlayerStyle.px(62);anchors.bottom:parent.bottom;anchors.bottomMargin:PlayerStyle.px(12);spacing:PlayerStyle.px(12)
            PlayerSetupButton { text: qsTr("Skip"); fontWeight:Font.Normal; implicitHeight:PlayerStyle.px(24);AccessibleCompat.id: "onboardingSkip"; onClicked: PlayerCustomization.closeOnboarding(false,dialog.theme,dialog.accent,"") }
            PlayerSetupButton { visible:dialog.page===1;text:qsTr("System accent");fontWeight:Font.Normal;implicitHeight:PlayerStyle.px(24);onClicked:{dialog.accent="system";MainCtx.previewAppearance(dialog.theme,dialog.accent)} }
        }
    }
}
