#!/usr/bin/env node
'use strict';

const crypto = require('node:crypto');
const fs = require('node:fs');
const fsp = require('node:fs/promises');
const http = require('node:http');
const path = require('node:path');

const ROOT = path.resolve(__dirname, '..');
const SITE = path.join(ROOT, 'site');
const OUT = path.join(SITE, 'print');
const MANIFEST = path.join(OUT, 'manifest.json');
const PLAYWRIGHT = '/Users/zincdigital/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright';
const CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const CANONICAL_ORIGIN = 'https://the-architecture-neurals.vercel.app';
const MAX_RUNTIME_MS = 7 * 60 * 1000 + 30 * 1000;
const MIME = { '.css': 'text/css', '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json', '.svg': 'image/svg+xml', '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.woff2': 'font/woff2' };

function fail(message) { throw new Error(message); }
function sha256(buffer) { return crypto.createHash('sha256').update(buffer).digest('hex'); }
function posix(relativePath) { return relativePath.split(path.sep).join('/'); }
function slug(value) { return String(value).toLowerCase().replace(/[^a-z0-9_-]+/g, '-').replace(/^-+|-+$/g, ''); }
function outputFor(kind, id, route) {
  if (kind === 'map-entity') return `site/print/neural--entity--${slug(id)}.pdf`;
  if (kind === 'map-topic') return `site/print/neural--topic--${slug(id)}.pdf`;
  if (kind === 'synthesis') return `site/print/synthesis--view--${slug(id)}.pdf`;
  const name = route.replace(/^\//, '').replace(/\.html$/, '').replaceAll('/', '--') || 'index';
  return `site/print/${name}.pdf`;
}

async function walk(directory) {
  const results = [];
  for (const entry of await fsp.readdir(directory, { withFileTypes: true })) {
    const absolute = path.join(directory, entry.name);
    if (entry.isDirectory()) results.push(...await walk(absolute));
    else if (entry.isFile()) results.push(absolute);
  }
  return results;
}

async function sourceFingerprint() {
  const files = (await walk(SITE))
    .filter((file) => !file.startsWith(OUT + path.sep) && path.basename(file) !== '.DS_Store')
    .concat(__filename)
    .sort((a, b) => posix(path.relative(ROOT, a)) < posix(path.relative(ROOT, b)) ? -1 : 1);
  const inputs = [];
  let aggregate = '';
  for (const file of files) {
    const bytes = await fsp.readFile(file);
    const item = { path: posix(path.relative(ROOT, file)), sha256: sha256(bytes), bytes: bytes.length };
    inputs.push(item);
    aggregate += `${item.path}\0${item.sha256}\0${item.bytes}\n`;
  }
  return { algorithm: 'sha256', value: sha256(Buffer.from(aggregate, 'utf8')), inputs };
}

async function buildPlan() {
  const map = JSON.parse(await fsp.readFile(path.join(SITE, 'map', 'data.json'), 'utf8'));
  const research = JSON.parse(await fsp.readFile(path.join(SITE, 'research', 'data.json'), 'utf8'));
  if (!map.nodes || !Object.keys(map.nodes).length || !Array.isArray(map.edges) || !map.edges.length) fail('map/data.json is missing the relationship map');
  if (!Array.isArray(research.topics) || !research.topics.length) fail('research/data.json is missing the topics');
  const publicHtml = (await walk(SITE)).filter((file) => file.endsWith('.html') && !file.includes(`${path.sep}src${path.sep}`) && !file.startsWith(OUT + path.sep));
  const pages = publicHtml.sort().map((file) => {
    const relative = posix(path.relative(SITE, file));
    const route = `/${relative}`;
    const html = fs.readFileSync(file, 'utf8');
    const title = ((html.match(/<title>([^<]*)<\/title>/i) || [])[1] || relative).replace(/&amp;/g, '&');
    return { kind: 'page', route, title, output: outputFor('page', '', route) };
  });
  const entities = Object.entries(map.nodes).map(([id, node]) => ({ kind: 'map-entity', id, route: `/neural.html?entity=${encodeURIComponent(id)}`, title: `${node.name} — Full entity record — The Neural Map`, output: outputFor('map-entity', id) }));
  const topics = research.topics.map((topic) => ({ kind: 'map-topic', id: topic.id, route: `/neural.html?topic=${encodeURIComponent(topic.id)}`, title: `${topic.title} — Topic map — The Neural Map`, output: outputFor('map-topic', topic.id) }));
  const synthesisHtml = await fsp.readFile(path.join(SITE, 'synthesis.html'), 'utf8');
  const synthesis = [...synthesisHtml.matchAll(/data-view-tab="([^"]+)"[^>]*>([^<]+)<\/button>/g)].map((match) => ({kind:'synthesis',id:match[1],route:`/synthesis.html?view=${encodeURIComponent(match[1])}`,title:`${match[2]} — Synthesis view — The Architecture`,output:outputFor('synthesis',match[1])}));
  if (!synthesis.length) fail('No synthesis views found in the rendered page');
  const routes = [...pages, ...entities, ...topics, ...synthesis];
  if (new Set(routes.map((item) => item.route)).size !== routes.length) fail(`route plan is incomplete or duplicated (${routes.length} routes)`);
  return { canonicalOrigin: CANONICAL_ORIGIN, counts: { pages: pages.length, mapEntities: entities.length, mapTopics: topics.length, synthesis: synthesis.length }, routes, map, research, sourceFingerprint: await sourceFingerprint() };
}

function parseArgs() {
  const args = process.argv.slice(2);
  const onlyAt = args.indexOf('--only');
  return { plan: args.includes('--plan'), only: onlyAt >= 0 ? args[onlyAt + 1] : null };
}

function startServer() {
  const server = http.createServer(async (request, response) => {
    try {
      const pathname = decodeURIComponent(new URL(request.url, 'http://local').pathname);
      let candidate = pathname === '/' ? path.join(SITE, 'index.html') : path.join(SITE, pathname.replace(/^\/+/, ''));
      const resolved = path.resolve(candidate);
      if (!(resolved === SITE || resolved.startsWith(SITE + path.sep))) { response.writeHead(403).end('Forbidden'); return; }
      const stat = await fsp.stat(resolved).catch(() => null);
      if (stat && stat.isDirectory()) candidate = path.join(resolved, 'index.html');
      const bytes = await fsp.readFile(candidate);
      response.writeHead(200, { 'content-type': `${MIME[path.extname(candidate).toLowerCase()] || 'application/octet-stream'}; charset=utf-8`, 'cache-control': 'no-store' });
      response.end(bytes);
    } catch (error) {
      response.writeHead(error.code === 'ENOENT' ? 404 : 500, { 'content-type': 'text/plain' });
      response.end(error.code === 'ENOENT' ? 'Not found' : 'Server error');
    }
  });
  return new Promise((resolve, reject) => {
    server.once('error', reject);
    server.listen(0, '127.0.0.1', () => resolve({ server, origin: `http://127.0.0.1:${server.address().port}` }));
  });
}

function evidencePayload(item, plan) {
  const { map, research } = plan;
  const relationshipByEdge = new Map((research.relationships || []).map((entry) => [entry.mapEdgeIndex, entry]));
  const sourceById = new Map((research.sources || []).map((entry) => [entry.id, entry]));
  const claimById = new Map((research.claims || []).map((entry) => [entry.id, entry]));
  let indices = map.edges.map((_, index) => index);
  let heading = 'Complete relationship evidence ledger';
  let note = 'All relationships in the accumulated map are listed. Evidence grades and missing source links remain explicit.';
  if (item.kind === 'map-entity') {
    indices = indices.filter((index) => map.edges[index].s === item.id || map.edges[index].t === item.id);
    heading = `${map.nodes[item.id].name}: full entity record`;
    note = 'This PDF is the full entity record. Entity selection takes priority; secondary topic, grade, and edge filters are intentionally absent.';
  } else if (item.kind === 'map-topic') {
    const topic = research.topics.find((entry) => entry.id === item.id);
    const members = new Set(topic.entityIds || []);
    indices = indices.filter((index) => members.has(map.edges[index].s) && members.has(map.edges[index].t));
    heading = `${topic.title}: topic relationship evidence`;
    note = 'This topic view lists mapped relationships between entities assigned to the topic. Topic membership supports navigation and does not establish a factual or causal connection.';
  }
  return { heading, note, rows: indices.map((index) => {
    const edge = map.edges[index];
    const mapping = relationshipByEdge.get(index) || {};
    return { index, from: map.nodes[edge.s]?.name || edge.s, to: map.nodes[edge.t]?.name || edge.t, grade: edge.g, label: edge.l, reportHref: mapping.reportHref || '', claims: (mapping.claimIds || []).map((id) => claimById.get(id)).filter(Boolean), sources: (mapping.sourceIds || []).map((id) => sourceById.get(id)).filter(Boolean) };
  }) };
}

async function preparePage(page, item, plan, localOrigin) {
  const pageErrors = [];
  page.removeAllListeners('pageerror');
  page.on('pageerror', (error) => pageErrors.push(error.message));
  const response = await page.goto(localOrigin + item.route, { waitUntil: 'load', timeout: 45_000 });
  if (!response || !response.ok()) fail(`${item.route}: HTTP ${response && response.status()}`);
  await page.waitForFunction(() => !document.fonts || document.fonts.status === 'loaded', null, { timeout: 30_000 });
  if (item.kind === 'map-entity' || item.kind === 'map-topic' || item.route === '/neural.html') {
    await page.waitForFunction(() => document.querySelector('#nm-status') && !document.querySelector('#nm-status').textContent.includes('Loading relationships'), null, { timeout: 30_000 });
    if (item.kind === 'map-entity') await page.waitForFunction(() => document.querySelector('#nm-name')?.textContent.trim(), null, { timeout: 10_000 });
  }
  if (pageErrors.length) fail(`${item.route}: page error: ${pageErrors.join('; ')}`);
  const payload = item.kind.startsWith('map-') || item.route === '/neural.html' ? evidencePayload(item, plan) : null;
  await page.evaluate(({ item, payload, canonicalOrigin }) => {
    document.title = item.title;
    document.querySelectorAll('details').forEach((node) => { node.open = true; });
    if (payload) {
      const host = document.querySelector('#neural') || document.querySelector('main') || document.body;
      const section = document.createElement('section');
      section.id = 'print-complete-evidence';
      section.style.cssText = 'margin-top:2rem;border-top:2px solid #111;padding-top:1rem';
      const h2 = document.createElement('h2'); h2.textContent = payload.heading; section.append(h2);
      const note = document.createElement('p'); note.textContent = payload.note; section.append(note);
      payload.rows.forEach((row) => {
        const article = document.createElement('article'); article.style.cssText = 'break-inside:avoid;border-top:1px solid #aaa;padding:.7rem 0';
        const h3 = document.createElement('h3'); h3.textContent = `${row.from} → ${row.to}`; article.append(h3);
        const summary = document.createElement('p'); summary.textContent = `[${row.grade}] ${row.label}`; article.append(summary);
        row.claims.forEach((claim) => {
          const box = document.createElement('div');
          const p = document.createElement('p'); p.textContent = `${claim.status || 'record'} · ${claim.text || ''}`; box.append(p);
          if (claim.context) { const context = document.createElement('p'); context.textContent = claim.context; box.append(context); }
          article.append(box);
        });
        if (row.sources.length) row.sources.forEach((source) => {
          const p = document.createElement('p'); const a = document.createElement('a'); a.href = source.url; a.textContent = source.title; p.append(a);
          p.append(document.createTextNode(` — ${[source.publisher, source.publishedAt, source.locator].filter(Boolean).join(' · ')}`)); article.append(p);
        }); else { const missing = document.createElement('p'); missing.textContent = 'Record link not yet attached. The historical evidence grade is preserved.'; article.append(missing); }
        if (row.reportHref) { const p = document.createElement('p'); const a = document.createElement('a'); a.href = row.reportHref; a.textContent = 'Read report context'; p.append(a); article.append(p); }
        section.append(article);
      });
      host.append(section);
    }
    if (item.kind === 'synthesis') {
      const main = document.querySelector('main') || document.body;
      const marker = document.createElement('aside'); marker.style.cssText = 'border:1px solid #777;padding:.7rem;margin:0 0 1rem'; marker.textContent = `Selected synthesis view: ${item.title.replace(/ — Synthesis view.*/, '')}`; main.prepend(marker);
    }
    const canonicalPage = new URL(item.route, canonicalOrigin);
    document.querySelectorAll('a[href]').forEach((node) => {
      const raw = node.getAttribute('href');
      if (!raw || /^(mailto:|tel:|javascript:)/i.test(raw)) return;
      try {
        const resolved = new URL(raw, canonicalPage);
        node.setAttribute('href', resolved.origin === location.origin ? new URL(resolved.pathname + resolved.search + resolved.hash, canonicalOrigin).href : resolved.href);
      } catch (_) {}
    });
  }, { item: { kind: item.kind, id: item.id, route: item.route, title: item.title }, payload, canonicalOrigin: CANONICAL_ORIGIN });
  await page.emulateMedia({ media: 'print' });
  await page.evaluate(() => new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve))));
}

