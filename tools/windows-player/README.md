# Native player inspection without desktop control

Build the pinned [Windows baseline](../windows-baseline/README.md) first, keeping
its SDK/runtime backports and configured build directory. The S1 pristine-source
gate applies before the redesign overlay, not afterwards. Apply the fork's maintained overlay to that source tree, including the changed
`modules`, `src`, `share/lua/extensions` and contrib rules/patches, and copy this
tool directory alongside it. When applying an archive after the
baseline, extract with `tar --touch -xf <overlay>` so changed headers are newer
than the baseline-generated `.moc.cpp` files. Preserving an older archive mtime
can leave Qt metadata stale even when configuration rebuilds the C++ objects.
Rebuild the pinned UPnP dependency
as described below. Then use `build-player.sh normal` or
`build-player.sh diagnostics` inside the same toolchain; optional arguments set
source/build/runtime roots. Both modes force the guarded translation units to
rebuild and strip the repaired plugins into the isolated runtime. Stop its owned
consumers first. This creates a local preview without installation/publication.

The pinned Qt 6.8.3 source is available from the [official archive](https://download.qt.io/archive/qt/6.8/6.8.3/submodules/qtbase-everywhere-src-6.8.3.tar.xz); verify it against `contrib/src/qt/SHA512SUMS`.

S3 also rebuilds the pinned Qt SDK with `rebuild-qt-network.sh` for native
Schannel HTTPS. Before rebuilding UPnP or configuring the player, run
`prepare-runtime-crt.sh` to select the patched startup objects and CRT libraries
into `/work/runtime-crt-only`. Use `-B/work/runtime-crt-only/` in CC/CXX and
`-L/work/runtime-crt-only` in LDFLAGS, preserving the baseline's other flags.
Run `python3 tools/windows-player/configure-player.py` after the SDK repairs to regenerate libtool's cached startup-object paths and select the target libarchive/QtNetwork pkg-config files. The helper preserves existing configure and linker arguments. Do not put the
full `/work/runtime-fixed/lib` install ahead of contrib libraries: its Windows
`libupnp.a` import library shadows pupnp and does not implement `UpnpResolveURL`.
`rebuild-upnp.sh` accepts `VLC_RUNTIME_LIB_DIR` for the selected CRT directory.

S5 also runs `rebuild-qt-timers.sh` against that existing target Qt build before
linking VLC. The maintained contrib patches make MinGW animation timers and the
regular-expression JIT cache owned by `QThreadStorage`, whose destruction runs
before native TLS storage release.
It preserves other platforms, timer behavior and ordinary thread completion.
`build-qt-timer-check.sh` builds the focused native regression with the same
static SDK/CRT. Its free wrapper only observes the exact emutls allocation
identity; it does not poison memory or change allocator order. Unpatched Qt
fails with code 23 before a dangling destructor runs; patched Qt must destroy
both real timers and the JIT stack and exit normally. Integrated app exits still require separate
verification. See [Qt's lifetime contract](https://doc.qt.io/qt-6.8/qthreadstorage.html).

## S5 preference and bookmark contract

Preferences retain VLC's existing configuration keys and ConfigControl editors,
metadata, backend defaults/ranges and persistence in `vlcrc`. The native module
inventory assigns every public option to one of the thirteen reference
categories; the existing key editor owns core and global mappings. Unselected
advanced module editors are instantiated only when opened; existing editors
retain unsaved edits while navigating. Save applies the visited editors; Cancel
and the close button discard staged values. Search covers keys, descriptions,
module and category and opens the actual corresponding editor, including its
advanced module. Visible help includes the native default, bounded range, key,
module and restart semantics. Existing `qt-initial-prefs-view` values 0/1/2 now
select categories / expanded advanced options / all-settings search results.

The existing Windows interface-language registry and `MainWindow/color-scheme-index`
remain their owners. Language and theme changes are staged until Save. The
reference accent palette stages the existing `qt-accent-color`; its help reveals
the native custom/system/default value editor. The native accent option now drives the current QML controls and native dialogs, preserving Figma orange for `default`, the system highlight for `system`, and valid custom colors. Invalid stored colors remain untouched and display the source default. S6 retains layout profiles and onboarding, including their theme/accent workflows.

The new native options are `qt-key-add-bookmark` (default `Ctrl+Shift+b`, applied
on restart), `qt-shortcut-feedback` (true), `qt-shortcut-feedback-key` (true) and
`qt-shortcut-feedback-duration` (1500 ms, range 500-5000). The latter three affect
Qt action feedback immediately; native video OSD remains controlled by `osd`.
Feedback is an intentional user-configurable timed display, not synchronization.
An existing conflicting core binding keeps priority; shortcut changes require
restart and the native conflict editor requires an explicit reassignment. Native
menu/interface commands are reserved and cannot be silently shadowed. Existing
configuration defaults, bindings and unrelated keys are not migrated.

Bookmarks use native media-library identities and bookmark rows, with no new
settings file. Opening the sidebar does not create history or library entries.
An explicit Add registers a missing external-media identity through VLC before
saving its actual engine time. History-disabled profiles may keep explicitly
requested bookmarks without adding playback history. Bookmarks and embedded
chapters are separate lists; chapters retain native input metadata and selection.
Queued work is bound to the media revision, so changing inputs cannot apply a
position to another media. Save failure has visible feedback. The native media
library remains responsible for database recovery; no destructive fallback or
second bookmark database is introduced.

Native preferences reset retains upstream configuration/interface-settings reset
semantics after confirmation, including the Windows language override. Media,
bookmarks and separate subtitle association/download files are preserved. Tests
must isolate configuration and avoid changing the installed Windows language
registry; a normal Cancel never writes it.

## Library state and audit contract

The existing interface settings own `redesign/library-v1`. Version 1 stores
folder/playlist pins (native library identity, title and section) and the detail
view flag. An absent key starts with empty pins and details off. Existing
`MainCtx.gridView` remains the grid/list preference; details overrides only its
presentation. No prior setting is migrated. Reset library layout clears these
pins and details and preserves the existing grid/list preference.
Cached shortcut labels longer than 1024 UTF-16 units retain their beginning and
end with a middle ellipsis, without splitting surrogate pairs. The native media
identity and actual playlist/folder name are preserved and resolved on opening.
Writes obey the same size bound as reads; reaching it leaves the previous value
intact with actionable feedback.

Invalid, oversized, duplicate-pin or unknown-version data is preserved read-only,
with a visible explanation. Repair or remove only this key while VLC is closed;
there is no automatic destructive recovery. Media identities, watched state,
playlists and recent history remain in VLC's native library. History-disabled
profiles do not query or show the recent Home shelves.

Home's frequently visited folders use native playback history and play counts,
with last-played date breaking ties. Only present indexed local folders qualify.
No separate browsing-history store is created. History-disabled profiles do not
instantiate these models. Pins remain available in navigation (the compact
library exposes them in Open media). Folder-address editing is available from
that menu or Alt+D, leaving the default Figma breadcrumb layout intact.
VLC's existing Ctrl+L queue shortcut is preserved. Address resolution walks native
indexed roots/subfolders, including empty folders and all breadcrumb ancestors.
The pinned root/subfolder APIs return all children; this model applies search,
ordering and logical cache pagination explicitly.

The new library uses Qt internal drag/drop for in-window queue insertion. Existing
views retain their native external drag behavior. Diagnostic `press`, `move` and
`release` actions retain the framework button state across rendered observations;
they never inject OS input. Do not confuse a completed gesture dispatch with a
verified queue insertion: inspect the resulting queue and unchanged current input.

`verify-player-capture.py --library --snapshot <native.json> --capture <native.png>`
checks the resolved native library, accessible navigation, 24-pixel header icons,
Home card sizes/spacing and miniplayer window fit against Figma frames
`6261:15078`, `848:1997` and `970:4028`. It checks Qt's captured chrome;
separately composed video requires the owned-window capture procedure below.

## Normal-runtime regression

For library-stage acceptance, pass `--with-media-library` to
`verify-player-runtime.py`. It requires the native media-library plugin to start,
in addition to actual video, natural EOF, input release, Qt shutdown, normal exit
and absence of diagnostic transport in the delivered plugin. Use a fresh empty
portable profile, keeping the fixture library profile separately until its
persistence checks and evidence reconciliation finish.

### S3 state and subtitle identity contract

The Qt subtitle downloader links the existing contrib `libarchive` through
pkg-config; Meson declares the same dependency. This supports standard ZIP and
ZIP64. Qt's private ZIP reader rejected a valid small ZIP64 provider archive as
an oversized 4 GiB member. Extraction remains memory-only, rejects duplicate
member paths and CRC failures, and caps 256 entries, 8 MiB per subtitle and
16 MiB total. Original member paths feed readable names and collision references.
`subtitle-data-check.pro` exercises these contracts with synthetic ZIP64 data.
For the pinned chroot's native cross-pkg-config, select its target
`PKG_CONFIG_LIBDIR` and `PKG_CONFIG_PATH` and use `PKG_CONFIG_SYSROOT_DIR=/`;
the complete target filesystem is already rooted at `/` inside that chroot.

`redesign-media-tools.json` lives in VLC's selected configuration directory.
Version 1 stores explicit local file associations, named folder presets and the
timeline, waveform and statistics visibility flags. A profile without this file
starts with no associations/presets and all three overlays disabled. Existing
`vlcrc`, queue and history remain owned by VLC; no legacy settings are migrated
or rewritten by the new store. Updates use `QSaveFile` and an 8 MiB limit. An
unreadable, oversized, corrupt or unknown-version file is preserved and the store
becomes read-only, with a visible status. Rejected mouse or keyboard edits leave
toggle visuals and accessibility in their accepted state; the shared checkbox
uses Qt's `nextCheckState` callback to keep the setting owner authoritative.
Repair that file while VLC is closed;
there is no automatic reset or destructive recovery.

Associations use canonical local media URLs and both files' size, modification
time and SHA-256 fingerprint (whole files up to 8 MiB, first/last 64 KiB for
larger files). Changed or missing files require explicit selection again;
moving files does not trigger identity guessing. The matching dialog can remove
saved associations, including missing paths. It preserves ambiguous candidates
for manual choice. At most 2048 associations and 64 folder presets are stored.

New inputs inherit configured subtitle defaults, then the most specific saved
folder preset, then explicit input-specific choices. Presets capture appearance,
delay, subtitle timing and audio/subtitle language and track preferences. A valid
per-file subtitle association selects that exact external source. A later manual
track choice wins for the current input. Manual appearance/timing changes do not
rewrite a preset or leak into the next show. Section reset restores VLC's option
defaults and disables that section's filters; subtitle reset also clears delay,
FPS override and duration adjustment. Presets and associations have separate
explicit removal actions. The sleep timer is session-only and stops the playlist
on expiry; cancellation or restarting VLC clears it.

Provider keys and optional OpenSubtitles bearer tokens are session-only and are
absent from this store. Downloaded text subtitles are intentional persistent
files under VLC's user-data `redesign-subtitles` directory. Each download has an
exclusive directory and a readable filename containing provider, public subtitle
reference, original filename and available release, language and the detected actual format.
The language uses VLC's supported `.en.srt`-style suffix with canonical ISO
codes, so filenames also preserve real track-language detection. Generic archive
members retain their parent context; truncated or nested member paths get a
stable short member reference to distinguish collisions. Archive choices retain
their original member paths. Track display labels retain VLC's original metadata
and add the readable external filename using the core's exact source identity.
For downloaded files the track list puts the title/episode before the provider
reference, keeping the episode visible in the 400-pixel panel. The full label
remains accessible and available through the existing tooltip.
These names must remain distinguishable after restarting VLC; source inspection
alone does not verify that acceptance criterion.

`verify-player-runtime.py` checks a normal build on an owned inactive desktop.
Pass an isolated E: runtime with an **empty** `portable` directory, a finite
synthetic fixture, and registered E: scratch/evidence paths. It rejects existing
portable settings, checks diagnostic markers are absent, generates the actual
plugin cache, then verifies first picture, natural EOF, input release, Qt shutdown,
normal process exit and absence of QML runtime errors. Its `result.json` preserves
failed checks too. Register validation-created profile files before running and
clean them through the normal reviewed transaction afterwards.

```powershell
python tools/windows-player/verify-player-runtime.py --runtime E:/VLC-Redesign/S2 --fixture E:/Temp/<task>/Blur-pattern.mp4 --scratch E:/Temp/<task> --evidence E:/Temp/<task>/evidence/normal-final
```

The EOF regression caught delayed setup callbacks outliving their UI objects.
Named QObject methods preserve the same queued initialization while letting
[Qt 6.8.3's delayed-call queue](https://github.com/qt/qtdeclarative/blob/v6.8.3/src/qml/qml/qqmldelayedcallqueue.cpp)
cancel a call whose owner is deleted. Anonymous closures created inside another
handler do not reliably carry that owner guard. No delay or null-object fallback
is needed.

## Instrumented interactive audit

Native-widget snapshots now include their measured position, font, DPR, checked
state and visible-region status. Preferences expose only their public option-key
inventory; passwords remain redacted. The categories, results and shortcut table
also expose currently rendered model rows, not invisible rows presented as UI.
Native widget clicks and keys use the same QPA dispatch boundary as Quick, with
real focus/shortcut handling. Clipped click targets and unfocused key targets are
rejected before dispatch. `widget_resize` resizes a visible owned native dialog
through its actual QWidget layout, for the S5 responsive checks. All of these
hooks remain diagnostic-only and use the same authenticated, revision-bound
session; they do not inject Windows input or activate the user's desktop.

`maininterface/player_diagnostics.hpp` is compiled out unless
`VLC_PLAYER_DIAGNOSTICS` is explicitly defined. The Autotools test build enables
it with `make -C modules/gui/qt PLAYER_DIAGNOSTICS_CPPFLAGS=-DVLC_PLAYER_DIAGNOSTICS libqt_plugin.la`.
Rebuild `mainui.cpp` and `compositor_dcomp.cpp` when switching the flag: changing make variables
alone does not invalidate existing objects. Normal builds leave the flag empty.

The instrumented build also requires both environment variables:

- `VLC_PLAYER_DIAGNOSTICS_DIR`: existing absolute task-owned E: directory.
- `VLC_PLAYER_DIAGNOSTICS_TOKEN`: random session token of at least 32 characters.

Launch interactive audits in an isolated portable runtime on an **inactive Windows desktop**.
The task's `isolated_desktop.py` creates an owned desktop, binds only the child
process through `STARTUPINFO.lpDesktop`, never calls `SwitchDesktop`, waits for
that exact process to exit, then closes its handles. Native startup, fullscreen
and menus keep their ordinary behavior within that desktop. This prevents them
from covering the user's workspace or acquiring its input, without changing
production activation behavior. Do not run instrumented audits on the input
desktop. The test process uses Qt file dialogs so the existing QWidget diagnostic
tree can inspect their real controls; Windows shell-dialog routing is outside
this audit.
The launcher records `session.json` there with the exact `pid`, `executable` and
`token`. A diagnostic-only `VLC_PLAYER_DIAGNOSTICS_PROXY_PORT` can select an explicitly
owned loopback HTTP CONNECT test peer. It requires the diagnostic directory and
authentication token. The peer can acknowledge CONNECT and hold the TLS handshake
until the app cancels or changes input, without receiving decrypted credentials
or forwarding the provider request. This verifies cancellation against socket
closure rather than timing a live provider. It changes only this test process's
Qt proxy, never system configuration. Normal builds contain no proxy override.
`VLC_PLAYER_DIAGNOSTICS_BUILD` records the inspected plugin hash,
separately verified by the launcher. Do not commit session tokens.

```powershell
python tools/windows-player/inspect-player.py --session E:/Temp/vlc-s2-20261018/evidence/native-v6/session.json snapshot --capture
python tools/windows-player/inspect-player.py --session E:/Temp/vlc-s2-20261018/evidence/native-v6/session.json click --target playButton --capture
python tools/windows-player/inspect-player.py --session E:/Temp/vlc-s2-20261018/evidence/native-v6/session.json quit
```

The client verifies process identity and publishes each authenticated command
under its unique request ID through atomic file replacement. Requests do not
overwrite one shared file, so a read-only observation cannot lose another
client's command. The app closes each input before dispatch and the response payload before creating a
separate `.ready` completion marker. The client waits for that marker on Windows
directory notifications or that
process's exit, without a synchronization timeout or sleep. The app watches the
directory on its Qt dispatcher. Mutations require a fresh snapshot revision;
stale/absent/disabled targets fail before dispatch. Actions feed Qt mouse/key
events through the pinned QPA event queue and real window handlers. QPA constructs
each mouse event at delivery, after the preceding event updates its device
point/grabber state; preconstructing and posting a complete mouse sequence is
not equivalent and can leave a button pressed. They do not inject Windows input,
activate the window, evaluate arbitrary code, or call playback setters directly.
With Qt GUI private headers, keyboard events pass through Qt's pinned QPA test
boundary with virtual Qt focus, without requesting OS focus. This is a synthetic
framework event test, not proof of OS keyboard routing. A `key --target` checks
that the named item is already visible, enabled and in the active focus chain;
it does not redirect keyboard events or force focus. The client separately
reports whether this exact VLC process owns the Windows foreground window before
and after each request, without inspecting other applications' content.
`focus` invokes the target's existing Qt accessibility SetFocus action. This
lets the settings panel's own focus handler reveal an offscreen control, without
Windows activation, pointer input, arbitrary evaluation or content-position setters.
Snapshot bounds use each item's layout rectangle; TextInput.boundingRect() can
cover only its text/cursor and does not describe its clickable control rectangle.
The diagnostic build also records the last delivered pointer sequence and eight
seek submissions, making UI dispatch and core acceptance independently inspectable.

An action response reports dispatch and the observed tree; verify the expected
effect separately. Dispatch does not establish playback or asset readiness.

`--await-core` observes locked native player state rather than the UI timer's
optimistic seek position. Available fields are state, position, time_seconds,
length_seconds, URL and seekability. Position/time observations bind to the
current media URL and fail if it changes or ends. Use `at_least` for advancing
playback instead of waiting for an exact transient clock value. VLC's raw
clock getters can retain the previous clock while paused after a seek; the UI's
seek notification can already show the requested time. Establish that request
through its UI notification, then verify advancing native time and rendered pixels
after resuming. Do not treat an optimistic UI position as decoded-frame proof. A second request
while an observation is pending fails explicitly, except a read-only snapshot
without capture. That snapshot labels its UI-dispatcher boundary and does not
claim a new rendered frame. Use `cancel` to end an observation, and inspect its
original result before sending another action.
For example:

```powershell
python tools/windows-player/inspect-player.py --session E:/Temp/vlc-s2-20261018/evidence/native-v17/session.json click --target progressSlider --fraction-x 0.5 --await-core position --await-value 0.49 --await-comparison at_least
```

Snapshots also identify owned Qt windows/popups and report the DirectComposition
video-backdrop regions, actual swapchain attachment, Gaussian sigma, rounded
clips and HRESULT. These describe the native composition graph; Qt's UI-only
capture does not include that separately composed video/effect layer.

Snapshots follow an actual Qt `frameSwapped` observation and optional render-target
capture completion, rather than a queued callback before deferred layout.
They include instantiated item IDs/types/text, measured logical geometry,
effective visibility/enabled state, focus/check/value state, QML errors, mounted
image resolution counts, PID/build/Qt/DPR, revision and monotonic elapsed
observation. `player_ready` requires seven player controls to have measured
bounds, no collected QML error, and no pending/failed mounted image. It does not
establish feature acceptance. Virtualized unmounted rows are outside this tree;
native QWidget menus and video surfaces are separate. Visible flags do not prove
lack of occlusion. Truncation is explicit. Captures use Qt's own render target,
independent of desktop occlusion; the callback does not prove physical display
presentation. They remain evidence for native chrome appearance.
Queue delegates also expose their current model index: pooled items can retain
old text/visibility while not painting. An index of -1 is outside the current
queue; the client excludes those rows when resolving a media URL.

Keep temporary snapshots/captures under the exact E: scratch root. Preserve only
reviewed acceptance evidence in the design resources, then use transactional
cleanup after this process and its consumers finish.

Desktop isolation follows [CreateDesktopW](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-createdesktopw) and [STARTUPINFO.lpDesktop](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/ns-processthreadsapi-startupinfow). Framework event delivery follows the pinned Qt 6.8.3 implementation: [widget show](https://github.com/qt/qtbase/blob/v6.8.3/src/widgets/kernel/qwidget.cpp), [popup input grabs](https://github.com/qt/qtbase/blob/v6.8.3/src/widgets/kernel/qapplication.cpp), [Windows QPA](https://github.com/qt/qtbase/blob/v6.8.3/src/plugins/platforms/windows/qwindowswindow.cpp), and [synthetic framework events](https://github.com/qt/qtbase/blob/v6.8.3/src/gui/kernel/qwindowsysteminterface.h). The QPA boundaries are test-only and Qt-private; do not expose them in a normal build.

For asynchronous core changes or panel transitions, pass `--await-property`
with a JSON `--await-value`; `--await-target` selects a separate stable item.
For example, opening the queue can await `playqueuePane.width == 400` at 100%
scale, while choosing a track awaits that row's `selected == true`. Only named
properties in the fixed whitelist are read. QML notify signals complete the
observation, followed by a rendered frame/capture; no timer or polling deadline
is used. `cancel` cancels a pending observation without undoing the UI action;
`quit` also closes the exact test instance. Observe the original client result.

Input is queued through Qt so an open-file action can enter its real modal Qt
dialog without blocking the diagnostic dispatcher. Targets clipped outside a
scrolling ancestor are rejected before dispatch. The instrumented session alone
sets `vlcPlayerDiagnosticSession`; the existing drag item then suppresses entry
into Windows OLE drag. That test mode does not verify desktop OLE routing.
The redesigned library uses the same Qt internal queue-drop path in normal and
diagnostic builds; verify it with held press/move/release and the resulting queue
and current input. Verify queue reordering through its real sort UI, and URL drops through Qt's
drop event handlers; desktop OLE routing remains outside this instrumented audit.
Ordinary builds never set the context property and retain the original native
drag path. Pointer `drag` remains useful for sliders. Wheel events inspect popup
scroll reachability through `scroll`, optionally awaiting the body's `contentY`.
Wheel timestamps share the QPA pointer clock: a zero timestamp can make Qt's
Flickable use an unrelated local timer and reject the calculated velocity.
URL-drop diagnostics send Qt's enter, move and drop sequence and reject an
unaccepted drop; a failed drop also releases the framework drag state.

## Composed video capture without foreground control

Windows Graphics Capture rejects windows on an inactive desktop. For this one
rendering check, the diagnostic build accepts
`VLC_PLAYER_DIAGNOSTICS_OFFSCREEN=1`: before showing its window, it disables
native focus/activation and places the window beyond the union of screen bounds.
That session permits only snapshot, resize, cancel, quit and the existing Ctrl+P
action for a composed Preferences capture. The diagnostic Preferences window is
also placed beyond every screen, with native activation and focus disabled.
Interactive and
fullscreen checks continue on an inactive desktop with ordinary window behavior.
Verify the actual native window bounds and foreground ownership before capture.
Normal builds contain neither this mode nor the diagnostic command transport.

`capture-player-window.cpp` captures one SDR frame of the recorded window. It
checks HWND/PID and the recorded full executable path, suppresses cursor capture,
and waits for a frame or that process's exit without a deadline. It uses no
picker, input injection or desktop capture. Its PNG includes the composed video
and effects, plus the native window border. It is not an HDR/Dolby Vision test.
Build this separate inspection utility with an installed MSVC/Windows SDK
developer environment, writing compiler/linker output and scratch to E:, for
example:

```bat
cl /std:c++20 /EHsc /O2 /MT /FoE:\Temp\<task>\capture.obj /FeE:\Temp\<task>\capture.exe C:\<checkout>\tools\windows-player\capture-player-window.cpp /link windowsapp.lib d3d11.lib dxgi.lib windowscodecs.lib ole32.lib user32.lib
E:\Temp\<task>\capture.exe <recorded-pid> <native_id_hex> E:\Temp\<task>\runtime\vlc.exe E:\Temp\<task>\composed.png
```

This utility's compiler does not replace VLC's pinned MinGW build toolchain.
Capture follows [CreateForWindow](https://learn.microsoft.com/en-us/windows/win32/api/windows.graphics.capture.interop/nf-windows-graphics-capture-interop-igraphicscaptureiteminterop-createforwindow).

`verify-player-capture.py` checks actual control bounds, labels, title fallback
and mounted assets. With `--pattern`, it also checks that blur stays inside the
chrome. It uses Pillow to read the recorded pixels. Generate the SDR fixture with
`ffmpeg -f lavfi -i testsrc2=size=1920x1080:rate=24 -t 2 -c:v libx264 -preset ultrafast -pix_fmt yuv420p -an Blur-pattern.mp4`,
open it paused without a media library, and capture a light 16:9 client at about
1920×1080 physical pixels. Use logical sizes 1920×1080, 1280×720 and 960×540
for Qt scale factors 1/1.5/2, allowing fractional native border rounding. At 100%,
source geometry remains exactly 1920×1080. The regression rejects both an
unblurred edge under the chrome and blur leaking into the main picture.

## Pinned UPnP dependency correction

The first media-library audit exposed a self-loop in the pinned pupnp 1.14.31:
its Windows alias macros rename MinGW's inline `strncasecmp` definition into a
function calling itself. The fork's `contrib/src/upnp/mingw-posix-aliases.patch`
retains MinGW's POSIX declarations and preserves MSVC's aliases. The standard
contrib rules apply it. `rebuild-upnp.sh` reproduces the same-version repair in
the isolated baseline SDK, verifies the upstream archive against VLC's recorded
SHA-512, builds the existing dependency and relinks the UPnP plugin. It does not
upgrade the SDK or change a user's installation. `upnp-url-check.c` exercises
case-insensitive HTTP scheme handling without a network request. Native
media-library startup, real playback/history and normal process exit are separate
integration checks.

Fetch `https://codeload.github.com/pupnp/pupnp/tar.gz/refs/tags/release-1.14.31`
as `/scratch/cache/pupnp-release-1.14.31.tar.gz`; the recipe checks VLC's
`contrib/src/upnp/SHA512SUMS` before extraction. It expects a fresh dedicated
`/work/upnp-rebuild-s2` and retains the existing Windows SDK prefix.

## Video backdrop

The redesigned title bar, controls and resume banner carry the retained Figma
50px background-blur property. The Windows compositor shares the actual video
swapchain across four system-created, clipped DirectComposition visuals below
Qt's translucent fills. A forwarding content handle intercepts only the vout's
existing `SetContent` boundary; every other visual method retains its original
behavior. This avoids another decoder, video readback or desktop blur. Bounds,
corner radii, visibility and scaling come from the actual QML backgrounds during
Qt's synchronization phase. The helper lives only as long as the vout window.
Gaussian sigma uses half the Figma radius, matching the reported Figma Dev Mode
CSS conversion; that mapping requires visual comparison and does not establish
mathematical equivalence of the renderers.

The fourth region covers the active frosted library popup, including its overlay
item. Context menus and the network dialog share `LibraryGlass.qml`.
The network source frame `6216:13614` uses 95% panel fill, 14px corners,
50px background blur and an 8/15px shadow. Context-menu sources `2139:8935`
and `2404:13340` use their 95% fill and 10px corners. The existing four-pass Qt blur handles library UI;
the shared native video copy handles separately composed video beneath it.
The Qt kernel is scaled by actual DPR to approximate the same Gaussian sigma;
it does not create another decoder or capture the desktop.

DirectComposition contracts: [visual content](https://learn.microsoft.com/en-us/windows/win32/api/dcomp/nf-dcomp-idcompositionvisual-setcontent),
[Gaussian blur](https://learn.microsoft.com/en-us/windows/win32/api/dcomp/nn-dcomp-idcompositiongaussianblureffect).
The unfiltered video must remain below the clipped copies. Initialize all four
[rectangle clip bounds](https://learn.microsoft.com/en-us/windows/win32/api/dcomp/nf-dcomp-idcompositiondevice-createrectangleclip):
their defaults are large positive/negative extents, not a zero-origin empty clip.

Library drags snapshot the pressed row or current multi-selection before the
ML payload resolves. Ordinary clicks commit selection on release, keeping the
selection toolbar from moving the delegate during a held pointer gesture.

Popup readiness requires the blur output and rounded texture to resolve, with no
shader error. Qt 6.8.3 copies cached shader metadata without invoking the new
manager’s preparation path, leaving its status at Uncompiled: see the
[cache path](https://github.com/qt/qtdeclarative/blob/v6.8.3/src/quick/items/qquickshadereffect.cpp#L1157-L1161)
and [manager default](https://github.com/qt/qtdeclarative/blob/v6.8.3/src/quick/scenegraph/qsgrhishadereffectnode_p.h#L112).
Compiled status alone is therefore not a valid completion predicate. Native
captures, source fill/corner geometry and error-free lifecycle transitions remain
separate acceptance evidence.
