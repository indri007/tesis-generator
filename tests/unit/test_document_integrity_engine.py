"""Unit tests for Academic Document Integrity Engine."""

from __future__ import annotations

from core.evaluation.document_integrity_engine import (
    AcademicIntegrityReport,
    compute_ngram_shingles,
    compute_shingle_jaccard,
    run_academic_integrity_audit,
    segment_document_sections,
    strip_direct_quotes,
)


def test_segment_document_sections():
    sample_text = (
        "JUDUL PENELITIAN TESIS\n\n"
        "BAB I PENDAHULUAN\nLatar belakang penelitian ini membahas komunikasi publik...\n\n"
        "BAB II TINJAUAN PUSTAKA\nTeori dependensi media (Ball-Rokeach & DeFleur, 1976)...\n\n"
        "DAFTAR PUSTAKA\nBall-Rokeach, S. J., & DeFleur, M. L. (1976). A dependency model.\n"
    )
    sections = segment_document_sections(sample_text)
    assert len(sections) >= 3
    section_names = [s.name for s in sections]
    assert any("BAB I" in name or "PENDAHULUAN" in name for name in section_names)
    assert any("DAFTAR PUSTAKA" in name for name in section_names)

    # Check bibliography exclusion flag
    bib_section = next(s for s in sections if "DAFTAR PUSTAKA" in s.name)
    assert bib_section.is_bibliography is True


def test_strip_direct_quotes():
    text_with_quotes = (
        'Peneliti menyatakan bahwa "komunikasi politik adalah transmisi pesan" secara tegas. '
        'Menurut pakar: “media baru mengubah relasi sosial”.'
    )
    stripped, quote_spans = strip_direct_quotes(text_with_quotes)
    assert "komunikasi politik adalah transmisi pesan" not in stripped
    assert "media baru mengubah relasi sosial" not in stripped
    assert len(quote_spans) == 2


def test_ngram_word_shingles():
    tokens = ["penelitian", "komunikasi", "publik", "efektif", "dan", "terukur"]
    shingles_3 = compute_ngram_shingles(tokens, n=3)
    assert len(shingles_3) == 4
    assert shingles_3[0] == "penelitian komunikasi publik"
    assert shingles_3[3] == "efektif dan terukur"


def test_compute_shingle_jaccard_identical_and_disjoint():
    tokens_a = ["analisis", "jaringan", "komunikasi", "kebijakan", "publik"]
    tokens_b = ["analisis", "jaringan", "komunikasi", "kebijakan", "publik"]
    tokens_c = ["teori", "strukturalisme", "fungsional", "sosiologi", "klasik"]

    # Identical
    score_id = compute_shingle_jaccard(tokens_a, tokens_b, n=2)
    assert score_id == 1.0

    # Disjoint
    score_disjoint = compute_shingle_jaccard(tokens_a, tokens_c, n=2)
    assert score_disjoint == 0.0


def test_academic_integrity_audit_reciprocity():
    doc_text = (
        "BAB I PENDAHULUAN\n"
        "Penelitian komunikasi ini mengacu pada studi terdahulu (Habermas, 1984). "
        "Di samping itu, temuan lain (Susanto, 2021) menunjukkan pergeseran paradigma.\n\n"
        "DAFTAR PUSTAKA\n"
        "Habermas, J. (1984). The Theory of Communicative Action. Beacon Press.\n"
        "Pratama, B. (2020). Analisis Media Digital. Gramedia.\n"
    )

    report = run_academic_integrity_audit(
        text_doc=doc_text,
        text_ref=None,
        exclude_bib=True,
        exclude_quotes=False,
    )

    assert isinstance(report, AcademicIntegrityReport)
    assert report.total_in_text_citations >= 1
    assert report.total_bibliography_entries >= 1

    # Check reconciliation
    orphans = [item for item in report.citations_reconciliation if item.status == "MISSING_IN_BIB"]
    unused = [item for item in report.citations_reconciliation if item.status == "UNUSED_BIB"]
    matched = [item for item in report.citations_reconciliation if item.status == "MATCHED"]

    assert any("susanto" in item.author_year.lower() for item in orphans)
    assert any("pratama" in item.author_year.lower() for item in unused)
    assert any("habermas" in item.author_year.lower() for item in matched)


def test_selective_exclusion_impact_on_similarity():
    # Two documents sharing identical bibliography but totally different body text
    doc_a = (
        "BAB I PENDAHULUAN\n"
        "Studi ini meneliti komunikasi politik di parlemen daerah Jawa Timur.\n\n"
        "DAFTAR PUSTAKA\n"
        "Alexander, J. (2010). The Civil Sphere. Oxford University Press.\n"
        "Castells, M. (2009). Communication Power. Oxford University Press.\n"
    )
    doc_b = (
        "BAB I PENDAHULUAN\n"
        "Penelitian ini menganalisis teknik komputasi awan dan optimasi throughput jaringan.\n\n"
        "DAFTAR PUSTAKA\n"
        "Alexander, J. (2010). The Civil Sphere. Oxford University Press.\n"
        "Castells, M. (2009). Communication Power. Oxford University Press.\n"
    )

    report_with_bib = run_academic_integrity_audit(
        text_doc=doc_a,
        text_ref=doc_b,
        exclude_bib=False,
    )

    report_without_bib = run_academic_integrity_audit(
        text_doc=doc_a,
        text_ref=doc_b,
        exclude_bib=True,
    )

    # When bibliography is excluded, similarity should be significantly lower (close to 0)
    assert report_without_bib.cosine_similarity < report_with_bib.cosine_similarity
