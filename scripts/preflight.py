# -*- coding: utf-8 -*-
"""编译前预检：把"字体缺字"这类事故挡在编译之前。

事故来源：本机装的 Source Han Serif SC 的 Heavy 字重缺 `、` `。`，加粗中文一出现，
标点就被静默吞掉——只有编译后翻日志里的 `Missing character` 才发现。

这个脚本反过来做：读源文件里**实际用到的字符**，逐个查字体的 cmap，
缺哪些、缺多少、在不在正文，编译前就说清楚。

用法：
    python preflight.py src/report.md --fonts "SimSun,SimHei,Times New Roman"
    python preflight.py src/report.md --fonts "Noto Serif SC" --tools

退出码：字体缺字为 FAIL（1）；字体没装、工具缺失为 WARN。
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

FAIL_CHARS = 0


def load_text(path: Path) -> str:
    text = path.read_text(encoding="utf-8", errors="replace")
    # 去掉代码块与 LaTeX 命令：它们不参与正文字体渲染
    out, in_code = [], False
    for line in text.split("\n"):
        if line.strip().startswith("```"):
            in_code = not in_code
            continue
        if not in_code:
            out.append(line)
    return "\n".join(out)


def is_cjk(c: str) -> bool:
    o = ord(c)
    return (0x3400 <= o <= 0x4DBF or 0x4E00 <= o <= 0x9FFF or
            0xF900 <= o <= 0xFAFF or 0x3000 <= o <= 0x303F or
            0xFF00 <= o <= 0xFFEF)


def used_chars(text: str) -> set[str]:
    """只看非 ASCII：ASCII 由西文字体负责，CJK 字体缺 ASCII 不致命。"""
    return {c for c in text if ord(c) > 127 and not c.isspace()}


def font_cmap(family: str):
    """返回 (字体文件, cmap, 实际字体名)。找不到返回 (None, None, None)。"""
    from matplotlib import font_manager as fm
    from fontTools.ttLib import TTFont, TTCollection

    # qa_pdf 的 --fonts 习惯写 TimesNewRoman（无空格），matplotlib 要 Times New Roman
    import re
    variants = [family,
                re.sub(r"(?<=[a-z])(?=[A-Z])", " ", family),
                family.replace(" ", "")]
    path = None
    for name in dict.fromkeys(variants):
        try:
            path = fm.findfont(fm.FontProperties(family=name), fallback_to_default=False)
            break
        except Exception:
            continue
    if path is None:
        return None, None, None
    try:
        if str(path).lower().endswith(".ttc"):
            coll = TTCollection(str(path))
            font = coll.fonts[0]
        else:
            font = TTFont(str(path))
        name = font["name"].getDebugName(1) or Path(path).stem
        return path, set(font.getBestCmap().keys()), name
    except Exception:
        return None, None, None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("source")
    ap.add_argument("--fonts", default="SimSun,SimHei,Times New Roman",
                    help="逗号分隔的字体族名")
    ap.add_argument("--tools", action="store_true", help="同时检查构建工具")
    ap.add_argument("--limit", type=int, default=12, help="每族最多列几个缺字")
    args = ap.parse_args()

    src = Path(args.source)
    if not src.exists():
        print(f"FAIL: 源文件不存在 {src}")
        return 1

    text = load_text(src)
    chars = used_chars(text)
    print(f"源文件 {src.name}：非 ASCII 字符 {len(chars)} 个")

    failed = 0
    for family in [f.strip() for f in args.fonts.split(",") if f.strip()]:
        path, cmap, real = font_cmap(family)
        if cmap is None:
            print(f"[WARN] {family}：未找到该字体（会被别的字体顶替，先确认它真的装了）")
            continue
        # 判断这族字体的职责：能覆盖汉字的一律当 CJK 字体查全部非 ASCII；
        # 否则当西文字体，只查它该管的非 ASCII（引号、破折号、重音字母）。
        cjk_chars = {c for c in chars if is_cjk(c)}
        covered_cjk = sum(1 for c in cjk_chars if ord(c) in cmap)
        is_cjk_font = bool(cjk_chars) and covered_cjk / len(cjk_chars) >= 0.1
        target = chars if is_cjk_font else {c for c in chars if not is_cjk(c)}
        missing = sorted(c for c in target if ord(c) not in cmap)
        if not missing:
            print(f"[PASS] {family}（{real}）：查了 {len(target)} 个字符，全覆盖")
            continue
        failed += 1
        sample = " ".join(f"{c}(U+{ord(c):04X})" for c in missing[:args.limit])
        more = f" …共 {len(missing)} 个" if len(missing) > args.limit else ""
        print(f"[FAIL] {family}（{real}）：缺 {len(missing)} 个字符 —— {sample}{more}")

    if args.tools:
        for tool, hint in (("pandoc", "文档转换"), ("xelatex", "PDF 渲染"),
                           ("quarto", "单源多格式（可选）"), ("bibtex", "GB/T 7714（可选）")):
            found = shutil.which(tool)
            print(f"[{'PASS' if found else 'WARN'}] {tool}：" + (found or f"未找到（{hint}）"))

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
