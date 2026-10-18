// Bounded production-icon extraction for the archived VLC player design.
// Uses saved, already outlined geometry and full affine transforms; no renderer
// decomposition, font substitution, canvas background or Figma network access.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { decode, expandSelection, resolveStyleReferences, hash, id } from './export.mjs';

export const icons = [
  ['45:18', 'previous'], ['45:12', 'next'], ['44:419', 'play'],
  ['44:427', 'pause'], ['42:398', 'subtitles'], ['44:407', 'audio'],
  ['217:191', 'queue'], ['182:179', 'volume'], ['182:198', 'muted'],
  ['48:54', 'fullscreen'], ['187:322', 'stop'], ['45:40', 'close'],
  ['48:46', 'minimize'], ['48:51', 'maximize'], ['2230:9222', 'tools'],
  ['51:808', 'folder'], ['48:57', 'vlc'], ['247:418', 'more'],
  ['87:1041', 'sidebar'],
  ['463:564', 'sort'], ['463:560', 'remove'], ['463:550', 'add'],
  ['187:470', 'repeat'], ['187:474', 'shuffle'], ['463:417', 'move'],
  ['2127:7548', 'bookmarks'], ['2127:7531', 'chapters'], ['2127:7523', 'queue-tab'],
  ['999:4810', 'video'], ['494:2394', 'choice-selected'], ['494:2400', 'choice-empty'],
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
  const { document } = expandSelection(decoded.document, icons.map(([key]) => key));
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
          paths.push(`<rect x="${inset}" y="${inset}" width="${node.size.x - inset * 2}" height="${node.size.y - inset * 2}" rx="${Math.max(0, (node.cornerRadius ?? 0) - inset)}" fill="${stroke ? 'none' : 'white'}" stroke="${stroke ? 'white' : 'none'}" stroke-width="${weight}" opacity="${opacity}"/>`);
        }
        continue;
      }
      for (const paint of visiblePaints) for (const geometryPath of node[geometry] ?? []) {
        const blob = document.blobs[geometryPath.commandsBlob - (document.blobBaseIndex ?? 0)];
        if (!blob?.bytes) throw new Error('Missing saved path geometry');
        const opacity = (paint.opacity ?? 1) * (paint.color?.a ?? 1);
        paths.push(`<path fill="white" fill-opacity="${opacity}" fill-rule="${geometryPath.windingRule === 'ODD' ? 'evenodd' : 'nonzero'}" d="${pathCommands(blob.bytes)}"/>`);
      }
    }
    const nested = (children.get(id(node.guid)) ?? []).map(render).join('');
    if (!paths.length && !nested && node.type !== 'FRAME')
      throw new Error(`Selected icon has unsupported drawable: ${node.name} (${node.type})`);
    return `<g transform="${affine(node.transform)}" opacity="${node.opacity ?? 1}">${paths.join('')}${nested}</g>`;
  };
  fs.mkdirSync(destination, { recursive: true });
  const exported = icons.map(([key, name]) => {
    const root = nodes.get(key);
    if (!root) throw new Error(`Missing selected icon ${key}`);
    // A symbol's fill is its Figma editing canvas, not part of the icon.
    const content = (children.get(key) ?? []).map(render).join('');
    const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${root.size.x}" height="${root.size.y}" viewBox="0 0 ${root.size.x} ${root.size.y}">${content}</svg>\n`;
    const filename = `${name}.svg`;
    fs.writeFileSync(path.join(destination, filename), svg);
    return { id: key, name: root.name, filename, width: root.size.x, height: root.size.y, sha256: hash(svg) };
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
  const manifest = { source_sha256: hash(bytes), extraction: 'Saved outlined paths with nested affine matrices; white masks and original volume gradient.', icons: exported, controls };
  fs.writeFileSync(path.join(destination, 'manifest.json'), `${JSON.stringify(manifest, null, 2)}\n`);
  return manifest;
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  if (!process.argv[2]) throw new Error('Supply an explicit asset output directory');
  console.log(JSON.stringify(extractPlayerAssets(path.resolve(process.argv[2])), null, 2));
}
