"""Build the DOCX/PPTX reference templates for the academic-typesetting skill.

The DOCX reference is derived from Pandoc's own default reference.docx so that
every style Pandoc's writer expects (Table, Table Caption, Body Text, Compact,
Bibliography, ...) is present. Generating a blank python-docx Document instead
-- as an earlier version of this script did -- drops those styles, which makes
Quarto wrap captioned tables in a 1x1 layout table and strip the caption style.

Usage:
    python setup_templates.py
"""

import subprocess
import tempfile
from pathlib import Path

from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt
from pptx import Presentation
from pptx.util import Inches

TEMPLATE_DIR = Path(__file__).parent.resolve()
WORKSPACE_DIR = TEMPLATE_DIR.parent.resolve()

LATIN = "Times New Roman"
CJK = "SimSun"
BODY_PT = 10.5

# w:sz is in eighths of a point: 12 = 1.5pt, 6 = 0.75pt
TOP_BOTTOM_SZ = "12"
HEADER_RULE_SZ = "6"


def _set_run_font(style, size=BODY_PT, bold=None, line_spacing=None):
    font = style.font
    font.name = LATIN
    font.size = Pt(size)
    if bold is not None:
        font.bold = bold
    if line_spacing is not None:
        style.paragraph_format.line_spacing = line_spacing
    rpr = style.element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.insert(0, rfonts)
    rfonts.set(qn("w:ascii"), LATIN)
    rfonts.set(qn("w:hAnsi"), LATIN)
    rfonts.set(qn("w:cs"), LATIN)
    rfonts.set(qn("w:eastAsia"), CJK)


def _border(tag, val, sz):
    el = OxmlElement(f"w:{tag}")
    el.set(qn("w:val"), val)
    el.set(qn("w:sz"), sz)
    el.set(qn("w:space"), "0")
    el.set(qn("w:color"), "000000")
    return el


def _apply_three_line_table_style(style):
    """Top rule, header rule, bottom rule. No vertical or inner rules."""
    el = style.element

    for tag in ("w:tblPr", "w:tblStylePr"):
        old = el.find(qn(tag))
        if old is not None:
            el.remove(old)

    tblpr = OxmlElement("w:tblPr")
    borders = OxmlElement("w:tblBorders")
    borders.append(_border("top", "single", TOP_BOTTOM_SZ))
    borders.append(_border("left", "none", "0"))
    borders.append(_border("bottom", "single", TOP_BOTTOM_SZ))
    borders.append(_border("right", "none", "0"))
    borders.append(_border("insideH", "none", "0"))
    borders.append(_border("insideV", "none", "0"))
    tblpr.append(borders)
    el.append(tblpr)

    stylepr = OxmlElement("w:tblStylePr")
    stylepr.set(qn("w:type"), "firstRow")
    tcpr = OxmlElement("w:tcPr")
    tcborders = OxmlElement("w:tcBorders")
    tcborders.append(_border("bottom", "single", HEADER_RULE_SZ))
    tcpr.append(tcborders)
    stylepr.append(tcpr)
    el.append(stylepr)


def _build_docx_reference(dest: Path):
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp) / "pandoc-default-reference.docx"
        raw = subprocess.run(
            ["pandoc", "--print-default-data-file", "reference.docx"],
            capture_output=True,
            check=True,
        ).stdout
        base.write_bytes(raw)

        doc = Document(str(base))
        styles = doc.styles
        have = {s.name for s in styles}

        _set_run_font(styles["Normal"], line_spacing=1.35)
        for name in ("Body Text", "First Paragraph", "Compact", "Caption",
                     "Table Caption", "Image Caption", "Bibliography",
                     "Title", "Subtitle", "Author", "Date"):
            if name in have:
                _set_run_font(styles[name], line_spacing=1.35)
        for lvl in range(1, 10):
            name = f"Heading {lvl}"
            if name in have:
                _set_run_font(styles[name], bold=True)

        _apply_three_line_table_style(styles["Table"])

        doc.save(str(dest))


def _build_pptx_reference(dest: Path):
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    prs.save(str(dest))


def init_workspace():
    output_dir = WORKSPACE_DIR / "output"
    assets_dir = WORKSPACE_DIR / "assets"
    output_dir.mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir(parents=True, exist_ok=True)

    docx_ref = TEMPLATE_DIR / "nature_style.docx"
    _build_docx_reference(docx_ref)
    print(f"  [OK] {docx_ref}")

    pptx_ref = TEMPLATE_DIR / "academic_style.pptx"
    _build_pptx_reference(pptx_ref)
    print(f"  [OK] {pptx_ref}")

    print(f"\nWorkspace initialized:\n  Templates: {TEMPLATE_DIR}"
          f"\n  Output:    {output_dir}\n  Assets:    {assets_dir}")


if __name__ == "__main__":
    init_workspace()
