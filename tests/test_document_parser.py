from pathlib import Path

import fitz
import pytest
from docx import Document

from engines.document_parser import parse_document


def test_parse_document_dispatcher(tmp_path: Path):
    docx_path = tmp_path / "thesis.docx"
    doc = Document()
    doc.add_paragraph("Uji DOCX")
    doc.save(str(docx_path))

    pdf_path = tmp_path / "thesis.pdf"
    with fitz.open() as pdf:
        p = pdf.new_page()
        p.insert_text((72, 72), "Uji PDF")
        pdf.save(str(pdf_path))

    # Dispatch DOCX
    parsed_docx = parse_document(str(docx_path))
    assert parsed_docx.file_type == "docx"

    # Dispatch PDF
    parsed_pdf = parse_document(str(pdf_path))
    assert parsed_pdf.file_type == "pdf"

    # Dispatch Unsupported
    with pytest.raises(ValueError, match="Format DOC lama belum didukung"):
        parse_document("test.doc")

    with pytest.raises(ValueError, match="Format tidak didukung"):
        parse_document("test.txt")
