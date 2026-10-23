import { test } from 'node:test';
import assert from 'node:assert/strict';
import { affine, pathCommands } from './player-assets.mjs';

test('preserve nested reflection without decomposing into a rotation', () => {
  assert.equal(affine({ m00: -1, m01: 0, m02: 24, m10: 0, m11: 1, m12: 0 }),
    'matrix(-1 0 0 1 24 0)');
});
test('decode the original cubic path and reject truncated geometry', () => {
  const bytes = Buffer.alloc(26);
  bytes[0] = 4;
  [1, 2, 3, 4, 5, 6].forEach((value, index) => bytes.writeFloatLE(value, index * 4 + 1));
  bytes[25] = 0;
  assert.equal(pathCommands(bytes), 'C 1 2 3 4 5 6 Z');
  assert.throws(() => pathCommands(bytes.subarray(0, 23)), /Invalid saved/);
  assert.throws(() => pathCommands([8]), /Invalid saved/);
});

// The offline screen renderer converted each reflection to a 180-degree
// rotation, leaving detached Home/Network fragments at the left edge.
// The production path must keep the original signed matrices at every level.
test('Home and Network use the archived reflected components', async () => {
  const { icons } = await import('./player-assets.mjs');
  assert.deepEqual(icons.filter(([id]) => ['70:828','70:833'].includes(id)),
    [['70:828','home'],['70:833','network']]);
  const { decode, id, resolveStyleReferences } = await import('./export.mjs');
  const fs = await import('node:fs');
  const decoded = decode(fs.readFileSync(new URL('../../doc/redesign/resources/vlc-redesign.fig', import.meta.url)));
  resolveStyleReferences(decoded.document);
  for (const key of ['70:829','70:830','70:834']) {
    const matrix = decoded.nodes.get(key).transform;
    assert.equal(matrix.m00 * matrix.m11 - matrix.m01 * matrix.m10, -1, key);
    assert.match(affine(matrix), /^matrix\(-1 0 0 1 /);
  }
});

test('filled Home uses the cached subtraction with its doorway cut out', async () => {
  const fs = await import('node:fs');
  const path = await import('node:path');
  const { extractPlayerAssets } = await import('./player-assets.mjs');
  const output = process.env.VLC_DESIGN_TEST_OUTPUT;
  assert.ok(output, 'Set VLC_DESIGN_TEST_OUTPUT to an explicit task-owned scratch directory');
  extractPlayerAssets(output);
  const svg = fs.readFileSync(path.join(output,'home-active.svg'),'utf8');
  assert.equal((svg.match(/<path /g) ?? []).length,1,'The saved boolean result is the final outline');
  assert.equal((svg.match(/<rect /g) ?? []).length,0,'Construction operands must not repaint the doorway');
});
