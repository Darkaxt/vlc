// Bounded production-icon extraction for the archived VLC player design.
// Uses saved, already outlined geometry and full affine transforms; no renderer
// decomposition, font substitution, canvas background or Figma network access.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { decode, expandSelection, resolveStyleReferences, hash, id } from './export.mjs';

export const icons = [
  ['45:22', 'forward10'], ['45:28', 'backward10'],
  ['45:32', 'forward15'], ['45:36', 'backward15'],
  ['1919:9572', 'replay'], ['2115:7386', 'speed'],
  ['2115:7492', 'snapshot'], ['2127:7779', 'bookmark'],
  ['2146:9032', 'hdr'], ['2154:9680', 'zoom'], ['6073:14046', 'quit'],
  ['2139:8439', 'pip'],
  ['2430:14629', 'favorite'], ['2430:14666', 'favorite-active'],
  ['2437:14888', 'edit'],
  ['2139:8985', 'settings-info'], ['1803:2957', 'settings-general'], ['999:4960', 'settings-interface'],
  ['3046:10386', 'settings-privacy'], ['1089:4450', 'settings-controls'],
  ['2115:7482', 'settings-recording'], ['2516:9369', 'settings-extensions'],
  ['1803:2965', 'settings-general-active'], ['1088:4044', 'settings-interface-active'],
  ['3050:10424', 'settings-privacy-active'], ['1089:4464', 'settings-controls-active'],
  ['3180:17978', 'settings-playback-active'], ['1102:5055', 'settings-video-active'],
  ['496:2439', 'settings-audio-active'], ['467:497', 'settings-subtitles-active'],
  ['87:1031', 'settings-library-active'], ['477:1202', 'settings-network-active'],
  ['6571:16751', 'settings-recording-active'], ['2516:9375', 'settings-extensions-active'],
  ['45:18', 'previous'], ['45:12', 'next'], ['44:419', 'play'],
  ['44:427', 'pause'], ['42:398', 'subtitles'], ['44:407', 'audio'],
  ['217:191', 'queue'], ['182:179', 'volume'], ['182:198', 'muted'],
  ['48:54', 'fullscreen'], ['187:322', 'stop'], ['45:40', 'close'],
  ['48:46', 'minimize'], ['48:51', 'maximize'], ['2230:9222', 'tools'],
  ['51:808', 'folder'], ['48:57', 'vlc'], ['247:418', 'more'],
  ['69:814', 'sidebar'],
  ['2461:9644', 'menu-file', true], ['2461:9734', 'menu-folder', true],
  ['2461:9672', 'menu-network', true], ['2460:9552', 'menu-disc', true],
  ['2493:9342', 'menu-capture', true], ['2461:9628', 'menu-convert', true],
  ['2493:9246', 'menu-recent', true], ['2493:9300', 'menu-profile', true],
  ['2493:9253', 'menu-shortcuts', true], ['2493:9283', 'menu-customize', true],
  ['2493:9293', 'menu-settings', true], ['2461:9651', 'menu-info', true],
  ['6073:13944', 'tab-playback', true],
  // Export the selected panel instances, including their two-tone overrides.
  // The solid Global Settings variants have different artwork.
  ['2127:7755', 'tab-video', true], ['2127:7761', 'tab-audio', true],
  ['2127:7699', 'tab-subtitles', true],
  ['2138:8026', 'visualizer-spectrometer', true],
  ['2139:8064', 'visualizer-scope', true],
  ['2139:8048', 'visualizer-spectrum', true],
  ['2139:8078', 'visualizer-waveform', true],
  ['87:1026', 'home-active'], ['71:857', 'library-videos'], ['87:1015', 'library-videos-active'],
  ['71:851', 'library-music'], ['87:1009', 'library-music-active'],
  ['42:357', 'library-playlists'], ['858:5098', 'library-playlists-active'],
  ['2154:9699', 'recent'], ['477:1202', 'network-active'],
  ['6206:13629', 'albums'], ['858:5155', 'artists'], ['6191:13585', 'genres'],
  ['70:828', 'home'], ['70:833', 'network'], ['999:4806', 'music'],
  ['856:2147', 'search'], ['2107:6523', 'grid'], ['2107:6531', 'list'],
  ['71:890', 'back'], ['71:887', 'forward'], ['330:267', 'expand-library'],
  ['463:564', 'sort'], ['463:560', 'remove'], ['463:550', 'add'],
  ['187:470', 'repeat'], ['187:474', 'shuffle'], ['463:417', 'move'],
  ['2127:7548', 'bookmarks'], ['2127:7531', 'chapters'], ['2127:7523', 'queue-tab'],
  ['999:4810', 'video'], ['999:4802', 'playback'], ['71:868', 'chevron-down'], ['71:875', 'chevron-right'], ['494:2394', 'choice-selected'], ['494:2400', 'choice-empty'],
];

