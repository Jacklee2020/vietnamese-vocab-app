#!/usr/bin/env python3
"""校验词库 CSV：格式、空值、重复、分类数量。用法：python3 scripts/validate_dict.py <csv路径>"""
import csv
import sys

EXPECTED_HEADER = ["序号", "分类", "越南语", "中文"]
MIN_WORDS = 3000
EXPECTED_CATEGORIES = 12


def main(path: str) -> int:
    with open(path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f))

    errors = []

    header = [c.strip() for c in rows[0]]
    if header != EXPECTED_HEADER:
        errors.append(f"表头错误：{header}，应为 {EXPECTED_HEADER}")

    data = rows[1:]
    if len(data) < MIN_WORDS:
        errors.append(f"词条数 {len(data)} < {MIN_WORDS}")

    seen_seq, seen_vi = set(), set()
    categories = set()
    for i, row in enumerate(data, start=2):
        if len(row) != 4:
            errors.append(f"第 {i} 行列数错误：{len(row)} 列 -> {row}")
            continue
        seq, cat, vi, zh = (c.strip() for c in row)
        if not (seq and cat and vi and zh):
            errors.append(f"第 {i} 行存在空值：{row}")
        if seq in seen_seq:
            errors.append(f"第 {i} 行序号重复：{seq}")
        seen_seq.add(seq)
        if vi in seen_vi:
            errors.append(f"第 {i} 行越南语重复：{vi}")
        seen_vi.add(vi)
        categories.add(cat)

    if len(categories) != EXPECTED_CATEGORIES:
        errors.append(f"分类数 {len(categories)} != {EXPECTED_CATEGORIES}：{sorted(categories)}")

    if errors:
        print(f"❌ 校验失败，共 {len(errors)} 个问题：")
        for e in errors[:50]:
            print("  -", e)
        return 1

    print(f"✅ 校验通过：{len(data)} 词 · {len(categories)} 大类")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("用法：python3 scripts/validate_dict.py <csv路径>")
        sys.exit(2)
    sys.exit(main(sys.argv[1]))
