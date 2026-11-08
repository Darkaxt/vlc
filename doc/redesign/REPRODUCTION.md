# Desktop reproduction and recovery

## Native desktop port in progress (M15, 8 November)

Normal1.1.11 below is still the verified downloadable release. Native packaging
work lives on `codex/native-desktop`; it has not replaced master or published a
release. The workflow is `.github/workflows/desktop-packages.yml`, using native
`macos-15`, `macos-15-intel`, `ubuntu-24.04` and `ubuntu-24.04-arm` runners,
one compiler job and no local WSL workload. Its explicit target selector avoids
adding unrequested matrix rows. Native sources/actions are pinned; installed
toolchain package/compiler identities bind the reusable objects. Preserve the
original run/job and cache identities during repair; do not clean/reconfigure
unchanged inputs or infer native playback from an uploaded artifact.

The new backend uses stock upstream MPV0.42.0, commit
`b0841e8c4d156b8403dc1876c4cbd9011eb583f3`, on Cocoa and X11/XWayland, with a
Qt-owned OpenGL render context. It does not require the Windows DV patch. The
Windows D3D11/WASAPI implementation and `player/mpv/source.json` retain their
separate source/runtime binding. `source-portable.json` and
`tools/desktop-player/native-inputs.json` identify the native inputs. The latter
binds upstream macOS contrib `e0baa29690f97c5d746643d59358fd6055eda8f6` after
checking that the intervening contrib delta is confined to the recorded Windows
Qt/UPnP files. Do not construct a VideoLAN artifact URL from a fork-only commit.

Initial run42424025878 from41d03952a9381115b067382209d57ab417c364b2 compiled
stock MPV on Apple Silicon, then failed to resolve Brotli's LC_RPATH during
staging. Intel found libplacebo7.360.1, below MPV's required7.387.0; Linux x86
found an absent GLAD2 source submodule. The prepared corrections resolve declared
native runpaths and fetch the exact libplacebo/submodule pins. Their native
execution and actual Qt player acceptance remain pending. Linux ARM
job128558356675 confirmed the same GLAD failure; the original run and its local
watch session have exited with failure, preserving their caches. No package from this run is a
qualified release. M15's remaining package/source/license and real playback
criteria are recorded in PLAN/SPECIFICATION.

Run42426649287/job128566297996 (91c16ad3c5a80dbf7310a900c893a43af4cbe48b)
compiled/linked the Qt redesign including native MPV, then stopped linking
ncurses against its prebuilt producer SDK path. Preserve cache ending42426649287;
the next driver overrides only ncurses's SDK flag with the selected `xcrun` SDK
and records original/resolved flags in `native-link-bindings.json`. Generated
bootstrap files now retain exact nanosecond mtimes, avoiding a cold configure
on a new runner checkout. The initial cache needs its explicitly recorded,
input-verified bootstrap reconstruction once.

`prepare-native-review.py` copies the normal Mac app into `$RUNNER_TEMP`, builds
only the existing test-only `mainui` diagnostics, relocates that plugin against
the normal app's dependency map and restores normal objects/library hashes and
mtimes in `finally`. `verify-native-player.py` uses owned filesystem/process
events, isolated profiles and synthetic media; it requests both Qt-only and
owned native-window captures. Neither its prepared source nor Quick-only
pictures qualify native playback. Inspect composed pixels and actual results.
Linux's equivalent display/audio session remains required implementation.

## Current1.1.11 stabilization diagnostics

