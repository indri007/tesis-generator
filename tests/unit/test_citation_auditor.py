"""Unit tests for CitationAuditor and citation extraction edge cases (APA 7)."""

import pytest
from models.document_model import ParsedDocument, ParsedParagraph
from engines.citation_auditor import CitationAuditor
from engines.audit_engine import audit_thesis


def make_doc_from_text(text: str) -> ParsedDocument:
    doc = ParsedDocument(filename="test_thesis.docx", file_type="docx")
    doc.paragraphs = [ParsedParagraph(text=line) for line in text.splitlines()]
    return doc


def test_standard_citations_matched_in_bib():
    text = """BAB II TINJAUAN PUSTAKA
Smith (2022) mengemukakan pentingnya infrastruktur digital.
Penelitian lain juga mendukung hal tersebut (Jones, 2021).

DAFTAR PUSTAKA
Jones, M. (2021). Digital Transformation in Media. Oxford Press.
Smith, J. (2022). Digital Communication and Media Technologies. Academic Press.
"""
    doc = make_doc_from_text(text)
    auditor = CitationAuditor(doc)
    findings = auditor.audit()

    orphan_findings = [f for f in findings if f["rule_id"] == "CITATION_ORPHAN_001"]
    unused_findings = [f for f in findings if f["rule_id"] == "CITATION_UNUSED_REF_001"]

    assert len(orphan_findings) == 0
    assert len(unused_findings) == 0


def test_narrative_discourse_markers_and_multiline_protection():
    text = """BAB II TINJAUAN PUSTAKA
Menurut Rahmawati (2023) komunikasi digital memperkuat loyalitas audiens.
Berdasarkan Kurniawan (2021) media sosial meningkatkan partisipasi.
Kajian Levi-Strauss (2020) mengenai struktur kultural.

DAFTAR PUSTAKA
Kurniawan, B. (2021). Media Sosial dan Partisipasi Publik. Pustaka Ilmu.
Levi-Strauss, C. (2020). Structural Anthropology Revisited. Cambridge Press.
Rahmawati, A. (2023). Strategic Marketing in Communication Age. Media Nusantara.
"""
    doc = make_doc_from_text(text)
    auditor = CitationAuditor(doc)
    findings = auditor.audit()

    orphan_findings = [f for f in findings if f["rule_id"] == "CITATION_ORPHAN_001"]
    assert len(orphan_findings) == 0, f"Unexpected orphans: {orphan_findings}"

    # Also verify ParsedDocument.to_rule_input parity
    rule_input = doc.to_rule_input()
    assert rule_input["citations"]["orphaned_count"] == 0


def test_year_suffixes_2020a_2020b():
    text = """BAB II TINJAUAN PUSTAKA
Hal ini dibahas pada karya awal (Smith, 2020a) dan diperluas kemudian oleh Smith (2020b).

DAFTAR PUSTAKA
Smith, J. (2020a). Foundations of Cyber Communication. Sage.
Smith, J. (2020b). Advanced Topics in Cyber Communication. Sage.
"""
    doc = make_doc_from_text(text)
    auditor = CitationAuditor(doc)
    findings = auditor.audit()

    orphan_findings = [f for f in findings if f["rule_id"] == "CITATION_ORPHAN_001"]
    assert len(orphan_findings) == 0


def test_et_al_and_dkk_in_citations():
    text = """BAB II TINJAUAN PUSTAKA
Banyak peneliti sependapat dengan temuan ini (Smith et al., 2021).
Menurut Rahmawati dkk. (2022) kolaborasi antardisiplin sangat krusial.
Temuan serupa juga diungkapkan oleh Williams et al. (2020).

DAFTAR PUSTAKA
Rahmawati, A., Santoso, B., & Wibowo, C. (2022). Kolaborasi Komunikasi. UI Press.
Smith, J., Jones, M., & Brown, K. (2021). Collective Intelligence. MIT Press.
Williams, R., Davis, T., & Clark, H. (2020). Modern Media Networks. Routledge.
"""
    doc = make_doc_from_text(text)
    auditor = CitationAuditor(doc)
    findings = auditor.audit()

    orphan_findings = [f for f in findings if f["rule_id"] == "CITATION_ORPHAN_001"]
    assert len(orphan_findings) == 0


def test_multiple_citations_in_single_parenthesis():
    text = """BAB II TINJAUAN PUSTAKA
Beberapa studi telah mengkaji fenomena ini (Smith, 2020; Jones, 2021; Williams et al., 2022).

DAFTAR PUSTAKA
Jones, M. (2021). Digital Media Dynamics. Oxford Press.
Smith, J. (2020). Internet Cultures. Academic Press.
Williams, R., Davis, T., & Clark, H. (2022). Social Networking Studies. Routledge.
"""
    doc = make_doc_from_text(text)
    auditor = CitationAuditor(doc)
    findings = auditor.audit()

    orphan_findings = [f for f in findings if f["rule_id"] == "CITATION_ORPHAN_001"]
    assert len(orphan_findings) == 0


