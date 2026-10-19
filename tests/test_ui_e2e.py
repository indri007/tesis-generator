"""E2E Smoke Tests for Streamlit Multi-Page UI using AppTest."""

from __future__ import annotations

import pytest
from streamlit.testing.v1 import AppTest

from engines.citation_auditor import CitationFinding
from engines.plagiarism_engine.orchestrator import PlagiarismReport


class MockFinding:
    def __init__(self, rule_id: str, severity: str, message: str, recommendation: str = ""):
        self.rule_id = rule_id
        self.severity = severity
        self.message = message
        self.description = message
        self.recommendation = recommendation


@pytest.fixture
def mock_state():
    """Provides a complete session_state fixture for multi-page AppTest rendering."""
    format_findings = [
        MockFinding("FORMAT_MARGIN_001", "WARNING", "Margin kiri 3.8 cm, seharusnya 4.0 cm", "Perbaiki margin kiri menjadi 4 cm"),
        MockFinding("FORMAT_FONT_001", "INFO", "Font Times New Roman 12 pt sesuai standar"),
    ]
    structure_findings = [
        MockFinding("STRUCT_BAB_001", "ERROR", "Bab IV Pembahasan Hasil Penelitian tidak ditemukan", "Tambahkan Bab IV lengkap"),
    ]
    citation_findings = [
        CitationFinding(
            citation_text="Smith, J. (2022). Digital Media Studies.",
            status="verified",
            severity="info",
            details={"source": "scopus", "scopus_id": "2-s2.0-85123456789"},
            evidence_ref="hal. 14",
        ),
        CitationFinding(
            citation_text="Kurniawan, B. (2021). Media Sosial di Indonesia.",
            status="metadata_mismatch",
            severity="warning",
            details={"source": "sinta", "mismatches": ["Tahun: ditulis 2021, terindeks 2020"]},
            evidence_ref="hal. 28",
        ),
        CitationFinding(
            citation_text="Tanpa Nama (2019). Artikel Anonim.",
            status="not_found",
            severity="critical",
            details={"source": "unknown", "reason": "DOI dan judul tidak ditemukan di Scopus/SINTA"},
            evidence_ref="hal. 55",
        ),
    ]
    plag_report = PlagiarismReport(
        overall_plagiarism_score=0.14,
        overall_ai_score=0.09,
        verdict="clean",
        findings=[
            {
                "checker_name": "Lexical TF-IDF Checker",
                "score": 0.12,
                "verdict": "clean",
                "matched_segments": [],
            },
            {
                "checker_name": "Semantic S-BERT Checker",
                "score": 0.14,
                "verdict": "clean",
                "matched_segments": [],
            },
            {
                "checker_name": "AI Detector (Perplexity & Burstiness)",
                "score": 0.09,
                "verdict": "clean",
                "matched_segments": [{"avg_perplexity": 68.4, "burstiness": 0.421}],
            },
        ],
    )

    return {
        "audit_metadata": {
            "filename": "Tesis_MIKOM_Final_2026.docx",
            "file_type": "DOCX",
            "page_count": 138,
            "total_words": 46200,
        },
        "doc_info": {
            "filename": "Tesis_MIKOM_Final_2026.docx",
            "file_type": "DOCX",
            "page_count": 138,
            "total_words": 46200,
        },
        "format_findings": format_findings,
        "structure_findings": structure_findings,
        "citation_findings": citation_findings,
        "plagiarism_report": plag_report,
        "document_text": "Ini adalah pengantar naskah tesis magister ilmu komunikasi UPN Veteran Jawa Timur.",
        "plagiarism_segments": [
            {
                "text": "Komunikasi massa adalah proses di mana organisasi media memproduksi pesan secara terstruktur.",
                "score": 0.45,
                "source": "McQuail (2010)",
                "location": "Bab 2, hal. 18",
                "checker": "lexical",
                "matched_text": "Komunikasi massa adalah proses di mana media memproduksi pesan.",
            },
            {
                "text": "Metodologi penelitian menggunakan pendekatan kualitatif dengan paradigma konstruktivis.",
                "score": 0.20,
                "source": "Creswell (2018)",
                "location": "Bab 3, hal. 42",
                "checker": "semantic",
            },
        ],
        "summary_counts": {
            "PASS": 52,
            "ERROR": len(structure_findings),
            "WARNING": len(format_findings),
            "UNVERIFIED": 0,
        },
        "overall_score": 89.5,
    }


def test_full_flow(mock_state):
    """Pastikan kelima halaman render tanpa error."""
    pages = [
        "app/ui/pages/2_audit_overview.py",
        "app/ui/pages/3_citation_audit.py",
        "app/ui/pages/4_plagiarism_audit.py",
        "app/ui/pages/5_report_export.py",
    ]
    for page in pages:
        at = AppTest.from_file(page)
        # Enable .update() on AppTest session_state proxy if missing
        if not hasattr(type(at.session_state), "update"):
            type(at.session_state).update = lambda self, d: [self.__setitem__(k, v) for k, v in d.items()]

        at.session_state.update(mock_state)
        at.run()
        assert not at.exception, f"Error di {page}: {at.exception}"

