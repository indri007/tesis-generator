"""Unit tests for DocxAutoFixer engine in accordance with MIKOM 2026 guidelines."""

from pathlib import Path
from docx import Document
from docx.shared import Cm, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from engines.revision_engine import DocxAutoFixer


def test_docx_auto_fixer_applies_mikom_2026_formatting(tmp_path: Path):
    # 1. Create a dummy docx with default/wrong formatting
    in_file = tmp_path / "thesis_draft_wrong_format.docx"
    doc = Document()
    p1 = doc.add_paragraph("Ini adalah contoh paragraf pertama dengan format bawaan.")
    p2 = doc.add_paragraph("Ini adalah contoh paragraf kedua yang perlu dirapikan.")
    doc.save(str(in_file))

    orig_bytes = in_file.read_bytes()

    # 2. Apply DocxAutoFixer
    out_file = tmp_path / "thesis_draft_mikom_fixed.docx"
    fixer = DocxAutoFixer(str(in_file))
    log = fixer.fix_all(str(out_file))

    # 3. Assert non-destructive source file integrity
    assert in_file.read_bytes() == orig_bytes, "Source file must not be modified!"

    # 4. Assert output file exists and is valid
    assert out_file.exists()
    assert len(log) >= 2

    # 5. Inspect modified document properties
    fixed_doc = Document(str(out_file))
    for section in fixed_doc.sections:
        assert round(section.top_margin.cm, 1) == 4.0
        assert round(section.left_margin.cm, 1) == 4.0
        assert round(section.bottom_margin.cm, 1) == 3.0
        assert round(section.right_margin.cm, 1) == 3.0

    for p in fixed_doc.paragraphs:
        assert p.alignment == WD_ALIGN_PARAGRAPH.JUSTIFY
        assert p.paragraph_format.line_spacing == 2.0
        for r in p.runs:
            assert r.font.name == "Times New Roman"
            assert r.font.size == Pt(12)


def test_docx_auto_fixer_preserves_headings_and_tables(tmp_path: Path):
    """Verify that headings keep their alignment and tables are formatted safely."""
    in_file = tmp_path / "thesis_with_table.docx"
    doc = Document()
    h = doc.add_paragraph("BAB I PENDAHULUAN")
    h.alignment = WD_ALIGN_PARAGRAPH.CENTER

    tbl = doc.add_table(rows=2, cols=2)
    tbl.cell(0, 0).text = "Variabel"
    tbl.cell(0, 1).text = "Indikator"
    doc.save(str(in_file))

    out_file = tmp_path / "thesis_table_fixed.docx"
    fixer = DocxAutoFixer(str(in_file))
    log = fixer.fix_all(str(out_file))

    assert out_file.exists()
    actions = [item["action"] for item in log]
    assert "SET_MARGINS_4_4_3_3_CM" in actions
    assert "SET_FONT_AND_SPACING" in actions
    assert "FORMAT_TABLE_CELLS" in actions

    fixed_doc = Document(str(out_file))
    # Heading kept center alignment
    assert fixed_doc.paragraphs[0].alignment == WD_ALIGN_PARAGRAPH.CENTER


def test_docx_auto_fixer_error_handling(tmp_path: Path):
    """Verify proper exceptions on missing file or corrupt file."""
    import pytest

    # Non-existent file
    with pytest.raises(FileNotFoundError):
        DocxAutoFixer(str(tmp_path / "does_not_exist.docx"))

    # Corrupt file
    corrupt_file = tmp_path / "corrupt.docx"
    corrupt_file.write_bytes(b"Corrupt binary data that is not a zip or docx")
    fixer = DocxAutoFixer(str(corrupt_file))
    with pytest.raises(ValueError, match="rusak atau tidak dapat diuraikan"):
        fixer.fix_all(str(tmp_path / "never_created.docx"))


def test_revision_engine_contract_and_types():
    """Verify RevisionEngine.calculate_scores returns correct structure and data types."""
    from engines.revision_engine import RevisionEngine

    findings = [
        {"rule_id": "ERR_1", "status": "ERROR", "category": "Statistics"},
        {"rule_id": "WARN_1", "status": "WARNING", "category": "Format"},
        {"rule_id": "INFO_1", "status": "INFO", "category": "Metadata"},
        {"rule_id": "UNV_1", "status": "UNVERIFIED", "category": "Integrity"},
    ]
    engine = RevisionEngine(findings)
    score_card = engine.calculate_scores()

    assert isinstance(score_card, dict)
    assert "counts" in score_card
    assert "overall_score" in score_card
    assert "penalty" in score_card
    assert "category_scores" in score_card

    counts = score_card["counts"]
    assert counts["ERROR"] == 1
    assert counts["WARNING"] == 1
    assert counts["INFO"] == 1
    assert counts["UNVERIFIED"] == 1
    assert counts["PASS"] == 0

    # Penalty = (1 * 15.0) + (1 * 5.0) + (1 * 2.0) = 22.0 -> Score = 78.0
    assert score_card["penalty"] == 22.0
    assert score_card["overall_score"] == 78.0
    assert isinstance(score_card["overall_score"], float)


