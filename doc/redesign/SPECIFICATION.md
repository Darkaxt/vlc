# VLC desktop redesign specification

Version 1, registered 13 October 2026. Owner: Darkaxt. Upstream baseline: VLC master `392bc1d0abdb7396b6c97fef206efa1d23868e19`. Resource policy updated during registration at the user's request: retain the original Figma archive and its contents manifest; omit derivative PDF/PNG exports from Git.

## Authority and current authorization

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
