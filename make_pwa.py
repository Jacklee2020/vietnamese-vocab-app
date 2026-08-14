# -*- coding: utf-8 -*-
"""从单文件 App 生成可托管的 PWA 版（index.html + manifest + sw + 图标）。"""
import json, os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, '越南语背单词App.html')
OUT = os.path.join(HERE, 'pwa')
os.makedirs(OUT, exist_ok=True)

html = open(SRC, encoding='utf-8').read()

# 1) head 注入 manifest / apple-touch-icon
head_add = ('<link rel="icon" href="apple-touch-icon.png">\n'
            '<link rel="manifest" href="manifest.webmanifest">\n'
            '<link rel="apple-touch-icon" href="apple-touch-icon.png">\n'
            '<meta name="apple-mobile-web-app-title" content="越南语背单词">\n'
            '<meta name="apple-mobile-web-app-capable" content="yes">\n')
assert '<meta name="theme-color"' in html
html = html.replace('<meta name="theme-color" content="#e8452c">',
                    head_add + '<meta name="theme-color" content="#e8452c">', 1)

# 2) 注册 Service Worker（仅 https / localhost，file:// 下自动跳过）
sw_reg = ('<script>\n'
          "if ('serviceWorker' in navigator && (location.protocol === 'https:' || location.hostname === 'localhost' || location.hostname === '127.0.0.1')) {\n"
          "  window.addEventListener('load', function () { navigator.serviceWorker.register('sw.js').catch(function () {}); });\n"
          '}\n'
          '</script>\n</body>')
assert html.count('</body>') == 1
html = html[:html.rfind('</body>')] + sw_reg

open(os.path.join(OUT, 'index.html'), 'w', encoding='utf-8').write(html)

# 3) manifest
manifest = {
    "name": "越南语背单词 · 3000词",
    "short_name": "越南语背单词",
    "description": "越南语核心词汇 3000 词背诵、测验与复习",
    "lang": "zh-CN",
    "start_url": "./index.html",
    "scope": "./",
    "display": "standalone",
    "background_color": "#f3f4f6",
    "theme_color": "#e8452c",
    "icons": [
        {"src": "icon-192.png", "sizes": "192x192", "type": "image/png"},
        {"src": "icon-512.png", "sizes": "512x512", "type": "image/png"},
        {"src": "icon-512-maskable.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"},
    ],
}
open(os.path.join(OUT, 'manifest.webmanifest'), 'w', encoding='utf-8').write(json.dumps(manifest, ensure_ascii=False, indent=2))

# 4) Service Worker：缓存全部资源，离线可用
open(os.path.join(OUT, 'sw.js'), 'w', encoding='utf-8').write('''/* 越南语背单词 PWA 离线缓存 */
const CACHE = 'vnvocab-v1';
const ASSETS = ['./', './index.html', './manifest.webmanifest', './icon-192.png', './icon-512.png', './icon-512-maskable.png', './apple-touch-icon.png'];
self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(ASSETS)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener('fetch', e => {
  if (e.request.method !== 'GET') return;
  e.respondWith(
    caches.match(e.request).then(hit => hit || fetch(e.request).then(res => {
      const copy = res.clone();
      caches.open(CACHE).then(c => c.put(e.request, copy));
      return res;
    }).catch(() => caches.match('./index.html')))
  );
});
''')

# 5) 图标
def draw_icon(size, maskable=False):
    pad = int(size * (0.18 if maskable else 0.06))
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    r = int(size * 0.22)
    # 圆角矩形渐变（红 → 橙）
    grad = Image.new('RGBA', (size, size))
    gd = ImageDraw.Draw(grad)
    for y in range(size):
        t = y / size
        col = (int(232 - 8 * t), int(69 + 45 * t), int(44 + 15 * t), 255)
        gd.line([(0, y), (size, y)], fill=col)
    mask = Image.new('L', (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, size - 1, size - 1], radius=r, fill=255)
    img.paste(grad, (0, 0), mask)
    # 白色 V 字（两条粗斜杠）
    w = int(size * 0.20)          # 笔画宽
    x0, x1 = size * 0.22, size * 0.78
    y_top, y_bot = size * 0.26, size * 0.74
    vcol = (255, 255, 255, 255)
    d = ImageDraw.Draw(img)
    d.line([(x0, y_top), (size / 2, y_bot)], fill=vcol, width=w)
    d.line([(size / 2, y_bot), (x1, y_top)], fill=vcol, width=w)
    # 底部小圆点（越南星黄点缀）
    cy = size * 0.82
    d.ellipse([size / 2 - w / 2, cy - w / 2, size / 2 + w / 2, cy + w / 2], fill=(255, 204, 0, 255))
    return img

draw_icon(512, maskable=True).save(os.path.join(OUT, 'icon-512-maskable.png'))
draw_icon(512).save(os.path.join(OUT, 'icon-512.png'))
draw_icon(192).save(os.path.join(OUT, 'icon-192.png'))
draw_icon(180).save(os.path.join(OUT, 'apple-touch-icon.png'))

print('PWA 版已生成:')
for f in sorted(os.listdir(OUT)):
    print(' -', f, os.path.getsize(os.path.join(OUT, f)), 'B')
