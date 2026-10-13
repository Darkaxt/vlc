# VLC redesign stages and reconciliation

The [specification](SPECIFICATION.md) governs every stage. Current authorization covers **S0 only**. All product stages are **NOT STARTED**; none is ACTIVE, BLOCKED or COMPLETE. No product implementation, build, installation or release is authorized by this registration task.

| Stage | Status | Scope and requirement ownership | Acceptance evidence |
|---|---|---|---|
| S0 Specification and references | ACTIVE | R60 reference attribution/provenance; R63 repository registration | Fork parent verified; authoritative specification and plan committed; original Figma hash matches; every archive entry inventoried and embedded images decode; editable Figma access linked; derivative PDF/PNGs omitted; links resolve; uploaded files verified from remote Git objects. |
| D1 Design source readiness | NOT STARTED | R64; R60 export provenance | Reproduce offline decode; inventory required variants; export representative custom vector icons and validate representative screen reconstruction against the original; document unsupported features/Figma fallback. No renderer/export pipeline has been implemented. |
| S1 Unmodified baseline | NOT STARTED | R01, R02 baseline, R03 upstream capability inventory, R04 preservation contract | Platform scope resolved; reproducible upstream build and real playback; configuration/capability inventory; no redesign behavior required yet. |
| S2 Working redesigned player | NOT STARTED | R10-R14 player portion; R04 relevant persistence; R52 player quality | Real open -> playback -> seek -> subtitles/audio -> queue -> fullscreen/keyboard workflow; focus/hover/resize verification. |
| S3 Tracks effects and media tools | NOT STARTED | R15, R20-R25; R04 and R52 relevant behavior | Real thumbnail/waveform/timeline/matching/preset/filter/tool workflows; real provider boundary for R21; supported/unsupported input handling and persistence. |
| S4 Library and media entry | NOT STARTED | R30-R33 library/open portion; R04 and R52 relevant behavior | Real indexed library navigation -> enqueue -> playback; persistent pins/playlists/home; real network playlist and open actions. |
| S5 Preferences bookmarks and shortcuts | NOT STARTED | R03 capability reconciliation, R14 menu/resume completion, R33 conversion/streaming dialogs, R40-R43; R04 and R52 relevant behavior | Every upstream capability remains reachable; actual settings-key mapping and persistence; bookmark/chapter/hotkey/extension workflows. |
| S6 Customization and onboarding | NOT STARTED | R50-R51; R04 and R52 relevant behavior | Real layout editing/profile restore/reset and restart; onboarding skip/reopen; theme/accent behavior with existing settings. |
| S7 Integrated verification | NOT STARTED | R01-R04 final reconciliation; R52 complete interface quality; R60 production asset audit; R61-R62 | All product requirements and tracked deferrals resolved; real integrated matrix, reproducible package and recovery/upstream-sync instructions; verified completion commit. |

Execution order is S0 -> D1 -> S1 -> S2 -> S3 -> S4 -> S5 -> S6 -> S7. D1 is a preparatory design step before VLC product implementation; the user explicitly said not to start it now. The one-off source decoding inspection is feasibility evidence, not completion of D1. Cross-stage requirements are cumulative: each stage verifies its touched behavior; S7 reconciles the whole result. This does not permit a stage to omit its assigned acceptance criteria. Missing required behavior remains ordinary unfinished work or a concrete blocker, never implicit scope reduction.

## Current reconciliation

- S0 satisfied: upstream GitHub fork created; baseline pinned; source untouched; full specification and stage map written; original Figma archive and contents inventory preserved with attribution and editable-access links. Derivative exports are being removed from the repository under the user's revised resource policy. File and remote verification are pending until the registration commit is checked.
- S0 remaining: derivative-copy cleanup, resource integrity/link checks, commit/upload and remote verification.
- Product stages: no acceptance criterion has been verified by compilation or playback.
- Blockers: none for S0. Future platform/provider decisions are pre-implementation decision gates, not claims of currently blocked stages.
- Tracked deferrals: none. Later product scope has explicit stage ownership in the table; no ACTIVE product stage exists from which work has been deferred.

## Stage operation

Activate only one stage after implementation is authorized. Record acceptance criteria satisfied and remaining, blockers with their resolution conditions, and any tracked deferral with its exact later-stage owner and final verification. Close a stage only after inspected verification covers all its criteria. Prioritize the earliest actionable blocked required stage and retain the one-ACTIVE-stage limit.
