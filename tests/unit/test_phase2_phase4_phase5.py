"""Unit Tests for Phase 2 (Scopus & Retraction), Phase 4 (PRISMA 2020), and Phase 5 (ThisIsEconomy Bridge).

Tests:
- Scopus Journal Verifier: Q1/Q2/Q3/Q4 verification, ISSN normalization, UNVERIFIED preservation rule.
- Retraction Integrity Auditor: Retraction check, reasons, dates, clean records.
- ThisIsEconomy Bridge: 8-dimension thesis alignment, component coverage, baseline metrics.
- PRISMA 2020 Flow Calculator: Mathematical balance verification, error detection, Mermaid diagram generation.
"""

from __future__ import annotations

from core.evaluation.prisma_flow_calculator import (
    PRISMAFlowCalculator,
    PRISMAFlowCounts,
)
from core.integrations.thisiseconomy_bridge import ThisIsEconomyBridge
from core.sources.retraction_integrity import (
    IntegrityStatus,
    RetractionIntegrityAuditor,
)
from core.sources.scopus_journal_verifier import (
    ScopusJournalVerifier,
    normalize_issn,
)


class TestScopusJournalVerifier:
    def test_normalize_issn(self):
        assert normalize_issn("0021-9916") == "0021-9916"
        assert normalize_issn("00219916") == "0021-9916"
        assert normalize_issn("1369118x") == "1369-118X"
        assert normalize_issn("invalid") is None

    def test_verify_known_q1_journal(self):
        verifier = ScopusJournalVerifier()
        # Telematics and Informatics
        res = verifier.verify_journal("Telematics and Informatics")
        assert res["is_scopus_indexed"] is True
        assert res["quartile"] == "Q1"
        assert res["quartile_year"] == 2024
        assert res["sjr"] > 1.0
        assert "Scimago" in res["quartile_source"]

    def test_verify_by_issn(self):
        verifier = ScopusJournalVerifier()
        # New Media & Society electronic ISSN
        res = verifier.verify_journal(journal_name="Unknown", issn="1461-7315")
        assert res["is_scopus_indexed"] is True
        assert res["quartile"] == "Q1"
        assert res["verified_source_title"] == "New Media & Society"

    def test_unverified_preservation_rule(self):
        verifier = ScopusJournalVerifier()
        # Random non-indexed journal
        res = verifier.verify_journal("Blog Komunikasi Mahasiswa Lepas")
        assert res["is_scopus_indexed"] is False
        assert res["quartile"] == "UNVERIFIED"
        assert res["scopus_status"] == "UNVERIFIED"
        assert res["is_candidate_only"] is True
        assert "PERINGATAN INTEGRITAS" in res["integrity_disclaimer"]


class TestRetractionIntegrity:
    def test_clean_doi(self):
        auditor = RetractionIntegrityAuditor()
        res = auditor.check_integrity("10.1016/j.tele.2023.102045")
        assert res["integrity_status"] == IntegrityStatus.CLEAN.value
        assert res["is_retracted"] is False
        assert res["is_compromised"] is False

    def test_retracted_doi_detection(self):
        auditor = RetractionIntegrityAuditor()
        res = auditor.check_integrity("10.1016/j.fake.2021.001")
        assert res["integrity_status"] == IntegrityStatus.RETRACTED.value
        assert res["is_retracted"] is True
        assert res["is_compromised"] is True
        assert "Fabricated" in res["retraction_reason"] or "fabricated" in res["retraction_reason"]
        assert res["retraction_date"] == "2022-04-15"

    def test_audit_reference_list(self):
        auditor = RetractionIntegrityAuditor()
        records = [
            {"record_id": "r1", "doi": "10.1016/j.tele.2023.102045", "title": "Clean Paper"},
            {"record_id": "r2", "doi": "10.1016/j.fake.2021.001", "title": "Retracted Paper"},
        ]
        audit = auditor.audit_reference_list(records)
        assert audit["total_audited"] == 2
        assert audit["clean_count"] == 1
        assert audit["retracted_count"] == 1
        assert audit["integrity_gate_passed"] is False