def test_revision_engine_empty_and_none_findings():
    """Verify RevisionEngine safely handles empty list and None without division by zero."""
    from engines.revision_engine import RevisionEngine

    for empty_input in ([], None):
        engine = RevisionEngine(empty_input)
        score_card = engine.calculate_scores()

        assert score_card["overall_score"] == 100.0
        assert score_card["penalty"] == 0.0
        assert score_card["counts"]["ERROR"] == 0
        assert score_card["counts"]["WARNING"] == 0
        assert score_card["counts"]["UNVERIFIED"] == 0


def test_revision_engine_status_normalization_and_unknowns():
    """Verify status normalization and explicit handling of unknown / non-dict findings."""
    from engines.revision_engine import RevisionEngine

    findings = [
        {"rule_id": "E1", "finding_status": "critical"},  # maps to ERROR
        {"rule_id": "W1", "severity": "warn"},           # maps to WARNING
        {"rule_id": "P1", "status": "passed"},           # maps to PASS
        {"rule_id": "U1", "status": "MYSTERIOUS_STATUS"}, # unknown -> UNVERIFIED
        "invalid_non_dict_finding",                       # non-dict -> UNVERIFIED
    ]
    engine = RevisionEngine(findings)
    score_card = engine.calculate_scores()
    counts = score_card["counts"]

    assert counts["ERROR"] == 1
    assert counts["WARNING"] == 1
    assert counts["PASS"] == 1
    assert counts["UNVERIFIED"] == 2


def test_revision_engine_score_bounds_and_no_nan():
    """Verify score clamping between [0.0, 100.0] and exclusion of NaN / Inf."""
    import math
    from engines.revision_engine import RevisionEngine

    many_errors = [{"rule_id": f"E_{i}", "status": "ERROR"} for i in range(10)]
    engine = RevisionEngine(many_errors)
    score_card = engine.calculate_scores()

    assert score_card["overall_score"] == 0.0
    assert not math.isnan(score_card["overall_score"])
    assert not math.isinf(score_card["overall_score"])


def test_revision_engine_with_base_summary_and_reporting():
    """Verify integration with base_summary and downstream ReportEngine."""
    from engines.revision_engine import RevisionEngine
    from engines.report_engine import ReportEngine

    findings = [{"rule_id": "WARN_1", "status": "WARNING", "category": "Format"}]
    base_summary = {"PASS": 12, "ERROR": 0, "WARNING": 0, "UNVERIFIED": 0}

    engine = RevisionEngine(findings, base_summary=base_summary)
    score_card = engine.calculate_scores()

    assert score_card["counts"]["PASS"] == 12
    assert score_card["counts"]["WARNING"] == 1
    assert score_card["overall_score"] == 95.0

    checklist = engine.generate_checklist()
    doc_info = {"filename": "test.docx", "page_count": 50}

    rep_engine = ReportEngine(
        score_card["counts"],
        findings,
        doc_info,
        checklist,
        score_card["overall_score"]
    )
    json_rep = rep_engine.to_json()
    assert "95.0" in json_rep or "95" in json_rep
    assert rep_engine.overall_score == 95.0


def test_streamlit_ui_audit_flow_with_apptest():
    """Simulate complete Streamlit UI upload and audit flow using AppTest."""
    from streamlit.testing.v1 import AppTest

    docx_path = Path("/Users/jevin/AI-Thesis-Generator/golden_dataset/documents/TEST-001_normal.docx")
    assert docx_path.exists(), "TEST-001_normal.docx fixture must exist"

    at = AppTest.from_file("/Users/jevin/AI-Thesis-Generator/app.py", default_timeout=25)
    at.run()

    # Upload document
    fu = at.file_uploader(key="thesis_uploader")
    fu.upload("TEST-001_normal.docx", docx_path.read_bytes())
    at.run()

    # Click audit button
    audit_btns = [b for b in at.button if "MULAI AUDIT" in b.label]
    assert len(audit_btns) > 0, "Audit button must be present after upload"
    audit_btns[0].click()
    at.run()

    # Verify zero exceptions were thrown during execution (including RevisionEngine calls)
    assert len(at.exception) == 0, f"App threw exceptions during audit flow: {[e.message for e in at.exception]}"

    # Verify dashboard elements rendered
    subheaders = [s.value for s in at.subheader]
    assert any("Ringkasan Hasil Audit" in s for s in subheaders)
    assert any("Unduh Laporan Audit Lengkap" in s for s in subheaders)


def test_revision_engine_accepts_flexible_kwargs_and_backward_compatibility():
    """Verify RevisionEngine is resilient to arbitrary kwargs and preserves base_summary."""
    from engines.revision_engine import RevisionEngine

    findings = [{"rule_id": "ERR_1", "status": "ERROR", "category": "Format"}]
    base_summary = {"PASS": 10, "ERROR": 0, "WARNING": 0, "UNVERIFIED": 0}

    # Pass unexpected keyword arguments to verify defensive initialization
    engine = RevisionEngine(
        findings,
        base_summary=base_summary,
        unexpected_argument="test_val",
        another_flag=True,
    )
    assert engine.base_summary == base_summary

    # calculate_scores with unexpected kwargs
    score_card = engine.calculate_scores(base_summary=base_summary, extra_param="ignored")
    assert score_card["counts"]["PASS"] == 10
    assert score_card["counts"]["ERROR"] == 1
    assert score_card["overall_score"] == 85.0

