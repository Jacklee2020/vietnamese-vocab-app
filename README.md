# 🇻🇳 越南语千词斩 · Vietnamese Vocabulary Trainer

一个离线可用的越南语词汇背诵 PWA。手机、电脑浏览器直接可用，无需注册、无需服务器、无需联网。

## ✨ 功能特性

- **3378 个核心词汇**，12 大类：数字时间、餐饮交通、购物住宿、商务金融、医疗、核心词类、常用口语短句等
- **每日新词计划**：50 / 100 / 200 / 300 / 500 词可调
- **间隔复习**：按遗忘曲线自动安排复习，巩固记忆
- **三种自测模式**：🔊 听音选义、✍️ 四选一、⌨️ 拼写
- **越南语发音**：点击单词卡片即朗读（系统 TTS）
- **完全离线**：Service Worker 缓存，飞行模式也能用
- **零后端**：学习进度保存在本机浏览器（localStorage/IndexedDB）

## 🚀 快速开始

方式一：直接用浏览器打开 `pwa/index.html`

方式二：把 `pwa/` 目录部署到任意静态托管（GitHub Pages、Netlify、Nginx……），得到链接后手机访问。

**安装到手机（推荐）**

- iPhone：Safari 打开 → 分享 → 「添加到主屏幕」
- Android：Chrome 打开 → 菜单 → 「添加到主屏幕」

## 📂 项目结构

```
vocab_app/
├── pwa/                     # 应用本体（词库已内嵌，整个目录即完整应用）
│   ├── index.html           # 全部页面逻辑 + 3378 词数据
│   ├── manifest.webmanifest # PWA 清单
│   ├── sw.js                # Service Worker（离线缓存）
│   └── icon-*.png           # 应用图标
├── 词库_合并版.csv          # 完整词库（可编辑原始数据，UTF-8）
├── 词库_合并版.xlsx         # 完整词库（Excel 版）
├── merge_data.py            # 词库合并、去重、校对脚本
├── make_pwa.py              # PWA 构建脚本
├── make_app.py / template.html  # 旧版单文件生成脚本与模板
├── *_test.cjs / debug_quiz.cjs  # 开发测试脚本
├── 更新说明.md              # 版本更新说明
└── README.md
```

## 🗂️ 词库格式

`词库_合并版.csv` 列：`序号, 分类, 越南语, 中文`。编辑后重新生成，或将新数据替换到 `pwa/index.html` 的 `WORDS_DATA` 即可。

## 🧰 技术栈

纯 HTML + CSS + JavaScript，**零依赖、无构建步骤**。PWA = Web App Manifest + Service Worker。

## 📄 许可

- 代码：MIT License
- 词库数据：保留所有权利（All Rights Reserved），仅供个人学习交流，未经授权不得商用
