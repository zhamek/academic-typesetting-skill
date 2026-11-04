# DOCX / PPTX 路径

要出 Word 或幻灯片时才读。这条路径没有 LaTeX 引擎，三件事会静默失效，全靠随包的资产兜住。

## 1 失灵的两种宏

| 源写法 | PDF | DOCX/PPTX 不加过滤器 |
| --- | --- | --- |
| `$\ce{Mg^2+}$` | Mg²⁺ | 原样印出 `$\ce{Mg^2+}$` |
| `\qty{1.5}{\milli\mole\per\litre}` | 1.5 mmol L⁻¹ | **整段消失，无任何警告** |

`filters/latex-macros-to-unicode.lua` 把两者改写成 Unicode。**只用在 docx/pptx**，PDF 必须保留真宏。

覆盖范围：电荷、上下标、常用单位宏（`\milli\mole\per\litre` → `mmol L⁻¹`、`\degreeCelsius` → `°C`、`\micro\gram` → `µg`）。
不覆盖：带条件的反应式、状态符号、复杂同位素。这类内容在 Word 稿里请直接手写 Unicode。

Quarto 配置：

```yaml
format:
  docx:
    reference-doc: ../templates/nature_style.docx
    filters: [../filters/latex-macros-to-unicode.lua]
  pptx:
    reference-doc: ../templates/academic_style.pptx
    filters: [../filters/latex-macros-to-unicode.lua]
    slide-level: 2
```

## 2 三线表在 Word 里为什么会变成五条线

Quarto 给每个带题注的表套一层 1×1 的布局表，这层包装继承了同一个 `Table` 样式，于是顶线/底线各画两次，页面上出现五条横线。这是结构问题，不是样式没配对。

修法：渲染后跑一次

```bash
python templates/fix_docx_tables.py output/report.docx
```

脚本把"内部还嵌着表"的包装表强制无边框，只留真正的数据表走三线样式。

**顺序不能反：** `quarto render --to docx` → `fix_docx_tables.py`。先修后渲染等于没修。

## 3 参考模板

- `templates/nature_style.docx`：从 `pandoc --print-default-data-file reference.docx` 派生，再叠加 Typography。
  必须从 Pandoc 默认模板派生——**从空白 `Document()` 生成会丢掉 `Table`/`Table Caption`/`Compact`/`Bibliography` 等样式**，Pandoc 写出来时就找不到对应样式，包装表问题随之出现。
- `templates/academic_style.pptx`：16:9（13.333×7.5 in）。母版排版尚未定制，标题与正文继承 python-pptx 默认主题，正式交付前要手动过一遍。
- 改 §3 的任何参数后重跑 `python templates/setup_templates.py`，脚本是唯一真源，不要手改二进制。

## 4 Word 里的中文排版

- 正文字体设两套：西文 Times New Roman、中文宋体，通过 `w:rFonts` 的 `ascii`/`eastAsia` 分开设，只设一个会出现"中文变成 Times 里的宋体替代字"。
- 段落首行缩进用**字符**单位（`w:firstLineChars="200"`），不要用磅值——换字号后磅值会错位。
- 中文字距/行距用 `w:line="360" w:lineRule="auto"`（1.5 倍）而不是固定磅值。
- 导出 PDF 时勾选"嵌入字体"，否则评审机上中文变方框。

## 5 PPTX 的版面下限

| 元素 | 下限 | 说明 |
| --- | --- | --- |
| 正文 | 18pt | 投影后排也看得清 |
| 标题 | 28–36pt | 一页只讲一件事 |
| 每页要点 | ≤ 7 行 | 超过就拆页 |
| 图 | 一页一图，宽 ≥ 60% 版面 | 多面板图另设一页放大 |
| 页码/页脚 | 10pt | 可选 |

Pandoc 的 `slide-level: 2` 表示 `##` 起新页；`#` 是分节页。中文标题不要用自动编号（会变成 "1 引言" 之类），幻灯片通常不要编号。

## 6 交付前自检

```bash
python scripts/qa_pdf.py output/report.pdf --lang zh   # 若同时出了 PDF
python -c "import docx; d=docx.Document('output/report.docx'); print(len(d.tables))"
```

Word 稿至少肉眼过三件事：表是不是三线、题注有没有跟着表走、中文字体有没有掉回 Calibri。
