from pathlib import Path

try:
    import pymupdf as fitz
except ImportError:
    import fitz

from models.document_model import (
    ParsedDocument,
    ParsedParagraph,
)


def parse_pdf(path: str) -> ParsedDocument:
    file_path = Path(path)

    if not file_path.is_file():
        raise FileNotFoundError(path)

    result = ParsedDocument(
        filename=file_path.name,
        file_type="pdf",
    )

    with fitz.open(str(file_path)) as pdf:
        if pdf.needs_pass:
            raise ValueError(
                "PDF memerlukan kata sandi."
            )

        result.page_count = pdf.page_count

        metadata = pdf.metadata or {}
        result.metadata = {
            "title": metadata.get("title") or "",
            "author": metadata.get("author") or "",
            "subject": metadata.get("subject") or "",
        }

        pages_without_text = []

        for page_index, page in enumerate(pdf):
            page_number = page_index + 1
            text = page.get_text("text", sort=True)

            if not text.strip():
                pages_without_text.append(page_number)
                continue

            result.paragraphs.append(
                ParsedParagraph(
                    text=text.strip(),
                    page=page_number,
                    source_type="pdf_page_text",
                )
            )

        if pages_without_text:
            result.warnings.append(
                "Halaman tanpa teks yang dapat diekstrak: "
                + ", ".join(map(str, pages_without_text))
                + ". Periksa kemungkinan PDF hasil scan."
            )

        result.format_data = {
            "pages": [
                {
                    "page": page.number + 1,
                    "width_pt": round(page.rect.width, 2),
                    "height_pt": round(page.rect.height, 2),
                    "rotation": page.rotation,
                }
                for page in pdf
            ]
        }

    return result
