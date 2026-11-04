# -*- coding: utf-8 -*-
"""交付闸：把一个 PDF 当作成品来量，而不是当作源码来看。

用法：
    python qa_pdf.py report.pdf
    python qa_pdf.py report.pdf --lang zh --fonts SimSun,SimHei,TimesNewRoman
    python qa_pdf.py report.pdf --log build.log --strict

输出 PASS / WARN / FAIL。有 FAIL 时退出码 1；加 --strict 则 WARN 也算失败。

检查依据见 references/qa-gate.md；每种失败对应的修法也在那里。
"""
from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from pathlib import Path

import fitz

# 数学/图表库的默认字体混进正文，通常意味着某处静默回退
MATH_FALLBACK = ("LatinModernMath", "DejaVu", "AsanaMath", "STIX")
# 整篇用 Latin Modern 的文档（LuaTeX 默认）是另一种情况：先看声明的字体是否生效，
# 全都缺席才提示，不能把"故意用 LM"当成错误。
TEXT_FALLBACK = ("LMRoman", "Nimbus", "Liberation", "Bitstream", "FreeSerif", "TeXGyre")

A4 = (595.28, 841.89)
LETTER = (612.0, 792.0)

CAPTION_PREFIX = re.compile(r"^\s*(表|图)\s*(\d{1,3})")
CAPTION_PREFIX_EN = re.compile(r"^\s*(Table|Figure)\s*(\d{1,3})", re.I)


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


def body_zone(page_height: float, header_pt: float = 60, footer_pt: float = 55):
    return header_pt, page_height - footer_pt


def collect_blocks(doc):
    """返回 [(页码, x0, y0, x1, y1, 文本, 字号)]，已去掉页眉页脚区。"""
    out = []
    for pno, page in enumerate(doc, 1):
        top, bot = body_zone(page.rect.height)
        for block in page.get_text("dict")["blocks"]:
            if block.get("type") != 0:
                continue
            x0, y0, x1, y1 = block["bbox"]
            if y1 <= top or y0 >= bot:
                continue
            text = " ".join(
                span["text"] for line in block.get("lines", []) for span in line.get("spans", [])
            ).strip()
            if not text:
                continue
            size = max((s["size"] for line in block.get("lines", []) for s in line.get("spans", [])),
                       default=0.0)
            out.append((pno, x0, y0, x1, y1, text, size))
    return out


def content_bottom(doc, pno):
    """该页正文区最低的内容位置，含图片与矢量线条，不含页眉页脚。

    多栏排版里 PyMuPDF 常把整页文字合并成一个跨越页底的大 block（y1 落进页脚带），
    所以这里把每个 bbox 先裁进正文区再取底边，而不是整块丢弃。
    """
    page = doc[pno - 1]
    top, bot = body_zone(page.rect.height)
    low = top
    for kind, bbox in page.get_bboxlog():
        if kind == "ignore":
            continue
        y0, y1 = bbox[1], bbox[3]
        if y1 <= top or y0 >= bot:
            continue
        low = max(low, min(y1, bot))
    return low


