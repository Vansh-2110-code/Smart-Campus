#!/usr/bin/env python3
"""
build_guides_pdf.py
===================
Converts PROJECT_GUIDE_BEGINNER.md and PROJECT_GUIDE_ADVANCED.md
into publication-quality executive PDF documents with:
- Academic Emerald Green & Crisp White design system
- Running headers & footers with dynamic 'Page X of Y' (NumberedCanvas)
- Comprehensive Unicode and ASCII sanitization (Zero black square ■ glyphs)
- Clean ASCII art box diagrams and crystal-clear code snippets
- Professional data tables with intelligent proportional column widths
- Blockquote callout boxes with emerald left borders
- Controlled page-breaks via <!-- pagebreak -->
"""

import os
import re
import sys
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Preformatted,
    KeepTogether,
    HRFlowable,
    PageBreak,
)

# Universal glyph replacement mapping for standard PostScript fonts
EMOJI_REPLACEMENTS = {
    "⚡": "[FAST]",
    "📸": "[PHOTO]",
    "▶": "[START]",
    "🟢": "[NORMAL]",
    "🟡": "[REVIEW]",
    "🔴": "[ALERT]",
    "🎓": "[ACADEMIC]",
    "🚪": "[DOOR]",
    "🚨": "[SECOPS]",
    "📋": "[QUEUE]",
    "📥": "[EXPORT]",
    "🔊": "[AUDIO]",
    "🧠": "[AI-MODEL]",
    "📜": "[DOCS]",
    "🌐": "[API-WEB]",
    "👥": "[HEADCOUNT]",
    "👤": "[PERSON]",
    "🏫": "[CAMPUS]",
    "🏢": "[BUILDING]",
    "🏛️": "[ADMIN]",
    "🔬": "[LAB]",
    "📚": "[LIBRARY]",
    "—": " -- ",
    "–": " - ",
    "“": '"',
    "”": '"',
    "‘": "'",
    "’": "'",
    "…": "...",
    "👉": "->",
    "•": "*",
    "✓": "[OK]",
    "✔": "[OK]",
    "✗": "[FAIL]",
    "❌": "[FAIL]",
    "⚠️": "[WARN]",
    "→": "->",
    "←": "<-",
    "↔": "<->",
    "≥": ">=",
    "≤": "<=",
    "≈": "~=",
    "≠": "!=",
    "±": "+/-",
    "µ": "u",
    "π": "pi",
    "θ": "theta",
    "λ": "lambda",
    "σ": "sigma",
    "δ": "delta",
    "Delta": "Delta",
    "mathbb": "",
    "mathcal": "",
}

BOX_REPLACEMENTS = {
    "┌": "+",
    "┐": "+",
    "└": "+",
    "┘": "+",
    "├": "+",
    "┤": "+",
    "┬": "+",
    "┴": "+",
    "┼": "+",
    "─": "-",
    "│": "|",
    "═": "=",
    "║": "|",
    "╔": "+",
    "╗": "+",
    "╚": "+",
    "╝": "+",
    "╠": "+",
    "╣": "+",
    "╦": "+",
    "╩": "+",
    "╬": "+",
    "▼": "v",
    "▲": "^",
    "►": ">",
    "◄": "<",
}


def sanitize_all_glyphs(text: str) -> str:
    """Replaces Unicode box-drawing characters and emojis with clean, printable ASCII equivalents."""
    for k, v in BOX_REPLACEMENTS.items():
        text = text.replace(k, v)
    for k, v in EMOJI_REPLACEMENTS.items():
        text = text.replace(k, v)
    return text


