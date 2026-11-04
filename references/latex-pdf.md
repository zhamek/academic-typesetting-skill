# PDF 路径（XeLaTeX / Pandoc / Quarto）

出 PDF 时才读。这里只写实测有效的东西，所有结论都在本机 MiKTeX 25.12 + Pandoc 3.9 上跑过。

## 1 文档类与字号

```latex
\documentclass[11pt,a4paper]{ctexart}      % 纯中文首选：自带断行、字号、图表名
\documentclass[11pt,a4paper]{article}      % 中英混排，配 templates/header-cn.tex
```

- `extarticle` 只认 8/9/10/11/12/14/17/20；**10.5pt 会被静默忽略**（日志仅一行 `Unused global option`）。
- ctexart 下直接用 `\zihao{5}`（五号）/`\zihao{-4}`（小四）/`\zihao{4}`（四号），精确不需要换算。
- 用 article + 手工 xeCJK 时，`\fontsize{10.5pt}{15.5pt}\selectfont` 也可硬设，但标题层级不会跟着缩放，不如 ctex 干净。

## 2 几何

```latex
\usepackage[margin=2.5cm]{geometry}      % 或 top=2.2cm,bottom=2.2cm,left=2.5cm,right=2.5cm
```

- 版心宽 = 纸宽 − 左右边距。A4 + 2.5cm → **16.0 cm**；这是所有表格列宽和插图宽度的预算上限。
- 页眉会占用顶部空间：`\headheight` 小于 15pt 时 fancyhdr 报警并撑开版面，设 `\setlength{\headheight}{15pt}`。
- Pandoc 的 `-V geometry:"..."` 与 `\usepackage{geometry}` 二选一，重复加载会 option clash。

## 3 表格

### 3.1 列宽算术（最容易错的地方）

`\tabcolsep` 默认 6pt，n 列之间有 (n−1) 个 2×`\tabcolsep` 的间隙。4 列、`@{}` 收边时：

```
可用内容宽 = 16.0cm − 3 × 12pt ≈ 16.0 − 1.27 = 14.73cm
```

设 `\setlength{\tabcolsep}{4.5pt}` 则间隙降到 3×9pt = 0.95cm，可用 15.05cm。
七列以上建议把 `\tabcolsep` 压到 3pt 并考虑横排（`sidewaystable`）。

宽度用固定 `p{}` 而不是等分 `X`：

```latex
\small
\setlength{\tabcolsep}{4.5pt}
\begin{tabular}{@{}>{\raggedright\arraybackslash}p{2.2cm}
                     >{\raggedright\arraybackslash}p{4.45cm}
                     >{\raggedright\arraybackslash}p{4.45cm}
                     >{\raggedright\arraybackslash}p{3.95cm}@{}}
```

- 右不齐：中文短句在窄列里两端对齐会拉出大片空隙。
- `\arraystretch` 1.0–1.15；超过 1.3 表会虚胖，还挤占版面。
- 表内字号 `\small`（9pt）或 `\footnotesize`（8pt）；正文 11pt 时优先 `\small`。

### 3.2 原始 LaTeX 块的四条禁令

