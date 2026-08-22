# -*- coding: utf-8 -*-
"""从单文件 App 生成可托管的 PWA 版（index.html + manifest + sw + 图标）。

注意：仓库根目录的「越南语背单词App.html」是内部工作文件（已被 .gitignore 排除），
clone 后请把该文件放回仓库根目录再运行本脚本；若源文件不存在，脚本会直接退出。
"""
import json, os, sys
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, '越南语背单词App.html')
OUT = os.path.join(HERE, 'pwa')

# manifest / sw 当前版本常量（与仓库中 pwa/ 目录保持一致，修改时请同步）
APP_NAME = "越南语千词斩"
APP_SHORT = "越南语千词斩"
APP_DESC = "越南语词汇学习 PWA · 3378 词 · 12 大类 · 离线可用"
THEME_COLOR = "#4aa3df"
CACHE_NAME = "vnvocab-v7"

def main() -> int:
    if not os.path.exists(SRC):
        print("❌ 未找到源文件：越南语背单词App.html（内部工作文件，未随仓库发布）")
        print("   请将该文件放回仓库根目录后重试。")
        return 1

    os.makedirs(OUT, exist_ok=True)
    html = open(SRC, encoding='utf-8').read()

    # 1) head 注入 manifest / apple-touch-icon
    head_add = ('<link rel="icon" href="apple-touch-icon.png">\n'
                '<link rel="manifest" href="manifest.webmanifest">\n'
                '<link rel="apple-touch-icon" href="apple-touch-icon.png">\n'
                '<meta name="apple-mobile-web-app-title" content="' + APP_SHORT + '">\n'
                '<meta name="apple-mobile-web-app-capable" content="yes">\n')
    assert '<meta name="theme-color"' in html
    html = html.replace('<meta name="theme-color" content="#e8452c">',
                        head_add + '<meta name="theme-color" content="' + THEME_COLOR + '">', 1)

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
    open(os.path.join(OUT, 'manifest.webmanifest'), 'w', encoding='utf-8').write(json.dumps(manifest, ensure_ascii=False, indent=2))

    # 4) Service Worker：HTML 走 network-first，静态资源 stale-while-revalidate
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
    open(os.path.join(OUT, 'sw.js'), 'w', encoding='utf-8').write(sw)

    # 5) 图标
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

    print('PWA 版已生成:')
    for f in sorted(os.listdir(OUT)):
        print(' -', f, os.path.getsize(os.path.join(OUT, f)), 'B')
    return 0


if __name__ == "__main__":
    sys.exit(main())
