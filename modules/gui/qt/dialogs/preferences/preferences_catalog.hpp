// SPDX-License-Identifier: GPL-2.0-or-later
// Ordered presentation contract for the original Figma settings frames.
// Keys retain VLC ownership; slash suffixes name views of one shared draft value.
#pragma once

namespace PreferencesCatalog
{
enum class Editor { Native, Slider, Toggle, Inverse, Policy, Filter, Choice, Action };
struct Row
{
    const char *key;
    int category;
    const char *group;
    const char *label;
    Editor editor = Editor::Native;
    const char *choices = nullptr;
    bool advanced = false;
    double minimum = 0;
    double maximum = 1;
    double step = 0;
    bool information = true;
    int editorHeight = 0; // Original-frame exception to the native control metric.
};
constexpr Row withoutInformation(Row row)
{
    row.information = false;
    return row;
}
constexpr Row withEditorHeight(Row row, int height)
{
    row.editorHeight = height;
    return row;
}
#define PREF(k,c,g,l) {k,c,g,l}
#define EDIT(k,c,g,l,e,v) {k,c,g,l,Editor::e,v}
#define SLIDE(k,c,g,l,a,b,s) {k,c,g,l,Editor::Slider,nullptr,false,a,b,s}
#define ACTION(k,c,g,l,b) {"@" k,c,g,l,Editor::Action,b}
#define ADV(k,c,g,l) {k,c,g,l,Editor::Native,nullptr,true}
#define ASLIDE(k,c,g,l,a,b,s) {k,c,g,l,Editor::Slider,nullptr,true,a,b,s}
inline constexpr Row rows[] = {
    withoutInformation(PREF("qt-accent-color",0,N_("Appearance"),N_("VLC accent color"))),
    withoutInformation(PREF("qt-mpv-accent-color",0,N_("Appearance"),N_("MPV accent color"))),
    PREF("interact",0,N_("Startup"),N_("Show confirmation and error dialogs")),
    PREF("qt-updates-notif",0,N_("Startup"),N_("Check for updates automatically")),
    PREF("qt-verbose",0,N_("Diagnostics"),N_("Developer messages")),
    PREF("file-logging",0,N_("Diagnostics"),N_("Save a log")),
    withEditorHeight(PREF("logfile",0,N_("Diagnostics"),N_("Log file")),36),
    PREF("log-verbose",0,N_("Diagnostics"),N_("Log details")),
    ADV("qt-error-dialogs",0,N_("Advanced Options"),N_("Show minor warnings")),
    ADV("extra-options",0,N_("Advanced Options"),N_("Additional command line options")),
    ADV("logmode",0,N_("Advanced Options"),N_("Log format")),
    ADV("stats",0,N_("Advanced Options"),N_("Collect playback statistics")),
    {"@config-folder",0,N_("Advanced Options"),N_("Open configurations folder"),Editor::Action,N_("Open"),true},
    {"@reset-preferences",0,N_("Advanced Options"),N_("Reset all settings"),Editor::Action,N_("Reset"),true},
    withoutInformation({"@vlc-commands",0,N_("Advanced Options"),N_("VLC commands"),Editor::Action,N_("Open"),true}),
    ADV("syslog",0,N_("Developer Options"),N_("Write to the system log")),
    ADV("syslog-debug",0,N_("Developer Options"),N_("Include debug messages in the system log")),
    ADV("syslog-ident",0,N_("Developer Options"),N_("System log identity")),
    ADV("syslog-facility",0,N_("Developer Options"),N_("System log facility")),

    EDIT("intf/skins2",1,N_("Skin"),N_("Use a custom skin"),Filter,"skins2"),
    withEditorHeight(PREF("skins2-last",1,N_("Skin"),N_("Skin file")),36),
    SLIDE("qt-background-blur-radius",1,N_("Appearance"),N_("Background blur"),0,100,25),
    PREF("embedded-video",1,N_("Window"),N_("Play video inside main window")),
    EDIT("qt-video-autoresize",1,N_("Window"),N_("Resize window to fit video"),Policy,"Never|Fit video within the screen"),
    withoutInformation(PREF("qt-remember-window",1,N_("Window"),N_("Remember window size and position"))),
    PREF("video-on-top",1,N_("Window"),N_("Keep window above other windows")),
    PREF("qt-titlebar",1,N_("Window"),N_("Show window decorations")),
    PREF("qt-name-in-title",1,N_("Window"),N_("Show the file name in the title bar")),
    EDIT("qt-fullscreen-screennumber",1,N_("Window"),N_("Open fullscreen on"),Choice,"fullscreen-screen"),
    PREF("qt-minimal-view",1,N_("Playback Controls"),N_("Start in compact mode")),
    PREF("qt-controls-visibility",1,N_("Playback Controls"),N_("Auto-hide the controls")),
    withEditorHeight(withoutInformation(SLIDE("mouse-hide-timeout",1,N_("Playback Controls"),N_("Hide after"),0,10000,1000)),47),
    PREF("qt-fs-controller",1,N_("Playback Controls"),N_("Show controls in fullscreen")),
    PREF("qt-system-tray",1,N_("Notifications and System Tray"),N_("Show a system tray icon")),
    PREF("qt-start-minimized",1,N_("Notifications and System Tray"),N_("Start minimized to the tray")),
    PREF("qt-notification",1,N_("Notifications and System Tray"),N_("Show a popup when the track changes")),
    withEditorHeight(withoutInformation(SLIDE("qt-notification-duration",1,N_("Notifications and System Tray"),N_("Popup duration"),0,10000,1000)),47),
    PREF("playlist-tree",1,N_("Playlist"),N_("Show the playlist as a tree")),
    withoutInformation(ASLIDE("qt-opacity",1,N_("Window"),N_("Window opacity"),0.1,1,0.45)),
    withoutInformation(ADV("qt-pause-minimized",1,N_("Window"),N_("Pause video when window is minimized"))),
    ADV("qt-auto-raise",1,N_("Window"),N_("Bring VLC to the front when playback starts")),
    withoutInformation(ADV("qt-audio-cover-art",1,N_("Window"),N_("Show cover art in the window when playing audio"))),
    withoutInformation(ADV("qt-embedded-open",1,N_("Window"),N_("Show the file browser inside the open dialog"))),
    withoutInformation(ADV("qt-icon-change",1,N_("Window"),N_("Allow the app icon to change"))),
    withoutInformation(ASLIDE("qt-fs-opacity",1,N_("Playback Controls"),N_("Fullscreen controls opacity"),0.1,1,0.45)),
    withoutInformation(ASLIDE("qt-fs-sensitivity",1,N_("Playback Controls"),N_("Fullscreen controls sensitivity"),0,4000,2000)),
    ADV("qt-close-to-system-tray",1,N_("Notifications and System Tray"),N_("Hide the window on close")),

    PREF("save-recentplay",2,N_("History"),N_("Save recently played items")),
    PREF("save-playback-position",2,N_("History"),N_("Remember the playback position")),
    PREF("history-exclude",2,N_("History"),N_("Never remember items matching")),
    ACTION("clear-history",2,N_("History"),N_("Clear history now"),N_("Clear")),
    PREF("metadata-network-access",2,N_("Network"),N_("Fetch titles and cover art from the internet")),
    EDIT("extraintf/audioscrobbler",2,N_("Network"),N_("Submit played tracks to Last.fm"),Filter,"audioscrobbler"),
    PREF("lastfm-username",2,N_("Network"),N_("Last.fm username")),
    PREF("lastfm-password",2,N_("Network"),N_("Last.fm password")),
    PREF("scrobbler-url",2,N_("Network"),N_("Last.fm submission URL")),

    withoutInformation(ACTION("shortcuts",3,N_("Keyboard Shortcuts"),N_("Defaults"),N_("Edit Keyboard Shortcuts"))),
    withoutInformation(ACTION("reset-shortcuts",3,N_("Keyboard Shortcuts"),N_("Reset all shortcuts"),N_("Reset"))),
    withoutInformation(PREF("extrashort-jump-size",3,N_("Skip Amounts"),N_("Very short skip"))),
    withoutInformation(PREF("short-jump-size",3,N_("Skip Amounts"),N_("Short skip"))),
    withoutInformation(PREF("medium-jump-size",3,N_("Skip Amounts"),N_("Medium skip"))),
    withoutInformation(PREF("long-jump-size",3,N_("Skip Amounts"),N_("Long skip"))),
    withoutInformation(PREF("mouse-pause-policy",3,N_("Mouse"),N_("Single click on the video"))),
    withoutInformation(PREF("qt-double-click-action",3,N_("Mouse"),N_("Double click on the video"))),
    withoutInformation(PREF("hotkeys-y-wheel-mode",3,N_("Mouse"),N_("Scroll wheel"))),
    withoutInformation(PREF("hotkeys-x-wheel-mode",3,N_("Mouse"),N_("Horizontal scroll"))),
    withoutInformation(PREF("qt-reverse-wheel",3,N_("Mouse"),N_("Reverse scroll direction"))),
    withoutInformation(EDIT("extraintf/http",3,N_("Remotes"),N_("Web remote control"),Filter,"http")),
    withoutInformation(PREF("http-port",3,N_("Remotes"),N_("Port"))),
    ADV("qt-disable-volume-keys",3,N_("Keyboard"),N_("Ignore the keyboard volume keys")),

    PREF("restore-playback-pos",4,N_("Startup"),N_("Continue where you left off")),
    EDIT("start-paused",4,N_("Startup"),N_("Start playing as soon as a file opens"),Inverse,nullptr),
    withoutInformation(SLIDE("rate",4,N_("Startup"),N_("Default playback speed"),0.25,2,0.25)),
    PREF("playlist-cork",4,N_("Startup"),N_("Pause when another app uses audio")),
    PREF("preferred-resolution",4,N_("Tracks"),N_("Preferred video quality")),
    PREF("menu-language",4,N_("Tracks"),N_("Preferred menu language")),
    withEditorHeight(PREF("audio-track",4,N_("Tracks"),N_("Default audio track")),36),
    withEditorHeight(PREF("sub-track",4,N_("Tracks"),N_("Default subtitle track")),36),
    EDIT("repeat/order",4,N_("Order"),N_("Repeat"),Choice,"repeat-policy"),
    PREF("random",4,N_("Order"),N_("Shuffle")),
    PREF("play-and-pause",4,N_("Order"),N_("Stop after each item")),
    EDIT("play-and-stop/finish",4,N_("Order"),N_("When playback finishes"),Choice,"finish-policy"),
    EDIT("input-fast-seek",4,N_("Seeking"),N_("Seek precisely"),Inverse,nullptr),
    PREF("qt-seek-preview",4,N_("Seeking"),N_("Show thumbnail while scrubbing")),
    withEditorHeight(PREF("dvd",4,N_("Files & Discs"),N_("Default optical drive")),36),
    PREF("avi-index",4,N_("Files & Discs"),N_("Repair damaged AVI files")),
    PREF("mkv-preload-local-dir",4,N_("Files & Discs"),N_("Load matching .mkv files from the same folder")),
    withEditorHeight(ADV("input-timeshift-path",4,N_("Files & Discs"),N_("Time-shift buffer folder")),32),
    {"input-timeshift-granularity",4,N_("Files & Discs"),N_("Time-shift buffer size"),Editor::Choice,"timeshift-size",true},
    ADV("qt-playback-engine",4,N_("Playback engine"),N_("Startup playback engine")),

    PREF("video",5,N_("Output"),N_("Enable video")),
    PREF("fullscreen",5,N_("Output"),N_("Start videos in fullscreen")),
    EDIT("disable-screensaver",5,N_("Output"),N_("Stop the screensaver during playback"),Toggle,nullptr),
    PREF("video-wallpaper",5,N_("Output"),N_("Play video as desktop wallpaper")),
    withoutInformation(SLIDE("hue",5,N_("Picture"),N_("Hue"),-180,180,60)),
    withoutInformation(SLIDE("brightness",5,N_("Picture"),N_("Brightness"),0,2,0.5)),
    withoutInformation(SLIDE("contrast",5,N_("Picture"),N_("Contrast"),0,2,0.5)),
    withoutInformation(SLIDE("saturation",5,N_("Picture"),N_("Saturation"),0,3,1)),
    withoutInformation(SLIDE("gamma",5,N_("Picture"),N_("Gamma"),0.01,10,2)),
    withoutInformation(ACTION("reset-picture",5,N_("Picture"),N_("Reset picture"),N_("Reset"))),
    PREF("deinterlace",5,N_("Deinterlacing"),N_("Deinterlacing")),
    PREF("deinterlace-mode",5,N_("Deinterlacing"),N_("Method")),
    EDIT("aspect-ratio",5,N_("Framing"),N_("Aspect ratio"),Choice,"aspect-ratio"),
    EDIT("crop",5,N_("Framing"),N_("Crop"),Choice,"crop-ratio"),
    PREF("autoscale",5,N_("Framing"),N_("Scale video to the window")),
    EDIT("zoom",5,N_("Framing"),N_("Zoom"),Choice,"zoom"),
    PREF("align",5,N_("Framing"),N_("Position in the window")),
    withEditorHeight(PREF("snapshot-path",5,N_("Snapshots"),N_("Save to")),32),
    withEditorHeight(PREF("snapshot-prefix",5,N_("Snapshots"),N_("File name prefix")),32),
    PREF("snapshot-format",5,N_("Snapshots"),N_("Format")),
    EDIT("snapshot-width/size",5,N_("Snapshots"),N_("Size"),Choice,"snapshot-size"),
    PREF("snapshot-sequential",5,N_("Snapshots"),N_("Number files sequentially")),
    PREF("snapshot-preview",5,N_("Snapshots"),N_("Show a preview after capture")),
    ADV("custom-aspect-ratios",5,N_("Framing"),N_("Custom aspect ratios")),
    ADV("custom-crop-ratios",5,N_("Framing"),N_("Custom crop ratios")),
    withEditorHeight(ADV("monitor-par",5,N_("Framing"),N_("Monitor pixel aspect ratio")),32),
    {"input-timeshift-granularity/video",5,N_("Buffering"),N_("Time-shift buffer size"),Editor::Choice,"timeshift-size",true},

    PREF("audio",6,N_("Output"),N_("Enable audio")),
    PREF("mmdevice-audio-device",6,N_("Output"),N_("Output device")),
    PREF("stereo-mode",6,N_("Output"),N_("Speaker setup")),
    withoutInformation(SLIDE("qt-max-volume",6,N_("Volume"),N_("Maximum volume"),100,300,100)),
    EDIT("volume-save/startup",6,N_("Volume"),N_("Startup volume"),Choice,"startup-volume"),
    PREF("volume-step",6,N_("Volume"),N_("Volume step")),
    EDIT("audio-filter/normvol",6,N_("Loudness"),N_("Normalize loudness"),Filter,"normvol"),
    PREF("norm-max-level",6,N_("Loudness"),N_("Target level")),
    EDIT("audio-filter/night",6,N_("Loudness"),N_("Night mode"),Filter,"night"),
    PREF("audio-replay-gain-mode",6,N_("Loudness"),N_("Replay gain")),
    PREF("audio-replay-gain-preamp",6,N_("Loudness"),N_("Replay gain preamp")),
    EDIT("audio-filter/equalizer",6,N_("Effects"),N_("Equalizer"),Filter,"equalizer"),
    PREF("equalizer-preset",6,N_("Effects"),N_("Equalizer preset")),
    withoutInformation(ACTION("equalizer",6,N_("Effects"),N_(""),N_("Open Equalizer"))),
    PREF("equalizer-2pass",6,N_("Effects"),N_("Two-pass")),
    EDIT("audio-filter/spatial",6,N_("Effects"),N_("Spatial audio"),Filter,"spatial"),
    EDIT("audio-filter/spatial-mode",6,N_("Effects"),N_("Spatial audio mode"),Choice,"spatial-mode"),
    EDIT("audio-filter/stereo_widen",6,N_("Effects"),N_("Stereo widening"),Filter,"stereo_widen"),
    EDIT("audio-filter/compressor",6,N_("Effects"),N_("Compressor"),Filter,"compressor"),
    withEditorHeight(PREF("pitch-shift",6,N_("Effects"),N_("Pitch shift")),32),
    EDIT("audio-filter/chorus_flanger",6,N_("Effects"),N_("Chorus/flanger"),Filter,"chorus_flanger"),
    EDIT("audio-filter/karaoke",6,N_("Effects"),N_("Karaoke"),Filter,"karaoke"),
    PREF("audio-language",6,N_("Tracks"),N_("Preferred audio language")),
    PREF("audio-desync",6,N_("Tracks"),N_("Audio delay")),
    PREF("audio-visual",6,N_("Visualization"),N_("Visualizer")),
    ADV("mmdevice-passthrough",6,N_("Output"),N_("Pass compressed audio to the receiver")),
    ADV("force-dolby-surround",6,N_("Output"),N_("Detect Dolby Surround")),
    ADV("audio-resampler",6,N_("Output"),N_("Resampling quality")),
    ADV("role",6,N_("Output"),N_("Media role")),
    {"qt-visualization-fit/size",6,N_("Visualization"),N_("Visualization size"),Editor::Policy,"Custom size|Match window",true},
    ADV("effect-width",6,N_("Visualization"),N_("Custom width")),
    ADV("effect-height",6,N_("Visualization"),N_("Custom height")),

    PREF("spu",7,N_("Tracks & Languages"),N_("Enable subtitles")),
    PREF("sub-language",7,N_("Tracks & Languages"),N_("Preferred language")),
    PREF("subsdec-encoding",7,N_("Tracks & Languages"),N_("Text encoding")),
    PREF("sub-autodetect-file",7,N_("Loading Subtitles"),N_("Load subtitle files automatically")),
    EDIT("sub-autodetect-fuzzy",7,N_("Loading Subtitles"),N_("File name matching"),Choice,"subtitle-match"),
    PREF("freetype-font",7,N_("Appearance"),N_("Font")),
    withEditorHeight(EDIT("freetype-absolute-fontsize/mode",7,N_("Appearance"),N_("Size values"),Choice,"font-size-mode"),36),
    withoutInformation(EDIT("sub-text-scale/size",7,N_("Appearance"),N_("Font size"),Choice,"font-size")),
    withoutInformation(PREF("freetype-bold",7,N_("Appearance"),N_("Bold"))),
    withoutInformation(PREF("freetype-color",7,N_("Appearance"),N_("Text color"))),
    withoutInformation(SLIDE("freetype-opacity",7,N_("Appearance"),N_("Text opacity"),0,255,127.5)),
    withoutInformation(EDIT("freetype-outline-thickness",7,N_("Appearance"),N_("Outline thickness"),Choice,"outline-thickness")),
    withoutInformation(PREF("freetype-outline-color",7,N_("Appearance"),N_("Outline color"))),
    withoutInformation(EDIT("freetype-shadow-opacity/enable",7,N_("Appearance"),N_("Shadow"),Toggle,nullptr)),
    withoutInformation(PREF("freetype-shadow-color",7,N_("Appearance"),N_("Shadow color"))),
    withoutInformation(EDIT("freetype-shadow-distance",7,N_("Appearance"),N_("Shadow distance"),Choice,"shadow-distance")),
    withoutInformation(EDIT("freetype-background-opacity/mode",7,N_("Appearance"),N_("Background"),Choice,"background-mode")),
    withoutInformation(PREF("freetype-background-color",7,N_("Appearance"),N_("Background color"))),
    withoutInformation(SLIDE("freetype-background-opacity",7,N_("Appearance"),N_("Background opacity"),0,255,127.5)),
    withoutInformation(PREF("sub-alignment",7,N_("Appearance"),N_("Vertical position"))),
    withoutInformation(SLIDE("sub-delay",7,N_("Timing"),N_("Subtitle delay"),-50,50,50)),
    PREF("qt-shortcut-feedback",7,N_("On-Screen Messages"),N_("Show feedback for shortcuts")),
    withoutInformation(SLIDE("qt-shortcut-feedback-duration",7,N_("On-Screen Messages"),N_("Show feedback for"),500,5000,2250)),
    PREF("video-title-show",7,N_("On-Screen Messages"),N_("Show filename when a video starts")),
    withoutInformation(SLIDE("video-title-timeout",7,N_("On-Screen Messages"),N_("Show filename for"),1000,10000,4500)),
    ADV("sub-autodetect-path",7,N_("Loading Subtitles"),N_("Load subtitles from these folders")),
    ADV("sub-ass-style-override",7,N_("Appearance"),N_("Ignore styling in ASS and SSA subtitles")),
    ADV("freetype-shadow-angle",7,N_("Appearance"),N_("Shadow angle")),
    ADV("freetype-text-direction",7,N_("Appearance"),N_("Text direction")),
    ADV("freetype-monofont",7,N_("Appearance"),N_("Monospace font")),
    ADV("qt-shortcut-feedback-key",7,N_("On-Screen Messages"),N_("Include the shortcut in feedback")),
    {"qt-visualization-fit/subtitle-size",7,N_("Visualization"),N_("Visualization size"),Editor::Policy,"Custom size|Match window",true},

    PREF("one-instance",8,N_("Opening Files"),N_("Only allow one VLC window")),
    PREF("one-instance-when-started-from-file",8,N_("Opening Files"),N_("Apply to files opened from the file manager")),
    PREF("playlist-enqueue",8,N_("Opening Files"),N_("Add to the playlist instead of replacing it")),
    PREF("recursive",8,N_("Opening Files"),N_("When opening a folder")),
    PREF("show-hiddenfiles",8,N_("Opening Files"),N_("Show hidden files")),
    EDIT("metadata-network-access/artwork",8,N_("Metadata & Artwork"),N_("Fetch titles and artwork"),Choice,"artwork-policy"),
    PREF("media-library",8,N_("Metadata & Artwork"),N_("Use the media library")),

    EDIT("network-caching/preset",9,N_("Buffering"),N_("Buffering"),Choice,"buffering-preset"),
    withoutInformation(PREF("file-caching",9,N_("Buffering"),N_("Local files"))),
    withoutInformation(PREF("disc-caching",9,N_("Buffering"),N_("Discs"))),
    withoutInformation(PREF("network-caching",9,N_("Buffering"),N_("Network streams"))),
    withoutInformation(PREF("live-caching",9,N_("Buffering"),N_("Live capture"))),
    PREF("http-proxy",9,N_("Proxy"),N_("HTTP proxy")),
    PREF("http-proxy-pwd",9,N_("Proxy"),N_("HTTP proxy password")),
    PREF("gnutls-system-trust",9,N_("Security"),N_("Verify certificates against the system trust store")),
    EDIT("gnutls-priorities",9,N_("Security"),N_("Cipher preference"),Choice,"cipher-policy"),

    PREF("dec-dev",10,N_("Decoding"),N_("Hardware-accelerated decoding")),
    EDIT("postproc-q",10,N_("Decoding"),N_("Video post-processing"),Choice,"postproc"),
    PREF("avcodec-skiploopfilter",10,N_("Decoding"),N_("Skip the H.264 loop filter")),
    PREF("avcodec-threads",10,N_("Decoding"),N_("Decoding threads")),
    withoutInformation(PREF("drop-late-frames",10,N_("Smooth Playback"),N_("Drop frames when the system cannot keep up"))),
    withoutInformation(PREF("high-priority",10,N_("Smooth Playback"),N_("High-priority playback"))),
    PREF("qt-process-priority",10,N_("Smooth Playback"),N_("Process priority")),
    withoutInformation(ACTION("rescan-plugins",10,N_("Smooth Playback"),N_("Rescan plugins"),N_("Rescan"))),
    ADV("sout-transcode-venc",10,N_("Developer"),N_("Encoder")),
    ADV("codec",10,N_("Developer"),N_("Decoder")),
    ADV("clock-synchro",10,N_("Developer"),N_("Clock synchronisation")),
    ADV("clock-jitter",10,N_("Developer"),N_("Clock jitter")),
    ADV("cr-average",10,N_("Developer"),N_("Clock reference averaging")),

    PREF("input-record-path",11,N_("Recording"),N_("Save recordings to")),
    withoutInformation(PREF("input-record-native",11,N_("Recording"),N_("Record without re-encoding when possible"))),
    withoutInformation(PREF("qt-cast-discovery",11,N_("Casting"),N_("Discover cast devices"))),
    PREF("sout-chromecast-conversion-quality",11,N_("Casting"),N_("Cast quality")),
    withoutInformation(PREF("sout-display",11,N_("Streaming"),N_("Play locally while streaming"))),
    withoutInformation(PREF("sout-audio",11,N_("Streaming"),N_("Include audio"))),
    withoutInformation(PREF("sout-video",11,N_("Streaming"),N_("Include video"))),
    withoutInformation(PREF("sout-spu",11,N_("Streaming"),N_("Include subtitles"))),
    PREF("sout-x264-preset",11,N_("Streaming"),N_("Encoding preset")),
    PREF("sout-x264-tune",11,N_("Streaming"),N_("Tuning")),

    withoutInformation(PREF("qt-autoload-extensions",12,N_("Add-ons"),N_("Load add-ons on startup"))),
};
#undef PREF
#undef EDIT
#undef SLIDE
#undef ACTION
#undef ADV
#undef ASLIDE
}
