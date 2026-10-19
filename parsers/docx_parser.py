"""DOCX parser for extracting typographic, geometric, and structural properties."""

from __future__ import annotations

from typing import Any

import docx
from docx.enum.text import WD_ALIGN_PARAGRAPH


class DocxParser:
    """Extracts typography, layout, formatting, tables, and text from .docx files."""

    def __init__(self, file_path_or_stream: Any):
        self.doc = docx.Document(file_path_or_stream)

    def extract_page_setup(self) -> dict[str, Any]:
        """Extracts margins and page dimensions from document sections."""
        sections_data = []
        for i, s in enumerate(self.doc.sections):
            top_cm = round(s.top_margin.cm, 2) if s.top_margin else None
            left_cm = round(s.left_margin.cm, 2) if s.left_margin else None
            bottom_cm = round(s.bottom_margin.cm, 2) if s.bottom_margin else None
            right_cm = round(s.right_margin.cm, 2) if s.right_margin else None
            width_cm = round(s.page_width.cm, 2) if s.page_width else None
            height_cm = round(s.page_height.cm, 2) if s.page_height else None

            sections_data.append({
                "section_index": i,
                "top_cm": top_cm,
                "left_cm": left_cm,
                "bottom_cm": bottom_cm,
                "right_cm": right_cm,
                "width_cm": width_cm,
                "height_cm": height_cm,
                "orientation": str(s.orientation)
            })

        first_section = sections_data[0] if sections_data else {}
        return {
            "sections": sections_data,
            "primary_margins": {
                "top_cm": first_section.get("top_cm", 4.0),
                "left_cm": first_section.get("left_cm", 4.0),
                "bottom_cm": first_section.get("bottom_cm", 3.0),
                "right_cm": first_section.get("right_cm", 3.0)
            },
            "primary_dimensions": {
                "width_cm": first_section.get("width_cm", 21.0),
                "height_cm": first_section.get("height_cm", 29.7)
            }
        }

    def extract_paragraphs(self) -> list[dict[str, Any]]:
        """Extracts paragraph items with typography, spacing, alignment, and text."""
        result = []
        for idx, p in enumerate(self.doc.paragraphs):
            text = p.text.strip()
            if not text:
                continue

            # Typography from runs
            fonts = set()
            sizes = set()
            bolds = []
            italics = []

            for r in p.runs:
                if r.font.name:
                    fonts.add(r.font.name)
                if r.font.size and hasattr(r.font.size, "pt"):
                    sizes.add(round(r.font.size.pt, 1))
                if r.bold is not None:
                    bolds.append(r.bold)
                if r.italic is not None:
                    italics.append(r.italic)

            # Alignment
            align_name = "UNKNOWN"
            if p.alignment == WD_ALIGN_PARAGRAPH.JUSTIFY:
                align_name = "JUSTIFY"
            elif p.alignment == WD_ALIGN_PARAGRAPH.CENTER:
                align_name = "CENTER"
            elif p.alignment == WD_ALIGN_PARAGRAPH.LEFT:
                align_name = "LEFT"
            elif p.alignment == WD_ALIGN_PARAGRAPH.RIGHT:
                align_name = "RIGHT"

            # Line Spacing
            line_spacing = p.paragraph_format.line_spacing
            spacing_val: float | None = None
            if isinstance(line_spacing, (int, float)):
                spacing_val = float(line_spacing)
            elif line_spacing and hasattr(line_spacing, "pt"):
                # Approximate 12pt line * 1.5/2
                spacing_val = round(line_spacing.pt / 12.0, 2)

            result.append({
                "index": idx,
                "text": text,
                "style": p.style.name if p.style else "",
                "fonts": list(fonts),
                "sizes": list(sizes),
                "is_bold": any(bolds) if bolds else False,
                "is_italic": any(italics) if italics else False,
                "alignment": align_name,
                "line_spacing": spacing_val
            })
        return result

    def extract_tables(self) -> list[dict[str, Any]]:
        """Extracts tables and their dimensions."""
        tables_data = []
        for idx, table in enumerate(self.doc.tables):
            row_count = len(table.rows)
            col_count = len(table.columns) if row_count > 0 else 0
            sample_cells = []
            for row in table.rows[:3]:
                sample_cells.append([c.text.strip() for c in row.cells[:4]])

            tables_data.append({
                "table_index": idx + 1,
                "row_count": row_count,
                "col_count": col_count,
                "sample_preview": sample_cells
            })
        return tables_data

    def estimate_page_count(self) -> int:
        """Estimates or extracts total page count for DOCX."""
        # Check explicit page breaks
        breaks = 0
        total_words = 0
        for p in self.doc.paragraphs:
            total_words += len(p.text.split())
            for r in p.runs:
                if "\f" in r.text:
                    breaks += 1

        # In typical standard double spaced A4, 1 page ~ 250 - 300 words
        estimated_by_words = max(1, total_words // 260)
        return max(breaks + 1, estimated_by_words)

    def extract_all(self) -> dict[str, Any]:
        """Aggregate all extracted data into structured dictionary."""
        page_setup = self.extract_page_setup()
        paragraphs = self.extract_paragraphs()
        tables = self.extract_tables()
        estimated_pages = self.estimate_page_count()
        full_text = "\n".join([p["text"] for p in paragraphs])

        return {
            "format": "docx",
            "page_count": estimated_pages,
            "page_setup": page_setup,
            "paragraphs": paragraphs,
            "tables": tables,
            "full_text": full_text
        }