Normal [1.1.11](https://github.com/Darkaxt/vlc/releases/tag/redesign-v1.1.11)
binds source `9b421345116abb28917edfac30a8a64c9b2884d0`. Current usable player:
`D:/VLC-Redesign/releases/1.1.11/Modern-VLC-Fork-1.1.11-win64-portable/vlc.exe`.
All four published assets were independently retrieved and hash-checked;
downloaded VLC starts with the shipped cache untouched and plays/exits normally.
MPV SDR/P5 actual presentation and downloaded lifecycle pass. Automatic logging
keeps today and two preceding UTC dates, pruning at launch/day/size rotation,
eight4MiB files maximum. Explicit saved/CLI disable works; explicit destinations
remain user-managed. No background cleanup runs while closed. Cachegen and
preparser opt out. UTC receipt timestamps differ from buffered core-phase elapsed
timings; the latter use a stable clock across Windows thread initialization.
The full intermittent30s report is not yet attributed to app or system.

Normal276/run85 `0b66389faa21411d954b862ad626ed03` closes0/group empty, private
mounts released, no OOM,30.6s affected player build. Current read-only receipt is
in1.1.11/verification/retained-build-result.json. The retained native ext4 runtime
and pipeline remain `/scratch/preview-1.1.8/runtime` and `compilation/state.json`;
Windows mirrors are `scratch-share/logging-ready-1.1.11/runtime` and `compilation`.
Native symbols are `/scratch/logging-ready-1.1.11-release-symbols`; next pipeline
directory0086. Reuse the installed WSL gate and
`verify-retained-build-1.1.11.py /scratch/retention-delivery-1.1.11.json` through
the current native private chroot. Preserve3.5GiB/512MiB/oneCPU/onecompiler,
-O3/-g0,NDEBUG,QML debugger disabled, pinned prefixes and unchanged mtimes.
Do not initialize SDKs or rerun configure for unchanged inputs. Old1.1.10 paths
below are historical; its recovery evidence is read-back on G:. Required current
release assets and runtime/pipeline stay retained; spent Windows acceptance output
is retired. Unsupported native symbol-alias cleanup remains explicitly recorded
under historical M6 rather than using raw Linux/UNC deletion.


## Current1.1.10 startup delivery

Normal [1.1.10](https://github.com/Darkaxt/vlc/releases/tag/redesign-v1.1.10)
binds source `ed36b5fabdbbc89171061f1f08a5515480fce2b0`. The usable local player is
`D:/VLC-Redesign/releases/1.1.10/Modern-VLC-Fork-1.1.10-win64-portable/vlc.exe`.
All four assets are independently retrieved/hash-checked. The exact410-plugin
index is generated from stripped DLLs at a fixed UTC mtime; ZIP DOS-local, UTC
and NTFS timestamps preserve native validation after standard Windows extraction.
Do not run cache-gen before downloaded-package acceptance. The verifier leaves
the shipped cache untouched by default; `--generate-plugin-cache` is an explicit
build-tree diagnostic. A timestamp-resetting extractor still gets correct native
rescanning. Full module count603,7-Zip/PowerShell relocation and changed-plugin
invalidation are verified. The native-window-show benchmark is not first-paint
evidence and does not flush Windows caches or explain the complete10+s report.

Normal run81, Coordinator271 `a29cc1ed6bb94bbcb49a2fcdcef4e144`, built the affected
step in45.6s and closed0/group empty with private mounts released. Read-only272
`999132bbf75b4a8289cb755181bf3c89` verifies the continuing417-PE native cohort,
configuration and codec link maps. No SDK/MPV dependency rebuild/reconfiguration.
The native runtime/pipeline remain `/scratch/preview-1.1.8/runtime` and
`/scratch/preview-1.1.8/compilation/state.json`; the Windows mirrors are now
`D:/VLC-Redesign/build/windows-x64/scratch-share/startup-1.1.10/runtime` and
`compilation`. Next pipeline directory0082. Use the current installed WSL gate
and `verify-retained-build-1.1.10.py /scratch/retention-delivery-1.1.10.json` with
both explicit arguments through the native private chroot. Keep the same limits,
native SDK, dependency prefixes and unchanged-source mtimes.

Current compact receipts are in1.1.10/verification. The prior1.1.9 evidence index
points to a read-back G: archive; old paths in those records are provenance,
not current launchers. Superseded release packages and test runtimes are retired.
Historical material below retains its original identities and is not current
launch clearance.


R109/M13 startup optimization is ACTIVE. Use the current1.1.9 below as the normal
baseline; fresh-package startup must not run vlc-cache-gen before measurement.
The previous verifier did prime the index, so its lifecycle result alone is not
a cold-start performance result. Profile after cleanup I/O is idle, preserve real
profiles and use isolated owned native windows without desktop controls.

Current delivery is normal
[1.1.9](https://github.com/Darkaxt/vlc/releases/tag/redesign-v1.1.9), source
`dbb446b6ccb8619d46ba2244ac12bd4f3eb88e32`. Run the local usable executable at
`D:/VLC-Redesign/releases/1.1.9/Modern-VLC-Fork-1.1.9-win64-portable/vlc.exe`.
All four published assets were independently downloaded/hash-checked. Normal VLC
and MPV lifecycle, actual SDR/P5 presentation, stripped417-PE mappings, complete
corresponding source and protected profiles pass. M8/M9/M11/M12 ledgers record
the accepted native workflows and original test-observer failures separately.

Normal80, Coordinator268 `1b76b18d07a34962a10ebc2c4a893c38`, closed0/group empty
with private mounts released and no memory-limit/OOM events. Qt took156.1s;
retained native-ext4 SDK/MPV/codec objects and409 plugins were reused. Read-only
Coordinator270 `48bc995446624c699daf53f0ccce6825` verifies the continuing source,
configuration, stripped runtime and codec link-map binding without rebuilding.
Its original269 failure was an unstaged delivery JSON; the corrected explicit
input passed on the unchanged build. Current next pipeline directory is0081.

Current qualification and compact frozen controls are in the delivered version's
`verification` directory. `RAW-EVIDENCE.json` binds the exhaustively read-back
G: archive of raw snapshots/captures; these are retained regression evidence,
not runtime inputs. Original absolute paths in frozen records are provenance,
not installed launchers. Superseded ordinary review runtimes are retired.
`build-retention.json` binds the actual1.1.9 native source/runtime/pipeline/symbols.
Use `verify-retained-build-1.1.9.py /scratch/retention-delivery-1.1.9.json` through
the installed WSL gate/private chroot so both control and receipt are staged.
Do not restore old NTFS compiler paths or reinitialize/reconfigure unchanged inputs.

The continuing build consumer is now `VLC-Build-20261106` with its D:-backed ext4
root `/toolchain`. Source is `/toolchain/work/src`, build is
`/toolchain/work/build/win64`, runtime is
`/toolchain/scratch/preview-1.1.8/runtime` and pipeline is
`/toolchain/scratch/preview-1.1.8/compilation`. Windows finished-artifact mirrors
remain under `D:/VLC-Redesign/build/windows-x64/scratch-share/icons-1.1.9`.
Use the installed WSL Coordinator launcher and `with-isolated-toolchain.py
--native --scratch /mnt/d/VLC-Redesign/build/windows-x64`, without `--initialize`.
Preserve4GiB shared VM,3.5GiB workload,512MiB swap, one CPU and one compiler job.
Native storage sets the Windows-header-copy cache to0. No SDK reinstallation,
configure rerun or dependency rebuild is needed for an unchanged UI-only delta.

`build-retention.json` and `verify-retained-build-1.1.8.py` bind normal236
`c08d05c518ae4dcab33b604ddfed06f9` and read-only237
`b028ce36e0314fb6abfd7eb1522dc809`. Both closed with empty Linux groups and
released private mounts. Use the matching optional1.1.8 symbols ZIP to seed a
fresh incomplete manifest from verified unchanged mappings. Never mutate a
completed symbol manifest. The weekly schedule has been read back against this
exact binding. Old NTFS paths below are historical, not another build target.

The superseded NTFS toolchain, old Windows runtime/pipeline mirrors, obsolete
local1.1.7 and spent task roots were retired through signed helper tickets after
consumer and recovery checks. Source recovery is
`G:/VLC-Redesign/recovery/native-migration-20261106.git`; prior1.1.7 verification
and isolated-profile evidence is in
`G:/VLC-Redesign/evidence/1.1.7-verification.zip`. The corresponding recovery
contracts, hashes and applied cleanup receipts are retained with1.1.8 evidence.

Bind a raw reusable assembly using `VLC-PLUGIN-BUILDINFO.json`, its actual native
DLLs and the recorded assembly/source receipts. Its inherited package-seed
`BUILDINFO.json` is historical. `package-release.py` generates the delivered
`BUILDINFO.json` afresh from the exact source argument and native DLL identity;
the independently checked1.1.8 package has the correct version/source/Qt hash.

R96 cleanup is still tracked in PLAN.md. Native read-only238 inventoried spent
`/toolchain/scratch/runtime`, `/toolchain/scratch/compilation` and
`/toolchain/scratch/preview-1.1.8/normal-symbols`; the active1.1.8 runtime/pipeline,
compiler objects and VHDX are excluded. Installed transactional-cleanup0.9.0 has
no native Linux backend. Do not bypass it with raw deletion or UNC mappings.

Historical reproduction checkpoints follow; their original pending work, release
paths and rollback instructions are superseded by the current binding above.

6 November M6 storage migration: keep normal1.1.7 as the delivered
rollback. The interrupted optimized Qt assembly remains run44, original225
`b8aa2029e76d416b8770072015525a2e`, with its exit137/group-empty report. The
authorized native destination is the VLC-only distribution `VLC-Build-20261106`
at `D:/VLC-Redesign/build/wsl-native-20261106`. Windows imports only a small
bootstrap selected from the exact pinned snapshot; bulk restoration into
`/toolchain` uses the supported WSL gate. A private chroot preserves `/work`
paths, SDK/MPV/codec objects and source/input nanosecond mtimes. Restore229 and
verification230 completed0/group empty with zero content/link/timestamp mismatches
and unchanged configure inputs. Binding `83d35faf-0581-4379-97be-4484c904eed4`
records the verified ext4 root. Native continuation231 and affected repairs232–235
have completed0/group empty with released private mounts;235 is pipeline49 from
`c9fbd50e4dd3b1f2e222a1ff957005a20537fca3`. The affected Qt step took27.0 seconds.
The complete native media/engine and wizard checks use
`D:/Temp/vlc-s8-preview-1.1.8-mpv-photo-20261106`; original failed checks remain
historical evidence. The existing NTFS cohort
remains frozen rollback until content/configuration/performance verification,
native compilation, full M6 acceptance, normal1.1.8 delivery and weekly binding
verification pass. Ubuntu, Docker, the default distribution and `.wslconfig`
must remain unchanged. No SDK installation/configure or global resource change
is part of this migration. Use `with-isolated-toolchain.py
--native` through the installed WSL gate, with one compiler job and the retained
normal-mpv-current409-plugin guard; native storage disables the NTFS header-copy
cache. The pending controls and original-operation records are under the exact
M6 paths recorded in PLAN.md.

Normal 1.1.7 is delivered from `e9caba476b64c27817ef935532d22921bae28f43`. Canonical `D:/VLC-Redesign/build/windows-x64` source/runtime/pipeline/objects and pinned dependencies passed read-only verification `10ede87d304f49a8ac4ab4245a45d4f6` after normal223/run43 (`bcdd28e63a3842c0a5a9f6969083be09`). Use `build-retention.json`, `verify-retained-build-1.1.7.py` and the matching optional1.1.7 symbols ZIP. Seed a fresh incomplete symbol manifest from verified unchanged pairs; never write into a completed manifest. Current native/artifact/delivery evidence, original checker failures and actual reviewed images are retained at `D:/VLC-Redesign/releases/1.1.7/verification`. Frozen snapshots preserve original paths and are not installed launchers.

M5 reproduction: use a separate copy of the normal portable package with an empty portable profile. Click a shortcut keycap on the final setup page: capture, named conflicts, Reassign, Unset, Cancel and Escape stay inside the wizard. Finish saves accepted edits; cancel/failed save preserves previous bindings. Restart to apply shortcut changes. In Keyboard Shortcuts, searching Stream or Ctrl+S exposes the editable interface command. The complete 100% wizard/rollback/restart workflow, 150/200% layout/capture-cancellation/Finish/restart checks and standalone Stream save/restart/actual-dispatch evidence retain its real diagnostic producer `3c1ce0f16be7d21e558e2d966f3c52a85b9f7000`; the normal delivery has identical production blobs. The resumed release reused the completed assembly and did not compile again.

Historical checkpoints follow with their original paths and outcomes. Selected1.1.6 records, reviewed pixels and isolated-profile recovery inputs are retained under `verification/prior-1.1.6-evidence`; redundant intermediates and older release packages were retired only after verified1.1.7 delivery and retained/weekly binding checks.

Normal1.1.6 is delivered from `bf45ca9748427279b08b995755c52f164f78e60d`. Canonical `D:/VLC-Redesign/build/windows-x64` runtime/pipeline/source/objects and pinned dependencies passed read-only217/62562fb08c66414f812db083f542be4a after normal216/run39. Use `build-retention.json`, the installed `verify-retained-build-1.1.6.py` and the matching optional1.1.6 symbols ZIP; seed a fresh incomplete symbol manifest for the next incremental writer. Current qualification, original failure evidence, saved isolated profiles and frozen control snapshots are retained at `D:/VLC-Redesign/releases/1.1.6/verification`. Frozen snapshots preserve original paths; they are not installed launchers. Spent D:/Temp native trees, old candidate/control roots and unpublished local1.1.5 were removed through the recorded exact cleanup transaction after consumers exited.

5 November1.1.6 continuation: retain normal run38's objects/toolchain and seed a
fresh incomplete split-symbol manifest with its411 verified unchanged mappings.
Exclude the six regenerated app/Qt mappings; preserve the complete417-entry old
manifest. A complete manifest is an immutable recovery input, not an incremental
writer destination. Keep manually launched reviews in their own package copy:
Windows uses the adjacent portable directory, so launching the canonical package
pollutes later empty-profile qualification. Native acceptance clones a pristine
package; preserve the earlier prelaunch failure and active review profile.

5 November auxiliary-host correction: normal213/run0036 completed the normal
player/assembly0. Its controller then closed1 at the terminal retained-manifest
assertion; preserve its original report and the separate provenance reconciliation,
not a rewritten success code. Native49106 passed the source80a891 menu/engine/
transport/sidebar delta. Qualification26288 prepared and verified all three normal
archives and native VLC checks, then actual SDR presented/EOF/released0 but failed
all-window placement because `Static`/`dummy` occupied `[0,0,6,6]`. No Default
relaunch of those bytes is permitted. Its window events identify COMCTL32, and
the only matching creation is createBackHostVisual's show-before-cloak at0,0.

`acrylic-host-probe/result.json` under the existing D: native root compares both
creation orders on an owned inactive desktop. Owner-bound creation, nonactivation
and cloak-before-show pass; the native process/resources close0. Apply that exact
creation order in the player and preserve the original placement failure. Use a
same-mode normal-mpv-current continuation: unchanged diagnostic flags permit
reuse of all other Qt objects, SDK, MPV, codecs and409 plugins. Verify the changed
helper plus fresh exact-package SDR/P5 placement/presentation before any composed
review or publication. All earlier producer identities remain explicit.

4 November paused-overlay continuation: normal211 was stopped under its exact
owned request66f86108cd684ef7b46ba49cd1baec45 after the actual panel rejected blur;
its final report records exit137, empty Linux group and no max/OOM events.
Preserve the interrupted pipeline identity and all completed objects. The current
source repair binds declared QML backgrounds before presentation, adds the MPV
purple/header emblem without changing the saved VLC accent, and retains the gear
panel across transport clicks. Verify this complete delta together before normal
qualification; do not reuse209's old widget success as proof of these new changes.
The native probe's late-bound/early-bound paused-resize pictures and the manually
resumed player establish the blur lifetime defect. There is no new decoder,
CPU frame readback, sleep/retry loop or vout/core ABI change in its repair.

4 November normal826 composed-picture rejection: M4 remains ACTIVE and1.1.5
unpublished. New source work replaces system Desktop Acrylic with a live thumbnail
of the app-owned source window, blurred on the existing native widget's own Qt
DirectComposition target. One14-logical-pixel clip owns Settings/menu UI and blur;
combo surfaces use6px. The header stays opaque and the body retains the reference
95% tint over Gaussian sigma25px at the actual DPR. Disable the second DWM border,
corner clip and Qt's temporary fade/roll windows. No desktop capture, CPU frame
readback, second decoder, extra window or OS transparency change is introduced.

The pinned Qt6.8.3 QPA accessor patch is
`contrib/src/qt/0003-Expose-the-existing-backing-store-swapchain.patch`.
`tools/windows-player/repair-qt-backingstore.py` applies it under the supported
managed toolchain, rebuilds only the retained QtGui target and stages its archive.
An opt-in, typed RHI/swapchain pair is published on the owning QWindow at flush;
no Qt header/class layout/API/ABI changes or dependent SDK rebuild is needed.
It records all Qt archive pre/post hashes and recovery in
`VLC-QT-BACKINGSTORE-REPAIR.json`; packaging conveys that receipt with the source
and portable runtime. No SDK configure/bootstrap, compiler-flag change or VLC
core/plugin ABI change is required. The exact patch/recipe/receipt exception in
the normal current-plugin guard retains every non-Qt plugin under its existing
binary and source binding. Unexpected dependency changes still fail that guard.
Actual Windows-composited pixels, first-show timing, resize/lifetime behavior,
both-engine video context menus, Settings and normal release qualification remain
required; source readiness or a committed native visual does not establish them.

Build207 closed0 with the pinned QtGui bridge archive
`c03fd79580c85cdf9846308080d6a72f7f70c4821e45b001ec5421da09f3b357`.
Its native menu workflow closes0 but rejects E_INVALIDARG before composition is
ready. The owned inactive probe at
`D:/Temp/vlc-s8-settings-1.1.5-20261102/native-content-api-updates/result.json`
identifies the actual DirectComposition protocol: a target-root visual cannot be
added as a child until SetRoot(nullptr), and cannot be restored as a root until
RemoveVisual. Shared thumbnail updates require DWM_TNP_ENABLE3D on every call;
the same update returns E_INVALIDARG without the bit and S_OK with it. Commit
the complete new tree atomically and preserve the inverse ownership order on
release. The small MSVC probe did not rebuild Qt/VLC or touch the input desktop.
The original failed native result remains retained; it is not accepted evidence.

Focused209 (`ec97458032ea41e39a46ec4196151eff`) closes0/group empty/private
mounts released after the explicit QString conversion repair. Source20265f45,
Qt14387b6263ad5075f8abb3266832691da44ba609ae1338f1b9202ef8deacaff6 now commits
the live context/submenu backdrops in both engines. Native getter34 is unsupported
on this host despite setter34 returning S_OK; the independent border-readback
probe records both HRESULTs. Record an unavailable query, never invent a border
readback or substitute it for the mandatory actual-pixel check. Count VLCMenu
parents alongside QMenu children and require populated deferred child actions.
Original native71930 closes0 with all four cases passing: menus in both engines,
all Settings at100/150/200%, icons and idle/audio/video/customization/EOF.
`native-content-checker-acceptance.json` binds source20265f45, Qt14387b62, checker
694b18a9 and each result hash. Current widget/contact-sheet pictures were inspected;
`native-content-widget-picture-review.json` records their precise visual scope.
The reconciled native/visual receipts preserve previous producer records and
verify unchanged owner sources, including whole MPV source equality after removing
only the newly tested right-click forwarding branch. They explicitly leave actual
Windows-composited blur/corners unverified. Reuse that evidence for unchanged code.
The private composed-capture proof remains failed because the test dialog lacks
native WS_EX_NOACTIVATE. No input-desktop launch follows that failure. Reuse the
normal package review procedure for the exact normal binary; preparation is not
acceptance or publication, and the composed-picture gate remains mandatory.

Standalone probe206 (`ae1b5e7bb18544d4bff77267507a7ae9`, original session49270)
closed0, Linux group empty and private mounts released, peak697901056bytes, no
max/OOM. It compiled/linked only the menu diagnostic. Its direct popup first
paint began at487.6ms from cold construction. The first native copy mistakenly
selected libtool's launcher rather than its`.libs` executable; that deployment
failure is retained. The real animated case exposed a diagnostic observer gap:
opacity can finish without another Paint. Only that exact owned probe was
cancelled with3221225786; native resources closed and the input desktop stayed
Default. This is not product acceptance. Transaction9270b7433caa5bc67ed244cd5071962e
removed16 spent binary/cache members (129675905logicalbytes), without errors.
Sources, original linked diagnostic and failure evidence remain available for
the corrected integrated observation.

4 November idle-player correction: build204
`8daad442430e4df88f37fc51febbadb5` (original managed session9612) closed0,
group empty/private mounts released, sourcee5558c75, Qt
`235a1dcfb9ab2977f106c03b40f418e75145c32108ac66f11b37836ceb7fb0ec`.
Only Player.qml changed production behavior: absent embedded video no longer
means audio. Started audio-only tracks select artwork; empty/stopped inputs
select the black canvas and existing cone. Native idle acceptance is at
`E:/Temp/vlc-settings-implementation-20261102/idle-player-native-acceptance.json`;
the four inspected captures and their limits are in idle-player-picture-notes.
Both engines verify empty Cancel/Escape/Save, paused audio, video replacement,
Stop and EOF. Keep original checker failures and their explicit resume chain;
the successful VLC case was retained while unfinished MPV terminal checks were
resumed on the identical binary. Observe MPV EOF through mpv_video_ready's
explicit changed subscription, then assert stopped state at the later idle
capture. The older await-core state path can miss idle-active's later cache
notification, and the source helper verifies a URL rather than waiting for a
future URL. No production workaround or timeout was added. The native/raw
canonical proof retains203's unchanged owners; normal composed picture and
final delivery remain required.

4 November: the user rejected the actual Qt63bb Settings composition. Preserve
that normal package while its review process is open; do not overwrite it or
call its successful DWM readback a visual pass. The cohesive M4 repair removes
the integer window mask, presents native widget windows through Qt's existing
D3D11 RHI support, and applies backdrop/rounded native composition to Settings
and popup lifecycles. Quick menus reuse LibraryGlass and the existing decoded
swapchain blur, with slots allocated for actual visible menus rather than a
four-region cap. No new decoder, desktop capture or SDK setup is involved.
The affected acceptance must prove the selected native backend/styles, actual
composed corners/blur, nested menu behavior, empty-disclosure suppression and
volume changes with real WASAPI. The dummy-output visual launcher has no volume
or mute callbacks. Keep M4 ACTIVE and1.1.5 unpublished until those gates pass.

The199 native pass still rejects no-redirection and stale texture observations.
The owned hidden-window probe in the current M4 controls demonstrates that this
Windows host preserves NOREDIRECTIONBITMAP from CreateWindowEx: neither a later
SetWindowLongPtr nor a WM_STYLECHANGING filter can add/remove it. Create only the
affected D3D11 translucent QWidget under Qt's existing scoped
QT_QPA_DISABLE_REDIRECTION_SURFACE policy, then restore the exact prior value;
never enable it globally for ordinary or GL windows. QVLCDialog explicitly
polishes before createWinId and Qt's QMenu polishes before popup. Generic QWidget
show can create before polish, so prepare a combo's fully constructed popup
container from the combo's own Show event, before mouse/key/accessibility popup
actions. Reuse the pinned Qt6.8.3 RHI surface selection; no Qt patch/rebuild is
required.

The matching retained-object native texture probe independently reproduces an
old-window beforeSynchronizing consumer left behind on source detachment and
no new consumer after reattachment. Rebind the complete source observation on
windowChanged before overwriting its old captured window. Keep the source's
provider assertion at the point where a window exists, including safe teardown
through a windowless QQuickItem base destructor. Green proof and the complete
affected player/menu acceptance remain required; do not filter out the original
debug recovery messages or treat a source-only change as acceptance.

Build202's closed green probe and six successful affected native workflows apply
to source2a9ec390. Preserve their producer identities when only dialog teardown
and the menu checker change. The native widget visitor includes only visible
widgets; it does not emit a separate visibility field.202's checker error then
quit with the native menu open and exposed a real callback-removal crash. Keep
that dump and failed receipt. Destroy the parentless Preferences dialog from its
DialogsProvider owner while the interface still exists, before interface-close
cleanup returns and core deletes its variables. The complete affected menu
acceptance must include both nested native composition and quitting with that
menu still open; do not hide the crash by merely dismissing it in the checker.
Other successful202 workflows may be reused only with unchanged-owner source
guards.203 (`0929686267e2488684f6fb180b5140a0`, sourceaa654113)
closed0/group empty/private mounts released with no max/OOM events. Its native
main/submenu composition and normal menu workflow pass. The new open-menu quit
case initially used a clipped default viewport; preserve that failed result and
resume only that closed case with the same1280x900 reference viewport. The
resumed open-menu quit exits0, proving the callback lifetime fix. Widget/menu
manual review remains explicitly separate from the actual composed normal
picture. Normal/composed picture and final release gates remain outstanding.

The normal placement observer records native parent ancestry. Only accept an
observed DirectUIHWND when its immediate parent has the same PID, one of the
exact InputSwitch indicator classes and the exact System32/InputSwitch.dll
module. Wrong owner/class/module, missing parent, indicator-only grandparent and
Qt windows remain failures. Reuse the retained observed classifier diagnostic;
it does not establish fresh placement. Current normal SDR and P5 launches must
still pass their own inactive-desktop placement proof before actual presentation.

Original196 was deliberately stopped to remove an accidental62-consumer shared
header dependency. Keep its137/group-empty/no-OOM report and completed objects.
The popup observer now belongs wholly to Qt startup. qvlcframe.cpp/.hpp return
exactly to their qualified67fb Git blobs; only those reverted source files may
recover their last-content-commit timestamps after hash checks. Record the
source commit, hashes and timestamps. Every genuinely changed input retains
normal Make dependency handling. Resume the original interrupted player step
with closed196, the same diagnostic flags and the exact409-plugin reuse guard.

Normal193 (`eb3dc21c8da44ab8a3e529989e5cdd6e`, source67fb8cd8) successfully
compiled/linked Qt and staged the410-plugin cohort. Its failure was the later
symbol step: an already-stripped retained DLL contained its old GNU debuglink,
but the new manifest had seeded only MPV mappings. Keep the original failure.
Restore all409 byte-identical retained plugin symbol records and their matching
sidecars, verifying runtime-image/hash/CRC identities. Exact incomplete objcopy
outputs were retired using transaction7b91add7718d88b0a803436df3470816 (two
files/104005 logical bytes), preserving the runtime and compiled objects.
Packaging-only recovery195 (`25f6b217118f4e168522122b559bb73b`) closed0 in274.5s,
peak212168704 bytes, all max/OOM counters0, group empty and private mounts
released. No compiler or linker ran; original run20 remains failed, and run21
records its exact symbol-only continuation. All417 mappings now verify.

The current67fb8cd8 normal artifacts and real Windows VLC/MPV SDR/P5 checks pass
in `release-operation.json` under the existing Settings scratch. Preserve the
case-prefix preflight failure, missing former1.1.4 local source-carrier failure
and original inactive InputSwitch child-window observation. The old verified
candidate's source archive (SHA256
`2e8f66821d21ba77910740bf43d09bce71ebb5f8cf9d9e9a84adfc9789df26ad`)
supplied only unchanged dependency archives; current application Git blobs and
all121 dependency sources were independently stream-verified. A fresh passive
ancestry probe proved DirectUIHWND's same-process InputSwitch parent and passed
strict placement before actual offscreen SDR/P5 Present(S_OK)/EOF/release.
Do not repeat accepted checks or launch from the failed placement observation.

Actual composed Settings blur/corners from the isolated
`backdrop-review-rendering/review-settings.cmd` launcher was rejected. No
agent desktop controls or OS setting changes are authorized.1.1.5 remains
unpublished. After the repaired composed visual gate, close qualification, publish/independently
verify delivery and complete retained/weekly rebinding before retirement.

M4 repair192 (`038e53e23ca24049ad584a3d09dc8d2f`) assembled
`c1380668f2f89dcc6531cd3e0e9dfe3cfa784d18` through the retained Qt-only path.
Player compilation/link completed0 in1143.5s; the whole Linux group closed0 in
1173.3s with peak1715027968 bytes, no max/OOM events, `populated=false` and
released private mounts. The409 non-Qt plugins, configured SDK, core/codec/MPV
inputs and completed Qt objects were reused. Live linker evidence identified
9p disk wait; this was not a dependency rebuild or memory failure.

The affected native Settings continuation and manual widget review pass on that
exact application source. Preserve original failed focus-proxy/disclosure
checker reports and the concurrent Nuvio comparison: additional Nuvio changes
were observed after VLC exit, while installed VLC settings/language remained
unchanged. A fresh full baseline subsequently passed with no exclusions or
restored user files. Reuse the completed unchanged13-category layout evidence
under its explicit producer/delta limits; `--settings-input-repair` verifies the
affected input/save/restart/focus/Privacy paths. Normal assembly, actual composed
blur/corners, final artifacts/publication and retained/weekly delivery verification
remain pending. Do not restart SDK setup or repeat the accepted native matrix.

M4 continuation191 (`8aaae126db2d4a179ee6188682aa257b`, source `ef1ac620`)
successfully resumed190's retained objects through `--resume` and
`--after-interruption`. It closed0 with an empty Linux group, released private
mounts and no max/OOM events.190's intentional137 closure remains historical;
neither result requires SDK initialization or dependency/configuration reset.
The pinned Qt6.8.3
[style option implementation](https://raw.githubusercontent.com/qt/qtbase/v6.8.3/src/widgets/styles/qstyleoption.cpp)
reads `WA_KeyboardFocusChange` from the top-level window, but
[QApplication](https://raw.githubusercontent.com/qt/qtbase/v6.8.3/src/widgets/kernel/qapplication.cpp)
sets it on keyboard navigation and
[QWidget](https://raw.githubusercontent.com/qt/qtbase/v6.8.3/src/widgets/kernel/qwidget.cpp)
resets it when showing a widget; it does not represent the last input device.
Actual item-edge pixels on191 are mouse0, Tab14, mouse-return14. Preserve this
native failure and use category-local focus/key/mouse events for the repair.
That remaining collection completed before192 rebuilt the bounded change with
unchanged diagnostic flags. The dropdown check's original failure
captured a real `QRollEffect` while the list remained hidden; observe its actual
transition rather than inventing a delay or replaying the click. Fresh native
alpha-format/round-region checks pass, but composed blur remains unverified.

The191 Settings pass also reproduced a later Save rejecting the displayed125%
font-size label. Use one parser for preset/custom values and their displayed
units; a numeric-only QIntValidator cannot validate Automatic or percentage
labels. Original Privacy frame3062:11911 contains no disclosure. Original-size
snapshots are the native -1/-1 pair (`src/libvlc-module.c`), not0/0. These source
repairs were then verified through192's affected continuation. The collection is closed,
including150/200% layouts, missing-font preservation and history. Retain its
original font/focus failures; `--settings-input-repair` checks the affected
focus/Privacy/input/save/restart paths while reusing reviewed unchanged layouts.
The native browser covers1542 non-shortcut options;231 CONFIG_ITEM_KEY names
derived from the pinned core/Qt declarations account for the1773-key inventory.
Keep their dedicated hotkey-editor route and avoid a name-prefix guess.

Current delivery is [Modern VLC Fork 1.1.4](https://github.com/Darkaxt/vlc/releases/tag/redesign-v1.1.4),
application source `6288be3623fdeefb505f3f0c5ea5fd24bf0fcf2d`, upstream
`8a47770f6333df6b60181329db5fdaad318bdb44`. This maintenance integrates the
HEIF grid overflow fix through normal merge history. All four published assets
were independently retrieved and checked; normal VLC playback passed, and the
downloaded MPV lifecycle reuses actual SDR/P5 presentation only after identical
whole-portable-ZIP and Qt/geometry/monitor bindings. The portable ZIP is
145033709 bytes, with every shipped PE stripped and matching separate symbols.
Windows distribution remains unsigned. Local delivery and retained qualification
are `D:/VLC-Redesign/releases/1.1.4` and its `verification` directory.

The current reusable cohort is `D:/VLC-Redesign/build/windows-x64`.
`build-retention.json` binds the promoted runtime and matching compilation state
to read-only gate175 (`516f6f89459f4041934df321287ed937`), which verified source,
configuration, 410 plugins, 417 stripped PE mappings and exact runtime/codec
identities without building or initializing. Its Linux group is empty and
private mounts are released. The original normal build predecessor is174
(`0d7c81b6fc964abdae3a4e2e08dda36a`), following full-graph assembly169 and
Qt-only170; next pipeline directory `run-0004` is absent. Use the installed
WSL Coordinator launcher and `with-isolated-toolchain.py --scratch
/mnt/d/VLC-Redesign/build/windows-x64` without `--initialize`. Its flat-script
convention stages `verify-retained-build-1.1.4.py` from the build root into
`/scratch/verify-retained-build-1.1.4.py`. Retain the SDK, source/object trees,
MPV prefix, separate medialibrary/codec prefixes and synthetic/private regression
inputs under their existing continuing-consumer contracts. Use
`normal-mpv-current` only for UI deltas satisfying the exact409-plugin reuse
guard; relevant core/API/global-flag changes require `normal-mpv-full`.

Normal unattended playback explicitly uses volatile/default-off `--qt-passive`.
Qt6.8.3's no-focus flag alone does not create `WS_EX_NOACTIVATE`; the app-owned
Windows handler establishes it before native show and preserves it through
style changes. Ordinary startup retains its default focus style. Require a
fresh inactive-desktop native-style/placement proof before offscreen actual
presentation. Before allocation and again at readiness, the maintained verifier
requires WinSta0 worker startup, input and player desktops to match `Default`;
it refuses a screen-saver/locked-desktop mismatch without launching the player.
Never switch desktops or use desktop controls. Source6288 passed fresh SDR/P5
Present(S_OK), natural EOF, teardown and foreground-preservation checks. Earlier
foreground, Qt-only native-style and screen-saver picture failures remain in
local qualification with their original limits. Frozen control snapshots retain
original paths and are historical records, not installed relocatable launchers.
The weekly automation now binds this verified1.1.4 cohort and preserves its
existing schedule, target, resource limits and full M2 acceptance contract.

[M3 final reconciliation](resources/m3-1.1.4-verification.json) records completed
delivery and cleanup. Obsolete1.1.3 remote release assets and its local version
directory are retired; Git tags/history remain. Original weekly scratch and
one-shot launchers are removed. Required local HEIF fixture/frames and historical
failed receipts remain in1.1.4 qualification, outside Git and published assets.
Installed `D:/Tools/Modern VLC`, real profiles and other projects' consumers were
preserved. Host-only closure documentation does not change the tagged6288 app.

## Historical M2 reproduction

The following records describe the preceding1.1.3 delivery; use the current
cohort and qualification above for new maintenance.

M2 (COMPLETE,2 November2026) delivers1.1.3 using the retained SDK/MPV/codec
inputs, without initializing a VM. Application objects use one consistent
optimized --disable-debug/-O3/-g0/NDEBUG configuration with the QML debugger off. `ForkRelease::currentVersion` in
`modules/gui/qt/dialogs/help/fork_release.hpp` is the compiled fork release version;
the packaging helper rejects a mismatched version. Upstream VLC's own version
continues to identify its core. Windows artwork is generated from the preserved
Figma cone by `generate-app-icon.py`; the shared windres icon has an explicit
dependency through `windows-icon.mk`, and Qt consumes the matching PNG.
The native `first-run-policies-check` uses the exact production release parser,
window geometry and embedded-text extraction helpers with the pinned SDK/CRT.
Embedded text is demuxed/decoded on one cancellable worker for local media only;
video/audio are discarded, with no output device, network access or disk cache.
SRT/ASS/MP4 text, selected stream identity, image limitations and cancellation
are checked alongside actual UI/control/state behavior before release. Normal
automatic update failures remain silent; manual checks target the established
GitHub release channel and offer its release page rather than installing an
upstream binary. The complete M2 workflows and final delivery are verified below.

Current delivery is [Modern VLC Fork1.1.3](https://github.com/Darkaxt/vlc/releases/tag/redesign-v1.1.3), application commit `6cba6f96e3b341acac3886c97597b7aa74c6c169`. The portable ZIP, complete corresponding source, matching separate symbols and checksums were independently downloaded and checked. [Final delivery](resources/m2-1.1.3-verification.json) and [native acceptance](resources/m2-1.1.3-native-acceptance.json) record the complete Figma/menu/Playback/preview/icon/sizing correction and preserved first-run/subtitle/engine/update behavior. Normal MPV SDR/P5 placement and actual presentation both passed; the downloaded lifecycle reuses that presentation only after identical whole-ZIP hash and unchanged Qt/geometry/display bindings. Local delivery and qualification are `D:/VLC-Redesign/releases/1.1.3` and its `verification` directory. Windows distribution remains unsigned. Seek previews require VLC and use keyframes.

The reusable build remains `D:/VLC-Redesign/build/windows-x64`; `build-retention.json` and `scratch-share/retained-build-verification.json` bind source/runtime/configuration to read-only gate168 (`1ca995994a4f4826a2ef88f0e68f6a13`). Runtime and matching `scratch-share/compilation` were promoted together; next run0015 is absent and available. Use the installed WSL gate and the existing `with-isolated-toolchain.py --scratch /mnt/d/VLC-Redesign/build/windows-x64`, without --initialize. Its `/scratch/<script>` convention stages a flat script from the build root: current verifier is `verify-retained-build-1.1.3.py`. The original staging-guard failure167 is preserved;168 passed with an empty group and released private mounts. Original normal pipeline predecessor remains166, not the read-only ticket. Use `normal-mpv-current` only for UI deltas that satisfy its exact409-plugin reuse guard; use `normal-mpv-full` for relevant API/core/global flag changes. Retain the configured410-plugin graph, SDK, MPV objects/prefix, medialibrary/codec inputs and synthetic `m2-regression-fixtures` under their existing weekly retention contract. The Monday09:00 heartbeat preserves this binding and full repair acceptance.

The normal VLC checker uses unconditional ordered playback/decoder/demux/access teardown, STOPPED, Qt-loop completion and native exit0. The old object-destruction name message is compiled out by NDEBUG; absence of it is not a release failure. Its original failed receipt, corrected actual-run evidence and rejection controls are in local qualification. No application rebuild was needed to repair that host observer.

Obsolete release entries/assets and local1.1.1/1.1.2 version directories were retired only after verified new delivery and weekly rebinding; Git tags/history and committed historical qualification remain. The installed `D:/Tools/Modern VLC` and real profiles were preserved. The original1.0.0/S7 procedure below is historical recovery guidance, not the current build binding.

The fork reuses VLC's engine and Qt frontend. It does not replace the installed
VLC or require MPV. The current upstream application pin is
`c7834066e27cf07a2a15f1e8aab17c12df97e5d4`; the historical S7 baseline is
`392bc1d0abdb7396b6c97fef206efa1d23868e19`. Target Qt is 6.8.3; the image's host
qmake label is 6.8.0. The unchanged prebuilt archive and target headers retain
those distinct upstream identities. The image digest, complete input hashes,
source overlay and actual native runtime evidence bind each reproduction.

## Historical S7 isolated environment

Use a fresh, exactly registered `D:/Temp/vlc-s7-<run>` root for sustained I/O,
with a uniquely named disposable WSL distribution. Preserve every existing
distribution, checkout, profile and review package. Register that exact scratch
root with the installed transactional-cleanup helper before creating bulk
output. Intentional final packages belong under `D:/VLC-Redesign`; completed
recovery material may be archived to G: after verification.

Run `python -B tools/windows-baseline/prepare-stage.py --scratch <exact-root>`
to fetch and verify the immutable Debian base layer, crane 0.22.1, complete CI
image, Windows contrib archive, MinGW v12, Qt 6.8.3 and pupnp 1.14.31 sources.
It prepares files only. It does not import, compile, install or publish.

Import `downloads/debian-base.tar.gz` with `wsl --import <new-name>
<exact-root>/wsl <base-archive> --version 2`. Check the name and disk path are
absent first; preserve the exact receipt if native import reports an error.
An exited Windows client is not proof that the service has finished. Inspect
the actual registration and disk before any recovery. Importing the complete
OCI export directly failed on this host; the established recipe imports the
base and extracts the full image into `/toolchain` within that guest instead.

The minimal guest needs Python 3 and its standard library to run the installed
WSL supervisor. Provision that prerequisite within this new distribution only;
do not upgrade Ubuntu or Docker. For the recorded run, authenticated Debian
APT downloads supplied libexpat1, libpython3.13-minimal, python3.13-minimal and
python3-minimal. Configure Python's versioned package before its predependent
unversioned launcher. Verify imports of `argparse`, `json`, `os`, `pathlib`,
`re`, `select`, `sys` and `time` before submitting a build.

All heavy Linux extraction, compilation, source packaging and dependency work
uses the installed `wsl-build-gate` launcher. Retain the original request through
queue wait and actual completion. The recorded profile is a 4 GiB shared VM,
3.5 GiB workload RAM, 512 MiB workload swap, one CPU, 256 processes and one
compiler job. Inspect OOM counters and `populated=false` separately from the
build exit code. Do not replace admission with direct WSL execution or treat
an idle-looking process as completion.

Extract the verified full image to `/toolchain` under that admitted workload.
Create `/toolchain/work/home`, `/toolchain/work/tmp`, `/toolchain/work/build`
and `/toolchain/scratch`. Set `VLC_STAGE_SCRATCH` to the exact Linux mount of
the registered Windows task root, then invoke
`tools/windows-baseline/run-in-toolchain.sh` with an explicit script argv.
It binds the required system paths and scratch, runs the pinned chroot with
one-job settings, and unmounts its owned bindings after the command. The gate
supervises actual descendant exit; the image's defective Wine wait client is
not a substitute.

## Baseline and maintained fork

Within the chroot, fetch the upstream pin with sufficient history (the recorded
run used depth 100) into `/work/src`; do not use a depth-one root commit to
infer the matching contrib revision. Copy the baseline scripts and patches to
`/scratch`, with LF line endings. Keep an executable Autom4te launcher whose
body is `exec /usr/bin/autom4te --force "$@"`, and point `AUTOM4TE` to it.

Run, in order, `build.sh`, `relink-static-runtime.sh`, `prepare-runtime.sh`,
`link-fixed-qt.py` and `build-checks.sh`. These use the recorded compiler and
prebuilt contribs. An interrupted prebuilt cache must match the pinned archive
before reuse; never let a failed prebuilt silently start a full contrib build.
Inspect a failed original operation before resuming its exact build tree.

After the pristine baseline finishes, stage the maintained source delta with
`tools/windows-player/stage-player-source.py --output <exact-root>/<name>.tar`.
The helper records normalized per-file hashes and excludes unrelated untracked
files. Extract it with `tar --touch` into `/work/src`: changed headers must be
newer than the baseline's generated MOC outputs. Inspect the separately hashed
source-deletion patch, run `git apply --check`, then apply it within this disposable
source checkout. S7 removes the legacy skin's Delicious font and packages the
existing GPL FreeSans font instead. The helper rejects unreviewed deletion paths.

Select only the repaired CRT via `prepare-runtime-crt.sh`. Build QtNetwork with
`rebuild-qt-network.sh`, apply the recorded Qt owner-lifetime corrections with
`rebuild-qt-timers.sh`, and rebuild the same pupnp release with `rebuild-upnp.sh`
using `/scratch/downloads`. Regenerate the changed Automake definitions with
`/bin/sh /work/src/bootstrap`, retaining the verified `AUTOM4TE` launcher.
Then run `configure-player.py` and
`build-player.sh diagnostics` for native inspection. Keep these operations in
the same admitted, observed sequence. The full MinGW import directory must not
shadow the contrib pupnp library; use `/work/runtime-crt-only` as documented.

The development baseline disables NLS. The maintained-player configuration
explicitly enables it so the final product preserves VLC's interface-language
support. `build-player.sh` compiles/installs the upstream catalogs into the
runtime's `locale` folder, and release packaging requires that folder. Verify
actual localized native labels and gettext output with the launcher's supported
`--language el` override; do not change the user's Windows language registry
for testing. The new interface's untranslated messages retain normal English
fallback; no translation service or new translation work is implied.
Remove inherited `LC_ALL`, `LC_MESSAGES` and `LANGUAGE` from that isolated test
process: the agent shell's `LC_ALL=C.UTF-8` otherwise overrides the launcher's
LANG selection. The compiled native gettext implementation and actual catalogs
must both participate in the check.

GNU gettext's default PO dependency rule may merge and rewrite tracked
translator sources. The maintained build supplies `PO_DEPENDS_ON_POT=no`;
the normal `.po.gmo` rule still merges against the template into its temporary
build input. Before normal metadata generation, `reconcile-source-catalogs.py`
restores prior generated PO changes only after the actual template merge and
msgfmt results prove equivalent messages and runtime locale metadata. A real
translation difference stops the operation and preserves the sources. This
keeps the owned checkout's exact commit identity without disabling catalogs or
editing the canonical translations.

Build `normal` only after the integrated implementation and its required
regressions are complete. The final package must contain no diagnostic transport,
session credentials, test executables, fixtures or user profile. Package notices
and matching application/dependency source are final acceptance requirements.
The final ledger will bind the published tag, source commit, assets and hashes;
none is inferred from a successful compilation.

Fetch matching configured dependency sources with
`collect-dependency-sources.sh`. It keeps the configured Windows selection and
upstream checksum rules while disabling found-package detection only for source
fetching. Retain the selection and actual checked archives. Run
`inventory-dependency-notices.py` under the same gate, with those archives and
the pinned MinGW source as an explicit extra input. It extracts named notices
without changing the full source archives; this inventory does not replace
review of their linking/distribution licenses. Include the corresponding
application source, dependency archives and maintained patches/build scripts
with the final release. The private Delicious validation ZIP is not a dependency
source input and must not enter that archive. After the initial inventory,
run `complete-dependency-notices.py` against those exact source/notice folders.
It retains the four reviewed license-bearing headers, and explicitly classifies
fxc2/WiX host-tool bundles separately from corresponding library sources.
These compiler/installer bundles are absent from the portable application;
their pinned retrieval/build rules remain available without republishing them.

After the source commit is verified, `package-source-release.py` creates the
versioned corresponding-source archive. Pass its exact commit/version,
source/notice folders, D: deliverable destination and a fresh registered scratch
child explicitly. It streams `git archive` of the current tree, with original
library archives, maintained patches, build/relink instructions and source hashes.
It includes no Git history, removed font, private download, profile or VM. The
combined Qt 6 application is conveyed under GPLv3 with its full text and original
component notices; source files retain their existing applicable license terms.
Independently verify the resulting source archive and the published asset.

After pre-release verification and the source-bound normal build,
`tools/windows-player/package-release.py` creates a fresh versioned portable
folder and ZIP below `D:/VLC-Redesign`. Pass its exact runtime, dependency-notice
folder, source commit, version and destination explicitly. It checks native
version/changeset, rejects diagnostic transport markers, copies the supported
runtime files and full notices, adds an empty portable profile and records
shipped file hashes. Test the resulting package after independent extraction;
the helper does not publish it or establish final delivery acceptance.

Before the final normal build, bind the isolated build checkout's Git identity
to the verified fork commit as well as its file contents. Fetch that exact commit
from the existing fork and reconcile every staged source file against it; preserve
working files while updating the temporary checkout's index/HEAD. Regenerate the
revision metadata through the maintained build and check the packaged libVLC
changeset independently. An overlay on an unchanged upstream Git HEAD is adequate
for diagnosis, but must not mislabel the final modified package as that upstream
revision.

## Configuration preservation and recovery

Native verification uses a copied runtime with an empty `portable` directory
beside its exact executable. `VLC_USERDATA_PATH` alone is insufficient evidence
of isolation on Windows. Snapshot installed configuration/database identities
with `check-installed-profile.py`, keep those private, and compare them after
testing. Synthetic fixtures are generated by `generate-s7-fixtures.py`; no user
media is required. App-owned Qt diagnostics use an inactive desktop and never
send OS input or activate/switch desktops.

For a synthetic portable Qt profile, Windows QSettings uses
`portable/vlc/vlc-qt-interface.ini`; native `vlcrc` and the optional font cache
remain directly beneath `portable`. Theme/DPI acceptance controls the test
process with `QT_ENABLE_HIGHDPI_SCALING=0`, `QT_FONT_DPI=96` and the explicit
`QT_SCALE_FACTOR`, after removing inherited screen-scale overrides. Verify
actual theme, window DPR and 40/54 logical-pixel player chrome in the snapshot;
requested environment values alone do not prove those dimensions. These
controls belong to validation only and do not alter product/system DPI settings.

The upstream Windows pipe helper used only a per-process counter in the shared
named-pipe namespace. Concurrent VLC/preparser processes collided and could lose
the initial playlist or fail interface startup. The maintained helper includes
the PID and full 64-bit counter. Run `check-native-pipe.py --runtime <runtime>
--output <fresh-result.json>` against the actual candidate; its first worker
holds both pipe pairs until the second worker has created its own, with explicit
release and process completion. The historical `--expect-collision` check is for
the unmodified helper only. Do not hide this defect with retries, serial-only
application behavior, or by disabling native preparsing.

The fork retains upstream setting identities. The versioned redesign stores
reject malformed, oversized and newer-version data without overwriting it.
Cancel leaves accepted state unchanged. Recovery must preserve the original
profile before a user-directed repair; do not delete the profile as a startup
workaround. Use a separate empty portable instance to distinguish a profile
problem from a package problem. Never copy a test profile over the installed
one. The stage evidence documents defaults, precedence, reset and write-failure
behavior of each added store.

The first-run wizard's optional Delicious font is downloaded directly from its
publisher after choosing **Download and finish**. **Use FreeSans** finishes setup
without a download; **Cancel download** cancels the current request. The package
contains FreeSans as its offline fallback and retains Inter for the redesigned
interface. A validated cached font is reused on reopening/restart. The cache is
`redesign/fonts/Delicious_R_2021.otf` below VLC's active configuration directory;
with a portable runtime, that is below its `portable` folder. No OS font is
installed. To reset this optional asset, move that exact user-downloaded file out
of the profile while VLC is closed; the next launch uses the bundled fallback.
Preserve an unreadable/unrecognized file for inspection rather than overwriting
or deleting the whole profile. The wizard can be reopened to download it again
after the exact cache conflict is resolved. Download/archive/font bytes are
temporary validation inputs or user-owned profile data, never release assets.

## Upstream synchronization

Keep the upstream pin and fork revision separate. Fetch a candidate upstream
revision without resetting the working tree; review its Qt/player/configuration,
WASAPI, contrib and ABI changes against this fork's capability inventory and
patches. Reconcile each retained patch against its actual upstream replacement
before dropping it. A newer version number is not proof that a correction is
present. Rebuild with a compatible pinned toolchain/contrib pair, repeat affected
native playback/state/presentation gates, then perform the project's complete
final delivery verification. Preserve dirty work and never force-push to conceal
a conflict. The verified 1.0.0 procedure above remains the S7 baseline; S8 uses
the additional assembly contract below.

After all consumers exit and required evidence/deliverables are preserved, stop
only the owned temporary distribution, review/inspect the exact cleanup manifest,
issue its separate ticket and apply it. Retire only the resulting empty WSL
registration. Verify unrelated bindings and the final installed-profile comparison.

## M1 optimized release packaging

The1.1.1 upstream update pins VLC master at
`c7834066e27cf07a2a15f1e8aab17c12df97e5d4`. Use the existing retained toolchain
and `bind-upstream-source.py` with a frozen Git bundle, patch digest, exact old/new
commits and the original closed supervisor report. It applies exact committed
blobs/modes, including reviewed upstream source deletions, and preserves unchanged
source mtimes and all build objects. Never reuse the pre-upstream plugin cohort:
the public subtitle structure and core exports changed.

Use `diagnostics-mpv-full`, then `normal-mpv-full` in the maintained pipeline.
`build-upstream-medialibrary.py` verifies upstream's SHA-512 and builds0.14.1
statically into `/work/upstream-medialibrary-0.14.1/prefix`, using the existing CRT
and SQLite3.53.4. Configure explicitly binds its flags before the old0.13 SDK
copy, regenerates Autotools/manifests, and rejects a disabled library plugin.
The full mode builds the entire configured module graph and stages only those
current outputs into a fresh runtime; `VLC-PLUGIN-BUILDINFO.json` binds the plugin
set to the merged application and upstream commits. Existing compatible SDK and
MPV dependencies remain pinned, with the medialibrary override recorded separately
in the combined corresponding-source inventory. No global SDK replacement occurs.
The codec override similarly builds MPG1231.33.7, ZVBI0.2.46, MAD0.16.5 and
AOM3.15.2 into `/work/upstream-codecs-1.1.1/prefix`, using the upstream SHA-512
rules and exact patches. Configuration binds their actual archive paths before
the old SDK. `upstream-codec-links.mk` runs with direct `all-am` after the
separate Qt build so recursive Automake does not discard its extra makefile.
Real linker maps bind all four updated archives and reject old SDK members.
The same fragment retains the baseline SRT input/output, x265 and GME static
GCC exception-runtime correction; explicit `-lgcc_s` must not reintroduce a
missing `libgcc_s_seh-1.dll`. Preserve all configured security linker flags.
The source inventory contains121 corresponding archives plus3 host-only inputs;
the AOM PATENTS text is included in the binary notice materials.

After the complete diagnostic assembly and native acceptance, the normal
variant resumes from `player` with the existing configuration, objects and
MPV identity. Do not rerun configure merely to change diagnostic guards:
CONFIGURE_LINE is in global config.h and a changed dependency path invalidates
the frontend even when the feature probes are unchanged. Cache omission uses
`VLC_PLAYER_COMPILE_CACHE=0` with an explicit reason; the complete target graph
still runs and validates every dependency.

The selected upstream native regressions use `build-native-tests.py` with
`native-tests.mk`, `--platform-header native-test-platform.h` and
`--qt-platform-source native-test-qt-platform.cpp` from this tools directory.
Pass the exact Windows `--windows-layout` later used by `run-native-tests.py`.
The input signature forces only the selected test objects when those macros,
configured makefiles or test recipes change, including on coarse timestamps.
The two C units link the existing VLC libcompat. Windows requires
VLC_TEST_TIMEOUT=0; a nonzero POSIX alarm request fails explicitly. The CSD
model unit imports the existing static SDK offscreen platform. These adapters
change no production target or upstream assertion. Build the separate
`native-test-builtin-plugin.c` with `build-native-builtin-plugin.py` in the
same admitted toolchain. Windows core omits ELF weak-builtin discovery; this
test-only DLL registers the existing exported EXE table and preserves the
upstream mocks and their state. Pass its receipt through
`--builtin-plugin-receipt`, and the pinned compiler's x64 POSIX `libssp-0.dll`
through `--compiler-runtime`, to `run-native-tests.py`. Both are hash checked
and staged only in the isolated test layout. Run the actual three
recorded executables on owned inactive desktops, checking real exit results;
optional Qt Quick Test and the entire POSIX-oriented upstream suite are not
claimed by these selected regressions.

Native library migration acceptance expects the pinned medialibrary0.14.1
schema38-to39 transition while preserving every other stored setting,
media/file identity and history value. Codec acceptance parses VLC's native
YUV format and per-frame headers before comparing decoded AV1 frame payloads.
Offscreen pixel checks explicitly disable VLC's auto-raise option, retaining
the foreground-ownership rejection and actual WGC image comparison.

The 1.1.1 private-desktop placement verifier originally rejected a second Windows
input-indicator class, `UAC_InputIndicatorOverlayWnd`. Its original failed receipt
is preserved. Independent review established that both it and `UAC Input Indicator`
came from the same Microsoft-signed System32/InputSwitch.dll; the native run
exited 0, all visible Qt windows stayed outside every monitor, no owner became
foreground and the input desktop was unchanged. This is an explicit review of
that closed placement run, not a rewritten passing verifier receipt. Subsequent
normal MPV SDR/P5 and downloaded P5 actual-picture checks passed the unchanged
strict all-visible-owned-windows-offscreen guard. Frozen local control snapshots
retain original historical paths; use maintained project tools and the current
retained binding for new execution.

Version1.1.1 corrects the1.1.0 symbol bloat without removing plugins or engines.
Use `normal-mpv-full` with the exact `--release-symbols` directory for the
merged release. Its MPV prelude reuses the existing verified raw prefix;
the upstream-required medialibrary/codec overrides are the separate inputs
described above.
`stage-built-mpv-runtime.py` calls `release_symbols.py --mpv-only` before writing
payload hashes, so the generated Qt header binds the actual stripped DLLs.
Do not strip or binary-patch MPV after compiling that binding.

The normal player driver finishes all required outputs, then runs the same
symbol splitter over every EXE/DLL in the completed cohort. Original build
outputs remain untouched. GNU objcopy keeps separate matching debug files;
strip-all removes COFF symbols and debug sections, and GNU debuglink
records each sidecar's basename/CRC. The helper requires byte-identical runtime
sections and stable entry point, image base, imports/exports/exception/TLS/IAT/
relocation directories across stripping. Only debug sections/link metadata,
COFF symbols/strings and file-layout bookkeeping may change.
The first strip-unneeded diagnostic retained 658 import-related COFF entries in
MPV and correctly failed the zero-symbol guard. The corrected policy uses
[GNU strip-all](https://sourceware.org/binutils/docs/binutils/strip.html), while
the unchanged runtime-section/directory checks remain mandatory.
Full debug output remains separate. A source-built
full debug file is used when its runtime image matches the staged binary.

`RELEASE-SYMBOLS.json` covers every shipped PE and records original/final byte
hashes, runtime-image hashes, debuglink and separate-symbol hashes. The portable
packager rejects missing coverage, retained debug sections/symbols, pending
outputs and mismatched runtime identities. `package-release-symbols.py` verifies
every sidecar and creates a separate optional symbols ZIP; the portable ZIP
contains no sidecars. The symbol ZIP can be merged into the matching portable
tree's `.debug` directories for debugging. Include `--release-symbols` when
packaging corresponding source so transformation provenance accompanies it.

Normal acceptance uses `verify-normal-presentation.py` and
`observe-normal-window.py`: explicit package/fixture/scratch/Qt hash, synthetic
geometry source and placement-proof paths are required. First run `--mode private`
for placement only, then `--mode offscreen` for actual MPV SDR/DV picture/EOF/
teardown. The private proof distinguishes only the identified OS input indicator
from Qt windows; offscreen acceptance checks every visible owned window. Reuse
unchanged S8 behavior/color evidence only with matching source and unchanged
runtime-image fingerprints. Publish once after the complete release passes,
then independently retrieve binary/source/symbol/checksum assets and repeat the
affected downloaded-package checks. Preserve1.1.0 and protected profiles.

## S8 source-bound MPV assembly and verified retained binding

S8 is delivered and verified as 1.1.0. Current reusable inputs are
`D:/VLC-Redesign/build/windows-x64`: `toolchain/work/src`, the configured
`toolchain/work/build/win64`, MPV dependency/object/prefix trees, pinned archives,
`scratch-share/runtime`, merged notices and `scratch-share/compilation/state.json`.
`build-retention.json` records the continuing weekly consumer, original identities,
source commit and verified new binding. Gate 126
`588990fbfc4c47b2a28de2bb65576500` exited 0 with an empty group, no OOM and released
mounts; the clean source/configuration/runtime check performed no rebuild or initialization.

Use the installed WSL gate and canonical `with-isolated-toolchain.py` with
`--scratch /mnt/d/VLC-Redesign/build/windows-x64`; never pass `--initialize` there.
Keep chroot `/work` and `/scratch` bindings. Stage a verified required source delta,
preserve identical file mtimes and resume the recorded pipeline step. Reconfigure
only when its relevant inputs change. Flat `/scratch/FILE` command inputs must
exist at the retained root for the wrapper's checked copy. The retained
`apply-player-source.py`/`bind-verified-source.py` are frozen reviewed transfer controls;
inspect their current contract before use. Do not discard object trees or redo cold SDK setup.

Historical commands below show the original assembly at `D:/Temp/vlc-s8-20261029`.
That exact root and its E: finalization controller are now absent. They are
provenance, not instructions to recreate scratch or initialize another toolchain.
Full local qualification and exact original control snapshots are at
`D:/VLC-Redesign/releases/1.1.0/verification`. Frozen snapshots keep original paths
and are not installed relocatable launchers. Three bounded hash-bound local DV
clips live under the retained `dv-keyframes`; never put clips/frames in Git or releases.

Normal MPV acceptance needs actual `Present(S_OK)` evidence. An inactive desktop
can reach EOF without a successful presentation, so that check alone is insufficient.
The passing normal procedure first proves the public synthetic saved Qt geometry
on an owned inactive desktop, bound to the exact Qt DLL, saved screen/DPR and
monitor rectangles. It then starts that normal executable fully offscreen with
`SW_SHOWNOACTIVATE`, `--qt-auto-raise=0`, tray/notification/network prompts disabled
and an empty synthetic portable profile. A passive owned-PID WinEvent observer is
ready before launch. Require actual MPV picture presentation, EOF/teardown, every
visible owned window offscreen, no foreground ownership and unchanged input desktop.
No OS input, window-control/activation call or desktop switch is permitted.
Re-prove Qt/geometry/display bindings after any relevant change; do not copy an
old placement proof onto a new binary or weaken the actual-picture criterion.
The corresponding source/delivery archives and empty original portable package
were independently checked; principal binaries follow the existing unsigned policy.


Use the same pinned toolchain image, CRT and contrib layout. Preserve the 1.0.0
portable runtime and source archive as baseline inputs; copy only the empty-profile
runtime into task-owned scratch. Existing installed VLC and its profile are not
build destinations. `prepare-mpv-review.py` records the initial reference input;
the shipped S8 engine must instead come from the maintained source build.

`modules/gui/qt/player/mpv/source.json` records the exact core and shader source
commits/archive hashes, the unchanged C API headers and the native WASAPI-session
patch. Fetch its core/shader archive groups with `prepare-mpv-sources.py`; preserve
existing completed inputs rather than fetching them again. The old nightly DLL
is a diagnostic reference, not corresponding-source proof for the new runtime.

After all S8 source/package integration is assembled, freeze one current overlay
with `stage-player-source.py --base-ref HEAD`. Apply that archive to the exact
matching disposable source checkout. Run `assemble-s8.sh` through the installed
WSL gate and `with-isolated-toolchain.py`, with one compiler job and the prescribed
VM/workload limits. This single workflow resumes the existing Qt SDK dependency
graph, builds the private MPV/FFmpeg/libplacebo/shader dependencies, stages both
runtime DLLs, merges their notices, configures VLC and builds the complete
diagnostic player. No playback acceptance runs during assembly. A failed command
retains its build tree: diagnose the actual failure and resume affected targets;
do not rerun first-time SDK initialization or overwrite partial source trees.

For an existing build, use `apply-player-source.py` with the frozen overlay,
manifest and exact closed predecessor report. The manifest's resolved base commit
must match the build checkout; the original workflow must be empty and its
pipeline stopped. The helper validates the entire archive/member hashes before
writing, rejects source deletions/reparse escapes/Git metadata, and changes only
different bytes. Those files get fresh mtimes; identical files retain theirs.
Blind tar extraction's archive mtimes are unsuitable for incremental Make.
The compact application receipt records changed and preserved members.

`assemble-s8.sh SOURCE BUILD RUNTIME resume` continues
`compilation-pipeline.py` at its recorded failed step after the cause is repaired.
The initial `build` selection starts at the SDK network step; explicit
`shaders`, `spirv-cross`, `placebo`, `ffmpeg`, `mpv` and `player` selections are
available when the earliest affected step is known. Preserve the original gate
session until its actual exit and empty-group result before launching a repair.
Never replay a still-running or uncertain operation. The pipeline itself does
not blindly retry: its owner diagnoses the failed command and resumes the same
state. A compiler failure does not pause the authorized task.

The Qt object phase uses Make keep-going to collect independent frontend
integration compiler failures in one assembly. Any failed object still fails the
step; the cache is released and the final Qt link does not run. Diagnose the
collected failures together after group-empty completion, then resume with the
affected sources changed. This is compiler diagnostics, not product acceptance.
`assemble-s8.sh SOURCE BUILD RUNTIME normal` runs the final `normal-mpv` player
through the same pipeline. Each new run preserves its own `attempt.json`, mode,
`VLC_PLAYER_COMPILE_CACHE` choice/reason,
source HEAD, complete recipe identities and step results alongside the full logs.

Durable state is `/scratch/compilation/state.json`, with exact commands, source
recipe hashes, step status and actual CPU/wall/exit results. Full logs live under
`/scratch/compilation/run-NNNN/`; `/scratch` is the task's `scratch-share` binding
on the host. Successful prerequisite objects and libraries stay in the existing
build tree. This is assembly evidence, not feature acceptance.

After a diagnosed runtime dependency repair, pass
`--replace-mpv-buildinfo-sha256 SHA256` to the pipeline with the exact previous
task-owned `MPV-BUILDINFO.json` identity. The runtime step verifies prior and new
payload identities, copies through checked pending files and atomically publishes
the new manifest before generating the plugin's compiled hashes. Interrupted
old/new payload mixtures can resume under that same identity; unknown changed
or partial files require inspection. An unchanged completed notice inventory is
reused only after checking its pinned source archives, SDK binding, compiler and
every retained notice. No refetching or source extraction is needed for unchanged
inputs. Resume at the earliest actually affected dependency, preserving objects.

The software-frame FFmpeg/libplacebo filter creates a Vulkan device internally;
build libplacebo with `vk-proc-addr=enabled`. Its exact SDK Vulkan import archive
is selected through a task-local pkg-config entry, leaving the original SDK
unchanged. Windows must provide its graphics-driver Vulkan loader in System32;
the application loads only its two hashed MPV payloads plus system dependencies.
Do not accept an audio-only or blank reference: decoded/output video parameters
and absence of native fatal/error messages are required before comparing pixels.

The Windows-mounted toolchain has measured header/metadata I/O overhead. During
dependency compilation, `cache-toolchain.py` binds byte-verified copies of the
unchanged MinGW compiler and common headers at their original paths inside the
owned mount namespace. Its tmpfs ceiling is 512 MiB and remains charged to the
existing workload cgroup; no VM budget or global setting changes. The recorded
299,768,706-byte cache reduced the same header-preprocessing probe from 7.15 s
to 1.54 s wall time, which is not a whole-build speed claim. The pipeline releases
these mounts and memory before configuring/linking VLC. Namespace exit also
retires them on failure; compiled objects remain reusable on D:.
For a resume at MPV, the cache also covers immutable SDK headers, MPV source and
the installed dependency API directories, totaling 386,838,288 bytes in the
recorded run. The prefix's whole include directory stays writable so MPV's own
new headers persist; only its already installed dependency subdirectories are
cached. All cache mounts are read-only and retain original paths and bytes.

For the player step, `cache-toolchain.py create --qt-build` caches only immutable
Windows/C++/SDK headers and frozen frontend sources, with a separate 256 MiB
ceiling inside the same workload. `qt-objects.mk` extends the generated Automake
prerequisites to compile its full object/resource graph. The driver releases
that cache before the normal Qt link; the generated build directory stays writable.
Qt diagnostic/runtime preprocessor flags have a persisted signature: changing
them invalidates the guarded source units once, while a same-flags repair keeps
completed objects. A first cold build generates headers through their actual
`src` targets and prepares the complete Qt `BUILT_SOURCES` graph.

After an externally stopped operation, inspect its original managed result before
resuming. `compilation-pipeline.py --resume --after-interruption REPORT` accepts
only an exact matching predecessor cgroup/run, a started command, a nonzero result
and `populated=false`. It records that report's hash and interruption separately
from a compiler failure. Inspect the final started object: an absent object is
rebuilt by Make; uncertain generated output requires exact reviewed cleanup.
This does not stop WSL, control desktop windows or replay an uncertain success.

The weekly consumer is `vlc-weekly-upstream-sync-and-release`. After native
acceptance and commit binding, `retain-build-inputs.py --source-commit COMMIT
--closed-report REPORT` promotes only the toolchain, pinned archives, assembled
runtime/notices, compilation state and three bounded private DV clips from the S8 task to
`D:/VLC-Redesign/build/windows-x64`. Pass every relevant successful closed report,
including the pipeline's latest report; confirm the gate is idle and all native
runtime consumers have exited before invocation. The build source must already
be clean and bound to that exact verified commit. Each same-volume move retains
its recorded directory identity. Its journal permits inspection/resumption of a
partially completed move without overwriting a pre-existing destination.

The launcher accepts this one retained path only with the matching toolchain
marker and named consumer receipt; initialization is prohibited there. All chroot
`/work` and `/scratch` paths stay the same. Verify a gated launch and read-only
configured-input check at the new binding, inspect its real completion, then
record that verification and reconcile/discard superseded cleanup inventories.
The three hash-bound P5/P8.1/P8.4 clips stay local for that weekly acceptance
consumer and must never enter Git or a source/binary release. Other test
profiles, full media, captures and spent controls remain temporary and require
transactional cleanup. Retention lasts only while the
pinned cohort serves the weekly/build consumer; superseded generated inputs need
explicit consumer checks and reviewed retirement. This is a scoped build-input
binding change, not a repository or WSL virtual-disk migration.

`stage-built-mpv-runtime.py` writes `MPV-BUILDINFO.json` from the actual payloads,
source archives, maintained recipe/patch and matching installed public headers.
The player build generates `mpv_runtime_identity.hpp` from those payload hashes
and compiles the hashes into Qt. Loading requires the complete matching app-local
DLL set; the writable JSON is provenance, not runtime authorization. Native
mmdevice remains the Windows volume/mute persistence owner. The patched MPV
runtime joins its existing session/endpoint and supplies only above-unity gain.

Before the MPV build, run `prepare-mpv-sources.py --host-inputs --scratch
D:/Temp/vlc-s8-20261029` to fetch the hash-pinned Jinja2 3.1.6 source archive.
The libplacebo phase exposes only its Python package through a task-local
`PYTHONPATH`, using MarkupSafe 2.1.5 already in the pinned image. No global pip
installation or Ubuntu change is needed. This host-only shader template tool is
recorded in the build manifest and notice inventory; it is not a linked Windows
library or a copied product payload.

MPV's enabled subtitle-encoding detector also requires uchardet, which the
retained SDK does not contain. Fetch the official 0.0.8 archive with
`prepare-mpv-sources.py --text-inputs --scratch D:/Temp/vlc-s8-20261029`;
`source.json` pins the publisher's SHA-256. The MPV phase builds only its static
library in the private prefix and retains its original source/notices. There are
ten additional linked-source archives, alongside the 106 unchanged SDK archives.
Explicit compiler `-B` library prefixes expose these SDK libraries to Meson's
static system-library detector, with the selected CRT first. This cross-compiler
ignores `LIBRARY_PATH`; linker-only `-L` arguments do not supply that discovery.
Treat the retained SDK's broad include directory as an `-isystem` fallback.
Meson may order its dependency flags before the new prefix; GCC then ignores a
duplicate SDK `-I` and consistently selects the source-built libplacebo/FFmpeg
APIs first. Reconfigure existing MPV built-in compiler options without wiping
its build tree. Compiler-flag changes invalidate affected MPV objects, while
completed dependency archives remain reusable.

Run the coordinated S8 acceptance matrix only after complete integration. It
covers both engines, live handovers, the shared queue/history/tracks/subtitles,
native audio-session persistence, failure paths, Figma/theme/scaling and actual
P5/P8.1/P8.4/SDR/HDR10 pixels. Color-reference commands must bind to the same newly
built DLL hash as the integrated player. The selected renderer outputs BT.709/sRGB
SDR; no native Dolby Vision signaling or full Profile 7 FEL result is implied.
Use the integrated helper's `--backend-controls` with `--switch-engines` for
real keyboard rate/delay changes and preservation across both handovers. The
prior-profile helper reads its startup engine from the synthetic saved `vlcrc`;
`--external-subtitle FILE` additionally checks the existing fingerprint-bound
association on both launches. `check-installed-profile.py --include-nuvio`
captures VLC settings/language plus Nuvio persistent settings and WebView stores.
Keep these snapshots private; no installed profile is copied into a test runtime.
For `verify-mpv-colors.py`, generate first-frame references with `--time 0`.
That pixel-only case uses the existing capture-only offscreen mode because WGC
rejects inactive-desktop windows. It checks actual native window bounds outside
the monitors and foreground/input-desktop preservation. Interactive seeking and
handover remain separate inactive-desktop acceptance; the capture mode accepts
no such input actions. A blank/non-distinguishing frame cannot satisfy the
positive/negative pixel comparison.

After acceptance, build `normal-mpv` from the same verified source and runtime;
retain the common MPV binding and remove diagnostic hooks. Commit verified scope
and relink the recorded source revision as in S7. Use `package-release.py
--include-mpv` with the merged notice directory. The packager requires both DLLs,
their compiled identities and matching source/notice provenance. For
`package-source-release.py`, supply the new archive directory with `--sources`,
the merged `--notices` and `--mpv-buildinfo`. The optional `--baseline-source` and
its expected `--baseline-source-sha256` reuse the unchanged SDK source archives
directly from the verified S7 source package; each copied archive is separately
hash-checked with bounded memory. The output includes all required library source,
the application, maintained patches/build scripts and the MPV build manifest.

Publish only the final verified S8 release through the established channel.
Independently retrieve its binary/source packages, inspect their identities and
normal native behavior, compare protected installed state, and retire only spent
task artifacts through transactional cleanup. Build completion is not stage
acceptance or final delivery.
## November2 weekly maintenance1.1.4 qualification

Application source6288be3623fdeefb505f3f0c5ea5fd24bf0fcf2d contains upstream
8a47770f6333df6b60181329db5fdaad318bdb44 HEIF checked grid-offset arithmetic and
an explicit volatile default-off `--qt-passive` option. Normal validation uses
that option with auto-raise disabled. Qt6.8.3 does not map its no-focus flag to
WS_EX_NOACTIVATE; the Windows handler establishes the style before show and
preserves it during native restyling. Ordinary startup retains its default style.

Before offscreen validation, the maintained verify-normal-presentation.py checks
that WinSta0's worker-startup desktop equals the input desktop, repeats that check
at launch readiness, and requires a fresh inactive-desktop placement/native-style
proof bound to the exact Qt binary, saved geometry and monitor layout. A screen
saver can leave the worker on Default while input belongs to Screen-saver; such
a run cannot establish actual presentation. Dismissal is performed by the user,
never desktop controls. Continuation93701 verified actual SDR/P5 presentation,
EOF/release and foreground preservation on Default using the unchanged6288 build.
Original failed receipts remain separate from acceptance evidence. This entry
records qualification; publication/retained-binding results are recorded below
only after their actual gates pass.

## M4 settings qualification and backdrop evidence

The thirteen-category settings matrix passed on70dd7b60c2ef17868093f48f1e938c29e9d09ceb
at100/150/200% in dark/light, normal/narrow layouts, including staged edits,
rollback/retry, native history and saved-option restart checks. Reuse that
evidence only with its original source/binary hashes and an explicit reviewed
production-delta binding. The subsequent b6492edd14852f2b2e85422ec27feed65ad5e9b7
correction moves the optional Recent media-library model into a separately
loaded QML file, because its type is not registered with --no-media-library.
Repeat the affected main-menu, handover and prior-profile workflows, including
the final normal player both with and without the media library. The S7
handover/profile helpers require the existing generated120-second multi-track
fixture; the short control.mkv is not an equivalent fixture.

Widget captures establish paint/layout, rounded clipping and surface alpha;
they omit the DWM-composed backdrop. Original Figma frame999:5047 specifies
#0e0e0e at95% with background blur50. Successful Acrylic request/readback and
alpha242 therefore cannot establish visible blur over player content. Require
an actual composed screenshot bound to the normal release's Qt plugin hash,
and retain the original screenshot unmodified. Never publish private DV clips
or their frames as comparison artwork. README credits can ship without optional
screenshots; compositor evidence remains a separate release acceptance gate.

Inactive-desktop native verifiers may record an unrelated external transition
of the input desktop without treating it as application activation. They must
still prove their owned desktop never became the input desktop and preserve
the actual before/after names and process-exit evidence. Actual offscreen
presentation retains its stricter continuous Default/input-desktop and fresh
placement-proof requirements. This verifier distinction does not authorize
desktop controls, forced focus, OS transparency changes or repeated unlock prompts.

Continuation188 verified the actual manual-setup route through General,
Advanced Options, VLC commands, Welcome / Appearance Setup. Opening it cancels
the settings draft before requesting the existing onboarding owner. Idle engine
selection remains in the native Playback submenu of that same themed route.
The complete affected native pass on d214 includes both engines' saved-profile
restarts, MPV history/privacy/volume and paused/playing/idle handovers. Playing
position bounds use observed application-clock elapsed time and playback rate;
paused handovers still require preserved position within decoder precision.
Settings intentionally hides Save/Cancel until an edit is staged. The integrated
verifier stages the captured native `value-interact` checkbox before testing
Cancel; an untouched dialog closes through `preferencesClose`. Original failed
verifier receipts are preserved, not relabeled as passed. These native and raw
paint checks still do not establish the DWM-composed Settings backdrop.

For normal presentation, saved geometry must match the verifier's actual DPI
policy. The native VLC probe uses the current system DPR (1.5 on3 November),
while verify-normal-presentation.py explicitly disables high-DPI scaling and
uses DPR1.0. Do not feed the former's geometry directly into the latter.
Use the fresh saved geometry from that same package's completed normal
private-playback launch under the exact presentation environment, then obtain
new private placement proofs before any input-desktop launch. Preserve failed
placement receipts; never reinterpret a centered inactive window as clearance.
The normal1.1.5 SDR/P5 acceptance uses `normal-geometry-dpi100.ini` and its
recorded source/hash. The original DPR1.5 file remains diagnosis evidence.
Actual normal SDR/P5 presentation passed; this does not replace the separate
composed Settings screenshot requirement above.

The subsequent user screenshots reject the189 Settings presentation. Raw alpha
in a QWidget render did not prove the native window had an alpha format.
QVLCDialog binds a transient parent by creating its handle; Settings previously
set WA_TranslucentBackground after that call. Qt6.8.3's
QWidgetPrivate::updateIsTranslucent deliberately cannot change an already-created
native surface. Configure frameless/alpha attributes before parent binding and
require the actual native format's alphaBufferSize to be at least8. Retain the
composed-image gate; alpha format/request success alone is still insufficient.

Reference numeric/track/font fields must be checked by actual editor type,
alignment and presence of steppers, not just width. Inspect open combo popups
with their own native view/delegate palette at100/150/200% in both themes.
The original Controls fields are36px high,6px corner radius, left-aligned plain
inputs; action captions use Inter Semi Bold. Default audio/subtitle tracks are
typed indices, with native -1/0 semantics preserved. Reference Advanced Options
stays neutral while expanded and has20px content separation. Additional native
settings and the startup engine remain accessible through Search or General,
Advanced Options, VLC commands, All VLC settings; they are not default rows in
the prototype category's expanded surface. Source corrections remain unverified
until a new affected native/composed acceptance passes.