class TestThisIsEconomyBridge:
    def test_baseline_metrics_loading(self):
        bridge = ThisIsEconomyBridge()
        baseline = bridge.baseline
        assert baseline.total_nodes > 0
        assert baseline.indobert_accuracy >= 0.70
        assert "neutral" in baseline.indobert_emotions
        assert baseline.sarcasm_instances_analyzed > 0

    def test_evaluate_paper_alignment(self):
        bridge = ThisIsEconomyBridge()
        title = "Analisis Jaringan Komunikasi Kebijakan MBG dengan IndoBERT dan Deteksi Sarkasme"
        abstract = "Menggunakan social network analysis (SNA) dan betweenness centrality untuk memetakan disinformasi di Telegram."

        res = bridge.evaluate_paper_alignment(title, abstract, "paper_001")
        assert res.alignment_score >= 50.0
        assert "SNA" in res.matched_dimensions
        assert "INDOBERT" in res.matched_dimensions
        assert "SARCASM" in res.matched_dimensions
        assert "MBG_POLICY" in res.matched_dimensions
        assert res.relevance_level in ["HIGHLY_ALIGNED", "MODERATELY_ALIGNED"]

    def test_audit_corpus_alignment(self):
        bridge = ThisIsEconomyBridge()
        records = [
            {
                "title": "Marketing 6.0 and Phygital public relations in government communication",
                "abstract": "Human-centric public communication.",
            },
            {
                "title": "Telegram Bot Detection using Deep Learning Transformers",
                "abstract": "Detecting automated messaging channels and bots.",
            },
        ]
        corpus_audit = bridge.audit_corpus_alignment(records)
        assert corpus_audit["total_papers_audited"] == 2
        assert "D7_MARKETING_6_0" in bridge.THESIS_DIMENSIONS
        assert "MARKETING_6_0" in corpus_audit["dimension_coverage"]


class TestPRISMAFlowCalculator:
    def test_mathematical_consistency_valid(self):
        # 1000 raw -> 800 unique (200 dup)
        # 800 screened -> 300 excluded (500 sought)
        # 500 sought -> 20 not retrieved (480 assessed)
        # 480 assessed -> 80 excluded (400 included)
        counts = PRISMAFlowCounts(
            total_identified=1000,
            duplicates_removed=200,
            total_screened=800,
            records_excluded_screening=300,
            reports_sought_for_retrieval=500,
            reports_not_retrieved=20,
            reports_assessed_for_eligibility=480,
            reports_excluded_eligibility=80,
            total_included=400,
        )
        res = counts.validate_mathematical_consistency()
        assert res["is_valid"] is True
        assert len(res["errors"]) == 0

    def test_mathematical_consistency_invalid_detected(self):
        counts = PRISMAFlowCounts(
            total_identified=1000,
            duplicates_removed=200,
            total_screened=750,  # 1000 - 200 = 800 != 750 (Mismatch!)
        )
        res = counts.validate_mathematical_consistency()
        assert res["is_valid"] is False
        assert len(res["errors"]) > 0

    def test_calculate_from_pipeline_and_mermaid(self):
        counts = PRISMAFlowCalculator.calculate_from_pipeline(
            total_raw=500,
            unique_canonical=400,
        )
        assert counts.total_identified == 500
        assert counts.duplicates_removed == 100
        assert counts.total_screened == 400
        assert counts.total_included > 0

        # Generate Mermaid diagram
        mermaid = PRISMAFlowCalculator.generate_mermaid_diagram(counts)
        assert "```mermaid" in mermaid
        assert "flowchart TD" in mermaid
        assert "IDENTIFICATION" in mermaid
        assert "SCREENING" in mermaid
        assert "ELIGIBILITY" in mermaid
        assert "INCLUDED" in mermaid
