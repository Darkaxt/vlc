# VLC redesign stages and reconciliation

**Execution ACTIVE: the user explicitly revoked pausing and requested a compilation pipeline (30 October).** S8 is the sole ACTIVE stage.
The resumable pipeline records commands, source identities, full logs, real results
and elapsed/CPU measurements; its owner repairs actual failures and continues
without restarting successful prerequisites.
The integrated diagnostic player passes the source-bound native workflows and
same-DLL DV/color comparisons recorded below. The final normal build, release,
delivery verification and reusable-input retention remain. Prior build/native
process groups are released.
Scratch is the registered `D:/Temp/vlc-s8-20261029` sustained-I/O exception.
R67-R70 product acceptance and final delivery remain pending; no playback
acceptance runs during assembly. [Current operation, evidence and next action](#s8-execution-and-acceptance-contract).
Preserve unrelated distributions/settings and never replay consumed overlay entries.

**Current work: S8 is ACTIVE**, authorized by the user's 29 October "continue" and subsequent source clarification. R67-R70 in the authoritative specification define the integrated MPV/Dolby Vision outcome. S7 remains COMPLETE and its published 1.0.0 delivery is preserved. S9 remains NOT STARTED. [S8 contract and current reconciliation](#s8-execution-and-acceptance-contract).

The [specification](SPECIFICATION.md) governs every stage. **S7 is COMPLETE**: product acceptance, final release delivery, preservation and exact scratch cleanup are verified. [Modern VLC Fork 1.0.0](https://github.com/Darkaxt/vlc/releases/tag/redesign-v1.0.0) is a normal published release bound to application commit `dd61caec26f8cc65f15d78369d09fb254196c810`. Independently downloaded binary/source/checksum assets match their recorded hashes; the downloaded normal package passes native playback, Greek localization, legacy-font paths and bitmap-subtitle checks. Installed VLC configuration/databases and Windows language state are unchanged. The temporary S7 build VM, D: scratch and E: cleanup controller are absent after inspected ticket application. S0, D1 and S1-S6 remain COMPLETE. S8 is now ACTIVE; S9 remains NOT STARTED. [Delivery evidence](resources/s7/final-release.json), [requirement reconciliation](resources/s7/specification-reconciliation.json).

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
| S8 MPV and Dolby Vision integration | ACTIVE | R67-R70; Windows x64, NuvioDV reference, optional engine and real DV rendering | Diagnostic native selection/handover, player/history/library/subtitle workflows, theme/scaling and composed P5/P8.1/P8.4/SDR/HDR10 color checks pass. Normal build/package, final release/readback, final preservation, retained build binding and cleanup remain. |
| Proposed S9 Profiling and selective Rust migration | NOT STARTED | R66; after S8 and the completed existing plan | Release-bound resource baseline, justified bounded component selection, explicit FFI/preservation contract, one integrated migration and equivalent before/after evidence; retain only demonstrated benefits, then deliver/verify any retained implementation. |

**S8 MPV and Dolby Vision integration** is **ACTIVE**, after completed S7. The user selected `Darkaxt/mpv-android-libdovi`, confirmed NuvioDV as the successful behavioral reference and delegated the output choice. Follow R67-R70; correct video colors/display are required, with actual output capability reported and no unverified native Dolby Vision/FEL promise.

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

Continuation after the completed redesign is S8 -> S9. Only S8 is ACTIVE;
S9 remains planning scope until its prerequisites and execution authority apply.

## S8 execution and acceptance contract

**Current assembly: COMPLETE; S8 remains ACTIVE.** Ticket124
`c55be81274b04050b0530d79c45f049d`, original session18779, run19 exited0;
the Linux group is empty and private mounts are released. Peak1,830,211,584 bytes,
no OOM; player wall1108.0s versus CPU93.1s. Overlay26 is
`358c92cd498c9f6d20c745d61f26a9822157c5f4de220aa04758f67c19796e2b`.
The only production change after123 validates automatic subtitle extensions.
Native transition02 now proves actual pending HTTP handover, repeat-choice
disabling, cancellation on a queue change and real replacement playback.
Subtitle-profile01 proves selected external SubRip on first launch/restart and
unchanged saved association. Both native/server consumers exit0. A separate
positive-drop test attempt03 targeted a hidden player view and failed before
dispatch; it exited cleanly and is not product evidence. Current diagnostic Qt
SHA-256 is `5290fb7e8ed985bf2930e7384201bc5a688d0408489e740cf729a349724865b3`.
[Compact source-bound acceptance](resources/s8/native-integrated-verification.json).
Next: commit-bind the verified source, build normal-mpv from the retained player
step, verify/package it, then one final normal release/readback. Dependencies and
unchanged applicable native evidence are reused; no new stage is opened.

**Current assembly: COMPLETE, not product-stage completion.** Ticket123
(`8667db0ef0b64f999338ee12f86c562d`), session36431, overlay25 SHA-256
`68484d6983f32c15a16bac1490ae323a979338176e29cd8112d7da24a7577548`.
Run18 rebuilt the required core/player corrections from the retained player
step: exit0, empty Linux group, released namespace, peak1,827,266,560 bytes and
no OOM events. Player wall1678.3s versus CPU118.3s confirms I/O remains dominant.
The current diagnostic Qt plugin is
`f5ee0c444cf5c332ea5c9819064f075c73e54622dbef25a797b876a9bc7bfa61`.
The repaired full-player profile/history/menu/library and presentation sequence
has completed. Native history03, corrected volume-profile02 (including verified
original session restoration), library02, default/handover12, input-paths03 and
both themes at100/150/200 percent pass. P5 color04 also passes with unchanged
software reference/negative thresholds and the same7ca MPV payload.

**Resolved R67/R69 finding:** the deterministic HTTP transition case
holds a real libmpv request, verifies actual switching state/outgoing VLC stopped
and disables repeat engine selection, then drops a new video. Native01 proves
that MPV's `AddAssociatedMedia` ignored `check_ext`, accepted that MP4 as a
subtitle and prevented the main queue from receiving it. The owned native/server
processes are closed with exit0. Canonical source now uses the existing exported
subtitle extension/type validator before accepting that association. Closed124,
transition02 and subtitle-profile01 verify the correction. No dependency rebuild
is needed.
The real-header and directory/explicit-filename installer regression passed with
helper `4696c6284cf0dfe0b8eacd9f45ccc386ed20ad13b797998886a97e3071ec8b67`.
The prior run17 completed with native exit0, empty Linux group and released
private namespace, peak1,954,705,408 bytes and no OOM events. Its diagnostic Qt
plugin was `2bdadd27d2398e318816c8e31bccd71978dfe34b1d1b6163bf109bf515295854`.
Native handover, history, remaining workflows and final normal delivery remain
current-stage acceptance work.
The actual FFmpeg continuation passed without compilation (168.2s wall/7.6s CPU);
unchanged libraries/headers retained their timestamps. MPV then passed in30.9s
wall/1.9s CPU with existing objects and unchanged DLL SHA-256
`7ca5086cd73b6188f2e1181ac28dbc5ab8e757cd881c2255591909f24f612e2a`.
This resolves the unnecessary MPV recompilation finding for the current graph;
Native criteria and retained-binding acceptance remain open.
The later normal build changes Qt instrumentation flags only, so reuse this
applicable dependency evidence and continue from the player step if those
dependencies/recipes stay unchanged.

**Current native findings (31 October):** P5, P8.1, P8.4, SDR and HDR10 each pass
actual WGC-composed pixel comparison against the same MPV DLL's software
reference. P5 also rejects the mapping-disabled negative control. Native Win32
client/DWM geometry proves the capture crop at3,0; the original guessed3,1
alignment failed and was corrected without relaxing color thresholds. Four
playing/paused handovers, idle engine selection/restart, restored controls and
track selectors pass the complete native11 regression after test focus/menu/
track-group corrections. Native input-paths02 passes audio, local/HTTP queues,
live pause/resume, missing media, error recovery and finite all-failed repeat-all.
Both missing and incompatible runtime rejection workflows pass. MPV-startup
library01 exposes a row-lifetime defect while selecting alternate audio; its
library portion has not yet run.

Resolved R69 findings: the real prior Spanish language
preference was ignored, and real ML progress0.35208332538604736 while paused
became0 after normal close. A controlled stop confirms MPV time/duration become
unavailable while the old adapter converts them to zero before END_FILE saves
history. The source trace also proves the native mainloop unconditionally saves
its never-started queue input's zero at destruction once MPV has registered that
media in ML. Canonical source preserves unavailable clock values, excludes that
never-started input from native history writes, supplies existing VLC language
preferences and updates track selection roles without resetting stable rows.
These corrections are built in123 and actual history03/library02 pass, including
Spanish selection,42.166668s/1.1 resume, privacy preservation and stable clicked
track rows. Do not rebuild the unchanged dependency stack. S8 remains the sole
ACTIVE stage; S9 NOT STARTED. Historical observations below are superseded by
the current source-bound acceptance receipt and are not new execution orders.

**Closed installer failure:** ticket121 (`9c89c64069d645b595310e5c55ad377c`)
confirmed FFmpeg compilation is up to date and preserved its installed headers,
then stopped on `doc/examples/Makefile.example -> prefix/share/ffmpeg/examples/Makefile`.
The installer helper's directory-only argument contract omitted this actual
single-source/explicit-filename call. Support that form with the same bounded
source/prefix validation and content comparison; diagnose missing, unchanged and
changed explicit-target behavior before the original target-graph continuation.
Closed121/run16: group empty, private namespace released, peak478,937,088 bytes,
no OOM. Resume that failed pipeline at FFmpeg with completed objects retained.
R67-R70 remain ACTIVE and unaccepted; this is an internal R70 blocker.

**Previous managed continuation:** ticket121 (`9c89c64069d645b595310e5c55ad377c`),
session63188, overlay23 SHA-256
`6411a915d519d6cc421b9891ca609b6f6ebd2f52d00402bc39e3cd017d0add0d`.
The complete85-file packet includes the verified installer helper. Resume the
same retained FFmpeg/MPV/player graph with exact old buildinfo identity
`684ae313ba595e7860bc4c9377fc8b1f62cb42304c9a0735f21a07683bc44237`.
Keep the original managed operation through completion and native group exit.
The exact empty unstarted run16 directory was removed by APPLIED cleanup
`bf98e6909566e1e589ff6e5fdd3ddbe4`, one member, no errors/exclusions.
No native acceptance runs during assembly. Native handover, color, profile/
history and queue cases follow the complete diagnostic assembly; normal
package/release, independent delivery and reusable build binding remain open.

**Closed input failure:** ticket120 (`73ee4c92b2704a9a9f5bfc49f0ec0c48`),
session21605, applied overlay22 but stopped before compilation: the root
`install-*` ignore rule excluded the new installer helper from host source
staging. The helper has an exact maintained-source ignore exception now.
The driver verifies recipe identities before creating its run directory.
Closed120 has group-empty/private-namespace release, no OOM and39,526,400-byte
peak. The existing pipeline checkpoint remains closed118/run15; remove the
exact empty unstarted run16 through reviewed cleanup, then apply a complete
new packet and continue from FFmpeg. No completed object is invalidated by
this packet failure. Cleanup `a23cfecf4049046d997f688f0b9030a1` is APPLIED:
7,844 inspected members/5,050,332,737 logical bytes, no exclusions/errors;
native06/07/color01 runtime copies, spent21 controls, installer fixtures and
consumed/rejected remux intermediates are absent. All native evidence and
verified private self-contained fixtures are retained for current acceptance.

**Current native acceptance:** case07 completed with exit0, finished Qt event
loop and unchanged input desktop. VLC-to-MPV rendered decoded video and
preserved paused position, rate, volume/mute and delays. The return to VLC
preserved the observed MPV rate1.21 but exposed delay50ms becoming49ms:
binary floating-point seconds were truncated to integer microseconds before
the VLC millisecond conversion. Round all three MPV delay notifications to
the nearest native tick. This internal R67/R69 blocker remains open until the
cohesive player rebuild and affected full handover workflow pass. Case06's
additive-rate test assumption was corrected to observe an actual increase;
case07 retains strict preservation checks. No new build has started.
The cohesive continuation also adds diagnostic-only event-backed video-output
and ML-history readiness, real native history/restart/privacy checks, and ordinary
MPV presentation/EOF/released-resource logging for the eventual normal package.
The normal verifier requires those actual native events and absence of all test
hooks. Private P5/P8.1/P8.4 excerpts now preserve RPU/configuration and VPS/SPS/PPS
in hvcC, after the first trim was rejected for missing parameter sets. The P5
software positive/disabled-mapping images are discriminating; native color01
exited cleanly but its harness read output parameters before their event, so it
does not establish pixel acceptance. The amended harness waits for decoded
output readiness and compares the reference's actual first timestamp (0.125s),
not a guessed zero. R68 remains open. Rebuild once with this integrated patch,
reusing completed dependencies and applying the verified unchanged-byte installer.

**Closed Qt continuation:** ticket118 (`dc230a4e792e4873ae8c98b6b5f2763a`),
session13188, pipeline run15, overlay21 SHA-256
`0e5f8efb66067c3b68ac4f1dbe69537e855f8a52dacef47366a2e2442aac05b1`.
Configuration and player passed; group-empty/cache release receipts were
inspected, with no OOM. Qt SHA-256 is
`a03bb4642d01121faf52a43bd8910a7ba88c01bb784283e486000a15da7f8420`.
Installer regression ticket119 (`7be64ccc888e4005a8885497060bf99e`) also passed:
the actual unchanged FFmpeg header kept its timestamp, while missing/changed
fixture bytes installed correctly. Its content-comparison helper is wired in
the canonical recipe; target-graph reuse remains an R70 acceptance blocker
for the final pipeline. Preserve all existing objects. Cleanup
`7705cd9e703c5d18871296532cac5d33` is APPLIED: nine spent overlay20 controls/
prior inspection inputs, 7,275,088 logical bytes, no exclusions or errors.
Original reports, all native evidence, current118 and queued119 inputs remain.
R70's final normal-package helper currently recognizes VLC-only first-picture/
EOF/release logs. Extend it for an explicit MPV launch with real presentation,
EOF and native-resource release evidence through ordinary debug logging, while
requiring diagnostic transport to be absent. Complete the current integrated
playback/color acceptance first; include this normal-verification support in
the required final normal build and verify the delivered package itself.
R69 still requires an actual MPV media-library save/restart resume check,
including restored position/rate and history-disabled preservation; the current
prior-profile helper uses `--no-media-library` and does not establish that result.
Reuse the existing native library/profile owners and verify their real saved
state rather than substituting a second history store.

**Closed dependency repair:** ticket116 (`a5568f7ec8c64336a8442763f170f006`), native
session37338, pipeline run14, from `libplacebo`. Overlay20 SHA-256
`6519b73cf0b0d29e26d7e78a33e814586b175e69069d72934e90621128f7254b`
verified82 inputs, changed11, preserved71 identical timestamps. It repairs the
diagnosed Vulkan/native-rate boundaries, reuses existing shader/FFmpeg objects
and preserves unchanged installed header times, verifies completed notices, and
refreshes runtime identities against prior buildinfo
`8e6615369b7d8c908713bc5e5638d0822d115bf80ec15ed490b48d6025e7d4a7`.
The dependency/runtime/notice steps passed. Configuration then exited1 because
the pipeline reran its initial-only `test ! -e config.status` script against an
already configured player. The driver now verifies the existing configuration
when present. Closed116 has an empty group, released cache/private namespace,
864,972,800-byte peak and no OOM. Resume at `configure-player`; do not repeat its
completed dependency steps. MPV SHA-256 is now
`7ca5086cd73b6188f2e1181ac28dbc5ab8e757cd881c2255591909f24f612e2a`.
Runtime staging passed its old/new identity checks, and notice reuse verified
all ten pinned source archives and965 notice files.
Libplacebo and FFmpeg completed successfully (564.0/62.5 and179.5/8.8 s wall/CPU).
MPV is recompiling more inputs than intended: installed FFmpeg headers received
new timestamps despite `install -C`, while MPV's generated configuration stayed
unchanged. For example `prefix/include/libavcodec/avcodec.h` was rewritten at
04:49:34 local, whereas `mpv-build/config.h` remains30 October20:30:07. Preserve
the current compilation; before R70 reusable-pipeline acceptance, inspect native
source/destination attributes and correct unchanged-byte installation on this
Windows mount. Do not hide changed inputs through arbitrary timestamp rewrites.
This is an internal R70 advancement blocker, not a parked stage or S9 deferral.
Read-only ticket117 (`3bea5c0dc6994dabbb481daa7429f9a7`) exited0, group empty,
and confirmed source and installed headers both report mode777, UID/GID1000:1000.
`install -C -m644` therefore fails its metadata comparison on this mount despite
identical header bytes. Before reusable-pipeline acceptance, use a scoped
content comparison that preserves identical files and performs the real install
only for changed/missing files. Do not alter timestamps of changed headers.
Cleanup `b7a06dd1209f0f6fbdc704f697e8ff7b` is APPLIED: native05 runtime/cache,
consumed overlay19 controls and prior spent inspection inputs, 2,628 inspected
members, 1,550,720,906 logical bytes, no exclusions/errors. All native evidence,
original supervisor reports and active116 inputs remain preserved.

**Current acceptance findings, after closed115:** native case05 loaded the exact
packaged MPV and completed the first paused media/position transition with the
outgoing VLC stopped. It failed rate preservation: native VLC was 1.1 while the
paused UI timer cache still held 1.0. Handover now snapshots native media/time/
pause/rate/delays under its lock, and native setRate compares the actual core
when restoring from MPV. The observed audio-only MPV result was independently
traced to `vk-proc-addr=disabled`: FFmpeg's software-frame libplacebo path creates
its own Vulkan device and needs that entry point. Enable it with the existing
SDK's exact Vulkan import archive, preserving the SDK and all completed shader/
FFmpeg objects. The installed System32 Vulkan loader is present. MPV warnings/
errors now route to VLC's logger; diagnostic builds include verbose native logs.
The old same-DLL SDR diagnostic captured black with null video parameters and
fatal filter errors, so its generated `passed` field is rejected as a reference.
The reference helper now requires decoded/output video parameters and no fatal/
error logs before accepting pixels. Both observed failures are internal S8
advancement blockers. No handover feature or DV pixel acceptance is claimed.
Next: one retained dependency/frontend rebuild, then integrated acceptance.

**Native acceptance failure and current repair:** the assembled player starts
VLC playback, seeks and remains usable after rejecting MPV selection. The actual
Messages dialog reports Windows loader error 126. A read-only PE import audit
finds both required app-local payloads present; `winvlc.c` restricts default DLL
searches to System32, while Qt's QLibrary uses plain LoadLibrary. MPV now uses
absolute LoadLibraryEx with DLL_LOAD_DIR plus SYSTEM32 after verifying both
payload hashes, preserving the global policy. The diagnostic observer also now
uses actual native rate/category-delay callbacks: the paused core had reached
1.1 while its optimistic UI notification had already fired. Cases 01-04 remain
failed diagnostic evidence, not accepted handovers. All native processes exited;
no build is running. Next: apply the cohesive loader/observer repair to retained
objects, rebuild the affected Qt inputs, then resume integrated S8 acceptance.
No DV pixel, engine-handover or release acceptance is claimed.

The repair completed as ticket 115 (`c71092860adb4fd59b48def0f6d97374`),
session 77574, pipeline run 13, exit 0, group empty and namespace released.
Peak memory 1,829,363,712 bytes, no OOM; player wall 1,308.9 s / CPU 102.5 s.
Qt SHA-256 `ec67b397491cf913980452b9f375f3bf1ab40dbe389dd73bfa7409f0aa0200cf`;
MPV remains `2decbd50...`. Integrated native case05 now checks actual controls,
paused/playing and idle switches, and explicit disabled VLC-only tools.
Overlay19 SHA-256
`0dc817161b2289c8e3bb0547cd5ab6f295a8fa609491774a629183e423dedc59`
changed four inputs and preserved the other 78 timestamps. Ticket 114 exited
before applying the overlay because a predecessor receipt was absent from its
required host staging location; its group and namespace closed. That staging
error was corrected before ticket 115, without changing completed build state.
Cleanup `68de204999474710181e37561a0a4375` is APPLIED: the four closed cases'
runtime/cache copies and six consumed overlay18 controls were removed after
inspection of all 10,442 members, 6,141,339,267 logical bytes, no exclusions or
errors. Native evidence and original supervisor reports remain preserved.

**Diagnostic assembly closed successfully:** ticket 113
(`a42e3e81515743f8976d76a8018abfd3`), native session 98571, run 12, exit 0,
empty group, namespace released, peak 1,826,050,048 bytes, no OOM events.
Player wall 1,059.5 s / CPU 72.7 s; the Windows 9P bridge dominated the observed
link delay. Qt SHA-256 `3372fc5d60514133cb3743b4c116e9c43536d1497d32595b9d344880deefed87`,
hotkeys `ff37995e180a5a8343036b7885e3fad71af9fa6f45859672737dd7a24c5269fb`,
core `ee5da1763ae507a8e79843ab4371313736aa515331e48e1f61fc6fc16c155018`.
MPV remains the source-built `2decbd50...` runtime. Native acceptance begins with
the isolated `native-vlc-handover-01` workflow and actual keyboard rate/delay
preservation across both engines. A fresh private VLC/Nuvio protected-state
baseline was captured immediately before it. R67-R70 acceptance remains pending.

**Closed resource/link resume:** ticket 113 (`a42e3e81515743f8976d76a8018abfd3`),
native session 98571, run 12. Overlay18 SHA-256
`28af0ebffc9ac5ff86bb2f7ce98066ab28f313e53b80be4115d2c169fc53db45`
verified 82 files, changed five scripts/docs and preserved all 77 other timestamps,
including every C++ and QML input. The normal Make graph runs with the explicit
parent module resource prerequisite and the recorded compile-cache omission.
Supervise this exact operation through its result and group/namespace exit.
Live read-only diagnosis identifies the linker in `p9_client_rpc` disk sleep,
about 1.6 GiB RSS, zero swap, no cgroup OOM or CPU throttling. The observed delay
is the Windows-mounted filesystem bridge; preserve the running link. The private
receipt is `evidence/link-113-io.json`; the final successful link is recorded above.

**Closed repaired build:** ticket 112 (`93b687df96d54859a880af6d8a3ce0ef`),
native session 4861, pipeline run 11, only `player`. Overlay17 SHA-256
`15d6a66db3938d27e17a618ee4ce14f95d8dbad6df94dea35a954b6e2e9d2716`
verified all 81 inputs, changed nine and preserved 72 identical files' timestamps.
The production compiler repairs affect only the two previously failed sources;
the diagnostic observation addition also rebuilds `mainui.cpp`. Completed core,
SDK, MPV, generated objects and QML libraries remain retained. Preserve this
original session through actual completion and group/cache/namespace release.
Integrated acceptance, reusable bindings and final release remain required.
The two corrected sources and diagnostic `mainui.cpp` compiled successfully;
all retained QML libraries stayed up to date. The Qt link then identified an
absent parent-owned `modules/module.rc.lo`, not a corrupt existing object.
The parent Automake rule is now requested explicitly before plugin links.
Ticket 112 exited 1, group empty, cache/namespace released, peak 1,950,248,960
bytes, no OOM; player wall 714.8 s / CPU 77.7 s. Resume only `player` with
`VLC_PLAYER_COMPILE_CACHE=0` and its recorded reason: the full normal Make graph
still rebuilds any outdated input, while this link retry avoids recopying the
header cache after its completed object phase. No product acceptance has run.

**Player interruption and resume:** the user stopped WSL after ticket 108
(`ea6bde2278c64f28acfe726676229944`), native session 68449, pipeline run 8.
The original supervisor reports exit 137, an empty group, 377,643,008-byte peak
and no OOM events. The final started PlaylistMediaList object is absent; retain
all completed objects. Reconcile that exact supervisor report before resuming
only `player`. A byte-verified, read-only Qt header/source cache is capped at
256 MiB inside the existing workload; compile the complete Automake object graph,
release the cache, then link normally. Core DLLs, executables, MPV/dependencies
and configuration remain retained. No further desktop interaction is needed.
Product acceptance has not run yet; S8 remains the sole ACTIVE stage.

Acceptance-harness reconciliation: `verify-mpv-colors.py` now uses the existing
capture-only offscreen mode for WGC, with actual native out-of-monitor bounds and
foreground/input-desktop checks. Its same-DLL software reference must use time
zero; interactive seek/handover stays in the inactive-desktop workflow. This
corrects the old harness's incompatible inactive-desktop/WGC combination without
claiming any pixel result or relaxing R68's positive/negative controls.
The integrated harness's `--backend-controls` case uses actual Qt hotkeys for
rate and audio/subtitle delays, waits on the active engine's notify signals,
checks those values across both handover directions, and restores the originals.
Three diagnostic-only observation names reuse already exposed native snapshot
values; they add no product control or persistent service. This case is prepared,
not verified, and joins the next frozen source batch.
The prior-profile case reads its startup engine from synthetic saved `vlcrc`
on both launches, with no engine command-line override. Its optional external
subtitle case restores the existing fingerprint-bound media-tools association,
waits for a real loaded track and checks that the stored association bytes stay
unchanged. It uses the Windows portable configuration root, not Qt's nested
settings directory. These restart/association checks remain unrun.
The read-only protected-state helper's `--include-nuvio` option also covers the
existing NuvioDV properties and Nuvio WebView settings/storage, excluding browser
and GPU caches. Capture a fresh private baseline immediately before the first
native acceptance case and compare after final delivery; preserve the older VLC
baseline independently. No credential contents are saved or profile files changed.

**Compiler repair:** ticket 109 (`89d75178fe684bc49d987ab4ec5c42ba`), native session
15270, pipeline run 9, ended at MainCtx's use of an opaque player as a VLC object.
The same misuse was traced in controller state changes and playlist startup.
A locked `vlc_player_SetExternalPlayback` API now owns the exact player's native
Start reservation; a frontend getter reads startup pause from the real interface
configuration. No private object-layout cast or instance-wide block on unrelated
players is introduced. Public ABI changes are three additive entry points,
with all old headers/callback layouts/exports and retained-plugin sources checked.
The shared headers require affected objects to rebuild. The next Qt object graph
uses Make keep-going to collect independent integration compiler errors in one
assembly; a failed object still fails the step and prevents final linking.
Ticket 109 is closed, group empty, namespace/cache released, peak 1,361,637,376
bytes, no OOM. Preserve completed prerequisites and resume only `player`.
Ticket 109's Qt cache was released with that operation. The current cache's
identity and lifecycle belong to ticket 110 below.
The final normal build now uses the same pipeline's explicit `normal-mpv` mode.
New attempts retain their own result snapshots and all assembly recipe identities.

**Closed compiler census:** ticket 110 (`b72f9ce519274819a55dc48276fd3975`), native
session 35425, run 10, only `player`. Frozen overlay16 has SHA-256
`09f7b4b7a5b01e743f265ca29d80460a77d75f7ad812138110388b4adae75aa3`.
Its application validated all 81 members, updated 22 changed files and preserved
59 identical files' timestamps. Shared-header dependents rebuild normally.
No runtime/profile or unrelated distribution is changed. Preserve this original
session through the complete compiler census and inspected group-empty result.
That operation has now exited: make 2 / supervisor 1, empty group, cache and private
namespace released, peak 1,934,807,040 bytes and no OOM events. The player step
took 10,819.5 s wall / 1,870.5 s CPU. Exactly two compiler errors were collected;
all other requested objects and QML static libraries completed. No native
acceptance ran. Freeze the repaired overlay and resume only `player` next.
Its read-only Qt cache verifies 169,642,032 bytes / 8,901 files, SHA-256
`4828f3b59f6c1204a293fe994062c470deac0d978290164605373a4eb5bba00e`,
below the 268,435,456-byte ceiling. The header probe took 1.88 s wall / 0.38 s
CPU; this is not a whole-build performance claim. The census has identified an
unqualified playlist-locker name and a lazy QByteArray expression used as a
materialized array. Both fixes are prepared in the canonical checkout; the frozen
active source remains unchanged. Finish the census, batch all diagnosed fixes,
inspect actual supervisor/cache release, then apply the next verified overlay
and resume only `player`, preserving identical input timestamps and valid objects.

The operation records below are historical recovery evidence. They do not
supersede ticket 110 or authorize replaying consumed launch scripts.

**Current player resume:** ticket 107 (`81d97cedab034874b5942760c9f2f6dc`)
generated the cold-build headers and built compatibility objects, core DLLs and
Windows executables. Qt then identified missing `ui_open_file.h`: the incremental
library-only target bypassed Automake's complete `BUILT_SOURCES` prerequisites.
The corrected script now requests Qt's normal `all` target, preparing its whole
generated-source set before compilation. The core/executables remain retained.
Read-only CRT/compiler/localization checks passed; config.status/config.h/libtool/
Makefile hashes stayed unchanged. The Qt flag signature persists across retries;
the canonical line-buffering fix is synchronized so logs expose every new line.
Ticket 107 is closed with an empty group/released namespace, 383,291,392-byte peak
and no OOM. Resume only `player`; no cache, dependency or configure rerun.
R67-R70 product acceptance remains pending; do not pause at build errors.

**Previous assembly operation:** ticket 106 (`f371ecad45ad46e88402694cf6293af9`), native
session 46722, pipeline run 6. Before cache setup, actual GCC syntax and dependency
output passed with the new prefix libplacebo header under the formerly failing
dependency-first include order. Ticket 105 had caught only an incorrect diagnostic
trace assertion before pipeline entry; the dependency-file check corrects that
assertion. MPV/runtime/notices/cache release/configuration subsequently finished;
the later player resumes above own the remaining assembly and acceptance.

**Current assembly repair:** ticket 104 (`951eb9f17b9d476795646c3213acaaf1`),
pipeline run 5, built uchardet and configured MPV. Compilation identified SDK
libplacebo headers shadowing the new prefix through Meson's dependency include
ordering. The target SDK is now an `-isystem` fallback, including an existing-tree
Meson option update and an exact header/syntax reproduction before cache setup.
No third-party source or AVFrame compatibility fallback is introduced. Ticket 104
ended with an empty group/released namespace, 746,799,104-byte peak and no OOM.
Resume the failed MPV step; affected MPV objects must rebuild with correct headers,
while all dependency archives remain retained. R67-R70 acceptance is pending.

**R70 repeat-build lifecycle (current-stage advancement blocker):** the user
requested a reusable compilation pipeline and weekly upstream build/release
automation. After this operation exits, preserve the verified pinned SDK and
dependency build tree as intentional active project inputs on D:, with that
automation as the named continuing consumer. Perform a scoped path-binding
migration only after whole-tree exit; preserve current bindings during assembly,
verify the destination and record the retention/retirement contract. This does
not move the canonical checkout, installed player/profile or unrelated VM disks.
Native test profiles, private media captures and spent scratch remain expendable
and require exact cleanup. Final S8 closure requires verified reusable build
bindings and cleanup of the temporary residuals; no S9 work is authorized here.

Retention implementation is prepared in `retain-build-inputs.py` and the exact
project-root launcher guard, but has not run. It requires successful closed
reports, a complete pipeline and a clean source clone bound to the verified
commit. Its directory-identity journal preserves same-volume move state; the
new launch binding still requires actual gated verification before acceptance.
The existing weekly schedule now follows the revoked-pause clarification and
prohibits desktop controls; its Monday 09:00 recurrence is unchanged.

**Current assembly, 30 October:** pipeline run 2 / ticket 100
(`1ed02fbc5b944ce9944f935ef02168db`) completed SPIRV-Cross, libplacebo and FFmpeg.
FFmpeg took 5,898.6 s wall / 1,222.6 s CPU; filesystem overhead remains material.
MPV configuration then failed at iconv: its header/static library are present,
but Meson's system detector enumerates compiler search paths rather than the
cross-file's linker-only SDK paths. Run 3 / ticket 102 established that this cross
compiler ignores `LIBRARY_PATH`; that failed hypothesis is removed. The compiler
definitions now use explicit `-B` library prefixes, keeping the selected CRT first.
The resume entry checks actual compiler discovery before preparing the cache.
Resume at MPV in the same pipeline state; no prerequisite rebuild
or product acceptance checkpoint. Ticket 100 ended with an empty group, released
namespace, 1,015,164,928-byte peak and no OOM events. Only the changed recipe/cache/
pipeline scripts were copied into the retained source; unchanged file timestamps
and compiled objects remain intact. The MPV resume adds immutable SDK/source/API
inputs to the existing byte-verified 512 MiB cache and releases it before VLC.
R67-R70 remain unaccepted. The historical tickets below explain retained outputs,
not new execution orders; the user explicitly revoked pausing on build failure.

Ticket 103 verified iconv discovery after the compiler-prefix correction, then
identified the enabled uchardet dependency missing from this SDK. It ended with
an empty group/released namespace, 592,666,624-byte peak and no OOM. Preserve
subtitle encoding detection: the recipe now builds pinned official uchardet
0.0.8 as a static library before MPV configuration, with source/notice accounting
added to the same runtime manifest and final packages. The enabled dependency
set is checked together before configuring MPV. Resume the same failed MPV step;
FFmpeg and the SDK stay retained. No new stage or product acceptance is claimed.

Current assembly checkpoint, 30 October: ticket 90 (`f81b62fad0564b659a58eacbc4b00617`) exited 1 with its Linux group empty, peak charged memory 1,270,919,168 bytes and no OOM events. Qt/Schannel and the Qt lifetime patches finished. MPV source setup finished; shaderc CMake generation failed because `SHADERC_SKIP_INSTALL=ON` disabled SPIRV-Tools export sets while this pinned shaderc revision still enabled glslang's exports through a configure-time generator-expression bug. The recipe retains consistent export sets without installing that dependency tree. Resume `assemble-s8.sh` at its explicit `shaders` phase, preserving the completed SDK and extracted sources. The previous recursive-unmount cleanup also failed on inherited locked system submounts; the wrapper now waits outside the private PID/mount namespace and verifies release after namespace exit. R67-R70 remain unaccepted; these are internal assembly blockers, not a reason to park S8. Next: one managed remaining assembly, then the complete integrated S8 acceptance pass and final normal delivery.

Ticket 91 (`2c29c4c6b27b4640b56aa22c7623d77d`) compiled the complete shaderc combined archive, then exited 1 because its separate `shaderc_combined-pkg-config` custom target had not been requested. The recipe now requests that target alongside the library; existing objects remain reusable. The actual group is empty, peak charged memory was 627,052,544 bytes, no OOM occurred, and the revised namespace owner verified mount release. Resume the same `shaders` phase through the remaining assembly. The user's subsequent instruction is to shut down the laptop after this task is completed and verified; no shutdown is authorized by a partial build checkpoint.

Ticket 92 (`5e4d19284cd7441ca16083869d6fabbc`) generated shaderc's metadata and built/installed SPIRV-Cross, then libplacebo configuration stopped because the cross-file omitted `dlltool`. The exact existing `x86_64-w64-mingw32-dlltool` is now bound in both the maintained recipe and this generated cross-file. Resume at the explicit `placebo` phase, retaining Qt and shaders. Ticket 92 exited 1 with an empty group, verified namespace release, peak charged memory 542,822,400 bytes and no OOM. Integrated acceptance remains pending; no feature or stage is accepted from dependency-build results.

Ticket 93 (`28d50fb323fd41db8a64dbac74620a58`) configured libplacebo with D3D11, Vulkan, shaderc and DV support; compilation stopped in its first shader-generation target because this pinned image lacks Jinja2. The recipe now uses hash-pinned Jinja2 3.1.6 source through a task-local Python path with the image's existing MarkupSafe 2.1.5. This is a recorded host build input, not an additional linked Windows dependency. Resume the stopped `placebo` target and remaining assembly, retaining all compiled prerequisites. Ticket 93 exited 1 with an empty group, verified namespace release, peak charged memory 369,000,448 bytes and no OOM. No S8 acceptance is claimed.

Ticket 94 (`d7d8256970f8450b8801cd8835870b47`) generated the Jinja shader sources, then the Vulkan generator stopped because libplacebo searched its private install prefix for `vk.xml`. The registry already exists in the verified VLC SDK at `/work/build/contrib/x86_64-w64-mingw32/share/vulkan/registry/vk.xml`; the recipe now passes that path explicitly for fresh configuration and resume. Preserve all compiled/generated work and resume `placebo`. Ticket 94 exited 1 with an empty group, verified namespace release, peak charged memory 57,651,200 bytes and no OOM. S8 remains ACTIVE with all integrated acceptance pending.

Ticket 95 (`7ab859d4273948a09feec0d96c99d043`) built and installed libplacebo. FFmpeg configuration then failed its actual dependency link because GNU ld's `-static` search excludes the intentional SPIRV-Cross `*.dll.a` import library. The private pkg-config binding now names that existing import archive explicitly; other libraries retain static linkage. Read-only PE import inspection confirms the built SPIRV-Cross DLL imports only KERNEL32 and msvcrt. Resume assembly at `ffmpeg`, preserving Qt, shaders and libplacebo. Ticket 95 exited 1 with an empty group, verified namespace release, peak charged memory 357,294,080 bytes and no OOM. This is assembly evidence only; R67-R70 acceptance, normal release/delivery and shutdown remain pending.

User-authorized clarification, 29 October: R67 includes an in-player on-demand VLC/MPV switch. Preserve the current item's position and paused/playing state across deterministic outgoing-engine teardown and incoming-engine load, with brief transition feedback and recoverable errors. Verify both directions, idle and playing/paused switching, repeated requests, queue changes during transition and unavailable runtime/media. The initial restart-only selection draft does not satisfy this criterion.

Authorization is `already_authorized`. This is one integrated implementation stage. Scope clarification and diagnostic probes do not create artificial preparatory stages or count as feature acceptance.

The user-confirmed Android source is `Darkaxt/mpv-android-libdovi` at NuvioMobileDV's pinned application/library contract (`a6d4de8b2109347e07dcd2daef258deee9a97e29`, AAR SHA-256 `b266c9f5ed940b761da572f1496fcf2152fe624cdfd42354b33ba5c9e3fc8721`). Its pinned stack contains libdovi 3.3.2, FFmpeg `239f2c733de417201d7ad3b3b8b0d9b63285b2b1`, libplacebo `3330a515d62139259c26239014f286e233bd3a5c` and mpv `14f2d48cbc7dda61adb4bd181e107a1f3f76e533`. Its two FFmpeg patches target Android MediaCodec metadata/P010 and are not Windows patches. The user's successful Android playback is user-reported; it is a concrete behavioral reference, not a Windows verification result.

NuvioDesktopDV provides the corresponding Windows reference: `shinchiro/mpv-winbuild-cmake` release `20261021`, archive `mpv-dev-x86_64-20261021-git-e471496c56.7z` SHA-256 `efc719eff3dc5954b4a5efc800632808bcec01cc9034940dd14e5eb7fe9ea633`; DLL SHA-256 `04e4d27dc385dc18ddd93fbe69c75e635b864f3c6ec53a9122df54c2f7842f4a`. Its documented source is mpv `e471496c56f0f49c133bd88b50aed62b845f1909`, FFmpeg `9a861e9687d30e657d59521817cad18405995983` and libplacebo `285d1cc8af2ab79b72ac662eb09736de8c12392b`, containing `c93aa134` and FFmpeg's integrated RPU parsing. Reverify the DLL/build evidence and native behavior before relying on it for acceptance; a string or API symbol alone does not prove correct colors.

**Integration decision:** retain the pinned libmpv Direct3D11 render API and existing Qt DirectComposition video/backdrop surface. Source inspection and native pixel diagnostics demonstrate that the render API uses legacy `gl_video`, restores base-layer mapping and does not perform DV reshaping. Apply the required FFmpeg/libplacebo filter `lavfi=[libplacebo=apply_dolbyvision=1:colorspace=bt709:color_primaries=bt709:color_trc=iec61966-2-1:range=pc:format=rgba]` before presentation, producing explicitly tagged full-range RGBA BT.709/sRGB SDR. This is a conversion path, not native DV output or proof of physical display luminance. Select `hwdec=d3d11va-copy`: direct `d3d11va` loses the effective correction at the hardware-frame/filter boundary and is rejected despite reporting DV input metadata. At the actual 15-second scene, copy-back versus software decoding has per-channel mean absolute error 0.0284/0.0082/0.0108 (0-255); direct hardware decoding gives 69.65/15.99/9.41 and the mapping-disabled negative control gives 69.80/15.80/9.40. Profile 8.1 and 8.4 software references are also captured from the official same-scene fixtures. These are independent renderer diagnostics, not integrated Qt feature acceptance. The official runtime archive was independently downloaded and its DLL matched the pinned hash; corresponding dependency sources/notices remain required. Retain the existing queue/settings identities, explicit selection and VLC default. The bounded owner uses a dedicated native surface/render thread and UI-owned commands/events, with event-driven handover and ordered render-before-core teardown. Existing advanced VLC-only tools disclose their required engine.

| Acceptance unit | Satisfied | Remaining criteria / advancement blocker | Resolution and evidence |
|---|---|---|---|
| R67 engine selection/runtime | Native default/saved selection, both handover directions paused/playing, idle choice, queue change during real pending HTTP, repeat-request disabling and missing/incompatible recovery pass | Confirm the final normal package retains the exact source-bound runtime and usable native engine paths | Source-bound native receipt; normal delivery checks remain in R70 |
| R68 DV rendering | Actual composed P5/P8.1/P8.4/SDR/HDR10 pixels pass same-DLL reference comparisons; P5 incorrect-mapping negative control rejected | Confirm final normal MPV payload identity and real DV playback; retain explicit SDR output/native DV/FEL limits | Native WGC RGB errors below3/channel, measured crop3,0, unchanged7ca runtime; final package acceptance in R70 |
| R69 player/preservation/Figma | Real controls, queue/library/playlist independence, rate/delays, language/tracks/SRT, fullscreen/keys, EOF/error/live inputs, history/privacy/restart and both themes/scales pass; installed VLC/Nuvio/language hash comparison unchanged | Final normal native runtime and post-delivery preservation comparison | Native receipt and private before/after readback; no tracked deferral |
| R70 final delivery | Both runtime DLLs and merged 116-input corresponding-source notice inventory built; established channel and S7 package preserved | Normal final build, corresponding-source package, verified commit/sync, one final release/readback, reusable build binding and exact scratch cleanup | Independent downloaded package/native/source checks, protected-state comparison and gated retained-build verification |

S8 stays ACTIVE with no tracked deferral. The integrated diagnostic acceptance
is verified in the current source-bound receipt. Remaining internal advancement
blockers belong to R70: exact committed normal build/native package, complete
corresponding source, one normal release and independent readback, final
preservation, gated reusable-input binding and exact scratch cleanup. No later
stage is active. The historical build findings below do not reopen resolved work.

The user stopped the original SDK process through Coordinator after both native app-control transports were unavailable. Original SDK ticket `662980ea77e14ad1be0bf89665b53fee` (89), native session 67182 and monitor cell 749 have now completed. The inspected supervisor result reports exit 137, `populated=false`, no OOM events and peak charged RAM 1,202,204,672 bytes; Coordinator reports idle with no live workflow or recovery requirement. This confirms cancellation, not successful SDK completion. Qt GUI is linked and Widgets code generation completed before exit. Preserve the reusable source/build tree. Finish the remaining source/package integration before starting the coherent assembly workflow; no replacement build is running.

Native audio mix/stereo/visualization and casting menus disclose their VLC requirement, the timecode widget identifies its VLC dependency, and the native bookmark menu uses the shared player controller. The volume adapter retains native mmdevice callbacks/settings ownership, applies MPV software gain only above unity and selects the same endpoint/session/default role. The source-bound runtime includes `mpv-wasapi-session.patch` SHA-256 `fc6f68dc77884c7f07a997219ef76c7809e868956d14e7d41d64cb8f1d5c6d28` and has been built and bound to the exact runtime identity. R04/R67/R69 volume persistence remains an internal advancement blocker until actual restart, attenuation/boost/mute and both handovers pass in the assembled player. No new persisted volume/mute store is introduced.

Initial native volume can be unknown while mmdevice opens its Windows session. The adapter now leaves that unknown state intact instead of writing a guessed 100% level. The existing player audio listener publishes the first reported level, retaining the former OSD behavior; the adapter aligns once after that event unless an explicit user volume command has already established its level. This readiness correction remains uncompiled and requires the same real restart/handover verification.

The customizable settings popup's native-only choice models (visualizer, stereo, zoom/aspect/crop/deinterlace) are now labeled and disabled under MPV, while real audio/subtitle track models remain selectable. Native statistics/invert controls disclose the same dependency. The video page identifies MPV's SDR conversion and reports no-video inputs honestly. These UI changes remain uncompiled/unverified; preserve the Figma contract in the pending native theme/DPI workflow.

Current next action is the original compiler census and batched repair described above, followed by integrated acceptance. Native STOPPED precedes final input destruction, and normal VLC Stop retains a cached vout/window. Handover therefore requests cache retirement on the existing player worker after inputs join, then waits for actual compositor window release, including listener-held references, before MPV claims the provider. Public changes are three additive entry points: the stopped-player release operation, exposure of existing native playlist expansion, and the locked per-player external-playback reservation. `check-mpv-plugin-abi.py` verifies unchanged existing public headers/callback layouts/exports and retained-plugin sources against 1.0. Core, Qt and hotkeys are rebuilt. The isolated runtime, native capture utility and synthetic ordinary-media fixtures are prepared. `verify-integrated-player.py --switch-engines` covers paused/playing handovers both ways; its missing/incompatible runtime cases also require inspection of the captured actionable error details. `verify-mpv-colors.py` checks actual composed Qt pixels against the same-DLL software reference and Profile 5 negative control. These acceptance workflows have not run against S8. Local installation remains pending integrated acceptance and final delivery; the installed VLC/profile stays protected.

Execution consolidation: the required MPV sources/dependencies build sequentially in one managed `build-mpv-runtime.sh build` invocation after SDK completion. Reuse completed SDK/runtime build trees; correct an actual failure and resume its affected phase/targets rather than restarting prerequisites. Bind the finished runtime and all required dependency DLLs before building the coherent player source. Run feature acceptance against that integrated player; no additional standalone initialization checkpoint is required first. Same-DLL software color references remain required acceptance inputs. A normal release build follows integrated acceptance so diagnostic hooks are excluded from delivery.

User clarification: validate at the end of S8, after its complete required implementation and integration, in one coordinated stage-acceptance pass. Do not insert component-validation checkpoints during assembly. Before that pass, monitor retained build operations and resolve actual build failures. An acceptance failure returns the affected S8 behavior to implementation and focused revalidation; unchanged applicable evidence is reused. Final package/delivery verification remains required for S8 closure.

Media-entry diagnostics reproduced the plain-M3U failure with MPV's forced FFmpeg demuxer (`No format found`, ordered native exit). Native automatic preparse skips network items and does not supply the required playlist expansion here. The draft uses MainCtx's existing no-deadline parser for containers, with cancellation/completion ownership, then native playlist expansion and cursor. An earlier input ending during preparse cannot advance past the requested container. Error advancement walks the native cursor, skips already failed queue identities and stops a wholly unreadable repeat-all queue without reopening failures. Explicit playback retries reset that failure set. The earlier reference-DLL option/D3D11 probe applies only to its recorded controller hash; the subsequent shared-session options require the source-bound patched runtime and invalidate that probe for current initialization. `verify-input-paths.py --engine mpv` covers local/HTTP playlists, live pause/resume, missing input, recovery to valid media and finite repeat-all failure. These source changes remain uncompiled and the integrated checks have not run.

R70 uses the completed source-bound build rather than distributing the reference nightly. Ten exact corresponding-source archives are retained: MPV, FFmpeg, libplacebo, fast_float, shaderc, glslang, SPIRV-Headers, SPIRV-Tools, SPIRV-Cross and uchardet. The separate prefix preserves VLC's SDK glslang. The runtime's `MPV-BUILDINFO.json` binds `libmpv-2.dll` SHA-256 `2decbd50da1bff7edd8903733f37d85c568f3464c770de390024af8e7d5142cf` and `libspirv-cross-c-shared.dll` SHA-256 `ff4328aa7a73a28a1f0a0e54e285155edf971d2020c7c90e4769b8d077ead8c9` to the recipe, headers and source registry. The merged notice inventory contains 116 corresponding-source inputs, including the 106 baseline SDK inputs, and separately identifies host-only tools. Actual source packaging, integrated native acceptance, normal delivery/readback and reusable build bindings remain R70 advancement blockers. No standalone native initialization probe is required during assembly.

Same-profile copy-back/software diagnostics now pass for all three official fixtures: maximum per-channel mean error is below 0.03 for P5, P8.1 and P8.4 at the same 15-second frame. Ordinary SDR references and a locally authored HEVC Main10 HDR10 fixture are also prepared. The latter uses an actual BT.709-to-BT.2020/PQ pixel conversion, not metadata retagging; its source/arguments/probe/hash are recorded. These are acceptance inputs and independent renderer observations, not completed integrated player criteria.

The shared-session handover workflow checks native volume/mute through both engines, with paused attenuation and playing amplification cases kept muted, alongside position/pause preservation and captured engine controls. The read-only bridge separately requests MPV's actual WASAPI volume/mute asynchronously, so a matching UI value cannot conceal a different output session; real query errors terminate that observation without a deadline. `verify-prior-profile.py --engine mpv --check-volume-persistence` adds same-path process restart to the existing malformed-state, appearance, track-language and font-preservation workflow. These native checks remain unrun. Superseded overlay04/copies were retired through inspected cleanup `b133c1adb9495afbc4ef186e85dcdf55` (APPLIED, 3,075,612 logical bytes). Unused overlay05/copies and completed four-file patch-application scratch were retired through `754e43bcbe621f2e3fbbf1dad19995d0` (APPLIED, 3,356,714 logical bytes). Both have no exclusions/errors. Canonical source, pinned MPV archive, patch and compact receipt remain. Stage the next overlay only after the actual source-bound DLL identity is available, immediately before the player build.

Read-only native display query records two attached 10-bit outputs, one currently using DXGI BT.2020/PQ HDR and one SDR. Both report advanced color enabled. The selected MPV path remains explicitly SDR; this evidence does not establish native HDR/DV signaling or calibrated luminance. Spent archive/object/compiler scratch was retired through inspected transaction `5bedcebbb9cdd276175a578a69432821`, APPLIED without exclusions/errors, 37,722,234 logical bytes. Superseded overlays 01-03 and their exact staging copies were retired through inspected transaction `374d3a7fd643cf8ef05f81a52f12e380`, APPLIED without exclusions/errors, 8,628,478 logical bytes. Already consumed rootfs/contrib/MPV/crane retrieval archives, the abandoned Debian import download and completed HDR fixture TEMP directory were retired through inspected transaction `0f77e4950cfd63995c4ffc0d1420adf2`, APPLIED without exclusions/errors, 8,010,676,486 logical bytes. Their extracted current consumers and compact provenance remain; initialized toolchain invocations do not need those removed retrieval archives. Capture/query executables and current staging inputs remain needed by subsequent acceptance and delivery checks.

The first direct owned-WSL import was terminated by Warden (exit 126, attempt `vlc-s8-wsl-import-20261029-141430`); its transient registration/disk rolled back and unrelated distributions were preserved. That rejected import was recorded in the shared recovery ledger and was not retried. The supported alternative is the installed WSL gate running Ubuntu's unchanged UID 1000 in a private rootless user/mount/PID namespace with the verified image extracted into the exact registered task directory. It performs no import, registration or policy change. Original gate ticket `662980ea77e14ad1be0bf89665b53fee` owns SDK preparation; observe its actual completion before dependent work. Its enforced workload remains 3.5 GiB RAM, 512 MiB swap and one CPU under the 4 GiB VM ceiling.

Registered scratch is `D:/Temp/vlc-s8-20261029`, transaction `a9e4f2c8f5a10e202798c9e92917ad8c`. Its disposable SDK source clone at `toolchain/work/src` has exact-root transaction `1ef0e2dbf70559b3ae1b91cd0e7063ca`; retire it before the containing transaction's final review after all consumers exit. Sustained native/build/media I/O requires D:; small disposable control material may use an exact E: folder if needed. Preserve other tasks' Nuvio build trees and installed runtimes; read/copy verified inputs without modifying them. All heavy Linux work must use the installed WSL gate and existing resource ceiling. Final delivery belongs to the last S8 work item, after the complete feature and preservation criteria pass.

Completed independent renderer probes no longer need `evidence/shader-cache`. Exact-root inspected cleanup `323bb52fc78c3c0dad1ca293eef419ac` is APPLIED (24 members, 80,300 logical bytes; no exclusions/errors). Native reference PNG/JSON records remain outside that root. Subsequent renderer/probe commands disable shader caching; their new references must bind to the actual source-built DLL hash, retaining the same-DLL condition for integrated pixel comparison. The private libplacebo and MPV builds both select the new shaderc compiler, avoiding mixed glslang versions in that runtime while leaving VLC's SDK intact.

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
- Product stages: S0, D1 and S1-S7 are COMPLETE. S8 is the sole ACTIVE stage under the current contract above; S9 remains NOT STARTED. S7's final release delivery and the earlier resource recovery/cleanup are verified. Separate installation over existing VLC remains outside scope.
- Blockers: none for S0, D1 or S1. S3 acceptance and delivery are verified; it has no remaining blocker.
- Tracked deferrals: none. The former startup-paused WASAPI defect was resolved and verified in S7/R61; it is not an open S8 requirement. Current S8 acceptance gaps stay advancement blockers within ACTIVE S8.

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
