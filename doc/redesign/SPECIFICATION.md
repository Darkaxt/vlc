# VLC desktop redesign specification

Version 1, registered 13 October 2026. Owner: Darkaxt. Upstream baseline: VLC master `392bc1d0abdb7396b6c97fef206efa1d23868e19`. Resource policy updated during registration at the user's request: retain the original Figma archive and its contents manifest; omit derivative PDF/PNG exports from Git.

## Authority and current authorization

This is the authoritative specification for a VLC fork based on Juxtopposed's VLC Redesign. It records the complete product concept, implementation constraints, acceptance criteria, references, and stage ownership. The implementation plan must preserve these requirements. Reference images describe appearance; this document governs behavior and acceptance. Existing upstream functionality remains authoritative where the concept does not specify a change.

On 17 October 2026 the user authorized the first unfinished preparatory stage (D1 design-source readiness), then an explicit stop so its effort can be measured. This supersedes the earlier instruction to leave D1 unstarted. Scope includes reproducible offline decoding, required variant inventory, representative vector exports and screen reconstruction/validation, documentation, verification, commit and previously authorized GitHub synchronization. It does not authorize S1 or later VLC product implementation, compilation, installation, or application releases. Stop after D1 and report measured elapsed effort and remaining fidelity limitations.

For this bounded stage, representative outputs are the light player and global-settings screens at their source dimensions, plus monochrome/two-tone icon variants. Validate against native Figma exports where available, preserve source IDs and hashes, and explicitly record unsupported rendering features and fallback requirements. These are design-source tools and evidence, not a VLC player implementation.

The user subsequently authorized proceeding with S1 on Windows x64, as proposed, on 17 October 2026. S1 covers an unmodified source build, real playback, capability/configuration inventory, verification, commit and existing GitHub synchronization. All temporary files and testing must be under a task-owned folder on E:\ and cleaned afterward. This authorization supersedes the completed D1 stop boundary for S1; S2-S7 and installation/distribution/releases remain outside this turn's scope. Windows x64 is the confirmed baseline target, without restricting eventual additional platform scope. Linux portability should be retained in shared Qt code; native macOS, Android, iOS, and TV interfaces require separate scope decisions and are not implied to be implemented by a Qt desktop change.

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

Local inspection decoded the embedded schema and document message without Figma: 12,563 nodes, 1,321 blobs, 38 component sets and 208 variants under the main Icon component set. Parent references and geometry blob indices passed structural checks; semantic encode/decode round-trip passed. That initial inspection established offline access to design data. D1 subsequently added selected SVG/screen export tooling and native visual comparison, with the fidelity limits recorded in the stage ledger. Pixel-identical rendering is not established. D1 closed at its authorized stop; the subsequent instruction now authorizes S1 only, as recorded above, followed by a stop before product redesign.

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

Video reference: 1:35-5:29 and 13:56-14:08. Inspect the `Player`, `Player - Light` and `Controls` frames/components in the [editable Figma design](resources/vlc-redesign.fig).

| ID | Requirement and acceptance criteria | Stage |
|---|---|---|
| R10 | Compact player layout: previous/play-pause/next on the left, track and queue controls on the right, cone-inspired volume control, thicker seek bar below the controls, title and window controls above. Open actual media and demonstrate working play, pause, stop, previous/next, volume/mute, seeking and fullscreen through the new controls. | S2 |
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

## Library navigation and opening media

Video reference: 9:22-13:54.

| ID | Requirement and acceptance criteria | Stage |
|---|---|---|
| R30 | Make library access discoverable from the current media/folder title and a sidebar control. Support compact browsing beside playback and a full library with miniplayer/queue access. Drag actual library items into the queue without interrupting current playback. | S4 |
| R31 | Include videos/folders, music, network streams, playlists, recents and home. Folder browsing has breadcrumb/address navigation, search, grid/list/detail views and sorting including watched/unwatched. Music supports songs, albums, artists and genres using actual library metadata. Verify navigation and selection on a real indexed library, including missing metadata and empty categories. | S4 |
| R32 | Create/manage stored playlists; add selections from other views; pin playlists and folders; show recent and resumable media on home. Define watched state and pin persistence and honor history/privacy choices. Verify restart persistence and queue/playlist independence. | S4 |
| R33 | Provide clear entry points for files, folders, discs, network URL/playlist, capture device, clipboard, recent media, conversion and streaming/casting where upstream supports them. Separate the ordinary open path from conversion/stream configuration. Verify one real network playlist and retain the complete upstream action inventory; do not ship third-party channel lists by default. | S4, S5 |

## Bookmarks shortcuts and preferences

Video reference: 14:52-18:53. Inspect `Settings - global`, `Settings - audio`, `Keyboard Shortcuts` and `right-click menu` in the editable design.

| ID | Requirement and acceptance criteria | Stage |
|---|---|---|
| R40 | Add a bookmark with a direct action/shortcut and manage bookmark and chapter lists in the sidebar. Seek to real positions and distinguish user bookmarks from embedded chapters. Define bookmark persistence and verify it across restart. | S5 |
| R41 | Provide a directly accessible keyboard-shortcuts dialog and on-screen action feedback that can include the actual shortcut pressed. Preserve existing mappings unless an explicitly reviewed conflict requires change; present conflicts rather than silently replacing bindings. Verify remapping, focus handling, typing into fields and feedback preferences. | S5 |
| R42 | Reorganize preferences into General, Interface, Privacy, Controls, Playback, Video, Audio, Subtitles and OSD, Library, Network, Performance, Recording/Streaming, and Extensions. Basic and advanced options live within their relevant category. Explain options with visible help affordances and descriptive choices rather than unexplained numbers. Maintain a mapping to real upstream option keys, defaults, ranges, persistence and restart requirements; every inventoried option remains accessible. | S5 |
| R43 | Distinguish installable extensions/add-ons from internal modules/plugins. Preserve extension and module capability while placing internal technical settings in the appropriate advanced area. Verify an existing supported extension and advanced module settings remain reachable. | S5 |

