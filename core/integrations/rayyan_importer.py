"""Rayyan Reference Import and Deduplication Module.

Supports official Rayyan export formats (CSV and RIS).
Preserves provenance and original identifiers.
Implements non-destructive multi-level deduplication (Exact, Candidate, Unique).
"""

from __future__ import annotations

import csv
import io
import re
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class RayyanRecord:
    original_id: str
    title: str
    normalized_title: str
    authors: list[str]
    year: str | None
    journal: str = ""
    doi: str | None = None
    abstract: str = ""
    labels: list[str] = field(default_factory=list)
    inclusion_status: str = "Unscreened"
    provenance: str = "rayyan_csv"
    duplicate_status: str = "UNIQUE"  # UNIQUE | EXACT_DUPLICATE | CANDIDATE_DUPLICATE
    duplicate_of_id: str | None = None
    similarity_score: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def normalize_title(title: str) -> str:
    """Normalizes a title for robust comparison."""
    if not title:
        return ""
    # Lowercase, replace hyphens and punctuation with spaces, collapse spaces
    cleaned = re.sub(r"[^\w\s]", " ", title.lower())
    return " ".join(cleaned.split())


def normalize_doi(doi: str | None) -> str | None:
    """Normalizes DOI by stripping URI schemes and lowercasing."""
    if not doi:
        return None
    d = doi.strip().lower()
    d = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", d)
    d = re.sub(r"^doi:\s*", "", d)
    d = d.strip(" /")
    return d if d else None


def compute_token_similarity(text_a: str, text_b: str) -> float:
    """Computes Jaccard word token similarity between two normalized strings."""
    tokens_a = set(text_a.split())
    tokens_b = set(text_b.split())
    if not tokens_a or not tokens_b:
        return 0.0
    intersection = tokens_a.intersection(tokens_b)
    union = tokens_a.union(tokens_b)
    return len(intersection) / len(union)


def parse_rayyan_csv(content: str) -> list[RayyanRecord]:
    """Parses official Rayyan CSV export content."""
    records: list[RayyanRecord] = []
    reader = csv.DictReader(io.StringIO(content.strip()))

    for idx, row in enumerate(reader):
        # Case-insensitive field lookup
        row_lower = {k.strip().lower(): v.strip() for k, v in row.items() if k}

        original_id = (
            row_lower.get("key")
            or row_lower.get("rayyan_key")
            or row_lower.get("id")
            or f"RAYYAN-ROW-{idx + 1}"
        )
        title = row_lower.get("title", "")
        norm_title = normalize_title(title)

        authors_raw = row_lower.get("authors") or row_lower.get("author", "")
        authors = [a.strip() for a in re.split(r"[,;]|\band\b", authors_raw) if a.strip()]

        year_raw = row_lower.get("year", "")
        year_match = re.search(r"\b((?:19|20)\d{2})\b", year_raw)
        year = year_match.group(1) if year_match else None

        doi = normalize_doi(row_lower.get("doi"))
        journal = row_lower.get("journal") or row_lower.get("publication_title", "")
        abstract = row_lower.get("abstract", "")

        labels_raw = row_lower.get("rayyan_labels") or row_lower.get("labels", "")
        labels = [l.strip() for l in labels_raw.split(";") if l.strip()]

        status = "Unscreened"
        if "included" in labels_raw.lower() or "included" in row_lower.get("decisions", "").lower():
            status = "Included"
        elif "excluded" in labels_raw.lower() or "excluded" in row_lower.get("decisions", "").lower():
            status = "Excluded"
        elif "maybe" in labels_raw.lower():
            status = "Maybe"

        records.append(
            RayyanRecord(
                original_id=original_id,
                title=title,
                normalized_title=norm_title,
                authors=authors,
                year=year,
                journal=journal,
                doi=doi,
                abstract=abstract,
                labels=labels,
                inclusion_status=status,
                provenance="rayyan_csv",
            )
        )

    return records