async function writeManifest(plan, completed) {
  const artifacts = [...completed.values()].sort((a, b) => a.route.localeCompare(b.route));
  const routes = Object.fromEntries(artifacts.map((item) => [item.route, { url: item.url, title: item.title, pages: item.pages, kind: item.kind, sha256: item.sha256, bytes: item.bytes }]));
  const manifest = { schemaVersion: 1, generatedAt: new Date().toISOString(), canonicalOrigin: CANONICAL_ORIGIN, sourceFingerprint: plan.sourceFingerprint, routes, artifacts };
  await fsp.mkdir(OUT, { recursive: true });
  const temporary = `${MANIFEST}.tmp`;
  await fsp.writeFile(temporary, JSON.stringify(manifest, null, 2) + '\n');
  await fsp.rename(temporary, MANIFEST);
}

async function main() {
  const started = Date.now();
  const args = parseArgs();
  if (!fs.existsSync(PLAYWRIGHT)) fail(`Playwright runtime missing: ${PLAYWRIGHT}`);
  if (!fs.existsSync(CHROME)) fail(`Chrome channel missing: ${CHROME}`);
  const plan = await buildPlan();
  if (args.plan) {
    process.stdout.write(JSON.stringify({ canonicalOrigin: plan.canonicalOrigin, counts: plan.counts, routes: plan.routes, sourceFingerprint: plan.sourceFingerprint }, null, 2) + '\n');
    return;
  }
  let selected = plan.routes;
  if (args.only) {
    const wanted = new Set(args.only.split(',').map((value) => value.trim()));
    selected = plan.routes.filter((item) => wanted.has(item.route) || wanted.has(path.basename(item.output, '.pdf')));
    if (selected.length !== wanted.size) fail(`--only did not uniquely match every requested route/name: ${args.only}`);
  }
  const { chromium } = require(PLAYWRIGHT);
  await fsp.mkdir(OUT, { recursive: true });
  const completed = new Map();
  if (fs.existsSync(MANIFEST)) {
    try { const previous=JSON.parse(await fsp.readFile(MANIFEST, 'utf8')); if (previous.sourceFingerprint?.value === plan.sourceFingerprint.value) { for (const item of previous.artifacts || []) completed.set(item.route,item); } } catch (_) {}
  }
  const { server, origin } = await startServer();
  const browser = await chromium.launch({ executablePath: CHROME, headless: true });
  const context = await browser.newContext();
  const liveAssetRequests = new Set();
  context.on('request', request => { if (request.url().startsWith(CANONICAL_ORIGIN + '/')) liveAssetRequests.add(request.url()); });
  let cursor = 0;
  let manifestQueue = Promise.resolve();
  const deadline = started + MAX_RUNTIME_MS;
  try {
    await Promise.all(Array.from({ length: Math.min(3, selected.length) }, async () => {
      const page = await context.newPage();
      while (cursor < selected.length) {
        if (Date.now() > deadline) fail(`hard runtime deadline reached after ${completed.size} incremental artifacts`);
        const item = selected[cursor++];
        const absolute = path.join(ROOT, item.output);
        await preparePage(page, item, plan, origin);
        await page.pdf({ path: absolute, format: 'Letter', printBackground: true, preferCSSPageSize: true, displayHeaderFooter: false, tagged: true });
        if (liveAssetRequests.size) fail('PDF rendering requested live assets instead of the current build: ' + [...liveAssetRequests].join(', '));
        const pdf = await fsp.readFile(absolute);
        if (pdf.length < 1_000 || !pdf.subarray(0, 5).equals(Buffer.from('%PDF-'))) fail(`${item.route}: invalid PDF output`);
        const pages = Math.max(1, (pdf.toString('latin1').match(/\/Type\s*\/Page\b/g) || []).length);
        const artifact = { kind: item.kind, route: item.route, url: '/' + posix(path.relative(SITE, absolute)), canonicalUrl: new URL(item.route, CANONICAL_ORIGIN).href, output: posix(path.relative(ROOT, absolute)), title: item.title, pages, sha256: sha256(pdf), bytes: pdf.length };
        completed.set(item.route, artifact);
        manifestQueue = manifestQueue.then(() => writeManifest(plan, completed));
        await manifestQueue;
        process.stderr.write(`PDF ${completed.size}/${selected.length}: ${item.route} -> ${artifact.output} (${pages} pages)\n`);
      }
      await page.close();
    }));
  } finally {
    await context.close().catch(() => {});
    await browser.close().catch(() => {});
    await new Promise((resolve) => server.close(resolve));
  }
  const finalFingerprint = await sourceFingerprint();
  if (finalFingerprint.value !== plan.sourceFingerprint.value) fail('Rendering inputs changed during PDF generation; regenerate before publishing');
  process.stderr.write(`PDF BUILD: generated ${selected.length} route(s) in ${((Date.now() - started) / 1000).toFixed(1)}s; manifest has ${completed.size} artifact(s)\n`);
}

main().catch((error) => { console.error(`PDF BUILD FAILED: ${error.stack || error.message}`); process.exitCode = 1; });
