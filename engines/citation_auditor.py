"""Citation and Reference Auditor: Cross-references in-text citations against Daftar Pustaka (APA 7)."""

from __future__ import annotations

from typing import Any

from models.document_model import ParsedDocument
from parsers.citation_parser import audit_citations


class CitationAuditor:
    """Verifies citation reciprocity and APA 7th edition formatting."""

    def __init__(self, document: ParsedDocument):
        self.doc = document
        self.text = document.get_text()

    def audit(self) -> list[dict[str, Any]]:
        findings = []

        audit_res = audit_citations(self.text)

        # 0. Check boundary reliability
        if not audit_res.segmentation.boundaries_reliable:
            findings.append({
                "rule_id": "STRUCT_SECTION_BOUNDARY_001",
                "category": "Struktur",
                "status": "ERROR",
                "field": "structure.boundaries_reliable",
                "actual": audit_res.segmentation.unreliable_reason or "Batas bagian tidak dapat ditentukan secara andal",
                "expected": "Batas bagian dokumen (Bab, Daftar Pustaka, Lampiran) terdefinisi secara teratur",
                "message": f"Struktur dokumen tidak standar: {audit_res.segmentation.unreliable_reason}",
                "recommendation": "Pastikan urutan bab, daftar pustaka, dan lampiran sesuai dengan pedoman tesis MIKOM 2026.",
                "page": None,
                "section": "Struktur Dokumen",
            })

        # 1. Check bibliography presence
        if not audit_res.segmentation.bib_present or not audit_res.references:
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
                "section": "Daftar Pustaka",
            })
            return findings

        # 2. Cross-reference 1: In-text citations missing from Bibliography (Orphans)
        if audit_res.orphaned_citations:
            unique_missing = sorted(list(set(c.raw for c in audit_res.orphaned_citations)))
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
                "section": "Sitasi & Daftar Pustaka",
            })

        # 3. Cross-reference 2: References never cited in body text (Unused)
        if audit_res.unused_references:
            unused_snippets = [r.raw[:60] for r in audit_res.unused_references]
            findings.append({
                "rule_id": "CITATION_UNUSED_REF_001",
                "category": "Sitasi",
                "status": "WARNING",
                "field": "references.unused_count",
                "actual": f"{len(unused_snippets)} rujukan tidak disitasi: {', '.join(unused_snippets[:3])}",
                "expected": "Semua rujukan disitasi dalam isi naskah",
                "message": f"Terdapat {len(unused_snippets)} entri pada Daftar Pustaka yang tidak pernah disitasi dalam badan naskah.",
                "recommendation": "Hapus rujukan yang tidak disitasi atau tambahkan sitasinya pada bab pembahasan.",
                "page": None,
                "section": "Daftar Pustaka",
            })

        return findings