class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas to dynamically compute and draw running headers & 'Page X of Y' footers."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()

        # Top Accent Bar on Page 1
        if self._pageNumber == 1:
            self.setFillColor(colors.HexColor("#059669"))
            self.rect(0, 786, 612, 6, fill=True, stroke=False)
            self.setFillColor(colors.HexColor("#10B981"))
            self.rect(0, 782, 612, 4, fill=True, stroke=False)

        # Running Header (pages 2+)
        if self._pageNumber > 1:
            self.setFont("Helvetica-Bold", 7.5)
            self.setFillColor(colors.HexColor("#059669"))
            raw_title = getattr(self, "doc_title", "SMART CAMPUS INTELLIGENCE SYSTEM")
            doc_title = sanitize_all_glyphs(raw_title)
            self.drawString(45, 755, doc_title.upper())

            self.setFont("Helvetica", 7.5)
            self.setFillColor(colors.HexColor("#64748B"))
            self.drawRightString(612 - 45, 755, "UNIFIED ARCHITECTURE & VERIFICATION SPECIFICATION")

            self.setStrokeColor(colors.HexColor("#E2E8F0"))
            self.setLineWidth(0.75)
            self.line(45, 747, 612 - 45, 747)

        # Running Footer (all pages)
        self.setFont("Helvetica", 7.5)
        self.setFillColor(colors.HexColor("#64748B"))
        self.drawString(
            45, 30, "Smart Campus Unified Access & Biometric Attendance  |  DPDP Act 2023 Compliant"
        )
        self.drawRightString(
            612 - 45, 30, f"Page {self._pageNumber} of {page_count}"
        )
        self.setStrokeColor(colors.HexColor("#E2E8F0"))
        self.setLineWidth(0.75)
        self.line(45, 40, 612 - 45, 40)

        self.restoreState()


def clean_markdown_text(text: str) -> str:
    """Escapes HTML entities, sanitizes emojis, and translates markdown formatting."""
    text = sanitize_all_glyphs(text)

    # Escape HTML special chars
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;").replace(">", "&gt;")

    # Convert markdown bold **text** -> <b>text</b>
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)

    # Convert markdown italic *text* -> <i>text</i>
    text = re.sub(r"\*(.+?)\*", r"<i>\1</i>", text)

    # Convert markdown inline code `code` -> font
    text = re.sub(
        r"`(.+?)`",
        r'<font face="Courier" color="#065f46" size="7.5"><b>\1</b></font>',
        text,
    )

    # Convert markdown links [text](url) -> <u>text</u>
    text = re.sub(r"\[(.+?)\]\(.+?\)", r"<u>\1</u>", text)

    return text


