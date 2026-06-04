# Academic Typesetting — Claude Code Skill

[![Skill Type](https://img.shields.io/badge/Claude%20Code-Skill-8A2BE2)](https://claude.ai/code)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)]()

Integrated academic typography engine for [Claude Code](https://claude.ai/code) utilizing **Quarto** for single-source publishing to PDF, DOCX, and PPTX. Enforces **Nature/Science journal-grade** layout geometry, strict font discipline, bioinformatics nomenclature, vector graphics scaling, and Zotero CSL automated citation.

---

## Overview

This skill replaces the legacy `pdf-typography` skill with a unified engine covering three output formats from a single Markdown source (.qmd). Claude outputs **semantic Markdown** — zero OOXML/LaTeX template code generation, avoiding context window exhaustion and style degradation.

### Architecture

```
User writes .qmd (Markdown + LaTeX)
       │
       ▼
   Quarto / Pandoc compile
       │
       ├──→ PDF   (xelatex + mhchem + siunitx)
       ├──→ DOCX  (reference-doc: nature_style.docx)
       └──→ PPTX  (reference-doc: academic_style.pptx)
```

## Quick Start

### Prerequisites

| Tool | Purpose | Install |
|------|---------|---------|
| **Quarto** | Single-source compiler | `winget install quarto` or [quarto.org](https://quarto.org) |
| **Pandoc 3.9+** | AST conversion engine | Bundled with Quarto, or `winget install pandoc` |
| **XeLaTeX** | PDF rendering (Chinese font support) | `winget install TeXLive` or [tug.org](https://tug.org) |
| **python-docx** | One-time template generation | `pip install python-docx python-pptx` |
| **Git** | Version control | `winget install git` |

### Installation

1. Copy this skill directory to `~/.claude/skills/academic-typesetting/` (Claude Code auto-discovers it)
2. Run the one-time workspace initializer:

```bash
cd ~/.claude/skills/academic-typesetting/templates
python setup_templates.py
```

This generates `nature_style.docx` and `academic_style.pptx` reference templates.

3. Verify LaTeX compiler:

```bash
xelatex --version
```

### Usage in Claude Code

Trigger the skill by mentioning any of these keywords in your prompt:

> 排版 / 论文 / 报告 / 幻灯片 / 基因编辑 / 生信 / PDF / DOCX / PPTX / quarto / 三线表

Example:

> 帮我将这份实验报告排版为 PDF，包含化学式 $\ce{Ca(NO3)2.4H2O}$ 和三线表

Claude will generate a `.qmd` file in your project's `src/` directory. Compile with:

```bash
# All formats
quarto render src/report.qmd --output-dir output

# Single format
quarto render src/report.qmd --to pdf
quarto render src/report.qmd --to docx
quarto render src/report.qmd --to pptx
```

### Project Directory Convention

Per the user's CLAUDE.md global rules:

```
D:\000 cc\<your-project-name>\
├── src/
│   └── report.qmd          # Main Quarto source
├── templates/
│   ├── nature_style.docx   # DOCX reference template
│   ├── academic_style.pptx # PPTX reference template
│   └── nature.csl          # Citation style
├── assets/
│   └── figures/            # Vector graphics (SVG/PDF)
├── output/                 # Compiled output
├── references.bib          # BibTeX bibliography
└── .vscode/
    └── tasks.json          # VS Code build task
```

---

## Typography Specifications

### Font Stack

| Role | PDF / DOCX (Print) | PPTX (Projection) |
|------|-------------------|-------------------|
| Body Latin | Times New Roman (**Serif**) | Arial / Helvetica (**Sans-serif**) |
| Body CJK | SimSun / 宋体 (**Serif**) | SimHei / 黑体 (**Sans-serif**) |
| Heading Latin | Times New Roman Bold (**Serif**) | Arial Bold (**Sans-serif**) |
| Heading CJK | STZhongsong / 黑体 | SimHei / 黑体 |
| Monospace (Code/Seq) | Consolas / Courier New | Consolas |

### Type Scale

| Element | PDF / DOCX | PPTX |
|---------|-----------|------|
| Document Title | 20pt Bold | 36pt Bold |
| Heading 1 | 14pt Bold | 28pt Bold |
| Heading 2 | 12pt Bold | 24pt Bold |
| Body | 10.5pt (五号) | 18--22pt |
| Figure/Table Caption | 8.5pt | 14pt |
| References | 9pt | — |
| Header/Footer | 8pt | 10pt |

### Page Geometry

- **Paper**: A4 (210 × 297 mm)
- **Margins**: 2.2 cm all sides (print); 1.5 cm (slides)
- **Line spacing**: 1.35× (print); 1.2--1.5× (slides)
- **Paragraphs**: 8pt after, zero first-line indent
- **Slide ratio**: 16:9 (PPTX)

### Tables: Three-Line (Booktabs) Style

- Top rule: 1.5pt solid
- Header-bottom rule: 0.75pt solid
- Table-bottom rule: 1.5pt solid
- **No vertical borders** — ever
- **No interior horizontal borders**
- Caption **above** table (print) / above table (slides)

---

## Writing Rules

### Chemical Formulas

Always `$\ce{...}$` — Pandoc auto-converts to mhchem (PDF) or OMML (DOCX/PPTX):

```markdown
$\ce{Ca(NO3)2.4H2O}$ was used as the calcium source.
```

### Physical Quantities

Always `\qty{number}{unit}` — Pandoc converts to siunitx or thin-space formatting:

```markdown
Incubated at \qty{25}{\degreeCelsius} for \qty{30}{\minute}.
```

### Gene & Protein Nomenclature (Bioinformatics)

| Type | Format | Example |
|------|--------|---------|
| **Gene symbol** | *Italic* | *Cas9*, *PIK3CA*, *TP53* |
| **Protein symbol** | Upright | Cas9, PIK3CA, TP53 |
| **mRNA / cDNA** | Upright | mRNA, cDNA |
| **Species name** | *Italic* | *Homo sapiens* |
| **Restriction enzyme** | Upright | EcoRI, HindIII |
| **Mutation (protein)** | Upright, HGVS | p.Gly12Val |
| **Mutation (cDNA)** | Upright, HGVS | c.35G>A |

### Nucleotide / Amino Acid Sequences

Use backtick-wrapped code spans. For sequences > 10 bases, insert thin space (U+2009) every 10 bases:

```markdown
Primer: `5'-ATGCGATGCC GATGCATCGA TCGAT-3'`
```

### Vector Graphics

- **Preferred**: PDF (for PDF output) / SVG (for DOCX/PPTX output)
- **Raster fallback**: ≥ 300 DPI (EM images, gel photos)
- **Width anchoring**:
  - Single-column: `89mm`
  - Double-column: `183mm`

### Bibliography

- Mount `references.bib` at workspace root
- Use `nature.csl` — sequential superscript citation `[1]`
- In-text: `[@key2024]`

---

## Defense Mechanisms

The skill includes three hardcoded stress-test defense algorithms to prevent generation failures:

### 1. Massive Table Truncation

> **IF** table rows > 10 OR columns > 6
> **THEN** output only first 5 rows with external Python conversion script placeholder.

### 2. Bracket Closure Audit

> All `$`, `{`, `[`, `(` must pass stack-matching check before output.
> Display formulas (`$$...$$`) must occupy entire lines with blank lines above and below.

### 3. Relative Path Drift Warning

> Before any path-involving code, emit a runtime path warning block declaring the expected workspace root.

---

## Pre-Compilation Checklist

- [ ] Gene symbols italic (`*Gene*`), proteins upright
- [ ] DNA/RNA sequences: thin-space grouped every 10 bases
- [ ] Physical quantities: `\qty{}{}` wrapping, no bare `25°C`
- [ ] Zero Unicode superscripts (`³`, `⁻` → `^3`, `^-`)
- [ ] Vector graphics preferred; raster ≥ 300 DPI
- [ ] PPTX density: ≤ 7 list items per slide
- [ ] All brackets closed (stack-match verified)
- [ ] `xelatex --version` passes before PDF compilation

---

## File Structure

```
academic-typesetting/
├── SKILL.md                        # Main skill definition
├── README.md                       # This file
├── templates/
│   ├── nature_style.docx           # DOCX reference template
│   ├── academic_style.pptx         # PPTX reference template
│   └── setup_templates.py          # One-time initializer
├── assets/                         # Figure storage
└── output/                         # Compiled output
```

## License

MIT — Use, modify, and distribute freely. Attribution appreciated.

---

*Built for Claude Code. Nature is a registered trademark of Springer Nature Limited. This skill is an independent project and not affiliated with Springer Nature.*
