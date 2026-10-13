# VLC redesign editable reference resources

Design by **Juxtopposed**: [VLC Redesign on Figma Community](https://www.figma.com/community/file/1691465999134370980/vlc-redesign), listed under [Creative Commons Attribution 4.0](https://creativecommons.org/licenses/by/4.0/). This bundle supports the [authoritative specification](../SPECIFICATION.md).

## Editable source and ongoing access

- [Original editable Figma archive](vlc-redesign.fig), 9,264,580 bytes
- [Working editable Figma copy in Darkaxt's drafts](https://www.figma.com/design/aZeRFRJVMwWl1uNS4I0Hdg/VLC-Redesign--Community-)
- [Original Community design](https://www.figma.com/community/file/1691465999134370980/vlc-redesign)
- [Archive contents and resource hashes](manifest.json)
- [Offline design inventory and decode verification](design-inventory.json)

The `.fig` file is a ZIP container. Its 46 entries comprise `canvas.fig`, `meta.json`, `thumbnail.png`, an `images/` directory entry and 42 embedded images (40 PNG, 2 JPEG). ZIP integrity and embedded image decoding were verified. The archive's SHA-256 is `86637a31ad4ffbcaddc89244e0588df2c0cbe0954a6fe87c7bf5b6a65345e49e`.

`canvas.fig` begins with the `fig-kiwi` signature (format version 106). Local inspection decoded the raw-DEFLATE schema and Zstandard document using the official [kiwi-schema](https://github.com/evanw/kiwi) package, version 0.5.0, and Node.js built-in decompression. The message contains 12,563 nodes, including 1,557 VECTOR and 1,954 TEXT nodes, plus 1,321 blobs, 38 component sets and 208 variants under the main Icon set. All node IDs were unique; parent references and vector geometry blob indices passed structural checks. Semantic encode/decode round-trip passed, while the re-encoded byte sequence differed. The original archive is preserved unchanged.

The [design inventory](design-inventory.json) records page and top-level node IDs, component/variant metadata, fonts, decoding provenance and verification limits. The complete decoded message is intentionally not duplicated in Git. No renderer, SVG exporter, pixel-fidelity validation or full editable-project reconstruction was implemented. Further offline extraction/reconstruction belongs to D1 and is **NOT STARTED** per the user's instruction.

The raster image entries are embedded assets, not a complete set of rendered UI screens. Custom vector paths exist in canvas nodes and geometry blobs, rather than standalone SVG entries. Keeping the intact archive preserves those design structures; extracting only `images/` would not preserve the complete editable source.

Keep the hosted editable file available as a reference and fallback for custom icon/component exports. Prefer the original vector/component data through a verified offline exporter or Figma, rather than reconstructing icons from PDF pixels. For each future production export, record component/node, variant, format, changes and attribution. The local `.fig` can be imported if hosted access becomes unavailable. Sign-in and sharing permissions remain managed by the account owner; no credentials, cookies or session data are stored here. The working-copy link does not make a private draft public.

The editable UI inspected during assessment included `Designs` and `Components` sections, Dark/Light color styles, blur/shadow effects, player and music variants, `Controls`, onboarding, profile, subtitle, shortcut, network, playlist and settings designs. The `Controls` component lists default, queue, subtitles, audio, video, video/audio/subtitle settings, waveform, playback, subtitle timeline, music, bookmarks and chapters variants. This is a representative UI inventory, not a claim of an exhaustive binary node audit.

## Resource policy

At the user's request, derivative PDF and PNG exports are omitted from Git. The original `.fig` and inventory are the canonical repository references. The user's supplied PDF and ZIP remain untouched in Downloads. Screenshots or vectors can be exported from the retained editable source when a concrete implementation requirement needs them; add only those necessary resources with provenance.

## Source provenance and reuse

[upstream-source-manifest.json](upstream-source-manifest.json) records selected inspected upstream files at `392bc1d0abdb7396b6c97fef206efa1d23868e19`. The creator's [video](https://www.youtube.com/watch?v=ERFeOgqk324) explains the interaction concept. Its complete transcript is not redistributed here.

Preserve creator attribution. Audit fonts, images, media and trademarks separately before promoting an export into production assets. Upstream VLC licenses and notices remain in their existing files; the design listing's CC BY license does not replace the code licenses. No raster assets have been extracted into a second repository copy and no design edits were made to the preserved archive.
