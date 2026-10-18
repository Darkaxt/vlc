# Native player inspection without desktop control

Build the pinned [Windows baseline](../windows-baseline/README.md) first, keeping
its SDK/runtime backports and configured build directory. The S1 pristine-source
gate applies before the redesign overlay, not afterwards. Apply the fork's
maintained `modules/gui/qt` and `contrib/src/upnp` changes to that source tree,
and copy this tool directory alongside it. Rebuild the pinned UPnP dependency
as described below. Then use `build-player.sh normal` or
`build-player.sh diagnostics` inside the same toolchain; optional arguments set
source/build/runtime roots. Both modes force the guarded translation units to
rebuild and strip the repaired plugins into the isolated runtime. Stop its owned
consumers first. This creates a local preview without installation/publication.

## Normal-runtime regression

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
`token`. `VLC_PLAYER_DIAGNOSTICS_BUILD` records the inspected plugin hash,
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
framework event test, not proof of OS keyboard routing. The client separately
reports whether this exact VLC process owns the Windows foreground window before
and after each request, without inspecting other applications' content.
An action response reports dispatch and the observed tree; verify the expected
effect separately. Dispatch does not establish playback or asset readiness.

`--await-core` observes locked native player state rather than the UI timer's
optimistic seek position. Available fields are state, position, time_seconds,
length_seconds, URL and seekability. Position/time observations bind to the
current media URL and fail if it changes or ends. Use `at_least` for advancing
playback instead of waiting for an exact transient clock value. A second request
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
into Windows OLE drag. Do not claim a completed native queue drag from that test
mode. Verify queue reordering through its real sort UI, and URL drops through Qt's
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
That session permits only snapshot, resize, cancel and quit. Interactive and
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
swapchain across three system-created, clipped DirectComposition visuals below
Qt's translucent fills. A forwarding content handle intercepts only the vout's
existing `SetContent` boundary; every other visual method retains its original
behavior. This avoids another decoder, video readback or desktop blur. Bounds,
corner radii, visibility and scaling come from the actual QML backgrounds during
Qt's synchronization phase. The helper lives only as long as the vout window.
Gaussian sigma uses half the Figma radius, matching the reported Figma Dev Mode
CSS conversion; that mapping requires visual comparison and does not establish
mathematical equivalence of the renderers.

DirectComposition contracts: [visual content](https://learn.microsoft.com/en-us/windows/win32/api/dcomp/nf-dcomp-idcompositionvisual-setcontent),
[Gaussian blur](https://learn.microsoft.com/en-us/windows/win32/api/dcomp/nn-dcomp-idcompositiongaussianblureffect).
The unfiltered video must remain below the clipped copies. Initialize all four
[rectangle clip bounds](https://learn.microsoft.com/en-us/windows/win32/api/dcomp/nf-dcomp-idcompositiondevice-createrectangleclip):
their defaults are large positive/negative extents, not a zero-origin empty clip.
