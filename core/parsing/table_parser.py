"""Parser and auditor helper for tables and figures."""

from __future__ import annotations

import re
from typing import Any


class TableFigureParser:
    """Extracts table and figure definitions and cross-references them against narrative text."""

    def __init__(self, raw_text: str):
        self.raw_text = raw_text

    def extract_tables(self) -> list[dict[str, Any]]:
        """Extract table occurrences with numbering and titles."""
        # e.g., "Tabel 4.1 Distribusi Responden" or "Tabel 4.1: Judul"
        pattern = re.compile(r"\bTabel\s+(\d+\.\d+)\b[:\s\-–]*(.*?)(?=\n|$)", re.IGNORECASE)
        tables = []
        for match in pattern.finditer(self.raw_text):
            num = match.group(1)
            title = match.group(2).strip()
            # Count how many times "Tabel X.Y" is mentioned elsewhere in the document
            mention_pattern = re.compile(rf"\bTabel\s+{re.escape(num)}\b", re.IGNORECASE)
            total_mentions = len(mention_pattern.findall(self.raw_text))

            tables.append({
                "number": num,
                "title": title or "(Tanpa Judul)",
                "raw_match": match.group(0),
                "total_mentions": total_mentions,
                "is_referenced_in_text": total_mentions > 1  # 1 for caption itself, >1 for text reference
            })
        return tables

    def extract_figures(self) -> list[dict[str, Any]]:
        """Extract figure occurrences with numbering and titles."""
        pattern = re.compile(r"\b(?:Gambar|Bagan|Diagram)\s+(\d+\.\d+)\b[:\s\-–]*(.*?)(?=\n|$)", re.IGNORECASE)
        figures = []
        for match in pattern.finditer(self.raw_text):
            num = match.group(1)
            title = match.group(2).strip()
            mention_pattern = re.compile(rf"\b(?:Gambar|Bagan|Diagram)\s+{re.escape(num)}\b", re.IGNORECASE)
            total_mentions = len(mention_pattern.findall(self.raw_text))

            figures.append({
                "number": num,
                "title": title or "(Tanpa Judul)",
                "raw_match": match.group(0),
                "total_mentions": total_mentions,
                "is_referenced_in_text": total_mentions > 1
            })
        return figures

    def check_numbering_sequence(self, items: list[dict[str, Any]], item_type: str = "Tabel") -> list[str]:
        """Detects sequence gaps, e.g. 4.1, 4.2, 4.4 (missing 4.3)."""
        by_chapter: dict[str, list[int]] = {}
        for item in items:
            parts = item["number"].split(".")
            if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
                ch = parts[0]
                idx = int(parts[1])
                by_chapter.setdefault(ch, []).append(idx)

        warnings = []
        for ch, indices in by_chapter.items():
            unique_sorted = sorted(set(indices))
            if not unique_sorted:
                continue
            for expected in range(1, max(unique_sorted) + 1):
                if expected not in unique_sorted:
                    warnings.append(f"{item_type} {ch}.{expected} tidak ditemukan dalam naskah.")
        return warnings