def test_orphaned_citation_detected():
    text = """BAB II TINJAUAN PUSTAKA
Kajian oleh Johnson (2023) belum terdaftar dalam referensi.

DAFTAR PUSTAKA
Smith, J. (2022). Digital Communication and Media Technologies. Academic Press.
"""
    doc = make_doc_from_text(text)
    auditor = CitationAuditor(doc)
    findings = auditor.audit()

    orphan_findings = [f for f in findings if f["rule_id"] == "CITATION_ORPHAN_001"]
    assert len(orphan_findings) == 1
    assert orphan_findings[0]["status"] == "ERROR"
    assert "Johnson" in orphan_findings[0]["actual"]

    rule_input = doc.to_rule_input()
    assert rule_input["citations"]["orphaned_count"] == 1


def test_unused_reference_detected():
    text = """BAB II TINJAUAN PUSTAKA
Smith (2022) mengemukakan pentingnya infrastruktur digital.

DAFTAR PUSTAKA
Kurniawan, B. (2021). Media Sosial dan Partisipasi Publik. Pustaka Ilmu.
Smith, J. (2022). Digital Communication and Media Technologies. Academic Press.
"""
    doc = make_doc_from_text(text)
    auditor = CitationAuditor(doc)
    findings = auditor.audit()

    unused_findings = [f for f in findings if f["rule_id"] == "CITATION_UNUSED_REF_001"]
    assert len(unused_findings) == 1
    assert unused_findings[0]["status"] == "WARNING"

    rule_input = doc.to_rule_input()
    assert rule_input["references"]["unused_count"] == 1


def test_heading_variations_references_and_appendices():
    text = """BAB II TINJAUAN PUSTAKA
Kajian Smith (2022) mengemukakan data empiris.

REFERENCES
Kurniawan, B. (2021). Media Sosial dan Partisipasi Publik. Pustaka Ilmu.
Smith, J. (2022). Digital Communication and Media Technologies. Academic Press.

LAMPIRAN
Kurniawan di sini adalah data survei lampiran, bukan sitasi teks.
"""
    doc = make_doc_from_text(text)
    auditor = CitationAuditor(doc)
    findings = auditor.audit()

    # Kurniawan is unused because it only appears in LAMPIRAN, not body text
    unused_findings = [f for f in findings if f["rule_id"] == "CITATION_UNUSED_REF_001"]
    assert len(unused_findings) == 1


def test_missing_bibliography_section():
    text = """BAB I PENDAHULUAN
Latar belakang penelitian tanpa daftar pustaka.
"""
    doc = make_doc_from_text(text)
    auditor = CitationAuditor(doc)
    findings = auditor.audit()

    assert any(f["rule_id"] == "STRUCT_BIB_PRESENCE_001" and f["status"] == "ERROR" for f in findings)


def test_multiple_citations_are_not_silently_ignored():
    text = """BAB II TINJAUAN PUSTAKA
Beberapa studi membahas fenomena ini
(Smith, 2020; Jones, 2021; Williams et al., 2022).

DAFTAR PUSTAKA
Jones, M. (2021). Digital Media Dynamics. Oxford Press.
Smith, J. (2020). Internet Cultures. Academic Press.
Williams, R., Davis, T., & Clark, H. (2022). Social Networking Studies. Routledge.
"""
    doc = make_doc_from_text(text)
    findings = CitationAuditor(doc).audit()

    orphan_findings = [
        f for f in findings
        if f["rule_id"] == "CITATION_ORPHAN_001"
    ]

    assert not orphan_findings, (
        "Sitasi majemuk yang memiliki referensi tidak boleh dianggap yatim."
    )

    rule_input = doc.to_rule_input()
    assert rule_input["citations"]["orphaned_count"] == 0
    assert rule_input["citations"]["count"] == 3
    assert rule_input["references"]["count"] == 3
    assert rule_input["references"]["unused_count"] == 0


