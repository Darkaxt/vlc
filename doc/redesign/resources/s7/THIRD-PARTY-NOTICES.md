# Modern VLC Fork attribution and notices

This is an independent modified VLC fork. VideoLAN and the original designers
do not endorse it. VLC, libVLC, the cone artwork and their original authorship
remain credited to VideoLAN and the contributors identified in `AUTHORS` and
`THANKS`. Preserve the complete `COPYING`, `COPYING.LIB`, per-file and dependency
notices with the distributed package and corresponding source. Different
components retain their respective licenses; this notice does not relicense them.

The redesigned interface follows **VLC Redesign by Juxtopposed**, from
[the original Figma Community file](https://www.figma.com/community/file/1691465999134370980/vlc-redesign),
under [Creative Commons Attribution 4.0](https://creativecommons.org/licenses/by/4.0/).
Changes include implementation as responsive native Qt/QML, extracting outlined
SVG geometry and affine transforms, native control/state integration and rendering
adjustments documented in the design manifest. The original archive SHA-256 is
`86637a31ad4ffbcaddc89244e0588df2c0cbe0954a6fe87c7bf5b6a65345e49e`.
Reference photographs/screenshots are retained for design inspection and are not
promoted into new production media. The production resource inventory records
each extracted vector's source node and hash.

**Inter** is by The Inter Project Authors, retained from
[rsms/inter](https://github.com/rsms/inter) revision
`353b61b9f4430d5f420d56605a6e7993e0941470`. The unmodified variable font is
distributed under the SIL Open Font License 1.1. Preserve its full license from
`modules/gui/qt/fonts/redesign/LICENSE.txt` with the binary package.

The optional classic-skin **Delicious** font is by Jos Buivenga / exljbris.
Font bytes are not included in this release. First-run setup can retrieve the
unmodified 2021 Regular font directly from the publisher for the active user's
profile. Its source and usage terms are linked in the wizard:
[Delicious](https://www.exljbris.com/delicious.html),
[font license](https://www.exljbris.com/eula.html). The distributed default skin
uses VLC's existing GPL FreeSans fallback when the validated user font is absent.
The package retains FreeSans's embedded copyright/license statements and the
full applicable GPL text. The HRTF data retains its embedded 3D Sound Labs
LGPL-2.1-or-later notice and full LGPL text.

The unchanged upstream `VLCIcons.ttf` is generated from VLC's retained glyph
manifest and sources. Its Fluent-named glyphs derive from Microsoft's
[Fluent System Icons](https://github.com/microsoft/fluentui-system-icons), under
the MIT license, copyright 2020 Microsoft Corporation. Preserve the complete
adjacent `FLUENT-ICONS-LICENSE.txt`. The source inventory lists the actual VLC
glyph inputs; no newly downloaded Fluent artwork replaces those pinned inputs.

The combined Qt 6 application is conveyed under GNU GPL version 3, exercising
the applicable later-version permissions of VLC's GPL-2.0-or-later components.
Original component licenses remain in their sources and accompanying notices.
Preserve the complete GPLv3 text alongside the original GPLv2/LGPL texts.
Qt's applicable licensing is documented in the
[Qt 6.8 licensing reference](https://doc.qt.io/qt-6.8/licensing.html);
the [GNU compatibility FAQ](https://www.gnu.org/licenses/gpl-faq.html#AllCompatibility)
explains later-version combinations. The source package includes the actual
library sources, maintained patches and build/relink instructions; the portable
application adds no signing or device-activation restriction on a rebuilt copy.

The final package must also contain notices extracted from its actual dependency
sources, including the exact rebuilt Qt, MinGW/winpthreads and pupnp versions.
The dependency/source manifest and release identity are separate final gates;
this file alone does not establish completed package compliance or delivery.

Some upstream source bundles keep their grants inside headers rather than named
LICENSE files. The notice inventory explicitly retains the actual AMD AMF,
Blackmagic DeckLink, NVIDIA codec and Lua license-bearing source headers.
Fetched fxc2 shader-compiler and WiX installer-tool bundles are host tools and
are excluded from both application binary and corresponding-library source
archives. fxc2's pinned tree carries no standalone grant and includes Microsoft
compiler DLLs; no right to republish that bundle is inferred from its public URL.
Its pinned retrieval/build rules remain in the application source. This changes
no playback capability and does not omit a linked library's corresponding source.
