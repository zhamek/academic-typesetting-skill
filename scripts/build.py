# -*- coding: utf-8 -*-
"""配置驱动的构建：一条命令把源文件变成 PDF/DOCX，并打印每页填充情况。

之前每个项目都要现写一个 build.py——同样的 pandoc 参数抄一遍、页码量一遍。
这里把参数收进 typeset.yaml，脚本只做三件事：拼命令、跑、量。

用法：
    python build.py                      # 读当前目录 typeset.yaml
    python build.py --config proj/typeset.yaml --qa

typeset.yaml 示例见 templates/typeset.example.yaml。
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent))
from qa_pdf import body_zone, content_bottom  # noqa: E402

DEFAULTS = {
    "engine": "pandoc",
    "class": "article",
    "fontsize": "11pt",
    "papersize": "a4",
    "geometry": "top=2.2cm,bottom=2.2cm,left=2.5cm,right=2.5cm",
    "number_sections": True,
    "resource_path": ["."],
    "filters": [],
    "extra_args": [],
}


def load_config(path: Path) -> dict:
    cfg = dict(DEFAULTS)
    cfg.update(yaml.safe_load(path.read_text(encoding="utf-8")) or {})
    for key in ("source", "output"):
        if not cfg.get(key):
            raise SystemExit(f"typeset.yaml 缺少 {key}")
    return cfg


def pandoc_cmd(cfg: dict, base: Path) -> list[str]:
    out = Path(cfg["output"])
    cmd = ["pandoc", str(Path(cfg["source"])), "-o", str(out)]
    if out.suffix.lower() == ".pdf":
        cmd += ["--pdf-engine=xelatex"]
        if cfg.get("header"):
            cmd.append(f"--include-in-header={cfg['header']}")
        cmd += ["-V", f"documentclass={cfg['class']}"]
        if cfg.get("classoption"):
            cmd += ["-V", f"classoption={cfg['classoption']}"]
        cmd += ["-V", f"fontsize={cfg['fontsize']}",
                "-V", f"papersize={cfg['papersize']}"]
        if cfg.get("geometry"):
            cmd += ["-V", f"geometry:{cfg['geometry']}"]
    if cfg.get("bibliography"):
        cmd += ["--citeproc", f"--bibliography={cfg['bibliography']}"]
        if cfg.get("csl"):
            cmd.append(f"--csl={cfg['csl']}")
    if cfg.get("number_sections"):
        cmd.append("--number-sections")
    rp = cfg["resource_path"]
    cmd.append("--resource-path=" + ";".join(rp if isinstance(rp, list) else [rp]))
    for f in cfg.get("filters") or []:
        cmd.append(f"--filter={f}")
    cmd += cfg.get("extra_args") or []
    return cmd


def report_pages(pdf: Path) -> None:
    import fitz

    doc = fitz.open(pdf)
    top = body_zone(doc[0].rect.height)[0]
    h = doc[0].rect.height
    bottoms = {p: content_bottom(doc, p) for p in range(1, doc.page_count + 1)}
    full = max((b for p, b in bottoms.items() if p != doc.page_count), default=top)
    print(f"\n{doc.page_count} 页 · 版心底线 {full:.0f}pt")
    gaps = []
    for p, b in bottoms.items():
        ratio = (b - top) / max(full - top, 1)
        flag = "" if p == doc.page_count or ratio >= 0.85 else "  ← 偏空"
        print(f"  p{p:>2}  {ratio:5.0%}{flag}")
        if flag:
            gaps.append(p)
    if gaps:
        print(f"提示：{gaps} 页有留白，看 contact_sheet.py 判断是浮动体掉页还是末页正常结束")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="typeset.yaml")
    ap.add_argument("--qa", action="store_true", help="构建后直接跑交付闸")
    args = ap.parse_args()

    cfg_path = Path(args.config)
    if not cfg_path.exists():
        print(f"找不到配置 {cfg_path}（示例：templates/typeset.example.yaml）")
        return 1
    cfg = load_config(cfg_path)

    cmd = ["quarto", "render", str(cfg["source"]), "--to",
           "pdf" if str(cfg["output"]).lower().endswith(".pdf") else "docx"] \
        if cfg["engine"] == "quarto" else pandoc_cmd(cfg, cfg_path.parent)

    print("$ " + " ".join(cmd))
    res = subprocess.run(cmd, cwd=str(cfg_path.parent), capture_output=True,
                         text=True, encoding="utf-8", errors="replace")
    if res.returncode != 0:
        tail = (res.stderr or res.stdout or "")[-2000:]
        print("构建失败：\n" + tail)
        return res.returncode

    out = cfg_path.parent / cfg["output"]
    if out.suffix.lower() == ".pdf":
        report_pages(out)
    print(f"\n输出 → {out}")

    if args.qa:
        qa = Path(__file__).parent / ("qa_pdf.py" if out.suffix.lower() == ".pdf" else "qa_docx.py")
        cmd = [sys.executable, str(qa), str(out), "--lang", cfg.get("lang", "zh")]
        if cfg.get("fonts") and out.suffix.lower() == ".pdf":
            cmd += ["--fonts", cfg["fonts"]]
        return subprocess.run(cmd).returncode
    return 0


if __name__ == "__main__":
    sys.exit(main())
