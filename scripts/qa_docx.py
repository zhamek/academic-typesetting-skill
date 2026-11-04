# -*- coding: utf-8 -*-
"""DOCX 交付闸：把 Word 成品当成要交的东西来量。

PDF 那边有 qa_pdf.py，Word 这边一直没人管——`fix_docx_tables.py` 修完三线表，
到底修没修对，只能靠肉眼。这个脚本补上。

用法：
    python qa_docx.py output/report.docx
    python qa_docx.py output/report.docx --lang zh --strict

检查项见 references/non-latex.md §6 与 qa-gate.md。
"""
from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from pathlib import Path

from docx import Document
from docx.oxml.ns import qn
from docx.shared import Emu

A4 = (210, 297)  # mm
BORDER_KEYS = ("top", "bottom", "left", "right", "insideH", "insideV")


class Report:
    def __init__(self):
        self.items: list[tuple[str, str, str]] = []

    def add(self, level: str, name: str, detail: str = ""):
        self.items.append((level, name, detail))
        print(f"[{level}] {name}" + (f" — {detail}" if detail else ""))

    @property
    def failed(self) -> int:
        return sum(1 for lv, _, _ in self.items if lv == "FAIL")

    @property
    def warned(self) -> int:
        return sum(1 for lv, _, _ in self.items if lv == "WARN")


def table_borders(tbl) -> dict[str, str]:
    """读 tblPr/tblBorders，返回 {边: val}；未显式设置时返回空。"""
    tblPr = tbl._tbl.tblPr
    if tblPr is None:
        return {}
    el = tblPr.find(qn("w:tblBorders"))
    if el is None:
        return {}
    out = {}
    for key in BORDER_KEYS:
        node = el.find(qn(f"w:{key}"))
        if node is not None:
            out[key] = node.get(qn("w:val")) or "single"
    return out


def effective_dpi(shape, doc) -> float | None:
    """内嵌图的像素宽 / 显示宽(inch)。"""
    try:
        blip = shape._inline.graphic.graphicData.pic.blipFill.blip
        rid = blip.get(qn("r:embed"))
        part = doc.part.related_parts[rid]
        px_w = part.image.size[0]
        inch_w = Emu(shape.width).inches if shape.width else 0
        return px_w / inch_w if inch_w else None
    except Exception:
        return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("docx")
    ap.add_argument("--lang", default="zh", choices=["zh", "en"])
    ap.add_argument("--strict", action="store_true")
    args = ap.parse_args()

    path = Path(args.docx)
    if not path.exists():
        print(f"FAIL: 文件不存在 {path}")
        return 1
    doc = Document(str(path))
    r = Report()

    paras = doc.paragraphs
    body = [p for p in paras if p.text.strip()]
    r.add("PASS" if body else "FAIL", "文档非空", f"{len(body)} 段正文")
    r.add("PASS" if doc.tables else "PASS", "表格数", str(len(doc.tables)))

    # ---------- 页面 ----------
    # 参考模板常常不写 w:pgSz，此时 python-docx 返回 None，不能直接换算
    sec = doc.sections[0]
    w_mm = round(Emu(sec.page_width).mm) if sec.page_width else None
    h_mm = round(Emu(sec.page_height).mm) if sec.page_height else None
    if w_mm and h_mm:
        r.add("PASS" if abs(w_mm - A4[0]) <= 2 and abs(h_mm - A4[1]) <= 2 else "WARN",
              "纸张 A4", f"{w_mm}×{h_mm} mm")
    else:
        r.add("WARN", "纸张 A4", "文档未显式设置页面尺寸（Word 默认 Letter）——导出 PDF 前手动改 A4")

    margins = [round(Emu(m).cm, 1) for m in
               (sec.top_margin, sec.bottom_margin, sec.left_margin, sec.right_margin) if m]
    if margins:
        r.add("PASS" if min(margins) >= 1.5 else "WARN", "页边距 ≥1.5cm",
              " / ".join(map(str, margins)) + " cm")
    else:
        r.add("WARN", "页边距 ≥1.5cm", "未设置，用 Word 默认")

    # ---------- 字体 ----------
    normal = doc.styles["Normal"]
    latin = normal.font.name or ""
    east = None
    try:
        east = normal.element.rPr.rFonts.get(qn("w:eastAsia"))
    except Exception:
        pass
    r.add("PASS" if latin and east else "WARN", "正文中英文字体分设",
          f"西文 {latin or '未设'} / 中文 {east or '未设'}")

    # ---------- 三线表 ----------
    ugly = []
    for i, t in enumerate(doc.tables, 1):
        b = table_borders(t)
        if not b:
            continue
        for key in ("left", "right", "insideV"):
            val = b.get(key, "nil")
            if val not in ("nil", "none", "0"):
                ugly.append(f"表{i} {key}={val}")
    r.add("PASS" if not ugly else "WARN", "表格无竖线",
          "无竖线" if not ugly else "仍有: " + ", ".join(ugly[:4]))

    # ---------- 题注 ----------
    caption_paras = [p for p in paras if "caption" in p.style.name.lower() or "题注" in p.style.name]
    n_float = len(doc.tables) + len(doc.inline_shapes)
    if n_float and not caption_paras:
        r.add("WARN", "题注样式", f"{n_float} 个图表但没有题注段落")
    else:
        r.add("PASS", "题注样式", f"{len(caption_paras)} 条题注")

    # ---------- 图片 ----------
    low = []
    for i, s in enumerate(doc.inline_shapes, 1):
        dpi = effective_dpi(s, doc)
        if dpi and dpi < 300:
            low.append(f"图{i} {dpi:.0f}dpi")
    r.add("PASS" if not low else "WARN", "插图 ≥300dpi",
          f"{len(doc.inline_shapes)} 张图" if not low else ", ".join(low[:4]))

    # ---------- 字号一致性 ----------
    sizes = Counter(round(p.style.font.size.pt) for p in body if p.style.font.size)
    if sizes:
        common = sizes.most_common(1)[0][0]
        r.add("PASS", "正文字号", f"{common} pt（{sizes.most_common(1)[0][1]} 段）")

    # ---------- 残留 ----------
    text = "\n".join(p.text for p in paras) + "\n".join(
        c.text for t in doc.tables for row in t.rows for c in row.cells)
    for token in ("??", "TODO", "{{", "[@", "undefined"):
        r.add("PASS" if token not in text else "FAIL", f"无残留 {token!r}")

    # ---------- 元数据 ----------
    core = doc.core_properties
    ok = bool((core.title or "").strip()) and bool((core.author or "").strip())
    r.add("PASS" if ok else "WARN", "文档属性",
          f"{core.title or '—'} / {core.author or '—'}" if ok else "title 或 author 为空")

    print(f"\nFAIL {r.failed} · WARN {r.warned} · 共 {len(r.items)} 项")
    return 1 if (r.failed or (args.strict and r.warned)) else 0


if __name__ == "__main__":
    sys.exit(main())