在 `.qmd` / `.md` 的 ` ```{=latex} ` 块里，markdown 规则全部失效：

| 写法 | 后果 | 正确写法 |
| --- | --- | --- |
| `90% DCW` | `%` 注释掉后半行，报 `Extra alignment tab` | `90\% DCW` |
| `*PEX10*` | 星号原样印出来 | `\textit{PEX10}` |
| `$>$` | 引入 Latin Modern 数学字体，正文里混进一种字体 | 直接写 `>` |
| `表~1` 里的 `~` | 正常（不换行空格），但在某些模板里会变成别的 | 确认模板未重定义 `~` |

### 3.3 表格 vs 长表

- 8 行以内用 `table` 浮动 + `tabular`，不要 `longtable`（会跨页断行、还重复表头）。
- 确实要跨页才用 `longtable`，并配 `\endfirsthead`/`\endhead`。

## 4 浮动体：位置是试出来的

LaTeX 的 `[htbp]` 是"建议"，不是承诺。实测出三条可用策略：

| 策略 | 什么时候 | 代价 |
| --- | --- | --- |
| `[H]`（float 宏包） | 表小、紧跟其讨论段落 | 放不下就整块搬到下一页，本页底部留大洞 |
| `[!t]` | 表/图较大 | 页顶落位，本页正文填满；但可能把某段从中间截断 |
| `[!tb]` + 调 `\textfloatsep` | 图 | 同上 |

**让 `[H]` 落位的技巧（实测有效）：** 如果表差几行放不下，把表**前面那段导语挪到表后面**——表提前 3 行就能落位，导语顺理成章变成"表 1 汇总了……"，读起来反而更顺。

浮动页松散的根因是胶水可伸缩，收紧它：

```latex
\makeatletter
\setlength{\@fptop}{0pt}            % 顶部不伸缩
\setlength{\@fpsep}{12pt}           % 浮动体之间固定 12pt
\setlength{\@fpbot}{0pt plus 1fil}  % 余量全部堆到底部
\makeatother
\renewcommand{\topfraction}{0.9}
\renewcommand{\textfraction}{0.08}
```

## 5 交叉引用

- 表/图环境里写 `\label{tab:microbe}`，正文引用；**不要手写数字**。
- **pandoc 的坑：** markdown 正文里的 `~` 会被写成 `\textasciitilde{}`，于是 `表~\ref{x}` 印出来是"表 ~1"。
  用 `header-cn.tex` 里的 `\tabref{x}` / `\figref{x}`（宏内自带 `表~`/"图~"），pandoc 会把它们当 raw inline 原样传下去。
- 在 Pandoc markdown 正文里 `\ref{...}` 会被当作 raw inline 原样进 LaTeX——PDF 可用，但 DOCX 会丢。要同源出 DOCX 就改用 Quarto 的 `@tbl-` 语法。
- 章节号由 `--number-sections` 给；参考文献标题用 `.unnumbered`。

## 6 插图

```latex
\begin{figure}[!tb]
\centering
\includegraphics[width=\linewidth]{assets/fig1.pdf}
\caption{……}
\end{figure}
```

- **一定写 `width=`**：matplotlib 的 `bbox_inches='tight'` 自带 0.02in pad，图会比画布宽 2–3pt，不缩放就 Overfull。
- `[width=\linewidth]` 与"按印刷宽度作图"配合，图内字号才会等于纸上字号。

## 7 参考文献

citeproc 输出 `CSLReferences` 列表：

```latex
\begin{CSLReferences}{1}{0}   % #1 悬挂缩进, #2 条目间距
```

- 条目间距为 0，靠 `\baselineskip`；想更紧只能改字号（`\footnotesize`）而不是加 `\vspace`。
- 参考文献常把最后一页撑成"只有 3 条"：先减字号，再考虑 `\clearpage` 另起页——**不要**为了凑页在正文里注水。
- 中文文献列表要 GB/T 7714 时换 CSL，不要手改条目。

## 8 双栏排版

课程报告与学位论文默认单栏；超过 10 页、或想接近期刊版式时才会考虑双栏。

- 中文双栏的硬约束是**每行字数**：A4 + 2cm 边距、栏间距 6mm 时单栏宽约 8.1cm，
  11pt 只有 21 字/行，偏短。双栏就要降到 9.5–10pt，或把边距压到 1.8cm。
- 实现：`\documentclass[twocolumn]` 或 `multicols`；跨栏表/图用 `table*` / `figure*`，
  它们只能落在页顶，不能 `[H]`。
- 版心预算按**单栏宽**算，不是按整页宽——列宽算术里那个 16cm 换成 8.1cm。
- 双栏下段落更容易出现"稀疏行"：西文长词加 `\-`，中文保持两端对齐。
- `qa_pdf.py` 的页填充测量按内容 bbox 裁进正文区，双栏文档同样适用（实测）。

## 9 编译诊断：日志里只看三类信号

```bash
grep -E "Overfull|Underfull|Float too large|undefined" build.log | sort | uniq -c
```

| 信号 | 含义 | 处理 |
| --- | --- | --- |
| `Overfull \hbox (x pt too wide)` | 内容超出版心 | 表格列宽加总错、图没写 width、长 URL/英文术语断不开 |
| `Float too large for page by Xpt` | 图+题注高于版心 | 缩小图或缩短题注；改 `[H]` 为 `[!t]` |
| `Reference ... undefined` | 少跑一遍 | 连编两次 |

编译两次是常态（引用、页码都要第二轮才稳定）。
