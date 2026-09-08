// Exercise the actual map generator without a browser or third-party dependencies.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const root = path.resolve(__dirname, '..');
const context = {};
vm.runInNewContext(fs.readFileSync(path.join(root, 'src/mapgen.js'), 'utf8'), context);
const original = JSON.parse(fs.readFileSync(path.join(root, 'src/map_source.json'), 'utf8'));
const clone = () => JSON.parse(JSON.stringify(original));
const result = context.buildMap(original);
assert.equal(Object.keys(result.data.nodes).length, Object.keys(original.nodes).length);
assert.equal(result.data.edges.length, original.edges.length);
for (const [index, edge] of original.edges.entries()) {
  assert.equal(JSON.stringify(result.data.edges[index]), JSON.stringify({s:edge[0],t:edge[1],g:edge[2],l:edge[3]}));
}
const quoted = clone();
quoted.nodes.TRUMP.name = 'Quoted "name" <script> & record';
const rendered = context.buildMap(quoted).svg;
assert.ok(rendered.includes('aria-label="Quoted &quot;name&quot; &lt;script&gt; &amp; record — open dossier"'));
assert.ok(!rendered.includes('<script>'));
const mutations = [
  x => { x.nodes['BAD" onclick="x'] = x.nodes.TRUMP; },
  x => { x.nodes.TRUMP.x = Infinity; },
  x => { x.nodes.TRUMP.r = -1; },
  x => { x.edges.push(['MISSING','TRUMP','A','claimed link']); },
  x => { x.edges[0][2] = 'UNVERIFIED'; },
  x => { x.current = '2026-02-30'; },
];
for (const mutate of mutations) { const candidate=clone(); mutate(candidate); assert.throws(()=>context.buildMap(candidate)); }
const addition = clone();
addition.nodes.RESEARCH_ENTITY = {x:2200,y:1600,r:48,name:'New entity',sub:'Dated source record'};
addition.edges.push(['TRUMP','RESEARCH_ENTITY','O','test-only adjacency']);
const expanded = context.buildMap(addition);
assert.equal(expanded.data.edges.length, original.edges.length+1);
assert.equal(Object.keys(expanded.data.nodes).length, Object.keys(original.nodes).length+1);
assert.equal(JSON.stringify(expanded.data.edges.slice(0,-1)),JSON.stringify(result.data.edges));
console.log('Map generator: 9 cases passed (baseline, escaped identity, 6 rejected inputs, additive expansion).');
