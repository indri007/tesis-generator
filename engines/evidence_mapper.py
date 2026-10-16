"""Evidence mapper linking rule findings with parsed document excerpts and locations."""

from __future__ import annotations

import re
import unicodedata
from typing import Any


def normalize_text(value: str) -> str:
    """Normalisasi teks untuk pencarian kutipan."""
    value = unicodedata.normalize("NFKC", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def find_evidence_locations(
    document,
    query: str,
    max_results: int = 5,
) -> list[dict[str, Any]]:
    """Cari kutipan pada paragraf hasil parsing.
    Nomor halaman hanya dicantumkan jika parser menyediakannya.
    """
    if not query or not query.strip():
        return []

    needle = normalize_text(query).casefold()
    results = []

    for index, paragraph in enumerate(document.paragraphs):
        text = normalize_text(paragraph.text)

        if needle in text.casefold():
            results.append({
                "page": paragraph.page,
                "section": paragraph.section,
                "paragraph_index": index,
                "excerpt": text[:1200],
                "match_type": "exact_normalized",
            })

            if len(results) >= max_results:
                break

    return results


def map_finding_to_evidence(
    finding: Any,
    document,
) -> dict:
    """Memetakan temuan ke bukti dokumen.

    evidence_query harus berisi teks yang memang diharapkan
    ditemukan dalam dokumen, bukan nilai aktual hasil audit.
    """
    if not isinstance(finding, dict):
        return {
            "rule_id": "GENERIC_FINDING",
            "finding_status": "INFO",
            "page": None,
            "section": None,
            "excerpt": str(finding),
            "mapping_status": "UNVERIFIED",
            "source": {},
        }

    query = finding.get("evidence_query", "")
    locations = find_evidence_locations(document, query)

    source = finding.get("source") or {}
    has_document_location = bool(locations)

    if has_document_location:
        primary = locations[0]
        page = primary["page"]
        section = primary["section"]
        excerpt = primary["excerpt"]
        mapping_status = (
            "MAPPED" if page is not None else "PARTIAL"
        )
    else:
        page = None
        section = None
        excerpt = None
        mapping_status = "UNVERIFIED"

    return {
        "rule_id": finding.get("rule_id", finding.get("id", "")),
        "finding_status": finding["status"],
        "category": finding["category"],
        "description": finding.get("description", ""),
        "actual": finding.get("actual"),
        "expected": finding.get("expected"),
        "page": page,
        "section": section,
        "excerpt": excerpt,
        "all_locations": locations,
        "mapping_status": mapping_status,
        "evidence_verified": (
            mapping_status == "MAPPED"
            and bool(excerpt)
        ),
        "source_title": source.get("title") or source.get("document"),
        "source_page": source.get("page"),
        "source_verified": source.get("verified", False),
        "recommendation": finding.get("recommendation", ""),
    }
