---
name: academic-typesetting
description: 学术文档的排版与交付引擎——单一 Markdown 源出 PDF/DOCX/PPTX，管字体字号、三线表、图表题注、浮动体位置、CJK 断行与参考文献样式，并用脚本量测交付质量。触发：排版/论文/报告/幻灯片/三线表/PDF/DOCX/PPTX/学位论文/课程报告/中文排版/quarto。
---

# 学术排版引擎

管"把内容生产成能交付的文件"，不管"内容从哪来"。

## 0 分工——先确认该不该我出场

| 请求 | 归属 |
| --- | --- |
| 写/改正文、摘要、引言、投稿信、开题 | nature-writing |
| 英文润色、句式、投稿前自审 | nature-polishing |
| 数据图怎么画（柱状/热图/森林图/面板） | nature-figure |
| 黑白矢量示意图、位点图 | figkit-bw-figure |
| **已有内容排成可交付的 PDF/DOCX/PPTX** | **本 skill** |

同时被触发时不重复劳动：让 nature-* 出文字，本 skill 只负责落地成文件。

## 1 六条硬规则

1. **先量，后改。** 任何版面判断都要经过 `编译 → 渲染成图 → 量 → 动手`。只看 `.tex` 猜版面必错。
2. **字体字号显式声明。** 正文 Times New Roman + 宋体，标题黑体，等宽 Consolas。不依赖任何默认。
3. **编号交给环境。** LaTeX 里用 `\label`/`\ref`，Quarto 里用 `@fig-`/`@tbl-`；手写"表1"在插入新表后必错。
4. **中文正文：首行缩进 2 字符、段间距 0、行距 1.4–1.5×字高。** 西文网页式 `parskip` 不要套到中文报告上。
5. **浮动体位置是试出来的，不是设出来的。** 每页版心要接近占满足（≥ 85%），大片留白算缺陷。
6. **交付前必须过闸：** `python scripts/qa_pdf.py <pdf> --lang zh --fonts SimSun,SimHei,TimesNewRoman`，有 FAIL 不许交。

## 2 引擎与文档类选择

| 场景 | 用什么 | 理由 |
| --- | --- | --- |
| 沙箱允许 spawn、需要交叉引用 + 多格式 | **Quarto** | `@fig-`/`@tbl-` 原生编号；一份源出 pdf/docx/pptx |
| 沙箱禁止 spawn `cmd.exe`、只要 PDF | **pandoc + xelatex** | 已实测可用；编号改 `\label`/`\ref`，其余能力等价 |
| 纯中文课程报告 / 学位论文 | **ctexart / ctexbook** | 自带 `\zihao` 字号、CJK 断行、中文图表名，省掉手工 xeCJK |
| 中英混排、期刊风格 | `article` / `extarticle` + 自带 `templates/header-cn.tex` | 控制力最强 |

**字号陷阱（实测）：** `extarticle` 只认 8/9/10/11/12/14/17/20pt。写 `fontsize: 10.5pt` 会被静默忽略并退回 10pt——日志里只有一行 `Unused global option(s)`。要精确五号（10.5pt）用 ctex 的 `\zihao{5}`；否则用 article 11pt（≈ 小四偏小）并接受它不是五号。

## 3 工作循环

下文用 `$S` 指代本 skill 目录（`~/.claude/skills/academic-typesetting`），因为脚本不在项目里。

```bash
# ① 编译：项目自带的 build 脚本优先；没有就直接调 pandoc / quarto
quarto render src/report.qmd --to pdf        # 或 README 里的 pandoc 命令

# ② 联系表：全部页面拼一张，一眼看留白、掉页、浮动体漂移
python "$S/scripts/contact_sheet.py" output/report.pdf

# ③ 量测：字体嵌入 / 页填充率 / 越界 / 位图 / 编号连续 / 元数据
python "$S/scripts/qa_pdf.py" output/report.pdf --lang zh

# ④ 对着 FAIL/WARN 改，回到 ①
```

量什么、阈值多少、每种失败怎么修，见 `references/qa-gate.md`。

## 4 参考文件——按需加载，不要全读

| 文件 | 什么时候读 |
| --- | --- |
| `references/cjk-typography.md` | 定字号、缩进、标点、图表题注、三线表线宽、参考文献体系 |
| `references/latex-pdf.md` | PDF 路径：文档类、几何、浮动体、表格列宽、原始 LaTeX 块的坑 |
| `references/non-latex.md` | 出 DOCX/PPTX：lua 过滤器、参考模板、三线表修正 |
| `references/figures.md` | 插图：矢量、按印刷宽度作图、图内字体、matplotlib 陷阱 |
| `references/qa-gate.md` | 每次交付前；以及版面出问题时的诊断顺序 |

同时在 `templates/`：`header-cn.tex`（实测可用的中文前导）、`nature.csl`、DOCX/PPTX 参考模板、`setup_templates.py`、`fix_docx_tables.py`；在 `filters/`：`latex-macros-to-unicode.lua`。

## 5 常见故障速查

| 症状 | 真正的原因 | 修法 |
| --- | --- | --- |
| 编译报 `Extra alignment tab` / `Misplaced \noalign` | 表格某行里有没转义的 `%`，把后半行注释掉了 | 表格内写 `\%`；`>` 直接写，别包 `$>$`（会引进数学字体） |
| 原始 LaTeX 块里出现字面星号 | markdown 斜体在 raw block 里不生效 | 用 `\textit{}` |
| 某页下方空一大块 | 一个 `[H]` 表格/图放不下，被推到下一页 | 表格改 `[!t]` 让正文填满本页；或把它前面那段导语挪到表后，让表提前几行落位 |
| 浮动体落在离引用两页远的地方 | 队列里有更大的浮动体堵着 | 先放小表后放大表；或给大表 `[!t]` 单独占页顶 |
| 图比版心宽 2–3pt，日志报 Overfull | `bbox_inches='tight'` 默认带 pad，图比画布宽一点 | `\includegraphics[width=\linewidth]` 强制贴合 |
| 图里出现无衬线数字/符号 | matplotlib 的 mathtext 回退到 DejaVu | 图内别写 `$...$`（写"二氧化碳"、`g / L`）；或设 `mathtext.fontset=custom` |
| 参考文献页码变成 `123～130 (2024 年)` | citeproc 走了中文 locale | 用 `templates/nature.csl`，它带 `<locale zh-CN>` 覆盖块，别拿官方文件覆盖 |
| 中文里"表 1"和"1"之间空格时有时无 | 编号与题名之间是 `\labelsep`，不是手打的空格 | `\captionsetup{labelsep=quad}` |

## 6 交付版面基线（中文课程报告 / 综述）

- A4，页边距 2.2–2.5 cm，正文 11pt 宋体/Times，行距 1.17（≈1.4×字高）
- 标题黑体：一级 14pt、二级 12pt、三级 11pt，段前 15/12/10pt、段后 7/5/4pt
- 表：`\footnotesize` + `\arraystretch` 1.0–1.15 + 定宽 `p{}` 右不齐；三线 1.5/0.75/1.5pt
- 图：矢量 PDF，宽度 = 版心宽，图题在下；图内字号 = 印刷字号（按宽度作图，不缩放）
- 参考文献：正文上标编号，列表 `\small`/`\footnotesize` 悬挂缩进
- 页眉左标题右作者学号，首页不显示页眉；页脚居中页码

数字与单位之间留 1/4 空（`135 g/L`、`531 kb`），不要写成 `135g/L`。