def test_assertion_hardening_detailed_metadata():
    """Gate 2: Verifies explicit author, year, count, and match status."""
    text = """BAB II TINJAUAN PUSTAKA
Kajian oleh Rahmawati (2023) dan (Smith, 2020a).

DAFTAR PUSTAKA
Rahmawati, A. (2023). Strategic Marketing. Media Nusantara.
Smith, J. (2020a). Digital Foundations. Sage.
"""
    doc = make_doc_from_text(text)
    rule_input = doc.to_rule_input()

    # Exact count assertions
    assert rule_input["citations"]["count"] == 2
    assert rule_input["citations"]["orphaned_count"] == 0
    assert rule_input["references"]["count"] == 2
    assert rule_input["references"]["unused_count"] == 0
    assert rule_input["bibliography"]["exists"] is True

    # Detailed author and year assertions
    citations = rule_input["citations"]["list"]
    authors = {c["author"] for c in citations}
    years = {c["year"] for c in citations}
    keys = {c["key"] for c in citations}

    assert "Rahmawati" in authors
    assert "Smith" in authors
    assert "2023" in years
    assert "2020a" in years
    assert "rahmawati" in keys
    assert "smith" in keys


def test_extraction_consistency_rule_input_vs_citation_auditor():
    """Gate 3: Ensures CitationAuditor and ParsedDocument.to_rule_input() are 100% consistent."""
    text = """BAB II TINJAUAN PUSTAKA
Penelitian Smith (2022) mengkaji komunikasi media.
Studi lain oleh (Jones, 2021) mendukung hal ini.
Namun temuan Brown (2024) belum ada rujukan.

DAFTAR PUSTAKA
Jones, M. (2021). Digital Media Dynamics. Oxford Press.
Smith, J. (2022). Digital Communication and Media Technologies. Academic Press.
Kurniawan, B. (2021). Media Sosial dan Partisipasi Publik. Pustaka Ilmu.
"""
    doc = make_doc_from_text(text)
    auditor = CitationAuditor(doc)
    findings = auditor.audit()
    rule_input = doc.to_rule_input()

    # Parity check on counts
    expected_orphaned = 1  # Brown (2024) is missing in bib
    expected_unused = 1    # Kurniawan (2021) is never cited in body
    expected_body_citations = 3

    assert rule_input["citations"]["count"] == expected_body_citations
    assert rule_input["citations"]["orphaned_count"] == expected_orphaned
    assert rule_input["references"]["unused_count"] == expected_unused

    orphan_findings = [f for f in findings if f["rule_id"] == "CITATION_ORPHAN_001"]
    unused_findings = [f for f in findings if f["rule_id"] == "CITATION_UNUSED_REF_001"]

    assert len(orphan_findings) == 1
    assert "Brown" in orphan_findings[0]["actual"]
    assert len(unused_findings) == 1
    assert "Kurniawan" in unused_findings[0]["actual"]


def test_negative_matching_same_surname_different_initials():
    """Gate 4: Rejects matching when author initials differ (A. Smith vs Smith, B.)."""
    text = """BAB II TINJAUAN PUSTAKA
Menurut (A. Smith, 2020) model komunikasi berubah secara eksponensial.

DAFTAR PUSTAKA
Smith, B. (2020). Communication Theories in Modern Age. Oxford Press.
"""
    doc = make_doc_from_text(text)
    findings = CitationAuditor(doc).audit()

    orphan_findings = [f for f in findings if f["rule_id"] == "CITATION_ORPHAN_001"]
    unused_findings = [f for f in findings if f["rule_id"] == "CITATION_UNUSED_REF_001"]

    # (A. Smith, 2020) should NOT match Smith, B. (2020)
    assert len(orphan_findings) == 1, "A. Smith harus dianggap orphan karena bib memuat Smith, B."
    assert len(unused_findings) == 1, "Smith, B. harus dianggap unused karena body mengutip A. Smith"


def test_negative_matching_substring_collision():
    """Gate 4: Rejects substring matching (Lee in Bleeker)."""
    text = """BAB II TINJAUAN PUSTAKA
Kajian awal diungkapkan oleh (Lee, 2020).

DAFTAR PUSTAKA
Bleeker, T. (2020). Modern Media Networks and Societies. Routledge.
"""
    doc = make_doc_from_text(text)
    findings = CitationAuditor(doc).audit()

    orphan_findings = [f for f in findings if f["rule_id"] == "CITATION_ORPHAN_001"]
    unused_findings = [f for f in findings if f["rule_id"] == "CITATION_UNUSED_REF_001"]

    # 'Lee' is substring of 'Bleeker', must NOT match
    assert len(orphan_findings) == 1, "'Lee' tidak boleh dicocokkan dengan 'Bleeker'"
    assert len(unused_findings) == 1, "'Bleeker' harus tetap berstatus unused"


