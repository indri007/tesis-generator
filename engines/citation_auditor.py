"""Citation and Reference Auditor: Cross-references in-text citations against Daftar Pustaka (APA 7)."""

from __future__ import annotations

import re
from typing import Any

from models.document_model import ParsedDocument


class CitationAuditor:
    """Verifies citation reciprocity and APA 7th edition formatting."""

    def __init__(self, document: ParsedDocument):
        self.doc = document
        self.text = document.get_text()

    def audit(self) -> list[dict[str, Any]]:
        findings = []

        # 1. Extract in-text citations: (Author, Year) or Author (Year)
        in_text_pattern = re.compile(
            r"(?:\((?P<cit_paren>[A-Z][a-zA-Z\s\-–]+(?:,\s*(?:19|20)\d{2}|[a-zA-Z\s]+,\s*(?:19|20)\d{2}))\)|(?P<cit_narrative>[A-Z][a-zA-Z\-–]+(?:\s+[A-Z][a-zA-Z\-–]+){0,2})\s*\((?P<cit_year>(?:19|20)\d{2})\))"
        )
        citations = []
        for match in in_text_pattern.finditer(self.text):
            cit = match.group("cit_paren") or f"{match.group('cit_narrative')}, {match.group('cit_year')}"
            author = cit.split(",")[0].strip()
            # Clean author
            author_clean = re.sub(r"\b(dkk\.|et\s+al\.|dan|and)\b", "", author, flags=re.IGNORECASE).strip()
            first_name = author_clean.split()[0] if author_clean.split() else author_clean
            citations.append({
                "raw": cit,
                "author": author,
                "key": first_name.lower()
            })

        # 2. Extract bibliography entries
        bib_match = re.search(r"\b(?:DAFTAR\s+PUSTAKA|REFERENCES)\b(.*?)(?=\bLAMPIRAN\b|$)", self.text, re.DOTALL | re.IGNORECASE)
        bib_lines = []
        bib_text = ""
        if bib_match:
            bib_text = bib_match.group(1).strip()
            bib_lines = [l.strip() for l in bib_text.splitlines() if len(l.strip()) > 15]

        if not bib_lines:
            findings.append({
                "rule_id": "STRUCT_BIB_PRESENCE_001",
                "category": "Sitasi",
                "status": "ERROR",
                "field": "bibliography.exists",
                "actual": "Daftar Pustaka tidak ditemukan",
                "expected": "Memuat Daftar Pustaka lengkap",
                "message": "Bagian Daftar Pustaka tidak ditemukan pada naskah tesis.",
                "recommendation": "Tambahkan Daftar Pustaka dengan format APA 7th edition.",
                "page": None,
                "section": "Daftar Pustaka"
            })
            return findings

        # Cross-reference 1: In-text citations missing from Bibliography
        bib_lower = bib_text.lower()
        missing_in_bib = []
        for cit in citations:
            if cit["key"] and len(cit["key"]) > 2 and cit["key"] not in bib_lower:
                missing_in_bib.append(cit["raw"])

        if missing_in_bib:
            unique_missing = list(set(missing_in_bib))
            findings.append({
                "rule_id": "CITATION_ORPHAN_001",
                "category": "Sitasi",
                "status": "ERROR",
                "field": "citations.orphaned_count",
                "actual": f"{len(unique_missing)} sitasi tanpa rujukan: {', '.join(unique_missing[:3])}",
                "expected": "Semua sitasi memiliki rujukan di Daftar Pustaka",
                "message": f"Ditemukan {len(unique_missing)} sitasi teks yang tidak memiliki entri pada Daftar Pustaka.",
                "recommendation": "Lengkapi entri Daftar Pustaka untuk setiap sitasi di atas.",
                "page": None,
                "section": "Sitasi & Daftar Pustaka"
            })

        # Cross-reference 2: References never cited in body text
        body_before_bib = self.text[:self.text.lower().find("daftar pustaka")] if "daftar pustaka" in self.text.lower() else self.text
        body_lower = body_before_bib.lower()
        unused_refs = []
        for line in bib_lines:
            words = line.split()
            if words and len(words[0]) > 2:
                author_key = words[0].strip(".,;:()").lower()
                if author_key not in body_lower:
                    unused_refs.append(line[:60])

        if unused_refs:
            findings.append({
                "rule_id": "CITATION_UNUSED_REF_001",
                "category": "Sitasi",
                "status": "WARNING",
                "field": "references.unused_count",
                "actual": f"{len(unused_refs)} rujukan tidak disitasi",
                "expected": "Semua rujukan disitasi dalam isi naskah",
                "message": f"Terdapat {len(unused_refs)} entri pada Daftar Pustaka yang tidak pernah disitasi dalam badan naskah.",
                "recommendation": "Hapus rujukan yang tidak disitasi atau tambahkan sitasinya pada bab pembahasan.",
                "page": None,
                "section": "Daftar Pustaka"
            })

        return findings
