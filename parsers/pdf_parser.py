"""PDF parser for extracting page count, text per page, scan detection, and layout."""

from __future__ import annotations

import io
from typing import Any

import pymupdf  # PyMuPDF


class PdfParser:
    """Parses PDF documents, extracting pages, text layers, scan indicators, and coordinates."""

    def __init__(self, file_path_or_bytes: str | bytes | io.BytesIO):
        if isinstance(file_path_or_bytes, str):
            self.doc = pymupdf.open(file_path_or_bytes)
        elif isinstance(file_path_or_bytes, bytes):
            self.doc = pymupdf.open(stream=file_path_or_bytes, filetype="pdf")
        elif isinstance(file_path_or_bytes, io.BytesIO):
            self.doc = pymupdf.open(stream=file_path_or_bytes.getvalue(), filetype="pdf")
        else:
            # Fallback
            self.doc = pymupdf.open(file_path_or_bytes)

    @property
    def page_count(self) -> int:
        return len(self.doc)

    def is_scanned(self, min_words_threshold: int = 20) -> bool:
        """Determines if the PDF appears to be a scanned image without an embedded text layer."""
        if len(self.doc) == 0:
            return True
        total_words = 0
        pages_to_check = min(10, len(self.doc))
        for i in range(pages_to_check):
            page_text = self.doc[i].get_text()
            total_words += len(page_text.split())

        avg_words = total_words / pages_to_check
        return avg_words < min_words_threshold

    def extract_pages_data(self) -> list[dict[str, Any]]:
        """Extracts text, words, detected page numbers, and dimensions per page."""
        pages = []
        for idx in range(len(self.doc)):
            page = self.doc[idx]
            rect = page.rect  # width, height in points
            text = page.get_text()
            words = text.split()

            # Inspect header / footer lines for page numbers
            lines = [line.strip() for line in text.split("\n") if line.strip()]
            header_line = lines[0] if lines else ""
            footer_line = lines[-1] if lines else ""

            pages.append({
                "page_number": idx + 1,
                "width_pt": round(rect.width, 2),
                "height_pt": round(rect.height, 2),
                "width_cm": round(rect.width * 2.54 / 72.0, 2),
                "height_cm": round(rect.height * 2.54 / 72.0, 2),
                "text": text,
                "word_count": len(words),
                "header_line": header_line,
                "footer_line": footer_line
            })
        return pages

    def extract_all(self) -> dict[str, Any]:
        """Aggregate full PDF data."""
        pages_data = self.extract_pages_data()
        scanned = self.is_scanned()
        full_text = "\n\n".join([p["text"] for p in pages_data])
        total_words = sum([p["word_count"] for p in pages_data])

        return {
            "format": "pdf",
            "page_count": self.page_count,
            "is_scanned": scanned,
            "scan_warning": "PDF terdeteksi sebagai scan/image tanpa lapisan teks. Gunakan OCR untuk akurasi maksimal." if scanned else None,
            "pages": pages_data,
            "total_words": total_words,
            "full_text": full_text
        }
