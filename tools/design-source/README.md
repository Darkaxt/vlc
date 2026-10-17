# Bounded VLC design-source tooling

This D1 tool reads the [canonical Figma archive](../../doc/redesign/resources/vlc-redesign.fig) without Figma credentials. It exports the two screens and three icon variants in [selection.json](selection.json). The existing [inventory](../../doc/redesign/resources/design-inventory.json) identifies all registered component sets and main icon variants; the tests check their IDs and names against a fresh decode.

With Node.js 24.13.0 or a compatible newer runtime, from this directory:

```powershell
npm ci --ignore-scripts --no-audit --no-fund
npm test
npm run export -- ./output/d1
```

Dependency installation requires the npm registry or an existing cache. Subsequent decoding/rendering uses local files; default CDN font loading is disabled. `VLC_DESIGN_MODULES` may point to a separate directory containing the locked dependencies for validation outside the checkout. The output directory must be supplied explicitly. Generated outputs are ignored by Git, and the original archive is never rewritten.

The workflow checks the source SHA-256, decodes the embedded Kiwi schema and Zstandard message, checks semantic round-trip and parent identities, resolves saved paint/effect styles, and expands only selected instances using full override paths and component swaps. It passes that bounded in-memory document to the published renderer. There are no patched dependencies. Each exported file receives a source node ID, original dimensions, format and SHA-256 in `export-manifest.json`; PNG dimensions also record effects extending outside the source frame.

Dependencies are pinned with integrity hashes: [kiwi-schema](https://github.com/evanw/kiwi) 0.5.0, [fflate](https://github.com/101arrowz/fflate) 0.8.2, and [@grida/refig](https://github.com/gridaco/grida/tree/main/packages/grida-canvas-sdk-render-figma) 0.0.7, with its locked canvas WASM dependency. The three direct packages publish MIT licenses; canvas WASM publishes Apache-2.0. Retain dependency notices if redistributing tooling. Design attribution and separate production-asset licensing remain governed by the [resource policy](../../doc/redesign/resources/README.md).

## Verified scope and limits

On 17 October 2026, a clean locked dependency installation passed the source/negative-control/style/override-path tests. Exporting with global `fetch` replaced by a throwing function succeeded in 11.09 seconds: player PNG 1920×1080, settings PNG 1138×955 (1048×865 body plus effects), and three 24×24 icons in SVG and PNG. The SVGs contain vector paths, without image elements or external resources.

Visual inspection against the hosted native Figma frames confirmed the selected player composition, image, light styles, sidebar and control sequence, and the settings layout, groups, colors and component choices. Differences remain in font metrics/weight, blur/shadow appearance, and some icon placement/orientation or clipping, including the settings Advanced Options chevron. This is a validated comparison with recorded limitations, not a pixel-fidelity claim or full editable-project reconstruction. No exhaustive renderer coverage is established for other screens.

Use the original decoded geometry and component metadata for later VLC implementation. Check icons affected by transforms or clipping against native Figma and export those directly there when necessary. Keep [hosted Figma access](https://www.figma.com/design/aZeRFRJVMwWl1uNS4I0Hdg/VLC-Redesign--Community-) for this fallback. Do not promote a screen PNG into application UI or assume these reference exports have passed the production asset audit.

Selected renderings and native comparison screenshots may be retained locally under `output/d1`; no bulk PDF, screen export archive, decoded document copy or raster backup is committed.
