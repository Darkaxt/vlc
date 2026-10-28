.pragma library
function defaults() {
    return {topLeft:['more','browser','divider','folder'],topCenter:['filename'],topRight:['fullscreen'],
            bottomLeft:['previous','play','next'],bottomCenter:['elapsed','seek','duration'],
            bottomRight:['mute','volume','tools','subtitles','audio','queue']}
}
var zones=['topLeft','topCenter','topRight','bottomLeft','bottomCenter','bottomRight']
var controls=['more','browser','divider','folder','filename','fullscreen','previous','play','next','elapsed','seek','duration',
              'mute','volume','tools','subtitles','audio','queue','spacer','speed','forward10','backward10','forward15','backward15',
              'stop','repeat','shuffle','record','snapshot','pip','hdr','zoom','sidebar','quit','settings','home','thumbnail','artist',
              'playlistname','properties','replay','chapters','bookmark','bookmarks','playlists']
var palette=['spacer','divider','speed','forward10','backward10','forward15','backward15','stop','repeat',
             'shuffle','record','snapshot','pip','hdr','zoom','sidebar','quit','settings',
             'home','thumbnail','filename','artist','folder','playlistname','properties','replay','chapters',
             'bookmark','bookmarks','playlists']
function copy(value) { return JSON.parse(JSON.stringify(value)) }
function exactKeys(value,keys) {
    return value && typeof value==='object' && !Array.isArray(value)
            && Object.keys(value).length===keys.length && keys.every(key=>Object.prototype.hasOwnProperty.call(value,key))
}
function validateLayout(layout) {
    if(!exactKeys(layout,zones))return false
    var seen={}
    for(var z=0;z<zones.length;++z){
        var list=layout[zones[z]]
        if(!Array.isArray(list)||list.length>64)return false
        for(var i=0;i<list.length;++i){
            var key=list[i]
            if(typeof key!=='string'||controls.indexOf(key)<0)return false
            if(key!=='spacer'&&key!=='divider'){
                if(seen[key])return false
                seen[key]=true
            }
        }
    }
    return true
}
function validateSettings(value) {
    return exactKeys(value,['theme','accent','grid','remaining']) && Number.isInteger(value.theme)
            && value.theme>=0 && value.theme<=2 && typeof value.accent==='string'
            && /^(system|default|#[0-9a-fA-F]{6})$/.test(value.accent)
            && typeof value.grid==='boolean' && typeof value.remaining==='boolean'
}
function validateStore(store) {
    if(!exactKeys(store,['version','layout','profiles','selected'])||store.version!==1||!validateLayout(store.layout)
            ||!Array.isArray(store.profiles)||store.profiles.length>32||typeof store.selected!=='string')return false
    var names=Object.create(null)
    for(var i=0;i<store.profiles.length;++i){
        var p=store.profiles[i]
        if(!exactKeys(p,['name','layout','settings'])||typeof p.name!=='string'||p.name.trim()!==p.name
                ||!p.name||p.name.length>128||Object.prototype.hasOwnProperty.call(names,p.name.toLowerCase())
                ||!validateLayout(p.layout)||!validateSettings(p.settings))return false
        names[p.name.toLowerCase()]=true
    }
    return store.selected===''||store.profiles.some(p=>p.name===store.selected)
}
function moveControl(layout,from,index,to,position) {
    if(!validateLayout(layout)||zones.indexOf(to)<0||!Number.isInteger(position)||position<0||position>layout[to].length)return null
    var next=copy(layout),key
    if(from==='palette'){
        key=index
        if(controls.indexOf(key)<0)return null
    }else{
        if(zones.indexOf(from)<0||!Number.isInteger(index)||index<0||index>=next[from].length)return null
        key=next[from].splice(index,1)[0]
        if(from===to && index<position)--position
    }
    next[to].splice(position,0,key)
    return validateLayout(next)?next:null
}
