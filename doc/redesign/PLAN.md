# VLC redesign stages and reconciliation

**M6 Font navigation, media preview and engine identity: ACTIVE (5 November).** R90–R95 are newly authorized. Investigation identified unconditional theme/font/shortcuts navigation, VLC's ten-second image-demux default, a fixed centered cone, session-only engine selection and an unthemed amber Playback-tab SVG. M5 cleanup and delivery closure passed; only M6 receives implementation. Acceptance: available-font forward/back bypass plus unchanged missing/corrupt/download/fallback flow; untimed still-image behavior across both engines and image/video replacement, preserving animation and explicit timed playback; engine-aware centered/window/taskbar identity; saved engine selection and restart in both directions without changing a failed selection; theme-aware two-tone accents with original artwork preserved; one normal1.1.8 release with independent delivered-package verification. These implementable gaps block M6 acceptance; no external blocker or tracked deferral. No M5 criterion is deferred into M6. These new requirements are not delivered in 1.1.7.

M6 coherent source is integrated before compilation. Native checks cover both-engine photo survival/replacement/animation/timed override, centered and HWND identity, successful selection/restart/explicit override, rejected switch/failed save and actual two-tone icon pixels. Available-font forward/back/reopen checks use the real cached font service. Fresh acceptance remains pending. Reuse the verified Ubuntu-hosted private toolchain namespace and Qt-only409-plugin guard; preserve all SDK/MPV/codec objects, optimized flags and native state. Task control is `E:/Temp/vlc-preview-1.1.8-20261105`; sustained native/build I/O uses exact `D:/Temp/vlc-s8-preview-1.1.8-20261105` and retained `scratch-share/preview-1.1.8`. Cleanup transaction `b4da9d0b04c7eb47593c482da9cfea68` registers these exact outputs. This is an intermediate source freeze, not verified completion or publication.

