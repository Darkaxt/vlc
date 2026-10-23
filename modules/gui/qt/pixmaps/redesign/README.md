# VLC player design assets

These transparent SVG masks derive from Juxtopposed's **VLC Redesign**, licensed
under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Attribution and
editable reference links are in [the design resource index](../../../../../doc/redesign/resources/README.md).

The canonical archive is `doc/redesign/resources/vlc-redesign.fig`, SHA-256
`86637a31ad4ffbcaddc89244e0588df2c0cbe0954a6fe87c7bf5b6a65345e49e`.
[manifest.json](manifest.json) records each original component ID and output hash.
The source vectors have been converted to white masks for native light/dark
tinting; the Figma component canvas is omitted. Saved path geometry and nested
affine matrices are retained. Rectangle primitives use their current dimensions,
radius and stroke alignment, rather than potentially stale geometry caches.

Reproduce with the locked design-source dependencies and
`node tools/design-source/player-assets.mjs <explicit-output-directory>`.
Temporary dependencies and exports must use the task's E: scratch root.
The extraction does not use Figma credentials or the screen renderer.

The cone volume control uses saved vectors `244:211` and `244:214` in
`volume-cone.svg` and `volume-level.svg`, including the inner inset, gradient,
dark overlay and clipping. It uses VLC's existing SVG plugin.
Native appearance comparison remains separate from binary/path verification.

S4 adds the archived Home (`70:828`) and Network (`70:833`) components and the
library search/view/navigation masks. The offline screen renderer reduced a
reflected matrix to a rotation, producing detached Home/Network fragments near
the left edge. These screen renderings are unsuitable as an icon oracle. The
production SVGs retain every signed affine matrix; the source/reflection
regression checks bind these component IDs. Final native pixels still require
visual verification against the design contract.
