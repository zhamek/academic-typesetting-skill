---
name: academic-typesetting
description: Integrated academic typography engine utilizing Quarto for single-source publishing (PDF, DOCX, PPTX). Enforces Nature-grade layout geometry, strict font discipline, bioinformatics nomenclature, vector graphics scaling, and Zotero CSL automated citation. Triggers on 排版/论文/报告/幻灯片/基因编辑/生信/PDF/DOCX/PPTX/quarto/三线表.
---

# Integrated Academic Typesetting Skill

## Part 0: Shared Academic Typography Meta-Specifications

### 0.1 Cross-Platform Bilingual Font Stack

| Role | PDF / DOCX (Print) | PPTX (Projection) |
| --- | --- | --- |
| **Body Latin** | Times New Roman (**Serif**) | Arial / Helvetica (**Sans-serif**) |
| **Body CJK** | SimSun / 宋体 (**Serif**) | SimHei / 黑体 (**Sans-serif**) |
| **Heading Latin** | Times New Roman Bold (**Serif**) | Arial Bold (**Sans-serif**) |
| **Heading CJK** | STZhongsong / 黑体 (**Serif/Sans**) | SimHei / 黑体 (**Sans-serif**) |
| **Monospace (Code/Seq)** | Consolas / Courier New | Consolas |

### 0.2 Bioinformatics & Gene-Editing Nomenclature Constraints