def main() -> int:
    ap = argparse.ArgumentParser(description="PDF 交付闸")
    ap.add_argument("pdf")
    ap.add_argument("--lang", default="zh", choices=["zh", "en"])
    ap.add_argument("--fonts", default="SimSun,SimHei,TimesNewRoman",
                    help="期望出现的字体族，逗号分隔子串")
    ap.add_argument("--log", default=None, help="xelatex/pandoc 日志，用于统计 Overfull")
    ap.add_argument("--max-pages", type=int, default=None)
    ap.add_argument("--strict", action="store_true", help="WARN 也返回非零")
    args = ap.parse_args()

    path = Path(args.pdf)
    if not path.exists():
        print(f"FAIL: 文件不存在 {path}")
        return 1

    doc = fitz.open(path)
    r = Report()

    # ---------- 基本 ----------
    r.add("PASS" if doc.page_count else "FAIL", "页数", f"{doc.page_count} 页")
    if args.max_pages:
        r.add("PASS" if doc.page_count <= args.max_pages else "FAIL",
              "页数上限", f"{doc.page_count} ≤ {args.max_pages}")

    w, h = doc[0].rect.width, doc[0].rect.height
    is_a4 = abs(w - A4[0]) < 3 and abs(h - A4[1]) < 3
    is_letter = abs(w - LETTER[0]) < 3 and abs(h - LETTER[1]) < 3
    r.add("PASS" if (is_a4 or is_letter) else "FAIL",
          "页面几何", f"{w:.0f}×{h:.0f} pt ({'A4' if is_a4 else 'Letter' if is_letter else '非标准'})")

    # ---------- 字体 ----------
    fonts = {}
    for page in doc:
        for f in page.get_fonts(full=True):
            xref, ext, _type, basefont = f[0], f[1], f[2], f[3]
            fonts[basefont] = ext
    not_embedded = [n for n, ext in fonts.items() if ext in ("n/a", "", None)]
    r.add("PASS" if not not_embedded else "FAIL", "字体嵌入",
          "全部嵌入" if not not_embedded else f"未嵌入: {', '.join(not_embedded[:4])}")

    math_fb = sorted({n for n in fonts if any(k.lower() in n.lower() for k in MATH_FALLBACK)})
    r.add("PASS" if not math_fb else "WARN", "无数学回退字体",
          "干净" if not math_fb else f"出现 {', '.join(math_fb[:3])}（图内 mathtext 或 $>$）")

    declared = [s.strip() for s in args.fonts.split(",") if s.strip()]
    hits = [fam for fam in declared
            if any(fam.lower().replace(" ", "") in n.lower().replace(" ", "") for n in fonts)]
    if declared and not hits:
        text_fb = sorted({n for n in fonts if any(k.lower() in n.lower() for k in TEXT_FALLBACK)})
        hint = f"，正文用的是 {', '.join(text_fb[:2])}" if text_fb else ""
        r.add("WARN", "字体族约定",
              f"声明的 {len(declared)} 个字体族都没用上{hint}；换了字体栈请用 --fonts 指定")
    elif declared and len(hits) < len(declared):
        r.add("WARN", "字体族约定", f"缺少 {', '.join(f for f in declared if f not in hits)}")
    elif declared:
        r.add("PASS", "字体族约定", "、".join(hits) + " 均生效")

    # ---------- 版面 ----------
    blocks = collect_blocks(doc)
    if blocks:
        sizes = Counter(round(b[6] * 2) / 2 for b in blocks)
        body_size = sizes.most_common(1)[0][0]
    else:
        body_size = 0

    bottoms = {p: content_bottom(doc, p) for p in range(1, doc.page_count + 1)}
    top_edge = body_zone(h)[0]
    full = max((b for p, b in bottoms.items() if p != doc.page_count), default=top_edge)
    short = []
    for p, b in bottoms.items():
        if p == doc.page_count:
            continue
        ratio = (b - top_edge) / max(full - top_edge, 1)
        if ratio < 0.85:
            short.append(f"p{p} {ratio:.0%}")
    r.add("PASS" if not short else "WARN", "页填充率 ≥85%",
          "各页饱满" if not short else f"偏空: {', '.join(short)}")

    margin = 1.5 / 2.54 * 72
    outside = [(b[0], round(b[1])) for b in blocks if b[1] < margin - 3 or b[3] > w - margin + 3]
    r.add("PASS" if not outside else "FAIL", "内容不越界",
          "正常" if not outside else f"{outside[:3]}")

    # ---------- 图 ----------
    raster = []
    for pno, page in enumerate(doc, 1):
        for img in page.get_images(full=True):
            for rect in page.get_image_rects(img[0]):
                if rect.width <= 0:
                    continue
                dpi = img[2] * 72 / rect.width
                if dpi < 300:
                    raster.append(f"p{pno} {dpi:.0f}dpi")
    r.add("PASS" if not raster else "WARN", "插图分辨率",
          "全为矢量或 ≥300dpi" if not raster else f"偏低: {', '.join(raster[:4])}")

    # ---------- 编号连续性 ----------
    seq = {"表": [], "图": []}
    for pno, x0, y0, x1, y1, text, size in blocks:
        pat = CAPTION_PREFIX_EN if args.lang == "en" else CAPTION_PREFIX
        m = pat.match(text)
        if not m:
            continue
        kind = m.group(1)
        centered = abs((x0 + x1) / 2 - w / 2) < 30
        # 题注通常比正文小一号；正文里"表 1 汇总了……"这类句子字号等于正文、且以句号收尾，
        # 不能算题注，否则编号序列会出现重复。
        is_caption = (size <= body_size - 0.3) or (
            centered and len(text) < 55 and not any(p in text for p in "。，；：")
        )
        if is_caption:
            seq.setdefault(kind if kind in seq else kind, []).append(int(m.group(2)))
    bad = []
    for kind, nums in seq.items():
        if not nums:
            continue
        if nums != list(range(1, len(nums) + 1)):
            bad.append(f"{kind}: {nums}")
    r.add("PASS" if not bad else "WARN", "图表编号连续",
          "1..n" if not bad else "跳号/重号 " + "; ".join(bad))

    # ---------- 残留 ----------
    text_all = "".join(p.get_text() for p in doc)
    for token in ("??", "[@", "**", "undefined", "TODO", "待补"):
        r.add("PASS" if token not in text_all else "FAIL", f"无残留 {token!r}")

    # ---------- 元数据 ----------
    md = doc.metadata or {}
    ok_meta = bool((md.get("title") or "").strip()) and bool((md.get("author") or "").strip())
    r.add("PASS" if ok_meta else "WARN", "PDF 元数据",
          f"{md.get('title','')} / {md.get('author','')}" if ok_meta else "title 或 author 为空")

    # ---------- 日志 ----------
    if args.log and Path(args.log).exists():
        log = Path(args.log).read_text(encoding="utf-8", errors="replace")
        over = len(re.findall(r"Overfull \\hbox", log))
        flo = len(re.findall(r"Float too large", log))
        und = len(re.findall(r"Reference .* undefined", log))
        r.add("PASS" if over == 0 else "WARN", "日志 Overfull",
              "无" if over == 0 else f"{over} 处（列宽/图宽/长英文串）")
        if flo:
            r.add("WARN", "浮动体超页高", f"{flo} 处")
        if und:
            r.add("FAIL", "未解析引用", f"{und} 处（补编一轮）")

    print(f"\nFAIL {r.failed} · WARN {r.warned} · 共 {len(r.items)} 项")
    if r.failed or (args.strict and r.warned):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
