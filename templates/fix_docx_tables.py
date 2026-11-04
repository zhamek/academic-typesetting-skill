"""Strip borders from Quarto's caption-wrapper tables in a rendered DOCX.

Quarto wraps a captioned table in a 1x1 layout table that carries the same
`Table` style as the real data table. The style's top and bottom rules then draw
an extra box around the caption and the table, so the page shows five horizontal
rules instead of the three a three-line table should have (one above the caption,
one below the table, plus the data table's own three).

This script leaves data tables on the three-line `Table` style and forces every
wrapper table (a table that contains a nested table) to no borders.

Run it after `quarto render --to docx`:

    python fix_docx_tables.py output/report.docx
"""

import sys
from pathlib import Path

from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

# CT_TblPr child order: tblBorders must sit after these ...
_BEFORE_BORDERS = (
    "tblStyle", "tblpPr", "tblOverlap", "bidiVisual", "tblStyleRowBandSize",
    "tblStyleColBandSize", "tblW", "jc", "tblCellSpacing", "tblInd",
)
# ... and before these.
_AFTER_BORDERS = (
    "shd", "tblLayout", "tblCellMar", "tblLook", "tblCaption", "tblDescription",
)

_EDGES = ("top", "left", "bottom", "right", "insideH", "insideV")


def _has_nested_table(tbl_element):
    """True if this table contains another table (i.e. it is a wrapper)."""
    return tbl_element.find(".//" + qn("w:tbl")) is not None


def _set_borderless(table):
    tbl_pr = table._tbl.tblPr

    old = tbl_pr.find(qn("w:tblBorders"))
    if old is not None:
        tbl_pr.remove(old)

    borders = OxmlElement("w:tblBorders")
    for edge in _EDGES:
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), "none")
        el.set(qn("w:sz"), "0")
        el.set(qn("w:space"), "0")
        el.set(qn("w:color"), "auto")
        borders.append(el)

    # Insert at the schema-correct position; Word rejects out-of-order tblPr.
    anchor = None
    for child in tbl_pr:
        tag = child.tag.split("}")[-1]
        if tag in _AFTER_BORDERS:
            anchor = child
            break
    if anchor is not None:
        anchor.addprevious(borders)
    else:
        tbl_pr.append(borders)


def fix(path):
    doc = Document(str(path))
    fixed = 0
    for table in doc.tables:          # top-level tables only
        if _has_nested_table(table._tbl):
            _set_borderless(table)
            fixed += 1
    if fixed:
        doc.save(str(path))
    return fixed


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: python fix_docx_tables.py <file.docx> [more.docx ...]")
        raise SystemExit(2)
    for arg in sys.argv[1:]:
        p = Path(arg)
        n = fix(p)
        print(f"  [{'OK' if n else '--'}] {p}  (wrapper tables stripped: {n})")
