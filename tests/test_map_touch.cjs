const assert = require('node:assert/strict');
const { chromium } = require('/Users/zincdigital/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');

const target = process.env.MAP_TEST_URL || 'http://127.0.0.1:8765/neural.html';
let browser;

async function viewBox(page) {
  return page.locator('#nm-canvas svg').evaluate(svg => svg.viewBox.baseVal.width);
}

async function pinch(cdp, center, from, to) {
  const points = distance => [
    { x: center.x - distance / 2, y: center.y },
    { x: center.x + distance / 2, y: center.y },
  ];
  await cdp.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: points(from) });
  await cdp.send('Input.dispatchTouchEvent', { type: 'touchMove', touchPoints: points(to) });
  await cdp.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] });
}

async function assertMobilePlacement(page, width) {
  await page.setViewportSize({ width, height: 844 });
  await page.waitForTimeout(100);
  const layout = await page.evaluate(() => {
    const toolbar = document.querySelector('.nm-toolbar');
    const network = document.querySelector('#nm-network');
    const canvas = document.querySelector('#nm-canvas');
    const toolbarBox = toolbar.getBoundingClientRect();
    const networkBox = network.getBoundingClientRect();
    const canvasBox = canvas.getBoundingClientRect();
    return {
      afterToolbar: toolbar.nextElementSibling === network,
      toolbarBottom: toolbarBox.bottom,
      networkTop: networkBox.top,
      canvasVisible: Math.max(0, Math.min(innerHeight, canvasBox.bottom) - Math.max(0, canvasBox.top)),
    };
  });
  assert.equal(layout.afterToolbar, true, `${width}px network is not after toolbar`);
  assert.ok(layout.networkTop >= layout.toolbarBottom - 1, `${width}px network precedes toolbar`);
  assert.ok(layout.networkTop < 844, `${width}px network starts below first viewport`);
  assert.ok(layout.canvasVisible >= 100, `${width}px shows only ${layout.canvasVisible}px of map`);
  return layout;
}

(async () => {
  browser = await chromium.launch({ channel: 'chrome', headless: true });
  const context = await browser.newContext({
    viewport: { width: 390, height: 844 },
    isMobile: true,
    hasTouch: true,
    deviceScaleFactor: 1,
  });
  const page = await context.newPage();
  await page.goto(target, { waitUntil: 'networkidle' });
  await page.locator('#nm-canvas svg').waitFor();
  const mobile319 = await assertMobilePlacement(page, 319);
  const mobile390 = await assertMobilePlacement(page, 390);
  await page.setViewportSize({ width: 1200, height: 900 });
  await page.waitForTimeout(100);
  assert.equal(await page.evaluate(() => document.querySelector('#nm-coverage').nextElementSibling?.id), 'nm-network');
  assert.equal(await page.evaluate(() => document.querySelector('#nm-network').nextElementSibling?.id), 'nm-entities');
  await page.setViewportSize({ width: 390, height: 844 });
  await page.waitForTimeout(100);
  await page.locator('#nm-canvas').scrollIntoViewIfNeeded();
  const canvas = await page.locator('#nm-canvas').boundingBox();
  const center = { x: canvas.x + canvas.width / 2, y: canvas.y + canvas.height / 2 };
  const cdp = await context.newCDPSession(page);

  const fitted = await viewBox(page);
  await pinch(cdp, center, 70, 180);
  const pinchedIn = await viewBox(page);
  assert.ok(pinchedIn < fitted * 0.65, `pinch-in did not zoom: ${fitted} -> ${pinchedIn}`);
  assert.equal(new URL(page.url()).searchParams.has('entity'), false, 'pinch selected an entity');

  await pinch(cdp, center, 180, 60);
  const pinchedOut = await viewBox(page);
  assert.ok(pinchedOut > pinchedIn * 2, `pinch-out did not zoom: ${pinchedIn} -> ${pinchedOut}`);
  assert.equal(new URL(page.url()).searchParams.has('entity'), false, 'pinch-out selected an entity');

  await page.locator('#nm-fit').tap();
  for (let i = 0; i < 10; i += 1) await page.locator('#nm-zoom-in').tap();
  const readableDisc = await page.locator('.nm-disc').first().evaluate(node => node.getBoundingClientRect().width);
  assert.ok(readableDisc >= 44, `zoom controls left first node at ${readableDisc}px`);

  await page.locator('#nm-fit').tap();
  const node = page.locator('.nm-node').first();
  const key = await node.getAttribute('data-key');
  await node.tap();
  assert.equal(new URL(page.url()).searchParams.get('entity'), key);
  assert.equal(await page.locator('#nm-dossier').getAttribute('role'), 'dialog');

  await page.locator('#nm-card [data-ui-share]').tap();
  const share = page.locator('#share-dialog');
  await assert.doesNotReject(() => share.waitFor({ state: 'visible' }));
  await page.keyboard.press('Tab');
  assert.equal(await page.evaluate(() => document.activeElement.closest('#share-dialog') !== null), true);
  await page.keyboard.press('Escape');
  assert.equal(await share.evaluate(dialog => dialog.open), false);
  assert.equal(new URL(page.url()).searchParams.get('entity'), key, 'closing Share closed entity');

  await page.locator('#nm-close').tap();
  await page.locator('#nm-search').fill('zzzz-no-such-entity');
  assert.equal(await page.locator('#nm-network').isVisible(), true);
  assert.equal(await page.locator('#nm-empty').isVisible(), true);
  assert.match(await page.locator('#nm-status').textContent(), /^0 matching entities/);

  console.log(JSON.stringify({ mobile319, mobile390, fitted, pinchedIn, pinchedOut, readableDisc, selectedEntity: key }));
  await browser.close();
})().catch(async error => {
  console.error(error);
  process.exitCode = 1;
  await browser?.close();
});
