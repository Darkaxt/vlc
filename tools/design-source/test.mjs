import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { fileURLToPath } from 'node:url';
import { decode, expandSelection, resolveStyleReferences, selection } from './export.mjs';

const source = fs.readFileSync(fileURLToPath(new URL(selection.archive, import.meta.url)));
test('registered source decodes with original node/blob identities and semantic round trip', () => {
  const decoded = decode(source);
  assert.equal(decoded.nodes.size, 12563);
  assert.equal(decoded.document.blobs.length, 1321);
  for (const item of selection.screens) assert.equal(decoded.nodes.get(item.id).name, item.name);
  assert.equal(decoded.archive['images/263af3f5ba4e58ffff30f3d3e5872e3dcabf4dc1'][0], 0xff);
  const inventory = JSON.parse(fs.readFileSync(fileURLToPath(new URL('../../doc/redesign/resources/design-inventory.json', import.meta.url))));
  assert.equal(inventory.source_sha256, selection.sha256);
  assert.equal(inventory.component_sets.length, 38);
  assert.equal(inventory.icon_variants.length, 208);
  for (const item of [...inventory.component_sets, ...inventory.icon_variants, ...inventory.top_level_nodes]) {
    assert.equal(decoded.nodes.get(item.id)?.name, item.name, `Inventory node ${item.id}`);
  }
});

test('changed source is rejected rather than silently using stale selection IDs', () => {
  const changed = Buffer.from(source);
  changed[changed.length - 1] ^= 1;
  assert.throws(() => decode(changed), /Archive hash differs/);
});

test('saved light style overrides the dark serialized paint cache', () => {
  const decoded = decode(source);
  const topbar = decoded.nodes.get('2425:13626');
  const style = decoded.nodes.get('2425:13979');
  assert.ok(topbar.fillPaints[0].color.r < 0.2);
  assert.ok(style.fillPaints[0].color.r > 0.8);
  resolveStyleReferences(decoded.document);
  assert.deepEqual(topbar.fillPaints, style.fillPaints);
});

const guid = n => ({ sessionID: 1, localID: n });
const node = (n, type, parent, properties = {}) => ({ guid: guid(n), type, name: `node-${n}`,
  ...(parent === null ? {} : { parentIndex: { guid: parent, position: `${n}` } }), ...properties });
const paint = r => [{ type: 'SOLID', color: { r, g: 0, b: 1 - r, a: 1 } }];

test('full instance paths keep overrides on one of two repeated nested icons', () => {
  const data = { nodeChanges: [
    { guid: { sessionID: 0, localID: 0 }, type: 'DOCUMENT' },
    { guid: { sessionID: 0, localID: 1 }, type: 'CANVAS' },
    node(1, 'INSTANCE', { sessionID: 0, localID: 1 }, { symbolData: {
      symbolID: guid(4), symbolOverrides: [{ guidPath: { guids: [guid(2), guid(11), guid(21)] }, fillPaints: paint(1) }],
    } }),
    node(4, 'SYMBOL', { sessionID: 0, localID: 1 }),
    node(2, 'INSTANCE', guid(4), { symbolData: { symbolID: guid(10) } }),
    node(3, 'INSTANCE', guid(4), { symbolData: { symbolID: guid(10) } }),
    node(10, 'SYMBOL', { sessionID: 0, localID: 1 }),
    node(11, 'INSTANCE', guid(10), { symbolData: { symbolID: guid(20) } }),
    node(20, 'SYMBOL', { sessionID: 0, localID: 1 }),
    node(21, 'ROUNDED_RECTANGLE', guid(20), { fillPaints: paint(0) }),
  ] };
  const result = expandSelection(data, ['1:1']);
  const leaves = result.document.nodeChanges.filter(n => n.type === 'ROUNDED_RECTANGLE');
  assert.deepEqual(leaves.map(n => n.fillPaints[0].color.r), [1, 0]);
  assert.ok(result.document.nodeChanges.every(n => n.type !== 'INSTANCE'));
});
