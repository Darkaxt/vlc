// Bounded offline design-source preparation for the archived VLC design.
// Rendering uses the MIT-licensed @grida/refig; no Figma API or credentials.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { createRequire } from 'node:module';
import { createHash } from 'node:crypto';
import { inflateRawSync, deflateRawSync, zstdDecompressSync } from 'node:zlib';
import { isDeepStrictEqual } from 'node:util';

const here = path.dirname(fileURLToPath(import.meta.url));
// Validation can stage dependencies outside the maintained checkout.
const require = createRequire(process.env.VLC_DESIGN_MODULES
  ? path.join(path.resolve(process.env.VLC_DESIGN_MODULES), 'package.json')
  : import.meta.url);
const { unzipSync, zipSync } = require('fflate');
const kiwi = require('kiwi-schema');
export const selection = JSON.parse(fs.readFileSync(path.join(here, 'selection.json')));
export const hash = bytes => createHash('sha256').update(bytes).digest('hex');
export const id = guid => `${guid.sessionID}:${guid.localID}`;

export function decode(bytes, expected = selection.sha256) {
  if (hash(bytes) !== expected) throw new Error('Archive hash differs from the selected design source');
  const archive = unzipSync(bytes);
  const canvas = Buffer.from(archive['canvas.fig'] ?? []);
  if (canvas.toString('ascii', 0, 8) !== 'fig-kiwi' || canvas.readUInt32LE(8) !== 106)
    throw new Error('Expected the registered fig-kiwi version 106 source');
  const chunks = [];
  let offset = 12;
  while (offset < canvas.length) {
    if (offset + 4 > canvas.length) throw new Error('Truncated chunk header');
    const length = canvas.readUInt32LE(offset);
    offset += 4;
    if (offset + length > canvas.length) throw new Error('Truncated canvas chunk');
    chunks.push(canvas.subarray(offset, offset + length));
    offset += length;
  }
  if (chunks.length !== 2) throw new Error('Expected schema and document chunks');
  const codec = kiwi.compileSchema(kiwi.decodeBinarySchema(inflateRawSync(chunks[0])));
  const raw = zstdDecompressSync(chunks[1]);
  const document = codec.decodeMessage(raw);
  if (!isDeepStrictEqual(document, codec.decodeMessage(codec.encodeMessage(document))))
    throw new Error('Decoded message semantic round trip failed');
  const nodes = new Map(document.nodeChanges.map(node => [id(node.guid), node]));
  if (nodes.size !== document.nodeChanges.length) throw new Error('Duplicate node IDs');
  for (const node of nodes.values()) {
    if (node.parentIndex && !nodes.has(id(node.parentIndex.guid)))
      throw new Error(`Missing parent for ${id(node.guid)}`);
  }
  return { archive, codec, document, nodes, schemaChunk: chunks[0] };
}

export function resolveStyleReferences(document) {
  const nodes = new Map(document.nodeChanges.map(node => [id(node.guid), node]));
  let references = 0;
  const visit = value => {
    if (!value || typeof value !== 'object' || ArrayBuffer.isView(value)) return;
    for (const [field, property, sourceProperty] of [
      ['styleIdForFill', 'fillPaints', 'fillPaints'],
      ['styleIdForStrokeFill', 'strokePaints', 'fillPaints'],
      ['styleIdForEffect', 'effects', 'effects'],
    ]) {
      const reference = value[field]?.guid;
      if (reference) {
        // The saved format uses the all-ones GUID for an explicitly detached style.
        if (reference.sessionID === 0xffffffff && reference.localID === 0xffffffff) continue;
        const style = nodes.get(id(reference));
        if (!style) throw new Error(`Missing style ${id(reference)}`);
        if (style[sourceProperty] !== undefined) {
          // Serialized paint caches may lag behind the authoritative saved style.
          value[property] = structuredClone(style[sourceProperty]);
          references++;
        }
      }
    }
    for (const child of Object.values(value)) visit(child);
  };
  visit(document.nodeChanges);
  return references;
}

function chunk(bytes) {
  const length = Buffer.alloc(4);
  length.writeUInt32LE(bytes.length);
  return Buffer.concat([length, bytes]);
}

