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
