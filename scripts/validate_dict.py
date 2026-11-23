#!/usr/bin/env python3
"""校验词库 CSV 与 Excel：格式、空值、大小写去重、OCR 音节完整性、中越文纯净度及 Excel 同步。
用法：python3 scripts/validate_dict.py <csv路径>
"""
import csv
import os
import re
import sys
import zipfile

EXPECTED_HEADER = ["序号", "分类", "越南语", "中文"]
MIN_WORDS = 3000
EXPECTED_CATEGORIES = 12

V = (
    "aàáảãạăằắẳẵặâầấẩẫậeèéẻẽẹêềếểễệiìíỉĩịoòóỏõọôồốổỗộơờớởỡợuùúủũụưừứửữựyỳýỷỹỵ"
    "AÀÁẢÃẠĂẰẮẲẴẶÂẦẤẨẪẬEÈÉẺẼẸÊỀẾỂỄỆIÌÍỈĨỊOÒÓỎÕỌÔỒỐỔỖỘƠỜỚỞỠỢUÙÚỦŨỤƯỪỨỬỮỰYỲÝỶỸỴ"
)
VI_SYL_RE = re.compile(
    rf"^(ngh|ng|nh|ch|th|ph|kh|gh|tr|gi|qu|[bcdfghklmnpqrstvxđ])?[{V}]{{1,3}}(ch|ng|nh|[cmnpt])?$",
    re.I,
)
HAN_RE = re.compile(r"[\u4e00-\u9fff]")

ALLOWED_LOANWORDS = {
    "wifi", "internet", "video", "camera", "calo", "vitamin", "taxi", "menu", "coca",
    "americano", "mayonnaise", "basa", "diesel", "visa", "size", "top", "gym", "oxi",
    "niken", "unesco", "google", "michelin", "lotte", "gatô", "ôtô", "nilông", "ipad",
    "online", "ship", "mini", "cotton", "gas", "vali", "sofa", "container", "email",
    "fax", "tnhh", "marketing", "otp", "gtgt", "vat", "zalopay", "atm", "qr", "code",
    "hsd", "nsx", "myanmar", "malaysia", "singapore", "pattaya", "tp", "hcm", "s",
    "m", "l", "xl", "b", "x", "cacbonic", "cacbondioxit",
}


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

    seen_seq, seen_vi_lower = set(), {}
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

        vi_key = vi.lower()
        if vi_key in seen_vi_lower:
            errors.append(f"第 {i} 行越南语重复：{vi}（与第 {seen_vi_lower[vi_key]} 行冲突）")
        seen_vi_lower[vi_key] = i
        categories.add(cat)

        # 校验越南语字段不含中文字符、不含 OCR 断裂音节或英文释义残留
        if HAN_RE.search(vi):
            errors.append(f"第 {i} 行越南语含中文字符：{vi}")
        tokens = re.findall(rf"[a-zA-Z{V}đĐī]+", vi)
        bad_tokens = [
            t for t in tokens
            if not VI_SYL_RE.match(t) and t.lower() not in ALLOWED_LOANWORDS
        ]
        if bad_tokens:
            errors.append(f"第 {i} 行越南语含非标准音节或英文残留：{vi} -> {bad_tokens}")

        # 校验中文字段包含汉字且无页眉残留
        if not HAN_RE.search(zh):
            errors.append(f"第 {i} 行中文释义缺失汉字：{zh}")
        if "PROFICIENCY" in zh or "TESTS FOR" in zh:
            errors.append(f"第 {i} 行中文释义含页眉残留：{zh}")

    if len(categories) != EXPECTED_CATEGORIES:
        errors.append(f"分类数 {len(categories)} != {EXPECTED_CATEGORIES}：{sorted(categories)}")

    # 若同目录存在同名 .xlsx，校验 Excel 行数同步
    xlsx_path = os.path.splitext(path)[0] + ".xlsx"
    if os.path.exists(xlsx_path):
        try:
            with zipfile.ZipFile(xlsx_path, "r") as z:
                sheet_xml = z.read("xl/worksheets/sheet1.xml").decode("utf-8")
            expected_ref = f'dimension ref="A1:D{len(data) + 1}"'
            if expected_ref not in sheet_xml:
                errors.append(f"Excel 文件 {os.path.basename(xlsx_path)} 行数与 CSV ({len(data)} 词) 不同步")
        except Exception as e:
            errors.append(f"Excel 文件读取失败：{e}")

    if errors:
        print(f"❌ 校验失败，共 {len(errors)} 个问题：")
        for e in errors[:50]:
            print("  -", e)
        return 1

    print(f"✅ 校验通过：{len(data)} 词 · {len(categories)} 大类（含音节纯净度与 Excel 同步校验）")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("用法：python3 scripts/validate_dict.py <csv路径>")
        sys.exit(2)
    sys.exit(main(sys.argv[1]))
