# -*- coding: utf-8 -*-
"""把 PDF 全部页面拼成一张联系表，用来一眼找留白、掉页、图题错位。

用法：
    python contact_sheet.py output/report.pdf
    python contact_sheet.py output/report.pdf --dpi 110 --cols 4 --out out/sheet.png

比逐页翻 PDF 快一个数量级：一屏看完十页，空白页会自己跳出来。
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import fitz
from PIL import Image, ImageDraw

GAP = 12
LABEL_H = 22


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("--dpi", type=int, default=72)
    ap.add_argument("--cols", type=int, default=5)
    ap.add_argument("--out", default=None)
    ap.add_argument("--bg", default="#e9e9e4")
    args = ap.parse_args()

    src = Path(args.pdf)
    if not src.exists():
        print(f"找不到 {src}")
        return 1

    doc = fitz.open(src)
    thumbs = []
    for page in doc:
        pix = page.get_pixmap(dpi=args.dpi)
        thumbs.append(Image.frombytes("RGB", (pix.width, pix.height), pix.samples))

    cols = max(1, min(args.cols, len(thumbs)))
    rows = (len(thumbs) + cols - 1) // cols
    tw = max(t.width for t in thumbs)
    th = max(t.height for t in thumbs)

    sheet = Image.new("RGB", (cols * tw + (cols + 1) * GAP,
                              rows * (th + LABEL_H) + (rows + 1) * GAP), args.bg)
    draw = ImageDraw.Draw(sheet)
    for i, t in enumerate(thumbs):
        r, c = divmod(i, cols)
        x = GAP + c * (tw + GAP)
        y = GAP + r * (th + LABEL_H + GAP)
        sheet.paste(t, (x, y + LABEL_H))
        draw.text((x + 2, y + 4), f"p{i + 1}", fill="#333333")

    out = Path(args.out) if args.out else src.parent / "preview" / "contact_sheet.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)
    print(f"{len(thumbs)} 页 → {out}  ({sheet.width}×{sheet.height})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
