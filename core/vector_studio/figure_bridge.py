"""Figure Bridge Module for Vector Design Studio.

Bridges VectorProjectSchema and SVG outputs into scientific publication formats:
- Lossless SVG to High-Resolution PNG (300 DPI) using PyMuPDF (fitz) + Pillow.
- Lossless SVG to Vector PDF.
- Direct DOCX figure injection with standard Pedoman Penulisan Tesis MIKOM 2026:
  * Centered figure insertion.
  * Formal label (e.g., 'Gambar 3.1: Diagram Alir Seleksi Literatur Berdasarkan PRISMA 2020').
  * Source note (e.g., 'Sumber: Data diolah penulis berdasarkan Page et al. (2021)').
  * Times New Roman typography and precise margins.
"""

from __future__ import annotations

import io
from pathlib import Path
from typing import Any

import fitz  # PyMuPDF

from core.vector_studio.document_schema import FigureAttribution, VectorProjectSchema
from core.vector_studio.svg_engine import SVGEngine


class FigureBridge:
    """Exports and formats vector figures for academic documents."""

    @classmethod
    def project_to_svg(
        cls,
        project: VectorProjectSchema,
        include_attribution: bool = False,
    ) -> str:
        """Compiles project to W3C SVG XML string."""
        return SVGEngine.compile_project_to_svg(project, include_attribution=include_attribution)

    @classmethod
    def svg_to_png_bytes(cls, svg_str: str, dpi: int = 300) -> bytes:
        """Renders SVG XML string to high-resolution PNG bytes using PyMuPDF."""
        svg_bytes = svg_str.encode("utf-8")
        doc = fitz.open(stream=svg_bytes, filetype="svg")
        try:
            page = doc[0]
            pix = page.get_pixmap(dpi=dpi)
            return pix.tobytes(output="png")
        finally:
            doc.close()

    @classmethod
    def svg_to_pdf_bytes(cls, svg_str: str) -> bytes:
        """Converts SVG XML string to vector PDF bytes using PyMuPDF."""
        svg_bytes = svg_str.encode("utf-8")
        doc = fitz.open(stream=svg_bytes, filetype="svg")
        try:
            return doc.convert_to_pdf()
        finally:
            doc.close()

    @classmethod
    def export_project_to_files(
        cls,
        project: VectorProjectSchema,
        output_dir: str | Path,
        base_filename: str = "thesis_figure",
        dpi: int = 300,
    ) -> dict[str, Path]:
        """Exports project into JSON, SVG, PNG (300 DPI), and PDF files simultaneously."""
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)

        results: dict[str, Path] = {}

        # 1. Project JSON Schema
        json_file = out_path / f"{base_filename}.atg.json"
        json_file.write_text(project.to_json(indent=2), encoding="utf-8")
        results["json"] = json_file

        # 2. W3C SVG
        svg_str = cls.project_to_svg(project, include_attribution=False)
        svg_file = out_path / f"{base_filename}.svg"
        svg_file.write_text(svg_str, encoding="utf-8")
        results["svg"] = svg_file

        # 3. High-Res PNG (300 DPI)
        png_bytes = cls.svg_to_png_bytes(svg_str, dpi=dpi)
        png_file = out_path / f"{base_filename}.png"
        png_file.write_bytes(png_bytes)
        results["png"] = png_file

        # 4. Vector PDF
        pdf_bytes = cls.svg_to_pdf_bytes(svg_str)
        pdf_file = out_path / f"{base_filename}.pdf"
        pdf_file.write_bytes(pdf_bytes)
        results["pdf"] = pdf_file

        return results

    @classmethod
    def inject_figure_into_docx(
        cls,
        docx_doc: Any,
        project: VectorProjectSchema,
        width_inches: float = 6.0,
        dpi: int = 300,
    ) -> None:
        """Appends formatted vector figure with Pedoman MIKOM 2026 attribution into a python-docx Document.

        Format:
        1. Title: Gambar [Bab].[Nomor]: [Judul Gambar] (Center, Bold, 12 pt, Space After)
        2. Image: Centered 300 DPI PNG
        3. Source: Sumber: [Keterangan Sumber] (Center, Italic, 10 pt, Space Before)
        """
        try:
            from docx.enum.text import WD_ALIGN_PARAGRAPH
            from docx.shared import Inches, Pt, RGBColor
        except ImportError as err:
            raise ImportError("python-docx is required for docx injection.") from err

        attribution: FigureAttribution = project.attribution or FigureAttribution()

        # Render 300 DPI PNG stream in-memory
        svg_str = cls.project_to_svg(project, include_attribution=False)
        png_bytes = cls.svg_to_png_bytes(svg_str, dpi=dpi)
        image_stream = io.BytesIO(png_bytes)

        # 1. Figure Title Paragraph (Top of figure or above figure)
        title_p = docx_doc.add_paragraph()
        title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        title_p.paragraph_format.space_before = Pt(12)
        title_p.paragraph_format.space_after = Pt(6)

        label_run = title_p.add_run(f"{attribution.figure_label}: ")
        label_run.bold = True
        label_run.font.name = "Times New Roman"
        label_run.font.size = Pt(11)
        label_run.font.color.rgb = RGBColor(0x14, 0x2A, 0x4A)

        title_run = title_p.add_run(attribution.title)
        title_run.font.name = "Times New Roman"
        title_run.font.size = Pt(11)
        title_run.font.color.rgb = RGBColor(0x14, 0x2A, 0x4A)

        # 2. Image Paragraph (Centered)
        img_p = docx_doc.add_paragraph()
        img_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        img_p.paragraph_format.space_before = Pt(4)
        img_p.paragraph_format.space_after = Pt(4)
        run_img = img_p.add_run()
        run_img.add_picture(image_stream, width=Inches(width_inches))

        # 3. Figure Source Note Paragraph (Bottom)
        source_p = docx_doc.add_paragraph()
        source_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        source_p.paragraph_format.space_before = Pt(4)
        source_p.paragraph_format.space_after = Pt(12)

        source_run = source_p.add_run(f"Sumber: {attribution.source}")
        source_run.italic = True
        source_run.font.name = "Times New Roman"
        source_run.font.size = Pt(10)
        source_run.font.color.rgb = RGBColor(0x47, 0x55, 0x69)