- **Gene Locus & Symbols:** Forced italic via Markdown `*...*`. Examples: *Cas9*, *PIK3CA*, *AAV9*, *pegRNA*.
- **Protein Symbols:** MUST be upright (roman). Examples: Cas9, PIK3CA, Reverse Transcriptase.
- **Nucleotide/Amino Acid Sequences:** MUST use inline code backticks (`) or code blocks. **When single-line sequence length > 10 bases, insert a thin space (Unicode `U+2009`) every 10 bases**, and enforce no-wrap on the line.
- **Mutation Annotation (HGVS Standard):** Strict HGVS nomenclature. Protein variants in upright three-letter/single-letter codes (e.g., `p.Gly12Val`). cDNA variants in upright (e.g., `c.35G>A`).

### 0.3 High-Resolution Vector Graphics Control

- **Format Priority:** Imported figures must prioritize vector formats: PDF for PDF backend, SVG for Word/PPTX backend. If raster images (EM, gel images) are used, resolution must be ≥ **300 DPI**.
- **Geometric Dimensioning:**
  - **Single-column Width:** Strictly anchored at `89mm`.
  - **Double-column Width:** Strictly anchored at `183mm`.
- **Figure Internal Font Sync:** When exporting figures from R (ggplot2) or Python (Seaborn), internal text fonts must be hardcoded as `Arial` or `Helvetica`. Default non-embedded raster fonts are prohibited.

### 0.4 Bibliography Automation

- **Data Source Binding:** Workspace root MUST mount a `references.bib` file.
- **Style Lock:** Use `nature.csl` style file, enforcing sequential superscript citation numbering (e.g., `[1]`).
- **Chinese-document locale handling — already built into the shipped `nature.csl`:** with `lang: zh-CN` set, citeproc otherwise formats the bibliography using Chinese locale conventions, producing page ranges like `123～130` and years like `2024 年` — wrong for a Nature-style reference list. The shipped `nature.csl` therefore carries an `<locale xml:lang="zh-CN">` block that forces the English year form and an en-dash page delimiter, so a Chinese manuscript gets Chinese cross-reference prefixes ("表1") *and* an English-format reference list. **Do not remove that block, and never overwrite the file with a pristine download of `nature.csl`** — doing so silently restores `123～130 (2024 年)`.

---

## Part 1: Quarto Compilation Engine Profiles

### 1.1 Environment Pre-flight Check

Before any compilation, verify the Quarto binary and the local LaTeX compiler are both reachable:

```bash
quarto --version    # this machine: C:\Program Files\Quarto\bin\quarto.exe
xelatex --version   # this machine: MiKTeX, C:\Users\35606\AppData\Local\Programs\MiKTeX\miktex\bin\x64\
```

If `quarto` is not found, fall back to the Pandoc commands in §1.4 — but the fallback path is materially weaker (no native cross-reference resolution), so prefer installing Quarto over relying on it.

If `xelatex` is not found, Quarto cannot convert AST to PDF. In that case, trigger degradation: prompt the user to export DOCX first, then save as PDF from Word.

### 1.2 Unified Single-Source Configuration (`src/report.qmd` YAML Frontmatter)

```yaml
---
title: "High-Throughput Screen of Split-Prime Editing Systems"
author: "Academic Researcher"
date: 2026-06-04
lang: zh-CN
bibliography: ../references.bib
csl: ../templates/nature.csl

format:
  pdf:
    pdf-engine: xelatex
    documentclass: extarticle
    fontsize: 10.5pt
    linestretch: 1.35
    geometry: "top=2.2cm, bottom=2.2cm, left=2.2cm, right=2.2cm"
    mainfont: "Times New Roman"
    sansfont: "Arial"
    monofont: "Consolas"
    include-in-header:
      - text: |
          \usepackage{mhchem}
          \usepackage{siunitx}
          \usepackage{booktabs}
          % parskip 已由 Quarto 的 LaTeX 模板加载；此处不可再 \usepackage[options]{parskip}，
          % 否则报 "Option clash for package parskip" 并中断编译。改直接设长度。
          \setlength{\parskip}{8pt}
          \setlength{\parindent}{0pt}
          \widowpenalty=10000
          \clubpenalty=10000
          
  docx:
    reference-doc: ../templates/nature_style.docx
    # REQUIRED: DOCX/PPTX have no LaTeX engine. Without this filter
    # \qty{}{} is dropped silently and \ce{} prints as literal text.
    filters:
      - ../filters/latex-macros-to-unicode.lua
    toc: false
    number-sections: true

  pptx:
    reference-doc: ../templates/academic_style.pptx
    filters:
      - ../filters/latex-macros-to-unicode.lua
    slide-level: 2
---
```

### 1.3 VS Code Local Automation Task Pipeline (`.vscode/tasks.json`)

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Quarto Compile All Formats",
      "type": "shell",
      "command": "quarto render ${file} --output-dir ../output",
      "group": {
        "kind": "build",
        "isDefault": true
      },
      "options": {
        "cwd": "${workspaceFolder}/src"
      },
      "problemMatcher": []
    }
  ]
}
```

### 1.4 Pandoc Fallback Commands (Quarto unavailable)

```bash
# PDF
# --include-in-header 是必需的：缺了它 \ce{} (mhchem) 和 \qty{}{} (siunitx) 会编译失败。
# --citeproc 三件套同理，缺了它引文不渲染，上标编号消失。
pandoc report.md -o output/report.pdf --pdf-engine=xelatex \
  --include-in-header=templates/academic-header.tex \
  --citeproc --bibliography=references.bib --csl=templates/nature.csl \
  -V mainfont="Times New Roman" -V CJKmainfont="Noto Serif SC" \
  -V documentclass=extarticle -V fontsize=10.5pt \
  -V geometry:"top=2.2cm, bottom=2.2cm, left=2.2cm, right=2.2cm"

# DOCX
pandoc report.md -o output/report.docx --reference-doc=templates/nature_style.docx \
  --citeproc --bibliography=references.bib --csl=templates/nature.csl

# PPTX
pandoc report.md -o output/report.pptx --reference-doc=templates/academic_style.pptx
```

---

## Part 2: Semantic Markdown Academic Writing Syntax

### 2.1 Canonical Text Example

```markdown
## Introduction

The optimization of *Prime Editing* vectors requires precise spatial control of the split-*SpCas9* architecture [@an理论2024]. As illustrated in @fig-pipeline, the concentration of $\ce{Mg^2+}$ ions was strictly maintained at \qty{1.5}{\milli\mole\per\litre} within the reaction buffer.

The synthetic pegRNA extension sequence was verified as:
`5'-ATGCGA TGCCGA TGCATC GATCGAT-3'`

## Results

Statistical significance was observed between the two groups (@tbl-metrics), with a final clearing rate calculated via $1000 \times g$ centrifugation.

![Architecture of Split-Prime Editing Pipeline](../assets/pipeline.svg){#fig-pipeline width=183mm}

| System Variant | Editing Efficiency (%) | Off-target Indels (%) |
|:---|:---|:---|
| PE3 (Standard) | $23.4 \pm 1.2$ | $0.45 \pm 0.02$ |
| Split-PE (Engineered) | $45.8 \pm 2.1$ | $< 0.01$ |

: Specific editing metrics and fidelity assessments {#tbl-metrics}
```

### 2.2 Key Syntax Rules

- **Chemical formulas**: Always `$\ce{...}$` wrapped in math inline delimiters.
- **Physical quantities**: Always `\qty{number}{unit}`. Number and unit separated by non-breaking space (handled by siunitx). Prefixes are lowercase: `\milli`, `\micro`, `\nano`.
- **Unit macro facts — verified against siunitx v3.5.5, do not guess:** there is **no `\molar` macro** (and none in v2 capitalised form either — `\Molar` is equally undefined). Molarity must be spelled `\mole\per\litre`, so 1.5 mM is `\qty{1.5}{\milli\mole\per\litre}`. Confirmed working macros: `\mole`, `\litre`, `\gram`, `\meter`, `\second`, `\minute`, `\degreeCelsius`, `\per`. A literal unit string also works and is the safest fallback: `\qty{1.5}{mmol/L}`. An undefined unit macro aborts the entire compilation, not just the one line.
- **Gene symbols**: `*GENE_NAME*` (italic).
- **Protein symbols**: Plain text `PROTEIN_NAME` (upright).
- **Sequences**: Backtick-wrapped with thin-space grouping every 10 bases.
- **Ranges**: Use en-dash `--` (e.g., pH 5.5--6.5), NEVER bare `~`.
- **Tables**: Pipe table format, caption BELOW table with `: Caption {#tbl-id}`.
- **Cross-references**: Write the bare `@tbl-id` / `@fig-id`. Quarto and Pandoc both supply the `表`/`Table` prefix themselves — writing `表 @tbl-id` produces the doubled "表 表 1".
- **Figures**: Caption ABOVE or BELOW image, vector format preferred, width anchored.

---

## Part 3: Reference Template Architecture & Initialization Script

### 3.0 Non-LaTeX Format Pipeline (DOCX / PPTX)

DOCX and PPTX have **no LaTeX engine**, which breaks three things that work fine in PDF. All three are handled by the shipped assets — but they only work if you wire them up.

**Step 1 — the Lua filter (mandatory).** `filters/latex-macros-to-unicode.lua` rewrites the two LaTeX-only constructs into Unicode. Register it under `filters:` in both the `docx` and `pptx` format blocks, as shown in §1.2. Without it:

| Source | PDF | DOCX/PPTX without filter |
| --- | --- | --- |
| `$\ce{Mg^2+}$` | Mg²⁺ | literal text `$\ce{Mg^2+}$` |
| `\qty{1.5}{\milli\mole\per\litre}` | 1.5 mmol L⁻¹ | **silently vanishes** — no warning |

The filter covers charges, subscripts and the unit macros it knows (`\milli\mole\per\litre` → `mmol L⁻¹`, `\degreeCelsius` → `°C`, `\micro\gram` → `µg`, …). It does **not** cover full mhchem — reactions with conditions, state symbols, complex isotope notation. For a DOCX-bound document, hand-write those in Unicode rather than trusting the filter.

**Step 2 — strip the caption wrapper (mandatory for DOCX).** Quarto wraps every captioned table in a 1×1 layout table, and that wrapper carries the same `Table` style as the data table. The style's top and bottom rules then draw an extra box, so the page shows **five** horizontal rules instead of three. Run after rendering:

```bash
python templates/fix_docx_tables.py output/report.docx
```

It forces wrapper tables borderless (those containing a nested table) and leaves real data tables on the three-line style.

**Order of operations for a DOCX deliverable:** `quarto render … --to docx` → `python templates/fix_docx_tables.py <file>`.

### 3.1 Style Reference Matrices

- **`nature_style.docx`**: derived from **Pandoc's own default reference document**, so every style its writer expects is present (`Table`, `Table Caption`, `Body Text`, `Compact`, `Bibliography`, …). Body font `Times New Roman` (Latin) / `SimSun` (CJK) at 10.5pt, line spacing 1.35x. The `Table` style carries a **Three-line Table** preset: 1.5pt top and bottom rules, a 0.75pt rule under the header row, no vertical or inner rules. (Generating this file from a blank python-docx `Document()` instead — as an earlier version of §3.2 did — drops all those styles.)
- **`academic_style.pptx`**: 16:9 canvas (13.333in × 7.5in). Slide-master typography is **not** yet customised — headings and body inherit python-pptx's default theme.

### 3.2 Automated Initialization Script (`templates/setup_templates.py`)

```bash
python templates/setup_templates.py
```

The script derives `nature_style.docx` from `pandoc --print-default-data-file reference.docx` and then applies the §3.1 typography on top, so every style Pandoc's DOCX writer expects survives. It also emits the 16:9 `academic_style.pptx` and creates the `output/` and `assets/` directories. Re-run it whenever §3.1 changes — the script is the source of truth, not this document.

---

## Part 4: Stress Testing Defense Mechanisms & Hardcore Pre-Compilation Audit Checklist

### 4.1 Extreme Scenario Defense Algorithms

#### [Stress Test 1] Massive Bioinformatics Differential Expression Gene Table Injection

- **Risk:** Claude attempts to output a full Markdown table containing tens of thousands of tokens, causing context window exhaustion and data degradation.
- **Model Execution Block Algorithm:**
  > **IF** detected table row count > 10 OR column count > 6
  > **THEN** trigger data truncation mechanism. Claude outputs only the first 5 sample rows, and auto-inserts a Python external conversion script placeholder below:

  ````markdown
  | Gene | log2FC | p-value | FDR |
  |:-----|:-------|:--------|:----|
  | *TP53* | 2.34 | 0.001 | 0.015 |
  | ... | ... | ... | ... |

  ```python
  import pandas as pd
  df = pd.read_csv("../assets/deg_data.csv")
  print(df.head(5).to_markdown())  # User should stream the output into the qmd document
  ```
  ````

#### [Stress Test 2] Deeply Nested Complex Formulas & Chemical Modifications

- **Risk:** Complex mathematical matrices or `mhchem` formulas with unmatched brackets cause local XeLaTeX/Pandoc compilation thread deadlock.
- **Model Execution Block Algorithm:**
  - **Enforce "Display Formula Absolute Isolation Principle"**: All `$$` blocks MUST occupy entire lines, with blank lines above and below.
  - **Trigger Character Closure Audit**: Top-down stack-matching check on generated strings, ensuring `$`, `{`, `[`, `(` are 100% closed. If not closed, REFUSE to submit output.

#### [Stress Test 3] VS Code Relative Path Drift

- **Risk:** User opens VS Code in a subdirectory, causing `../templates/` relative path breakage.
- **Model Execution Block Algorithm:**
  - Before any path-involving code output, MUST throw a hard warning block at the top, declaring workspace directory hierarchy:

  ```markdown
  > [RUNTIME PATH WARNING] Ensure VS Code workspace root is set to project base folder.
  > Compilation commands rely on relative tracking: current target = ${workspaceFolder}/src
  ```

### 4.2 Pre-Compilation Hardcore Audit Checklist

Before final code delivery to local VS Code, Claude MUST run through all of the following checks internally:

- [ ] **Gene Italic Compliance Rate:** Verify ALL `*Cas9*`, `*Ref-1*` etc. have italics applied, and ALL corresponding proteins have italics stripped.
- [ ] **Thin-Space Completeness:** Check DNA/RNA sequence strings — does every 10-base group have ` ` or `\quad` separation.
- [ ] **Physical Quantity Thin Space:** Check for bare `25°C` or `15min` — must ALL be converted to `\qty{25}{\degreeCelsius}` or `\qty{15}{\minute}`.
- [ ] **Zero Unicode Superscripts:** Check for `³` or `⁻` characters directly copied from external literature — must ALL be cleaned to standard LaTeX syntax `^3` or `^-`.
- [ ] **Vector Graphic Resolution Block:** Check all referenced image formats — if PNG/JPG, has user confirmed resolution ≥ **300 DPI** for Nature-grade print standard.
- [ ] **PPTX Density Block:** Check PPTX mode — number of unordered list items under each `##` heading must be strictly ≤ 7 lines.