def parse_rayyan_ris(content: str) -> list[RayyanRecord]:
    """Parses standard RIS reference format exported by Rayyan."""
    records: list[RayyanRecord] = []
    entries = content.strip().split("ER  -")

    for idx, entry in enumerate(entries):
        lines = [l.strip() for l in entry.strip().splitlines() if l.strip()]
        if not lines:
            continue

        fields: dict[str, list[str]] = {}
        for line in lines:
            if len(line) >= 6 and line[2:6] == "  - ":
                tag = line[:2].upper()
                val = line[6:].strip()
                fields.setdefault(tag, []).append(val)

        title = " ".join(fields.get("TI", []) or fields.get("T1", []) or fields.get("CT", []))
        if not title:
            continue

        authors = fields.get("AU", []) or fields.get("A1", [])
        year_raw = " ".join(fields.get("PY", []) or fields.get("Y1", []))
        year_match = re.search(r"\b((?:19|20)\d{2})\b", year_raw)
        year = year_match.group(1) if year_match else None

        doi_raw = " ".join(fields.get("DO", []))
        doi = normalize_doi(doi_raw)

        journal = " ".join(fields.get("JO", []) or fields.get("JF", []))
        abstract = " ".join(fields.get("AB", []) or fields.get("N2", []))
        orig_id = " ".join(fields.get("ID", [])) or f"RIS-REC-{idx + 1}"

        records.append(
            RayyanRecord(
                original_id=orig_id,
                title=title,
                normalized_title=normalize_title(title),
                authors=authors,
                year=year,
                journal=journal,
                doi=doi,
                abstract=abstract,
                provenance="rayyan_ris",
            )
        )

    return records


def deduplicate_records(records: list[RayyanRecord]) -> list[RayyanRecord]:
    """Performs multi-level non-destructive deduplication on reference records.

    Marks records as EXACT_DUPLICATE, CANDIDATE_DUPLICATE, or UNIQUE without deleting records.
    """
    n = len(records)
    for i in range(n):
        if records[i].duplicate_status == "EXACT_DUPLICATE":
            continue

        for j in range(i + 1, n):
            if records[j].duplicate_status == "EXACT_DUPLICATE":
                continue

            rec_a = records[i]
            rec_b = records[j]

            # 1. Exact DOI match
            if rec_a.doi and rec_b.doi and rec_a.doi == rec_b.doi:
                records[j].duplicate_status = "EXACT_DUPLICATE"
                records[j].duplicate_of_id = rec_a.original_id
                records[j].similarity_score = 1.0
                continue

            # 2. Exact Title and Year match
            if (
                rec_a.normalized_title
                and rec_a.normalized_title == rec_b.normalized_title
                and rec_a.year
                and rec_a.year == rec_b.year
            ):
                records[j].duplicate_status = "EXACT_DUPLICATE"
                records[j].duplicate_of_id = rec_a.original_id
                records[j].similarity_score = 1.0
                continue

            # 3. High Title Similarity (Candidate Duplicate)
            if rec_a.normalized_title and rec_b.normalized_title:
                sim = compute_token_similarity(rec_a.normalized_title, rec_b.normalized_title)
                if sim >= 0.85:
                    records[j].duplicate_status = "CANDIDATE_DUPLICATE"
                    records[j].duplicate_of_id = rec_a.original_id
                    records[j].similarity_score = round(sim, 3)
                    continue

                # 4. Same first author surname + same year + moderate title similarity (>= 0.70)
                first_author_a = rec_a.authors[0].split()[0].lower() if rec_a.authors else ""
                first_author_b = rec_b.authors[0].split()[0].lower() if rec_b.authors else ""
                if (
                    first_author_a
                    and first_author_a == first_author_b
                    and rec_a.year
                    and rec_a.year == rec_b.year
                    and sim >= 0.70
                ):
                    records[j].duplicate_status = "CANDIDATE_DUPLICATE"
                    records[j].duplicate_of_id = rec_a.original_id
                    records[j].similarity_score = round(sim, 3)

    return records
