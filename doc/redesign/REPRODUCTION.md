# Windows x64 reproduction and recovery

Current delivery is [Modern VLC Fork 1.1.0](https://github.com/Darkaxt/vlc/releases/tag/redesign-v1.1.0), application commit `c8a1cdfd31a97e7ecc0bda772d4148f1f87a6b26`. Its binary/source/checksums and independently downloaded native behavior are verified in [S8 final delivery](resources/s8/final-release.json). The original 1.0.0/S7 procedure below remains the preserved baseline; the S8 section records the source-bound MPV build and current retained binding.

The fork reuses VLC's engine and Qt frontend. It does not replace the installed
VLC or require MPV. The upstream application pin is
`392bc1d0abdb7396b6c97fef206efa1d23868e19`. Target Qt is 6.8.3; the image's host
qmake label is 6.8.0. The unchanged prebuilt archive and target headers retain
those distinct upstream identities. The image digest, complete input hashes,
source overlay and actual native runtime evidence bind each reproduction.

## Isolated environment

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
