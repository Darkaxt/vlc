# VLC desktop redesign specification

Version 1, registered 13 October 2026. Owner: Darkaxt. Upstream baseline: VLC master `392bc1d0abdb7396b6c97fef206efa1d23868e19`. Resource policy updated during registration at the user's request: retain the original Figma archive and its contents manifest; omit derivative PDF/PNG exports from Git.

## Authority and current authorization

**8 November native desktop packages, R111/R112, already authorized:**

The user requests macOS and Linux builds before contacting Juxtopposed, all
available desktop packages to establish a deployment pipeline, and removal of
the Windows-only MPV restriction. They explicitly permit plain upstream MPV on
the new platforms instead of requiring the custom Dolby Vision patch. Preserve
the existing verified Windows x64 MPV/Dolby Vision runtime and its provenance.
Creator outreach is pending; no message has been sent or approved for sending.

R111: produce native macOS (Apple Silicon and Intel), Linux (x86_64 and aarch64)
and the maintained Windows x64 delivery from one identified source revision.
Inventory and attempt applicable desktop packaging routes, including macOS app
ZIP/DMG, Linux portable archive/AppImage/DEB/RPM/Snap, and Windows portable
ZIP/7z and installer routes. Record exact unavailable prerequisites or failures;
do not label a broken build unsupported merely to remove it from acceptance.
Mobile/TV, OS/2 and WebAssembly libVLC targets are not this desktop redesign.
Do not publish to new stores or install over users' existing players/profiles.
Use native hosted CI where available, with pinned sources/actions, explicit
architecture/toolchain/runtime/license manifests and reusable dependency caches.
No paid runner, signing account or new credential is assumed. Use ad-hoc signing
where required to run macOS binaries; distinguish it from Developer ID signing
and notarization. Preserve the existing unsigned Windows distribution policy.

R112: use the same Qt/QML/Figma interface and queue/settings owner on each
platform. Implement native MPV loading, render-surface ownership, native audio,
and deterministic shutdown/replacement without Windows DLL/D3D11/WASAPI
assumptions outside the existing Windows backend. Ordinary MPV is sufficient on
macOS/Linux; do not promise the Windows Dolby Vision patch or native DV display
signaling there. Keep engine choice, separate accents, subtitles, seeking,
volume, image handling, live handover and floating-player behavior integrated.
Packaging an upstream Cocoa interface or launching a separate mpv application
does not satisfy this requirement. Platform capability differences must be
truthful and recorded, without silently removing existing Windows capabilities.

Acceptance requires native executable architecture/dependency checks, relocation,
actual Qt redesign and video evidence, VLC/MPV playback/audio/subtitles/seek,
handover, miniplayer/restore/dismissal, clean exit and profile preservation.
Verify each installable format in an isolated matching environment where its
platform permits it. Keep source/license obligations and matching optional
symbols separate from release binaries. A successful compile or archive alone
is not native acceptance. After the complete integrated outcome passes, publish
one normal versioned release through Darkaxt/vlc's established GitHub channel,
independently retrieve/check its assets and update the existing weekly pipeline.
Preserve verified1.1.11 until the new delivery and continuing build binding pass.

Native acceptance exposed unsolicited LAN discovery during local-file playback:
MediaLibrary::Init unconditionally enables every LAN discovery provider. Correct
that startup path within M15: local-only/empty libraries must not start LAN
providers; configured network roots (including unavailable shares) and explicit
network-folder discovery/reload must retain their behavior when network discovery
is enabled. Preserve upstream's explicit `ml-network-discovery=false` opt-out in
both startup and explicit folder operations. Do not accept a
system permission prompt as a way to pass local playback verification. Correct
the Cocoa OpenGL probe to request its supported 3.2 Core profile rather than
falling back to Qt's shader-less software renderer after a 3.0 Core request.

**8 November upstream synchronization, R113, already authorized:** once M15's
base native deployment workflow works, integrate the then-current upstream master
by normal merge history within M15 before the final architecture/package matrix
qualification and M16 publication. Preserve the
fork's interface, Windows MPV/DV runtime, native port and existing data. Refresh
and record exact revisions at integration; a reported backlog count is not a pin.

**7 November stabilization logging, R110 (M14), already authorized:**

Delivered in normal1.1.11; [reconciliation](resources/m14-1.1.11-verification.json) records bounded retention, opt-out, startup timing, actual playback and independently verified release.

The user requests file logging enabled by default until a stable release, with
no more than about three days retained, after an intermittent reported30+s
startup. The current portable profile has no explicit file-logging override;
the upstream default is off. Windows events contain no matching hang/crash or
storage warning. AppControl distinguishes the prior1.1.9 and current1.1.10
executables, so do not treat those launches as a controlled same-build comparison
or claim that the30s cause is established.

Enable the Windows fork's native file logger by default at diagnostic verbosity,
preserving explicit saved/command-line disable and explicit user log destinations.
For the automatic destination, use the actual portable/installed profile's logs
directory and timestamped process/session files. Keep today and the preceding
two UTC dates, pruned at launch and daily/size rotation (up to72hours), with
bounded per-file/aggregate storage. No cleanup task runs while the app is closed.
Prune only precisely
owned diagnostic files; preserve live writers, unrelated files and user-selected
destinations. Rotate during long-running sessions, not only at the next launch.
Include UTC and elapsed timing plus core startup milestones so buffered early
messages cannot be mistaken for the time at which they were originally emitted.
No uploads, elevated tracing, OS configuration changes or real-profile changes
are authorized by this logging implementation. Preserve ordinary playback and
VLC/MPV/Figma behavior. Acceptance covers default creation, config/CLI opt-out,
early startup timing,72hour expiry, size rotation, concurrent processes and
unwritable storage without blocking the player. Deliver one verified normal
1.1.11 four-asset release after the complete outcome passes; preserve1.1.10
until that delivery and the reusable build/weekly binding are verified.

**7 November startup optimization, R109 (M13), already authorized:**

Delivered and independently verified in normal1.1.10; [reconciliation](resources/m13-1.1.10-verification.json) records native startup observations, exact cache/extraction checks, playback, source/symbols, profiles and cleanup. The complete user-reported10+s delay is not attributed solely to the measured plugin cost.

The user reports that launching VLC is very slow and requests an optimization
round. After deployment to their stable folder, the first launch reportedly took
10+ seconds and the next less than4; this is a user observation, not instrumented
timing. Separate plugin loading, first-run QML work and Windows filesystem cache
warming. Measure the delivered player before changing behavior: fresh unprimed
portable extraction and subsequent launches, VLC/MPV, core initialization versus
first usable interface. Keep conditions comparable and report filesystem-cache
and concurrent-work limitations; do not flush OS caches or alter the real profile.
Trace measured delays to their owners and implement only evidenced startup
bottlenecks. Preserve the Figma interface, complete configured plugin graph,
VLC/MPV/DV capabilities, font onboarding, palettes, settings/data and provenance.

Before R109, the packager omitted plugins.dat while the runtime verifier generated it
before launching. Investigate this mismatch explicitly; it is a lead, not yet a
measured explanation for the complete delay. If a shipped index is justified,
bind it to the exact normal stripped plugin cohort, preserve native cache
validation, relative/relocatable paths and extraction timestamp semantics. Do not
drop plugins, force no-scan or weaken stale-plugin checks to manufacture speed.
Acceptance must exercise fresh downloaded-package startup without priming the
plugin cache first. The selected packaging correction generates the index from
the final stripped DLLs with one fixed UTC mtime, writes matching DOS-local plus
UTC/NTFS ZIP timestamps, and records each DLL/cache hash. Standard7-Zip and
PowerShell extraction plus relocation must preserve valid native metadata;
timestamp-resetting extractors retain correct native rescanning rather than
silently bypassing validation. Demonstrate improvement on comparable normal launches and
verify affected playback, first-run and engine/profile workflows.

M13 is one cohesive startup optimization and final1.1.10 delivery stage. Reuse
unchanged1.1.9 acceptance; batch the complete fix before one normal optimized
release build. Keep the native-ext4 toolchain, flags, resource limits and verified
cohort reuse contract. Deliver one normal four-asset1.1.10 release, independently
download/start it, update the retained/weekly binding and retire superseded
packages only after verified delivery. Preserve the current verified1.1.9 until
then. No additional tiny-UI manual review or speculative modernization is needed.


**6 November runtime icon repair, R97–R99 (M7), already authorized:**

- R97: extract the Windows icon group from the user's locally installed MPV
  executable, preserve every embedded image payload, and use that artwork for
  MPV's header, idle/minimal placeholder and native window/application icon.
  Record executable/build/source provenance, group/frame hashes and applicable
  existing MPV licensing. Compare actual native rendering at100/150/200% with
  the extracted original; retain the original shapes, colors and transparency.
  Do not redraw or vectorize the emblem, execute the reference binary, change
  its installation, or replace the pinned playback DLLs.
- R98: the running Windows taskbar/dock button must use MPV artwork while MPV
  is selected and restore the redesign VLC cone when switching back, including
  startup from a saved engine. Implement the application's window/Shell identity
  through supported Windows APIs, preserving existing user pins, shortcuts,
  icon caches, file associations and profile data. Launcher metadata must point
  to this fork with the corresponding engine, never the separate MPV install.
  Verify actual Shell identity/resource selection and visible running-button
  pixels as well as HWND icons; the earlier WM_GETICON-only check is insufficient.
- R99: after the icon workflow passes, refresh the repository README with
  actual current-player screenshots, side-by-side Figma comparisons and direct
  credits/links to the original Figma project and YouTube redesign video. Use
  public synthetic media in application captures; do not publish private clips,
  profile data or desktop content. Distinguish implemented behavior from the
  design reference and retain existing upstream/project attribution.
- R100 (6 November user clarification): persist accent personalization separately
  for VLC and MPV, with orange and artwork-matching purple defaults. Offer the
  existing palette independently for each engine, preserving existing VLC values
  and legacy profile compatibility. MPV's default logo remains the extracted
  original. Custom colors recolor its chromatic regions while preserving neutral
  details, alpha and shading; header, idle, native window and running taskbar
  must agree. Menu details must use the visible purple of the logo, not the deep
  website-background purple or an additional excessively darkened substitute.
  Verify palette selection/save/cancel, engine handover, restart, custom-colored
  icon pixels and actual Shell resource/button behavior before final delivery.
