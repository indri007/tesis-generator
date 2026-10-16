"""Unit tests for Academic Services, Public APIs & Plagiarism Disclaimer."""

import os

from core.integrations.academic_services import (
    CrossrefService,
    InternalSimilarityAuditor,
    OpenAlexService,
    ProprietaryAIAdapters,
    SemanticScholarService,
    configure_local_tracking,
    init_observability,
    verify_all_academic_connections,
)


def test_crossref_doi_format_validation():
    valid = CrossrefService.get_work("10.1016/j.tele.2023.102045", live=False)
    assert valid["status"] == "offline_validated"
    assert valid["is_valid_syntax"] is True

    invalid = CrossrefService.get_work("invalid-non-doi-string", live=False)
    assert invalid["status"] == "invalid_doi"
    assert invalid["is_valid_syntax"] is False


def test_openalex_offline_fallback():
    res = OpenAlexService.get_work_by_doi("10.1016/j.tele.2023.102045", live=False)
    assert res["status"] == "offline_fixture"
    assert len(res["concepts"]) > 0


def test_semantic_scholar_offline_fallback():
    res = SemanticScholarService.get_paper("10.1016/j.tele.2023.102045", live=False)
    assert res["status"] == "offline_fixture"
    assert "Informasi ringkas" in res["tldr"]


def test_local_tracking_configuration():
    status = configure_local_tracking()
    assert "sqlite:" in status["mlflow"]
    assert "offline" in status["wandb"]
    assert os.environ.get("WANDB_MODE") == "offline"


def test_observability_defaults_off():
    obs = init_observability(enable_sentry=False, enable_logfire=False)
    assert "disabled" in obs["sentry"]
    assert "disabled" in obs["logfire"]


def test_proprietary_ai_adapters():
    matrix = ProprietaryAIAdapters.get_service_matrix()
    services = {m["service"] for m in matrix}
    assert {"Consensus", "Perplexity", "Elicit", "SciSpace", "ResearchRabbit"}.issubset(services)


def test_internal_similarity_heuristic_and_disclaimer():
    doc1 = "Penerapan kecerdasan buatan pada industri media di Indonesia terbukti menggandakan kecepatan kurasi berita."
    doc2 = "Penerapan kecerdasan buatan pada industri media di Indonesia terbukti meningkatkan akurasi kurasi berita."

    audit = InternalSimilarityAuditor.calculate_ngram_overlap(doc1, doc2, n=3)
    assert audit.metric_label == "heuristik internal (n-gram overlap)"
    assert audit.is_turnitin_equivalent is False
    assert "BUKAN 'setara Turnitin'" in audit.disclaimer
    assert "kampus Anda" in audit.disclaimer
    assert audit.score_percentage > 0.0
    assert len(audit.official_campus_checklist) >= 3


def test_verify_all_academic_connections():
    summary = verify_all_academic_connections()
    assert "tier1_tracking" in summary
    assert "tier3_public_apis" in summary
    assert "tier5_originality_policy" in summary
