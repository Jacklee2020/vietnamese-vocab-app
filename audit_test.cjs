// 深度审计测试：验证从 v1.0 到 v1.8.1 所有历史特性的完整性与运行正常
const path = require('path');
const { chromium } = require('playwright');

const APP = 'file://' + path.resolve(__dirname, 'pwa/index.html');
const results = [];
const consoleErrors = [];
let pass = 0, fail = 0;

function check(name, cond, extra = '') {
  const status = cond ? 'PASS' : 'FAIL';
  results.push(`${status} | ${name}${extra ? ' | ' + extra : ''}`);
  if (cond) pass++; else fail++;
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
  await page.waitForTimeout(400);

  console.log('=== 开始全面特性审计 ===\n');

  // ----------------------------------------------------
  // 1. 视觉主题与色彩规范
  // ----------------------------------------------------
  const pri = await page.evaluate(() => getComputedStyle(document.documentElement).getPropertyValue('--pri').trim());
  const pri2 = await page.evaluate(() => getComputedStyle(document.documentElement).getPropertyValue('--pri2').trim());
  check('1. 主题色为淡蓝 (#4aa3df)', pri === '#4aa3df', 'pri=' + pri);
  check('1. 辅助渐变色为淡蓝 (#83c4ef)', pri2 === '#83c4ef', 'pri2=' + pri2);

  // ----------------------------------------------------
  // 2. 词库全量规模与 12 大分类
  // ----------------------------------------------------
  const totalWords = await page.evaluate(() => WORDS_DATA.length);
  check('2. 词库全量收录 4621 词', totalWords === 4621, 'WORDS_DATA=' + totalWords);

  const topicsCount = await page.evaluate(() => TOPICS.length);
  check('2. 12 大主题去重完整', topicsCount === 12, 'TOPICS.length=' + topicsCount);

  const allTopicsHaveWords = await page.evaluate(() => TOPICS.every(t => WORDS_DATA.some(w => w[0] === t)));
  check('2. 每个主题均包含词汇', allTopicsHaveWords, '');

  // ----------------------------------------------------
  // 3. 词汇自定义隐藏功能 (S.hidden)
  // ----------------------------------------------------
  // 3.1 初始状态
  const initHidden = await page.evaluate(() => S.hidden.length);
  check('3. S.hidden 初始数组正常', initHidden === 0, 'hidden=' + initHidden);

  // 3.2 模拟隐藏第 0 个单词
  const word0 = await page.evaluate(() => WORDS_DATA[0][1]);
  await page.evaluate(() => hideWordNow(0));
  const afterHide0 = await page.evaluate(() => ({
    hiddenLen: S.hidden.length,
    isHid: isHidden(0),
    vis: visCount(),
    inVisIds: visIds().includes(0)
  }));
  check('3. hideWordNow 隐藏生效', afterHide0.hiddenLen === 1 && afterHide0.isHid === true, word0);
  check('3. visCount 自动扣减 (4620)', afterHide0.vis === 4620, 'vis=' + afterHide0.vis);
  check('3. visIds 自动排除已隐藏词', afterHide0.inVisIds === false, '');

  // 3.3 恢复背诵
  await page.evaluate(() => restoreWord(0));
  const afterRestore0 = await page.evaluate(() => ({
    hiddenLen: S.hidden.length,
    isHid: isHidden(0),
    vis: visCount()
  }));
  check('3. restoreWord 恢复生效', afterRestore0.hiddenLen === 0 && afterRestore0.isHid === false, '');
  check('3. visCount 恢复全量 4621', afterRestore0.vis === 4621, 'vis=' + afterRestore0.vis);

  // 3.4 词表页面渲染与隐藏入口
  await page.locator('.tab:has-text("词表")').click();
  await page.waitForTimeout(200);
  const wordsHtml = await page.textContent('body');
  check('3. 词表页存在「已隐藏词汇」入口', wordsHtml.includes('已隐藏词汇'), '');

  // 3.5 单词详情弹窗内包含隐藏按钮
  await page.evaluate(() => wordModal(5));
  await page.waitForTimeout(100);
  const modalText = await page.textContent('#dialog');
  check('3. 单词弹窗包含「🙈 不再背诵」按钮', modalText.includes('不再背诵') && modalText.includes('播放发音'), '');
  await page.evaluate(() => hideModal());

  // ----------------------------------------------------
  // 4. 自适应复习算法 (错词加权 + 4小时薄弱词优先)
  // ----------------------------------------------------
  await page.evaluate(() => {
    // 模拟学过 3 个词：word1 (正常), word2 (错3次), word3 (刚错且低熟练度)
    const now = Date.now();
    S.learned[1] = { b: 3, due: now - 86400000 * 2, w: 0 }; // 权重: 0*2 + (5-3) = 2
    S.learned[2] = { b: 1, due: now - 86400000 * 2, w: 3 }; // 权重: 3*2 + (5-1) = 10
    S.learned[3] = { b: 0, due: now - 86400000 * 2, w: 5 }; // 权重: 5*2 + (5-0) = 15
    save();
  });
  const dueQueue = await page.evaluate(() => dueReviewIds());
  // word3 (权重15) 与 word2 (权重10) 应排在 word1 (权重2) 之前
  const w1Pos = dueQueue.indexOf(1);
  const w2Pos = dueQueue.indexOf(2);
  const w3Pos = dueQueue.indexOf(3);
  check('4. 自适应复习错词权重优先排序 (w3, w2 > w1)', w3Pos < w1Pos && w2Pos < w1Pos, `w3=${w3Pos}, w2=${w2Pos}, w1=${w1Pos}`);

  // ----------------------------------------------------
  // 5. 学习卡片核心交互
  // ----------------------------------------------------
  await page.locator('.tab:has-text("首页")').click();
  await page.waitForTimeout(200);
  await page.locator('main .btn').first().click();
  await page.waitForSelector('.wcard', { timeout: 5000 });
  check('5. 学习卡片正常弹出', await page.locator('.wcard').count() === 1, '');

  await page.locator('.wcard').click();
  await page.waitForTimeout(150);
  const zhText = await page.textContent('.wcard');
  check('5. 卡片翻转展示中文释义', /\p{Script=Han}/u.test(zhText), '');

  // 点认识完成一张卡片
  await page.locator('.btn.yes').click();
  await page.waitForTimeout(200);

  // ----------------------------------------------------
  // 6. 三种自测题型
  // ----------------------------------------------------
  // 6.1 四选一
  await page.locator('.tab:has-text("测验")').click();
  await page.waitForTimeout(200);
  await page.locator('#segMode button:has-text("四选一")').click();
  await page.locator('main .btn:has-text("开始测验")').click();
  await page.waitForSelector('.qword', { timeout: 5000 });
  const optCount = await page.locator('.opt').count();
  check('6. 四选一选项数量为 4', optCount === 4, 'opts=' + optCount);
  await page.locator('.opt').first().click();
  await page.waitForTimeout(900);

  // 6.2 听音模式
  await page.locator('.tab:has-text("测验")').click();
  await page.waitForTimeout(200);
  await page.locator('#segMode button:has-text("听音")').click();
  await page.locator('main .btn:has-text("开始测验")').click();
  await page.waitForSelector('.speak, button:has-text("🔊")', { timeout: 5000 });
  check('6. 听音模式发音按钮存在', await page.locator('main button:has-text("🔊")').count() > 0, '');

  // 6.3 拼写模式
  await page.locator('.tab:has-text("测验")').click();
  await page.waitForTimeout(200);
  await page.locator('#segMode button:has-text("拼写")').click();
  await page.locator('main .btn:has-text("开始测验")').click();
  await page.waitForSelector('.type-box', { timeout: 5000 });
  check('6. 拼写输入框渲染正常', await page.locator('#tinput').count() === 1, '');

  // ----------------------------------------------------
  // 7. 生词本与打印清单导出 (exportFav)
  // ----------------------------------------------------
  await page.locator('.tab:has-text("生词本")').click();
  await page.waitForTimeout(200);
  await page.evaluate(() => { S.fav = [5, 10, 20]; save(); switchTab('fav'); });
  await page.waitForTimeout(200);
  const favCount = await page.locator('.row').count();
  check('7. 生词本列表正常展示', favCount === 3, 'favCount=' + favCount);

  const hasExportBtn = await page.locator('button:has-text("导出打印清单"), button:has-text("🖨️")').count();
  check('7. 生词本包含「导出打印清单」按钮', hasExportBtn > 0, '');

  // ----------------------------------------------------
  // 8. 我的页学习报告 (weekSum, reviewStats)
  // ----------------------------------------------------
  await page.locator('.tab:has-text("我的")').click();
  await page.waitForTimeout(200);
  const meBody = await page.textContent('body');
  check('8. 学习报告面板存在', meBody.includes('学习报告') && meBody.includes('本周学习') && meBody.includes('累计复习') && meBody.includes('正确率'), '');
  const dayBlocks = await page.locator('main div[title*="词"]').count();
  check('8. 近 30 天打卡热力方块 (30个)', dayBlocks === 30, 'blocks=' + dayBlocks);

  // ----------------------------------------------------
  // 9. 每日新词设置 (10/20/50/100)
  // ----------------------------------------------------
  const dayOpts = await page.locator('.rate-seg').first().locator('button').allTextContents();
  check('9. 每日新词支持 10/20/50/100', JSON.stringify(dayOpts) === JSON.stringify(['10','20','50','100']), dayOpts.join(','));

  // ----------------------------------------------------
  // 10. 设备适配与语音辅助函数 (微信/TTS)
  // ----------------------------------------------------
  const helpersCheck = await page.evaluate(() => ({
    hasWx: typeof isWeChatIOS === 'function',
    hasVoiceCheck: typeof viVoiceAvailable === 'function',
    hasGuideBox: typeof guideBox === 'function'
  }));
  check('10. 微信环境检测函数存在', helpersCheck.hasWx, '');
  check('10. 越南语 TTS 语音可用性检测存在', helpersCheck.hasVoiceCheck && helpersCheck.hasGuideBox, '');

  // ----------------------------------------------------
  // 11. 深色模式切换
  // ----------------------------------------------------
  await page.locator('.toggle').last().click();
  await page.waitForTimeout(150);
  const isDark = await page.evaluate(() => document.body.classList.contains('dark'));
  check('11. 深色模式切换正常', isDark === true, '');

  // ----------------------------------------------------
  // 12. 数据导出与导入恢复 (JSON 备份)
  // ----------------------------------------------------
  const backupJson = await page.evaluate(() => JSON.stringify(S));
  check('12. 数据备份序列化有效', backupJson.includes('"learned"') && backupJson.includes('"fav"'), '');

  await browser.close();

  console.log('\n==============================');
  results.forEach(r => console.log(r));
  console.log('------------------------------');
  console.log(`审计完成：${pass} PASS / ${fail} FAIL`);
  if (consoleErrors.length) {
    console.log('控制台异常:', consoleErrors);
  } else {
    console.log('控制台无任何报错 ✅');
  }
  console.log('==============================');
  process.exit(fail ? 1 : 0);
})().catch(e => { console.error('审计异常:', e); process.exit(2); });