- R101 (6 November review feedback): the MPV source icon appears smaller than
  neighbouring taskbar icons and has uneven small-frame edges. Increase its
  apparent size by approximately10–15% using the preserved largest original
  frame with transparent outer padding removed and cleanly downsampled display
  frames. Preserve the original extracted ICO/PNGs and source hashes; record the
  exact display derivation. Use the same derived artwork in header, idle, native
  and taskbar icons, including custom colors. This explicitly supersedes the
  earlier pixel-identical small-frame display requirement, not source preservation.
  Verify unclipped artwork, optical dimensions,100/150/200% rendering and actual
  taskbar pixels, accounting for the taskbar's own display scaling.
  **6 November scope revision:** after inspecting the captured blue MPV taskbar
  button, the user ended the resizing effort ("the icon resizing is a lost
  cause"). Keep the current displayed size; further enlargement and its optical
  size comparison are withdrawn acceptance criteria. This does not waive R98's
  engine identity or R100's custom coloring. Preserve the original artwork,
  current derived resources and the failed enlargement evidence without claiming
  that the requested10–15% taskbar increase was achieved.

- R102 (6 November user correction): disabling the media library, including
  `--no-media-library`, must retain the Figma interface, engine identity, menus,
  playback and queue. Do not create a media-library instance, database or scanner
  while disabled. Indexed views must show a truthful unavailable state; direct
  file/folder/network playback and Settings must remain usable. Verify both
  engines, restart, main/library/miniplayer transitions and representative DPI.
- R103 (6 November user request): implement the complete Figma floating
  miniplayer, automatically shown at the lower right of the active monitor when
  the main player is minimized during video playback. Preserve the current input,
  time, tracks, engine and playback state in both VLC and MPV. Include the Figma
  compact card, expandable real queue, seekbar, filename/folder metadata, hover
  previous/play-pause/next, close and restore controls and natural-EOF replay.
  Use the selected engine's accent, current original icon artwork, rounded glass
  and native-DPI rendering. Dragging/resizing must remain monitor-bounded; restore
  the same main window and avoid resurrecting the mini after explicit dismissal.
  Audio-only and idle playback must not automatically create the floating video
  window. Move the existing in-library preview to the right as also requested.
  Implementation/design contract: the normal main HWND stays minimized; a
  separate nonactivating, always-on-top tool window owns the Figma card and the
  existing composition video visual. No second decoder/player or media reopen.
  Initial card width360 logical units,8-unit video surround,16:9 picture,
  compact filename/folder footer,14-unit outer radius and an expandable queue
  above the picture. Use existing Inter/PlayerStyle tokens and original icons.
  Constrain drag/resize/queue expansion to the selected screen's usable area;
  the expanded queue's header remains a native drag surface, with a hand cursor,
  independently of its list and toolbar controls. Its sort/remove/add glyphs use
  the reference's smaller16-unit scale and muted text tone, retaining usable hit
  areas and their existing queue actions (7 November user comparison).
  Drag coverage also includes filename/footer and unused queue space in compact
  and expanded states, as clarified by the user. The seekbar and interactive
  controls retain their gestures; a queue that overflows retains scrolling.
  Hovering the video reveals Close/Restore and transport controls during both
  playing and paused states, with the queue compact or expanded. Pointer exit
  hides the overlay unless keyboard focus or touch interaction requires it.
  Restoring republishes the main surface's complete size, position and DPI even
  when its layout did not change while minimized; no miniplayer-sized video or
  transparent uncovered video area may remain (7 November reported regression).
  Video-overlay controls must remain distinguishable over bright/busy pictures:
  use bright original glyphs on compact translucent dark backing, retaining
  hover/pressed/focus feedback and the selected engine's focus accent.
  test100/150/200% DPI and both playback engines. Restore/dismiss and natural EOF
  must use the existing player and queue owners; main geometry is preserved.
- R104 (6 November reported regression): investigate the actual audio-visualizer
  selection during video playback. Supported enabled modes must have a visible
  result; unsupported engine/input combinations must not accept a silent no-op.
  Match the original Figma visualizer and EQ-preset option iconography, retain
  native choice values and real processing, and verify output plus reset/disable.
  The user explicitly clarified that the animated effects belong **inside the
  progress bar**, not above it or in a separate window. Keep the main video and
  bar geometry unchanged, preserve the seek handle, pointer/keyboard seeking,
  previews and subtitle controls, and follow the active accent. As requested on
  6 November, use accent-colored effects on the unplayed black track and black
  effects on the accent-colored played portion. The inversion boundary follows
  the progress indicator without changing the bar's layout or sample mapping.
  Drive the effects
  from the playing audio stream; do not simulate activity or decode the file a
  second time. Pause freezes the effect; seek/input/track/engine changes discard
  stale samples, and disabling releases its audio observer. Existing standalone
  VLC visualization capabilities remain available through their native controls.

- R105 (6 November player-panel comparison): match all four gear-panel tabs to
  the supplied Figma references. Only the selected tab uses its original
  two-tone active artwork, recolored with the current engine accent; inactive
  tabs remain neutral. Match section order, dividers, row spacing, field widths,
  flip segments, numeric editors, delay/speed sliders and their ticks, expanded
  filter controls, preset footer and advanced-settings action. Preserve real
  control bindings, track selection and truthful VLC/MPV availability. Verify
  actual native rendering of Playback/Video/Audio/Subtitles, including selected
  icons in VLC orange, MPV purple and a custom accent. The supplied comparisons
  are the visual contract; functioning controls alone do not prove parity.
- R106 (7 November explicit request): integrate subtitle cue bands and their
  timing/navigation controls inside the existing progress bar, matching the
  supplied Figma screenshot. Remove the separate strip/extra control-bar row.
  Preserve selected embedded/external text cues in both engines, previous/next
  cue navigation, +/-50ms timing adjustments and direct cue dragging for sync.
  Keep ordinary seeking and the playhead distinct from subtitle-offset dragging;
  keyboard/accessibility actions remain available. Cues and playhead share the
  same timeline geometry. At narrow/customized widths keep seeking usable and
  every timing action reachable without overlap or out-of-window controls.
  Toggle-off/no-cue/still-image cases retain the regular seekbar. Verify actual
  native100/150/200% layout, cue timing, pointer/keyboard gestures and both-engine
  playback; preserve in-bar visualizer/waveform behavior and saved settings.

- R107 (7 November user request): the volume wedge uses a gradient derived from
  the active engine's effective accent instead of fixed green/yellow/orange.
  Keep the original wedge silhouette, clipping to actual volume, mute feedback,
  pointer/keyboard behavior and native-DPI rendering. Saved independent engine
  colors and live switches update the gradient immediately. Verify both engines,
  default/custom accents and rendered wedge colors at100/150/200 percent.
- R108 (7 November clarification): closing the floating player dismisses only
  that window. Keep media playing and the main player minimized. Suppress
  automatic raising/reopening through input/output callbacks until the user
  explicitly restores the main window; a subsequent explicit minimize can show
  the miniplayer again. Restore remains separate. This supersedes the earlier
  stop-on-dismiss behavior and its historical M8 acceptance. M12 owns this
  bounded interaction correction alongside R107 before final delivery.

Deliver one normal Windows update after the combined icon/switch/restart workflow
passes, reusing unaffected1.1.8 acceptance and the verified native ext4 cache.
The expanded request also requires R102/R104 repairs and R103 floating-miniplayer
acceptance, R105 player-panel parity and R106 inline subtitle synchronization
before that single final release; no
intermediate repair release. M8 retains the floating miniplayer; M9 owns R105;
M11 owns R106 and M12 owns R107/R108; both precede final delivery M10.
M7/M8/M9/M11/M12 and M10 are COMPLETE in normal1.1.9; source-bound native
acceptance, actual composed pictures and independently retrieved delivery are
recorded in their verification ledgers. Preserve original drag/restore/readability reports separately
from current verification; desktop controls remain prohibited.
M6's separately recorded native-cleanup capability blocker remains parked;
it is neither waived nor relabeled as M7 completion.

**6 November delivery evidence:** R90–R95 are verified in normal
[1.1.8](https://github.com/Darkaxt/vlc/releases/tag/redesign-v1.1.8), source
`4c8c98e6a269b852afc8f40e362580172f303ff9`. Independent four-asset verification,
actual native workflows/presentation, preserved profiles and retained/weekly
ext4 binding pass. Evidence is at
`D:/VLC-Redesign/releases/1.1.8/verification`. R96 retirement remains required;
the installed cleanup helper has no native Linux deletion backend. Preserve the
exact inventoried spent native output until that capability is available. This
records an unmet cleanup criterion and does not waive it or weaken the migration
acceptance contract. Windows retirement passed with35,436,609,671 logical bytes
removed through signed tickets and zero exclusions/errors. M6 is BLOCKED only
on native cleanup, with no running operation or required deferral. See the
[reconciliation](resources/m6-1.1.8-verification.json). Current state is maintained
in PLAN.md; earlier checkpoints retain their historical meaning.

**6 November R96 (M6), already authorized:** migrate the Linux build toolchain,
source and reusable objects from the Windows-mounted tree into native ext4
storage backed by a VLC-owned WSL2 virtual disk on internal D:. Preserve pinned
toolchain/dependency/runtime provenance, absolute `/work` paths, contents,
symlinks and build-input/object mtimes. Verify the copied cohort and unchanged
configure inputs before resuming the original interrupted pipeline; do not
reinstall the SDK or discard completed objects. Use the supported WSL gate with
the existing4GiB VM/3.5GiB workload/512MiB swap/one CPU/one compiler limits.
Remove the per-build Windows-header RAM-cache copy from the native execution
recipe. Measure equivalent representative metadata/header reads and compiler
preprocessing before/after, and observe host disk latency/queue and available
memory during migration and resumed work. These observations must not be
presented as proof of the historical desktop-freeze cause or a host-I/O latency
guarantee. Keep Windows source editing, native acceptance and release delivery at
their established paths; transfer only required changes/control metadata and
finished artifacts. Preserve the old cohort as the explicit rollback until the
new binding and release are verified, then retire expendable migration output
and superseded build inputs through transactional cleanup. Existing Ubuntu,
Docker, user settings and global WSL limits remain preserved. The user's “go
ahead” resumes this chat for this migration and the outstanding M6 outcome;
other chats are not resumed by this instruction.

**5 November next repair round, R90–R95 (M6), already authorized:**

- R90: bypass the optional font page in both forward and backward wizard navigation when the existing font service reports the font available. Missing or unrecognized fonts retain the download, cancellation and FreeSans flow. Preserve inline shortcut editing and Finish/restart behavior.
- R91: opening a still image is an untimed preview, not a synthetic ten-second video. Keep the image visible until the user leaves it; remove elapsed/duration, seeking and seek-preview UI for that input. Preserve image navigation, explicit timed/slideshow capabilities, real video and animated-image playback, and both playback engines. Verify the actual native image remains displayed beyond the old duration and that image/video replacement restores the appropriate controls.
- R92: the centered idle/loading placeholder follows the selected engine: reuse the existing official MPV artwork for MPV and the redesign cone for VLC. Verify switching in both directions without changing the existing top-left branding or playback handover.
- R93: a successful in-player engine selection becomes the saved startup engine. A failed switch must not change the saved choice; a failed preference save must be reported truthfully. Verify switching and restarting in both directions with an isolated profile, preserving explicit launch overrides and unrelated preferences.
- R94: the actual main-window title and running Windows taskbar/window icon follow the selected engine: MPV Media Player and the existing official MPV artwork for MPV, VLC Media Player and the redesign cone for VLC. Preserve the media-name-in-title preference and restore identity in both switch directions and on restart. The executable file's distribution identity is unchanged.
- R95: theme accent regions in two-tone settings/menu icons follow the effective accent, including MPV purple, while neutral outlines and original vector shapes remain intact. Correct the Playback tab's fixed amber triangle and check the other uses of the same rendering path. Verify native rendering with VLC default/custom accents and MPV selected.

Batch these repairs into one normal update after their complete workflows pass. The independently verified 1.1.7 delivery remains valid for R88–R89; these new requests do not retroactively claim that delivery contains R90–R95.

**M5 delivery reconciliation: COMPLETE.** Normal [1.1.7](https://github.com/Darkaxt/vlc/releases/tag/redesign-v1.1.7) from `e9caba476b64c27817ef935532d22921bae28f43` passed native wizard/editor/restart/dispatch, normal artifact/presentation, independent download, retained/weekly binding and cleanup gates. [Reconciliation](resources/m5-1.1.7-verification.json). Blockers and required deferrals are zero.

**5 November post-1.1.6 regression, R88–R89 (M5):** shortcut changes started
from onboarding must remain inside the wizard. Capture, named conflict feedback,
explicit reassignment, Unset and Cancel must never open Preferences, the Hotkeys
page or a native capture window. Escape cancels capture before it can dismiss the
wizard; invalid/conflicting input must not trap focus. Finish persists accepted
edits; cancelling setup or a failed save preserves prior bindings. Verify the
complete first-run/reopen/restart flow and actual saved action dispatch.
Preserve the four-field profile appearance contract (theme, accent, grid,
remaining); the Interface blur degree is read separately so it cannot invalidate
Finish or named profile saves. Preserve the existing live blur setting behavior.
Interface shortcuts, including Stream's Ctrl+S, must be searchable and editable
alongside playback shortcuts, with the existing defaults preserved. Replace the
hardcoded reservation/dispatch split with native CONFIG_ITEM_KEY bindings used by
the editor, QML dispatcher and displayed menu hints. Conflicts identify the actual
command and require explicit reassignment. Preserve unsupported-global semantics
and normal shortcut editing outside onboarding. Deliver one verified normal update
after this integrated outcome passes; the prior minor-UI waiver does not substitute
for automated regression verification.

**M4 delivery reconciliation: COMPLETE.** Normal [1.1.6](https://github.com/Darkaxt/vlc/releases/tag/redesign-v1.1.6) from `bf45ca9748427279b08b995755c52f164f78e60d` is independently verified. [Reconciliation](resources/m4-1.1.6-verification.json) records current native/artifact evidence, retained original UI producers and the explicit one-release waiver of further manual minor-UI review. R83–R87 close under that authorized acceptance boundary; blockers and required deferrals are zero.

5 November final delivery instruction: publish normal release1.1.6 now with the
current M4 fixes and Interface blur control. The user explicitly declines more
manual review of minor UI details and accepts the higher-priority repairs already
reviewed. Supersede the unreleased1.1.5 delivery target. Further manual Settings,
context/submenu and both-engine panel review, including Record's corrected icon
and blur-degree tuning, is waived for this delivery; do not claim those new pixels
were manually accepted. Retain the existing composed evidence under its original
source identity, verify the coherent optimized package, runtime identities,
VLC/MPV/DV presentation and lifecycle, then publish and independently verify all
four assets. This changes the release acceptance boundary, not playback safety,
profile preservation, licensing, provenance or execution/resource requirements.

**M4 settings/menu parity, authorized 2 November 2026:** implement the complete
thirteen-category review at
`D:/VLC-Redesign/verification/settings-parity-20261102/settings-parity-review.json`.
The original Figma archive and inspected interactive prototype remain the visual
authority. Earlier M2/M3 delivery proves their recorded functionality; its generic
settings presentation and extra menu row do not establish settings parity.

R83 (M4): restore the distinct black header, truly rounded transparent exterior,
original selected/unselected artwork, compact information icons, fields, grouped
switch housings, sliders/ticks, spacing and scroll behavior. Reproduce each
category's ordered basic and expanded sections and integrate the missing controls
through the existing VLC/Qt/MPV owners. Preserve native option identities, ranges,
credentials, saved values, search, staged edits, save-failure rollback and Cancel.
Preserve explicit VLC/MPV selection and disabled-by-default video window resizing.
Use truthful platform/capability states for platform-specific operations; never
create a decorative working-looking control or silently substitute another action.
Correct prototype copy errors such as the duplicated Last.fm username label.
Auxiliary acrylic-host windows must inherit their owning player window's native
position and be cloaked before being shown, without accepting focus. A visible
window-style bit alone does not prove composited pixels; record DWM cloaking for
diagnosis while preserving the strict offscreen-placement requirement for all
app-owned windows. Only the separately identified OS input indicator retains its
existing private-desktop exception. A failed placement never permits another
input-desktop launch without repair and fresh exact-package private proof.
Remove the thirteenth main-menu preservation row while retaining the underlying
VLC commands through an appropriately themed advanced route. Global Settings
must remain directly reachable from player/library and keyboard. No default
profile, installation, real media history or OS setting is changed by validation.
Preserve the existing manual Welcome / Appearance Setup action through that
themed advanced route while keeping the reference main menu's twelve rows.

Backdrop clarification,3 November2026: the original General frame999:5047 uses
the#0e0e0e surface at95% opacity and a50px BACKGROUND_BLUR. Preserve that glass
appearance over actual player content. A QWidget-only PNG omits the Windows
compositor backdrop and cannot establish that the background blur is working.
An alpha242 tint or a successful native acrylic request alone is not actual
composed-picture acceptance. Verify the composed result without changing the
user's OS transparency setting or using desktop controls.

4 November user review accepts the remaining Settings presentation as close
enough, but rejects the actual window's gray/jagged corners and opaque backdrop.
Repair that composition before delivery. Apply the same rounded, content-blurred
background treatment consistently to all application menus, including player
panels, main/context/submenus and native command menus; preserve their reviewed
layouts and functional controls. Inspect the real volume widget as part of the
same outcome; the silent review launcher's dummy audio output is not a mockup
and must not stand in for functional volume acceptance with a real audio output.
Hide Advanced Options in every category without reference advanced controls,
including Library and Recording, even where the prototype shows an empty
disclosure. Preserve extra native settings through Search and the existing
themed All VLC settings route. This is an explicit correction to the reference.

Actual-window rejection,3 November2026: the user's General, Controls and
Playback screenshots reject the current corners/backdrop and several field
types/styles. Keep M4 ACTIVE and treat those as internal repair blockers.
Configure translucent native surfaces before binding/creating their handles;
verify the actual alpha format, not just an alpha-bearing widget PNG. Match
plain numeric track inputs (including native -1 automatic and0 first-track
values), free-text font families, left-aligned numeric editors without steppers,
reference field heights/corners, semibold action captions and readable expanded
choice lists. Do not hardcode the prototype's example selections as saved values.
The expanded Advanced Options bar remains neutral and its body preserves the
reference gap. Use a real optical-drive selector with custom device-path entry.
Keep additional native/fork settings reachable through Search and General's
themed VLC commands / All VLC settings browser, rather than appending generic
option-browser/engine rows to the reference category layout. Preserve the live
VLC/MPV switcher and every native setting's staged/save/cancel behavior.

Further source/reference reconciliation,4 November2026: Privacy frame3062:11911
has no Advanced Options disclosure; preserve its extra native options through
Search without adding that row to the reference page. Font-size editing must
accept its own displayed percentage/Automatic labels through later Save and
restart. Snapshot Original size must use the existing native -1/-1 dimensions,
preserving custom dimensions and distinguishing0's aspect-ratio semantics.

R84 (M4): strengthen acceptance to reject unexpected primary-menu rows and verify
all thirteen settings categories, their sections/control types, dependent states,
native behavior and persistence. Compare actual native pixels with the reference
at normal/narrow viewports and 100/150/200 percent DPI, including dark/light and
corner/backdrop behavior. Complete all related implementation before one
coordinated acceptance pass; repair failures and recheck affected workflows.
Retain applicable unchanged playback/DV evidence, verify native VLC/MPV handover
and protected state, and deliver one final normal optimized release with source,
separate symbols and checksums through the established channel. Independently
verify delivery and retained/weekly rebinding before obsolete-output retirement.
No Rust work, additional upstream integration, SDK recreation or release-folder
reorganization is authorized by this scope.

Further composed-window review,4 November2026: the normal826438e2 candidate is
rejected. Match the painted/native corner boundaries without white frame pixels;
the video context menu must open with its actual themed contents immediately,
without a blank opaque intermediate window. Measure construction/show/first-paint
separately, and verify actual content blur for Settings and context/submenus.
Both VLC and MPV video right-clicks must reach the same native popup workflow.
Replace classic application-brand cone references throughout the Qt interface
(idle, minimal view, banners, About/update, window/tray icons and fallback art)
with the existing original redesign cone. Preserve unrelated functional glyphs.
These are internal R83/R84 acceptance blockers in the same ACTIVE M4 stage.

R85 (M4), authorized4 November2026: selecting MPV applies the purple from the
user's mpv.io reference as the effective interface accent and uses the official
MPV emblem in the top-left player header. Apply the accent to both Qt Quick and
native menus/settings through the existing theme owner. Switching back to VLC
restores the cone and the user's existing VLC accent. Preserve stored custom
colors, profiles and settings; do not rewrite the saved accent on engine changes.
Use the official source artwork at native DPR rather than redrawing the logo.
Verify initial engine selection and live VLC/MPV switching, label/icon/color
consistency and saved-state preservation as part of this same complete M4 outcome.

R86 (M4), authorized4 November2026: the gear Playback panel stays open while
the user operates the playback control bar, including Play/Pause, seeking and
volume. Escape, clicking elsewhere outside the panel/control bar, selecting a
different panel, and clicking the gear again still dismiss it. Playback state
must not be changed merely by opening, retaining or closing the panel. Verify
the real pointer and keyboard paths in both engines.

R87 (M4), authorized5 November2026: add Background blur to Interface settings.
Use a native integer preference from0 to100 logical pixels, default50, preserving
the existing Figma blur strength. Provide the degree as an editable numeric value
and slider. Save applies it without restarting to Settings, native menus/submenus,
Qt Quick panels and library popups in both engines; retain it after restart.
Zero removes blur while preserving the existing surface tint and rounded clip.
Cancel and failed Save retain the previously applied value. Follow the native
shared draft/save/reset route, and do not change Windows transparency settings.

5 November actual Record-icon rejection (R84): the current normala8 candidate
still paints magenta. The SVG contains#f0f while the existing palette substitution
matches#FF00FF. Calling that substitution is insufficient evidence. Normalize the
source placeholder without changing the shape, then verify actual native icon
pixels and the composed context menu before release. Prior widget/menu results
that did not inspect Record icon pixels do not satisfy this criterion.

Actual overlay review,4 November2026: Settings and the native root context menu
now show content blur and clean corners in the current review. The player-settings
overlay remains only translucent: the synthetic video's diagonal/grid is still
sharp beneath it. This is a failed R83/R84 actual-picture criterion, regardless
of native region metadata or S_OK. Diagnose the existing PlayerVideoBackdrop
video-copy path and verify the corrected actual video blur in both engines before
normal release qualification. No new implementation stage is opened.

Idle-player correction,4 November2026 (M4): entering Customize Player without
media and leaving through Cancel, Escape or Save must show the black idle canvas
and the usual cone (subject to the existing background-cone preference), never
album artwork, lyrics or audio-only controls. Select the music view only for
started audio-only media, including paused audio; preserve embedded video and
audio visualizations. Verify idle/customization, audio/video replacement and
stop/end-of-input transitions with both VLC and MPV before final delivery.

README delivery addition, authorized3 November2026: after verification, update
the project README with clear attribution and direct links to the original
YouTube redesign video, the Figma community project and the relevant upstream
foundations. A side-by-side reference/current-player screenshot is permitted
when it illustrates the verified result; exclude private media and unfinished
captures. This documentation belongs to M4's final delivery, without a new stage.

**M3 delivery reconciliation: COMPLETE.** Normal release
[1.1.4](https://github.com/Darkaxt/vlc/releases/tag/redesign-v1.1.4), app source
`6288be3623fdeefb505f3f0c5ea5fd24bf0fcf2d`, satisfies the maintenance R71/R72
contract below. [Verified reconciliation](resources/m3-1.1.4-verification.json)
binds the upstream merge, native HEIF boundaries/grid decode, coherent stripped
assembly, VLC/MPV actual playback and lifecycle, four independently retrieved
assets, preservation, retained/weekly binding and obsolete-output cleanup.
Unchanged M2 UI/Figma/subtitle/preview acceptance is reused only under its
recorded source/runtime applicability. All current blockers/deferrals are
resolved; historical failed receipts remain failures. S8/M2 stay COMPLETE and
S9 stays NOT STARTED. The notes below preserve the authorized scope and the
resolved protocol failures; they do not reopen completed implementation.

**Weekly maintenance, 2 November 2026 (M3):** the existing authorized weekly
upstream integration and final delivery workflow applies R71/R72 to one incoming
commit, `8a47770f6333df6b60181329db5fdaad318bdb44`, after the delivered upstream
pin `c7834066e27cf07a2a15f1e8aab17c12df97e5d4`. Its only upstream production
change adds checked arithmetic to the HEIF grid destination offset. Integrate
through normal merge history and deliver version 1.1.4 through the existing
four-asset release channel. Verify the changed demux path and overflow boundary,
coherent enabled-plugin assembly, compiled version/update identity, packaged
VLC/MPV playback and preservation. Reuse unchanged 1.1.3 UI/DV acceptance only
with explicit source/runtime applicability. Use the retained optimized toolchain,
objects and dependencies; no configure/SDK recreation when its inputs are
unchanged. Independently verify delivery, update the retained weekly binding and
retire obsolete outputs after their consumers exit. M2 remains COMPLETE and S9
remains NOT STARTED. This records existing recurring authorization, not a new
product requirement or an approval checkpoint.

M3's normal MPV validation observed actual presentation but failed the required
foreground-preservation criterion. The normal Qt path lacks the no-focus flags
used by the diagnostic path; a Windows SW_SHOWNOACTIVATE startup hint did not
enforce the contract. Repair this current-stage execution requirement with an
explicit volatile `--qt-passive` launch option, false by default, applying Qt's
nonactivating/no-focus flags before the interface is shown. Do not save this
option into user preferences or change ordinary interactive startup. Verify
default window flags on an inactive desktop, then require the passive native
WS_EX_NOACTIVATE style in a fresh private placement proof before any further
input-desktop run. Preserve the failed receipt; do not waive its foreground
failure or repeat the failed protocol unchanged. This is required normal-runtime
verification integration, not an additional implementation stage.

The first passive inactive-desktop proof correctly rejected Qt's native style:
Qt6.8.3 retains `WindowDoesNotAcceptFocus` in its activation-message policy but
does not map it to `WS_EX_NOACTIVATE`. Keep the native-style criterion unchanged.
The Windows interface handler must add that style during Qt's pre-platform-show
event and preserve it in `WM_STYLECHANGING` for this explicit passive option.
Default interactive windows must retain their ordinary style. Preserve the
failed private proof and repeat affected checks only after this native bridge
has been integrated; no input-desktop launch was attempted from that proof.

The native bridge and default-focus criteria now pass in source6288. A missing
picture marker in a later run was followed by a direct binding read identifying
worker `Default` and input `Screen-saver`; it is not accepted as an active-desktop
presentation result. Bind future offscreen verification to WinSta0 with equal
worker-startup and input desktops before allocation/launch and again at readiness,
without switching desktops or dismissing the screen saver through automation.
The refusal test creates no player. Fresh SDR/P5 presentation with the same6288
binaries passes after both desktops are observed as `Default`, including native
no-activation style, no foreground ownership, EOF and release. Preserve all earlier
failed receipts and their limits; do not reclassify them as successful runs.

The2 November rendered-reference audit and user correction also reopen R52 for
the player chrome/menu. M2 must restore the interactive Figma main menu as the
priority: direct media/global actions, original two-tone vector icons, aligned
shortcuts, Recent/Profile submenus, keyboard operation and a direct Settings
route to the implemented Global Settings dialog. Reconcile the thin panel toggle,
HH:MM:SS time fields, sidebar list/section chevrons, volume→audio→subtitles→tools→queue
order and the reported Playback panel's tabs, aligned selectors and speed slider.
Preserve real engine switching and all required functionality; label its choices
VLC and MPV. Preserve customized layouts/profiles when updating stock defaults.
Compare actual native captures with the live prototype and original archive,
including menu/submenu/focus states and representative DPI. These are M2
acceptance blockers, not a new stage or grounds for a partial release.
The original main-menu frame 6062:13354 defines a375px card with4px outer
padding,367×48px primary rows,24px original gray/orange icons,14px labels,
aligned shortcuts and10px outer rounding. Preserve its twelve primary actions
and divider placement. Anchor the card4px below the title bar and32px left
of the overflow-button center, bounded to the available window. A separate
compact More VLC commands entry preserves
remaining native commands without changing that primary action hierarchy.

The user's2 November request authorizes producing the corrected1.1.3 release and
removing older release versions after independently verifying its download.
R78 requires an actual optimized application configuration (`--disable-debug`,
upstream `-O3`, `-g0`, QML debugger off), effective generated-flag verification,
and no debug sections/symbol tables in the portable runtime. Retain established
separate source/checksum/symbol assets; separate symbols are not installed runtime
payload. Reuse unchanged SDK/MPV/codecs. The global debug-to-release profile
transition requires one consistent application object cohort. Preserve installed
application/settings and Git history during release retirement.

**M2 First-run usability and fork identity is COMPLETE (2 November 2026).**
The reopened R52/R78-R80 criteria below passed in corrective1.1.3;
`resources/m2-1.1.3-verification.json` records final native/delivery/cleanup evidence.
The following paragraphs preserve the authorized requirements and original reopen reasons.
The user's post-release black-preview report reopens R80 acceptance for the
supplied4K VP9 MP4. Verify actual nonblank/changing popup frames around5:11 and
other distinguishable positions, not only request completion, timestamps or a
single synthetic color sample. Trace decoding, exported image, provider and
rendered popup; preserve bounded/cancellable work, cache/latest-position behavior
and truthful unsupported-engine states. R78 now includes one corrective1.1.3
release after the full repair and its delivery/retention/cleanup gates. Retain
the1.1.2 evidence below as historical qualification with its original scope.
The user's2 November icon report also reopens R52 for transport-icon sharpness.
Preserve the established control sizes, palette, focus/disabled states and action
bindings. Original-versus-redrawn comparison rejected changed silhouettes,
corner radii and stroke weights. Preserve the original Play/Pause/Previous/Next
SVG geometry and24-unit icon grid; correct shared icon rasterization so it is crisp at
100/150/200% and fractional display scaling. Inspect actual enabled-control pixels
in the native application; a larger raster asset or source-only SVG is insufficient.
Use the existing Qt/SVG path, without a new renderer dependency or ImageGen bitmap.
Retain the actual comparison and selection rationale; compare original and
remade rendering at native size and enlarged before release.
The user's requested VTracer comparison uses PNG renders of the exact original
Play/Pause/Previous/Next artwork, with24px and384px tracing inputs. Keep rounded
corners and silhouettes; sharpness means avoiding unintended edge diffusion,
not replacing rounded corners with pointed ones. Retain the original SVGs if
tracing provides no demonstrated benefit. Native rendering remains acceptance.
The user's whole-UI sharpness clarification applies the same audit to redesigned
library/navigation, queue, settings/track controls, layout editor and welcome
icons. Keep source raster requests appropriate to the displayed icon size and
actual DPR; avoid a second texture filter on native-size SVG glyphs. Do not
disable the intentional scaling/filtering of media artwork or seek thumbnails,
or change rounded geometry, typography or intentional backdrop blur to disguise
this defect. Distinguish the confirmed fractional-position resampling from other
possible causes; the supplied100% pause pixels match a direct24px SVG raster.
The user's2 November panel-collapse report extends this repair batch: the library
panel must hide without briefly exposing a strip of the window backdrop. Resize
the video consumer before committing its new placement and removing the panel.
Verify open/collapse transitions while paused and playing in both playback engines,
including the actual swapchain dimensions at placement, not only final QML bounds.
The user also changes R74's default: disable `qt-video-autoresize` by default so
opening/replacing video preserves the chosen window size in either engine. Keep
the explicit preference available, with the existing work-area bounds when enabled;
manual resizing, fullscreen and restoration must continue to work. Preserve
explicit user preferences rather than rewriting their existing configuration.
[Final delivery and requirement reconciliation](resources/m2-verification.json) verifies R52/R65/R73-R82 in normal release1.1.2 and records exact evidence applicability and limits.
The user's reports and icon reference authorize correcting welcome sizing,
shortcut assignment, false empty-library indexing, the Windows application icon
and the second-start automatic-update error. Deliver these together as one normal
1.1.2 update using the existing retained build and release channels. M1 and S8
remain COMPLETE; S9 remains NOT STARTED. Preserve installed profiles, existing
library roots/history, settings, both engines, previous releases and shutdown cancellation.

| Requirement | Required behavior and acceptance | Owner |
|---|---|---|
| R73 | On first run and explicit reopening, enlarge the existing main window enough for the welcome popup's1090x759 design plus its40px surround at the current interface scale, bounded by the screen's available client area. Do not shrink an already larger window or impose this welcome minimum after setup. Verify actual fresh-profile geometry and reachable content at100/150/200% and smaller available sizes. | M2 |
| R74 | Welcome shortcut tiles must use real action/configuration identities and support mouse/keyboard access to the existing native capture/conflict/Unset/Cancel/Save flow. Paired actions remain independently editable. Correct the fullscreen reference and provide a real configurable file-browser action with actual dispatch. Show saved assignments after closing the editor; preserve cancel semantics and restart persistence. Unsupported global bindings must not masquerade as editable Unassigned cells. Verify assignment, conflict, cancel, unset, persistence and actual action behavior without OS input. | M2 |
| R75 | A fresh library with no selected root must show its honest empty/ready state, with no phantom Indexing0%. Initialize idle state correctly and retain real discovery/parser busy/progress/completion events. Verify blank-folder Finish/Skip/restart create no roots, then explicitly add a synthetic folder and verify actual discovery, busy-to-idle and indexed results. Preserve existing roots/history and exclusions. | M2 |
| R76 | Use the user's referenced in-app flat orange cone for the Windows executable/resource and running-window/taskbar icon, retaining transparent multi-size artwork and license attribution. Verify actual packaged PE icon data and native application/window icon, including another launch. Do not alter pinned shortcuts or reset the Windows icon cache. | M2 |
| R77 | Correct the automatic second-start update failure: check the established Darkaxt/vlc normal release channel against the fork version, preserve the existing automatic-check/privacy settings and cadence, and notify automatically only for a verified newer normal release. Background network/parse failures stay quiet; explicit checks report a usable result/error and retry. Offer the verified fork release page rather than installing an upstream VLC binary. Verify actual HTTPS metadata plus controlled current/newer/malformed/network-failure cases, silent second start, manual retry and existing-profile preservation. | M2 |
| R78 | After integrated acceptance, commit/synchronize and publish one normal1.1.3 portable/source/symbol/checksum release, independently retrieve and verify the delivered identities and affected native behavior. Reuse unchanged1.1.1 evidence with explicit applicability. Verify retained build/weekly binding and clean exact expendable scratch after consumers exit. No intermediate release, cold SDK/VM setup, desktop takeover or shutdown. | M2 |
| R79 | Opening/dropping video from the library must enter the main video view deterministically when embedded video becomes available, while audio and subtitle-file drops retain their behavior. Automatic sizing must fit both width and height, video/chrome and native frame inside the current screen's available geometry at the actual DPR, without changing maximized/fullscreen state or defeating the explicit no-autoresize setting. Verify actual wide/portrait/4K input, drop, geometry, main surface and restart at representative scales, including the video-output/embedding signal order. | M2 |
| R80 | Remove multi-second repeated seek-preview stalls caused by precise cold decoding and cancel/restart on every pointer movement. Use bounded input-scoped decoded-image reuse, fast keyframe preview seeking and coalesced latest-position work without arbitrary timers. Cache hits must publish synchronously; retain a valid prior image while a new frame decodes and invalidate on input/engine changes. Measure actual uncached/cache-hit and continuous-hover latency on representative local media, verify correct input/position/frame content and normal cancellation/teardown. Do not call slow or missing frames instantaneous or claim MPV preview support without implementation/verification. | M2 |
| R81 | Disable the native Sub Track submenu when the active engine has no subtitle tracks; keep Add Subtitle File available and update enablement when tracks arrive/disappear, media changes or engines switch. Verify no-track, embedded/external-track and post-switch states through actual native menus. | M2 |
| R82 | The user's1 November instruction explicitly includes the two confirmed reference gaps: display cue timelines for the selected embedded text subtitle track as well as supported external files, and expose the reference's previous/next cue arrows and minus/plus timing controls. Keep cue timestamps aligned with the selected native track, actual playback time, delay and applicable FPS correction; changing input/track/engine must invalidate stale results. Extraction must be asynchronous, bounded and cancellable, without decoding video/audio or changing playback. Verify embedded SRT/ASS in Matroska and timed text in MP4, multi-track selection and engine handover, external text, image/no-track limitations, controls, persistence and teardown. Image subtitles retain playback with a clear unavailable timeline; no OCR or saved-library-playlist association is added. | M2 |

The earlier S3/S7 closure records describe the then-verified external-text strip
and adjustable offset. They do not establish acceptance of embedded text cues or
the reference's dedicated controls. R82 supersedes that scope limitation for this
authorized repair; those missing behaviors are now verified in M2 release1.1.2.

**M1 Upstream sync and optimized release is COMPLETE (1 November 2026).**
[Modern VLC Fork 1.1.1](https://github.com/Darkaxt/vlc/releases/tag/redesign-v1.1.1)
is the normal published release from `b84e7326e3d3e554120f3866fbe1c1acfa5ec6cc`,
including 243 incoming commits through upstream
`c7834066e27cf07a2a15f1e8aab17c12df97e5d4`. R71-R72 are satisfied and verified:
coherent plugins and both engines, affected integrated/native/color workflows,
optimized normal package, matching symbols, complete corresponding source,
independently downloaded artifacts/playback, unchanged protected profiles,
retained build/weekly binding and exact scratch cleanup. No M1 criterion,
blocker or tracked deferral remains. [Final reconciliation](resources/m1-verification.json)
records the delivered identities and acceptance limits. Local delivery is
`D:/VLC-Redesign/releases/1.1.1`; previous releases remain preserved.
S8 stays COMPLETE, S9 NOT STARTED; no implementation stage is ACTIVE.

| Requirement | Required behavior and acceptance | Owner |
|---|---|---|
| R71 | Produce one normal1.1.1 Windows x64 release with debug sections and unnecessary COFF symbol tables removed from every shipped PE binary. Keep separate matching symbols, verify unchanged executable sections/imports/exports/relocations across stripping, and enforce this in the maintained release pipeline. Strip MPV before generating its exact compiled runtime identity; never patch a compiled hash or weaken library verification. Reuse current dependency/object trees and relevant unchanged S8 acceptance. Verify the complete normal package's plugins, VLC/MPV SDR and Dolby Vision actual presentation/EOF/teardown, isolation and protected-state preservation. Include complete corresponding source, checksums and separately usable symbol artifact. Independently download and verify the published package/source/symbol artifacts and native behavior. Preserve1.1.0 and clean exact expendable scratch after consumers exit. | M1 |
| R72 | Integrate the pinned actual upstream master through normal merge history before deploying1.1.1. Fetch and record exact upstream/source revisions and actual divergence; retain the fork's Qt/QML/Figma behavior, optional MPV/DV, queue/history/settings and advanced VLC capabilities. Resolve compatible conflicts and reconcile changed build/API/dependency contracts. Do not retain baseline plugins under a changed ABI: build and stage a coherent current enabled-plugin set, updating only required dependencies with complete corresponding-source/notices provenance. Verify affected integrated workflows and native/display/state boundaries against the merged source; reuse only demonstrably unchanged evidence. Synchronize the verified merge/source, publish one final normal optimized update through the existing GitHub and versioned local portable delivery channels, and independently verify actual delivered artifacts/native behavior. Do not publish the superseded pre-upstream candidate, overwrite installed VLC/Nuvio profiles, force-push, reset user history or resume shutdown attempts. | M1 |

**S8 MPV and Dolby Vision integration is COMPLETE (31 October 2026).** The user's 29 October continuation, selected `Darkaxt/mpv-android-libdovi` source, NuvioDV behavior reference, live engine-switch request and compilation-pipeline clarification govern R67-R70. Correct P5/P8.1/P8.4 rendering, ordinary SDR/HDR10, integrated controls/state/handover and representative Figma presentation are verified. Output is BT.709/sRGB SDR; native Dolby Vision signaling and full Profile 7 FEL reconstruction are not claimed. [Modern VLC Fork 1.1.0](https://github.com/Darkaxt/vlc/releases/tag/redesign-v1.1.0) is a normal published Windows x64 release from `c8a1cdfd31a97e7ecc0bda772d4148f1f87a6b26`, with complete corresponding source/checksums and independently downloaded native verification. [Final requirement reconciliation](resources/s8/final-release.json) records acceptance, source/runtime identities, protected-state preservation, verified reusable build/weekly binding and exact scratch cleanup. No S8 criterion, blocker or tracked deferral remains. S0, D1 and S1-S8 are COMPLETE; no stage is ACTIVE. S9 remains NOT STARTED and planning scope. Canonical checkout/AGENTS, installed VLC/Nuvio data, Windows language, prior1.0.0 and unrelated WSL bindings are preserved. Intentional delivery is `D:/VLC-Redesign/releases/1.1.0`; reusable build is `D:/VLC-Redesign/build/windows-x64`. Exact temporary D/E roots are absent. Earlier proposed/active-status paragraphs below are historical provenance superseded by this verified closure.

**S7 Integrated verification is COMPLETE (29 October 2026).** The user's "start working on S7 then" instruction authorized R01-R04 final reconciliation, R52 whole-interface acceptance, R60 production asset/license audit, R61 real integrated workflows and the WASAPI correction, R62 reproducibility/recovery/source synchronization/final release, and the subsequently added R65 first-run font workflow. Every assigned criterion is verified in [S7 evidence](resources/s7-verification.json), with no remaining blocker or tracked deferral. [Modern VLC Fork 1.0.0](https://github.com/Darkaxt/vlc/releases/tag/redesign-v1.0.0) is published with binary, corresponding source and checksums, independently downloaded and checked against application commit `dd61caec26f8cc65f15d78369d09fb254196c810`; native normal-package checks pass. Installed VLC configuration/databases/language state and unrelated WSL bindings are unchanged. The temporary S7 VM, D: scratch and E: cleanup controller are absent after inspected cleanup. S0, D1 and S1-S6 remain COMPLETE. S8 is also COMPLETE; S9 remains NOT STARTED under the R66 planning contract. Separate installation over existing VLC and OS desktop-input/activation remain outside scope. Intentional S7 delivery is `D:/VLC-Redesign/releases/1.0.0`; earlier review deliverables remain preserved. Historical authorization paragraphs below are provenance; the current S8 authority above governs continued implementation.

**S6 is COMPLETE (28 October 2026).** R50-R51 and applicable R04/R52 acceptance, the normal isolated review folder at `D:/VLC-Redesign/S6`, preservation, cleanup and GitHub application-source synchronization are verified in [S6 evidence](resources/s6-verification.json). The explicit S6 boundary excluded an intermediate application release or installation over existing VLC. The historical authorization paragraphs below remain provenance; the current S7 authorization above governs.

On 28 October 2026 the user resumed S6 and approved the scoped move of its existing stopped `VLC-S6-20261025` disk from E: to `D:/Temp/vlc-s6-20261028/wsl`, including scratch-binding updates and verification. This updated the earlier E:-only build-storage constraint: active VM/build/dependency/test I/O used the exact task-owned D: root under the new storage hierarchy, registered as cleanup transaction `6d4725546ee6f1a572f441b4e7c628d9`. After verified normal review delivery, both scratch roots and the temporary disk were removed through inspected cleanup tickets, and only the empty S6 registration was retired; Ubuntu/Docker bindings are unchanged. All heavy Linux work must use the installed WSL gate with the declared shared VM/workload limits and one compiler job, verified at execution. This approval did not move the canonical checkout or remove prior review deliverables. Product scope and the S6 stopping boundary remain unchanged.

On 25 October 2026 the user authorized **S6 Customization and onboarding** (`already_authorized`), covering R50-R51 and relevant R04/R52 state, preservation, native presentation and verification. Figma remains the visual authority. Scope includes complete native integration, a normal isolated review package, verification, cleanup, commit and existing GitHub source synchronization, then stops before S7. No intermediate application release or installation over existing VLC is authorized. The 28 October disk-move approval changed the S6 active scratch binding to D: and preserved the canonical checkout and unrelated distributions. Complex execution used reviewable script files and short explicit invocations; native UI verification used app-owned events without OS input or activation. The current completion above governs; earlier authorization paragraphs below are historical stage records.

This is the authoritative specification for a VLC fork based on Juxtopposed's VLC Redesign. It records the complete product concept, implementation constraints, acceptance criteria, references, and stage ownership. The implementation plan must preserve these requirements. Reference images describe appearance; this document governs behavior and acceptance. Existing upstream functionality remains authoritative where the concept does not specify a change.

On 17 October 2026 the user authorized the first unfinished preparatory stage (D1 design-source readiness), then an explicit stop so its effort can be measured. This supersedes the earlier instruction to leave D1 unstarted. Scope includes reproducible offline decoding, required variant inventory, representative vector exports and screen reconstruction/validation, documentation, verification, commit and previously authorized GitHub synchronization. It does not authorize S1 or later VLC product implementation, compilation, installation, or application releases. Stop after D1 and report measured elapsed effort and remaining fidelity limitations.

For this bounded stage, representative outputs are the light player and global-settings screens at their source dimensions, plus monochrome/two-tone icon variants. Validate against native Figma exports where available, preserve source IDs and hashes, and explicitly record unsupported rendering features and fallback requirements. These are design-source tools and evidence, not a VLC player implementation.

The user subsequently authorized proceeding with S1 on Windows x64, as proposed, on 17 October 2026. S1 covers an unmodified source build, real playback, capability/configuration inventory, verification, commit and existing GitHub synchronization. All temporary files and testing must be under a task-owned folder on E:\ and cleaned afterward. This authorization supersedes the completed D1 stop boundary for S1; S2-S7 and installation/distribution/releases remain outside this turn's scope. Windows x64 is the confirmed baseline target, without restricting eventual additional platform scope. Linux portability should be retained in shared Qt code; native macOS, Android, iOS, and TV interfaces require separate scope decisions and are not implied to be implemented by a Qt desktop change.

On 18 October 2026 the user authorized the next stage, S2 Working redesigned player, then emphasized taking the time needed to match the Figma specification as closely as possible. S2 includes its complete R10-R14 player workflows, R04 preservation and R52 player presentation/verification, along with commit and previously authorized GitHub synchronization. Figma layout, typography, colors, icon geometry and relevant states are visual acceptance requirements; the earlier offline renderer limitations do not define the target appearance. Temporary files and testing remain on E: with cleanup afterward. S3-S7, installation, distribution and application releases remain outside this authorization.

On 18 October 2026 the user authorized proceeding to S3 Tracks effects and media tools. This covers R15, R20-R25 and their R04/R52 preservation, persistence and Figma presentation requirements, verification, commit and previously authorized GitHub source synchronization. S3 is COMPLETE following native acceptance, normal-runtime verification, cleanup and authorized source synchronization. No implementation stage is ACTIVE. The stop boundary remains after S3; S4-S7, proposed S8, installation and application releases remain unauthorized. Temporary builds and testing use the exact task-owned `E:/Temp/vlc-s3-20261018` root and are cleaned afterward. Native verification continues through app-owned diagnostics without desktop input or activation.

On 22 October 2026 the user authorized the next stage, S4 Library and media entry, and resumed it on 23 October. Authorization is already granted for R30-R33's library/open portion and relevant R04/R52 preservation, persistence and Figma fidelity, integrated verification, cleanup, commit and existing GitHub source synchronization. S4 is COMPLETE; no implementation stage is ACTIVE; S5-S7 remain NOT STARTED. Work stops after S4 for review. All new temporary/build/testing output uses `E:/Temp/vlc-s4-20261023`, registered before creation. Native verification uses app-owned diagnostics on an inactive desktop, without desktop input or activation. This supersedes the earlier S3 stop boundary. The user's updated standing release instructions govern final delivery after the whole authorized implementation; S4 does not publish an intermediate application release or install over the user's VLC.

On 23 October 2026 the user authorized continuing to S5 Preferences bookmarks and shortcuts. S5 is COMPLETE, covering R03 capability reconciliation, R14 menu/resume completion, R33 conversion/streaming organization, R40-R43 and relevant R04/R52 behavior. This includes Figma-derived implementation, actual native workflow/visual/persistence verification, cleanup, commit and existing GitHub source synchronization. Stop after verified S5; S6-S7 and proposed S8 remain NOT STARTED. Do not publish an intermediate application release or install over existing VLC. Temporary/build/testing output used the registered exact root `E:/Temp/vlc-s5-20261023`; cleanup transaction `6949e668fd74a0fc25d39ead599fb1cf` is APPLIED and that root is absent. Native audits used app-owned events on an inactive desktop without OS input or activation; the separate capture-only offscreen attempt did not activate a window. Verified product, normal runtime, preservation, cleanup and source evidence are recorded in [S5 verification](resources/s5-verification.json).

On 18 October 2026 the user selected OpenSubtitles.com for R21 and then explicitly added SubDL and SubSource support to the project. S3 implements these three concrete providers behind an explicit provider selection, using each documented API/terms and separate local credentials. Verify a real authorized search/download/association path for each supported provider; preserve visible authentication, quota/network/error and cancellation states. The user authorized obtaining an OpenSubtitles application key using the existing account; no payment or new provider account is authorized. Credentials and session data must not enter source control, diagnostics or published evidence.

### S3 subtitle provider contract

The user selected these providers before implementation. APIs are called only
after an explicit search/download action; no background account creation,
payment, translation service or bulk fetching is authorized.

| Provider | Documented boundary | Credential and result handling |
|---|---|---|
| OpenSubtitles.com | [REST OpenAPI](https://stoplight.io/api/v1/projects/opensubtitles/opensubtitles-api/nodes/open_api.json), [official integration guide](https://blog.opensubtitles.com/opensubtitles/how-to-build-a-movie-subtitle-finder-cli-with-python-and-the-opensubtitles-api): HTTPS `/api/v1/subtitles`, optional `/login`, then `/download` with the selected `file_id`, followed by its temporary subtitle URL. | `Api-Key`, application `User-Agent`, optional account bearer token. Show filename/language/release and quota; an optional login uses the provider's documented default/VIP host only. On 18 October the user authorized control of their signed-in OpenSubtitles browser tab. The free `DarkaxtVLCRedesign` development consumer was registered there, and its key was transferred into task-owned Windows user-bound encrypted staging without a plaintext file. A real authenticated API search returned results; download/association and native integration acceptance remain to verify. |
| SubDL | [Official v2 documentation](https://subdl.com/developers), [terms](https://subdl.com/terms): HTTPS `api.subdl.com/api/v2` title search, subtitle search and selected-file download. | User's own API key in a header; no shared embedded key. Preserve title/season/episode/language/file identity and explicit selection of archive members. No paid/AI endpoints. |
| SubSource | [Official documentation](https://subsource.net/api-docs), [terms](https://subsource.net/terms): HTTPS `api.subsource.net/api/v1/movies/search`, title's `/subtitles`, selected `/subtitles/{id}/download`. | User's own `X-API-Key`. Preserve title/season/episode/language/file identity and explicit archive-member selection. No paid plan changes. |

Credentials are session-only by default, blank after restart, never written into
the new settings document, diagnostic snapshots, URLs, logs or Git. A user may
cancel an in-flight request; completion is driven by network events, with no
application deadline or automatic retry. Show authentication/permission,
subscription, quota/rate-limit, network and empty-result states distinctly.
Changing input or provider invalidates pending association work. Credentials are
sent only to the chosen provider's documented API origin; temporary download
origins receive no API key or bearer token. Bound responses and extraction,
reject unsupported subtitle/archive types, and never extract provider-controlled
paths directly. Downloading must not overwrite user subtitles. Chosen downloaded
files use the same persisted, identity-checked association path as local files.

On 19 October the user clarified that subtitles must remain distinguishable. Preserve meaningful original filename/release, language and provider context in results, archive-member choices, downloaded filenames and the Qt track list. When a provider supplies no release name, show its public subtitle/file reference. Generic `subtitle.ass`/`subtitle.srt`, opaque UUID-only filenames, and indistinguishable result/track labels do not satisfy R21. Put title/episode identity first in compact track labels so provider prefixes do not hide it. Preserve the actual subtitle format and existing track information; verify differentiation after adding multiple subtitles and after restart.

## Reference bundle and attribution

- [Resource index and provenance](resources/README.md)
- [Editable Figma file](resources/vlc-redesign.fig)
- [Working editable Figma copy](https://www.figma.com/design/aZeRFRJVMwWl1uNS4I0Hdg/VLC-Redesign--Community-)
- [Archive contents, image inventory and hashes](resources/manifest.json)
- [Offline design inventory and decoding evidence](resources/design-inventory.json)
- [Source inspection manifest](resources/upstream-source-manifest.json)
- [Implementation stages and reconciliation](PLAN.md)
- [Windows baseline assessment and reproduction evidence](BASELINE.md)

Design: **VLC Redesign**, by **Juxtopposed**, [Figma Community original](https://www.figma.com/community/file/1691465999134370980/vlc-redesign), listed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). The original editable export is preserved byte for byte. The resource manifest identifies every archive entry and embedded raster asset. These are design references, not a declaration that every embedded font, media image, or trademark is licensed for use in a shipped application. Preserve attribution and audit production assets before packaging.

Keep access to the original Community design and the working editable copy for subsequent vector/icon exports. Obtain custom icons from the original Figma components in an appropriate vector format; do not reconstruct production icons from PDF pixels. Preserve component/variant names, export settings, provenance and attribution. The local `.fig` can be imported to recover an editable copy if hosted access changes. Figma account permissions and sign-in remain managed by Figma; never put account credentials or session data in Git. Links alone do not grant access to private drafts.

Local inspection decoded the embedded schema and document message without Figma: 12,563 nodes, 1,321 blobs, 38 component sets and 208 variants under the main Icon component set. Parent references and geometry blob indices passed structural checks; semantic encode/decode round-trip passed. That initial inspection established offline access to design data. D1 subsequently added selected SVG/screen export tooling and native visual comparison, with the fidelity limits recorded in the stage ledger. Pixel-identical rendering is not established. D1 closed at its authorized stop; the subsequent authorizations progressed through S1 and now S2, as recorded above, with a stop after the currently authorized stage.

The creator's explanatory video is [I Redesigned VLC After 25 Years](https://www.youtube.com/watch?v=ERFeOgqk324). The specification paraphrases the concept and links to the video instead of redistributing its complete captions. The private planning conversation is not required to understand or implement this specification.

## Product objective

Keep VLC's broad media capability while making ordinary playback, track selection, library access, and settings discoverable without repeatedly leaving the video. Retain the cone and orange default identity, compact rectangular controls with modest corner rounding, consistent two-tone menu icons, monochrome action icons, and a quiet interface around the media. Support both light and dark appearance and an adjustable accent.

The full concept is larger than a skin. Do not represent a visual mock-up or a player-only prototype as completion of the library, settings, subtitle, or customization requirements.

## Architecture and preservation requirements

| ID | Requirement and acceptance criteria | Stage |
|---|---|---|
| R01 | Modify VLC's existing Qt/QML desktop frontend and reuse its playback, playlist, media-library, track, device and settings integrations. Keep upstream engine behavior unless a requirement needs a documented change. The result must remain an actual VLC fork with upstream provenance. | S1, S7 |
| R02 | Establish a reproducible unmodified Windows build before changing product behavior. Record source revision, compiler, contribs, Qt version, commands and a successful real playback result. Then reproduce the modified build using the same documented environment. | S1, S7 |
| R03 | Preserve access to existing open-file, disc, device, network, conversion, streaming, capture, filter and advanced settings functionality. Reorganizing controls must not silently remove capabilities. Reconcile an upstream capability inventory against the new UI or an explicitly accessible existing dialog. | S1, S5, S7 |
| R04 | Preserve user media, playlists, history preferences, settings and existing identities. Define defaults, persistence, migration, reset and recovery for any new stored state. Verify restart and migration with representative existing configuration before accepting the feature that stores it. No destructive reset on failure. | S1-S7 |

The inspected root interface uses a compiled `qrc:` QML resource, and some preferences, effects, open and convert dialogs still use Qt Widgets. Build a fork rather than assuming an independently installable QML skin. Avoid a replacement libVLC application that would unnecessarily recreate existing integration. New infrastructure must serve an active-stage requirement.

## Player and controls

The complete compact single-row toolbar has a 472 logical-pixel minimum before
interface scaling: 116 transport, 60 seek, 80 volume, 114 track/tools, 30 queue,
24 outer margins and 48 group gaps. VLC's existing window-size owner applies this
layout constraint in player mode so controls remain reachable. Its separate
Minimal View retains its own size contract. No persisted setting is introduced.

S2 verification constraint (18 October 2026): the user stopped desktop automation,
not implementation. Audit through app-owned diagnostics without moving the system
pointer, typing into the foreground application or activating windows. Explicitly
compiled test hooks may dispatch real Qt input events, export measured instantiated
items/errors/assets and capture the app's render target. Keep hooks disabled in
normal builds, authenticate the exact local session, and distinguish dispatched
input, observed state, rendered pixels and physical presentation.

Video reference: 1:35-5:29 and 13:56-14:08. Inspect the `Player`, `Player - Light` and `Controls` frames/components in the [editable Figma design](resources/vlc-redesign.fig).

| ID | Requirement and acceptance criteria | Stage |
|---|---|---|
| R10 | Compact player layout: previous/play-pause/next on the left, track and queue controls on the right, cone-inspired volume control, thicker seek bar in the same bottom row between transport and volume controls, title and window controls above. Open actual media and demonstrate working play, pause, stop, previous/next, volume/mute, seeking and fullscreen through the new controls. | S2 |
| R11 | Keep title and controls available in fullscreen when the pointer enters the corresponding top/bottom region; hide them when it leaves, while retaining controls during keyboard focus or an open menu. Provide a discoverable hide-all-UI command and keyboard shortcut. Verify pointer, focus and menu transitions without flicker or trapped controls. Follow actual input/focus state; do not use arbitrary delays as synchronization. | S2 |
| R12 | Distinguish the current playback queue from stored playlists. Add files by picker and drag/drop; remove and reorder queue entries; show current item and total duration where known. Verify playback order and next/previous after edits, including an empty queue and unknown-duration input. | S2 |
| R13 | Separate subtitle and audio entry points, with audio devices in the audio view and video tracks reachable without a permanent video-track button. Verify real multi-track media, subtitle disabling, output-device changes, and the no-track case. | S2 |
| R14 | Retain an efficient context menu and a separate main menu with clear media/global actions. Show a resume action near playback controls when resume data exists, honor history privacy settings, and retain keyboard operation. Existing accessible commands must remain reachable. | S2, S5 |
| R15 | Provide seek-preview thumbnails and an optional audio waveform. These must represent the actual input and seek position. Keep normal playback/seek responsive, invalidate work on input changes, bound memory/disk growth, and make unavailable previews explicit for unsupported or nonseekable media. Static cover art is not seek-preview verification. | S3 |

## Tracks subtitles effects and playback tools

Video reference: 5:39-9:17. Inspect the subtitle variants in `Controls` and `Add Subtitles to Playlist/Folder` in the editable design.

| ID | Requirement and acceptance criteria | Stage |
|---|---|---|
| R20 | Add local subtitles to a file, folder or playlist. Offer automatic matching and manual correction, show ambiguous/unmatched items, save chosen associations, and restore them across restart. Verify a multi-episode folder, collisions, missing subtitle files, and changed media paths without silently binding the wrong subtitle. | S3 |
| R21 | Provide a remote subtitle-search path as part of the full concept, alongside local files. OpenSubtitles is the video's example, not an approved vendor or credential requirement. Select a documented provider contract before implementing this boundary; make authentication, network access and errors visible. Prove an authorized real search/download/association path. Local matching alone does not satisfy remote search. | S3 |
| R22 | Subtitle settings remain usable during playback: timing controls, relative and exact font sizes, font, outline and position, with applicable changes visible immediately. Provide a subtitle timeline showing cue positions and an adjustable offset. Verify alignment after seeking and restarting. Determine supported subtitle types explicitly; image-based or otherwise unsupported cue timelines must be indicated without breaking subtitle playback. | S3 |
| R23 | Save named per-show/file-group presets covering subtitle appearance/delay and preferred subtitle/audio language or track. Make precedence against global defaults and manual session changes explicit. Verify consecutive episodes and restart restore the intended settings without applying another show's preset. | S3 |
| R24 | Audio and video sidebars expose existing filters with useful presets and live feedback, including equalizer, compressor, spatializer, stereo width, color, crop, rotation/flip, aspect and other supported video options. Preserve backend ranges and semantics. HDR/resolution controls must reflect actual capabilities rather than promise conversions the engine does not support. Verify representative real filters and reset behavior. | S3 |
| R25 | Playback tools expose speed, reverse where supported, sleep timer, subtitle timeline/waveform toggles and metadata. Reverse must reflect the input's capability. A user-configured sleep timer is an intentional timed feature, not a synchronization workaround; cancellation, expiry and restart policy must be explicit. Verify actual engine behavior and clear unavailable states. | S3 |

S3 subtitle type contract: local SRT, WebVTT, ASS and SSA provide decoded text cue timelines. Existing VLC SUB/IDX imports and embedded image tracks retain VLC playback while reporting that no text timeline is available. The pinned core's subtitle-import extension list excludes standalone SUP; it is not advertised for matching/import. A generic associated-input experiment selected raw PGS but did not demonstrate correct rendered output, so that experimental route is not included. Embedded PGS rendering is verified separately.

## Library navigation and opening media

Video reference: 9:22-13:54.

| ID | Requirement and acceptance criteria | Stage |
|---|---|---|
| R30 | Make library access discoverable from the current media/folder title and a sidebar control. Support compact browsing beside playback and a full library with miniplayer/queue access. Drag actual library items into the queue without interrupting current playback. | S4 |
| R31 | Include videos/folders, music, network streams, playlists, recents and home. Folder browsing has breadcrumb/address navigation, search, grid/list/detail views and sorting including watched/unwatched. Music supports songs, albums, artists and genres using actual library metadata. Verify navigation and selection on a real indexed library, including missing metadata and empty categories. | S4 |
| R32 | Create/manage stored playlists; add selections from other views; pin playlists and folders; show recent and resumable media on home. Define watched state and pin persistence and honor history/privacy choices. Verify restart persistence and queue/playlist independence. | S4 |
| R33 | Provide clear entry points for files, folders, discs, network URL/playlist, capture device, clipboard, recent media, conversion and streaming/casting where upstream supports them. Separate the ordinary open path from conversion/stream configuration. Verify one real network playlist and retain the complete upstream action inventory; do not ship third-party channel lists by default. | S4, S5 |

R32's Home follows Figma `6261:15078`: Continue Watching, Listen Again and Frequently Visited Folders. The folder shelf ranks indexed, present local folders by their media's native playback counts, then last-played date, using only media still in native history. It is empty after history clearing and is not instantiated when playback history is disabled. Pins remain navigation shortcuts, independently of this ranking. Folder addresses are available through Go to folder address and Alt+D; the default chrome retains Figma's breadcrumb row.

## Bookmarks shortcuts and preferences

Video reference: 14:52-18:53. Inspect `Settings - global`, `Settings - audio`, `Keyboard Shortcuts` and `right-click menu` in the editable design.

| ID | Requirement and acceptance criteria | Stage |
|---|---|---|
| R40 | Add a bookmark with a direct action/shortcut and manage bookmark and chapter lists in the sidebar. Seek to real positions and distinguish user bookmarks from embedded chapters. Define bookmark persistence and verify it across restart. | S5 |
| R41 | Provide a directly accessible keyboard-shortcuts dialog and on-screen action feedback that can include the actual shortcut pressed. Preserve existing mappings unless an explicitly reviewed conflict requires change; present conflicts rather than silently replacing bindings. Verify remapping, focus handling, typing into fields and feedback preferences. | S5 |
| R42 | Reorganize preferences into General, Interface, Privacy, Controls, Playback, Video, Audio, Subtitles and OSD, Library, Network, Performance, Recording/Streaming, and Extensions. Basic and advanced options live within their relevant category. Explain options with visible help affordances and descriptive choices rather than unexplained numbers. Maintain a mapping to real upstream option keys, defaults, ranges, persistence and restart requirements; every inventoried option remains accessible. | S5 |
| R43 | Distinguish installable extensions/add-ons from internal modules/plugins. Preserve extension and module capability while placing internal technical settings in the appropriate advanced area. Verify an existing supported extension and advanced module settings remain reachable. | S5 |

### S5 state and native option contract

Preferences keep VLC's native option keys, types, defaults, choice lists and
ranges. The category/search presentation introduces no replacement settings
database. Unvisited controls leave their native values unchanged; Cancel does
not apply staged edits. Save uses the native config-file writer. A failed Save
or Reset restores the previous in-memory option values and reports the error.
Windows interface language retains the existing `HKCU/Software/VideoLAN/VLC/Lang`
owner and restart requirement; merely opening or saving other options must not
create or rewrite that override. Theme retains the existing interface-settings
owner. The existing `qt-accent-color` is rendered immediately after Save,
preserving `default`, `system` and valid custom colors; an invalid saved color
remains preserved and displays the Figma default until explicitly changed.

New native options are `qt-key-add-bookmark` (local `Ctrl+Shift+b` by default),
`qt-shortcut-feedback` (true), `qt-shortcut-feedback-key` (true), and
`qt-shortcut-feedback-duration` (1500 ms, range 500–5000). Missing options use
those native defaults without a migration. Existing core mappings win if a
legacy profile conflicts with the new bookmark default. Shortcut remapping
uses the native editor/file and takes effect after restarting VLC; conflicts
are presented explicitly, and fixed application-menu shortcuts cannot be
silently replaced. Feedback switches and duration apply after Save. Native
video OSD remains controlled separately by the existing `osd` option.
Explicit native command-line overrides retain precedence for the running
session, including the actual shortcut map used for action feedback.

Bookmarks retain native media-library identities, timestamps and storage. An
explicit Add may register a previously unknown external-media identity without
adding playback history. Embedded chapters remain read from the actual input.
No bookmark schema or parallel store is introduced. Full confirmed preference
reset restores native option/interface defaults while retaining media-library
records, bookmarks and subtitle files. Reset shortcuts stages only shortcut
defaults and still requires Save. Verify ordinary restart, cancellation,
read-only-save recovery, full reset, shortcut-only reset and an existing profile
without changing the installed VLC profile.
The General page maps the source confirmation/error control to `interact`,
updates to `qt-updates-notif`, file logging to `file-logging`/`logfile`/
`log-verbose`, and the developer-message switch to `qt-verbose`. That switch is
labelled "Developer messages" so its native Qt-only logging scope remains
clear; it does not enable the test transport in a normal build. Minor warnings
(`qt-error-dialogs`), log format and playback statistics remain in General's
advanced module sections. The native file writer must report replacement
failures and retain the original Windows destination; the Preferences dialog
uses that result for rollback and retry.
An unanswered native playlist-recovery prompt retains its recovery file and
setting when VLC exits; only an explicit decision consumes that pending state.
Shortcut capture and recovery prompts use owner-bound, nonblocking completion
so closing their owner cannot resume work against deleted widgets or models.

## Customization onboarding and presentation quality

Video reference: 18:58-20:43.

| ID | Requirement and acceptance criteria | Stage |
|---|---|---|
| R50 | Provide in-place drag/drop layout customization with clear insertion areas, removable/restorable controls, and a reset path. Save named profiles spanning layout and applicable settings, not just a toolbar list. Define the profile's setting coverage explicitly and verify switching/restoring profiles across restart without affecting media or credentials. | S6 |
| R51 | Offer onboarding with light/dark/system theme, accent selection and basic shortcuts; allow skipping and reopening it. Preserve prior-user settings. Verify first run, skip, completion and subsequent startup. | S6 |
| R52 | Apply the reference visual system consistently to player, library, sidebars, menus and dialogs, including the Qt Widgets boundary. Verify representative states at 100%, 150% and 200% display scaling, keyboard focus, accessible labels, readable contrast, resized windows and long/localized text. Figma's 1920x1080 examples do not mandate a fixed-size window. | S2-S7 |

S6 implementation contract (28 October, ordinary details preserving R50-R51):

- The saved source frames `6587:19923` (1920x1080 customization), `6648:20666` (profile submenu), `1899:3055`, `1902:3670` and `1902:6770` (1090x759 onboarding) govern geometry, Inter typography, colors, swatches and interaction states. Preserve the user's explicit single-row playback/seek arrangement. The customization palette sits over the real player, with controls editable in top/bottom left/center/right zones; window-close/minimize/maximize remain available. Save commits the draft; Cancel/close restores the accepted layout. Removal, restoration, insertion, keyboard alternatives and reset remain accessible even if the user removes every optional control.
- M2/R52 shortcut-page correction (1 November 2026): use frame `1902:6770` and the user's video reference for raised keycaps: 42px faces, 3px #373737 borders, 12px corners, a 6px lower edge, 16px Inter Light labels, 82px row pitch and horizontal paired keys separated by a slash. Split modifier/key faces, use arrow glyphs and uppercase letter faces while preserving the actual R41 mappings and full accessible chord labels. At the 1090x759 source size the title is at y60, shortcuts start at (62,154), and footer buttons are 100x32 at y671 with 8px spacing. Adapt column space to truthful longer native chords and narrow/localized layouts without clipping, reducing key size or stacking paired directions. The optional R65 font step precedes the final shortcut page; that final page has Back/Finish and no redundant Skip. Verify actual native geometry and screenshots at 100/150/200 percent, plus focus and remapped long chords. Functional shortcut checks alone do not satisfy visual acceptance.
- Named profiles explicitly capture the six layout zones, theme choice (system/light/dark), accent preference (including system/default), library Grid/List preference, and elapsed-versus-remaining time preference. These are the complete covered settings. Switching applies those values through their existing owners; explicit profile Save updates its snapshot, and Restore reapplies that snapshot. Profiles exclude media/queue/history/library contents, credentials, device/output selection, shortcuts and engine/effect/subtitle state. Existing upstream toolbar profiles are preserved; the redesigned layout has its own versioned presentation store. Ordinary edits do not silently overwrite a named snapshot.
- The new presentation store uses `redesign/customization-v1`, with bounded, validated version-1 JSON, known control identifiers and unique action/metadata control identities (decorative spacers/dividers may repeat), at most 64 controls per zone and 32 named profiles with nonempty unique names up to 128 UTF-16 units. Missing state uses the verified current layout and actual existing settings without writing defaults. Malformed/newer/oversized state is preserved read-only with visible recovery guidance; rejection leaves accepted state unchanged. Reset only restores the redesigned layout, never media, credentials or unrelated configuration.
- Onboarding reuses the existing first-run trigger and is reopenable from the menu. It starts with actual current theme/accent and the optional media-folder choice; privacy/network access is never enabled by skipping or finishing. Theme/accent selection previews live, Finish saves explicit choices and adds only an explicitly selected valid media folder through native ML, and Skip/close discards draft choices while recording dismissal so subsequent startup does not reopen it. Reopening never applies default layout, scans default directories or overwrites unrelated prior-user settings. Shortcut examples resolve actual configured mappings, rather than presenting Figma's illustrative keys as guaranteed bindings.
- Verification covers real cross-zone drag/remove/restore/reset/Cancel/Save, functional moved controls during playback, named snapshot Save/switch/restore/rename/delete and restart, empty/narrow layouts, rejected/corrupt/newer/oversized state, first-run/Skip/Finish/reopen/restart, prior-user preservation and theme/accent updates in previously created native dialogs. App-owned Qt events and rendered hierarchy/pixels remain the evidence boundary; no desktop input is required.

The S7/R61 integrated playback gate owns the observed pinned-upstream WASAPI startup-paused failure: resuming `--start-paused` input returned `AUDCLNT_E_NOT_STOPPED` and hit the existing started-state assertion. Normal startup followed by real UI pause, paused seeking and resume works. S6 verifies its independent editing/profile/onboarding criteria through that normal native workflow; it does not change the audio backend. Before final integrated playback/release acceptance, S7 must resolve the double-start lifecycle and verify actual resume, advancing clock and normal exit for both startup modes. This records a concrete required integration deferral, not satisfaction of that final criterion.

S7's R60 packaging audit also found the optional legacy default skin's Delicious font has no redistributable grant in the retained source. The package uses VLC's existing GPL FreeSans fallback and omits Delicious font bytes. The user's subsequent instruction adds R65: the first-run wizard downloads the unmodified optional font directly from its publisher into the active user's profile and the default skin uses that verified local copy when available. Automatic downloading is distinct from redistributing the font in the release. Preserve the native skins capability, existing custom skins and user settings; verify both font paths. The Figma interface's Inter font contract remains unchanged.

## Verification and final completion

| ID | Requirement and acceptance criteria | Stage |
|---|---|---|
| R60 | Maintain source/design attribution, original design hashes and an inventory of production fonts, icons and media licenses. Preserve VLC and dependency license notices and source provenance. A design reference screenshot is not an approved production asset. | S0, S7 |
| R61 | Verify real integrated behavior with representative local video/audio, multiple tracks, text subtitles, playlists, network input, missing media, nonseekable media, configuration persistence and keyboard/fullscreen interactions. Use redistributable fixtures or user-authorized local files. Record actual results and limitations, not just screenshots or mocks. | S7 |
| R62 | Document reproducible local packaging, configuration recovery and upstream synchronization. Run focused checks appropriate to changed boundaries; run broader suites when cross-cutting risk requires them. Reconcile every requirement before claiming the full redesign complete. Commit verified scope; perform and verify the final release under the user's standing release authorization after integrated implementation is complete. Do not publish intermediate stages; separate production installation remains outside stage authority. | S7 |
| R63 | Register this specification, stage plan, attribution, original editable Figma archive, archive contents manifest and editable-access links in the GitHub fork. Omit derivative PDF/PNG exports from Git per the user's updated instruction. Verify relative links, file integrity, upstream parentage and remote commit contents. Keep source/application behavior unchanged in this registration task. | S0 |
| R64 | Before VLC UI implementation, establish a reproducible design-source workflow from the retained `.fig`: reproduce offline decoding, identify required screen/component variants, export representative custom vector icons, and validate representative screen reconstruction against the original appearance. Record unsupported features and any required Figma fallback. Limit tooling to the project's design needs; do not build a general Figma replacement. D1 was authorized and completed on 17 October 2026; subsequent S1 authorization is recorded above. | D1 |
| R65 | Extend the existing first-run wizard with direct automatic download of the optional Delicious legacy-skin font from its official publisher. Show the font's source/license and a usable skip/fallback path. Keep the unmodified font in the active user's profile, outside the shipped binary/source packages; validate the download and cached identity before use. Preserve existing profiles/custom skins; reuse the valid cached font on restart/reopening without another download. Verify real publisher HTTPS download, native font use, fallback, cancellation, failure/retry and preserved/corrupt-cache handling. Keep first launch usable offline and retain the existing onboarding/theme/shortcut behavior. | S7 |
| R66 | After the existing plan, assess measured resource/robustness improvements through profiling and selective Rust migration. Establish a release-bound native baseline, select one justified bounded component, preserve existing UI/playback/state/capability contracts and explicit FFI ownership/lifetimes, then compare equivalent real workflows. Require a demonstrated component-specific benefit and no unacceptable regressions before retaining or broadening the migration. Do not assume a language change alone reduces resource use or begin a wholesale rewrite. Planning is authorized; implementation remains a future stage. | Proposed S9 |
| R67 | Add an explicit Windows x64 MPV playback choice inside the existing Qt/QML application. Keep VLC as the default and preserve the single existing playback queue, media identities, library, Figma interface and settings ownership. The user's 29 October clarification requires an in-player, on-demand switch without closing the application: release the outgoing engine before opening the same item in the incoming engine, preserve position and play/pause state, show the brief transition, and handle unavailable media/runtime without corrupting the queue or saved data. The saved startup default remains separately configurable. Bind the MPV library to an exact package/source identity and load it from this application's runtime only. A missing/incompatible library must produce an actionable error and leave VLC selection and saved data usable. Do not launch an unrelated installed player or replace the frontend. | S8 |
| R68 | Reproduce NuvioDV's correctly rendered Dolby Vision base-layer/RPU behavior on Windows: preserve metadata through decode and apply the correct libplacebo reshape/colorspace conversion. Verify real Profile 5 and representative Profile 8.1/8.4 input where fixtures are available, including actual pixels against a known-good reference and an intentionally incorrect negative control. Preserve ordinary SDR/HDR10 playback and record actual output colorspace/display capabilities. Retain the libplacebo correction for long-play OpenGL synchronization-object leakage when that path is used. Native Dolby Vision signaling and full Profile 7 FEL reconstruction are not claimed without corresponding implementation and real evidence. | S8 |
| R69 | Connect MPV to the real player workflow: local/network media entry, play/pause/stop, previous/next/queue order, seeking/rate, volume/mute, audio/subtitle tracks and delays, external subtitle association, fullscreen/keyboard, end-of-file/error transitions and resume/history preservation. Keep the existing VLC implementation and advanced capabilities reachable. Clearly identify a tool that requires VLC instead of displaying a successful change that the active MPV backend ignores. Use deterministic event/lifecycle ownership; no arbitrary retries, waits or competing audio/video engines. Preserve Figma appearance and representative theme/scaling/resize/accessibility behavior. | S8 |
| R70 | Deliver one final versioned Windows release after all S8 criteria pass. Include the exact MPV runtime, required licenses and complete corresponding source/build provenance. Independently retrieve and verify the actual binary/source artifacts and native integrated behavior, compare protected installed state, commit/synchronize verified source and retire expendable scratch through the installed cleanup helper. No intermediate S8 release or S9 implementation is implied. | S8 |

**S8 volume state contract:** retain native mmdevice's Windows audio session as the volume/mute persistence owner. With `volume-save` enabled, MPV joins the existing `{4533f59d-59ee-00c6-adb2-c68b501a6655}` session on the same endpoint; with it disabled, both use the existing nonpersistent default session and native launch-volume setting. Default routing remains eConsole, including device-change notifications. MPV supplies only the software amplification above unity under the same cubic curve, while existing native callbacks report the shared session's volume and mute. No new persisted volume/mute key, migration, reset, or recovery store is introduced. The source-bound MPV build carries the explicit session/default-role patch. Verify ordinary and startup-paused playback, attenuation/boost/mute, both handover directions and restart against a representative existing configuration before accepting this contract.

**S8 compilation contract (user clarification, 30 October):** provide one named,
resumable pipeline for the existing pinned SDK, MPV dependencies and player.
Persist step state, exact commands, full logs, real exit codes and elapsed/CPU
measurements; preserve successful prerequisites across repairs. Diagnose and
correct build failures while keeping the authorized task active, then resume at
the affected step. The user explicitly revoked the earlier pause-on-failure
condition. Do not blindly retry failed commands, restart completed dependencies,
or run component-level product acceptance between edits. Address the measured
Windows-filesystem compiler overhead within the existing resource limits; any
temporary compiler cache must preserve source bytes/path bindings, remain inside
the owned namespace/cgroup and release memory before VLC's large link. This is
R70 build reproducibility work inside S8, not another implementation stage.

## Execution constraints

Use one ACTIVE implementation stage at a time, prove a narrow real player workflow before expanding, and close each stage against every assigned acceptance criterion. Required later-stage work is not a substitute for a current-stage criterion. Record exact internal/external blockers, resolution conditions and affected requirements; do not describe ordinary unfinished work as blocked. Do not silently drop difficult features.

Prefer deterministic state transitions and actual completion signals. Do not add arbitrary retries, sleeps or timeouts to hide lifecycle or synchronization problems. Preserve dirty worktrees, unrelated files and user configuration. Use bounded resources for previews and background media work. Keep build-generated artifacts out of version control.

Any future Windows Gradle-driven work must use the user's shared `Local\Darka.AndroidGradleBuildGate` and prescribed resource profile. The S1 desktop baseline build uses no Gradle.

## Known decisions and risks before implementation

- Windows x64 is the confirmed S1 baseline. Additional platform coverage, naming/branding, and distribution channels remain to be selected; the current working identity is a Darkaxt VLC fork, not an official VideoLAN release.
- VLC 4 is experimental. Pin the build baseline and document subsequent upstream updates rather than claiming stability from a screenshot.
- Provider credentials and terms for R21 must be resolved before that integration. The three-provider contract above is authorized; the OpenSubtitles free development key is registered. No payment or new account was created.
- Thumbnail generation, waveform extraction and subtitle cue access need implementation evidence. Existing library thumbnails and subtitle delay controls are useful components, not proof those workflows already exist.
- Qt Widgets and QML both require integration for complete dialog coverage. Native macOS and mobile interfaces are separate.
- There is no validated whole-project estimate. The original conversation's 40-120 hours must not become a delivery commitment. Estimate from the verified build and screen/behavior inventory before scheduling implementation.

## Source basis

The [source manifest](resources/upstream-source-manifest.json) pins inspected files and hashes. Relevant paths at the baseline are `modules/gui/qt/Makefile.am`, `maininterface/mainui.cpp`, `qt.cpp`, `player/player_controller.hpp`, `player/qml/SliderBar.qml`, `player/qml/TracksPageSubtitle.qml`, `player/qml/controlbarcontrols/ReverseButton.qml`, `medialibrary/thumbnailcollector.cpp` and `dialogs/toolbar/controlbar_profile.hpp` under the Qt directory, plus `doc/BUILD-win32.md` and `modules/gui/Makefile.am`. See [upstream Windows build guidance](https://github.com/videolan/vlc/blob/392bc1d0abdb7396b6c97fef206efa1d23868e19/doc/BUILD-win32.md) and [experimental nightlies](https://nightlies.videolan.org/).

### S2 visual authority clarification (18 October 2026)

The user explicitly selected the Figma single-row player and then instructed: "Figma, always Figma." Figma is authoritative for visual appearance and layout whenever prose differs. R10 therefore uses the 54 px source bottom strip with transport, seek and volume in one row; the previous below-controls wording is superseded. Functional requirements, accessibility and responsive behavior remain required. The original source nodes and native Figma appearance govern typography, colors, spacing, geometry and menu/sidebar placement.

### Proposed post-redesign stage: MPV and the user's libplacebo fork

Current status is **S8 COMPLETE**, verified 31 October after its normal published delivery; S9 is NOT STARTED. The paragraphs below retain the original proposal; current R67-R70 and the authorization above govern execution. The user confirmed the Android source repository and the NuvioDV behavioral reference.

On 18 October 2026 the user suggested an additional final stage to support the MPV engine and their libplacebo fork for correct Dolby Vision rendering. Record this as **proposed S8**, NOT STARTED, after S7. This is a future scope proposal, not authorization to implement another engine during S2 and not an added acceptance dependency of the currently authorized stage.

Before S8 implementation, identify the user's exact libplacebo repository/revision and supported platform, establish the engine-selection/integration contract, and define the Dolby Vision profiles/containers and actual rendering/output acceptance matrix. Preserve VLC playback and state while proving a real MPV -> forked-libplacebo -> supported display path. A library name, decoded frames, SDR screenshot or nominal Dolby Vision flag alone does not establish correct Dolby Vision output. Any required architecture/scope changes belong in the authoritative specification before that later implementation begins.

### Proposed S9: profiling and selective Rust migration

On 29 October 2026 the user requested this improvement scope be added after the
full existing plan. S9 is **NOT STARTED**, after S8. This instruction authorizes
the specification/plan update and continued S7 work; it does not activate a Rust
migration or make S9 a prerequisite for S7 delivery.

Profile the completed application first. Bind the baseline to its source commit,
delivered package, build flags, hardware/drivers and representative media/input
conditions. Measure idle/playback private memory and working set, peak memory,
CPU, startup, seek latency, frame pacing/dropped frames and package size; include
GPU memory when relevant to the measured rendering path. Separate effects of
algorithms, copies, buffering and dependencies from effects of language choice.

Choose the narrowest component with a concrete safety, maintenance or measured
resource justification. Candidate areas include bounded parsing/archive handling,
configuration validation and background-job ownership. These are candidates,
not a requirement to rewrite every one. Reuse the existing upstream Rust/plugin
support when suitable. Initially retain Qt/QML and established playback/rendering
libraries. No generalized engine/provider rewrite is implied.

Before implementation, specify the selected component's real end-to-end behavior,
ABI/data/ownership/thread-affinity/cancellation/error contracts and measurable
acceptance thresholds. Preserve Figma appearance, settings identities/recovery,
plugin/action reachability and the completed VLC/MPV integrations. Rust safety
does not automatically extend across an incorrect C/C++ interface. Include
upstream synchronization cost in the assessment.

Prove one integrated migration, compare equivalent release builds and actual
workloads against the baseline, and report both benefits and regressions. Retain
or broaden it only when its documented benefit justifies its integration cost
and all preservation/performance criteria pass. If the experiment does not meet
those criteria, restore the verified native implementation through Git and record
the result without claiming a successful migration. Any retained implementation
requires the normal final release and independent delivery verification.

### Measured S2 visual contract

The visual authority clarification above applies to all rows. Source dimensions
are logical design pixels, scaled through VLC's existing interface scale; the
1920 × 1080 reference is not a fixed application-window size.

| Element | Original Figma source | Source geometry and appearance |
|---|---|---|
| Light player | `2425:13624` | 1920 × 1080; header 40 high; bottom controls 54 high; Inter Regular 14 for title/time. |
| Dark player with controls | `247:445`, controls instance `491:1928` | Same player geometry; chrome approximately `#1b1b1b`, foreground `#8f8f8f`; light chrome `#d5d5d5`, foreground `#2e2e2e`. |
| Bottom controls | `491:1779` | 20 outer margins and group spacing; transport 130 wide; play button 54 × 28 with radius 6 and accent `#d37918`; timeline group expands between transport and volume. |
| Timeline | `1908:7385` | Current/end labels 76 wide, gaps 8; track 28 high, radius 6, inset progress and 8 × 24 thumb. Reference group 1406 wide at 1920. |
| Volume | `491:1731`, `244:211` | 24 mute icon, gap 8, 88 × 28 cone with saved rounded outline; real engine volume and existing maximum. |
| Track actions | `491:1728` | Three 30 × 32 entries spaced 12; playback/tools, subtitles, audio. Queue action is separate with a 20 gap. |
| Track popups | `491:2243`, `496:2523` | Right aligned, 400 × 524, 20 from the right edge and 20 above the bottom strip; clamp to usable window height/width. S3 owns its effects/preset/tool expansions. |
| Current queue | `463:831` under `491:1781` | Right popup 400 × 946 at (1500, 60); 20 right/bottom gaps. Header tabs 50 high, count/actions row 68 high, rows 32 high at 44 pitch, 20 list insets. Existing bookmarks/chapter commands remain reachable; their expanded redesign belongs to S5. |
| Resume | Retained player resume instance | 519 × 52, 16 radius; 20 left/10 right insets; caption Inter 16 and a 146 × 32 Continue button, 10 from the right. Preserve the source's single visible action; Escape dismisses the suggestion. |
| Video backdrop | Effect style `1702:4101` on title bar, `491:1779` and resume | Retained background blur radius 50 beneath the source translucent fills. Blur the playing video, with bounds/visibility/radii following the actual controls; desktop acrylic and flat translucent fills do not reproduce this effect. |
| Production symbols | `modules/gui/qt/pixmaps/redesign/manifest.json` | Original outlined paths and full affine transforms; no acceptance of the earlier renderer's reflected-icon errors. |
| Typeface | `modules/gui/qt/fonts/redesign/source.json` | Inter variable font from the recorded official rsms/inter revision, bundled unchanged with SIL OFL license. Font SHA-256 `4989b125924991b90d05b2d16e0e388c48f7d5bb8b30539bbf9c755278d0ccaf`. |

At narrow sizes, reduce outer/group spacing and the volume width before hiding
the adjacent time labels; preserve all transport/track/queue actions and an
operable seek target. Elide or wrap real long/localized names without covering
neighboring controls. Verify actual Qt output in light/dark, at 100/150/200 percent
scaling, a reference-aspect window and smaller resized windows. Compare source
appearance and measured geometry; the offline screen rendering is not the oracle.


### Measured S5 visual contract

The retained Figma frames govern Preferences (`3046:9282`, Audio `3180:17398`,
Controls `6536:14482`, Extensions `6575:17137`), shortcuts (`2437:14832`) and
positions (`6320:13784`, `6321:14045`). Preferences use a 1048 × 865 logical
window, 50-high header, 200-wide navigation with 8-pixel outer inset and content
beginning at x=240. Inter Regular 14 applies to labels/fields, with 16-pixel
headings and Medium section headings. Native value editors are 34 high,
switches 68 × 32 and advanced expanders 38 high. Source night foreground is
`#8f8f8f`, fields `#191919`, selected navigation `#222222`, heading `#969696`
and section heading `#c6c6c6`; source day colors follow the retained palette.
Rounded root corners are 14 pixels with 95-percent source tint. Supported native
window backdrop effects use VLC's existing window-effects provider; the system
kernel is platform-owned and is not claimed mathematically identical to Figma's
50-pixel blur. Opaque appearance is retained where that provider is unavailable
or the existing backdrop preference is disabled.

Native combos and spin arrows use the original `71:868` outline, preserving its
path/matrix with explicit day/night tint and upward rotation variants. Shortcut
rows are 47 high, key cells 33, groups 64 and header 69/79; the source 391/359/270
column proportions scale with the usable window. Bookmark/chapter tabs retain
the source 50-high queue header, 64-high count/actions area, 32-high rows at
44-pixel pitch and 20-pixel list insets.

Clamp windows to available space. Below 900 logical pixels, stack value editors
beneath labels while keeping file/Browse controls together; scroll the actual
category and keep Save/Cancel reachable. Preserve long Unicode text in native
storage and accessible labels while eliding list rows. Native Qt captures and
measured geometry at representative 100/150/200-percent scales govern this
stage's comparison. Fully offscreen Windows capture produced a uniform grey
surface and was rejected, so no desktop-composed blur-pixel equivalence is claimed.
