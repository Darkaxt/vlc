# Windows x64 reproduction and recovery

This is the S7 working recipe. S7 acceptance and release remain pending in
[PLAN.md](PLAN.md). The pinned inputs and original baseline are documented in
[the baseline recipe](../../tools/windows-baseline/README.md); its historical
E: examples do not override the current D: build-storage requirement.

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
a conflict. S8 is a separate proposed integration and is not part of this recipe.

After all consumers exit and required evidence/deliverables are preserved, stop
only the owned temporary distribution, review/inspect the exact cleanup manifest,
issue its separate ticket and apply it. Retire only the resulting empty WSL
registration. Verify unrelated bindings and the final installed-profile comparison.
