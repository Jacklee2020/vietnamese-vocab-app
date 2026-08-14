const { chromium } = require('playwright');
const APP = 'file:///Users/liqing/Documents/Codex/2026-08-05/zhe/vocab_app/%E8%B6%8A%E5%8D%97%E8%AF%AD%E8%83%8C%E5%8D%95%E8%AF%8DApp.html';
(async () => {
  const browser = await chromium.launch({
    executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    headless: true, args: ['--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage', '--no-first-run']
  });
  const page = await browser.newPage({ viewport: { width: 390, height: 844 } });
  page.on('pageerror', e => console.log('PAGEERROR:', e.message));
  await page.goto(APP, { waitUntil: 'load', timeout: 20000 });
  await page.waitForTimeout(300);
  console.log('STEP1 home ok');
  await page.locator('main .btn').first().click();
  await page.waitForSelector('.wcard', { timeout: 5000 });
  console.log('STEP2 session ok');
  for (let k = 0; k < 3; k++) { await page.locator('.btn.yes').click(); await page.waitForTimeout(150); }
  console.log('STEP3 answered 3');
  await page.locator('.tab:has-text("测验")').click();
  await page.waitForTimeout(200);
  console.log('STEP4 test tab clicked, main snippet:');
  console.log((await page.locator('#main').innerHTML()).slice(0, 200).replace(/\n/g, ' '));
  await page.locator('main .btn:has-text("开始测验")').click();
  await page.waitForTimeout(1500);
  const state = await page.evaluate(() => ({
    mode: TEST && TEST.mode, scope: TEST && TEST.scope, i: TEST && TEST.i,
    qsLen: TEST && TEST.qs && TEST.qs.length,
    optCount: document.querySelectorAll('.opt').length,
    qword: document.querySelector('.qword') ? document.querySelector('.qword').textContent : null,
    typeBox: !!document.querySelector('.type-box'),
    mainStart: document.querySelector('#main').innerHTML.slice(0, 300)
  }));
  console.log(JSON.stringify(state, null, 1));
  await browser.close();
})().catch(e => { console.error('DEBUG FAIL:', e.message); process.exit(2); });