// Preset rows contain saved overrides of the EQ component. Export the icon
// instance from each original row so the individual curves and colors survive.
export const equalizerIcons = [
  ['2372:8493', 'flat'], ['2372:8494', 'classical'],
  ['2372:8495', 'club'], ['2372:8496', 'dance'],
  ['6114:14027', 'fullbass'], ['6114:14036', 'fullbasstreble'],
  ['6114:14045', 'fulltreble'], ['6114:14054', 'headphones'],
  ['6114:14063', 'largehall'], ['6114:14072', 'live'],
  ['6114:14081', 'party'], ['6114:14090', 'pop'],
  ['6114:14099', 'reggae'], ['6114:14108', 'rock'],
  ['6114:14117', 'ska'], ['6114:14126', 'soft'],
  ['6114:14135', 'softrock'], ['6114:14144', 'techno'],
];

export function pathCommands(bytes) {
  const data = Buffer.from(bytes);
  const commands = [];
  for (let offset = 0; offset < data.length;) {
    const kind = data[offset++];
    const count = [0, 2, 2, 4, 6][kind];
    if (count === undefined || offset + count * 4 > data.length)
      throw new Error('Invalid saved Figma path command');
    commands.push(['Z', 'M', 'L', 'Q', 'C'][kind]);
    for (let i = 0; i < count; i++, offset += 4) {
      const coordinate = data.readFloatLE(offset);
      if (!Number.isFinite(coordinate)) throw new Error('Invalid path coordinate');
      commands.push(String(coordinate));
    }
  }
  return commands.join(' ');
}

export function affine(transform) {
  const t = transform ?? { m00: 1, m01: 0, m02: 0, m10: 0, m11: 1, m12: 0 };
  return `matrix(${t.m00} ${t.m10} ${t.m01} ${t.m11} ${t.m02} ${t.m12})`;
}

