"""Unit tests for scientific AI engines (Elicit, SciSpace, ResearchRabbit, Semantic Scholar, OpenAlex, Crossref)."""

from __future__ import annotations

from core.integrations.scientific_engines import (
    CrossrefEngine,
    ElicitEngine,
    OpenAlexEngine,
    PerplexityEngine,
    ResearchRabbitEngine,
    ScientificPaper,
    SciSpaceEngine,
    SemanticScholarEngine,
)


def test_elicit_engine_extraction():
    engine = ElicitEngine()
    text = """Penelitian ini menggunakan pendekatan kuantitatif dengan sampel sebanyak 250 mahasiswa.
Hasil penelitian menunjukkan bahwa integrasi AI secara signifikan meningkatkan kecepatan sintesis literatur."""
    res = engine.extract_study_parameters(text)
    assert res["sample_size"] == 250
    assert "quantitative" in res["study_design"].lower()
    assert "integrasi ai" in res["main_finding"].lower()


def test_scispace_engine_explanation():
    engine = SciSpaceEngine()
    abstract = "This paper explores the role of automated auditing in thesis generation. We demonstrate that rule-based systems reduce non-compliance by 94%."
    res = engine.explain_abstract(abstract)
    assert "automated auditing" in res["simplified_objective"].lower()
    assert "reduce non-compliance" in res["practical_takeaway"].lower()
    assert res["reading_time_minutes"] >= 1


def test_researchrabbit_engine_network_graph():
    engine = ResearchRabbitEngine()
    dois = ["10.1016/j.tele.2023.102045", "10.1016/j.jenvman.2022.115012", "10.1016/j.cosrev.2024.100612"]
    res = engine.build_network_graph(dois)
    assert res["seed_count"] == 3
    assert len(res["nodes"]) == 3
    assert len(res["edges"]) == 3
    assert res["network_density"] > 0


def test_semantic_scholar_engine_metrics():
    engine = SemanticScholarEngine()
    paper = ScientificPaper(
        title="Automated Thesis Auditing",
        authors=["Rahmawati, A."],
        year=2023,
        journal="Telematics and Informatics",
        doi="10.1016/j.tele.2023.102045",
        citation_count=50,
    )
    res = engine.compute_s2_metrics(paper)
    assert res["citation_count"] == 50
    assert res["influential_citation_count"] == 14
    assert res["influential_ratio"] == 0.28


def test_openalex_engine_mapping():
    engine = OpenAlexEngine()
    paper = ScientificPaper(
        title="Open Science in Machine Learning",
        authors=["Smith, J."],
        year=2022,
        journal="Nature",
        doi="10.1038/s41562-023-01654-1",
        open_access=True,
        keywords=["AI", "Open Access"],
    )
    res = engine.map_openalex_entity(paper)
    assert res["is_oa"] is True
    assert res["oa_status"] == "gold"
    assert len(res["concepts"]) == 2


def test_crossref_engine_doi_and_year_validation():
    # Valid DOIs
    assert CrossrefEngine.validate_doi("10.1016/j.tele.2023.102045") is True
    assert CrossrefEngine.validate_doi("10.1038/s41562-023-01654-1") is True
    assert CrossrefEngine.validate_doi("10.1109/TKDE.2024.3361284") is True

    # Invalid DOIs
    assert CrossrefEngine.validate_doi("invalid_doi_string") is False
    assert CrossrefEngine.validate_doi("https://example.com") is False
    assert CrossrefEngine.validate_doi(None) is False

    # 5-Year Rule (2021-2026)
    assert CrossrefEngine.verify_publication_year(2021) is True
    assert CrossrefEngine.verify_publication_year(2024) is True
    assert CrossrefEngine.verify_publication_year(2026) is True
    assert CrossrefEngine.verify_publication_year(2020) is False  # Older than 5 years
    assert CrossrefEngine.verify_publication_year(2015) is False


def test_perplexity_engine_grounded_research():
    engine = PerplexityEngine()
    res = engine.answer_query("Penerapan AI dalam jurnalisme redaksi")
    assert res["citations_count"] >= 1
    assert res["has_inline_citations"] is True
    assert "[1]" in res["answer"]
    assert res["sources"][0]["url"].startswith("http")
    assert res["provenance"] == "perplexity_grounded_engine"

