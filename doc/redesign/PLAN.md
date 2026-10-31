# VLC redesign stages and reconciliation

**S8 MPV and Dolby Vision integration is COMPLETE (31 October 2026).**
[Modern VLC Fork 1.1.0](https://github.com/Darkaxt/vlc/releases/tag/redesign-v1.1.0)
is a normal published release from application commit
`c8a1cdfd31a97e7ecc0bda772d4148f1f87a6b26`, with portable Windows x64 binary,
complete corresponding source and checksums. Independently downloaded artifacts
match the verified archives and pass real normal MPV Dolby Vision and VLC playback.
[Final release and requirement reconciliation](resources/s8/final-release.json)
supersedes the pre-release status in the original native acceptance snapshot.

S0, D1 and S1-S8 are COMPLETE. No implementation stage is ACTIVE.
S9 remains NOT STARTED and planning scope only. Remaining S8 criteria, blockers
and tracked deferrals: none. Installed VLC/Nuvio data and Windows language state
are unchanged; root AGENTS.md and the prior verified 1.0.0 release are preserved.
Separate installation over existing VLC remains outside scope.

The verified reusable build is `D:/VLC-Redesign/build/windows-x64` for the existing
Monday 09:00 Europe/Bucharest weekly consumer. Its source/configuration/runtime
check passed through gate 126, with an empty Linux group and released mounts.
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
