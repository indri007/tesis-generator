from pathlib import Path

from engines.docx_parser import parse_docx
from engines.pdf_parser import parse_pdf


def parse_document(path: str):
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
