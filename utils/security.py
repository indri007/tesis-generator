"""Security and temporary file management utilities."""

from __future__ import annotations

import os
import re
import shutil
import tempfile
from pathlib import Path
from typing import Any, BinaryIO

try:
    from typing import Self
except ImportError:
    from typing_extensions import Self

ALLOWED_EXTENSIONS = {".docx", ".pdf", ".txt"}
MAX_FILE_SIZE_BYTES = 200 * 1024 * 1024  # 200 MB safe limit
MAX_PAGES_LIMIT = None
WORD_MIN, WORD_MAX = 40_000, 60_000


def validate_file_extension(filename: str) -> tuple[bool, str]:
    """Validate that uploaded file is DOCX, PDF, or TXT."""
    if not filename:
        return False, "Nama file tidak valid."
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        return False, f"Format {ext} tidak didukung. Harap unggah file .docx, .pdf, atau .txt."
    return True, ext


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent directory traversal and injection."""
    if not filename:
        return "uploaded_thesis"
    # Normalize separators and extract pure basename
    name = Path(filename.replace("\\", "/")).name
    # Strip any consecutive dots (..) that could signify parent traversal
    name = re.sub(r"\.{2,}", "_", name)
    cleaned = re.sub(r"[^\w\s\.-]", "_", name).strip(". ")
    return cleaned or "uploaded_thesis"


class TempFileManager:
    """Context manager for temporary uploaded file persistence with guaranteed cleanup."""

    def __init__(self, prefix: str = "tesischeck_"):
        self.prefix = prefix
        self.temp_dir: str | None = None

    def __enter__(self) -> Self:
        self.temp_dir = tempfile.mkdtemp(prefix=self.prefix)
        return self

    def save_uploaded_stream(self, file_stream: BinaryIO, original_filename: str) -> str:
        if not self.temp_dir:
            raise RuntimeError("Temp directory not initialized.")
        safe_name = sanitize_filename(original_filename)
        dest_path = os.path.join(self.temp_dir, safe_name)
        with open(dest_path, "wb") as f:
            f.write(file_stream.read())
        # reset seek pointer if stream supports it
        if hasattr(file_stream, "seek"):
            file_stream.seek(0)
        return dest_path

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
            except Exception:
                pass
