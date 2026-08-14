# -*- coding: utf-8 -*-
"""把 out_20260811c/vocab_data.py 的词条嵌入 template.html，生成单文件离线 App。"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'out_20260811c'))
from vocab_data import WORDS  # noqa: E402

data = [[w[0], w[1], w[2]] for w in WORDS]
tpl = open(os.path.join(HERE, 'template.html'), encoding='utf-8').read()
payload = json.dumps(data, ensure_ascii=False).replace('</', '<\\/')
assert '/*__DATA__*/' in tpl
out = tpl.replace('/*__DATA__*/', payload)
dst = os.path.join(HERE, '越南语背单词App.html')
open(dst, 'w', encoding='utf-8').write(out)
print('词条数:', len(data))
print('输出:', dst)
print('大小: %.1f KB' % (os.path.getsize(dst) / 1024))
