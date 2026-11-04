# Academic Typesetting — Claude Code Skill

单一 Markdown 源 → PDF / DOCX / PPTX。管**生产**，不管**内容**。

写论文正文找 `nature-writing`，润色找 `nature-polishing`，数据图找 `nature-figure`，
黑白示意图找 `figkit-bw-figure`；本 skill 只负责把已有内容排成能交付的文件，并且**量给你看**。

## 它和 v1 有什么不同

v1 是一份 286 行的规范，靠模型自觉执行；它自己就写错了三处配置，而且没有任何验证手段。

v2 的判断很简单：**排版的问题只有编译、渲染、测量才能发现**。所以把规范拆成按需加载的五篇，
把"检查表"换成两个脚本，把这次实际踩到的坑（`%` 未转义、`extarticle` 不吃 10.5pt、
matplotlib 数学字体回退、浮动体掉页）固化成可执行的检查。

## 结构

```
academic-typesetting/
├── SKILL.md                     # 路由：什么时候用、六条硬规则、故障速查
├── references/                  # 按需加载，不要全读
│   ├── cjk-typography.md        # 字号、缩进、标点、题注、三线表、参考文献体系
│   ├── nomenclature.md          # 基因/蛋白正斜体、物种名、序列、HGVS、单位
│   ├── latex-pdf.md             # 文档类、几何、浮动体、列宽、原始 LaTeX 块的坑
│   ├── non-latex.md             # DOCX/PPTX：lua 过滤器、参考模板、五条线修正
│   ├── figures.md               # 矢量、按印刷宽度作图、图内字体、matplotlib 陷阱
│   └── qa-gate.md               # 量什么、阈值、失败怎么修
├── scripts/
│   ├── qa_pdf.py                # 交付闸：字体/页填充/越界/位图/编号/元数据
│   └── contact_sheet.py         # 全部页面拼一张联系表，一眼找留白
├── templates/
│   ├── header-cn.tex            # 实测可用的中文前导（含 \tabref/\figref）
│   ├── academic-header.tex      # 西文/英文布局变体
│   ├── nature.csl               # Nature 风；带 zh-CN locale 覆盖块
│   ├── nature_style.docx        # DOCX 参考模板
│   ├── academic_style.pptx      # PPTX 参考模板
│   ├── setup_templates.py       # 重建上面两个模板
│   └── fix_docx_tables.py       # 去掉 Word 里的"五条线"
└── filters/
    └── latex-macros-to-unicode.lua   # \ce{} / \qty{} → Unicode（仅 docx/pptx）
```

## 快速开始

```bash
# 0. 一次性的模板生成（改过 setup_templates.py 里的参数后重跑）
python templates/setup_templates.py

# 1. 编译（项目自带 build 脚本优先）
pandoc src/report.qmd -o output/report.pdf --pdf-engine=xelatex \
  --include-in-header=templates/header-cn.tex \
  --citeproc --bibliography=references.bib --csl=templates/nature.csl \
  --number-sections --resource-path=".;src;assets" \
  -V documentclass=article -V fontsize=11pt -V papersize=a4 \
  -V "geometry:top=2.2cm,bottom=2.2cm,left=2.5cm,right=2.5cm"

# 2. 看一眼全局
python scripts/contact_sheet.py output/report.pdf

# 3. 过闸
python scripts/qa_pdf.py output/report.pdf --lang zh
```

## 引擎选择

| 场景 | 用什么 |
| --- | --- |
| 需要交叉引用 + 多格式，环境允许 spawn | Quarto（`@fig-`/`@tbl-` 原生编号） |
| 沙箱禁止 spawn `cmd.exe`，或只要 PDF | pandoc + xelatex（编号用 `\label`/`\ref`） |
| 纯中文报告/学位论文 | `ctexart`（自带 `\zihao`、断行、中文图表名） |
| 中英混排、期刊风 | `article` + `templates/header-cn.tex` |

## 测量闸抓什么

`qa_pdf.py` 的 18 项里，最能抓到真问题的是这四个：

- **页填充率**：非末页低于 85% 就是浮动体掉页留下的洞。
- **字体回退**：出现 DejaVu / LatinModernMath，说明图里用了 mathtext 或正文里写了 `$>$`。
- **位图**：`page.get_images()` 非空，说明本该矢量的图被导成了 PNG。
- **编号连续**：表 1,2,2,4 这种跳号/重号，几乎都来自手写编号。

## 已知边界

- PPTX 母版未定制，正式交付前需要手动过一遍。
- `qa_pdf.py` 的编号检查用"字号小于正文 / 居中短句"判断题注，极端模板（题注与正文同号同宽）可能漏检。
- 只覆盖 XeLaTeX 链；LuaLaTeX/pdflatex 的中文路径未验证。

## License

MIT。Nature 是 Springer Nature 的注册商标；本项目独立开发，与其无关联。
