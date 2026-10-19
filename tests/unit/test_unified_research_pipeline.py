"""Unit and Integration Tests for Unified Research Pipeline (Rayyan, PICO, Consensus).

Validates:
- Gate 2: Rayyan CSV and RIS import, exact/candidate deduplication, non-destructive audit trail.
- Gate 3: PICO extraction with source quote verification, support for empty components, zero hallucination.
- Gate 4: Consensus CSV export parsing, provenance tracking, and authenticated API fallback.
- Gate 5: Unified QA orchestration, separation of duplicate vs plagiarism findings, CitationAuditor parity.
"""

from core.integrations.consensus_importer import (
    ConsensusClient,
    parse_consensus_csv,
)
from core.integrations.pico_extractor import extract_pico_from_text
from core.integrations.rayyan_importer import (
    deduplicate_records,
    parse_rayyan_csv,
    parse_rayyan_ris,
)
from core.integrations.unified_research_pipeline import UnifiedResearchPipeline
from models.document_model import ParsedDocument, ParsedParagraph

# ==============================================================================
# GATE 2: RAYYAN TESTS
# ==============================================================================

def test_rayyan_csv_import_and_exact_doi_deduplication():
    csv_content = """key,title,authors,year,journal,doi,abstract,rayyan_labels
RAYYAN-1,Digital Transformation in Media,Smith J; Jones M,2022,Oxford Press,10.1016/j.media.2022.01,Abstract text here,Included
RAYYAN-2,Digital Transformation in Media (Online First),Smith J; Jones M,2022,Oxford Press,10.1016/j.media.2022.01,Abstract text here,Maybe
RAYYAN-3,Social Media Engagement Strategies,Kurniawan B,2021,Media Nusantara,10.1016/j.socmed.2021.05,Unique abstract,Excluded
"""
    records = parse_rayyan_csv(csv_content)
    assert len(records) == 3
    assert records[0].doi == "10.1016/j.media.2022.01"
    assert records[0].inclusion_status == "Included"

    deduped = deduplicate_records(records)
    # Total records MUST remain 3 (non-destructive!)
    assert len(deduped) == 3

    # RAYYAN-2 has same DOI as RAYYAN-1 -> EXACT_DUPLICATE
    assert deduped[1].duplicate_status == "EXACT_DUPLICATE"
    assert deduped[1].duplicate_of_id == "RAYYAN-1"
    assert deduped[1].similarity_score == 1.0

    # RAYYAN-3 has different DOI and title -> UNIQUE
    assert deduped[2].duplicate_status == "UNIQUE"


def test_rayyan_candidate_duplicate_detection():
    csv_content = """key,title,authors,year,journal,doi
R-10,Effect of Artificial Intelligence on Journalistic Writing: A Multi-Case Study,Rahmawati A,2023,Journal of Communication,
R-11,Effect of Artificial Intelligence on Journalistic Writing: A Multi Case Study,Rahmawati A,2023,Journal of Communication,
R-12,Strategic Marketing in Digital Communication Age,Rahmawati A,2023,Media Studies,
"""
    records = parse_rayyan_csv(csv_content)
    deduped = deduplicate_records(records)

    # R-11 is a candidate duplicate of R-10 (high title token similarity without DOI)
    assert deduped[1].duplicate_status in ("EXACT_DUPLICATE", "CANDIDATE_DUPLICATE")
    assert deduped[1].duplicate_of_id == "R-10"

    # R-12 is distinct despite having the same author and year
    assert deduped[2].duplicate_status == "UNIQUE"


def test_rayyan_ris_format_import():
    ris_content = """TY  - JOUR
ID  - RIS-001
TI  - Structural Anthropology in Modern Communication
AU  - Levi-Strauss, C.
PY  - 2020
DO  - 10.1080/01234567.2020.01
ER  -

TY  - JOUR
ID  - RIS-002
TI  - Digital Foundations
AU  - Smith, J.
PY  - 2020
ER  -
"""
    records = parse_rayyan_ris(ris_content)
    assert len(records) == 2
    assert records[0].original_id == "RIS-001"
    assert records[0].authors == ["Levi-Strauss, C."]
    assert records[0].doi == "10.1080/01234567.2020.01"
    assert records[0].provenance == "rayyan_ris"


