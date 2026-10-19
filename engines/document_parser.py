from pathlib import Path

from engines.docx_parser import parse_docx
from engines.pdf_parser import parse_pdf
from models.document_model import ParsedDocument


def parse_document(path: str) -> ParsedDocument:
    file_path = Path(path)
    extension = file_path.suffix.lower()

    if extension == ".docx":
        return parse_docx(str(file_path))

    if extension == ".pdf":
        return parse_pdf(str(file_path))

    if extension == ".doc":
        raise ValueError(
            "Format DOC lama belum didukung. "
            "Konversi ke DOCX atau PDF terlebih dahulu."
        )

    raise ValueError(
        "Format tidak didukung. Gunakan DOCX atau PDF."
    )


def parse_single_citation(citation_text: str) -> dict[str, Any]:
    """Menguraikan satu teks sitasi menjadi struktur metadata (authors, year, title, doi)."""
    import re
    from typing import Any

    # Ekstraksi tahun (4 digit)
    year_match = re.search(r"\b(19\d\d|20\d\d)\b", citation_text)
    year = int(year_match.group(1)) if year_match else None

    # Ekstraksi DOI jika ada
    doi_match = re.search(r"\b10\.\d{4,9}/[-._;()/:A-Za-z0-9]+\b", citation_text)
    doi = doi_match.group(0) if doi_match else None

    # Ekstraksi nama penulis
    clean_text = re.sub(r"^[(\[]|[)\]]$", "", citation_text.strip())
    tokens = [t.strip().strip(",") for t in clean_text.split() if not re.match(r"^\d{4}$", t.strip().strip(","))]
    authors = [tokens[0]] if tokens else ["Unknown"]

    return {
        "text": citation_text,
        "authors": authors,
        "year": year,
        "title": None,
        "doi": doi,
        "location": "naskah",
    }

