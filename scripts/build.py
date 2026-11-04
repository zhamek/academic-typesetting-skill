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
import time
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent))
from qa_pdf import body_zone, content_bottom  # noqa: E402

DEFAULTS = {
    "engine": "pandoc",
    "citations": "csl",   # csl（citeproc + nature.csl）| gbt（GB/T 7714）
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


def build_gbt(cfg: dict, base: Path) -> Path:
    """GB/T 7714 路线：pandoc → .tex，再 xelatex → bibtex → xelatex ×2。

    latexmk 本可以串起这几步，但它在本机 Git Bash 下 spawn bibtex 返回 127，
    所以这里显式按顺序调，失败即停。
    """
    skill = Path(__file__).resolve().parent.parent
    out_pdf = base / cfg["output"]
    # .tex 放在项目根目录而不是 output/：前导、wrapper、.bib 都是相对根的路径，
    # 在 output/ 里编译会找不到 \input 和参考文献库。
    # 文件名固定用 ASCII：中文/带空格的 stem 会让本机 MiKTeX 的 bibtex 更容易崩。
    tex = base / "build_report.tex"

    cmd = ["pandoc", cfg["source"], "-o", str(tex), "-s", "--natbib",
           "-V", "biblio-style=gbt7714-numeric",
           "-V", f"documentclass={cfg['class']}",
           "-V", f"fontsize={cfg['fontsize']}",
           "-V", f"papersize={cfg['papersize']}",
           f"--include-in-header={skill / 'templates' / 'gbt-on.tex'}",
           f"--include-in-header={cfg['header']}"]
    if cfg.get("classoption"):
        cmd += ["-V", f"classoption={cfg['classoption']}"]
    if cfg.get("geometry"):
        cmd += ["-V", f"geometry:{cfg['geometry']}"]
    if cfg.get("bibliography"):
        cmd.append(f"--metadata=bibliography={cfg['bibliography']}")
    if cfg.get("number_sections"):
        cmd.append("--number-sections")
    cmd.append("--resource-path=" + ";".join(
        cfg["resource_path"] if isinstance(cfg["resource_path"], list) else [cfg["resource_path"]]))

    print("$ " + " ".join(cmd))
    res = subprocess.run(cmd, cwd=str(base), capture_output=True, text=True,
                         encoding="utf-8", errors="replace")
    if res.returncode != 0:
        print("pandoc 失败：\n" + (res.stderr or "")[-1500:])
        raise SystemExit(res.returncode)

    for step in (["xelatex", "-interaction=nonstopmode", tex.name],
                 ["bibtex", tex.stem],
                 ["xelatex", "-interaction=nonstopmode", tex.name],
                 ["xelatex", "-interaction=nonstopmode", tex.name]):
        print("$ " + " ".join(step))
        r = subprocess.run(step, cwd=str(base), capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
        # 只对 xelatex 严格：本机 MiKTeX 的 bibtex 会在退出时崩溃（139），
        # 但 .bbl 是完整的，所以以产物为准而不是返回码。
        if step[0] == "xelatex" and r.returncode != 0:
            print((r.stdout or "")[-1500:])
            raise SystemExit(r.returncode)
        if step[0] == "bibtex":
            bbl = base / (tex.stem + ".bbl")
            last = r
            for attempt in range(30):
                if bbl.exists() and bbl.stat().st_size > 0:
                    break
                # 本机 MiKTeX 的 bibtex 约七成概率在退出时崩溃（0xC0000374），失败时 .bbl 为 0 字节。
                time.sleep(0.4)
                last = subprocess.run(step, cwd=str(base), capture_output=True,
                                      text=True, encoding="utf-8", errors="replace")
            if not bbl.exists() or bbl.stat().st_size == 0:
                print("bibtex 连试 30 次都没有产出 .bbl：")
                print((last.stdout or "") + (last.stderr or ""))
                raise SystemExit(1)

    produced = base / (tex.stem + ".pdf")
    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    if produced != out_pdf:
        produced.replace(out_pdf)
    # 中间文件只留 .tex 便于排查，其余清掉
    for ext in (".aux", ".log", ".bbl", ".blg", ".out", ".toc"):
        (base / (tex.stem + ext)).unlink(missing_ok=True)
    return out_pdf


def report_pages(pdf: Path) -> None:
    import fitz

    doc = fitz.open(pdf)
    top = body_zone(doc[0].rect.height)[0]
    h = doc[0].rect.height
    bottoms = {p: content_bottom(doc, p) for p in range(1, doc.page_count + 1)}
    # 单页文档没有"正文页"可比，参考取全页最大；仍太小时直接不评估
    ref = [b for p, b in bottoms.items() if p != doc.page_count] or list(bottoms.values())
    full = max(ref, default=top)
    if full - top < 50:
        print("\n单页或极短文档：不评估页填充率")
        return
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
    ap.add_argument("--preflight", action="store_true", help="构建前查字体缺字与工具")
    args = ap.parse_args()

    cfg_path = Path(args.config)
    if not cfg_path.exists():
        print(f"找不到配置 {cfg_path}（示例：templates/typeset.example.yaml）")
        return 1
    cfg = load_config(cfg_path)

    if args.preflight:
        pre = Path(__file__).parent / "preflight.py"
        r = subprocess.run([sys.executable, str(pre), cfg["source"],
                            "--fonts", cfg.get("fonts", "SimSun,SimHei,Times New Roman")],
                           cwd=str(cfg_path.parent))
        if r.returncode != 0:
            print("预检失败，先修字体再编译（加 --qa 可跳过后续闸门）")
            return r.returncode

    if cfg.get("citations") == "gbt":
        out = build_gbt(cfg, cfg_path.parent)
    else:
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