# ==============================================================================
# GATE 3: PICO EXTRACTION TESTS
# ==============================================================================

def test_pico_positive_extraction_with_exact_grounding():
    text = (
        "Penelitian ini menganalisis pengaruh kualitas sistem terhadap kepuasan pengguna "
        "dibandingkan dengan metode konvensional pada mahasiswa Universitas Airlangga."
    )
    pico = extract_pico_from_text(text)

    # All components should be present
    assert pico.is_complete is True

    # Population
    assert pico.population.is_present is True
    assert "mahasiswa" in pico.population.value.lower()
    assert pico.population.source_quote in text

    # Intervention
    assert pico.intervention.is_present is True
    assert "kualitas sistem" in pico.intervention.value.lower()
    assert pico.intervention.source_quote in text

    # Comparison
    assert pico.comparison.is_present is True
    assert "metode konvensional" in pico.comparison.value.lower()
    assert pico.comparison.source_quote in text

    # Outcome
    assert pico.outcome.is_present is True
    assert "kepuasan pengguna" in pico.outcome.value.lower()
    assert pico.outcome.source_quote in text


def test_pico_negative_extraction_zero_hallucination():
    text = "Bab ini membahas latar belakang sejarah perkembangan kota Surabaya pada abad kesembilan belas."
    pico = extract_pico_from_text(text)

    # No clinical/empirical PICO elements exist in this text
    assert pico.population.is_present is False
    assert pico.population.value is None
    assert pico.intervention.is_present is False
    assert pico.intervention.value is None
    assert pico.comparison.is_present is False
    assert pico.comparison.value is None
    assert pico.outcome.is_present is False
    assert pico.outcome.value is None
    assert pico.is_complete is False


def test_pico_observational_study_missing_comparison():
    text = "Bagaimana pengaruh terpaan media sosial terhadap tingkat kecemasan audiens pada pengguna aktif di Jakarta?"
    pico = extract_pico_from_text(text)

    # Population, Intervention, Outcome present; Comparison is correctly None
    assert pico.population.is_present is True
    assert pico.intervention.is_present is True
    assert pico.outcome.is_present is True
    assert pico.comparison.is_present is False
    assert pico.comparison.value is None
    assert pico.is_complete is False


# ==============================================================================
# GATE 4: CONSENSUS INTEGRATION TESTS
# ==============================================================================

def test_consensus_csv_import_and_provenance():
    consensus_csv = """query,title,authors,year,journal,doi,consensus_meter,summary_claim,citations
Does social media enhance brand engagement?,Social Media and Brand Loyalty,Smith J; Davis R,2022,Journal of Marketing,10.1016/j.brand.2022.04,Yes,Active social media communication significantly boosts consumer retention.,45
Does social media enhance brand engagement?,Limits of Social Media Campaigns,Kurniawan B,2021,Communication Review,10.1080/comm.2021.09,No,Organic social campaigns showed negligible direct impact on sales.,12
Does social media enhance brand engagement?,Cross-Platform Influence Studies,Miller K,2020,Media Insights,10.1007/media.2020.11,Possibly,Impact varies widely across demographics and platform format.,8
"""
    result = parse_consensus_csv(consensus_csv)

    assert result.total_results == 3
    assert result.api_status == "OFFLINE_IMPORT"
    assert len(result.papers) == 3

    p0 = result.papers[0]
    assert p0.paper_title == "Social Media and Brand Loyalty"
    assert p0.consensus_meter == "Yes"
    assert p0.doi == "10.1016/j.brand.2022.04"
    assert p0.citation_count == 45
    assert p0.provenance == "consensus_csv"

    # Consensus summary verification
    assert "1 of 3 studies (33%) support the claim" in result.consensus_summary


def test_consensus_unauthenticated_api_fallback():
    # Client initialized without key must not attempt web scraping
    client = ConsensusClient(api_key=None)
    assert client.is_api_available() is False

    res = client.search_or_import("Does media quality improve retention?")
    assert res.api_status == "UNAUTHENTICATED_SKIPPED"
    assert res.total_results == 0
    assert "Unauthenticated scraping is disallowed" in res.consensus_summary


