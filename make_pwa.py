# -*- coding: utf-8 -*-
"""生成可托管的 PWA 版静态资源（manifest.webmanifest + sw.js + 图标）。"""
import json
import os
import sys
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'pwa')

APP_NAME = "越南语千词斩"
APP_SHORT = "越南语千词斩"
APP_DESC = "越南语词汇学习 PWA · 4621 词 · 12 大类 · 离线可用"
THEME_COLOR = "#4aa3df"
CACHE_NAME = "vnvocab-v8"


def main() -> int:
    os.makedirs(OUT, exist_ok=True)

    # 1) manifest.webmanifest
    manifest = {
        "name": APP_NAME,
        "short_name": APP_SHORT,
        "description": APP_DESC,
        "lang": "zh-CN",
        "start_url": "./",
        "scope": "./",
        "display": "standalone",
        "background_color": "#f3f4f6",
        "theme_color": THEME_COLOR,
        "icons": [
            {"src": "icon-192.png", "sizes": "192x192", "type": "image/png"},
            {"src": "icon-512.png", "sizes": "512x512", "type": "image/png"},
            {"src": "icon-512-maskable.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"},
        ],
    }
    with open(os.path.join(OUT, 'manifest.webmanifest'), 'w', encoding='utf-8') as f:
        f.write(json.dumps(manifest, ensure_ascii=False, indent=2))

    # 2) Service Worker：HTML 走 network-first，静态资源 stale-while-revalidate
    sw = '''/* ''' + APP_NAME + ''' PWA 离线缓存 */
const CACHE = ''' + "'" + CACHE_NAME + "'" + ''';
const ASSETS = ['./', './index.html', './manifest.webmanifest', './icon-192.png', './icon-512.png', './icon-512-maskable.png', './apple-touch-icon.png'];
self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(ASSETS)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener('fetch', e => {
  if (e.request.method !== 'GET') return;
  if (e.request.mode === 'navigate') {
    e.respondWith(
      fetch(e.request).then(res => {
        const copy = res.clone();
        caches.open(CACHE).then(c => c.put(e.request, copy));
        return res;
      }).catch(() => caches.match(e.request).then(hit => hit || caches.match('./index.html')))
    );
    return;
  }
  e.respondWith(
    caches.match(e.request).then(hit => {
      const refresh = fetch(e.request).then(res => {
        const copy = res.clone();
        caches.open(CACHE).then(c => c.put(e.request, copy));
        return res;
      }).catch(() => hit);
      return hit || refresh;
    })
  );
});
'''
    with open(os.path.join(OUT, 'sw.js'), 'w', encoding='utf-8') as f:
        f.write(sw)

    # 3) 图标生成
    def draw_icon(size, maskable=False):
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        r = int(size * 0.22)
        grad = Image.new('RGBA', (size, size))
        gd = ImageDraw.Draw(grad)
        for y in range(size):
            t = y / size
            col = (int(74 + 57 * t), int(163 + 33 * t), int(223 + 16 * t), 255)
            gd.line([(0, y), (size, y)], fill=col)
        mask = Image.new('L', (size, size), 0)
        ImageDraw.Draw(mask).rounded_rectangle([0, 0, size - 1, size - 1], radius=r, fill=255)
        img.paste(grad, (0, 0), mask)
        w = int(size * 0.20)
        x0, x1 = size * 0.22, size * 0.78
        y_top, y_bot = size * 0.26, size * 0.74
        vcol = (255, 255, 255, 255)
        d.line([(x0, y_top), (size / 2, y_bot)], fill=vcol, width=w)
        d.line([(size / 2, y_bot), (x1, y_top)], fill=vcol, width=w)
        cy = size * 0.82
        d.ellipse([size / 2 - w / 2, cy - w / 2, size / 2 + w / 2, cy + w / 2], fill=(255, 204, 0, 255))
        return img

    draw_icon(512, maskable=True).save(os.path.join(OUT, 'icon-512-maskable.png'))
    draw_icon(512).save(os.path.join(OUT, 'icon-512.png'))
    draw_icon(192).save(os.path.join(OUT, 'icon-192.png'))
    draw_icon(180).save(os.path.join(OUT, 'apple-touch-icon.png'))

    print('PWA 资源生成完毕:')
    for f in sorted(os.listdir(OUT)):
        print(' -', f, os.path.getsize(os.path.join(OUT, f)), 'B')
    return 0


if __name__ == "__main__":
    sys.exit(main())
