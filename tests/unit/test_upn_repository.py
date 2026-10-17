"""Unit tests for UPN Repository (EPrints comm/2026) submission compliance engine."""

import pytest
from engines.upn_repository_engine import UPNRepositoryEngine


def test_upn_repository_file_manifest():
    engine = UPNRepositoryEngine()
    manifest = engine.generate_file_manifest("22081010045")
    assert len(manifest) == 10
    filenames = [f.target_filename for f in manifest]
    assert "22081010045-cover.pdf" in filenames
    assert "22081010045-pengesahan.pdf" in filenames
    assert "22081010045.-bab1.pdf" in filenames
    assert "22081010045.-bab2.pdf" in filenames
    assert "22081010045.-bab3.pdf" in filenames
    assert "22081010045.-bab4.pdf" in filenames
    assert "22081010045.-bab5.pdf" in filenames
    assert "22081010045.-daftarpustaka.pdf" in filenames
    assert "22081010045.-lampiran.pdf" in filenames
    assert "22081010045-artikel.pdf" in filenames


def test_upn_repository_audit_pass():
    engine = UPNRepositoryEngine()
    doc_structure = {
        "title": "Analisis Resepsi Komunikasi Digital MBG",
        "chapters": {
            "BAB I": {"word_count": 7000},
            "BAB II": {"word_count": 12000},
            "BAB III": {"word_count": 7500},
            "BAB IV": {"word_count": 18000},
            "BAB V": {"word_count": 5000},
        },
        "has_abstract_id": True,
        "has_abstract_en": True,
    }
    report = engine.audit_submission_readiness(
        document_structure=doc_structure,
        npm="22081010045",
        author_name="Indri Kartika",
        author_email="indri@upnjatim.ac.id",
        similarity_percent=12.4,
    )
    assert report.is_ready_for_submission is True
    assert report.similarity_status == "LULUS AMBANG BATAS (<20%)"
    assert report.compliance_score == 100.0
    assert report.division == "comm"
    assert report.year == 2026
    assert len(report.file_manifest) == 10
    assert report.metadata_payload["eprint_division"] == "comm"


def test_upn_repository_audit_similarity_exceeded():
    engine = UPNRepositoryEngine()
    doc_structure = {"chapters": {"BAB I": {}, "BAB II": {}, "BAB III": {}, "BAB IV": {}, "BAB V": {}}}
    report = engine.audit_submission_readiness(
        document_structure=doc_structure,
        npm="22081010045",
        author_name="Indri Kartika",
        author_email="indri@upnjatim.ac.id",
        similarity_percent=24.5,
    )
    assert report.is_ready_for_submission is False
    assert "MELEBIHI AMBANG BATAS" in report.similarity_status
    assert len(report.recommendations) > 0
