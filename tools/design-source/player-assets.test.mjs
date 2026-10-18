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
