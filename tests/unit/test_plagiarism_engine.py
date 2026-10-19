"""Unit tests for engines.plagiarism_engine and core.integrations.mcp_client."""

import pytest
from engines.plagiarism_engine.base_checker import BaseChecker, CheckResult
from engines.plagiarism_engine.preprocessing import (
    normalize_text,
    preprocess_indonesian,
    split_into_sentences,
)
from engines.plagiarism_engine.lexical_checker import LexicalChecker
from engines.plagiarism_engine.semantic_checker import SemanticChecker
from engines.plagiarism_engine.ai_detector import AIDetector
from engines.plagiarism_engine.source_repository import SourceRepository
from engines.plagiarism_engine.orchestrator import PlagiarismOrchestrator, PlagiarismReport
from engines.plagiarism_engine.online_checker import OnlineAcademicChecker
from auditors.plagiarism_finding import PlagiarismFinding, AIGenerationFinding
from core.integrations.mcp_client import MCPClientWrapper


def test_preprocessing_indonesian():
    raw = "Peneliti sedang Mempelajari Komunikasi Organisasi di Era Digital!!!"
    norm = normalize_text(raw)
    assert "!" not in norm
    assert norm.islower()

    preprocessed = preprocess_indonesian(raw)
    assert len(preprocessed) > 0

    sentences = split_into_sentences("Kalimat pertama. Kalimat kedua! Kalimat ketiga?")
    assert len(sentences) == 3


def test_lexical_checker():
    corpus = [
        "Komunikasi massa adalah proses di mana organisasi media memproduksi pesan.",
        "Metode kualitatif berfokus pada eksplorasi fenomena sosial secara mendalam.",
    ]
    checker = LexicalChecker(corpus)

    # Identical or near identical sentence
    res = checker.check("Komunikasi massa adalah proses di mana organisasi media memproduksi pesan.")
    assert isinstance(res, CheckResult)
    assert res.score >= 0.70
    assert res.verdict in ["plagiarized", "suspicious"]
    assert len(res.matched_segments) >= 1

    # Disjoint sentence
    clean_res = checker.check("Kriptografi kuantum memanfaatkan superposisi foton fisika.")
    assert clean_res.score < 0.50
    assert clean_res.verdict == "clean"


def test_semantic_checker_graceful_fallback():
    corpus = ["Kredibilitas komunikator menentukan efektivitas persuasi publik."]
    checker = SemanticChecker(corpus)
    res = checker.check("Kredibilitas seorang komunikator sangat mempengaruhi keberhasilan pesan.")
    assert isinstance(res, CheckResult)
    assert res.verdict in ["clean", "plagiarized", "suspicious"]


def test_ai_detector():
    detector = AIDetector()
    # Short text < 3 sentences
    res_short = detector.check("Hanya satu kalimat saja.")
    assert res_short.score == 0.0
    assert res_short.verdict == "clean"

    # Multi-sentence sample text
    text = (
        "Komunikasi digital berkembang sangat pesat dalam satu dekade terakhir. "
        "Hal ini mempengaruhi pola interaksi antarwarga di berbagai platform media sosial. "
        "Oleh karena itu penting dilakukan penelitian mendalam mengenai fenomena tersebut."
    )
    res = detector.check(text)
    assert isinstance(res, CheckResult)
    assert 0.0 <= res.score <= 1.0


def test_source_repository():
    repo = SourceRepository()
    initial_count = len(repo.get_all())
    assert initial_count > 0

    repo.add_document("Teks referensi baru tentang teori komunikasi.")
    assert len(repo.get_all()) == initial_count + 1


def test_plagiarism_orchestrator():
    corpus = [
        "Komunikasi massa memproduksi dan menyebarkan informasi kepada khalayak.",
    ]
    orchestrator = PlagiarismOrchestrator(reference_corpus=corpus)
    report = orchestrator.run("Komunikasi massa memproduksi dan menyebarkan informasi kepada khalayak secara luas.")

    assert isinstance(report, PlagiarismReport)
    assert 0.0 <= report.overall_plagiarism_score <= 1.0
    assert 0.0 <= report.overall_ai_score <= 1.0
    assert report.verdict in ["clean", "suspicious", "rejected"]
    assert len(report.findings) == 3


def test_online_academic_checker():
    checker = OnlineAcademicChecker(enable_live_api=False)
    res = checker.check("Berdasarkan riset terdahulu (DOI: 10.1016/j.tele.2023.102045) temuan terkonfirmasi.")
    assert isinstance(res, CheckResult)
    assert len(res.evidence_refs) >= 1


def test_plagiarism_findings():
    pf = PlagiarismFinding(
        rule_id="MIKOM-PLAG-01",
        rule_name="Uji Plagiarisme",
        category="plagiarism",
        severity="ERROR",
        message="Kemiripan tinggi",
        location="Bab 2",
        evidence="Kutipan mirip",
        expected="< 25%",
        actual="85%",
        recommendation="Parafrase",
        similarity_score=0.85,
    )
    assert pf.priority == "PRIORITAS 1"

    aif = AIGenerationFinding(
        rule_id="MIKOM-AI-01",
        rule_name="Uji AI Content",
        category="ai_generated",
        severity="ERROR",
        message="Indikasi AI",
        location="Bab 1",
        evidence="Burstiness seragam",
        expected="Orisinal",
        actual="78%",
        recommendation="Variasikan kalimat",
        ai_probability=0.78,
    )
    assert aif.priority == "PRIORITAS 1"


def test_mcp_client_wrapper():
    wrapper = MCPClientWrapper()
    # Test SINTA lookup
    sinta_res = wrapper.search_sinta("Jurnal Komunikasi Indonesia")
    assert sinta_res is not None
    assert sinta_res.sinta_score == "S1"

    # Test comprehensive reputation check
    audit_rep = wrapper.audit_reference_reputation(
        title="Digital Journalism in Indonesia",
        journal="Jurnal Komunikasi Indonesia",
    )
    assert audit_rep["meets_mikom_standard"] is True
    assert audit_rep["sinta"] is not None
    assert audit_rep["sinta"]["sinta_score"] == "S1"
    assert audit_rep["reputation_badge"] in ["SINTA S1", "Scopus Q1"]