**M5 Onboarding and interface shortcuts: COMPLETE (5 November).** R88–R89 are delivered in normal [1.1.7](https://github.com/Darkaxt/vlc/releases/tag/redesign-v1.1.7) from `e9caba476b64c27817ef935532d22921bae28f43`. The complete wizard capture/Unset/Cancel/Escape/conflict/reassignment/Finish/restart/failed-save workflow passes at 100%, with layout, capture cancellation and Finish/restart also verified at 150/200%; no Preferences or Hotkeys window opens. Interface shortcuts including Stream are searchable/editable; saved Stream dispatch passes after restart. The four-field appearance profile contract and separate live blur getter are preserved. Actual native layouts inspected; optimized normal artifacts, VLC/MPV SDR/P5 presentation, independent downloads, retained/weekly bindings and obsolete-output cleanup pass. [Reconciliation](resources/m5-1.1.7-verification.json). Blockers0; required deferrals0; S9 remains NOT STARTED. Earlier compiler/checker failures remain in retained original evidence; all unaffected completed checks were reused against identical production blobs.

**M4: COMPLETE — normal1.1.6 delivered and independently verified.** Tag `redesign-v1.1.6` binds application source `bf45ca9748427279b08b995755c52f164f78e60d`. Current VLC/MPV SDR/P5 presentation, safe placement, foreground/lifecycle, all417 stripped mappings, four downloaded assets, retained/weekly binding and exact obsolete-output cleanup pass. The user explicitly waived additional manual review of minor UI details; no new Record/control pixels are claimed manually accepted. R83–R87 reconcile under that authorized release boundary. [Evidence](resources/m4-1.1.6-verification.json). Blockers0; tracked deferrals0. S8 remains COMPLETE; S9 remains NOT STARTED. Historical checkpoints below retain their original meaning.

**5 November delivery instruction: target1.1.6.** The user requests full
publication now and declines further minor-UI review. Finish the current coherent
Record/blur-degree delta, bump the packaged application identity, run automated
release/native presentation checks, and publish one normal1.1.6 release with all
four assets and independent delivery verification. New manual UI review is
explicitly waived, not falsely recorded as passed. Earlier composed evidence
retains its actual source identity. M4 remains the only ACTIVE stage until final
delivery/retention verification completes;1.1.5 remains an unpublished candidate.

**M4 Settings and menu parity: ACTIVE (2 November 2026).** User authorized
implementation of the complete thirteen-category live Figma audit. This is the
only ACTIVE stage; S9 remains NOT STARTED. M2/M3 delivery remains historical
evidence, not acceptance of the newly identified settings/menu defects.

**5 November current repair (R83-R87): ACTIVE.** Normala8 compilation/linking
succeeded in214/run37; its completed-symbol-manifest guard failed before symbol
processing. Exact411 unchanged mappings were verified and seeded in a new symbol
directory. Symbol-only215/run38 completed0 without a compiler/linker, with417
stripped mappings and group-empty/mount-release evidence. The eight artifact/native
qualification checks passed. User-launched normal Settings now visibly shows
content blur and smooth corners, but its context Record icon is still magenta:
the SVG's#f0f token does not match the colorizer's#FF00FF contract. Preserve that
actual rejection and repair the asset; strengthen native icon-pixel acceptance.
The user also authorized R87's Interface blur-degree control. Finish both in one
cohesive change before any further build. Verify0/default50/100, Cancel, Save,
restart and both rendering paths; reuse unchanged evidence honestly. M4 remains
the only ACTIVE stage, and1.1.5 is unpublished.

The resumed SDR placement verifier stopped before launching: the user review
created portable/vlc/vlc-qt-interface.ini beside its executable, so the package
clone's empty-profile assertion correctly rejected it. Preserve the live review
and its profile. Subsequent native qualification must clone a pristine extraction
of the verified ZIP, never a currently running review directory. Original failed
preflight and earlier completed checks remain evidence; no placement proof or
actual-picture clearance was produced by that preflight.

**5 November current continuation (R83-R86): ACTIVE.** Source `80a891c4`
passed the combined native menu/engine/transport and sidebar workflows in both
engines. All31 declared video backgrounds were bound before presentation; the
MPV purple/header emblem and restored custom VLC accent were inspected. Native
session49106 closed0 and protected profiles remained unchanged. The exact normal
pipeline213/run0036 completed0; its terminal immediate/original plugin-manifest
assertion closed the controller1 and was separately reconciled against all417
stripped PE mappings without changing bytes or repeating compilation.

Normal qualification26288 passed package/source/symbol checks, native VLC with
and without the library, and fresh private SDR placement. Its actual SDR run
presented video and closed0 but failed all-window placement: the upstream acrylic
`Static`/`dummy` helper was observed at `[0,0,6,6]`. Do not repeat that input-desktop
launch. Source created the helper at the origin, showed it, then cloaked it.
The owned inactive `acrylic-host-probe` reproduces the origin placement and proves
that owner-bound placement plus cloaking before ShowWindow succeeds. Its process
closed0/resources closed, and its desktop never became the input desktop.
The cohesive repair changes only that helper's production creation/cleanup and
the passive observer/private placement check; all non-Qt plugin/SDK/MPV inputs
remain retained. Complete one same-mode incremental normal Qt continuation,
fresh whole-window SDR/P5 placement/presentation, actual composed menu/panel
pictures and final1.1.5 delivery. M4 remains ACTIVE; no deferral or second stage.

**4 November paused-overlay diagnosis (R83-R86).** Normal211
(`66f86108cd684ef7b46ba49cd1baec45`) was scoped-stopped after the actual gear-panel
capture rejected sharp video under its translucent fill. Its original session
closes137/group empty/no OOM; retained SDK, QtGui, MPV, codecs and409-plugin cohort
remain intact. No compiler failure, second stage or release is implied.
The user-launched observation player independently shows correct native region
metadata but sharp paused video; after the user resumes/pauses, actual captures
show the intended blur. The small Windows probe reproduces the exact late-copy
failure after ResizeBuffers without Present, and proves that binding the same
clipped background before the resize preserves its picture. Keep those receipts
at `native-player-panel-owned-profile/manual-observation` and
`panel-swapchain-probe/{paused-resize,early-bound}` in the existing D: task root.
Source now materializes the declared QML backgrounds and prebinds their native
copies before the vout's first presentation, retaining hidden instances instead
of allocating by currently visible ordinal. The combined native pass above now
covers this lifecycle; actual composed normal blur remains required.
R85 source uses the unchanged official pinned MPV gradient SVG and the sampled
reference purple#420042 as an effective accent; stored VLC/custom colors remain
unchanged. R86 uses Qt's outside-parent dismissal rule with the control bar as
the gear popup parent: transport retains the panel; Escape/outside/gear/another
panel dismiss it. The original captured layout root and geometry are preserved.
Startup/live engine identity, custom-color restoration and real Play/Pause
retention passed in the combined native workflow above. The remaining window,
actual composed-picture and delivery criteria remain internal acceptance blockers.

**Latest4 November normal826 review: REJECTED.** The user's actual screenshots
show mismatched native/painted radii with white edge pixels, a slow blank opaque
video context menu, absent content blur and classic cone artwork. Preserve
`D:/Temp/vlc-s8-settings-1.1.5-20261102/composed-rejection-826438e2/review.json`.
These are internal R83/R84 repair/acceptance blockers; no user approval is pending.
Current review now shows the intended underlying-content blur and clean Settings
corners; the exact source20265f45/Qt14387b62 WGC capture is retained at
`backdrop-review-native-current/composed-settings` with unchanged foreground.
The user confirms it works. This is diagnostic-source visual proof, not normal
release qualification. Context capture found the popup already closed; preserve
the user's root-menu screenshot and still inspect the submenu/normal package.
The same review exposes Record's magenta template color: the QAction bypasses
the existing ColorizedSvgIcon path. Archived Record variants are gray#8f8f8f
(default) and orange#d37918 (active). Route this action through the same palette
colorizer as adjacent actions. Normal210 was stopped before completion using its
exact owned ticket; exit137/group empty/no max/OOM, dependencies/objects retained.
This new bounded icon correction must be included before final normal acceptance.
Focused209 (`ec97458032ea41e39a46ec4196151eff`, source20265f45) now closes0,
Linux group empty/private mounts released, peak1715535872bytes, no max/OOM.
Current diagnostic Qt is14387b6263ad5075f8abb3266832691da44ba609ae1338f1b9202ef8deacaff6.
Original native session71930 now closes0: both-engine context/deferred-submenu,
live handover, real WASAPI volume and menu teardown pass. Complete Settings at
100/150/200%, icons and both-engine idle/customization/audio/video/EOF pass.
All three current category contact sheets, full General at each scale, Controls
and Playback at100%, the populated context bitmap and four idle/audio/video
captures were inspected. These establish widget layouts, not compositor pixels.
Current reconciliation is `native-content-checker-acceptance.json` plus
`native-content-widget-picture-review.json` in the existing M4 control directory.
Unchanged policy/playback/profile/preview/first-run/lifetime receipts retain their
producer identities; guarded source equality and fresh affected workflows bind
them to20265f45. No duplicate native acceptance is needed for this unchanged code.
The checker corrections are test-only: this Windows host rejects border-color
readback although setting it returns S_OK, and the context parent is VLCMenu,
not QMenu. The standalone border probe and original failed results are retained.
The attempted composed capture remains FAILED: its inactive-desktop preflight
finds missing WS_EX_NOACTIVATE on the test dialog, so no input-desktop launch or
capture occurs. Preserve `native-content-composed/private-metadata-fix/result.json`.
The user-started `backdrop-review-native-current/review-settings.cmd` binds the
current optimized diagnostic-source runtime with diagnostic transport disabled
and its own profile. It is a visual review input, not normal release qualification.
Normal package preparation and its exact actual composed-picture gate remain required;
neither native graph readiness nor QWidget PNGs qualify actual blur/corners.
Build207 (sourcee4d65439) closed0, group empty and private mounts released,
peak1718808576bytes, no max/OOM, with409 retained non-Qt plugins. Its first
complete menu workflow verifies real WASAPI controls and live MPV handover,
then rejects native content composition with E_INVALIDARG. Exit0 and protected
profiles are verified; this is a failed product acceptance, not a crash.
The standalone Windows API probe reproduces invalid existing-root parenting,
legacy-mode shared-thumbnail updates and restoration of a still-parented visual.
Detaching/reparenting in one commit, retaining ENABLE3D on updates, and removing
the UI child before restoration each return S_OK in that same probe. Apply these
ownership/protocol corrections together, then repeat affected acceptance using
only the changed effects object and GUI link. The repaired QtGui archive and all
other compiled objects stay retained. No SDK/codec/configuration rebuild is needed.
Actual native/composed acceptance and normal delivery remain required.
The focused208 continuation closes1/group empty without max/OOM before GUI
link: Qt's QStringBuilder expression needs materializing as QString for QVariant
property conversion. Correct that diagnostic label and resume the affected object;
the API protocol repair and all retained dependency/object inputs remain intact.
The12 passed underlying normal205 checks remain historical applicable evidence,
not acceptance of the rejected composed picture. A standalone retained-Qt probe
compares animation with direct popup presentation; it does not rebuild VLC/Qt.
The cohesive source repair is prepared: live app-window content beneath each
native UI, one exact DPR-scaled clip, no system acrylic tint/border/rounding or
Qt fade/roll substitute, deferred context submenus and MPV right-click dispatch.
Every Qt brand alias now uses the existing flat cone; the vector preserves all
original paths/transforms and rasterizes pixel-identically to the current app PNG.
The Qt integration patches only one backing-store implementation file, publishing
an opted-in typed RHI/swapchain pair; no header/API/ABI or global flags change.
Source syntax, bounded patch applicability and the icon comparison pass. Actual
native integration, composed picture/timing, affected regression workflows and
normal delivery remain internal blockers. Reuse the retained QtGui object graph
and exact409 non-Qt plugin cohort; no SDK/bootstrap or codec rebuild. M4 stays
ACTIVE;1.1.5 is unpublished and no later stage or partial release is authorized.

**4 November composed-window review: REJECTED; M4 stays ACTIVE.** The user
reviewed the current normal Qt63bb package, accepted the other Settings styling,
and again rejected jagged gray corners and absent content blur. Read-only live
inspection confirms a WS_EX_LAYERED raster window with a complex integer region;
DWM type3/S_OK did not prove the required picture. Repair actual composition,
then apply the same glass background to all application menus as now requested.
Hide empty reference disclosures in Library/Recording and every equivalent
category, preserving native Search. Trace the real volume widget with a real
audio output; the isolated visual launcher currently selects a dummy output.
The cohesive source repair, affected native workflows and bounded manual
widget/menu picture review now pass as recorded below. Normal stripped assembly,
fresh safe presentation and actual Windows-composited corners/blur remain
acceptance blockers; no release is running. Preserve the former rejected review
package and all applicable prior evidence until the qualified replacement exists.

**4 November idle/customization correction:** normal assembly has not started.
The user reported the music placeholder after leaving Customize Player without
media. Player.qml selected audio solely from the absence of embedded video;
require started audio tracks without video tracks and provide the black/cone
idle canvas. Build204 (`8daad442430e4df88f37fc51febbadb5`, sourcee5558c75)
closed0/group empty/private mounts released, peak1715175424 bytes, no max/OOM.
The complete both-engine idle/customization/audio/video/Stop/EOF acceptance now
passes. Cancel/Escape/Save show the cone when empty; paused audio keeps its
artwork. Four focused native pictures were manually inspected. MPV video pixels
are outside its Qt Quick grab and still require the normal presentation gate.
Original pre-dispatch target, MPV terminal-notification and clipped-viewport
checker failures remain recorded; only unfinished closed cases were resumed,
without rebuilding the unchanged binary. The canonical acceptance binds the
fresh idle proof and unchanged203 menu/settings/texture owners explicitly.
Normal optimized assembly, actual composed blur/corners and final delivery
remain M4 blockers;1.1.5 is unpublished.

**Build203 native/widget reconciliation:**203
(`0929686267e2488684f6fb180b5140a0`, session53743, sourceaa654113)
closed0/group empty/private mounts released, peak1715171328 bytes, no max/OOM.
The complete main/Recent/Profile/Playback/audio/subtitle/queue/native-command
workflow passes, including real WASAPI volume and live engine handover. Nested
native QMenus have composition-only D3D surfaces, no integer regions or legacy
layered bitmaps, and the smooth-corner preference. The separate quit-with-menu-
open check initially hit its own clipped default viewport before Settings
dispatch, then resumed only that closed case using the reference viewport; exit0
proves callback teardown is repaired. Preserve the original failed checker result.
Six successful202 workflows retain their original producers/hashes under the
bounded owner-only source guard. Seven affected Settings pictures and ten menu
pictures were manually inspected, using an already settled queue capture rather
than its transition-start frame; this is explicitly not composed blur evidence.
The normal placement observer also records immediate native ancestry, accepting
DirectUIHWND only as an observed same-process child of the exact System32
InputSwitch indicator. Fresh normal SDR/P5 placement remains required. Keep M4
ACTIVE until the normal/composed and final delivery gates pass.

**Build202 affected reconciliation:**202
(`c2d6271488f44e3497ee53996dcb6877`, session28450, source2a9ec390)
closed0, group empty/private mounts released, peak1713422336 bytes, no max/OOM.
The retained-object green probe now measures attach1/detach0/old-window0/new1/
final0. The thirteen-category native composition survey, complete affected
Settings input/save/restart at100/150/200%, both-engine sidebar transitions,
first-run teardown and actual reported-media preview workflows pass. The native
menu workflow reaches real WASAPI volume, live engine switching and all Quick
panels, then its new checker wrongly reads a visibility field absent from the
already-visible widget list. Its resulting quit with the native commands menu
open exposes a real teardown access violation in VLCVarChoiceModel's callback
removal. Preserve the closed failure and dump. The parentless Preferences dialog
survives DialogsProvider destruction and keeps interface callbacks after the
interface-close cleanup returns; destroy that owned dialog before releasing its
interface dependencies. Correct the checker and require quit with the native
menu open. Reuse202's unchanged successful workflows under explicit source
guards; repeat the affected complete menu workflow after this cohesive repair.
Actual composed normal-package blur/corners and final delivery remain required;
M4 stays ACTIVE and1.1.5 unpublished.

**Build199 rejected native result:**199
(`a2fb8f51b3a342e58db04517132d8f82`, session96841, source942cb9a26b)
closed0/group empty/mounts released, peak1715392512 bytes, no max/OOM.
The four coordinated affected workflows still reject the same native flag and
texture-detachment paths; the source942 repair is not accepted. A never-visible
Windows probe on an owned inactive desktop proves NOREDIRECTIONBITMAP remains
fixed to its CreateWindowEx value: direct SetWindowLongPtr and both native
message return paths cannot add/remove it. Replace the ineffective style filter
with a scoped Qt creation policy before native QWidget creation, preserving
explicit overrides and ordinary/GL windows. Source tracing also finds that the
texture observer overwrites its old window before disconnecting its render
callback, then never initializes one on the replacement window. A bounded
retained-object native probe200 (`231cb71793f54aa9b2ded03fc221e311`,
session12672) compiled, but its standalone link omitted the observer's configured
atomic library.201 (`e119e21cbd2143fa8b2ec15c32e5a131`, session60116)
resumed only that link, closed0/group empty/mounts released, no max/OOM. Its real
native red result is exact:0→1 consumers on attach, still1 after detach and0
on the replacement window. All probe windows remained hidden; native resources
closed with the input desktop unchanged. The integrated correction scopes the
Qt native creation policy at widget polish, restores its exact prior environment,
and rebinds the observer before replacing its captured window. The failed style
filter and live-QML workaround are removed. Green lifecycle proof, affected
native/player picture acceptance and normal/composed delivery remain required.
Preserve199's failed receipts and200/201's diagnostic producer identities. M4
remains ACTIVE.

**Build196 locality correction:** original196
(`85c6b3fe8f0f400db79602557c11e1d0`, session56256) was stopped deliberately
through the supported exact-owner control after dependency evidence showed an
avoidable62-dialog invalidation from the popup helper declaration. It closed137,
group empty, peak966803456 bytes and no max/OOM events. This is not a compiler
failure or pause. Keep the helper wholly in Qt startup and restore the two
shared dialog files byte-for-byte to their qualified67fb contents. For only
those reverted files, verify original Git-blob identities and normalize their
source timestamps to their last content commit, recording that restoration.
Preserve every completed object and resume the same failed player step after
the exact closed196 interruption; no SDK/configuration/cache reset.

**Build197 compiler repair:** original197
(`fcf4b17cc1ba4b4897a18c264c90279a`, session30205) closed1 with an empty
group, released private mounts, peak1501159424 bytes and no max/OOM events.
The failed player step reports the pinned MinGW headers' missing
`WS_EX_NOREDIRECTIONBITMAP` macro in win32windoweffects_module.cpp. Use the
same numeric flag value already used by this module. Retain all successful
objects and resume this failed step under its original pipeline; do not reset
the SDK or replay acceptance before the complete assembly exists.

**Build198 native repair reconciliation:**198
(`e11275d257224055894824bb9354cd3f`, session94754, source4a195f2968)
closed0, group empty/private mounts released, peak1715757056 bytes, no max/OOM.
Real WASAPI keyboard/mouse volume and paused VLC→MPV→VLC handover pass in the
menu workflow; both-engine paused/playing sidebar transitions pass. The first
volume observation was a checker-focus error (Right sought ten seconds under
OtherFocus), cancelled explicitly with clean exit and preserved; real Tab focus
corrected it without an application rebuild. The complete affected native pass
then identified two internal blockers: no native no-redirection bit after show,
and stale texture observations during popup/view teardown. The initial
style-regeneration/non-live-chain hypotheses produced199, whose native rejection
and corrected creation/observer diagnosis are recorded above. Preserve the
original failed receipts rather than treating those hypotheses as acceptance.
Actual native/composed and final delivery gates remain unsatisfied.1.1.5 is
still unpublished.

**4 November normal-package qualification:** application source
`67fb8cd807d4cdaf010ed7706561eab380699513` has passed packaged VLC playback
with/without the media library, normal MPV lifecycle, fresh inactive placement
and actual offscreen SDR/P5 presentation with natural EOF and clean release.
Portable/source/symbol archives, all417 stripped PE/symbol mappings, the410-plugin
cohort,121 dependency sources, unsigned policy and full protected-profile
comparison pass. No diagnostic hooks ship.193 completed Qt compile/link but
failed when re-splitting an already-stripped retained plugin without its symbol
record.195 (`25f6b217118f4e168522122b559bb73b`) resumed symbol packaging only,
closed0 with empty group/released private mounts and no max/OOM events; no
compiler/linker ran during recovery. The409 exact retained mappings are restored.
Qualifier case-name/source-carrier errors and the first inactive InputSwitch
child-window observation remain preserved. A fresh ancestry probe identified
the same-process OS indicator child and passed strict placement before any
input-desktop launch. No accepted playback or full UI matrix was repeated.

R83/R84's **actual composed Settings blur/corners was rejected by the user**. The
current normal package's isolated, user-operated review launcher is
`D:/Temp/vlc-s8-settings-1.1.5-20261102/backdrop-review-rendering/review-settings.cmd`.
Its binding records Qt SHA256
`63bb4d2c8349a06ed5a441b4714b6f8386f8495caecc839a50152b1f8764847b`.
It opened synthetic media using a separate profile; the supplied composed
screenshot is failure evidence. No agent desktop control or real profile change
is authorized. Raw widget alpha/DWM readback is insufficient. Complete the
cohesive rendering/menu repair before incremental Qt-only build and affected
acceptance. Reuse unchanged qualification evidence where applicable, then
publish one normal1.1.5, independently verify delivery, and complete
retained/weekly rebinding and obsolete-output retirement.1.1.5 is unpublished;
the stage and overall outcome remain incomplete.

**4 November repair acceptance:** managed192
(`038e53e23ca24049ad584a3d09dc8d2f`) compiled source
`c1380668f2f89dcc6531cd3e0e9dfe3cfa784d18` and closed0 with an empty Linux
group, released private mounts and no max/OOM events. The affected native
Settings workflow and manual widget review now pass: formatted font-size
Save/restart, native original snapshot dimensions, mouse/Tab/mouse focus,
Privacy without an extra disclosure, staged Save/Cancel/locked-file rollback,
both-engine restart persistence, missing fonts and history. The fresh full
protected-profile comparison passes. Successful unchanged category layouts,
menu/profile/playback/policy evidence retain their original producer identities.
Original focus-proxy/disclosure checker failures and a concurrent external
Nuvio profile-write comparison remain false in preserved receipts; they were
diagnosed without another player build or excluding protected paths. Its normal
assembly/playback/artifact gates have subsequently passed as recorded above.
Actual composed blur remains unverified and1.1.5 unpublished.

**3 November actual-window rejection:** M4 remains ACTIVE. The user's composed
General/Controls/Playback captures reject the gray corners, absent blur, wrong
track/font input types, numeric alignment/steppers, popup foreground, action
typography and expanded Advanced Options treatment. Earlier paint/layout checks
remain historical evidence with their original producer identity; they do not
establish current visual acceptance. The normal1.1.5 candidate remains unpublished.
The verified source repair configures native alpha before handle creation, restores
the reference field/disclosure styles and input types, preserves editable native
values and exposes extra native settings through Search and General's themed
commands. Reuse the core, codecs, MPV and409 non-Qt plugins; no second stage,
SDK initialization or full dependency rebuild is needed.

The original rendering continuation190 was deliberately stopped after source
review found a keyboard-focus owner error. Its supported continuation191
(`8aaae126db2d4a179ee6188682aa257b`, source `ef1ac620`) closed0 with an empty
Linux group, released private mounts and no max/OOM events, retaining the409
non-Qt plugins and SDK/core/codec/MPV inputs. Its native mouse/Tab/mouse pixels
were0/14/14: keyboard focus was visible, but mouse return wrongly retained its
outline. The Qt window attribute is sticky, so querying its correct owner is
insufficient.192 tracks the category view's actual focus/key/mouse events locally;
fresh100/150/200% checks now clear the mouse outline while preserving keyboard
focus. The original failed receipt is retained. The menu and
both prior-profile workflows pass on191; the popup checker now observes the
actual roll-animation/list-visibility transition without a fixed delay. No
normal1.1.5 release is claimed by those historical191 results.

The same assembly's custom125% font-size value fails a later Save because its
numeric-only validator/parser rejects the displayed unit. Manual review of all
thirteen100% category pages also identified an extra Privacy disclosure (absent
from original frame3062:11911) and Snapshot Original size incorrectly rendered
as Custom(-1×-1); upstream documents -1/-1 as the original dimensions. Correct
these with the focus treatment in the same Preferences.cpp batch. The native
browser's1542 rows correctly exclude231 source-declared shortcut options from
the1773-key inventory; its earlier equality assertion was a checker error, not
a missing native setting. Preserve completed layout evidence and the original
failed results. The remaining150/200% matrix, missing-font preservation and
history checks have now finished with clean native exits; the original font and
focus failures remain false. All13 basic pages,12 applicable expanded pages and
representative DPI/theme/popup images have been manually inspected. The four
bounded source corrections and affected input/save/focus/Privacy regression are
verified through192 and the affected native continuation. Composed normal
presentation and final delivery remain required.

| Stage | Status | Acceptance satisfied | Remaining criteria / blockers | Deferrals |
|---|---|---|---|---|
| M4 Settings and menu parity | COMPLETE | Normal1.1.6 delivered and independently verified; R83–R87 reconciled under the explicit minor-UI manual-review waiver. Current native playback/presentation, packaging, source/symbol mappings, preservation, retained/weekly binding and obsolete cleanup pass. | None. | None. |
| M5 Onboarding and interface shortcuts | COMPLETE | R88–R89 verified through native wizard/editor/restart/dispatch, optimized artifacts and independently retrieved normal1.1.7. | None. | No blockers or tracked deferrals. |
| M6 Font navigation, media preview and engine identity | ACTIVE | R90–R95 mapped; causes investigated; M5 prerequisite closed. | Conditional wizard navigation; untimed still images; engine-aware centered/window/taskbar identity and restart persistence; theme-aware two-tone accents; native workflows and one verified normal1.1.8 update. | Internal acceptance gaps; no external blocker or tracked deferral. |

Use the existing Qt/native configuration controls and player/library owners.
Reuse retained SDK/MPV/codecs/objects. Earlier M4 integration affected core
history, saved options, subtitle rendering and MMDevice volume and used the full
incremental MPV path. The current bounded Preferences.cpp repair uses the
verified Qt-only409-plugin reuse guard. The integrated libass style
API requires the documented 0.13.0 minimum; the pinned 0.17.5 input already
satisfies it. Refresh only affected configuration inputs; do not initialize
the VM or rebuild unchanged dependencies. Final
delivery remains the established normal four-asset release, with debug/COFF
symbols outside the portable player. The user resolved the release-directory
size question; do not reorganize its requested artifacts under this task.

The existing review deliverable and thirty reference captures are at
`D:/VLC-Redesign/verification/settings-parity-20261102`. Its explicit retention
contract covers this repair. Stage closure requires actual rendered comparisons
and real actions, not merely exposing all native option keys in module groups.

**M4 source checkpoint:** all thirteen ordered categories are now represented by
219 distinct reference views backed by shared native draft values. Native
specialist options remain searchable under Advanced Options / All VLC options;
the main menu has the twelve reference rows, with remaining native commands in
General's themed advanced route. The source includes the original active icons,
black header/rounded exterior, reference slider/startup-volume/equalizer layouts,
dependent controls and real history, shortcuts, add-on and plugin-cache actions.
Previously unconsumed compact/fullscreen-control/tree preferences now have
active interface/queue bindings; folder presentation preserves native queue
identity/order. Native filter/appearance help preserves the established VLC-only
engine boundary. Shared speed/delay defaults also initialize MPV.

C/C++ history/parser portability diagnostics and the catalog declaration/unique
identities pass. All-category native layout/scroll/theme/DPI and settings
behavior/rollback/restart acceptance subsequently passed on70dd, with original
producer identities retained. Fresh affected menu/handover/profile checks passed
on d214. Remaining blockers are actual composed backdrop, final release and
independent delivery/binding/cleanup.
No deferrals or second ACTIVE stage are introduced. Version1.1.5 is reserved for
the final verified outcome; no M4 release has been published.

Assembly187 closed0 with an empty Linux group, released private mounts, no OOM
and409 retained non-Qt plugins. Its affected native census closed1 with clean
player exits. Recent model creation succeeded; its test wrongly required an
absolute URL. The playing handover's3.10-second position delta spanned5.50 seconds
on the actual application clock at1.21x, so the fixed3-second assertion counted
real menu/capture time as a seek error. Paused handovers preserved positions.
Use the measured application-clock/rate bound for playing media and retain the
exact paused-position criterion. Both prior-profile cases also exposed the
existing manual setup action missing from the redesigned menu route. Restore
it inside General's themed advanced commands, then recheck these affected paths;
the original passed settings matrix remains bound to70dd and unchanged rendering.

Continuation188 (`bff94711ca7c4139acdc7790b59df726`) closed0 from
`d214cc6f2c95f0616500d226b8e2da4fcd7eb280`, with409 non-Qt plugins retained,
empty Linux group, released mounts and no OOM/max events. The complete affected
native outcome passed: twelve-row menu/Recent, direct Settings, manual setup in
both engines, paused/playing and idle handovers, saved profiles, MPV history,
privacy and volume. The integrated verifier was corrected to follow the themed
advanced route and stage the actual native `interact` checkbox before testing
the reference's conditionally visible Save/Cancel footer. Earlier terminal
verifier failures remain false records; final owned session67713 exited0 with
clean player shutdown. Fresh native menu/Playback/advanced-popup captures were
manually inspected. Original settings proof retains its70dd producer identity.

README now credits/links the YouTube video, interactive Figma project and
upstream foundations, preserving the upstream text. Optional comparison images
are omitted because the available widget captures cannot prove the composed
backdrop. Normal packaging and SDR/P5 picture checks subsequently passed;
actual composed Settings verification remains required. No1.1.5 release has
been published and M4 remains ACTIVE.

Normal assembly189 (`8bc054e68da6455996fabc4bc3a4dd66`) closed0 from
`e9b168f3d0074b9745e7569a25b4ae4805414d95`, with409 unchanged non-Qt
plugins reused,417 stripped PE mappings, no OOM/max events, an empty Linux
group and released private mounts. The local portable/source/symbols/checksum
artifacts pass their archive and unsigned-policy checks. The Windows PowerShell
signature probe initially selected an incompatible inherited PowerShell7 module;
loading that host's bundled module repaired the probe without an OS or payload
change. The original false result remains recorded.

The first private placement check rejected saved DPR1.5 geometry under its
explicit DPR1.0 environment, before any input-desktop launch. The already
completed same-package normal private launch supplied matching DPR1.0 geometry.
Fresh SDR/P5 private placement proofs and subsequent nonactivating offscreen
actual presentation passed, with clean natural EOF and native/observer exits.
The failed receipt remains false. Original session53349 closed0; all twelve
normal preparation/picture checks pass. Actual composed Settings blur is still
unverified. A user-launched isolated review is prepared at
`D:/Temp/vlc-s8-settings-1.1.5-20261102/backdrop-review/review-settings.cmd`,
bound to the normal Qt SHA256
`732998066b13f62fb21cc779761cb587e2d7e07f8aac1c61f6a4734bdb49615f`.
No desktop controls, focus requests or OS transparency changes are authorized.

Managed assembly177 (`8f96080bd4ad4446a82a9f9e7ccb1c70`) bound source
`3fcb63600b0783666a500e850e5cd8ffbd7fea9a` and reached configuration. It was
explicitly stopped before player compilation after source comparison identified
remaining slider help glyphs, equalizer spacing and scrollbar field alignment.
Its closed report records exit137, OOM0 and an empty Linux group. These source
corrections and a native Windows region check were integrated before
resuming the same candidate/pipeline, preserving all retained dependency objects.
No native acceptance or final release is claimed.

Final M4 delivery also includes the user's3 November README request: credit/link
the original YouTube redesign video, Figma project and upstream foundations.
Prepare a reference/current-player screenshot comparison only from the finished
verified UI, excluding private media. Complete this before the final release.

Continuation178 (`3158d645aea64ff6b9f20ce752c08991`) completed configuration
successfully, then failed compiling the new primary subtitle alignment guard:
absolute placement belongs to `subpicture_region_t`, not `subpicture_t`. The
guard now reads the same region owner as existing placement/overlap code, so
authored absolute regions remain unaffected. Its closed report records exit1,
OOM0, an empty group and released private mounts. Resume the original candidate
at the failed player step; do not regenerate the passed configuration or discard
completed objects. Native acceptance remains pending.

Continuation179 (`1b6d635dea154e08b34deb3a83579360`) linked core/libVLC and
executables and completed the full frontend object/QML error census. Seven
preferences errors shared one cause: QStringBuilder expressions were not
materialized as QString at QVariant/conditional boundaries. The cohesive source
correction uses concrete QString values. Original-frame comparison additionally
corrected per-row information glyphs, the 320x36 rounded accent housing and
per-view custom-color identities; native acceptance now checks glyph presence,
locked-file rollback/retry and missing-font preservation. Catalog C++17 and
source syntax diagnostics pass; they are not native acceptance. Report179 is
closed with exit1, OOM0, empty group and released cache/private mounts. Preserve
all successful objects and resume only the failed player step after binding the
correction. Configuration remains passed; no SDK/dependency rebuild is required.

Continuation180 (`0a2389b2fd794d39bcb8b224dcbe9671`) completed the optimized
player and full410-plugin assembly at `8626b9016d9ceb9326c3700f932584dcac70213e`.
The appended native chrome test build failed because QSignalSpy was undeclared;
its correction waits directly for the existing state-change event. Report180
is closed with exit1, OOM0, an empty group and released private mounts. Native
acceptance has not run. A confirmed remaining settings-icon resampling path
(fixed24px pixmap reused at18px) is corrected by rendering the original SVG at
Qt's requested size/DPR, with original/old/current pixel comparisons. Continue
this same candidate through the guarded Qt-only incremental path, retaining
all409 non-Qt plugins and the completed core/SDK/MPV/codecs. This does not
reopen configuration or authorize rebuilding unchanged dependencies. Complete
native behavior and visual acceptance remains an internal M4 blocker.

Continuation181 (`438579acc3884b0b86f6b86911572dec`) retained409 non-Qt
plugins, then rejected two stale bitmap captures in the new vector disclosure
buttons. Both now select the existing source-derived up/down SVGs before native
rasterization. The failed player step took576.9s wall/33.4s CPU; the closed
whole-group report records605.7s wall/35.3s CPU, no throttling/OOM and released
private mounts. Read-only inspection directly observed cc1plus in disk sleep at
`p9_client_rpc`, with `/mnt/d` on9p/DrvFS. This explains the dominant I/O wait;
Qt Makefile changes also regenerated unchanged QML dependency/resource steps.
Preserve those generated outputs and completed objects while resuming the same
failed step. Native acceptance and the final normal release remain unverified.

Continuation182 (`bf69734f8dfb47c19a71261aff1e8941`) completed the optimized
Qt-only assembly and native policy/SVG test programs from `6c507440a4`, retaining
all409 non-Qt plugins. Its inspected closed report records exit0, an empty group,
released private mounts and no OOM/throttling. The player step used1277.9s wall
but104.9s CPU; measured compiler/linker9p waits explain the gap. Unchanged QML
generation rules already preserve identical outputs and do not require repair.
No toolchain, filesystem, VM or Windows-native migration has been performed.

The coordinated native pass verified the unchanged policy/SVG programs and
captured all thirteen settings categories, basic/expanded/scrolling, dark/light,
normal/narrow at100%. It did not pass overall: verifier navigation and leading
`--` text handling needed correction; a later external input-desktop transition
masked already completed native cleanup. The verifier now retains both the
actual exit/closure evidence and any desktop-preservation failure.

Actual reference/pixel inspection also rejected shrunken fields, accumulated
row-spacing drift, blank default choices, subtitle color fields and extension
toolbar presentation. The cohesive correction restores expanding320px fields,
original row/control metrics, editable native-language selection, validated RGB
hex/swatch fields, disclosure arrows and the responsive add-on toolbar. The new
geometry assertion demonstrably rejects the prior258px log editor. Source
diagnostics pass; corrected native rendering/behavior remains unverified. M4
stays ACTIVE, with complete affected acceptance and final delivery still required.

Continuation184 (`797d2e21f29e4c179700b4396e6f2c0d`) completed the guarded
Qt-only assembly from `2ceb2a07af` after183 was deliberately stopped before Qt
compilation for a toolbar-width correction. Report184 records exit0, an empty
group, released private mounts and no OOM; player1236.9s wall/100.3s CPU. Native
acceptance95498 closed with exit1 and clean player exit: the new width assertion
found a separate90px maximum in VLC's integer/float control factories. A bounded
diagnostic survey then inspected all thirteen categories on that same assembly;
it is explicitly not acceptance. The survey also exposed an unregistered closed
disclosure resource and small accumulated row-height drift.

The complete correction removes the legacy width cap only in reference views,
uses the archived right-chevron component `71:875` with registered/distributed
resource provenance, preserves native editable track indexes behind Automatic,
and restores source field/section dimensions and Browse geometry. The pinned
Qt6.8.3 stylesheet source confirms that polish reapplies CSS minimum geometry;
the view's exact dimensions therefore use designable QSize properties after
that geometry step. Original artwork generation/source-resource diagnostics
pass, with all existing artwork unchanged. Fresh native behavior/pixels, final
normal delivery and independent verification remain internal M4 blockers.

Continuation185 (`144d69b1492f4c2490b90ab9fe22725d`) passed the exact409-plugin
reuse assembly from `7e03e19df29c7781d338be09677b05b37a141445`. It closed0 with
empty Linux group, released private mounts, no OOM/max events and1712173056
bytes peak RAM; player1532.3s wall/142.0s CPU. Native8780 stopped on an overly
strict fixed-widget constraint assertion: the Interface slider wrapper actually
renders at the original47px through its child layout. The corrected check now
verifies that rendered47px height. Native38520 subsequently exposed a genuine
367px combo width. A single all-category survey6686 measured129 expanded form
editors and found five long native combo content hints, including below-viewport
rows. The shared reference adapter now uses the existing bounded combo hint
policy while preserving every native label/value.

Continuation186 (`7307e18849cb4703b436edf1138b5d54`) passed the guarded
assembly from `70dd7b60c2ef17868093f48f1e938c29e9d09ceb`, retaining409 non-Qt
plugins. The inspected report records exit0, empty Linux group, released private
mounts, no OOM/max events and1714921472 bytes peak RAM; player1251.5s wall/
122.7s CPU. Original native acceptance session62989 is running under
`E:/Temp/vlc-settings-implementation-20261102/accept-settings.py
--resume-combo-hints`, with results in `settings-native-6`. All thirteen dark/
light, normal/narrow100% categories and staged edit/rollback checks passed;
VLC/MPV saved-option restart and explicit-command-line precedence passed.
The150% layout/scroll matrix also completed, but62989 closed1 because the input
desktop changed before its clean player exit0. A bounded150% lifecycle probe
reproduced that same equality-check failure. Both original results are preserved
in `settings-native-6/result-before-desktop-change.json` and
`result-lifecycle-before-desktop-transition-handling.json`; neither is relabeled
as passed. Native actions separately reject foreground ownership, and the
owned desktop is never switched. The verifier now records input-desktop names
and preservation truthfully, rejects the owned test desktop becoming input,
and allows unrelated user lock/unlock transitions. The default strict check for
other native helpers is unchanged. Managed continuation23465 rechecks the150%
owned lifecycle and resumes200%/unfinished workflows while reusing the completed
unchanged100/150% layouts. No compilation or duplicate layout matrix is active.

The200% matrix and missing-font preservation passed. History navigation exposed
a verifier assumption that EOF always mounted `fullLibrary`; the actual narrow
window mounts `compactLibrary`. A first attempted Expand observation was also
rejected before dispatch because that observation target did not yet exist.
Both failed records are retained. The corrected test observes the actual mounted
library owner without changing its layout. Managed continuation90147 passed the
complete settings outcome, including real Recent history Cancel/confirm, native
database retention/reset and unchanged media/profile hashes. Its original
controller continues with the main menu, onboarding and affected player paths.
`settings-native-6/result.json` is now a closed passed result; its historical
desktop/navigation failures remain separate evidence, not relabeled passes.

Main-menu, first-run/shortcuts, playback/subtitles and the actual reported4K
seek-preview workflow passed on70dd. Handover then found a production regression
with `--no-media-library`: `RedesignTopBar.qml` declared `MLRecentMediaModel`
inline even though VLC registers that type only when the backend is available.
Its inactive Loader guard could not prevent the parent QML parse failure. The
model is now in a separately loaded declarative component, retaining the same
history/backend availability guard and native Recent behavior. This is a current
R83/R84 advancement blocker until the affected native workflows pass.

The controller also selected the wrong fixture for the older integrated/prior-
profile programs:12-second `control.mkv` has one audio stream and no subtitles,
while those programs require the120-second multi-track input. Reused the existing
`generate-s7-fixtures.py` into the exact task-owned `s7-fixtures` directory on D:
(native media I/O exception); its synthetic media/CC0 manifest is retained only
through this acceptance and then cleaned. No user media is generated or altered.
Bind the complete QML/test correction once, retain all409 non-Qt plugins and
unchanged settings/backend evidence, then recheck Recent with/without the media
library, real handover and both prior-profile paths. No whole SDK/configuration
rebuild or repeat of the completed thirteen-category matrix is justified.

All thirteen current normal/basic captures were visually inspected. The user's
backdrop observation remains an explicit acceptance gap: original frame999:5047
has#0e0e0e/95% tint and50px background blur. The native PNG has alpha242; an
owned inactive-desktop readback31264 returns S_OK/type3 for requested Windows
acrylic, with rounded physical bounds and clean player exit. Neither proves
composed blur over player content. The OS transparency setting is enabled and
unchanged. Preserve this distinction in final verification and README imagery;
do not replace actual backdrop evidence with a widget-only screenshot. M4 remains
ACTIVE and1.1.5 remains unpublished.

**M3 Weekly upstream maintenance (2 November 2026): COMPLETE.** Remotes/default
branch and exact revisions were refreshed: local/remote master was
`b155f371592ca830678624b457e79c134b671a5a`, upstream master is
`8a47770f6333df6b60181329db5fdaad318bdb44`, with one incoming HEIF grid-offset
overflow fix. The isolated branch `codex/weekly-upstream-20261102` merges it
without conflicts. Normal release
[1.1.4](https://github.com/Darkaxt/vlc/releases/tag/redesign-v1.1.4) is delivered
and independently verified from app source
`6288be3623fdeefb505f3f0c5ea5fd24bf0fcf2d`. Untracked AGENTS.md, installed
player/profiles, source history/tags and active build inputs are preserved.
No other implementation stage is ACTIVE; S9 remains NOT STARTED.

| Stage | Status | Acceptance satisfied | Remaining criteria / blockers | Deferrals |
|---|---|---|---|---|
| M3 Weekly upstream maintenance | COMPLETE | R71/R72: pinned upstream merge; optimized coherent assembly; native HEIF guard/grid decode; default and passive focus styles; fresh SDR/P5 actual presentation, EOF, release and foreground preservation; four normal published artifacts independently downloaded/hash/native verified; matching retained runtime/pipeline read-only verification175; persisted weekly binding; obsolete1.1.3 remote/local retirement; exact spent-output cleanup and final reconciliation. | None. | None. |

Original controls were `E:/Temp/vlc-weekly-20261102-1.1.4`; sustained native/build
I/O used `D:/Temp/vlc-s8-weekly-20261102-1.1.4`. Those exact spent roots and
`D:/VLC-Redesign/build/windows-x64/scratch-share/weekly-1.1.4` are removed.
Current runtime and matching compilation state were promoted together into
`D:/VLC-Redesign/build/windows-x64/scratch-share`; read-only gate175
(`516f6f89459f4041934df321287ed937`) passes with no rebuild, zero OOM/max events,
empty group and released mounts. The next pipeline directory is `run-0004`.
The weekly automation's schedule/target/status remain unchanged and its prompt
binds1.1.4. Obsolete1.1.3 release records/assets/local outputs are retired,
preserving Git tags/history. Seven reviewed cleanup transactions removed
15372647844 logical bytes without exclusions/errors; all exact retired roots
and one-shot launchers are absent. Required qualification and original control
snapshots remain under `D:/VLC-Redesign/releases/1.1.4/verification`.
[Final reconciliation](resources/m3-1.1.4-verification.json) records every gate,
artifact identity, evidence-reuse boundary and cleanup receipt. No blockers or
tracked deferrals remain. The closure refactoring assessment found no material
debt obstructing current acceptance; no later-stage work was opened.

Historical failed attempts below retain their original results and are resolved
by the final native bridge/desktop protocol; they are not current blockers.

Original gate169/session66178 is closed0, with an empty Linux group, released
mounts, zero OOM/max events and1703432192 bytes peak charged RAM. The one-commit
HEIF merge assembled successfully. Native arithmetic boundaries reject the old
guard and pass the fixed guard; actual packaged HEIF grid playback exports a
nonblank1024x256 frame and exits normally. Normal VLC playback also passes.
Qualification session74020 closed1 because the SDR offscreen MPV run acquired
foreground ownership despite correct offscreen placement and actual Present(S_OK).
All native processes exited0. This was an internal R71 acceptance blocker:
the normal launch protocol lacked enforced no-focus flags. Its raw failed
receipt is preserved. The explicit volatile passive option/native-style gate
were added through the guarded Qt-only cohort path, retaining completed
HEIF/non-Qt objects and unchanged decoder/runtime image evidence.

Qt-only continuation170 (`0ae8671ae2a647e19a9462af41673585`, source
`0515f2f2cffb2a7ee49357d1a9fa76078f455894`) closed0 with409 non-Qt plugins
retained,417 stripped mappings,1704787968 bytes peak RAM, zero OOM/max events and
released mounts/group. Qualification22762 passed normal VLC and default focus
style, then its passive **inactive-desktop** proof failed the native-style check.
No offscreen launch followed. Installed Qt6.8.3 source confirms that its no-focus
flag does not create `WS_EX_NOACTIVATE`; add the required Windows lifecycle bridge
without weakening that criterion. This intermediate internal blocker was resolved
in source6288 below; both failures and unchanged HEIF evidence are preserved.

Native bridge assembly174 (`0d7c81b6fc964abdae3a4e2e08dda36a`, app source
`6288be3623fdeefb505f3f0c5ea5fd24bf0fcf2d`) closed0, with zero OOM/max events,
1701789696 bytes peak RAM, empty group and released mounts. Only
`mainctx_win32.cpp` recompiled for that repair;409 other plugins remained bound.
Its default and passive native-style checks pass. Qualification3587 reached EOF
without a picture marker; a subsequent binding read found worker `Default` but
input `Screen-saver`. That run does not establish active-desktop presentation.
The host verifier now refuses a startup/input-desktop mismatch before copying or
launching, checks again at readiness and records actual desktop identities.
The negative guard test launches no player. With both desktops observed as
`Default`, continuation93701 passes fresh private placement and actual SDR/P5
Present(S_OK), EOF, release and no foreground ownership with the same binaries.
No rendering change or rebuild was needed for the desktop condition. The failed
receipts remain historical evidence. Portable/source/symbol/checksum artifacts
are verified; the portable ZIP is145033709 bytes. Normal publication and
independent delivery/native verification subsequently passed. The downloaded
MPV inactive-desktop lifecycle reuses actual presentation only after identical
whole-ZIP and Qt/geometry/monitor bindings; it makes no new picture claim.

**M2 First-run usability and fork identity is COMPLETE (2 November2026).**
[Modern VLC Fork1.1.3](https://github.com/Darkaxt/vlc/releases/tag/redesign-v1.1.3)
delivers the full Figma main-menu/Playback-panel correction and the reported
preview, original-icon sampling and window/sidebar sizing repairs. Application
source is `6cba6f96e3b341acac3886c97597b7aa74c6c169`; the final closure changes only
host verification tools, documentation and evidence. S0/D1/S1-S8/M1/M2 are
COMPLETE, including the recurring M3 maintenance above. No stage is ACTIVE.
S9 is NOT STARTED and remains planning scope.

| Stage | Status | Acceptance satisfied | Remaining criteria / blockers | Deferrals |
|---|---|---|---|---|
| M2 First-run usability and fork identity | COMPLETE | R52/R65/R73-R82: native Figma menu/submenus/keyboard and direct Global Settings from player/library; Playback panel, plain VLC/MPV choices, control order/time/toggle; welcome/remapping, no-root indexing, flat application icon, quiet update errors/manual retry, both engines/drop/geometry/fullscreen, original SVG pixels at100/125/150/200%, subtitle track/cue/timing/handover/restart, sidebar transitions and actual4K preview pixels/cache/latest/replacement/cancellation. Normal optimized release and four independently downloaded assets pass; retained weekly build/binding verified; older releases and spent D: output retired. | None. | None. |

[Final requirement/delivery reconciliation](resources/m2-1.1.3-verification.json)
records exact asset hashes, native evidence applicability, preservation and limits.
[Native acceptance](resources/m2-1.1.3-native-acceptance.json) binds the optimized
production tree and the complete corrected workflows, with original host failures
preserved locally. Actual native captures are under `resources/m2-1.1.3`.
The reported4K VP9 file decodes a cold5:11 preview in77.1686ms and publishes its
cached image in0.0005ms. These are decode/publication metrics, not full GUI latency.
Previews use keyframes and require VLC. Original transport silhouettes are retained;
native DPR rasterization avoids the second filtering pass. Window autoresize is
disabled by default; the explicit opt-in remains bounded to available screen space.

Normal managed ticket166 exited0 with an empty Linux group, released mounts and
zero OOM/max events. The consistent application profile is --disable-debug,
-O3/-g0, NDEBUG and QML debugger off. All303 generated QML objects have no debug
sections;417 shipped PE images are stripped and matched to separate symbols.
The current409 non-Qt plugins, SDK, MPV and codecs were verified and retained.
Normal VLC playback/EOF/teardown, MPV SDR/P5 actual Present(S_OK), native media
library startup and flat executable/window icons pass. Private placement preceded
each nonactivating offscreen MPV run; input desktop/foreground were preserved.
The independently downloaded player passes VLC playback and MPV lifecycle checks;
MPV actual presentation is reused only after identical whole-package SHA256 and
unchanged Qt/geometry/display binding. The release-build checker now uses ordered
unconditional teardown instead of an NDEBUG-only object-name log. Its original
failed receipt and negative controls remain retained; no extra player build was needed.

The usable portable player and four assets are in `D:/VLC-Redesign/releases/1.1.3`.
The portable ZIP is145034239 bytes; symbols are a separate optional download.
Local qualification, original Figma/native captures, failed observations and
recovery receipts are retained in `verification`. The build remains at
`D:/VLC-Redesign/build/windows-x64`; runtime AND matching compilation state were
promoted together. Read-only gate168 (`1ca995994a4f4826a2ef88f0e68f6a13`) verifies
source/configuration/417 PE mappings/410 plugins/dependencies and next run0015,
with no rebuild/initialization, no OOM, an empty group and released mounts.
The existing Monday09:00 heartbeat now binds to1.1.3 and that verified cohort.
UI-only changes may use normal-mpv-current's exact reuse guard; relevant global
flags/API/core changes require normal-mpv-full. Preserve unchanged dependency inputs.

Older release entries/assets and local1.1.1/1.1.2 directories were explicitly
retired after new delivery and retained/weekly verification. Git tags/history,
the installed `D:/Tools/Modern VLC`1.1.2, profiles and reusable inputs remain.
Historical release URLs below record their original delivery; retired versions
remain traceable through their preserved Git tags and committed reconciliation.
[Historical1.1.2 qualification](resources/m2-verification.json) retains its original scope.
No shutdown, desktop control or installed-player replacement was performed.

**M1 Upstream sync and optimized release is COMPLETE (1 November 2026).**
[Modern VLC Fork 1.1.1](https://github.com/Darkaxt/vlc/releases/tag/redesign-v1.1.1)
is the normal published update from application commit
`b84e7326e3d3e554120f3866fbe1c1acfa5ec6cc`, incorporating 243 incoming
commits through upstream `c7834066e27cf07a2a15f1e8aab17c12df97e5d4`.
[Final requirement reconciliation](resources/m1-verification.json) records R71-R72.

| Stage | Status | Acceptance satisfied | Remaining criteria / blockers | Deferrals |
|---|---|---|---|---|
| M1 Upstream sync and optimized release | COMPLETE | R71-R72: normal upstream merge; coherent 410-plugin assembly; required dependency/API updates and complete source/notices; integrated engine/handover, state, library, recovery, input and presentation workflows; P5/P8.1/P8.4/SDR/HDR10 pixel comparisons; three selected native upstream regressions; normal package and independently downloaded VLC/MPV actual playback/EOF/teardown; unchanged protected profiles; all 417 PE binaries stripped with matching separate symbols; four published assets independently checked; retained build and weekly binding verified; exact spent scratch removed. | None. | None. |

The portable folder is 329,720,825 bytes, 78.518% smaller than 1.1.0 without
removing engines or plugins. Runtime sections and MPV identity are preserved.
Corresponding source covers the application and 121 dependency archives;
124 notice entries distinguish those sources from 3 host-only inputs and
include AOM PATENTS. Matching symbols are a separate optional download.

The affected integrated acceptance covers 19 functional workflows, five real
color comparisons, native visual review and the real medialibrary 38-to-39
migration. Selected Windows upstream regressions cover audio-output
flush/resampling, video blending and Qt CSD. The entire POSIX-oriented upstream
suite and optional absent Qt Quick Test are not claimed. Normal-package
VLC SDR/HDR10 and MPV SDR/P5 checks pass; independently downloaded VLC and MPV P5
checks also pass. The signed Windows InputSwitch indicator classification in
the private-desktop placement receipt is documented in REPRODUCTION.md;
subsequent actual-picture checks passed the unchanged strict offscreen guards.

Reusable source/configuration/objects, SDK, MPV prefix, the separately prefixed
medialibrary 0.14.1 and codec updates, and private validation inputs remain at
`D:/VLC-Redesign/build/windows-x64`. The read-only retained check 142 verified
source b84e7326, the promoted canonical runtime and dependency bindings without
building or initializing a VM. All managed Linux groups exited with no OOM;
private mounts were released. The existing Monday 09:00 Europe/Bucharest
automation retains its cadence and now binds this verified release/cohort.
Current-release qualification is intentionally retained at
`D:/VLC-Redesign/releases/1.1.1/verification`; private frames remain local.

Both exact task roots `D:/Temp/vlc-s8-release-1.1.1-20261031` and
`E:/Temp/vlc-release-1.1.1-20261031` are absent following fully inspected
transactional cleanup. Installed VLC/Nuvio data, protected AGENTS, prior releases
and unrelated WSL bindings are preserved. Shutdown attempts remain cancelled.
No implementation stage is ACTIVE. S8 stays COMPLETE and S9 NOT STARTED;
this maintenance did not implement Rust migration or additional UI scope.

**S8 MPV and Dolby Vision integration is COMPLETE (31 October 2026).**
[Modern VLC Fork 1.1.0](https://github.com/Darkaxt/vlc/releases/tag/redesign-v1.1.0)
is a normal published release from application commit
`c8a1cdfd31a97e7ecc0bda772d4148f1f87a6b26`, with portable Windows x64 binary,
complete corresponding source and checksums. Independently downloaded artifacts
match the verified archives and pass real normal MPV Dolby Vision and VLC playback.
[Final release and requirement reconciliation](resources/s8/final-release.json)
supersedes the pre-release status in the original native acceptance snapshot.

S0, D1, S1-S8 and M1 maintenance above are COMPLETE. No stage is ACTIVE.
S9 remains NOT STARTED and planning scope only. Remaining S8 criteria, blockers
and tracked deferrals: none. Installed VLC/Nuvio data and Windows language state
are unchanged; root AGENTS.md and the prior verified 1.0.0 release are preserved.
Separate installation over existing VLC remains outside scope.

The verified reusable build is `D:/VLC-Redesign/build/windows-x64` for the existing
Monday 09:00 Europe/Bucharest weekly consumer. Its source/configuration/runtime
check originally passed through gate 126; M1's current source/runtime binding
passed through read-only gate 142, with an empty Linux group and released mounts.
Exact temporary roots `D:/Temp/vlc-s8-20261029` and
`E:/Temp/vlc-s8-finalization-20261031` are absent after reviewed cleanup.
The [specification](SPECIFICATION.md) governs all stages. S7 remains COMPLETE;
[its published 1.0.0 delivery](https://github.com/Darkaxt/vlc/releases/tag/redesign-v1.0.0)
and [requirement evidence](resources/s7/specification-reconciliation.json) remain available.

**Verified S6 outcome:** actual six-zone drag/drop, removal/reinsertion, keyboard movement, empty/narrow recovery, Reset/Cancel/Save and moved playback/seek; named snapshots covering layout, theme, accent, Grid/List and time display, with Save/switch/restore/rename/delete/restart and media preservation; first-run onboarding, preview/Skip/reopen/Finish/restart, native folder acknowledgement, invalid/excluded-root preservation and real core/interface write-failure rollback/retry. Malformed/newer/oversized/wrong-type/empty state stays read-only and preserved; absent state stays absent after Cancel. Figma geometry, Inter typography, source colors, light/dark 100/150/200%, keyboard/scroll/long Unicode text and native dialog appearance are recorded in [S6 evidence](resources/s6-verification.json). All nine accents pass measured primary-label contrast, preserving source default orange. Repaired native library signal, diagnostic seek observation, Qt palette ordering and literal-ampersand targeting are covered by actual regressions.

The normal review folder is `D:/VLC-Redesign/S6`, independently file-hash checked and verified for real picture, natural EOF, input release, media-library startup, Qt event-loop completion and exit 0. Diagnostic markers are absent; its portable folder was returned to empty isolation after verification. Installed VLC profile hashes and Windows language state remain unchanged. App-owned native events used inactive desktops, without OS input, desktop switching or foreground ownership. UI grabs exclude separate video and physical desktop backdrop pixels; they are not whole-engine/device acceptance.

**Resource/storage closure:** the approved S6 disk move to D: preserved its distribution identity and unrelated bindings. Heavy work used the installed WSL gate with measured 4 GiB VM, 3.5 GiB workload, 512 MiB swap, one CPU/compiler and empty final cgroups, with no OOM events. The normal build peaked at 3,676,135,424 bytes. After verified delivery, the temporary disk was removed through an inspected cleanup ticket and only its empty registration was retired. Ubuntu/Docker bindings are unchanged. Its allocation was 30,312,235,008 bytes; measured D: free space rose 30,312,226,816 bytes across retirement, with concurrent-volume-write attribution explicitly limited. No rollback package is retained. One current review folder and compact source-linked evidence are intentional outputs. Both `D:/Temp/vlc-s6-20261028` and `E:/Temp/vlc-s6-20261025` are absent; all inspected cleanup transactions are APPLIED without exclusions or errors. [Cleanup evidence](resources/s6/cleanup.json) records exact scope and logical counts.

**Former S6 deferral resolved in S7:** actual upstream WASAPI startup-paused ordering failed before the correction and passes afterward; both startup modes now pass resume, advancing clock, natural EOF and normal exit. The cross-process Windows pipe collision is independently reproduced and corrected. [Native integrated evidence](resources/s7/native-integrated-verification.json).

**Stage-closure refactoring assessment:** no current-acceptance finding remains. QML owns the validated layout draft/catalog; existing native owners retain settings, playback and library state. Native event subscriptions have explicit completion/cancellation/destruction lifetimes. No generalized engine/provider framework or speculative consolidation is introduced. The S7 audio lifecycle issue is resolved and verified.

| Stage | Status | Scope and requirement ownership | Acceptance evidence |
|---|---|---|---|
| S0 Specification and references | COMPLETE | R60 reference attribution/provenance; R63 repository registration | Fork parent verified; authoritative specification and plan committed; original Figma hash matches; every archive entry inventoried and embedded images decode; editable Figma access linked; derivative PDF/PNGs omitted; links resolve; uploaded files verified by independent HTTP retrieval at commit 327b3fd94a9f4bb26676429010fee3c489e98dff. |
| D1 Design source readiness | COMPLETE | R64; R60 export provenance | [Locked offline tooling](../../tools/design-source/README.md), fresh decode/inventory checks and semantic round-trip; selected SVG/PNG exports and source hashes verified; native Figma comparison inspected for both screens; renderer limits and fallback documented. [Export evidence](resources/d1-verification.json). |
| S1 Unmodified baseline | COMPLETE | R01, R02 baseline, R03 upstream capability inventory, R04 preservation contract | Windows x64 source build, native H.264/AAC callbacks and Qt/Direct3D11 playback with normal exit verified; source unchanged; capability inventory and configuration preservation contract recorded. [Assessment](BASELINE.md), [recipe](../../tools/windows-baseline/README.md), [evidence](resources/windows-baseline-verification.json). |
| S2 Working redesigned player | COMPLETE | R10-R14 player portion; R04 relevant persistence; R52 player quality | [Native S2 evidence](resources/s2-verification.json): real playback/seek/tracks/queue/resume/privacy/fullscreen/keyboard; composed light/dark 100/150/200% and resize checks; normal build with no diagnostic hooks; normal EOF/shutdown; temporary cleanup. |
| S3 Tracks effects and media tools | COMPLETE | R15, R20-R25; R04 and R52 relevant behavior | [Native S3 evidence](resources/s3-verification.json): real workflows for all three subtitle providers, local matching/presets/timing/effects, bounded analysis, timer, recovery and six theme/scale variants. Product acceptance, normal runtime, cleanup and source synchronization are verified. |
| S4 Library and media entry | COMPLETE | R30-R33 library/open portion; R04 and R52 relevant behavior | Real indexed library navigation -> enqueue -> playback; persistent pins/playlists/home; real network playlist and open actions. |
| S5 Preferences bookmarks and shortcuts | COMPLETE | R03 capability reconciliation, R14 menu/resume completion, R33 conversion/streaming dialogs, R40-R43; R04 and R52 relevant behavior | [Native S5 verification](resources/s5-verification.json): complete native option/action reachability, typed settings/reset/recovery, real bookmark/chapter/shortcut/extension/transcode workflows, representative Figma Widgets/QML comparison, normal package, preservation, cleanup and source synchronization. |
| S6 Customization and onboarding | COMPLETE | R50-R51; R04 and R52 relevant behavior | [Native S6 verification](resources/s6-verification.json): actual layout/profile/onboarding/persistence/recovery workflows, Figma and native appearance matrix, normal isolated review delivery, preservation, resource retirement, cleanup and source synchronization. |
| S7 Integrated verification | COMPLETE | R01-R04 final reconciliation; R52 complete interface quality; R60 production asset audit; R61-R62; R65 first-run font download | Product criteria, normal published 1.0.0 binary/source delivery, independent native/readback checks, preservation and exact cleanup pass. Remaining criteria, blockers and tracked deferrals: none. |
| S8 MPV and Dolby Vision integration | COMPLETE | R67-R70; Windows x64, NuvioDV reference, optional engine and real DV rendering | All assigned native/color/normal/delivery/preservation/reproduction criteria pass; published 1.1.0 independently downloaded and verified. No remaining criteria, blockers or tracked deferrals. |
| Proposed S9 Profiling and selective Rust migration | NOT STARTED | R66; after S8 and the completed existing plan | Release-bound resource baseline, justified bounded component selection, explicit FFI/preservation contract, one integrated migration and equivalent before/after evidence; retain only demonstrated benefits, then deliver/verify any retained implementation. |

**S8 MPV and Dolby Vision integration** is **COMPLETE**, after completed S7. The user selected `Darkaxt/mpv-android-libdovi`, confirmed NuvioDV as the successful behavioral reference and delegated the output choice. Follow R67-R70; correct video colors/display are required, with actual output capability reported and no unverified native Dolby Vision/FEL promise.

Proposed **S9 Profiling and selective Rust migration** is **NOT STARTED**, after S8.
The user authorized recording this improvement scope on 29 October and instructed
continued current work. Follow the specification's R66/S9 contract: profile the
completed delivered application, choose one bounded component with a concrete
safety/maintenance/resource justification, define its interfaces and acceptance
thresholds, integrate it through the real workflow, and compare equivalent native
and Rust release builds. Preserve Qt/QML, Figma, engine integrations, settings and
capability reachability. Candidate parsing/archive/configuration/job-lifetime work
does not authorize a wholesale rewrite or guarantee lower RAM/CPU. Record losses
as well as gains; return to the verified native implementation if the experiment
does not justify retention. A retained change requires normal release/readback.
All execution criteria remain unverified; no external blocker is identified and
no implementation is active for S9. This proposed later scope does not block S7.

Execution order is S0 -> D1 -> S1 -> S2 -> S3 -> S4 -> S5 -> S6 -> S7. D1 is a preparatory design step before VLC product implementation; D1, S1 and S2 closed at their requested stops; the user subsequently authorized S3. D1 now establishes bounded offline source readiness; it does not establish a complete Figma replacement or pixel-identical screen rendering. Cross-stage requirements are cumulative: each stage verifies its touched behavior; S7 reconciles the whole result. This does not permit a stage to omit its assigned acceptance criteria. Missing required behavior is an advancement blocker unless a valid named-stage deferral applies; implementable gaps keep their stage ACTIVE until its own criteria pass.

Continuation after the completed redesign is S8 -> S9. S8 is COMPLETE; no stage is ACTIVE.
S9 remains planning scope until its prerequisites and execution authority apply.

## S8 execution and acceptance contract

Status: **COMPLETE**, verified 31 October 2026. The user selected
`Darkaxt/mpv-android-libdovi` and NuvioDV as the behavior reference, required live
engine switching, and requested a resumable compilation pipeline. All R67-R70
criteria are satisfied; no blocker or tracked deferral remains.

| Requirement | Verified outcome | Remaining criteria / blockers / deferrals |
|---|---|---|
| R67 optional MPV/live selection | VLC remains default. Both live handover directions preserve current queue identity, position and paused/playing state. Pending HTTP input/queue-change cancellation and missing/incompatible app-local runtime recovery pass. | None. |
| R68 Dolby Vision rendering | Actual composed P5/P8.1/P8.4 pixels pass same-DLL software-reference comparisons with an intentionally incorrect P5 control; SDR/HDR10 regressions pass. Metadata survives D3D11VA copy-back through libplacebo reshape/conversion. | None under the stated SDR output contract. |
| R69 integrated workflows | Native local/network playlists, controls, seeking/rate, Windows audio-session volume/mute/restart, tracks/delays, external SRT first/restart, history/privacy/library, fullscreen/keys, EOF/error recovery and representative light/dark 100/150/200% appearance pass. | None. |
| R70 delivery/reproduction/preservation | Normal source-bound1.1.0 portable binary, all 116 corresponding library sources and checksums published once; independent downloads/hash/native checks pass. Profiles preserved, source synchronized, reusable build binding/weekly schedule verified and exact D/E scratch retired. | None. |

[Source-bound native acceptance](resources/s8/native-integrated-verification.json)
records the selected real workflows, positive/negative pixels and applicable
evidence reuse. It is a pre-release snapshot; its historical ACTIVE/remaining
fields are superseded by [final delivery](resources/s8/final-release.json).
Original failed attempts remain diagnostic evidence and are not counted as passes.

The shipped MPV SHA-256 is
`7ca5086cd73b6188f2e1181ac28dbc5ab8e757cd881c2255591909f24f612e2a`.
Output is full-range BT.709/sRGB SDR on the actual HDR-capable/SDR display setup.
Native Dolby Vision signaling and full Profile 7 FEL reconstruction are not claimed.
Advanced tools requiring VLC remain reachable and explicitly identify that need.

Normal run 20/ticket 125 exited 0 with no OOM, an empty Linux group and released
private mounts; peak charged memory was 1,822,052,352 bytes. The final Qt plugin
SHA-256 is `eab816bf0c122d3ee6865bc7acb38aa96274eb6cb3e9a4c21c24b9ea2d8b995f`.
Normal VLC, normal MPV SDR and normal MPV P5 show actual pictures, natural EOF and
ordered teardown. Independent downloaded-package MPV P5 and VLC checks also pass.
The normal package has no diagnostic hooks and its delivered portable profile is empty.

Inactive-desktop MPV cannot prove actual presentation. Normal MPV acceptance used
public synthetic saved offscreen geometry, nonactivating startup, and passive
owned-window events after private-desktop placement proof. Every visible owned
window remained outside the displays; no foreground ownership/input-desktop
change occurred. No OS input, desktop switching or Coordinator UI controls were used.

The existing source/build/dependency objects are retained at
`D:/VLC-Redesign/build/windows-x64`, with the same-volume identities and a verified
continuing consumer, `vlc-weekly-upstream-sync-and-release`. Gate 126 checked the
new binding read-only: clean exact c8 source, valid configuration/runtime hashes,
no initialization/rebuild, empty group and released mounts. Three bounded private
DV clips serve only local weekly acceptance; never publish them or their frames.
The existing Monday 09:00 Europe/Bucharest schedule was updated and read back.

The final D: cleanup ticket removed 14,312 members/6,458,996,106 logical bytes;
the E: controller ticket removed 28 members/24,038,804 bytes, without exclusions
or errors. Earlier closed native/normal copies were cleaned at their last-use
checkpoints. Current local release qualification and original control provenance
are retained at `D:/VLC-Redesign/releases/1.1.0/verification`; full media/frames and
spent test copies are absent. Frozen controls retain original paths for provenance,
not as relocatable installed launchers. [Reproduction](REPRODUCTION.md) records
the supported current build binding and evidence limitations. Historical assembly
details remain in the c8 Git version of this plan and the bounded local receipts.

Preserve the canonical checkout/AGENTS, installed profiles, original settings,
prior releases and unrelated WSL distributions. Use the installed WSL gate with
the 4 GiB shared VM, 3.5 GiB workload/512 MiB swap, one CPU/compiler. Do not repeat cold
SDK setup or configure unchanged inputs, reinitialize retained inputs, import a
distribution, migrate a VM disk, stop all WSL, raise budgets or control the desktop.
Resume each owned operation by its original identity; reuse unchanged acceptance
evidence. Validate coherent integrated behavior, not a build after every edit.

Closure assessment: existing VLC queue/history/configuration/audio owners remain
authoritative. MPV is bounded to the required app-local engine path; no general
provider framework, speculative refactoring or new persisted volume store was added.
No native code changed during final documentation closure; no additional build is needed.

## Earlier-stage reconciliation and current stage boundary

- S0 satisfied: `Darkaxt/vlc` is a GitHub fork of `videolan/vlc`; baseline pinned; application source unchanged; specification and stage map registered; intact Figma archive, archive/design inventories, attribution and editable-access links preserved. All 18 relative links resolve. ZIP contents and hashes passed, and offline semantic decode round-trip passed. All eight changed files were independently retrieved from GitHub at registration commit `327b3fd94a9f4bb26676429010fee3c489e98dff` and matched the local bytes, including the original Figma SHA-256. Remote master matched the registration commit. Derivative repository copies and temporary decoding files were removed through reviewed cleanup; the user's original Downloads files remain untouched.
- S0 remaining: none.
- D1 satisfied: fresh pinned-source decode and semantic round-trip; registered component/variant identities verified; two selected screens rendered offline; three custom icon variants exported as actual SVG vectors and PNG; original source and output hashes checked; both screens visually compared with native Figma after user sign-in. Clean unpatched locked dependencies were used, and exports succeeded with `fetch` disabled. Source layout/appearance is recoverable, with the documented renderer differences retained as limitations and Figma fallback.
- D1 remaining acceptance criteria: none. The bounded comparison did not require pixel-identical reconstruction; font metrics, blur/shadows and some transformed/clipped icon geometry differ. Hosted Figma remains necessary for affected exact exports. Full-project reconstruction and VLC playback are not claimed.
- D1 acceptance verification closed at 2026-10-17T01:06:10Z; work started at the user turn 2026-10-17T00:43:38Z. Elapsed agent wall time through acceptance/documentation: 22.5 minutes, including investigation, implementation, dependency setup, native reference access and validation. Final commit/synchronization/temporary cleanup are delivery overhead reported separately if material. This is not measured human labor or an estimate for the whole VLC fork. A repeat selected export took 11.09 seconds; first-run setup is excluded from that export duration.
- D1 refactor assessment: no unrelated refactoring or general-purpose Figma infrastructure needed. The instance/style adapter exists only to resolve observed failures on the selected source. No production assets or application source were changed.
- S1 satisfied: R01 upstream provenance and unchanged VLC source; R02 pinned Windows x64 build and successful real native playback; R03 public module/options and source menu/dialog inventories; R04 unchanged installed profile and documented persistence/migration/recovery preservation contract. Fresh native acceptance verified changing video, nonzero PCM, natural end-of-stream, the missing-file negative control, Qt/Direct3D11 first picture, input release, finished Qt event loop and normal process exit. Plugin-cache generation and inventory exited normally; no plugin-load errors remained. See [acceptance evidence](resources/windows-baseline-verification.json).
- S1 remaining acceptance criteria: none. Dependency-only static unwind linkage and the accepted MinGW 12 process-exit backport resolve the observed loader/shutdown failures; libtool startup-object selection was regenerated and verified. PE imports and ASLR/high-entropy/NX flags passed. The original VLC source and contrib archive remain unchanged. Target Qt package/qconfig metadata is 6.8.3, with host qmake and the archive's separate qtcoreversion header reporting 6.8.0; the recipe records these separately.
- S1 acceptance closed at 2026-10-17T03:42:46Z. Recorded work began at 01:11:49Z: approximately 151 minutes of agent wall time through acceptance, including setup, downloads, builds, dependency diagnosis/correction, documentation and validation. The initial source build took 41 minutes 26 seconds. This is measured first-run effort, not human labor or an estimate for redesign implementation. Cleanup/commit/synchronization are delivery overhead.
- S1 refactor assessment: no unrelated refactoring, new application abstraction, persisted state or UI behavior was needed. Build/inspection tools and the isolated runtime backport serve this baseline only. Minimized Qt and decoded PCM evidence do not establish complete interactive UX, physical speakers, every device or every network/disc capability.
- S1 cleanup: transaction `1687b77b32547b9bb412e762e97ba901` is APPLIED, with all 859 reviewed members and 29,592,019,339 logical bytes removed, no errors/exclusions, and the exact E: scratch root confirmed absent. The temporary `VLC-S1-20261017` WSL registration was removed; Ubuntu and Docker remain registered. Compact evidence and reproduction tools are preserved in the fork. Cleanup/retirement completed at 04:09:58Z, about 27 minutes after acceptance; exFAT content review and removal revalidation account for most of that overhead.
- Product stages: S0, D1 and S1-S8 are COMPLETE. No stage is ACTIVE under the current contract above; S9 remains NOT STARTED. S7's final release delivery and the earlier resource recovery/cleanup are verified. Separate installation over existing VLC remains outside scope.
- Blockers: none for S0, D1 or S1. S3 acceptance and delivery are verified; it has no remaining blocker.
- Tracked deferrals: none. The former startup-paused WASAPI defect was resolved and verified in S7/R61; it is not an open S8 requirement. S8 has no remaining acceptance gap, blocker or tracked deferral.

## S7 execution and acceptance contract

Authorization is `already_authorized`; this is one integrated final stage. The user requested the S9 plan addition and continuation of S7, without activating S8/S9.

| Acceptance unit | Satisfied and verified in S7 | Remaining acceptance |
|---|---|---|
| R01-R04 provenance/capabilities/state | Exact fork commit bound to normal binaries and corresponding source; every baseline module role and option/type preserved. Prior-profile/restart tests preserve malformed state, appearance, selected audio and unknown font. Final installed configuration/database and language comparison is unchanged. | None. |
| R61 integrated playback | Both startup modes; real local audio/video, multiple tracks, text/bitmap subtitles, local/HTTP playlists, nonseekable/missing media, keyboard/fullscreen, library/queue, natural EOF and process exit. Native WASAPI and cross-process pipe red/green regressions pass. Actual downloaded normal package passes picture/EOF/input release/library/Qt shutdown. | None. |
| R52 presentation | Inspected player, native preferences, library and font-page matrices in light/dark at DPR 1/1.5/2; Figma chrome geometry, Inter typography, contrast, resize/focus/long Unicode and Greek native labels. Earlier unchanged workflows retain applicable source-bound acceptance. | None. |
| R60 provenance/licenses | 199 Qt production inputs, 80 design vectors, 37 loose/skin assets and locale catalogs audited. Actual delivered notices and 106 matching dependency source archives checked. Full required licenses retained; no downloaded Delicious font or private test data shipped. | None. |
| R65 first-run font download | Real publisher HTTPS download and validated profile cache; actual native skins2 consumption; offline FreeSans fallback, cancel/retry/corrupt-cache preservation and restart/reopen without another download. Both font paths also pass with normal final binaries. | None. |
| R62 reproducibility/recovery/source/final release | Verified implementation pushed to existing public fork, exact source-bound normal build/revision relink, documented packaging/recovery/upstream sync, published 1.0.0 binary/source/checksums, independently downloaded manifests/hashes/version/PE/signature state and native behavior. Owned VM, D: scratch and E: cleanup controller absent; Ubuntu/Docker/default bindings preserved. | None. |

Current evidence: [release](resources/s7/final-release.json), [normal native runtime](resources/s7/final-normal-native.json), [source identity](resources/s7/final-source-parity.json), [resource-bounded builds](resources/s7/final-build.json), [preservation](resources/s7/final-preservation.json), [asset audit](resources/s7/final-runtime-assets.json), [VM retirement](resources/s7/owned-wsl-retirement.json), [scratch cleanup](resources/s7/final-scratch-cleanup.json). Every requirement is mapped in [the reconciliation ledger](resources/s7/specification-reconciliation.json).

The final normal build and revision relink exited 0 with empty cgroups, zero OOM events and the measured 4 GiB VM / 3.5 GiB workload / 512 MiB swap / one CPU limits. Their peaks were 3,692,720,128 and 643,239,936 bytes. The final source packager-only change required revision/core/launcher relinking; unchanged normal Qt bytes were verified. Gettext's generated catalog normalization is checked for semantic equivalence before restoring tracked source bytes; a genuinely changed Greek message is rejected by the negative control. Both final archives bind to the exact application commit, not a diagnostic overlay on upstream HEAD.

Historical build/test failures remain failures in their named evidence files. Earlier temporary mirror, archive-reader, native filesystem, Qt driver and locale-environment issues have verified corrections. No unresolved S7 acceptance criterion, blocker or tracked deferral remains. [Final controller cleanup](resources/s7/final-control-cleanup.json) is APPLIED with every inspected member removed and the exact root absent. Native UI checks used app-owned events on inactive desktops; captures exclude separately composed video/physical backdrop and establish no physical-listening or Dolby Vision output claim. The delivered Windows binaries are unsigned and report NotSigned; no signing claim is made. No separate installation over the user's VLC occurred.

The Rust improvement scope is R66/S9 after S8. Planning is satisfied; implementation remains NOT STARTED, with no profiling result or resource saving claimed. No S7 acceptance is deferred to those proposed stages.

## S2 execution and acceptance contract

Authorization is already granted. Preserve the reference design and existing VLC controllers; no new playback engine, web replica or general automation framework is needed.

- **R10 / S2 player:** derive source dimensions, spacing, type and colors from the retained Figma nodes before editing. Integrate compact transport/volume, seek between transport and volume in the same bottom row, title/window controls above, separate track/queue entries, and real open/play/pause/stop/previous/next/volume/mute/seek/fullscreen. Keep both light and dark appearance.
- **R11 / visibility:** top/bottom activation regions drive fullscreen chrome from actual pointer, focus and menu state. Retain controls while focused or a menu is open, hide upon leaving, and provide a discoverable hide-all command/shortcut. No delay-based visibility synchronization.
- **R12 / queue:** picker and drag/drop add actual files; remove/reorder preserve playback identity/order; current item and known total duration are visible. Verify edits, next/previous, empty queue and unknown duration separately from stored playlists.
- **R13 / tracks:** separate subtitle/audio entry points, audio-device selection and reachable video tracks; verify real multiple tracks, disabling subtitles, actual device selection and no-track states.
- **R14 / menus and resume:** keep main/context menus and their existing actions reachable, show resume near playback when actual history exists, preserve privacy and keyboard mappings. Later S5 reorganizes broader settings/shortcuts; required S2 player/menu/resume behavior is not deferred there.
- **R04 / state:** reuse existing configuration/queue/history owners and identities; record any necessary new setting's defaults, persistence, migration, reset and recovery before acceptance. Native verification uses isolated E: profiles; compare the installed profile without publishing its contents. Verify restart with representative prior configuration for any changed stored state.
- **R52 / visual acceptance:** establish a concrete source-node/layout contract, inspect rendered native Qt screenshots and measured item geometry against Figma at source aspect/viewport and resized windows, in light/dark and 100/150/200 percent scaling. Check focus, labels, contrast, long text, clipping and open sidebar/menu states. Do not accept the offline renderer's known font/effect/icon errors as design intent. Use original vectors or verified native Figma exports for affected assets; retain licenses/provenance for assets added in this stage.

Execution stays within this single stage: reference/geometry and source integration analysis -> coherent Qt/QML player/queue/track/visibility implementation -> real native workflow and visual acceptance -> reconciliation/cleanup/commit/synchronization. Test-first checks target behavioral contracts where useful; formal acceptance applies to the integrated player, not isolated controls. Add only missing diagnostics needed for these checks and reuse native Qt/accessibility/testing support.

**Current acceptance:** S2 is COMPLETE. Its functional, visual and normal-runtime criteria are verified, and temporary cleanup is complete. The integrated diagnostic build has passed the real player workflow and visual contract:

- R10/R12: actual advancing playback, pause, slider seek, Stop, next/previous after queue edits, picker addition, Qt URL drop, sort/remove preserving the current input, known and mixed unknown-duration totals, and final-item removal to the visible empty queue. The actual localhost stream advanced with unknown length and disabled seeking; its server and the player exited normally.
- R11/R13: native fullscreen edge regions independently reveal their chrome; leaving hides it; keyboard focus, an open native main menu and track popup retain the relevant chrome. Ctrl+Shift+H/Escape hide/restore. Real alternate audio/subtitle selection, subtitle disabling, explicit output-device selection, reachable video tracks, no-audio/no-subtitle video, no-video audio, and constrained popup scrolling are verified. A final 200% dark run verifies pointer coordinates, keyboard focus, accessible labels, popup scrolling and queue fit.
- R14/R04: real history is saved, restored after full process restart, and resumed at the stored engine position after the clock advances. Escape dismisses the suggestion. With existing `save-recentplay` disabled and restore policy Never, no prompt appears and stored progress remains unchanged. No new persisted setting or migration was introduced. Installed configuration hashes still match the pre-test snapshot.
- R52: actual composed video captures pass in light/dark at 100/150/200%, both reference aspect and 680×420 logical resized windows. Source 100% geometry is 1920×1080, title 40px, single-row controls 54px and seek 1238px. A 472px compact window retains all actions and an operable seek target. The retained Figma vectors, Inter font, source colors and single-action resume banner are used. Long multilingual metadata elides within the queue. Focus/accessible labels are inspected; source colors are preserved without claiming a WCAG certification.
- Native blur is verified on actual composed pixels: the video swapchain copies sit above the unfiltered video and are clipped to chrome/resume bounds. The regression rejects both the earlier unblurred chrome and whole-picture blur. The main picture remains sharp. The Figma radius-to-Gaussian-sigma conversion is a visually checked renderer mapping, not a mathematical pixel-identity claim.

**Remaining acceptance and internal blockers:** none for S2. All player functional, visual and normal-runtime acceptance checks pass. The final normal build has no diagnostic markers; its actual delivered path passes plugin-cache generation, first picture, natural EOF, input release, Qt event-loop exit and process exit 0 with no QML runtime warnings. Named QObject callbacks resolved the EOF teardown failure, preserving queued initialization while cancelling it at owner destruction. The installed profile remains unchanged. Reviewed temporary cleanup is complete; the verification record is ready for the final source commit and authorized synchronization. Those delivery actions follow this reconciliation. S3-S7 remain NOT STARTED; there is no external impediment or tracked deferral.

**Root-cause corrections:** the unavailable QtQuick.Shapes import was replaced with original Figma volume SVGs; video hover and the observing keyboard filter now preserve the actual input paths; cached media-name notification exposes the filename fallback correctly. The pinned UPnP 1.14.31 MinGW aliases rewrote inline POSIX functions into recursion, causing the first media-library shutdown to fail; the source guard, native URL regression and subsequent normal media-library exits verify the repair. Blur ordering and all four clip bounds are corrected and pixel checked. A diagnostic-only wheel timestamp now shares the real pointer clock; the failing high-DPI scroll check passes after that correction. Normal EOF also exposed unguarded delayed callbacks in the existing miniplayer/navigation UI; binding each queued method to its QObject owner removes the shutdown warnings, verified by the same normal-runtime regression. Failed/cancelled observations remain failures and are not substituted for acceptance evidence.

All build/test scratch has been removed through reviewed cleanup. Main transaction `ea5ea5bb69e8f9e4ffa5e07924eed0c3` is APPLIED; the separately reviewed process scratch transaction `db07f6ec02e235106bba4b8007f20ef4` is APPLIED. The exact E: scratch root is absent and the owned `VLC-S2-20261018` WSL registration is removed; Ubuntu and Docker remain. Review-runtime test preferences were cleaned through `b9e15e2659e5cc42d065fdfd084045a8` and `2c84125cbb0201d97c47e557ba2c37e0`, preserving its intentional portable directory. The earlier source-side bytecode cleanup `fd6dc72114129dc3880187b207ca625f` is APPLIED. No helper deletion error remains.

Compact [S2 acceptance evidence](resources/s2-verification.json) records the actual workflows, source/build identities, history/privacy results and visual matrix. The normal local review artifact is `E:/VLC-Redesign/S2`, with native captures and fuller evidence in `review`. No derivative design PNG/PDF exports were added to Git. See the [inspection and normal-runtime regression contract](../../tools/windows-player/README.md).

S2 refactor assessment: playback, history, queue and configuration remain with their existing VLC owners. The new chrome and bounded Windows compositor helper serve the current design requirement. The owner-bound queued methods resolve the concrete EOF lifetime failure without a general scheduler or null fallback. Existing shared controls remain for other views; no speculative engine abstraction or additional refactoring stage is warranted.

S2 closure is limited to the working player. The user has now authorized S3 below; S4-S7 and proposed S8 remain NOT STARTED. This does not declare the full redesign complete.

## Stage operation

Activate only one stage after implementation is authorized. Record acceptance criteria satisfied and remaining, blockers with their resolution conditions, and any tracked deferral with its exact later-stage owner and final verification. Close a stage only after inspected verification covers all its criteria. Prioritize the earliest actionable blocked required stage and retain the one-ACTIVE-stage limit.


## S3 execution and acceptance contract

Status: **COMPLETE**, already_authorized on 18 October 2026. Native acceptance, cleanup and source synchronization are verified. Execution is paused before S4.
Use the existing player/controllers and the archived Figma Controls variants
(`498:2937` video, `536:1059` audio, `763:1958` subtitles, `2238:9432`
playback, `2139:8124` waveform, `3744:12361` subtitle timeline), plus the
400-wide effect panels and 1048×800 matching dialogs. Source geometry,
Inter typography, icons and light/dark styles remain authoritative.

| Acceptance unit | Implementation and required verification | Current result / advancement blocker |
|---|---|---|
| R20/R22/R23 subtitle workflow | Real local file/folder/queue matching, ambiguous/unmatched/manual correction, persistence, missing/moved paths; live subtitle appearance/delay and supported text cue timeline; group presets with explicit precedence; consecutive episodes and restart. Preserve upstream image-subtitle playback with an explicit unavailable timeline. | Native file/folder/queue matching, manual corrections, association recovery/isolation, live appearance, SRT/ASS timing/seek/restart, embedded PGS playback, show precedence, restart and reset/removal are verified. Final integrated/normal-runtime reconciliation passes. |
| R24 audio/video effects | Figma sidebars bound to existing real filters, their ranges, presets, reset and live effects; capability-based HDR/resolution. | Native invert/crop/reset pixels, equalizer PCM gain/reset, pitch frequency and exact upstream preset/band/two-pass behavior are verified. Ranges and HDR/source-resolution capability reflect the engine. Final normal-runtime reconciliation passes. |
| R15 previews/waveform | Actual input/time thumbnails and decoded audio waveform; bounded storage/work; invalidation, responsive seek/playback and explicit unsupported/nonseekable states. | Distinct input/time previews, actual quiet/loud and selected-audio waveforms, unchanged-hover reuse, input invalidation, cancellation and unavailable HTTP/audio-only cases are verified. Native v21 also proves repeated seeking and advancing primary playback while waveform decoding is active. Final normal-runtime reconciliation passes. |
| R25 playback tools | Actual speed/reverse capability, cancellable sleep timer with explicit restart policy, analysis/timeline toggles and actual metadata. | Native engine speed, unavailable reverse, real timer expiry/cancel/restart, visibility persistence, keyboard toggles, statistics and source metadata are verified. Final normal-runtime reconciliation passes. |
| R21 remote subtitles | Document provider contract before implementation, visible network/auth/error states, real authorized search/download/association. | The user-selected OpenSubtitles.com, SubDL and SubSource workflows pass real native search/download/selection/save, ZIP64/season archive choice, errors, cancellation/input changes, meaningful names, multiple additions and restart. The authorized free OpenSubtitles consumer remains in the user account. Keys are session-only; encrypted audit material was removed during reviewed cleanup. No credentials or subtitle payloads are published. |
| R04/R52 integrated quality | Preserve installed profile; define versioned new state/defaults/manual precedence/reset/recovery; legacy configuration and restart; Figma light/dark, representative scaling/resizing/keyboard/long labels; normal build without debug hooks; clean scratch and verified commit/source sync. | Legacy defaults and byte preservation, corrupt/newer-version/oversized recovery, Figma light/dark 100/150/200 percent, all four pages, resizing, long fields and keyboard focus/toggles are verified. All accepted snapshots resolve their assets without QML errors. The normal build/runtime, source/evidence reconciliation, installed-profile preservation, cleanup and authorized commit/source synchronization also pass. |

No blockers or tracked deferrals remain. Every assigned acceptance unit is verified. The temporary root `E:/Temp/vlc-s3-20261018`, registered before creation with cleanup transaction `9b32d58f2f97f14de58debdd3b6be417`, is now absent.
Normal S2 review output is preserved independently at `E:/VLC-Redesign/S2`.

Final S3 reconciliation (19 October; native acceptance, normal runtime, cleanup and source delivery verified):

- **R15 satisfied:** distinct real input/time previews, unchanged-hover reuse, aligned quiet/loud and selected-track waveforms, bounded one-job/one-image/fixed-bin storage, cancellation/input invalidation and unavailable nonseekable/audio-only cases. Primary playback and repeated seeks work during active decoding; the second identical seek returns from 28.084 s to 24.646 s. The corrected slider binding also passes volume mouse/Tab/arrow/repeated-click checks.
- **R20/R22/R23 satisfied:** file/folder/queue matching, ambiguity and manual correction, saved associations, missing/changed identities and moved-media isolation; live font/color/outline/size/position pixels; adjustable cue offset and SRT/ASS FPS/delay alignment after seek/restart; preserved embedded PGS pixels with unavailable text timeline. Show defaults, most-specific folder presets, manual input choices, consecutive episodes, restart and reset/removal are verified. Native WebVTT keeps original timing and disables its unsupported FPS override.
- **R21 satisfied:** real native HTTPS search/download/selection/save for OpenSubtitles.com, SubDL and SubSource; valid ZIP64 and explicit five-episode archive choices; authentication error preservation; cancellation/input change without stale association. Meaningful filenames preserve original member/release, public provider reference, canonical language and actual format. Compact track labels put title/episode first. Three additions remain distinguishable and labels restore correctly after restart. Credentials and downloaded subtitle payloads are excluded from source delivery.
- **R24 satisfied:** actual invert/crop/reset pixels; equalizer PCM gain/reset; octave pitch change; exact upstream preset bands/preamp/two-pass behavior. Backend ranges and source HDR/resolution capabilities remain authoritative. The fixes refresh preset initialization coherently and preserve signed fractional gains.
- **R25 satisfied:** actual speed and reverse capability, real sleep expiry/cancel/restart policy, persistent visibility flags, actual statistics/metadata and keyboard toggle behavior.
- **R04/R52 product acceptance satisfied:** legacy font/size and configuration preservation; missing defaults; corrupt/newer-version/oversized stores preserved byte-for-byte; rejected mouse/keyboard toggles retain accepted state and visible recovery status. All four sidebars pass light/dark 100/150/200 percent, resized focus and real Tab navigation, with resolved assets and no QML errors. At 100 percent the panel is 400 by 946 with a 769-pixel body; other scales use a 1920 by 1080 physical viewport and the documented height clamp. Native runtime and original installed-profile preservation are verified; the prior isolated working profile was restored.
- **Normal-runtime acceptance satisfied:** the actual `E:/VLC-Redesign/S3` package passes plugin-cache generation, first picture, natural EOF, input release, Qt event-loop completion and exit 0, with no plugin-load/QML errors and no diagnostic transport or hooks. Windows/chroot implementation sources match; final LF normalization changes only evidence JSON line endings.
- **Refactoring assessment:** the existing VLC controllers own playback/track/filter state; the new store owns only S3 associations/presets/toggles. Bounded analysis and three explicit providers serve current requirements. No additional architecture or remediation stage is needed.

[Verification](resources/s3-verification.json), [workflow measurements](resources/s3/workflow-metrics.json), [native observations](resources/s3/native-observations.json), [theme/scale review](resources/s3/scale-matrix.png), [track names](resources/s3/subtitle-names.png), [subtitle appearance](resources/s3/subtitle-appearance.png) and [timing pixels](resources/s3/subtitle-timing.png) preserve compact evidence. The original Figma and exported-icon hashes still match their registered provenance.

**Cleanup satisfied:** transactions `9b32d58f2f97f14de58debdd3b6be417`, `87c5398ed57f434b64c0891f782ee8fe` and `c55f34ee4edb5ce5e62d809e6a4a09a2` are APPLIED with no errors/exclusions. All 11,060 reviewed members and 14,297,318,943 logical bytes were removed. The exact E: scratch and generated bytecode roots are absent; the disposable WSL instance is retired, Ubuntu/Docker remain, and the normal review runtime has a fresh empty portable profile. These are logical deletion counts, not a physical-free-space claim.

**S3 COMPLETE:** all assigned acceptance criteria and required integration are satisfied and verified. No blocker or tracked deferral remains. Implementation commit `523d4146fe2678239126cc0b14fbff3315a6265f` was independently matched to `origin/master` after the authorized source push; this documentation records that completed delivery. The final documentation head is checked separately after synchronization. The normal review runtime remains at `E:/VLC-Redesign/S3`. S4-S7 and proposed S8 remain NOT STARTED; no installation or release occurred.


## S4 execution and acceptance contract

- **R30:** Figma library chrome, discoverable title/sidebar entry, compact library alongside playback, full library/miniplayer/queue; real item drag into queue preserves current playback.
- **R31:** real indexed videos/folders/music/network/playlists/recents/home; breadcrumbs/address/search/grid/list/detail/sort/watched filters; music songs/albums/artists/genres; missing metadata and empty categories.
- **R32:** stored playlist create/manage/add from other views; persistent folder/playlist pins; recent/resumable home respecting history/privacy; restart and queue independence.
- **R33 open portion:** file/folder/disc/network URL and playlist/capture/clipboard/recent entry points; one real network playlist; preserve upstream actions without bundled third-party channel lists. S5 retains conversion/stream configuration organization.
- **R04/R52:** existing state owners and installed profile preservation; document any new persisted key's defaults/precedence/migration/reset/recovery; real native light/dark, scale/resizing/keyboard/long text Figma comparisons; affected S2/S3 regressions; normal runtime without hooks; reviewed cleanup and verified source delivery.

All assigned S4 acceptance criteria are satisfied and verified. No blocker or tracked deferral remains. S4 closes at its requested stop; S5-S7 remain NOT STARTED.


S4 reconciliation checkpoint (23 October):

- **R30 native acceptance verified:** indexed local/HTTP playback; title/sidebar entry; compact/full library, miniplayer and queue transitions. Held internal drag adds real media while the same input keeps playing and its clock advances. The final first-unselected-row case passes after moving selection commitment out of the held gesture. The complete miniplayer moves and fits after resize. These are Qt framework events without OS foreground ownership; desktop OLE routing is not claimed.
- **R31 native acceptance verified:** Unicode/# indexed roots and subfolders, complete breadcrumbs/direct empty-folder addresses, folder/root search, Grid/List/Details, title/order/watched sorting, watched/unwatched roundtrip and partially watched filtering. Mixed native media models expose all audio files when browsing from the current audio title, preserving paused input/time. Songs/albums/artists/genres use actual metadata, including a file without metadata. The native root/subfolder APIs return all children, so search/sort/cache pagination are applied explicitly.
- **R32 native acceptance verified:** stored playlist create/fill/rename/delete/remove-selection without queue/input changes; folder/playlist pins and view persistence across restart. Home uses native Continue Watching, Listen Again and history-ranked Frequently Visited Folders. Actual resume advances from the stored 0.749809 position to 90.016 and 90.140 seconds. History-disabled views instantiate no history models and exit normally; clearing history empties all three shelves. A 1340-unit playlist name survives pin/restart with a bounded 1024-unit cached shortcut, resolving its full native name on opening; the owned fixture was unpinned and deleted.
- **R04 state acceptance verified:** the existing interface owns only `redesign/library-v1` pins/details; existing `MainCtx.gridView` remains the Grid/List owner. Malformed/newer/oversized/legacy-grid/wrong-identity stores remain read-only and byte-preserved through normal exit. Reset removes own pins/details while preserving the existing List preference; a missing key remains absent. Installed-profile hashes have matched the original baseline; final post-runtime comparison remains.
- **R33 open acceptance verified:** actual HTTP M3U expansion and decoded first video. File/folder/disc/network/capture/clipboard and recent entry points remain reachable, including narrow menu scrolling/keyboard focus. Existing upstream advanced actions remain available; S5 owns conversion/stream configuration organization. No physical disc/capture device, global clipboard read or third-party channel-list claim is made.
- **R52 visual acceptance verified:** Home/Network edge fragments are absent. Original signed Figma matrices and cached Boolean outlines are preserved. Native Home headers/cards/shelves, rounded artwork, compact navigation and source icons pass measured source geometry in light/dark and representative 100/150/200 percent scaling. Long/narrow breadcrumbs, Home/form focus reveal, bounded menus and miniplayer resize pass. Final network/context glass matches source fill/corners/blur; its resources exist only during a visible popup. Qt's cached-shader manager status is not a valid completion predicate; resolved textures, shader errors and actual pixels govern readiness. All four existing S3 media-tools pages open with resolved assets and no QML errors. Final composed player pixels show real video in both themes; a glyph-free light-theme sample has 38 blurred chrome levels versus six in the sharp picture.

**S4 COMPLETE:** native product acceptance, normal runtime at the actual review path, source parity (with recorded line-ending-only normalization), installed-profile preservation, reviewed cleanup and verified implementation source synchronization pass. [Verification](resources/s4-verification.json), [native evidence](resources/s4/native-observations.json) and [workflow metrics](resources/s4/workflow-metrics.json) retain the reconciliation. The normal review runtime is `E:/VLC-Redesign/S4`. Implementation commit `091137df2081df5e3cf2a8886463e8400a9050a3` was independently matched to `origin/master`; this closure documentation is synchronized afterward. S5 has not started.

The pinned Windows baseline completed at 2026-10-23T01:16:28Z in disposable `VLC-S4-20261023`, under the registered E: root. Fresh overlay mtimes are required to regenerate changed MOC/QML inputs. A history-disabled native assertion was traced to a null ML owner, corrected and revalidated. Two failed test launches were retained as failures: an unsupported theme CLI option and an overlapping profile restart; neither caused a product workaround. The HTTP fixture server has exited normally.

CDB cleanup transactions `ae534ace91986e0dd81c8659381acc47` and `5dfc5dc1f78fe9422b5d85372d35eb54` removed exactly nine new symbol files (7,008,256 logical bytes) and eleven new empty directories. Their exact paths are independently absent; pre-existing cache entries were preserved. Main E: cleanup transaction `9be92acd7bbe74e138e0666a6e919364` is APPLIED with 5987 members and 10,000,747,691 logical bytes removed, no exclusions/errors, and the exact scratch root absent. Normal-review profile transaction `56af18723805dfc73d1b38d39cd243be` is APPLIED with ten members and 606,799 logical bytes removed; a fresh empty portable directory is the intentional review deliverable. Ubuntu/Docker and prior S2/S3 review runtimes remain. These are logical counts, not physical free-space claims. No intermediate application release or installation occurs.

**Closure refactoring assessment:** existing VLC controllers and ML models retain playback/library identity ownership. The new store owns only pins/details, and existing Grid/List state remains authoritative. Shared popup glass serves two current source designs with visible-lifetime ownership. No material required consolidation, new abstraction or additional implementation stage is warranted.


## S5 execution and acceptance contract

S5 is COMPLETE. Every assigned product, verification, preservation, cleanup and implementation-source delivery criterion is satisfied.

- **R03/R14/R33:** reconcile the native capability/action inventory; preserve all commands and resume/privacy behavior; make conversion and streaming configuration distinct from ordinary opening.
- **R40:** direct bookmark action and conflict-checked shortcut, native bookmark/chapter sidebar with real seeks, editing/removal and restart persistence. Retain native media identity/storage.
- **R41:** directly accessible shortcuts, real mappings/conflict handling/remapping, input-field focus, action feedback/preferences.
- **R42/R43:** Figma preferences categories, integrated basic/advanced sections, visible help, real native option metadata/defaults/ranges/restart/persistence, complete option reachability, separate installable add-ons/extensions and internal module settings; real supported extension verification.
- **R04/R52:** explicit changed-state contract, installed-profile preservation, prior-setting/restart/reset/recovery behavior and actual native Figma comparison at representative theme/scale/resize states including Widgets.

**S5 COMPLETE (24 October):** all assigned acceptance criteria were satisfied and verified. No S5 blocker or tracked deferral remained. At that close, S6-S7 and proposed S8 had not started and authority stopped after S5. The subsequent S6 authorization and current completion are recorded above; no intermediate application release or installation occurred.

| Acceptance unit | Satisfied and verified | Remaining / blockers / tracked deferrals |
|---|---|---|
| R03/R14/R33 | All 1755 public native option keys match the UI, with one Qt configuration owner. Main/context menus retain upstream builders. Real resume and history-disabled privacy pass. Distinct native Convert/Save and Stream paths reach actual configuration; real default H.264/MP3 output finalizes, independently probes as 90.076 seconds and reopens with both tracks and an advancing clock beyond 86 seconds. | None. |
| R40 | Native bookmark add/seek/rename/remove, embedded chapters, Unicode title/restart, media isolation, no-chapter/no-ML/nonseekable states. Real native database refresh preserves the timestamp-selected bookmark and unsaved rename draft. Test bookmarks are removed afterward; the original three remain. | None. |
| R41 | Reserved shortcut rejection, explicit conflict/assignment/Cancel, remapping/restart, real play/bookmark/jump actions, native and Quick field focus, feedback options/defaults/range and shortcut-only Reset staging/Cancel/Save/restart preserving unrelated settings. | None. |
| R42/R43 | Thirteen actual source categories, native metadata/help/defaults/ranges, lazy module search and typed settings Save/restart. Legacy views 0/1/2 and invalid accent preservation; locked Save/Reset byte and memory rollback, Cancel/retry and confirmed full Reset. Read-only language lookup preserves the absent installer key through startup/open/Cancel/unchanged Save/full Reset. Supported VLSub activation/configuration/search/info and native add-on manager work; internal modules remain in category advanced sections. | None. |
| R04/R52 | Native recovery Yes/No/unanswered state and existing storage owners. Scoped native config/PCR/Qt lifetime regressions pass. Actual final Widgets/QML captures and measured source geometry pass representative night/day 100/150/200-percent, keyboard, Unicode and narrow file-editor cases. Current source/build parity and installed-profile/registry preservation pass. The actual normal package passes native ML startup, first picture, natural EOF, input release, finished Qt event loop and exit 0, with no QML/plugin-load errors or diagnostic hooks. Exact reviewed cleanup and verified implementation-source synchronization pass. | None. |

Native regression evidence preserves false config-save success returns, the late-track PCR assertion and cursor invariant, shortcut/recovery owner-lifetime errors and MinGW timer/regex TLS teardown failures. Their corrections use existing native owners; no timer waits, allocator poisoning, disabled JIT, replacement bookmark schema or substitute settings database is introduced. Functional observations from older failed-exit runs remain separate from verified normal exits. Duplicate plug-in discovery, mislabeled category traversal, overlapping launch, premature output probe and a test launch without its companion DLL are excluded from acceptance.

Native QWidget captures are actual app-rendered pixels; they omit separately composed video and do not prove desktop backdrop blur pixels. Fully offscreen WGC returned a uniform grey frame and is rejected as visual evidence. Source tint/corners are verified in the widget renderer; the existing provider supplies platform backdrop effects where supported. S6 retains its R50 theme/accent lifecycle acceptance, including previously created native dialogs.

[Native observations](resources/s5/native-observations.json), [option inventory](resources/s5/native-options.json), [visual contract](resources/s5/visual-contract.json), [source parity](resources/s5/source-parity.json), [lifecycle regression](resources/s5/lifecycle-regression.json) and [normal-runtime verification](resources/s5-verification.json) retain compact evidence. Actual native matrices cover [all categories at night/100%](resources/s5/categories-night-100.png), [representative day/150%](resources/s5/light-150.png) and [night/200% with narrow forms](resources/s5/dark-200.png). Full native PNGs remain in `E:/VLC-Redesign/S5/review`, rather than duplicating Figma exports.

**Cleanup:** all three [transactions](resources/s5/cleanup.json) are APPLIED with no errors/exclusions: 9949 exact members and 10,465,729,731 logical bytes removed. The exact scratch root is absent, disposable WSL registration `VLC-S5-20261023` is retired and Ubuntu/Docker remain. The normal review package at `E:/VLC-Redesign/S5` has a fresh empty portable profile; prior S2/S3/S4 packages and the installed profile are preserved. These are logical deletion counts, not physical free-space measurements.

**Source delivery:** implementation commit `8cb127eb16689a4905822abf57d4e418b764c33d` was independently matched to `origin/master` after push. Every maintained implementation blob matches the verified build-source hash manifest, including the native files outside the sparse-checkout definition. This closure documentation is synchronized afterward and the final head checked separately. No intermediate release or installation occurred.

**Closure refactoring assessment:** native ConfigControl/metadata/config and interface settings retain their owners. The presentation groups current options and exposes existing extension/module capabilities. Native ML owns bookmarks; selection/draft state is transient UI state keyed by native timestamp. Shared native styling serves the currently required dialogs. Config/PCR/Qt dependency corrections address reproduced current-stage failures with focused native regressions. No additional architecture, abstraction, remediation stage or required consolidation is warranted.
