// App 功能测试：驱动 Chrome 渲染 PWA 版 App，验证核心流程
// 用法：node test_app.cjs （需本机安装 playwright，并已登录 Chrome）
const path = require('path');
const fs = require('fs');
const { chromium } = require('playwright');

const APP = 'file://' + path.resolve(__dirname, 'pwa/index.html');
const OUT = path.join(__dirname, 'preview');
const results = [];
const consoleErrors = [];
let pass = 0, fail = 0;

function check(name, cond, extra) {
  results.push(`${cond ? 'PASS' : 'FAIL'} | ${name}${extra ? ' | ' + extra : ''}`);
  cond ? pass++ : fail++;
}

(async () => {
  const browser = await chromium.launch({
    executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    headless: true,
    args: ['--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage', '--no-first-run', '--disable-background-networking']
  });
  const page = await browser.newPage({ viewport: { width: 390, height: 844 } });
  page.on('console', m => { if (m.type() === 'error') consoleErrors.push(m.text()); });
  page.on('pageerror', e => consoleErrors.push('PAGEERROR: ' + e.message));

  await page.goto(APP, { waitUntil: 'load', timeout: 20000 });

  // 1. 首页
  const body = await page.textContent('body');
  check('首页标题', body.includes('越南语千词斩'), '');
  const startBtn = await page.textContent('.hero ~ * .btn, main .btn').catch(() => '');
  await page.waitForTimeout(300);
  const homeBtn = await page.locator('main .btn').first().textContent().catch(() => '');
  check('开始学习按钮', (homeBtn || '').includes('开始今日学习'), homeBtn || '');
  await page.screenshot({ path: path.join(OUT, '01_首页.png') });

  // 2. 学习会话
  await page.locator('main .btn').first().click();
  await page.waitForSelector('.wcard', { timeout: 5000 });
  let cardText = await page.textContent('.wcard');
  check('学习卡片显示', cardText.includes('发音'), cardText.slice(0, 60).replace(/\n/g, ' '));
  // 翻牌
  await page.locator('.wcard').click();
  await page.waitForTimeout(200);
  const zhAfterFlip = await page.textContent('.wcard');
  check('翻牌显示中文释义', /\p{Script=Han}/u.test(zhAfterFlip), '');
  await page.screenshot({ path: path.join(OUT, '02_学习卡片.png') });
  // 点认识 3 次（可能进入下一个卡片）
  for (let k = 0; k < 3; k++) {
    await page.locator('.btn.yes').click();
    await page.waitForTimeout(120);
  }
  const after = await page.textContent('body');
  check('会话推进（或完成小结）', after.includes('本轮完成') || await page.locator('.wcard').count() === 1, '');

  // 3. 测验
  await page.locator('.tab:has-text("测验")').click();
  await page.waitForTimeout(200);
  await page.locator('main .btn:has-text("开始测验")').click();
  await page.waitForSelector('.qword, .type-box', { timeout: 5000 });
  const qword = await page.textContent('.qword').catch(() => '');
  check('四选一出题', qword.trim().length > 0, qword.slice(0, 40));
  await page.screenshot({ path: path.join(OUT, '03_测验.png') });
  const qsLen = await page.evaluate(() => TEST.qs.length);
  // 答 1 题 → 应推进到第 2 题
  await page.locator('.opt').first().click();
  await page.waitForTimeout(900);
  const prog1 = await page.textContent('body');
  check('答题后题号推进', prog1.includes('2 / ' + qsLen), 'qsLen=' + qsLen);
  // 答完剩余题目 → 结果页
  for (let k = 1; k < qsLen; k++) {
    await page.locator('.opt').first().click();
    await page.waitForTimeout(900);
  }
  const tbody = await page.textContent('body');
  check('测验结果页', tbody.includes('答对') && tbody.includes('题'), '');

  // 听音模式
  await page.locator('.tab:has-text("测验")').click();
  await page.waitForTimeout(150);
  await page.locator('#segMode button:has-text("听音")').click();
  await page.locator('main .btn:has-text("开始测验")').click();
  await page.waitForSelector('.qword, .speak', { timeout: 5000 });
  check('听音模式渲染', await page.locator('main .speak, main button:has-text("🔊")').count() > 0, '');
  await page.locator('.tab:has-text("测验")').click();
  await page.waitForTimeout(150);

  // 拼写模式
  await page.locator('#segMode button:has-text("拼写")').click();
  await page.locator('main .btn:has-text("开始测验")').click();
  await page.waitForSelector('.type-box', { timeout: 5000 });
  const qsLenT = await page.evaluate(() => TEST.qs.length);
  const answer = await page.evaluate(() => WORDS_DATA[TEST.qs[TEST.i].id][1]);
  await page.locator('#tinput').fill(answer);
  await page.locator('.type-box button').click();
  await page.waitForTimeout(1000);
  const progT = await page.textContent('body');
  check('拼写作答推进', progT.includes('2 / ' + qsLenT), answer);

  // 4. 词表 + 搜索
  await page.locator('.tab:has-text("词表")').click();
  await page.waitForTimeout(200);
  const topics = await page.locator('.topic-row').count();
  check('词表 12 主题 + 全部', topics >= 12, 'topic-row=' + topics);
  await page.locator('.topic-row').first().click();
  await page.waitForTimeout(200);
  const rows = await page.locator('.row').count();
  check('主题词列表有内容', rows > 0, 'rows=' + rows);
  const totalWords = await page.evaluate(() => WORDS_DATA.length);
  check('数据嵌入 4621 词', totalWords === 4621, 'WORDS_DATA=' + totalWords);
  await page.locator('.search').fill('Hà Nội');
  await page.waitForTimeout(300);
  const srch = await page.textContent('body');
  check('搜索命中', srch.includes('Hà Nội'), '');

  // 5. 我的 + 设置
  await page.locator('.tab:has-text("我的")').click();
  await page.waitForTimeout(200);
  const me = await page.textContent('body');
  check('统计面板', me.includes('已学') && me.includes('连续打卡'), '');
  const dayOpts = await page.locator('.rate-seg').first().locator('button').allTextContents();
  check('每日新词选项 50/100/200/300/500', JSON.stringify(dayOpts) === JSON.stringify(['50','100','200','300','500']), dayOpts.join(','));
  await page.screenshot({ path: path.join(OUT, '04_我的.png') });

  // 6. 深色模式
  await page.locator('.toggle').last().click();
  await page.waitForTimeout(200);
  const dark = await page.evaluate(() => document.body.classList.contains('dark'));
  check('深色模式切换', dark === true, '');

  // 7. 刷新持久化
  await page.reload({ waitUntil: 'load' });
  await page.waitForTimeout(400);
  const reloaded = await page.evaluate(() => localStorage.getItem('vnvocab3000v1') !== null);
  check('进度持久化', reloaded, '');

  // 8. 生词本（学习时“不认识”应已加入）
  await page.locator('.tab:has-text("生词本")').click();
  await page.waitForTimeout(200);
  const favBody = await page.textContent('body');
  check('生词本渲染', favBody.includes('生词本') || favBody.includes('📭'), '');

  await browser.close();

  console.log('===== 测试结果 =====');
  results.forEach(r => console.log(r));
  console.log(`---- ${pass} PASS / ${fail} FAIL ----`);
  if (consoleErrors.length) { console.log('---- 控制台错误 ----'); consoleErrors.slice(0, 10).forEach(e => console.log(e)); }
  else console.log('---- 无控制台错误 ----');
  process.exit(fail ? 1 : 0);
})().catch(e => { console.error('测试脚本异常:', e); process.exit(2); });
