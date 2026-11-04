# -*- coding: utf-8 -*-
"""把 pandoc markdown 的管道表换成定宽三线表（raw LaTeX）。

pandoc 默认把管道表写成等宽 longtable——四列各占 1/4，中文短文被拆成两三行、
长文被拉散。这个脚本按给定列宽重写成 `tabular` + booktabs，保留原有文字。

用法：
    python md_tables_to_latex.py src/report.qmd --widths 2.2,4.45,4.45,3.95
    python md_tables_to_latex.py src/report.qmd --widths ... --floats H,t,H,t --write

--floats 按表格出现顺序指定占位策略（H 精确 / t 页顶 / b 页底 / htb 交给 LaTeX），
个数不够时循环使用。

只处理"|---|---|"式管道表；表后紧跟的 `: 题注` 行会被吃进 caption。
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

SEP = re.compile(r"^\|[\s:|-]+\|\s*$")


def is_row(line: str) -> bool:
    return line.lstrip().startswith("|") and line.rstrip().endswith("|")


def split_cells(line: str) -> list[str]:
    inner = line.strip()[1:-1]
    return [c.strip() for c in inner.split("|")]


def md_to_latex(text: str) -> str:
    """只做表格里真正会遇到的几种转换。"""
    t = text
    # 数学里的简单上下标：CO$_2$ / g$^{-1}$ / $>$
    t = re.sub(r"\$([<>=])\$", r"\1", t)
    t = re.sub(r"\$_\s*\{?([0-9A-Za-z+\-]+)\}?\s*\$", r"\\textsubscript{\1}", t)
    t = re.sub(r"\$\^\s*\{?([0-9A-Za-z+\-]+)\}?\s*\$", r"\\textsuperscript{\1}", t)
    t = t.replace("%", r"\%")
    # markdown 斜体 -> \textit（不处理嵌套）
    t = re.sub(r"(?<!\w)\*([^*]+)\*(?!\w)", r"\\textit{\1}", t)
    t = re.sub(r"(?<!\\)_", r"\\_", t)
    return t


def build_table(rows: list[list[str]], caption: str, widths: list[float], place: str) -> str:
    ncol = len(rows[0])
    if len(widths) != ncol:
        raise ValueError(f"列宽 {len(widths)} 与表格列数 {ncol} 不一致")
    spec = "@{}" + "".join(f"L{{{w}cm}}" for w in widths) + "@{}"
    head, body = rows[0], rows[1:]
    out = [
        "```{=latex}",
        f"\\begin{{table}}[{place}]",
        "\\centering",
        f"\\caption{{{md_to_latex(caption)}}}",
        "\\small",
        "\\setlength{\\tabcolsep}{4.5pt}",
        f"\\begin{{tabular}}{{{spec}}}",
        "\\toprule",
        " & ".join(md_to_latex(c) for c in head) + r" \\",
        "\\midrule",
    ]
    out += [" & ".join(md_to_latex(c) for c in r) + r" \\" for r in body]
    out += ["\\bottomrule", "\\end{tabular}", "\\end{table}", "```"]
    return "\n".join(out)


def convert(text: str, widths: list[float], floats: list[str]) -> tuple[str, int]:
    lines = text.split("\n")
    out: list[str] = []
    i = 0
    idx = 0
    while i < len(lines):
        if is_row(lines[i]) and i + 1 < len(lines) and SEP.match(lines[i + 1]):
            block: list[str] = []
            while i < len(lines) and is_row(lines[i]):
                block.append(lines[i])
                i += 1
            # 跳过分隔行
            if block and SEP.match(block[0]):
                block = block[1:]
            elif len(block) > 1 and SEP.match(block[1]):
                block = [block[0]] + block[2:]
            caption = ""
            j = i
            while j < len(lines) and not lines[j].strip():
                j += 1
            if j < len(lines) and lines[j].lstrip().startswith(":"):
                caption = lines[j].lstrip().lstrip(":").strip()
                i = j + 1
            rows = [split_cells(r) for r in block]
            out.append(build_table(rows, caption, widths, floats[idx % len(floats)]))
            idx += 1
            continue
        out.append(lines[i])
        i += 1
    return "\n".join(out), idx


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("md")
    ap.add_argument("--widths", required=True, help="逗号分隔，单位 cm，如 2.2,4.45,4.45,3.95")
    ap.add_argument("--floats", default="H", help="逗号分隔：H/t/b/htbp")
    ap.add_argument("--out", default=None)
    ap.add_argument("--write", action="store_true", help="就地覆盖")
    args = ap.parse_args()

    src = Path(args.md)
    widths = [float(w) for w in args.widths.split(",")]
    floats = [f.strip() for f in args.floats.split(",")]
    total = sum(widths) + 0.315 * (len(widths) - 1)   # 3×4.5pt 列间距 ≈ 0.315cm
    print(f"列宽合计 {sum(widths):.2f} cm + 列间距 {total - sum(widths):.2f} cm = {total:.2f} cm（版心 16.0）")

    text = src.read_text(encoding="utf-8")
    new, n = convert(text, widths, floats)
    dst = Path(args.out) if args.out else src
    if args.write or args.out:
        dst.write_text(new, encoding="utf-8")
        print(f"转换 {n} 张表 → {dst}")
    else:
        sys.stdout.write(new[:800])
        print(f"\n…（共 {n} 张表，未写入；加 --write 落盘）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
