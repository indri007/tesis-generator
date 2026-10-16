"""Reference Auditor: Verifies APA 7 formatting and DOI lookup via CrossRef API."""

from __future__ import annotations

import json
from pathlib import Path
import re
import urllib.request
from typing import Any

from models.document_model import ParsedDocument


_LOCAL_CACHE: dict[str, dict[str, Any]] | None = None


def _get_local_cache() -> dict[str, dict[str, Any]]:
    global _LOCAL_CACHE
    if _LOCAL_CACHE is not None:
        return _LOCAL_CACHE

    _LOCAL_CACHE = {}
    cache_file = Path("data/processed/clean_references.jsonl")
    if cache_file.exists():
        try:
            with cache_file.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    rec = json.loads(line)
                    doi_key = rec.get("doi")
                    if doi_key:
                        _LOCAL_CACHE[doi_key.lower()] = rec
        except Exception:
            pass
    return _LOCAL_CACHE


def verify_doi_crossref(doi: str, timeout: float = 3.0) -> dict[str, Any]:
    """Verify DOI existence against local clean cache first, then CrossRef API."""
    cleaned_doi = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", doi).strip().lower()

    # 1. Cek local offline cache terlebih dahulu
    local_cache = _get_local_cache()
    if cleaned_doi in local_cache:
        item = local_cache[cleaned_doi]
        return {
            "is_valid": True,
            "doi": cleaned_doi,
            "title": item.get("title", ""),
            "year": item.get("year"),
            "source": f"Local Cache ({item.get('source', 'Offline')})",
            "status": "PASS",
        }

    # 2. Fallback ke CrossRef REST API jika belum ada di cache
    url = f"https://api.crossref.org/works/{cleaned_doi}"
    headers = {"User-Agent": "TesisCheck-MIKOM2026/1.0 (mailto:tesischeck@upnjatim.ac.id)"}

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as response:
            if response.status == 200:
                data = json.loads(response.read().decode())
                item = data.get("message", {})
                title = item.get("title", [""])[0]
                year = item.get("created", {}).get("date-parts", [[None]])[0][0]
                return {
                    "is_valid": True,
                    "doi": cleaned_doi,
                    "title": title,
                    "year": year,
                    "source": "CrossRef API",
                    "status": "PASS",
                }
    except Exception:
        pass

    return {
        "is_valid": False,
        "doi": cleaned_doi,
        "status": "UNVERIFIED",
    }


class ReferenceAuditor:
    """Audits bibliography entries for completeness, APA 7 compliance, and DOI verification."""

    def __init__(self, document: ParsedDocument):
        self.doc = document
        self.text = document.get_text()

    def audit(self) -> list[dict[str, Any]]:
        findings = []

        # Find DAFTAR PUSTAKA
        bib_match = re.search(r"\b(?:DAFTAR\s+PUSTAKA|REFERENCES)\b(.*?)(?=\bLAMPIRAN\b|$)", self.text, re.DOTALL | re.IGNORECASE)
        if not bib_match:
            return findings

        bib_text = bib_match.group(1).strip()
        lines = [l.strip() for l in bib_text.splitlines() if len(l.strip()) > 15]

        for line in lines:
            # Check year: (2020) or (1998)
            has_year = bool(re.search(r"\((?:19|20)\d{2}[a-z]?\)", line))
            if not has_year:
                findings.append({
                    "rule_id": "REF_YEAR_MISSING_001",
                    "category": "Referensi",
                    "status": "WARNING",
                    "field": "references.format",
                    "actual": line[:60],
                    "expected": "Tahun publikasi dalam tanda kurung, misal (2022)",
                    "message": f"Entri rujukan tidak memiliki tahun publikasi yang jelas: {line[:50]}...",
                    "evidence_query": line[:40],
                    "recommendation": "Cantumkan tahun penerbitan sumber pustaka dalam tanda kurung.",
                    "source": {"title": "Pedoman MIKOM 2026 Bab IV.D", "page": 45, "verified": True}
                })

            # Check DOI if present
            doi_match = re.search(r"(?:https?://(?:dx\.)?doi\.org/|doi:)\s*(10\.\d{4,9}/[-._;()/:A-Za-z0-9]+)", line)
            if doi_match:
                doi_str = doi_match.group(1)
                # Attempt quick verification
                res = verify_doi_crossref(doi_str, timeout=1.5)
                if not res["is_valid"]:
                    findings.append({
                        "rule_id": "REF_DOI_UNVERIFIED_001",
                        "category": "Referensi",
                        "status": "UNVERIFIED",
                        "field": "references.doi",
                        "actual": f"DOI: {doi_str}",
                        "expected": "DOI aktif terdaftar pada CrossRef",
                        "message": f"DOI {doi_str} belum dapat diverifikasi secara otomatis pada database CrossRef.",
                        "evidence_query": doi_str,
                        "recommendation": "Verifikasi tautan DOI artikel jurnal pada basis data CrossRef.",
                        "source": {"title": "CrossRef Metadata Registry", "page": None, "verified": False}
                    })

        return findings
