"""Revision Engine: Generates prioritized revision plans and automated formatting corrections."""

from __future__ import annotations

from typing import Any

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Pt


class RevisionEngine:
    """Classifies revision priorities and prepares corrected output files."""

    def __init__(self, findings: list[dict[str, Any]]):
        self.findings = findings

    def generate_checklist(self) -> dict[str, list[dict[str, Any]]]:
        """Categorizes findings into 3 actionable priority groups."""
        p1 = []  # Wajib Diperbaiki (Akademik, Rumus, Statistik, Sampel, Variabel)
        p2 = []  # Penting (Struktur bab, Sitasi, Rujukan)
        p3 = []  # Format (Margin, Font, Spasi)

        for f in self.findings:
            cat = f.get("category", "").lower()
            rule_id = f.get("rule_id", "")
            severity = f.get("status", "")

            if severity in ["PASS", "INFO"]:
                continue

            if any(k in cat for k in ["formula", "statistik", "variabel", "journal", "sample"]) or "RECALCULATION" in rule_id:
                p1.append(f)
            elif any(k in cat for k in ["struktur", "sitasi", "referensi", "abstrak"]):
                p2.append(f)
            else:
                p3.append(f)

        return {
            "PRIORITAS 1 — WAJIB DIPERBAIKI (Substantif & Validitas Ilmiah)": p1,
            "PRIORITAS 2 — PENTING (Struktur & Kelengkapan Akademik)": p2,
            "PRIORITAS 3 — FORMAT & TATA LETAK (Mekanik)": p3,
        }

    def apply_docx_formatting_fixes(self, input_path: str, output_path: str) -> bool:
        """Applies safe mechanical formatting corrections to a DOCX document:
        - Margins: Top 4cm, Left 4cm, Bottom 3cm, Right 3cm
        - Fonts: Times New Roman, 12pt
        - Spacing: Double (2.0)
        - Alignment: Justified
        """
        try:
            doc = Document(input_path)
            for section in doc.sections:
                section.top_margin = Cm(4.0)
                section.left_margin = Cm(4.0)
                section.bottom_margin = Cm(3.0)
                section.right_margin = Cm(3.0)

            for p in doc.paragraphs:
                p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                p.paragraph_format.line_spacing = 2.0
                for r in p.runs:
                    r.font.name = "Times New Roman"
                    r.font.size = Pt(12)

            doc.save(output_path)
            return True
        except Exception:
            return False
