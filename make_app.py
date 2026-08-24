# -*- coding: utf-8 -*-
"""把 词库_合并版.csv 的词条嵌入 template.html，生成单文件离线 App。"""
import csv
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CSV_SRC = os.path.join(HERE, '词库_合并版.csv')
TPL_SRC = os.path.join(HERE, 'template.html')
DST_APP = os.path.join(HERE, '越南语背单词App.html')


def main():
    if not os.path.exists(CSV_SRC):
        print(f"❌ 未找到词库文件：{CSV_SRC}")
        return 1

    with open(CSV_SRC, encoding='utf-8-sig', newline='') as f:
        rows = list(csv.reader(f))[1:]

    # [分类, 越南语, 中文]
    data = [[r[1].strip(), r[2].strip(), r[3].strip()] for r in rows if len(r) >= 4]

    with open(TPL_SRC, encoding='utf-8') as f:
        tpl = f.read()

    payload = json.dumps(data, ensure_ascii=False).replace('</', '<\\/')
    assert '/*__DATA__*/' in tpl, "模板中未找到 /*__DATA__*/ 占位符"

    out = tpl.replace('/*__DATA__*/', payload)
    with open(DST_APP, 'w', encoding='utf-8') as f:
        f.write(out)

    print(f"✅ 词条数: {len(data)}")
    print(f"✅ 输出: {DST_APP}")
    print(f"✅ 大小: {os.path.getsize(DST_APP) / 1024:.1f} KB")
    return 0


if __name__ == '__main__':
    sys.exit(main())
