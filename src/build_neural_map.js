#!/usr/bin/env node
// THE ARCHITECTURE — neural map build step. THIS is the generator the site actually uses.
//
//   node src/build_neural_map.js
//
// Reads  src/map_source.json   (the canonical node/edge tables — edit this)
// Runs   src/mapgen.js         (buildMap: layout, edge grading, label relaxation)
// Writes src/neural_svg.frag   ─┐ copied to site/map/svg.frag  and site/map/data.json
//        src/neural_data.json  ─┘ by build_site3.py on the next build
//
// Node 18+. No dependencies, no network. Run it BEFORE build_site3.py whenever
// map_source.json changes; then update the counts, "data state" date, window chips
// and week ledger in src/neural_map.html by hand — those are prose, not generated.
//
// NOTE: src/build_neural_map.py is a LEGACY artifact with hardcoded tables. It does not
// read map_source.json and does not write these two files. Do not use it. See its header.

const fs = require("fs");
const path = require("path");

const SRC = __dirname;
const mapgen = fs.readFileSync(path.join(SRC, "mapgen.js"), "utf8");
eval(mapgen); // mapgen.js is a bare function declaration, by design (no imports/exports)

const source = JSON.parse(fs.readFileSync(path.join(SRC, "map_source.json"), "utf8"));
const { svg, data } = buildMap(source);

fs.writeFileSync(path.join(SRC, "neural_svg.frag"), svg);
fs.writeFileSync(path.join(SRC, "neural_data.json"), JSON.stringify(data));

const nodes = Object.keys(data.nodes).length;
const edges = data.edges.length;
const flagged = Object.entries(data.nodes)
  .filter(([, v]) => v.flag)
  .map(([k, v]) => `${k}:${v.flag}`);

console.log(
  `neural map: ${nodes} nodes, ${edges} edges, data state ${data.current}` +
    ` (svg ${svg.length.toLocaleString()} B)`
);
console.log(`flagged this window: ${flagged.length ? flagged.join(" ") : "none"}`);
console.log(
  `now update src/neural_map.html: "${nodes} nodes · ${edges} edges", the data-state date` +
    ` (${data.current}), the window chips, and the week ledger.`
);