export function expandSelection(document, selectedIds) {
  const nodes = new Map(document.nodeChanges.map(node => [id(node.guid), node]));
  const children = new Map();
  for (const node of nodes.values()) {
    if (!node.parentIndex) continue;
    const parent = id(node.parentIndex.guid);
    if (!children.has(parent)) children.set(parent, []);
    children.get(parent).push(node);
  }
  for (const list of children.values()) list.sort((a, b) =>
    a.parentIndex.position < b.parentIndex.position ? -1 : a.parentIndex.position > b.parentIndex.position ? 1 : 0);
  const expanded = [];
  let serial = 1, swaps = 0, overridesApplied = 0;
  const apply = (node, scopes, target) => {
    let result = { ...node };
    for (const scope of scopes) {
      const key = [...scope.prefix, target].join('/');
      for (const override of scope.entries) {
        const address = override.guidPath?.guids?.map(id) ?? (override.guid ? [id(override.guid)] : []);
        if (address.join('/') === key) {
          result = { ...result, ...override };
          overridesApplied++;
        }
      }
    }
    return result;
  };
  const visit = (original, scopes, parent, componentStack, root = false) => {
    const originalId = id(original.guid);
    let node = apply(original, scopes, originalId);
    let descendants = children.get(originalId) ?? [];
    let nextScopes = scopes;
    let nextStack = componentStack;
    if (node.type === 'INSTANCE') {
      const componentId = id(node.overriddenSymbolID ?? node.symbolData.symbolID);
      const component = nodes.get(componentId);
      if (!component) throw new Error(`Missing component ${componentId}`);
      if (componentStack.includes(componentId)) throw new Error(`Component cycle at ${componentId}`);
      if (node.overriddenSymbolID) swaps++;
      const ownScopes = [
        { prefix: [], entries: node.symbolData?.symbolOverrides ?? [] },
        { prefix: [], entries: node.derivedSymbolData ?? [] },
      ];
      const componentRoot = apply(component, ownScopes, componentId);
      node = { ...componentRoot, ...node, type: 'FRAME' };
      // GUID paths contain instance hops and a leaf GUID, not every frame.
      // Outer scopes override this instance's defaults at the exact full path.
      nextScopes = [...ownScopes, ...scopes.map(scope => ({
        ...scope, prefix: [...scope.prefix, originalId],
      }))];
      descendants = children.get(componentId) ?? [];
      nextStack = [...componentStack, componentId];
    }
    const guid = root ? original.guid : { sessionID: 0xfffffffe, localID: serial++ };
    node = { ...node, guid, parentIndex: { guid: parent, position: original.parentIndex?.position ?? '!' } };
    if (node.type === 'SYMBOL') node.type = 'FRAME';
    delete node.symbolData;
    delete node.derivedSymbolData;
    delete node.overriddenSymbolID;
    delete node.guidPath;
    // Components are materialized with saved positions, not reflowed.
    expanded.push(node);
    for (const child of descendants) visit(child, nextScopes, guid, nextStack);
  };
  for (const selected of selectedIds) {
    const node = nodes.get(selected);
    if (!node) throw new Error(`Missing selected node ${selected}`);
    visit(node, [], { sessionID: 0, localID: 1 }, [], true);
  }
  const documentRoot = nodes.get('0:0'), page = nodes.get('0:1');
  if (!documentRoot || !page) throw new Error('Registered document/page roots missing');
  return { document: { ...document, nodeChanges: [documentRoot, page, ...expanded] }, swaps, overridesApplied, expandedNodes: expanded.length };
}

function preparedArchive(decoded) {
  const document = structuredClone(decoded.document);
  const styleReferences = resolveStyleReferences(document);
  const expanded = expandSelection(document, [...selection.screens, ...selection.icons].map(item => item.id));
  const header = Buffer.alloc(12);
  header.write('fig-kiwi');
  header.writeUInt32LE(106, 8);
  // Refig accepts deflate document chunks too. This is an in-memory adapter;
  // the canonical source and all embedded image bytes remain unchanged on disk.
  const canvas = Buffer.concat([header, chunk(decoded.schemaChunk), chunk(deflateRawSync(decoded.codec.encodeMessage(expanded.document)))]);
  return { bytes: zipSync({ ...decoded.archive, 'canvas.fig': canvas }, { level: 0 }), styleReferences,
    expansion: { nodes: expanded.expandedNodes, swaps: expanded.swaps, overrides: expanded.overridesApplied } };
}

export async function exportSelected(output) {
  fs.mkdirSync(output, { recursive: true });
  const started = performance.now();
  const source = fs.readFileSync(path.resolve(here, selection.archive));
  const decoded = decode(source);
  for (const item of [...selection.screens, ...selection.icons]) {
    const node = decoded.nodes.get(item.id);
    if (!node || node.size?.x !== item.width || node.size?.y !== item.height)
      throw new Error(`Selected node dimensions changed: ${item.id}`);
  }
  const prepared = preparedArchive(decoded);
  const entry = require.resolve('@grida/refig');
  const { FigmaDocument, FigmaRenderer } = await import(pathToFileURL(entry).href);
  const renderer = new FigmaRenderer(new FigmaDocument(prepared.bytes), {
    loadFigmaDefaultFonts: false, reflowAutoLayout: false,
  });
  const exported = [];
  try {
    for (const item of [...selection.screens, ...selection.icons]) {
      const formats = selection.screens.includes(item) ? ['png'] : ['svg', 'png'];
      for (const format of formats) {
        const { data } = await renderer.render(item.id, { format, width: item.width, height: item.height, scale: 1 });
        const filename = `${item.file}.${format}`;
        fs.writeFileSync(path.join(output, filename), data);
        const raster = format === 'png' ? Buffer.from(data) : null;
        exported.push({ ...item, filename, format, bytes: data.length, sha256: hash(data),
          ...(raster ? { rendered_width: raster.readUInt32BE(16), rendered_height: raster.readUInt32BE(20) } : {}) });
      }
    }
  } finally { renderer.dispose(); }
  const counts = {};
  for (const node of decoded.nodes.values()) counts[node.type] = (counts[node.type] ?? 0) + 1;
  const manifest = {
    source_sha256: hash(source), node_count: decoded.nodes.size,
    blob_count: decoded.document.blobs.length, node_types: counts,
    semantic_round_trip: true, resolved_style_references: prepared.styleReferences,
    materialized_instances: prepared.expansion,
    exported, runtime: process.version,
    export_elapsed_seconds: (performance.now() - started) / 1000,
    network: 'No network calls by this exporter; default CDN font loading disabled.',
    limitations: ['Font substitution, background blur and advanced paint/compositing may differ from native Figma. Native visual comparison must be reported separately from structural verification.'],
  };
  fs.writeFileSync(path.join(output, 'export-manifest.json'), `${JSON.stringify(manifest, null, 2)}\n`);
  return manifest;
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const output = process.argv[2];
  if (!output) throw new Error('Usage: node export.mjs <explicit-output-directory>');
  console.log(JSON.stringify(await exportSelected(path.resolve(output)), null, 2));
}
