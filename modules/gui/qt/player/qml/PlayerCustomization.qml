// SPDX-License-Identifier: GPL-2.0-or-later
pragma Singleton
import QtQuick
import VLC.MainInterface
import "PlayerLayoutRules.js" as Rules

QtObject {
    id: state
    readonly property string settingKey: "redesign/customization-v1"
    property var accepted: ({version:1,layout:Rules.defaults(),profiles:[],selected:""})
    property var draft: Rules.defaults()
    property bool editing: false
    readonly property var layout: editing ? draft : accepted.layout
    readonly property var profiles: accepted.profiles
    readonly property string selected: accepted.selected
    property string error: ""
    property string saveError: ""
    readonly property bool writable: error === ""
    property bool profilesVisible: false
    property bool onboardingVisible: false
    property bool onboardingSaving: false
    property var onboardingOriginal: ({})
    property string dragZone: ""
    property var dragIndex: -1
    property string dragKey: ""
    property bool dragging: false
    property Item dragOverlay: null
    property string focusZone: ""
    property int focusIndex: -1

    function persist(next,settings) {
        if(!writable)return false
        const encoded=JSON.stringify(next)
        if(!Rules.validateStore(next)||encoded.length>262144){saveError=qsTr("The layout or profiles cannot be saved. Check the control count and profile names.");return false}
        const failure=MainCtx.saveCustomization(encoded,settings || {})
        if(failure){saveError=failure;return false}
        accepted=next;saveError="";return true
    }
    function begin() { if(!writable){profilesVisible=true;return}focusZone="";focusIndex=-1;draft=Rules.copy(accepted.layout);editing=true }
    function cancel() { focusZone="";focusIndex=-1;dragging=false;editing=false;draft=Rules.copy(accepted.layout);saveError="" }
    function save() {
        const next=Rules.copy(accepted);next.layout=Rules.copy(draft)
        if(persist(next,{})){editing=false;dragging=false;return true}return false
    }
    function reset() { if(editing){focusZone="";focusIndex=-1;draft=Rules.defaults()} }
    function insert(from,index,to,position) {
        if(!editing)return false
        const next=Rules.moveControl(draft,from,index,to,position)
        if(!next){saveError=qsTr("This control is already placed, or this area is full.");return false}
        draft=next;saveError="";return true
    }
    function remove(zone,index) {
        if(!editing || !draft[zone] || index<0 || index>=draft[zone].length)return
        const next=Rules.copy(draft);next[zone].splice(index,1);draft=next
    }
    function contains(key) { return Rules.zones.some(zone=>layout[zone].indexOf(key)>=0) }
    function createProfile(name) {
        name=name.trim()
        const next=Rules.copy(accepted)
        next.profiles.push({name:name,layout:Rules.copy(accepted.layout),settings:MainCtx.presentationSettings()})
        next.selected=name;return persist(next,{})
    }
    function chooseProfile(name) {
        const profile=accepted.profiles.find(p=>p.name===name)
        if(!profile || editing)return false
        const next=Rules.copy(accepted);next.layout=Rules.copy(profile.layout);next.selected=name
        return persist(next,profile.settings)
    }
    function saveProfile() {
        const next=Rules.copy(accepted),profile=next.profiles.find(p=>p.name===selected)
        if(!profile)return false
        profile.layout=Rules.copy(accepted.layout);profile.settings=MainCtx.presentationSettings()
        return persist(next,{})
    }
    function renameProfile(name) {
        const next=Rules.copy(accepted),profile=next.profiles.find(p=>p.name===selected)
        if(!profile)return false
        name=name.trim();profile.name=name;next.selected=name;return persist(next,{})
    }
    function deleteProfile() {
        const next=Rules.copy(accepted);next.profiles=next.profiles.filter(p=>p.name!==selected);next.selected=""
        return persist(next,{})
    }
    function openOnboarding() {
        if(onboardingVisible)return
        onboardingOriginal=MainCtx.presentationSettings();onboardingVisible=true
    }
    function closeOnboarding(finish,theme,accent,folder) {
        const settings=Rules.copy(onboardingOriginal)
        if(finish){settings.theme=theme;settings.accent=accent}
        if(onboardingSaving)return false
        onboardingSaving=true
        MainCtx.finishRedesignOnboarding(finish,settings,finish?folder:"")
        return true
    }
    readonly property Connections requests: Connections {
        target: MainCtx
        function onCustomizePlayerRequested() { MainCtx.playerView=true;state.begin() }
        function onPlayerProfilesRequested() { state.profilesVisible=true }
        function onPlayerProfileSelected(name) { if(!state.writable)state.profilesVisible=true;else state.chooseProfile(name) }
        function onPlayerProfileSaveRequested() { if(!state.writable)state.profilesVisible=true;else state.saveProfile() }
        function onPlayerOnboardingRequested() { state.openOnboarding() }
        function onPlayerOnboardingFinished(error) {
            state.onboardingSaving=false
            state.saveError=error
            if(!error)state.onboardingVisible=false
        }
    }
    Component.onCompleted: {
        if(MainCtx.onboardingRequested)openOnboarding()
        if(!MainCtx.hasSetting(settingKey))return
        const raw=MainCtx.settingValue(settingKey,"")
        try{
            if(typeof raw!=="string"||raw.length>262144)throw new Error("size")
            const value=JSON.parse(raw)
            if(!Rules.validateStore(value))throw new Error("schema")
            accepted=value
        }catch(_){error=qsTr("Saved player customization could not be read. The original setting is preserved. Recover or remove only redesign/customization-v1 in your interface settings before editing.")}
    }
}
