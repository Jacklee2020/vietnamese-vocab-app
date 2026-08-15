#!/usr/bin/env python3
"""校验 pwa/index.html 内嵌词库与词库 CSV 是否一致。

防止修改 CSV 后忘记重新生成 HTML 导致线上数据与源数据不同步。
用法：python3 scripts/check_html_sync.py 词库_合并版.csv pwa/index.html
"""
import csv
import json
import re
import sys


def load_csv(path: str) -> list:
    with open(path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f))
    return rows[1:]  # 跳过表头


def load_html_words(path: str) -> list:
    html = open(path, encoding="utf-8").read()
    m = re.search(r"const WORDS_DATA = (\[.*?\]);", html, re.S)
    if not m:
        raise SystemExit("❌ 未在 HTML 中找到 WORDS_DATA 定义")
    return json.loads(m.group(1))


def main() -> int:
    if len(sys.argv) != 3:
        print("用法：python3 scripts/check_html_sync.py <csv路径> <html路径>")
        return 2

    csv_rows = load_csv(sys.argv[1])
    html_words = load_html_words(sys.argv[2])

    # CSV -> [分类, 越南语, 中文]
    csv_data = [(r[1].strip(), r[2].strip(), r[3].strip()) for r in csv_rows if len(r) >= 4]
    # HTML -> [分类, 越南语, 中文]
    html_data = [(w[0].strip(), w[1].strip(), w[2].strip()) for w in html_words]

    errors = []
    if len(csv_data) != len(html_data):
        errors.append(f"词条数不一致：CSV {len(csv_data)} vs HTML {len(html_data)}")

    csv_set = set(csv_data)
    html_set = set(html_data)

    only_csv = csv_set - html_set
    only_html = html_set - csv_set
    if only_csv:
        errors.append(f"CSV 有而 HTML 缺失 {len(only_csv)} 条，示例：{sorted(only_csv)[:3]}")
    if only_html:
        errors.append(f"HTML 有而 CSV 缺失 {len(only_html)} 条，示例：{sorted(only_html)[:3]}")

    if errors:
        print(f"❌ 词库不同步，共 {len(errors)} 个问题：")
        for e in errors[:10]:
            print("  -", e)
        return 1

    print(f"✅ 词库同步：CSV {len(csv_data)} 条 = HTML {len(html_data)} 条")
    return 0


if __name__ == "__main__":
    sys.exit(main())
