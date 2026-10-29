# S7 evidence

S7 is ACTIVE under the user's 29 October 2026 instruction. This directory holds
compact source/package-bound evidence after it is inspected. Raw logs, private
profiles, native diagnostic tokens, compiler trees, temporary media and VM disks
remain in the registered `D:/Temp/vlc-s7-20261029` scratch and are cleaned after
their last consumer exits.

`asset-inventory.json` inventories the actual Qt resource sources. New production
SVGs match the retained Figma component/hash manifest; the unmodified Inter font
matches its pinned upstream bytes. Inherited media/font/icon inputs match the
VLC source pin. No Figma raster reference or synthetic test media is promoted to
new production artwork. This source audit does not by itself verify packaged
notices, corresponding dependency source, native presentation or final delivery.
The inventory also records the unchanged source glyphs used for `VLCIcons.ttf`
and the pinned readback of Microsoft's Fluent icon notice. Preserve
`THIRD-PARTY-NOTICES.md`, `FLUENT-ICONS-LICENSE.txt` and Inter's full OFL notice
with the final binary, alongside the actual dependency notices/source.

Reproduce the inventory with:

```powershell
python -B tools/windows-player/audit-release-assets.py --output D:/Temp/vlc-s7-20261029/evidence/asset-inventory.json
```

Current acceptance and exact next action remain in `../../PLAN.md`. Historical
failed or interrupted observations are preserved as failures, not substituted
for acceptance. Final release and independent package readback are required
before overall completion.

`native-integrated-verification.json` records complete native player/library,
input-path, font and prior-profile workflows. Its presentation PNGs are captures
of the running application for acceptance evidence, not derivative Figma exports
or production artwork. The player/preferences matrices were inspected at real
light/dark DPR 1, 1.5 and 2. The actual Greek catalog and native labels also pass.
Raw diagnostic snapshots and session credentials are excluded.

`native-pipe-red.json` and `native-pipe-green.json` show the actual cross-process
pipe collision and its correction. `specification-reconciliation.json` maps every
requirement to current/prior applicable evidence and explicitly retains the
remaining preservation/package/release gates. `native-copy-cleanup.json` records
applied exact-file tickets and independently absent spent runtime copies.
