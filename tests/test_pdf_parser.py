import fitz

from engines.pdf_parser import parse_pdf


def test_parse_pdf(tmp_path):
    path = tmp_path / "sample.pdf"

    with fitz.open() as pdf:
        page = pdf.new_page()
        page.insert_text(
            (72, 72),
            "BAB I PENDAHULUAN"
        )
        pdf.save(str(path))

    result = parse_pdf(str(path))

    assert result.file_type == "pdf"
    assert result.page_count == 1
    assert "BAB I PENDAHULUAN" in result.get_text()
    assert result.paragraphs[0].page == 1