def test_negative_matching_author_in_title_of_another_work():
    """Gate 4: Rejects author appearing inside the title of another reference."""
    text = """BAB II TINJAUAN PUSTAKA
Teori linguistik generatif dirumuskan oleh (Chomsky, 2020).

DAFTAR PUSTAKA
Miller, K. (2020). A critical analysis of Chomsky's syntax. MIT Press.
"""
    doc = make_doc_from_text(text)
    findings = CitationAuditor(doc).audit()

    orphan_findings = [f for f in findings if f["rule_id"] == "CITATION_ORPHAN_001"]
    unused_findings = [f for f in findings if f["rule_id"] == "CITATION_UNUSED_REF_001"]

    # Chomsky is in Miller's title, NOT author section!
    assert len(orphan_findings) == 1, "Chomsky dalam judul Miller tidak boleh dianggap rujukan penulis"
    assert len(unused_findings) == 1, "Miller (2020) harus tetap berstatus unused"


def test_negative_matching_different_publication_year():
    """Gate 4: Rejects matching when years do not match."""
    text = """BAB II TINJAUAN PUSTAKA
Studi longitudinal oleh Smith (2022) menunjukkan tren positif.

DAFTAR PUSTAKA
Smith, J. (2019). Foundations of Cyber Communication. Sage.
"""
    doc = make_doc_from_text(text)
    findings = CitationAuditor(doc).audit()

    orphan_findings = [f for f in findings if f["rule_id"] == "CITATION_ORPHAN_001"]
    unused_findings = [f for f in findings if f["rule_id"] == "CITATION_UNUSED_REF_001"]

    # Year 2022 != 2019
    assert len(orphan_findings) == 1, "Smith (2022) tidak boleh dicocokkan dengan Smith (2019)"
    assert len(unused_findings) == 1, "Smith (2019) harus tetap berstatus unused"


def test_appendix_isolation_citation_in_appendix_not_counted_in_body():
    """Gate 5: Citations in LAMPIRAN/APPENDIX are isolated and do not count toward body citations."""
    text = """BAB II TINJAUAN PUSTAKA
Penelitian Smith (2022) menguji hipotesis pokok.

DAFTAR PUSTAKA
Smith, J. (2022). Digital Communication and Media Technologies. Academic Press.

LAMPIRAN 1
Tabel Kuesioner dan instrumen survei berdasarkan (Taylor, 2021).
"""
    doc = make_doc_from_text(text)
    auditor = CitationAuditor(doc)
    findings = auditor.audit()
    rule_input = doc.to_rule_input()

    # Main body only has 1 citation (Smith), Taylor in appendix is NOT counted in body
    assert rule_input["citations"]["count"] == 1
    # Taylor is not in bib, but since it is in appendix, it must NOT trigger body orphan error
    assert rule_input["citations"]["orphaned_count"] == 0
    orphan_findings = [f for f in findings if f["rule_id"] == "CITATION_ORPHAN_001"]
    assert len(orphan_findings) == 0


def test_appendix_isolation_reference_only_in_appendix_remains_unused():
    """Gate 5: A reference cited only in appendix is considered UNUSED in the main body."""
    text = """BAB II TINJAUAN PUSTAKA
Penelitian Smith (2022) menguji hipotesis pokok.

DAFTAR PUSTAKA
Smith, J. (2022). Digital Communication and Media Technologies. Academic Press.
Taylor, S. (2021). Survey Instruments in Communication Research. Wiley.

APPENDIX A
Panduan koding survei mengacu pada (Taylor, 2021).
"""
    doc = make_doc_from_text(text)
    auditor = CitationAuditor(doc)
    findings = auditor.audit()
    rule_input = doc.to_rule_input()

    # Taylor is cited only in APPENDIX, so in the main body it is UNUSED
    unused_findings = [f for f in findings if f["rule_id"] == "CITATION_UNUSED_REF_001"]
    assert len(unused_findings) == 1
    assert "Taylor" in unused_findings[0]["actual"]
    assert rule_input["references"]["unused_count"] == 1


def test_appendix_isolation_inverted_structure_reported_as_fail():
    """Gate 5: If section boundaries cannot be reliably determined (e.g. Lampiran before Bib), report FAIL."""
    text = """BAB II TINJAUAN PUSTAKA
Penelitian Smith (2022) menguji hipotesis.

LAMPIRAN 1
Data mentah instrumen penelitian.

DAFTAR PUSTAKA
Smith, J. (2022). Digital Communication. Academic Press.
"""
    doc = make_doc_from_text(text)
    auditor = CitationAuditor(doc)
    findings = auditor.audit()

    boundary_findings = [f for f in findings if f["rule_id"] == "STRUCT_SECTION_BOUNDARY_001"]
    assert len(boundary_findings) == 1
    assert boundary_findings[0]["status"] == "ERROR"
