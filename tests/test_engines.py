"""Tests for engines package: rule loader, rule engine, finding engine, evidence engine, and audit engine."""

from engines.audit_engine import audit_thesis
from engines.evidence_engine import create_evidence
from engines.finding_engine import build_findings, summarize
from engines.rule_engine import evaluate_rule
from engines.rule_loader import load_rules


def test_rule_loader_validates_json():
    """Rule Loader reads and validates JSON against schema without errors."""
    ruleset = load_rules("rules/mikom_2026.json")
    assert ruleset["rule_set_id"] == "MIKOM_2026"
    assert "rules" in ruleset
    assert len(ruleset["rules"]) >= 10

    # Ensure rule IDs are unique
    rule_ids = [r["id"] for r in ruleset["rules"]]
    assert len(rule_ids) == len(set(rule_ids))


def test_margin_matches_expected_value():
    """Rule Engine correctly marks matching field as PASS."""
    rule = {
        "id": "FORMAT-001",
        "category": "Format",
        "description": "Margin kiri",
        "severity": "ERROR",
        "field": "format.left_margin_cm",
        "operator": "equals",
        "expected": 4.0,
        "recommendation": "Perbaiki margin",
    }

    document = {
        "format": {
            "left_margin_cm": 4.0
        }
    }

    result = evaluate_rule(rule, document)
    assert result["status"] == "PASS"
    assert result["actual"] == 4.0


def test_missing_field_is_unverified():
    """Rule Engine correctly marks missing field as UNVERIFIED."""
    rule = {
        "id": "FORMAT-001",
        "category": "Format",
        "description": "Margin kiri",
        "severity": "ERROR",
        "field": "format.left_margin_cm",
        "operator": "equals",
        "expected": 4.0,
        "recommendation": "Perbaiki margin",
    }

    result = evaluate_rule(rule, {})
    assert result["status"] == "UNVERIFIED"
    assert result["actual"] is None


def test_rule_engine_operators():
    """Test min, max, not_empty, and regex operators."""
    # min operator
    rule_min = {
        "id": "TEST-MIN", "category": "Test", "severity": "ERROR",
        "field": "words", "operator": "min", "expected": 100, "recommendation": "Tambah kata"
    }
    assert evaluate_rule(rule_min, {"words": 150})["status"] == "PASS"
    assert evaluate_rule(rule_min, {"words": 80})["status"] == "ERROR"

    # max operator
    rule_max = {
        "id": "TEST-MAX", "category": "Test", "severity": "WARNING",
        "field": "pages", "operator": "max", "expected": 175, "recommendation": "Kurangi halaman"
    }
    assert evaluate_rule(rule_max, {"pages": 140})["status"] == "PASS"
    assert evaluate_rule(rule_max, {"pages": 190})["status"] == "WARNING"

    # not_empty operator
    rule_ne = {
        "id": "TEST-NE", "category": "Test", "severity": "ERROR",
        "field": "title", "operator": "not_empty", "expected": None, "recommendation": "Isi judul"
    }
    assert evaluate_rule(rule_ne, {"title": "Tesis K-Pop"})["status"] == "PASS"
    assert evaluate_rule(rule_ne, {"title": ""})["status"] == "ERROR"


def test_finding_engine_filters_and_summarizes():
    """Finding Engine filters out PASS and correctly tallies statuses."""
    evaluations = [
        {"status": "PASS", "rule_id": "R1"},
        {"status": "ERROR", "rule_id": "R2"},
        {"status": "WARNING", "rule_id": "R3"},
        {"status": "UNVERIFIED", "rule_id": "R4"},
        {"status": "INFO", "rule_id": "R5"},
        {"status": "PASS", "rule_id": "R6"},
    ]

    findings = build_findings(evaluations)
    assert len(findings) == 4
    assert all(f["status"] != "PASS" for f in findings)

    summary = summarize(evaluations)
    assert summary["total_rules"] == 6
    assert summary["PASS"] == 2
    assert summary["ERROR"] == 1
    assert summary["WARNING"] == 1
    assert summary["UNVERIFIED"] == 1
    assert summary["INFO"] == 1


def test_evidence_engine_creation():
    """Evidence Engine produces typed evidence models with verification status."""
    finding = {
        "rule_id": "FORMAT_MARGIN_LEFT_001",
        "status": "ERROR",
        "category": "Format",
        "actual": 3.0,
        "expected": 4.0,
        "recommendation": "Ubah margin kiri ke 4 cm",
        "source": {"title": "Pedoman MIKOM 2026", "page": 40}
    }

    evidence = create_evidence(finding, page=12, section="BAB I", excerpt="Margin kiri terdeteksi 3.0 cm")
    assert evidence["rule_id"] == "FORMAT_MARGIN_LEFT_001"
    assert evidence["status"] == "ERROR"
    assert evidence["page"] == 12
    assert evidence["section"] == "BAB I"
    assert evidence["source_page"] == 40
    assert evidence["evidence_verified"] is True

    # Missing page/excerpt results in evidence_verified = False
    unverified_ev = create_evidence(finding)
    assert unverified_ev["evidence_verified"] is False


def test_audit_thesis_end_to_end():
    """audit_thesis executes full pipeline against document model."""
    doc = {
        "page_count": 140,
        "margins": {
            "top_cm": 4.0,
            "left_cm": 4.0,
            "bottom_cm": 3.0,
            "right_cm": 3.0
        },
        "typography": {
            "font_family": "Times New Roman",
            "font_size_pt": 12,
            "line_spacing": 2.0,
            "alignment": "JUSTIFY"
        },
        "word_count": {
            "total_body_words": 48000
        },
        "chapters": {
            "BAB_I": {"exists": True},
            "BAB_II": {"exists": True},
            "BAB_III": {"exists": True},
            "BAB_IV": {"exists": True},
            "BAB_V": {"exists": True}
        },
        "bibliography": {"exists": True},
        "abstract": {
            "id": {"word_count": 210, "keyword_count": 4},
            "en": {"word_count": 205, "keyword_count": 4}
        },
        "citations": {"orphaned_count": 0},
        "references": {"unused_count": 0},
        "variables": {"inconsistency_count": 0},
        "formulas": {"arithmetic_error_count": 0, "model_mismatch_count": 0},
        "statistics": {"contradiction_count": 0, "sample_mismatch_count": 0},
        "journal_comparison": {"critical_mismatch_count": 0}
    }

    result = audit_thesis(doc, rules_path="rules/mikom_2026.json")
    assert result.rule_set_id == "MIKOM_2026"
    assert result.summary["total_rules"] > 0
    assert result.summary["ERROR"] == 0
    assert result.summary["PASS"] > 0
    assert len(result.findings) == 0