# ==============================================================================
# GATE 5: UNIFIED RESEARCH PIPELINE TESTS
# ==============================================================================

def test_unified_research_pipeline_orchestration():
    text = """BAB I PENDAHULUAN
1.1 Latar Belakang Masalah
Penelitian ini bertujuan untuk menguji pengaruh kualitas konten terhadap loyalitas audiens pada mahasiswa Surabaya.

BAB II TINJAUAN PUSTAKA
Smith (2022) mengemukakan pentingnya infrastruktur digital.
Penelitian lain juga mendukung hal ini (Jones, 2021).

DAFTAR PUSTAKA
Jones, M. (2021). Digital Media Dynamics. Oxford Press.
Smith, J. (2022). Digital Communication and Media Technologies. Academic Press.
"""
    doc = ParsedDocument(filename="thesis_unified.docx", file_type="docx")
    doc.paragraphs = [ParsedParagraph(text=line) for line in text.splitlines()]

    rayyan_csv = """key,title,authors,year,doi
R-1,Digital Communication and Media Technologies,Smith J,2022,10.1016/j.digital.2022
R-2,Digital Communication and Media Technologies,Smith J,2022,10.1016/j.digital.2022
"""
    consensus_csv = """query,title,authors,year,consensus_meter,summary_claim
Does content quality improve loyalty?,Content Quality and Audience Retention,Smith J,2022,Yes,High quality content drives engagement.
"""

    pipeline = UnifiedResearchPipeline(doc)
    report = pipeline.audit(rayyan_content=rayyan_csv, consensus_content=consensus_csv)

    # 1. PICO Verified
    assert report.pico["intervention"]["is_present"] is True
    assert "kualitas konten" in report.pico["intervention"]["value"].lower()
    assert report.pico["outcome"]["is_present"] is True
    assert "loyalitas audiens" in report.pico["outcome"]["value"].lower()

    # 2. Rayyan Deduplication Verified
    assert report.rayyan_summary["total_records"] == 2
    assert report.rayyan_summary["exact_duplicates"] == 1
    assert report.rayyan_summary["unique_records"] == 1

    # 3. Consensus Summary Verified
    assert report.consensus_summary["total_results"] == 1
    assert report.consensus_summary["papers"][0]["consensus_meter"] == "Yes"

    # 4. Citation Parity Verified
    orphan_findings = [f for f in report.citation_findings if f["rule_id"] == "CITATION_ORPHAN_001"]
    assert len(orphan_findings) == 0

    # 5. Rule input parity
    assert report.rule_input["citations"]["orphaned_count"] == 0
    assert report.rule_input["citations"]["count"] == 2

    # 6. Gate Status Boolean
    assert report.gate_status["pico_verified"] is True
    assert report.gate_status["rayyan_dedup_completed"] is True
    assert report.gate_status["consensus_verified"] is True
    assert report.gate_status["citations_passed"] is True


def test_unified_research_pipeline_with_elsevier_scopus():
    """Verify UnifiedResearchPipeline seamlessly includes Elsevier Scopus/ScienceDirect imports."""
    text = """BAB I PENDAHULUAN
Penelitian ini bertujuan untuk menguji pengaruh otomasi AI terhadap jurnalisme digital.
Smith (2022) mengkaji kerangka komunikasi.

DAFTAR PUSTAKA
Smith, J. (2022). Environmental Communication. Academic Press.
"""
    doc = ParsedDocument(filename="thesis_test.docx", file_type="docx")
    doc.paragraphs = [ParsedParagraph(text=line) for line in text.splitlines()]

    scopus_csv = """Authors,Title,Year,Source title,Cited by,DOI
"Santoso B.","Artificial Intelligence in Journalism",2023,"Telematics and Informatics",48,10.1016/j.tele.2023.102045
"""
    pipeline = UnifiedResearchPipeline(doc)
    report = pipeline.audit(elsevier_content=scopus_csv, elsevier_format="csv")

    assert report.elsevier_summary["total_results"] == 1
    assert report.elsevier_summary["q1_count"] == 1
    assert report.elsevier_summary["articles"][0]["doi"] == "10.1016/j.tele.2023.102045"
    assert report.gate_status["elsevier_verified"] is True

