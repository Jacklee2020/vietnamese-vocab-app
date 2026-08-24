# 更新记录（Changelog）

本文件记录「越南语千词斩」的版本更新与修复内容，遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/) 风格。

## [v1.2.0] - 2026-08-24

### ✨ 新增与词库扩充

- **A1-B2 等级考试词库全量增补**：从《越南语能力考试模拟题（B1-B2）》清洗并合入 1,243 个高频真题词汇，全量词库由 3,378 词扩充至 **4,621 词 · 12 大类**。
- **数据清洗流水线**：新增 `scripts/merge_exam_vocab.py` 自动化清洗脚本，修复 OCR 字符间隙、英文粘连、分列错位等问题，并自动完成 12 大场景分类。
- **构建流水线升级**：`make_app.py` 升级为直接基于标准 `词库_合并版.csv` 注入生成；Service Worker 缓存版本升级至 `vnvocab-v8`。

## [v1.1.0] - 2026-08-15

### 🐛 修复

- **测试脚本失效**：`test_app.cjs` / `debug_quiz.cjs` 移除本机绝对路径，改为读取仓库内 `pwa/index.html`；更新过时断言（3378 词 / 12 类 / 应用名「越南语千词斩」）。
- **PWA 更新不生效**：Service Worker 由「全量 cache-first」改为「HTML 走 network-first、静态资源 stale-while-revalidate」，发布新版本后用户刷新即可看到更新，不再依赖手动改缓存版本号（缓存名升级为 `vnvocab-v3`）。
- **词表页分类数显示错误**：页脚硬编码「11 类」改为动态读取 `TOPICS.length`（实际 12 类），并为第 12 类补上缺失的 emoji。
- **`confirmBox` 潜在 XSS**：由字符串拼接执行回调改为 `data-*` + 事件绑定，避免回调内容被当作代码执行。
- **manifest `start_url`**：由 `./index.html` 改为 `./`，避免部分环境下路径解析异常。

### ✨ 新增

- 新增 `scripts/check_html_sync.py`：校验 CSV 词库与 `pwa/index.html` 内嵌词库完全一致，防止改词库后忘记重新生成 HTML。
- CI 新增 `validate-sync` 工作流，自动执行词库同步校验。

### 🔧 其他

- `make_pwa.py` 与仓库 PWA 产物同步：应用名、主题色、缓存名统一为当前版本；源文件缺失时给出明确提示。
- `pwa_test.cjs` 断言更新为当前版本文案。

## [v1.0.0] - 2026-08-11

### 🎉 首发

- 3378 个核心越南语词汇 · 12 大分类，离线 PWA。
- 卡片学习、间隔复习、三种自测（四选一 / 听音 / 拼写）。
- 越南语真人发音（慢 / 正常 / 快），深色模式，进度导出 / 导入。

---

提交规范：`feat:` 新功能 / `fix:` 修复 / `docs:` 文档 / `chore:` 杂项。