## Customization onboarding and presentation quality

Video reference: 18:58-20:43.

| ID | Requirement and acceptance criteria | Stage |
|---|---|---|
| R50 | Provide in-place drag/drop layout customization with clear insertion areas, removable/restorable controls, and a reset path. Save named profiles spanning layout and applicable settings, not just a toolbar list. Define the profile's setting coverage explicitly and verify switching/restoring profiles across restart without affecting media or credentials. | S6 |
| R51 | Offer onboarding with light/dark/system theme, accent selection and basic shortcuts; allow skipping and reopening it. Preserve prior-user settings. Verify first run, skip, completion and subsequent startup. | S6 |
| R52 | Apply the reference visual system consistently to player, library, sidebars, menus and dialogs, including the Qt Widgets boundary. Verify representative states at 100%, 150% and 200% display scaling, keyboard focus, accessible labels, readable contrast, resized windows and long/localized text. Figma's 1920x1080 examples do not mandate a fixed-size window. | S2-S7 |

## Verification and final completion

| ID | Requirement and acceptance criteria | Stage |
|---|---|---|
| R60 | Maintain source/design attribution, original design hashes and an inventory of production fonts, icons and media licenses. Preserve VLC and dependency license notices and source provenance. A design reference screenshot is not an approved production asset. | S0, S7 |
| R61 | Verify real integrated behavior with representative local video/audio, multiple tracks, text subtitles, playlists, network input, missing media, nonseekable media, configuration persistence and keyboard/fullscreen interactions. Use redistributable fixtures or user-authorized local files. Record actual results and limitations, not just screenshots or mocks. | S7 |
| R62 | Document reproducible local packaging, configuration recovery and upstream synchronization. Run focused checks appropriate to changed boundaries; run broader suites when cross-cutting risk requires them. Reconcile every requirement before claiming the full redesign complete. Commit verified scope; publishing or installing builds requires separate authorization. | S7 |
| R63 | Register this specification, stage plan, attribution, original editable Figma archive, archive contents manifest and editable-access links in the GitHub fork. Omit derivative PDF/PNG exports from Git per the user's updated instruction. Verify relative links, file integrity, upstream parentage and remote commit contents. Keep source/application behavior unchanged in this registration task. | S0 |
| R64 | Before VLC UI implementation, establish a reproducible design-source workflow from the retained `.fig`: reproduce offline decoding, identify required screen/component variants, export representative custom vector icons, and validate representative screen reconstruction against the original appearance. Record unsupported features and any required Figma fallback. Limit tooling to the project's design needs; do not build a general Figma replacement. D1 was authorized and completed on 17 October 2026; subsequent S1 authorization is recorded above. | D1 |

## Execution constraints

Use one ACTIVE implementation stage at a time, prove a narrow real player workflow before expanding, and close each stage against every assigned acceptance criterion. Required later-stage work is not a substitute for a current-stage criterion. Record exact internal/external blockers, resolution conditions and affected requirements; do not describe ordinary unfinished work as blocked. Do not silently drop difficult features.

Prefer deterministic state transitions and actual completion signals. Do not add arbitrary retries, sleeps or timeouts to hide lifecycle or synchronization problems. Preserve dirty worktrees, unrelated files and user configuration. Use bounded resources for previews and background media work. Keep build-generated artifacts out of version control.

Any future Windows Gradle-driven work must use the user's shared `Local\Darka.AndroidGradleBuildGate` and prescribed resource profile. The S1 desktop baseline build uses no Gradle.

## Known decisions and risks before implementation

- Windows x64 is the confirmed S1 baseline. Additional platform coverage, naming/branding, and distribution channels remain to be selected; the current working identity is a Darkaxt VLC fork, not an official VideoLAN release.
- VLC 4 is experimental. Pin the build baseline and document subsequent upstream updates rather than claiming stability from a screenshot.
- Provider credentials and terms for R21 must be resolved before that integration. No provider account, payment or API key has been requested or created.
- Thumbnail generation, waveform extraction and subtitle cue access need implementation evidence. Existing library thumbnails and subtitle delay controls are useful components, not proof those workflows already exist.
- Qt Widgets and QML both require integration for complete dialog coverage. Native macOS and mobile interfaces are separate.
- There is no validated whole-project estimate. The original conversation's 40-120 hours must not become a delivery commitment. Estimate from the verified build and screen/behavior inventory before scheduling implementation.

## Source basis

The [source manifest](resources/upstream-source-manifest.json) pins inspected files and hashes. Relevant paths at the baseline are `modules/gui/qt/Makefile.am`, `maininterface/mainui.cpp`, `qt.cpp`, `player/player_controller.hpp`, `player/qml/SliderBar.qml`, `player/qml/TracksPageSubtitle.qml`, `player/qml/controlbarcontrols/ReverseButton.qml`, `medialibrary/thumbnailcollector.cpp` and `dialogs/toolbar/controlbar_profile.hpp` under the Qt directory, plus `doc/BUILD-win32.md` and `modules/gui/Makefile.am`. See [upstream Windows build guidance](https://github.com/videolan/vlc/blob/392bc1d0abdb7396b6c97fef206efa1d23868e19/doc/BUILD-win32.md) and [experimental nightlies](https://nightlies.videolan.org/).
