const path = require('path');
const { chromium } = require('playwright');
const BASE = 'http://127.0.0.1:8123/';
const results = [];
const errors = [];
let pass = 0, fail = 0;
const check = (n, c, x) => { results.push(`${c ? 'PASS' : 'FAIL'} | ${n}${x ? ' | ' + x : ''}`); c ? pass++ : fail++; };

(async () => {
  const browser = await chromium.launch({
    executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    headless: true, args: ['--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage', '--no-first-run']
  });
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 } });
  const page = await ctx.newPage();
  page.on('pageerror', e => errors.push('PAGEERROR: ' + e.message));
  page.on('console', m => { if (m.type() === 'error') errors.push('CONSOLE: ' + m.text()); });

  await page.goto(BASE + 'index.html', { waitUntil: 'load', timeout: 20000 });
  await page.waitForTimeout(500);
  let body = await page.textContent('body');
  check('页面经 HTTP 正常渲染', body.includes('越南语千词斩'), '');

  const reg = await page.evaluate(() => navigator.serviceWorker.getRegistration().then(r => r ? { scope: r.scope, state: r.active ? r.active.state : 'none' } : null));
  check('Service Worker 已注册', !!reg, reg && reg.state);
  await page.waitForFunction(() => navigator.serviceWorker.controller !== null, { timeout: 10000 }).catch(() => {});
  check('SW 已接管页面', await page.evaluate(() => !!navigator.serviceWorker.controller), '');

  const manifest = await page.evaluate(async () => {
    const r = await fetch('./manifest.webmanifest');
    const j = await r.json();
    return { ok: r.ok, name: j.name, icons: (j.icons || []).length };
  });
  check('manifest 可访问', manifest.ok && manifest.name.includes('越南语'), manifest.name + ' icons=' + manifest.icons);

  const iconOk = await page.evaluate(async () => {
    for (const f of ['icon-192.png', 'icon-512.png', 'icon-512-maskable.png', 'apple-touch-icon.png']) {
      const r = await fetch('./' + f);
      if (!r.ok) return false;
    }
    return true;
  });
  check('全部图标可访问', iconOk, '');

  // 离线测试
  await ctx.setOffline(true);
  await page.reload({ waitUntil: 'load', timeout: 15000 }).catch(() => {});
  await page.waitForTimeout(800);
  const offline = await page.textContent('body');
  check('离线刷新仍可用（SW 缓存）', offline.includes('越南语千词斩'), '');

  await ctx.setOffline(false);
  await page.locator('main .btn').first().click();
  await page.waitForSelector('.wcard', { timeout: 5000 });
  check('离线恢复后学习卡片正常', true, '');

  await browser.close();
  console.log('===== PWA 测试结果 =====');
  results.forEach(r => console.log(r));
  console.log(`---- ${pass} PASS / ${fail} FAIL ----`);
  if (errors.length) { console.log('---- 错误 ----'); errors.slice(0, 10).forEach(e => console.log(e)); }
  else console.log('---- 无错误 ----');
  process.exit(fail ? 1 : 0);
})().catch(e => { console.error('测试异常:', e); process.exit(2); });