export function extractPlayerAssets(destination) {
  const source = path.resolve(path.dirname(fileURLToPath(import.meta.url)),
    '../../doc/redesign/resources/vlc-redesign.fig');
  const bytes = fs.readFileSync(source);
  const decoded = decode(bytes);
  resolveStyleReferences(decoded.document);
  const { document } = expandSelection(decoded.document,
    [...new Set([...icons, ...equalizerIcons].map(([key]) => key))]);
  const nodes = new Map(document.nodeChanges.map(n => [id(n.guid), n]));
  const children = new Map();
  for (const node of nodes.values()) {
    const key = node.parentIndex && id(node.parentIndex.guid);
    if (!key) continue;
    if (!children.has(key)) children.set(key, []);
    children.get(key).push(node);
  }
  for (const list of children.values()) list.sort((a, b) =>
    a.parentIndex.position < b.parentIndex.position ? -1 : a.parentIndex.position > b.parentIndex.position ? 1 : 0);
  let preserveColors = false, clipSerial = 0;
  const paintColor = paint => preserveColors
    ? `rgb(${[paint.color.r, paint.color.g, paint.color.b].map(value => Math.round(value * 255)).join(',')})` : 'white';
  const render = node => {
    if (node.visible === false) return '';
    const paths = [];
    for (const [geometry, paints] of [['fillGeometry', 'fillPaints'], ['strokeGeometry', 'strokePaints']]) {
      const visiblePaints = (node[paints] ?? []).filter(p => p.visible !== false && (p.opacity ?? 1) !== 0);
      if (visiblePaints.length === 0) continue;
      if (visiblePaints.some(p => p.type !== 'SOLID'))
        throw new Error(`Non-monochrome paint in selected icon: ${node.name}`);
      if (node.type === 'RECTANGLE' || node.type === 'ROUNDED_RECTANGLE') {
        // Primitive geometry caches can predate resizing. Current dimensions,
        // radius and stroke alignment are authoritative in native Figma.
        const stroke = geometry === 'strokeGeometry';
        const weight = stroke ? node.strokeWeight ?? 0 : 0;
        const inset = !stroke ? 0 : node.strokeAlign === 'INSIDE' ? weight / 2 : node.strokeAlign === 'OUTSIDE' ? -weight / 2 : 0;
        for (const paint of visiblePaints) {
          const opacity = (paint.opacity ?? 1) * (paint.color?.a ?? 1);
          paths.push(`<rect x="${inset}" y="${inset}" width="${node.size.x - inset * 2}" height="${node.size.y - inset * 2}" rx="${Math.max(0, (node.cornerRadius ?? 0) - inset)}" fill="${stroke ? 'none' : paintColor(paint)}" stroke="${stroke ? paintColor(paint) : 'none'}" stroke-width="${weight}" opacity="${opacity}"/>`);
        }
        continue;
      }
      const outlined = [];
      for (const paint of visiblePaints) for (const geometryPath of node[geometry] ?? []) {
        const blob = document.blobs[geometryPath.commandsBlob - (document.blobBaseIndex ?? 0)];
        if (!blob?.bytes) throw new Error('Missing saved path geometry');
        const opacity = (paint.opacity ?? 1) * (paint.color?.a ?? 1);
        outlined.push(`<path fill="${paintColor(paint)}" fill-opacity="${opacity}" fill-rule="${geometryPath.windingRule === 'ODD' ? 'evenodd' : 'nonzero'}" d="${pathCommands(blob.bytes)}"/>`);
      }
      const contours = (node.fillGeometry ?? []).map(g => {
        const blob = document.blobs[g.commandsBlob - (document.blobBaseIndex ?? 0)];
        if (!blob?.bytes) throw new Error('Missing saved fill contour');
        return { windingRule: g.windingRule, commands: pathCommands(blob.bytes) };
      });
      // Open strokes have no fill interior. Their saved stroke outline is
      // already the centered result; masking it erases dividers/radio waves.
      const closedInterior = contours.length>0 && node.size.x>0 && node.size.y>0 && contours.every(({commands}) => {
        const starts=(commands.match(/(?:^| )M /g)??[]).length;
        return starts>0 && starts===(commands.match(/(?:^| )Z(?= |$)/g)??[]).length;
      });
      if (geometry === 'strokeGeometry' && node.strokeAlign === 'INSIDE' && outlined.length && closedInterior) {
        // Saved inside-stroke outlines straddle their contour. Figma clips
        // them to the fill shape; without that clip their apparent width and
        // bounds double (for example the clapperboard and sidebar outlines).
        const clip = `inside-${clipSerial++}`;
        const maskPaths = contours.map(g => {
          return `<path fill="white" fill-rule="${g.windingRule === 'ODD' ? 'evenodd' : 'nonzero'}" d="${g.commands}"/>`;
        }).join('');
        // Qt SVG 6.8 supports masks, but explicitly does not support clipPath.
        // Keep the exact original curves and mask the cached outline to its
        // contour, including a standard 10% mask-region antialiasing gutter.
        paths.push(`<defs><mask id="${clip}" maskUnits="userSpaceOnUse" maskContentUnits="userSpaceOnUse" x="${-node.size.x*0.1}" y="${-node.size.y*0.1}" width="${node.size.x*1.2}" height="${node.size.y*1.2}">${maskPaths}</mask></defs><g mask="url(#${clip})">${outlined.join('')}</g>`);
      } else paths.push(...outlined);
    }
    // Text-bearing S6 icons retain the original outlined glyph blobs too.
    // Their coordinates are em-normalized, Y-up from the saved baseline.
    // Use those bytes/positions instead of substituting or shaping a font.
    if(node.type==='TEXT' && !paths.length){
      const glyphs=node.derivedTextData?.glyphs;
      const paints=(node.fillPaints??[]).filter(p=>p.visible!==false&&(p.opacity??1)!==0);
      if(!glyphs?.length||paints.some(p=>p.type!=='SOLID'))throw new Error(`Missing supported saved glyph outlines: ${node.name}`);
      for(const glyph of glyphs){
        const blob=document.blobs[glyph.commandsBlob-(document.blobBaseIndex??0)];
        if(!blob?.bytes||(glyph.rotation??0)!==0||!Number.isFinite(glyph.fontSize))throw new Error(`Unsupported saved glyph: ${node.name}`);
        for(const paint of paints)paths.push(`<path fill="${paintColor(paint)}" fill-opacity="${(paint.opacity??1)*(paint.color?.a??1)}" transform="translate(${glyph.position.x} ${glyph.position.y}) scale(${glyph.fontSize} ${-glyph.fontSize})" d="${pathCommands(blob.bytes)}"/>`);
      }
    }
    // Figma saves the final boolean outline; its children are construction
    // operands. Redrawing them fills subtraction holes such as Home's doorway.
    const nested = node.type === 'BOOLEAN_OPERATION' && paths.length
      ? '' : (children.get(id(node.guid)) ?? []).map(render).join('');
    if (!paths.length && !nested && node.type !== 'FRAME')
      throw new Error(`Selected icon has unsupported drawable: ${node.name} (${node.type})`);
    return `<g transform="${affine(node.transform)}" opacity="${node.opacity ?? 1}">${paths.join('')}${nested}</g>`;
  };
  fs.mkdirSync(destination, { recursive: true });
  const selections = icons.map(([key, name, colored = false]) => ({key, name, colored, root: nodes.get(key)}));
  for (const [key, preset] of equalizerIcons) {
    const row = children.get(key) ?? [];
    const label = row.find(node => node.type === 'TEXT')?.textData?.characters;
    const root = row.find(node => node.name === 'Icon');
    if (!root || root.size.x !== 24 || root.size.y !== 24 || !label)
      throw new Error(`Missing saved equalizer row icon/label: ${key}`);
    selections.push({key, name: `eq-${preset}`, colored: true, root, label});
  }
  const exported = selections.map(({key, name, colored, root, label}) => {
    preserveColors = colored; clipSerial = 0;
    if (!root) throw new Error(`Missing selected icon ${key}`);
    // A symbol's fill is its Figma editing canvas, not part of the icon.
    const content = (children.get(id(root.guid)) ?? []).map(render).join('');
    const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${root.size.x}" height="${root.size.y}" viewBox="0 0 ${root.size.x} ${root.size.y}">${content}</svg>\n`;
    const filename = `${name}.svg`;
    fs.writeFileSync(path.join(destination, filename), svg);
    return { id: key, name: root.name, filename, width: root.size.x, height: root.size.y, ...(label ? {presetLabel:label} : {}), ...(colored ? {originalColors:true} : {}), sha256: hash(svg) };
  });
  // The cone is a saved vector, too. SVG keeps it usable with VLC's existing
  // renderer without introducing the separately packaged QtQuick.Shapes module.
  const cone = decoded.document.nodeChanges.find(n => id(n.guid) === '244:211');
  const fill = decoded.document.nodeChanges.find(n => id(n.guid) === '244:214');
  const geometry = node => node.fillGeometry.map(g => {
    const blob = decoded.document.blobs[g.commandsBlob - (decoded.document.blobBaseIndex ?? 0)];
    return pathCommands(blob.bytes);
  }).join(' ');
  const gradient = fill.fillPaints.find(p => p.type === 'GRADIENT_LINEAR');
  const rgb = c => `rgb(${[c.r, c.g, c.b].map(v => v * 255).join(',')})`;
  const stops = gradient.stops.map(s => `<stop offset="${s.position}" stop-color="${rgb(s.color)}" stop-opacity="${s.color.a}"/>`).join('');
  const paths = {
    'volume-cone.svg': `<path fill="white" d="${geometry(cone)}"/>`,
    // Figma's inner vector is inset 1.5px; its enclosing group is at y=-1.
    'volume-level.svg': `<defs><linearGradient id="level" x1="0%" x2="100%" y1="50%" y2="50%">${stops}</linearGradient></defs><g transform="translate(1.5 ${fill.transform.m12 - 1})"><path fill="url(#level)" d="${geometry(fill)}"/><path fill="black" fill-opacity="0.2" d="${geometry(fill)}"/></g>`,
  };
  const controls = Object.entries(paths).map(([filename, content]) => {
    const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="89" height="28" viewBox="0 0 89 28">${content}</svg>\n`;
    fs.writeFileSync(path.join(destination, filename), svg);
    return { ids: ['244:211', '244:214'], filename, sha256: hash(svg) };
  });
  // Native style sheets need a colored SVG rather than a runtime white mask.
  // Keep the saved chevron outline/matrices; only tint and orientation differ.
  const chevron = fs.readFileSync(path.join(destination, 'chevron-down.svg'), 'utf8');
  const nativeArrows = [];
  for (const [theme, color] of [['dark', '#8f8f8f'], ['light', '#2e2e2e']]) {
    for (const [direction, rotation] of [['down', 0], ['up', 180]]) {
      let svg = chevron.replaceAll('fill="white"', `fill="${color}"`);
      if (rotation) svg = svg.replace('>', `><g transform="rotate(${rotation} 12 12)">`).replace('</svg>', '</g></svg>');
      const filename = `native-chevron-${direction}-${theme}.svg`;
      fs.writeFileSync(path.join(destination, filename), svg);
      nativeArrows.push({ id: '71:868', filename, color, rotation, sha256: hash(svg) });
    }
  }
  const manifest = { source_sha256: hash(bytes), extraction: 'Saved outlined paths with nested affine matrices; white masks and original volume gradient.', icons: exported, controls, nativeArrows };
  fs.writeFileSync(path.join(destination, 'manifest.json'), `${JSON.stringify(manifest, null, 2)}\n`);
  return manifest;
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  if (!process.argv[2]) throw new Error('Supply an explicit asset output directory');
  console.log(JSON.stringify(extractPlayerAssets(path.resolve(process.argv[2])), null, 2));
}