def build_pdf_from_markdown(md_filepath: str, output_pdf_path: str, doc_title: str):
    """Parses markdown file and compiles into a publication-quality PDF."""
    print(f"\n[Compiling PDF] Reading: {md_filepath}")
    with open(md_filepath, "r", encoding="utf-8") as f:
        md_content = f.read()

    doc = SimpleDocTemplate(
        output_pdf_path,
        pagesize=letter,
        leftMargin=45,
        rightMargin=45,
        topMargin=46,
        bottomMargin=46,
    )

    styles = getSampleStyleSheet()

    # Color Palette
    c_emerald = colors.HexColor("#059669")
    c_dark = colors.HexColor("#064E3B")
    c_slate_dark = colors.HexColor("#0F172A")
    c_body = colors.HexColor("#334155")

    # Typography Styles
    title_style = ParagraphStyle(
        "PDFDocTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=c_dark,
        spaceAfter=4,
    )

    sub_title_style = ParagraphStyle(
        "PDFDocSubTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=14,
        textColor=c_emerald,
        spaceAfter=10,
    )

    h1_style = ParagraphStyle(
        "PDFH1",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11.5,
        leading=15.5,
        textColor=c_dark,
        spaceBefore=11,
        spaceAfter=5,
        keepWithNext=True,
    )

    h2_style = ParagraphStyle(
        "PDFH2",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9.5,
        leading=13.5,
        textColor=c_emerald,
        spaceBefore=8,
        spaceAfter=4,
        keepWithNext=True,
    )

    h3_style = ParagraphStyle(
        "PDFH3",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=12,
        textColor=c_slate_dark,
        spaceBefore=6,
        spaceAfter=3,
        keepWithNext=True,
    )

    body_style = ParagraphStyle(
        "PDFBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=11.5,
        textColor=c_body,
        spaceAfter=4,
    )

    bullet_style = ParagraphStyle(
        "PDFBullet",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=11.5,
        textColor=c_body,
        leftIndent=14,
        firstLineIndent=-10,
        spaceAfter=3,
    )

    code_block_style = ParagraphStyle(
        "PDFCode",
        parent=styles["Normal"],
        fontName="Courier",
        fontSize=6.7,
        leading=8.6,
        textColor=colors.HexColor("#0F172A"),
    )

    math_block_style = ParagraphStyle(
        "PDFMath",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#065F46"),
    )

    blockquote_style = ParagraphStyle(
        "PDFBlockquote",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=11.5,
        textColor=colors.HexColor("#064E3B"),
    )

    story = []
    lines = md_content.splitlines()

    in_code_block = False
    code_lines = []
    code_lang = ""

    in_table = False
    table_rows = []

    for line in lines:
        stripped = line.strip()

        # Handle Page Break Tag
        if stripped in ("<!-- pagebreak -->", "[PAGEBREAK]"):
            story.append(PageBreak())
            continue

        # Handle Code Block Start / End
        if stripped.startswith("```"):
            if in_code_block:
                in_code_block = False
                code_text = "\n".join(code_lines)
                sanitized_code = sanitize_all_glyphs(code_text)
                
                pre = Preformatted(sanitized_code, code_block_style)
                code_table = Table([[pre]], colWidths=[522])
                code_table.setStyle(
                    TableStyle([
                        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
                        ("BOX", (0, 0), (-1, -1), 0.75, colors.HexColor("#CBD5E1")),
                        ("LINEBEFORE", (0, 0), (0, -1), 3, colors.HexColor("#10B981")),
                        ("TOPPADDING", (0, 0), (-1, -1), 4),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                        ("LEFTPADDING", (0, 0), (-1, -1), 6),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ])
                )
                story.append(code_table)
                story.append(Spacer(1, 4))
                code_lines = []
            else:
                in_code_block = True
                code_lang = stripped[3:].strip()
                code_lines = []
            continue

        if in_code_block:
            code_lines.append(line)
            continue

        # Handle Markdown Tables
        if "|" in line and (line.startswith("|") or stripped.startswith("|")):
            if re.match(r"^\|?\s*[-:]+[-| :]*$", stripped):
                continue
            cells = [c.strip() for c in stripped.strip("|").split("|")]
            if cells:
                table_rows.append(cells)
                in_table = True
            continue
        else:
            if in_table and table_rows:
                in_table = False
                num_cols = max(len(r) for r in table_rows)
                
                if num_cols == 2:
                    col_widths = [150, 372]
                elif num_cols == 3:
                    col_widths = [130, 160, 232]
                elif num_cols == 4:
                    col_widths = [120, 110, 130, 162]
                else:
                    col_widths = [522 / max(1, num_cols)] * num_cols

                formatted_table_data = []
                for row_idx, row in enumerate(table_rows):
                    while len(row) < num_cols:
                        row.append("")
                    row_cells = []
                    for cell in row:
                        if row_idx == 0:
                            p = Paragraph(f"<b>{clean_markdown_text(cell)}</b>", ParagraphStyle(
                                "TH", parent=body_style, fontSize=7.5, leading=9.5, textColor=colors.white
                            ))
                        else:
                            p = Paragraph(clean_markdown_text(cell), ParagraphStyle(
                                "TD", parent=body_style, fontSize=7.2, leading=9.5
                            ))
                        row_cells.append(p)
                    formatted_table_data.append(row_cells)

                t = Table(formatted_table_data, colWidths=col_widths)
                t.setStyle(
                    TableStyle([
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#059669")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
                        ("TOPPADDING", (0, 0), (-1, -1), 4),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                        ("LEFTPADDING", (0, 0), (-1, -1), 5),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                    ])
                )
                story.append(t)
                story.append(Spacer(1, 5))
                table_rows = []

        # Empty line
        if not stripped:
            continue

        # Horizontal Rule
        if stripped.startswith("---") or stripped.startswith("***"):
            story.append(Spacer(1, 2))
            story.append(HRFlowable(width="100%", thickness=0.75, color=colors.HexColor("#E2E8F0"), spaceAfter=5, spaceBefore=3))
            continue

        # Blockquote (> text)
        if stripped.startswith(">"):
            b_text = stripped[1:].strip()
            b_text = re.sub(r"^\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]\s*", r"<b>[\1]</b> ", b_text)
            bq_p = Paragraph(clean_markdown_text(b_text), blockquote_style)
            bq_table = Table([[bq_p]], colWidths=[522])
            bq_table.setStyle(
                TableStyle([
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F0FDF4")),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#BBF7D0")),
                    ("LINEBEFORE", (0, 0), (0, -1), 3, colors.HexColor("#059669")),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ])
            )
            story.append(bq_table)
            story.append(Spacer(1, 4))
            continue

        # Math block $$ ... $$
        if stripped.startswith("$$") and stripped.endswith("$$") and len(stripped) > 4:
            math_text = stripped[2:-2].strip()
            math_p = Paragraph(f"<b>Formula:</b> {clean_markdown_text(math_text)}", math_block_style)
            m_table = Table([[math_p]], colWidths=[522])
            m_table.setStyle(
                TableStyle([
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#ECFDF5")),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#A7F3D0")),
                    ("LINEBEFORE", (0, 0), (0, -1), 2.5, colors.HexColor("#059669")),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ])
            )
            story.append(m_table)
            story.append(Spacer(1, 4))
            continue

        # Headers
        if stripped.startswith("# "):
            title_text = clean_markdown_text(stripped[2:])
            story.append(Paragraph(title_text, title_style))
            story.append(Spacer(1, 2))
            continue
        elif stripped.startswith("## "):
            h_text = clean_markdown_text(stripped[3:])
            story.append(Paragraph(h_text, h1_style))
            continue
        elif stripped.startswith("### "):
            h_text = clean_markdown_text(stripped[4:])
            story.append(Paragraph(h_text, h2_style))
            continue
        elif stripped.startswith("#### "):
            h_text = clean_markdown_text(stripped[5:])
            story.append(Paragraph(h_text, h3_style))
            continue

        # Bullet list items (- or * or numbered like 1. )
        bullet_match = re.match(r"^(\*|-|\d+\.)\s+(.+)$", stripped)
        if bullet_match:
            bullet_sym = bullet_match.group(1)
            b_text = f"<b>{bullet_sym}</b>  {clean_markdown_text(bullet_match.group(2))}"
            story.append(Paragraph(b_text, bullet_style))
            continue

        # Regular Body Paragraph
        p_text = clean_markdown_text(stripped)
        story.append(Paragraph(p_text, body_style))

    # Build document
    def canvas_factory(*args, **kwargs):
        c = NumberedCanvas(*args, **kwargs)
        c.doc_title = doc_title
        return c

    doc.build(story, canvasmaker=canvas_factory)
    print(f"[Success] Generated PDF: {output_pdf_path} (Size: {os.path.getsize(output_pdf_path):,} bytes)")


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # 1. Compile Beginner Guide
    beginner_md = os.path.join(base_dir, "PROJECT_GUIDE_BEGINNER.md")
    beginner_pdf = os.path.join(base_dir, "PROJECT_GUIDE_BEGINNER.pdf")
    if os.path.exists(beginner_md):
        build_pdf_from_markdown(
            md_filepath=beginner_md,
            output_pdf_path=beginner_pdf,
            doc_title="Smart Campus System - Complete Beginner's Guide",
        )

    # 2. Compile Advanced Guide
    advanced_md = os.path.join(base_dir, "PROJECT_GUIDE_ADVANCED.md")
    advanced_pdf = os.path.join(base_dir, "PROJECT_GUIDE_ADVANCED.pdf")
    if os.path.exists(advanced_md):
        build_pdf_from_markdown(
            md_filepath=advanced_md,
            output_pdf_path=advanced_pdf,
            doc_title="Smart Campus System - Advanced Architectural Specification",
        )


if __name__ == "__main__":
    main()
