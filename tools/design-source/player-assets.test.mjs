import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {createHash} from 'node:crypto';
import { affine, pathCommands } from './player-assets.mjs';

test('selected player tabs preserve original two-tone panel instances', async () => {
  const {extractPlayerAssets}=await import('./player-assets.mjs');
  const output=process.env.VLC_DESIGN_TEST_OUTPUT;
  const manifest=extractPlayerAssets(output);
  for (const [filename,key] of [['tab-video.svg','2127:7755'],['tab-audio.svg','2127:7761'],['tab-subtitles.svg','2127:7699']]) {
    const entry=manifest.icons.find(icon=>icon.filename===filename);
    assert.equal(entry.id,key);
    assert.equal(entry.originalColors,true);
    const svg=fs.readFileSync(path.join(output,filename),'utf8');
    assert.match(svg,/rgb\((211,121,24|171,99,20)\)/);
    assert.match(svg,/rgb\((107,107,107|143,143,143)\)/);
    assert.doesNotMatch(svg,/<image|<text/);
  }
});

test('visualizer and EQ choices retain their original two-tone Figma artwork', async () => {
  const {extractPlayerAssets, equalizerIcons}=await import('./player-assets.mjs');
  const output=process.env.VLC_DESIGN_TEST_OUTPUT;
  assert.ok(output);
  const manifest=extractPlayerAssets(output);
  const visualizers=manifest.icons.filter(icon=>icon.filename.startsWith('visualizer-'));
  const resources=fs.readFileSync(new URL('../../modules/gui/qt/assets.qrc',import.meta.url),'utf8');
  const distribution=fs.readFileSync(new URL('../../modules/gui/qt/Makefile.am',import.meta.url),'utf8');
  assert.deepEqual(visualizers.map(icon=>icon.id), ['2138:8026','2139:8064','2139:8048','2139:8078']);
  for(const icon of [...visualizers, ...manifest.icons.filter(icon=>icon.filename.startsWith('eq-'))]) {
    assert.equal(icon.width,24);
    assert.equal(icon.height,24);
    assert.equal(icon.originalColors,true);
    assert.ok(resources.includes(`alias="${icon.filename}"`),icon.filename);
    assert.ok(distribution.includes('pixmaps/redesign/'+icon.filename),icon.filename);
    const svg=fs.readFileSync(path.join(output,icon.filename),'utf8');
    assert.match(svg,/fill="rgb\(143,143,143\)"/);
    if(icon.filename!=='eq-flat.svg') assert.match(svg,/fill="rgb\((211,121,24|171,99,20)\)"/);
    assert.doesNotMatch(svg,/<image|<text|scale\(14 -14\)/,'Extract only the original icon, not the dropdown label');
    const distributed=fs.readFileSync(new URL('../../modules/gui/qt/pixmaps/redesign/'+icon.filename,import.meta.url));
    assert.equal(createHash('sha256').update(distributed).digest('hex'),icon.sha256);
  }
  assert.deepEqual(manifest.icons.filter(icon=>icon.filename.startsWith('eq-')).map(icon=>icon.presetLabel),
    ['Flat','Classical','Club','Dance','Full base','Full base & treble','Full treble','Headphones','Large hall','Live','Party','Pop','Reggae','Rock','Ska','Soft','Soft rock','Techno']);
  assert.equal(equalizerIcons.length,18);
});

test('native settings reference existing, distributed original Qt icon resources', async () => {
  const {icons}=await import('./player-assets.mjs');
  assert.deepEqual(icons.find(([,name])=>name==='chevron-right'),['71:875','chevron-right']);
  const root=new URL('../../modules/gui/qt/',import.meta.url);
  const source=fs.readFileSync(new URL('dialogs/preferences/preferences.cpp',root),'utf8');
  const resources=fs.readFileSync(new URL('assets.qrc',root),'utf8');
  const distributed=fs.readFileSync(new URL('Makefile.am',root),'utf8');
  const manifest=JSON.parse(fs.readFileSync(new URL('pixmaps/redesign/manifest.json',root)));
  const records=[...manifest.icons,...manifest.controls,...manifest.nativeArrows];
  const names=[...source.matchAll(/:\/redesign\/icons\/([a-z0-9-]+\.svg)/g)].map(match=>match[1]);
  assert.ok(names.includes('chevron-right.svg'));
  for(const name of new Set(names)) {
    assert.ok(resources.includes(`alias="${name}"`),`Unregistered Qt resource: ${name}`);
    assert.ok(distributed.includes('pixmaps/redesign/'+name),`Missing distributed source: ${name}`);
    const bytes=fs.readFileSync(new URL('pixmaps/redesign/'+name,root));
    const record=records.find(record=>record.filename===name);
    assert.ok(record,`Missing original artwork provenance: ${name}`);
    assert.equal(createHash('sha256').update(bytes).digest('hex'),record.sha256,name);
  }
});

test('reference sidebar uses the outlined default component and colored menu variants retain provenance', async () => {
  const {icons}=await import('./player-assets.mjs');
  assert.deepEqual(icons.find(([,name])=>name==='sidebar'),['69:814','sidebar']);
  assert.deepEqual(icons.find(([,name])=>name==='menu-file'),['2461:9644','menu-file',true]);
});

test('inside-stroke icons preserve Figma contours with Qt-compatible masks', async () => {
  const {extractPlayerAssets}=await import('./player-assets.mjs');
  const output=process.env.VLC_DESIGN_TEST_OUTPUT;
  assert.ok(output);
  extractPlayerAssets(output);
  for(const name of ['video','sidebar']) {
    const svg=fs.readFileSync(path.join(output,`${name}.svg`),'utf8');
    assert.match(svg,/<mask id="inside-\d+" maskUnits="userSpaceOnUse" maskContentUnits="userSpaceOnUse"/);
    assert.match(svg,/<path fill="white" fill-rule="nonzero" d="M /);
    assert.match(svg,/<g mask="url\(#inside-\d+\)">/);
    assert.doesNotMatch(svg,/<clipPath|clip-path=/,'Qt 6.8 ignores clipPath');
  }
  const colored=fs.readFileSync(path.join(output,'menu-file.svg'),'utf8');
  const network=fs.readFileSync(path.join(output,'menu-network.svg'),'utf8');
  assert.doesNotMatch(network,/<mask /,'Open radio-wave contours must retain their complete saved outlines');
  assert.match(colored,/fill="rgb\(171,99,20\)"/,'the original file component orange detail is not flattened to a white mask');
  assert.match(colored,/fill="rgb\(143,143,143\)"/,'the original neutral stroke remains separate from the orange');
});

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
