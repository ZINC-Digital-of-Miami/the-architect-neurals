const { chromium, request } = require('/Users/zincdigital/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs = require('fs');

const base = process.env.ARCH_TEST_BASE || 'http://127.0.0.1:8765';
fs.mkdirSync('.architecture/app-audit',{recursive:true});
let browser;
const canonical = 'https://the-architecture-neurals.vercel.app';
const out = { startedAt: new Date().toISOString(), checks: [], failures: [], console: [], responses: [], measurements: {} };
const ok = (name, pass, detail = {}) => {
  const row = { name, pass: !!pass, ...detail };
  out.checks.push(row);
  if (!pass) out.failures.push(row);
};
const settle = page => page.waitForTimeout(120);
const slug = s => s.replace(/[^a-z0-9]+/gi, '-').replace(/^-|-$/g, '').slice(0, 90);

(async () => {
  browser = await chromium.launch({ headless: true, executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' });
  const context = await browser.newContext({ viewport: { width: 1366, height: 900 }, reducedMotion: 'reduce' });
  const page = await context.newPage();
  page.on('console', msg => { if (msg.type() === 'error') out.console.push({ url: page.url(), type: 'console', text: msg.text() }); });
  page.on('pageerror', error => out.console.push({ url: page.url(), type: 'pageerror', text: error.message }));
  page.on('response', res => { if (res.status() >= 400 && res.url().startsWith(base)) out.responses.push({ url: res.url(), status: res.status() }); });

  await page.goto(base + '/', { waitUntil: 'domcontentloaded' });
  await page.locator('[data-ui-dropdown][aria-controls="topics-navigation"]').click();
  const navTopics = await page.locator('#topics-navigation a[href^="/topics/"]').evaluateAll(as => [...new Set(as.map(a => new URL(a.href).pathname))]);
  ok('root topic dropdown exposes exactly 15 unique topic routes', navTopics.length === 15, { count: navTopics.length, routes: navTopics });
  ok('root topic dropdown is actually open and its topic links are rendered', await page.locator('#topics-navigation').isVisible() && await page.locator('[data-ui-dropdown][aria-controls="topics-navigation"]').getAttribute('aria-expanded') === 'true');

  await page.locator('[data-ui-contents]').click();
  const contentsOpen = await page.locator('#contents-dialog').evaluate(d => d.open);
  const chapterLink = page.locator('#contents-dialog a[href*="#chapter-"]').first();
  const chapterHref = await chapterLink.getAttribute('href');
  const chapterId = new URL(chapterHref, base).hash.slice(1);
  for (const group of await chapterLink.locator('xpath=ancestor::details').all()) { if (!(await group.getAttribute('open'))) await group.locator(':scope > summary').click(); }
  await chapterLink.click();
  await settle(page);
  const chapterState = await page.evaluate(id => {
    const el = document.getElementById(id), d = document.getElementById('contents-dialog');
    return { hash: location.hash, focused: document.activeElement === el, dialogOpen: d.open, top: el?.getBoundingClientRect().top, exists: !!el };
  }, chapterId);
  ok('contents dialog opens', contentsOpen);
  ok('chapter link resolves, closes contents, updates hash, focuses and scrolls target', chapterState.exists && chapterState.hash === `#${chapterId}` && chapterState.focused && !chapterState.dialogOpen && chapterState.top >= 0 && chapterState.top < 200, { chapterId, ...chapterState });

  const laterId = await page.locator('h2[id],h3[id]').evaluateAll(es => (es.find(e => e.id.startsWith('chapter-21-q')) || es[Math.floor(es.length * .7)]).id);
  await page.evaluate(id => document.getElementById(id).scrollIntoView(), laterId);
  await settle(page);
  await page.locator('[data-ui-save]').click();
  const saved = await page.evaluate(() => ({ raw: localStorage.getItem('architecture:reading:/'), resumeHidden: document.querySelector('[data-ui-resume]').hidden, status: document.querySelector('[data-ui-status]').textContent }));
  const savedObject = JSON.parse(saved.raw);
  await page.evaluate(() => scrollTo(0, 0));
  await page.locator('[data-ui-resume]').click();
  await settle(page);
  const resumed = await page.evaluate(saved => {
    const el = document.getElementById(saved.id);
    const expected = Math.max(0, el.getBoundingClientRect().top + scrollY + saved.offset);
    return { scrollY, expected, focused: document.activeElement === el, status: document.querySelector('[data-ui-status]').textContent };
  }, savedObject);
  ok('save place writes page-scoped versioned storage and reveals Resume', savedObject.version === 1 && typeof savedObject.id === 'string' && Number.isFinite(savedObject.offset) && !saved.resumeHidden && /saved/i.test(saved.status), { saved: savedObject, status: saved.status });
  ok('resume returns to exact saved offset and focuses saved section', resumed.focused && Math.abs(resumed.scrollY - resumed.expected) <= 2 && /Returned/i.test(resumed.status), resumed);

  await page.goto(base + '/', { waitUntil: 'domcontentloaded' });
  await page.locator('.page-actions [data-ui-share]').click();
  const pageShare = await page.locator('#share-url').inputValue();
  await page.locator('[data-share-close]').click();
  const section = page.locator('h2[id]').filter({ has: page.locator('.section-share') }).first();
  const sectionId = await section.getAttribute('id');
  await section.locator('.section-share').click();
  const sectionShare = await page.locator('#share-url').inputValue();
  ok('page sharing emits exact canonical root URL', pageShare === canonical + '/', { actual: pageShare });
  ok('section sharing emits exact canonical fragment URL', sectionShare === `${canonical}/#${sectionId}`, { actual: sectionShare, sectionId });
  await page.locator('[data-share-close]').click();

  await page.goto(base + '/topics.html', { waitUntil: 'domcontentloaded' });
  const coverage = await page.locator('[data-topic-record]').evaluateAll(rows => rows.map(row => ({
    href: new URL(row.querySelector('a[href*="/topics/"]').href).pathname,
    title: row.querySelector('h2,h3')?.textContent.trim() || '',
    hidden: row.hidden
  })));
  const coverageRoutes = [...new Set(coverage.map(x => x.href))];
  ok('topics index has one visible record for every dropdown topic route', coverage.length === 15 && coverageRoutes.length === 15 && coverage.every(x => !x.hidden) && navTopics.every(x => coverageRoutes.includes(x)), { count: coverage.length, routes: coverageRoutes });
  const api = await request.newContext();
  for (const path of coverageRoutes) {
    const response = await api.get(base + path);
    const text = await response.text();
    ok(`topic route ${path} returns a substantive topic page`, response.status() === 200 && /<h1\b/i.test(text) && /\/research-ui\.js/.test(text), { status: response.status(), bytes: text.length });
  }
  await api.dispose();

  await page.goto(base + '/synthesis.html?view=overview', { waitUntil: 'domcontentloaded' });
  const viewIds = await page.locator('[data-view-tab]').evaluateAll(ts => ts.map(t => t.dataset.viewTab));
  const viewResults = [];
  for (const id of viewIds) {
    await page.locator(`[data-view-tab="${id}"]`).click();
    const state = await page.evaluate(id => ({
      selected: document.querySelector(`[data-view-tab="${id}"]`).getAttribute('aria-selected'),
      shown: [...document.querySelectorAll('[data-view]')].filter(v => !v.hidden).map(v => v.dataset.view),
      url: location.href
    }), id);
    viewResults.push({ id, ...state });
  }
  ok('synthesis switches all six views with one visible panel and URL state', viewIds.length === 6 && viewResults.every(x => x.selected === 'true' && x.shown.length === 1 && x.shown[0] === x.id && new URL(x.url).searchParams.get('view') === x.id), { views: viewResults });
  const deep = await page.locator('[data-view][hidden] [id]').first().evaluate(el => ({ id: el.id, view: el.closest('[data-view]').dataset.view }));
  await page.goto(`${base}/synthesis.html#${deep.id}`, { waitUntil: 'domcontentloaded' });
  await settle(page);
  const deepState = await page.evaluate(deep => ({ hash: location.hash, panelHidden: document.querySelector(`[data-view="${deep.view}"]`).hidden, selected: document.querySelector(`[data-view-tab="${deep.view}"]`).getAttribute('aria-selected'), targetVisible: !!document.getElementById(deep.id)?.getClientRects().length }), deep);
  ok('synthesis fragment deep link reveals the containing view', deepState.hash === `#${deep.id}` && !deepState.panelHidden && deepState.selected === 'true' && deepState.targetVisible, { deep, ...deepState });

  await page.goto(base + '/neural.html', { waitUntil: 'domcontentloaded' });
  await page.waitForFunction(() => !document.querySelector('#nm-status').textContent.includes('Loading') && document.querySelectorAll('#nm-entity-list [data-node]').length > 0);
  const mapInitial = await page.evaluate(() => ({ status: document.querySelector('#nm-status').textContent, topics: [...document.querySelector('#nm-topic').options].map(o => ({ value: o.value, text: o.textContent })), entities: document.querySelectorAll('#nm-entity-list [data-node]').length, nodes: document.querySelector('#nm-count').textContent }));
  const topicValue = mapInitial.topics.find(o => o.value)?.value;
  await page.selectOption('#nm-topic', topicValue);
  await settle(page);
  const mapTopic = await page.evaluate(() => ({ value: document.querySelector('#nm-topic').value, url: location.href, count: document.querySelectorAll('#nm-entity-list [data-node]').length, status: document.querySelector('#nm-status').textContent }));
  ok('map topic filter changes entities and persists exact topic in URL', mapTopic.value === topicValue && new URL(mapTopic.url).searchParams.get('topic') === topicValue && mapTopic.count < mapInitial.entities, { initial: mapInitial, filtered: mapTopic });
  await page.locator('#nm-reset').click();
  await page.locator('#nm-view-entities').click();
  const firstEntity = await page.locator('#nm-entity-list [data-node]').first().evaluate(el => ({ key: el.dataset.node, name: el.querySelector('.nm-entity-title').textContent.trim() }));
  await page.locator('#nm-search').fill(firstEntity.name);
  await settle(page);
  const searchState = await page.evaluate(() => ({ count: document.querySelectorAll('#nm-entity-list [data-node]').length, query: document.querySelector('#nm-search').value, status: document.querySelector('#nm-status').textContent }));
  ok('map search narrows the rendered entity list', searchState.query === firstEntity.name && searchState.count >= 1 && searchState.count < mapInitial.entities, { entity: firstEntity, ...searchState });
  await page.selectOption('#nm-grade', 'A');
  await page.locator('#nm-reset').click();
  const resetState = await page.evaluate(() => ({ search: document.querySelector('#nm-search').value, topic: document.querySelector('#nm-topic').value, grade: document.querySelector('#nm-grade').value, url: location.href, count: document.querySelectorAll('#nm-entity-list [data-node]').length }));
  ok('map reset clears search/topic/grade/selection and restores entity list', !resetState.search && !resetState.topic && !resetState.grade && !new URL(resetState.url).searchParams.has('entity') && !new URL(resetState.url).searchParams.has('topic') && !new URL(resetState.url).searchParams.has('grade') && resetState.count === mapInitial.entities, resetState);

  const candidates = [{key:'DONALD_TRUMP_JR',name:'Donald Trump Jr.'}];
  let evidenceResult = null;
  for (const candidate of candidates.slice(0, 25)) {
    await page.locator('#nm-entity-list [data-node]').filter({ hasText: candidate.name }).first().click();
    await page.locator('#nm-tab-evidence').click();
    const state = await page.evaluate(candidate => ({
      candidate,
      name: document.querySelector('#nm-name').textContent.trim(),
      entity: new URL(location.href).searchParams.get('entity'),
      edge: new URL(location.href).searchParams.get('edge'),
      evidenceVisible: !document.querySelector('#nm-panel-evidence').hidden,
      sourceLinks: [...document.querySelectorAll('#nm-panel-evidence a[href^="http"]')].map(a => a.href),
      synthesisLinks: [...document.querySelectorAll('#nm-panel-evidence a[href^="/synthesis"]')].map(a => a.href),
      panelText: document.querySelector('#nm-panel-evidence').textContent.trim().slice(0, 320)
    }), candidate);
    if (state.sourceLinks.length) { evidenceResult = state; break; }
    await page.locator('#nm-close').click();
  }
  ok('map entity selection opens a named dossier and persists entity URL', !!evidenceResult && evidenceResult.name.length > 0 && evidenceResult.entity === evidenceResult.candidate.key, evidenceResult || { testedCandidates: 25 });
  ok('map Evidence tab exposes the selected relationship with source and synthesis links', !!evidenceResult && evidenceResult.evidenceVisible && evidenceResult.sourceLinks.length > 0 && evidenceResult.synthesisLinks.length > 0, evidenceResult || { testedCandidates: 25 });
  if (evidenceResult) {
    const entityUrl = page.url();
    await page.reload({ waitUntil: 'domcontentloaded' });
    await page.waitForFunction(() => !document.querySelector('#nm-status').textContent.includes('Loading'));
    const deepEntity = await page.evaluate(() => ({ name: document.querySelector('#nm-name').textContent.trim(), evidenceVisible: !document.querySelector('#nm-panel-evidence').hidden, entity: new URL(location.href).searchParams.get('entity'), edge: new URL(location.href).searchParams.get('edge') }));
    ok('map entity/evidence deep URL survives reload', page.url() === entityUrl && deepEntity.entity === evidenceResult.entity && deepEntity.edge === evidenceResult.edge && deepEntity.evidenceVisible, { url: entityUrl, ...deepEntity });
    await page.locator('#nm-card [data-ui-share]').click();
    const mapShare = await page.locator('#share-url').inputValue();
    ok('map entity sharing preserves the exact entity/evidence URL on canonical host', mapShare === entityUrl.replace(base, canonical), { local: entityUrl, actual: mapShare, expected: entityUrl.replace(base, canonical) });
    await page.locator('[data-share-close]').click();
  }
  await page.locator('#nm-view-network').click();
  ok('reduced motion hides pulse control', !(await page.locator('#nm-motion').isVisible()));
  await page.emulateMedia({reducedMotion:'no-preference'});
  const pulseBefore = await page.locator('#nm-motion').textContent();
  await page.locator('#nm-motion').click();
  const pulsePaused = await page.evaluate(() => ({ text: document.querySelector('#nm-motion').textContent, pressed: document.querySelector('#nm-motion').getAttribute('aria-pressed'), paused: document.querySelector('#neural').classList.contains('is-pulse-paused') }));
  await page.locator('#nm-motion').click();
  const pulseAfter = await page.evaluate(() => ({ text: document.querySelector('#nm-motion').textContent, pressed: document.querySelector('#nm-motion').getAttribute('aria-pressed'), paused: document.querySelector('#neural').classList.contains('is-pulse-paused') }));
  ok('map pulse pause/resume changes state and restores it', /Pause/.test(pulseBefore) && pulsePaused.pressed === 'true' && pulsePaused.paused && /Resume/.test(pulsePaused.text) && pulseAfter.pressed === 'false' && !pulseAfter.paused && /Pause/.test(pulseAfter.text), { before: pulseBefore, paused: pulsePaused, after: pulseAfter });

  const sweepRoutes = ['/', '/topics.html', '/synthesis.html', '/neural.html', '/sources.html', ...coverageRoutes, ...JSON.parse(fs.readFileSync('site/research/data.json','utf8')).briefs.map(b=>b.url)];
  const overflow = [];
  for (const width of [319, 390, 1366]) {
    await page.setViewportSize({ width, height: width < 500 ? 760 : 900 });
    for (const path of sweepRoutes) {
      await page.goto(base + path, { waitUntil: 'domcontentloaded' });
      if (path === '/neural.html') await page.waitForFunction(() => !document.querySelector('#nm-status').textContent.includes('Loading'));
      const m = await page.evaluate(() => ({ innerWidth, rootWidth: document.documentElement.scrollWidth, bodyWidth: document.body.scrollWidth, clientWidth: document.documentElement.clientWidth }));
      const pass = m.rootWidth <= m.clientWidth && m.bodyWidth <= m.clientWidth;
      overflow.push({ width, path, pass, ...m });
      if (!pass) await page.screenshot({ path: `.architecture/app-flow-overflow-${width}-${slug(path || 'root')}.png`, fullPage: true });
    }
  }
  ok('no horizontal document overflow across all 23 routes at 319, 390, and 1366 px', overflow.every(x => x.pass), { measured: overflow.length, failures: overflow.filter(x => !x.pass) });

  await page.setViewportSize({ width: 319, height: 760 });
  await page.goto(base + '/neural.html', { waitUntil: 'domcontentloaded' });
  await page.waitForFunction(() => !document.querySelector('#nm-status').textContent.includes('Loading'));
  ok('mobile map is visible before changing display mode', await page.locator('#nm-network').isVisible() && await page.locator('#nm-view-network').getAttribute('aria-pressed') === 'true');
  await page.locator('#nm-view-entities').click();
  const mobileInitial = await page.evaluate(() => ({ entitiesVisible: !document.querySelector('#nm-entities').hidden, networkHidden: document.querySelector('#nm-network').hidden, bodyOverflow: document.body.style.overflow }));
  await page.locator('#nm-entity-list [data-node]').first().click();
  const mobileSelected = await page.evaluate(() => ({ sheetOpen: document.querySelector('#nm-dossier').classList.contains('is-open'), role: document.querySelector('#nm-dossier').getAttribute('role'), bodyOverflow: document.body.style.overflow, focused: document.activeElement === document.querySelector('#nm-name') }));
  await page.locator('#nm-close').click();
  const mobileClosed = await page.evaluate(() => ({ sheetOpen: document.querySelector('#nm-dossier').classList.contains('is-open'), bodyOverflow: document.body.style.overflow }));
  ok('319px entity-list selection uses a focusable modal sheet with scroll lock/restoration', mobileInitial.entitiesVisible && mobileInitial.networkHidden && mobileSelected.sheetOpen && mobileSelected.role === 'dialog' && mobileSelected.bodyOverflow === 'hidden' && mobileSelected.focused && !mobileClosed.sheetOpen && mobileClosed.bodyOverflow === mobileInitial.bodyOverflow, { mobileInitial, mobileSelected, mobileClosed });

  await page.locator('#nm-view-network').click();
  await page.locator('#nm-search').fill('no matching entity 91743');
  ok('unmatched network search shows a visible explanation', await page.locator('#nm-empty').isVisible());
  await page.locator('#nm-reset').click();
  await page.locator('#nm-view-entities').click();
  await page.locator('[data-node="DONALD_TRUMP_JR"]').click();
  await page.getByRole('button',{name:'Share entity',exact:true}).click();
  await page.keyboard.press('Tab');
  ok('mobile Share dialog receives keyboard focus above map entity sheet', await page.locator('#share-url').evaluate(el=>document.activeElement === el));
  await page.keyboard.press('Escape');
  ok('closing Share retains the selected entity', await page.locator('#nm-dossier').getAttribute('aria-modal') === 'true');
  await page.locator('#nm-close').click();
  await page.setViewportSize({width:390,height:760});
  await page.goto(base+'/',{waitUntil:'domcontentloaded'});
  const allReportSections=JSON.parse(fs.readFileSync('site/research/data.json','utf8')).reportSections.filter(r=>r.scope==='report');
  const sectionTargets=[];
  for(const row of allReportSections){
    await page.goto(base+row.href,{waitUntil:'domcontentloaded'});
    let waitError='';
    try {
      await page.waitForFunction(id=>{
        const el=document.getElementById(id),top=el?.getBoundingClientRect().top;
        return location.hash==='#'+id&&!!el.getClientRects().length&&top>=0&&top<250;
      },row.id,{timeout:3000});
    } catch(error) { waitError=error.message; }
    const measured=await page.locator('[id="'+row.id+'"]').evaluate(el=>({visible:!!el.getClientRects().length,top:el.getBoundingClientRect().top,text:el.textContent.trim()}));
    sectionTargets.push({id:row.id,pass:!waitError&&measured.visible&&measured.top>=0&&measured.top<250,waitError,...measured});
  }
  ok('all preserved report headings are reachable at mobile deep links',sectionTargets.length===154&&sectionTargets.every(r=>r.pass),{count:sectionTargets.length,failures:sectionTargets.filter(r=>!r.pass)});
  ok('no local HTTP failures or uncaught browser errors in exercised flows', out.responses.length === 0 && out.console.length === 0, { responses: out.responses, console: out.console });
  out.finishedAt = new Date().toISOString();
  fs.writeFileSync('.architecture/app-audit/browser-flows.json', JSON.stringify(out, null, 2) + '\n');
  console.log(JSON.stringify({ checks: out.checks.length, failures: out.failures, console: out.console, responses: out.responses }, null, 2));
  if(out.failures.length) process.exitCode=1;
  await browser.close();
})().catch(async error => {
  out.fatal = { message: error.message, stack: error.stack };
  out.finishedAt = new Date().toISOString();
  fs.writeFileSync('.architecture/app-audit/browser-flows.json', JSON.stringify(out, null, 2) + '\n');
  console.error(error);
  process.exitCode = 1;
  await browser?.close();
});
