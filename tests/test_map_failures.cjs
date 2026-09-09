const assert = require('node:assert/strict');
const { chromium } = require('/Users/zincdigital/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');

const target = process.env.MAP_TEST_URL || 'http://127.0.0.1:8765/neural.html';
let browser;

(async () => {
  browser = await chromium.launch({ channel: 'chrome', headless: true });

  async function scenario(failedPath) {
    const context = await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true });
    const page = await context.newPage();
    if (failedPath) await page.route(`**${failedPath}`, route => route.fulfill({ status: 500, body: '{}' }));
    await page.goto(target, { waitUntil: 'networkidle' });
    const result = await page.evaluate(() => {
      const q = id => document.getElementById(id);
      return {
        status: q('nm-status').textContent,
        registryStatus: q('nm-registry-status').textContent,
        networkVisible: !!q('nm-network').getClientRects().length,
        entitiesVisible: !!q('nm-entities').getClientRects().length,
        emptyVisible: !!q('nm-empty').getClientRects().length,
        entityCount: q('nm-entity-list').children.length,
        disabled: Object.fromEntries(['nm-search', 'nm-topic', 'nm-grade', 'nm-reset',
          'nm-view-network', 'nm-view-entities', 'nm-zoom-in', 'nm-zoom-out', 'nm-fit',
          'nm-motion'].map(id => [id, q(id).disabled])),
        pressed: [q('nm-view-network').getAttribute('aria-pressed'), q('nm-view-entities').getAttribute('aria-pressed')],
      };
    });
    await context.close();
    return result;
  }

  const normal = await scenario();
  assert.equal(normal.networkVisible, true);
  assert.equal(normal.disabled['nm-view-network'], false);
  assert.ok(normal.entityCount > 0);

  const registry = await scenario('/research/data.json');
  assert.equal(registry.disabled['nm-topic'], true);
  assert.equal(registry.disabled['nm-search'], false);
  assert.equal(registry.networkVisible, true);
  assert.match(registry.registryStatus, /topic index could not be loaded/i);

  const drawing = await scenario('/map/svg.frag');
  assert.equal(drawing.networkVisible, false);
  assert.equal(drawing.entitiesVisible, true);
  assert.equal(drawing.disabled['nm-view-network'], true);
  assert.equal(drawing.disabled['nm-view-entities'], false);
  assert.equal(drawing.disabled['nm-search'], false);
  assert.ok(drawing.entityCount > 0);
  assert.match(drawing.status, /network drawing is unavailable/i);

  const data = await scenario('/map/data.json');
  assert.equal(data.networkVisible, false);
  assert.equal(data.entitiesVisible, true);
  assert.equal(data.emptyVisible, true);
  assert.deepEqual(data.pressed, ['false', 'true']);
  assert.equal(Object.values(data.disabled).every(Boolean), true);
  assert.match(data.status, /Map unavailable: Entity data unavailable/);

  console.log(JSON.stringify({ normal, registry, drawing, data }));
  await browser.close();
})().catch(async error => {
  console.error(error);
  process.exitCode = 1;
  await browser?.close();
});
