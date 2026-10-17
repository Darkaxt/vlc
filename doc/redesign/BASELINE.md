# Windows x64 baseline assessment

The [specification](SPECIFICATION.md) and [stage ledger](PLAN.md) govern S1. This baseline keeps VLC application source unchanged at `392bc1d0abdb7396b6c97fef206efa1d23868e19`. It introduces build/verification tooling and dependency corrections; redesigned controls remain outside S1.

The reproducible [Windows recipe](../../tools/windows-baseline/README.md) pins the official CI image, matching contrib archive, source history, compiler and runtime backport. GCC identifies as 14 POSIX. Target Qt package metadata and `qconfig.h` identify 6.8.3; host qmake and the archive's separate `qtcoreversion.h` report 6.8.0. These labels are recorded separately. The original contrib archive is unchanged.

The initial Autotools source build completed from 01:45:10Z to 02:26:36Z on 17 October 2026 (41 minutes 26 seconds), using two workers. The preliminary Meson/Wine compiler-sanity failure was isolated from the generated compiler executable, which passed on native Windows. The accepted baseline uses the source's GCC CI build route, with native Windows acceptance.

Native integration exposed two dependency issues. Four SRT/x265/GME plugins requested shared GCC unwind support, which VLC's secure dependency search could not load. Targeted static unwind linkage corrected their imports. Qt playback then reproduced a MinGW 12 process-detach deadlock; the accepted [upstream runtime fix](https://github.com/mingw-w64/mingw-w64/commit/a556c6943c442465dc9a051bc6d3a6d452df4a1d) was backported into an isolated runtime prefix. The Qt build configuration must be regenerated so libtool uses the corrected startup objects. Neither correction changes VLC source or weakens DLL loading security.

## Capability and state preservation

The [native inventory](resources/windows-baseline-inventory.json) records module roles and public configuration names/types, with raw and deduplicated counts kept separate. It excludes user values and internal/obsolete options. The [source inventory](resources/windows-baseline-source-inventory.json) records menus, dialog declarations and configuration-path implementation hashes. These references support later reachability reconciliation; they do not claim that every disc, device, extension or network workflow was tested.

S1 adds no application settings or migrations. VLC identities, keys, defaults, history/privacy behavior and reset semantics remain upstream's. Tests use a `portable` directory beside the staged executable, explicit user-data/cache paths on E:, ignored existing configuration and disabled media-library access. Private pre-existing profile snapshots remain outside Git; only the unchanged/changed result is retained. Later stages must define persistence, precedence, migration, reset and recovery for each new stored setting and preserve existing media, settings and privacy choices.

## Acceptance and limits

S1 is COMPLETE. [Fresh native acceptance](resources/windows-baseline-verification.json) passed at 03:42:46Z on 17 October 2026: the generated six-second H.264/AAC clip produced 151 displayed frames, 143 changing-frame transitions, 288,768 decoded audio sample frames and natural end-of-stream. The missing-file negative control failed as expected. Qt/Direct3D11 produced a first picture, released the input, finished its event loop and exited normally with code 0. Plugin-cache generation/inventory passed with no plugin-load errors. The installed profile files were unchanged. The inventory records 586 unique module roles and 1,750 unique public option keys; these are preservation references, not delivered-feature counts.

Recorded agent wall time from 01:11:49Z through acceptance was approximately 151 minutes, including first-run setup/downloads, compilation, dependency diagnosis/correction, documentation and native validation. Cleanup, commit and synchronization are subsequent delivery overhead. This does not estimate human labor or the time required for the redesigned UI. The initial build and affected plugin/Qt rebuilds were exercised; a second full clean build was not required or claimed.

Qt's minimized check uses dummy audio; decoded PCM is checked separately. Physical speaker output and complete interactive UX are outside this baseline's evidence. The public inventory excludes internal/obsolete parser flags. Remaining platform and device coverage belongs to the explicitly named later stages.

S2-S7 remain NOT STARTED. No installation, deployment, distribution or VLC application release is part of S1. Build files, toolchain storage, media, dumps and test profiles are expendable E: scratch; compact provenance, acceptance evidence and reproduction tools are intentional repository deliverables.

Cleanup completed at 04:09:58Z: transactional cleanup removed all 29.6 GB of reviewed scratch (859 members), the exact E: root is absent, and the temporary WSL registration is removed. The existing Ubuntu/Docker registrations remain. Content hashing/revalidation on exFAT made cleanup/delivery preparation approximately 27 minutes of additional elapsed time after acceptance; commit/synchronization follow. No generated player binaries or dumps are retained in Git.
