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

---

## Part 1: Quarto Compilation Engine Profiles

### 1.1 Environment Pre-flight Check

Before any compilation, verify the local LaTeX compiler is reachable:

```bash
xelatex --version
```

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
          \usepackage[skip=8pt, indent=0pt]{parskip}
          \widowpenalty=10000
          \clubpenalty=10000
          
  docx:
    reference-doc: ../templates/nature_style.docx
    toc: false
    number-sections: true

  pptx:
    reference-doc: ../templates/academic_style.pptx
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
pandoc report.md -o output/report.pdf --pdf-engine=xelatex \
  -V mainfont="Times New Roman" -V CJKmainfont="Noto Serif SC" \
  -V documentclass=extarticle -V fontsize=10.5pt \
  -V geometry:"top=2.2cm, bottom=2.2cm, left=2.2cm, right=2.2cm"

# DOCX
pandoc report.md -o output/report.docx --reference-doc=templates/nature_style.docx

# PPTX
pandoc report.md -o output/report.pptx --reference-doc=templates/academic_style.pptx
```

---

## Part 2: Semantic Markdown Academic Writing Syntax

### 2.1 Canonical Text Example

```markdown
## Introduction

The optimization of *Prime Editing* vectors requires precise spatial control of the split-*SpCas9* architecture [@an理论2024]. As illustrated in @fig-pipeline, the concentration of $\ce{Mg^2+}$ ions was strictly maintained at \qty{1.5}{\milli\Molar} within the reaction buffer.

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
- **Physical quantities**: Always `\qty{number}{unit}`. Number and unit separated by non-breaking space (handled by siunitx).
- **Gene symbols**: `*GENE_NAME*` (italic).
- **Protein symbols**: Plain text `PROTEIN_NAME` (upright).
- **Sequences**: Backtick-wrapped with thin-space grouping every 10 bases.
- **Ranges**: Use en-dash `--` (e.g., pH 5.5--6.5), NEVER bare `~`.
- **Tables**: Pipe table format, caption BELOW table with `: Caption {#tbl-id}`.
- **Figures**: Caption ABOVE or BELOW image, vector format preferred, width anchored.

---

## Part 3: Reference Template Architecture & Initialization Script

### 3.1 Style Reference Matrices

- **`nature_style.docx`**: Body font locked to `Times New Roman` (Latin) / `SimSun` (CJK), 10.5pt, justified. Line spacing 1.35x. Table style bound to **Three-line Table** preset: no vertical borders, thickened top/bottom borders.
- **`academic_style.pptx`**: Slide ratio locked to `16:9`. Slide Master top-level config: Title 36pt Bold Arial, Body 20pt Arial Regular.

### 3.2 Automated Initialization Script (`templates/setup_templates.py`)

```python
# templates/setup_templates.py — Path-resolved workspace initializer
import os
from pathlib import Path
from docx import Document
from docx.shared import Pt
from pptx import Presentation
from pptx.util import Inches

def init_workspace():
    # Force-lock script directory as the templates directory
    TEMPLATE_DIR = Path(__file__).parent.resolve()
    WORKSPACE_DIR = TEMPLATE_DIR.parent.resolve()
    
    OUTPUT_DIR = WORKSPACE_DIR / "output"
    ASSETS_DIR = WORKSPACE_DIR / "assets"
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)

    # Generate DOCX template with style archetype
    doc = Document()
    style = doc.styles['Normal']
    style.font.name = 'Times New Roman'
    style.font.size = Pt(10.5)
    doc.save(str(TEMPLATE_DIR / "nature_style.docx"))
    print(f"  [OK] nature_style.docx -> {TEMPLATE_DIR / 'nature_style.docx'}")

    # Generate 16:9 PPTX template
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    prs.save(str(TEMPLATE_DIR / "academic_style.pptx"))
    print(f"  [OK] academic_style.pptx -> {TEMPLATE_DIR / 'academic_style.pptx'}")

    print(f"\nWorkspace initialized:")
    print(f"  Templates: {TEMPLATE_DIR}")
    print(f"  Output:    {OUTPUT_DIR}")
    print(f"  Assets:    {ASSETS_DIR}")

if __name__ == "__main__":
    init_workspace()
```

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
