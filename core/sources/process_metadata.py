"""Metadata Processing and Literature Aggregation Pipeline.

Provides backward-compatible utilities while delegating to CoreDataEngine.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from core.sources.core_data_engine import CoreDataEngine
from core.sources.doi_verifier import normalize_doi
from core.sources.text_processor import clean_abstract

__all__ = [
    "clean_html_tags",
    "extract_year",
    "format_author_list",
    "normalize_doi",
    "process_all_raw_metadata",
]

RAW_DIR = Path("data/raw")
PROCESSED_FILE = Path("data/processed/clean_references.jsonl")


def clean_html_tags(text: str) -> str:
    """Hapus tag HTML seperti <i>, <b>, dll."""
    return clean_abstract(text)


def format_author_list(raw_authors: list[Any]) -> list[str]:
    """Format daftar nama pengarang ke standar 'Belakang, Depan'."""
    formatted: list[str] = []
    for author in raw_authors:
        if isinstance(author, dict):
            family = author.get("family", "") or author.get("last_name", "")
            given = author.get("given", "") or author.get("first_name", "")
            if family and given:
                formatted.append(f"{family}, {given}")
            elif family:
                formatted.append(family)
            elif author.get("name"):
                formatted.append(str(author["name"]))
        elif isinstance(author, str) and author.strip():
            formatted.append(author.strip())
    return formatted


def extract_year(published: Any) -> int | None:
    """Ekstraksi tahun terbit dari berbagai format metadata."""
    if not published:
        return None
    if isinstance(published, int):
        return published if 1900 <= published <= 2030 else None
    if isinstance(published, dict):
        date_parts = published.get("date-parts")
        if date_parts and isinstance(date_parts, list) and len(date_parts) > 0:
            first_part = date_parts[0]
            if isinstance(first_part, list) and len(first_part) > 0:
                try:
                    yr = int(first_part[0])
                    if 1900 <= yr <= 2030:
                        return yr
                except (ValueError, TypeError):
                    pass
    if isinstance(published, str):
        match = re.search(r"\b(19\d\d|20\d\d)\b", published)
        if match:
            return int(match.group(1))
    return None


def process_all_raw_metadata() -> dict[str, int]:
    """Processes all raw JSONL files in RAW_DIR through CoreDataEngine."""
    PROCESSED_FILE.parent.mkdir(parents=True, exist_ok=True)
    raw_files = list(RAW_DIR.glob("*.jsonl"))
    if not raw_files:
        print(f"Tidak ada file .jsonl di {RAW_DIR}")
        return {"total_raw": 0, "unique_saved": 0}

    raw_items: list[dict[str, Any]] = []
    for fpath in raw_files:
        print(f"Memproses file: {fpath}")
        with fpath.open("r", encoding="utf-8") as in_f:
            for line in in_f:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                    raw_items.append(record)
                except json.JSONDecodeError:
                    continue

    engine = CoreDataEngine()
    manifest = engine.run_pipeline(raw_items, source_database="RawDirectoryIngest", output_dir=PROCESSED_FILE.parent)

    # Maintain clean_references.jsonl compatibility
    master_jsonl = PROCESSED_FILE.parent / "master_canonical_references.jsonl"
    if master_jsonl.exists():
        with open(master_jsonl, "r", encoding="utf-8") as src, open(PROCESSED_FILE, "w", encoding="utf-8") as dst:
            dst.write(src.read())

    print("\n=== RINGKASAN PEMROSESAN METADATA (PHASE 1 CORE ENGINE) ===")
    print(f"Total entri mentah dibaca : {manifest['input_records_count']}")
    print(f"Total unik tersimpan      : {manifest['unique_canonical_count']}")
    print(f"Included records          : {manifest['included_count']}")
    print(f"Excluded records          : {manifest['excluded_count']}")
    print(f"File output               : {PROCESSED_FILE}")
    print(f"Master canonical CSV      : {manifest['output_files']['master_csv']['path']}")

    return {
        "total_raw": manifest["input_records_count"],
        "unique_saved": manifest["unique_canonical_count"],
    }


if __name__ == "__main__":
    process_all_raw_metadata()
