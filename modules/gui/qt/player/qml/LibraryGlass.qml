// SPDX-License-Identifier: GPL-2.0-or-later
// Shared frosted backgrounds from Figma's library context menus/network dialog.
import QtQuick
import QtQuick.Window
import VLC.MainInterface
import VLC.Player
import VLC.Widgets as Widgets

Rectangle {
    id: glass
    required property Item backgroundSource
    property bool active: false
    readonly property bool ready: !active || (effect.item !== null && effect.item.ready)
    readonly property real backgroundBlurRadius: PlayerStyle.px(50)
    readonly property real eDPR: MainCtx.effectiveDevicePixelRatio(Window.window) || 1
    readonly property real blurPadding: backgroundBlurRadius*1.5
    objectName: "playerVideoBackdrop"
    radius: PlayerStyle.px(14)
    color: PlayerStyle.dark ? Qt.rgba(14/255,14/255,14/255,0.95) : Qt.rgba(231/255,231/255,231/255,0.95)
    Widgets.RoundedRectangleShadow { color: Qt.rgba(0,0,0,0.46); yOffset: PlayerStyle.px(8); blurRadius: PlayerStyle.px(15); hollow: true; z: -2 }
    Loader {
        id: effect
        anchors.fill: parent
        z: -1 // Source blur stays beneath the specified translucent panel fill.
        // A closed popup has no texture consumer. Keep the blur chain owned by
        // the visible popup and its actual window, including view teardown.
        active: glass.active && !!glass.Window.window && !!glass.backgroundSource && glass.backgroundSource.Window.window === glass.Window.window
        sourceComponent: Item {
            // Qt 6.8 cached shaders can retain Uncompiled on their new manager;
            // resolved textures and absence of a shader error are authoritative.
            readonly property bool ready: blurredBackdrop.ready && roundedBackdrop.status === Image.Ready && roundedBackdrop.shaderStatus !== ShaderEffect.Error
            ShaderEffectSource {
                id: libraryBackdrop
                width: glass.width+glass.blurPadding*2; height: glass.height+glass.blurPadding*2
                sourceItem: glass.active ? glass.backgroundSource : null
                sourceRect: {
                    if (!sourceItem || !glass.parent) return Qt.rect(0,0,width,height)
                    // Track the popup item's placement as well as its size. mapToItem
                    // alone does not establish dependencies on ancestor transforms.
                    const geometry = [glass.x,glass.y,glass.width,glass.height,glass.parent.x,glass.parent.y,glass.parent.width,glass.parent.height,glass.backgroundSource.x,glass.backgroundSource.y,glass.backgroundSource.width,glass.backgroundSource.height]
                    const origin = glass.mapToItem(sourceItem,0,0)
                    return Qt.rect(origin.x-glass.blurPadding,origin.y-glass.blurPadding,width,height)
                }
                textureSize: Qt.size(Math.ceil(width*glass.eDPR),Math.ceil(height*glass.eDPR))
                live: glass.active; visible: false
            }
            Widgets.DualKawaseBlur {
                id: blurredBackdrop
                width: libraryBackdrop.width; height: libraryBackdrop.height
                source: libraryBackdrop; live: glass.active
                mode: Widgets.DualKawaseBlur.Mode.FourPass
                // Four-pass variance is (175/6)*(radius-0.5)^2. Match the source's
                // 50px backdrop radius (Gaussian sigma 25px), scaled by actual DPR.
                radius: Math.max(1,Math.round(0.5+glass.backgroundBlurRadius*glass.eDPR/2/Math.sqrt(175/6)))
            }
            ShaderEffectSource {
                id: blurredTexture
                width: glass.width; height: glass.height
                sourceItem: blurredBackdrop
                sourceRect: Qt.rect(glass.blurPadding,glass.blurPadding,width,height)
                textureSize: Qt.size(Math.ceil(width*glass.eDPR),Math.ceil(height*glass.eDPR))
                hideSource: true; live: glass.active; visible: false
            }
            Widgets.EnhancedImageExt { id: roundedBackdrop; anchors.fill: parent; targetTextureProvider: blurredTexture; radius: glass.radius; z: -1 }
        }
    }
}
