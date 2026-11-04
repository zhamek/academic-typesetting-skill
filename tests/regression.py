# -*- coding: utf-8 -*-
"""闸门回归：拿已知结论的文档验证 qa_pdf.py 没有退化。

不内置 PDF（成品里常带姓名学号，不进仓库）。把当时那几份文件指给我：

    python tests/regression.py --good  path/to/交付件.pdf \
                              --v1     path/to/旧版8页.pdf \
                              --ref    path/to/双栏参考件.pdf

每个 case 声明了"应该报什么"，跑完逐条断言。缺哪个就跳过哪个。

为什么值得留这三个 case：
  good —— 闸门全绿，防止改检查时把正常文档判成错的
  v1   —— 正文里写了 $CO_2$，应报数学字体回退（LatinModernMath）
  ref  —— 双栏综述，表 1/表 2 只在题注出现、正文没引用，应报出来
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

QA = Path(__file__).resolve().parent.parent / "scripts" / "qa_pdf.py"

CASES = {
    "good": dict(expect_fail=0, expect_warn=0,
                 note="已交付件：应全绿"),
    "v1": dict(expect_fail=0, expect_warn_min=1, expect_warn_has="数学回退",
               note="旧版 8 页：正文 $CO_2$ 会引入 LatinModernMath"),
    "ref": dict(expect_fail=0, expect_warn_min=1, expect_warn_has="只出现在题注",
                note="双栏参考件：表 1/表 2 未在正文引用"),
}


def run(pdf: Path, fonts: str | None) -> tuple[int, str]:
    cmd = [sys.executable, str(QA), str(pdf), "--lang", "zh"]
    if fonts:
        cmd += ["--fonts", fonts]
    res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return res.returncode, res.stdout


def check(name: str, pdf: Path, fonts: str | None) -> bool:
    spec = CASES[name]
    code, out = run(pdf, fonts)
    fails = len(re.findall(r"^\[FAIL\]", out, flags=re.M))
    warns = len(re.findall(r"^\[WARN\]", out, flags=re.M))

    ok = code == 0 if spec["expect_fail"] == 0 else code != 0
    ok &= fails == spec["expect_fail"]
    if "expect_warn" in spec:
        ok &= warns == spec["expect_warn"]
    if "expect_warn_min" in spec:
        ok &= warns >= spec["expect_warn_min"]
    if "expect_warn_has" in spec:
        ok &= spec["expect_warn_has"] in out

    print(f"[{'PASS' if ok else 'FAIL'}] {name:<5} FAIL={fails} WARN={warns}  ({spec['note']})")
    if not ok:
        print(out.rstrip())
    return ok


def main() -> int:
    ap = argparse.ArgumentParser()
    for name in CASES:
        ap.add_argument(f"--{name}", default=None)
    ap.add_argument("--fonts-good", default=None, help="good 件的字体族，默认用脚本默认值")
    args = ap.parse_args()

    ran = 0
    ok = True
    for name in CASES:
        p = getattr(args, name)
        if not p:
            print(f"[SKIP] {name}: 未提供文件")
            continue
        ran += 1
        ok &= check(name, Path(p), args.fonts_good if name == "good" else None)

    print(f"\n{ran}/{len(CASES)} 个 case 已跑")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
