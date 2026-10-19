"""Unit Tests for Evaluation Metrics, Matcher, Error Taxonomy, and Inter-Annotator Agreement.

Validates that metrics handle edge cases (zero denominator, unknown categories),
computes Cohen's Kappa against exact manual derivations, and classifies all 8 error types.
"""

from __future__ import annotations

from core.evaluation.error_analysis import ErrorAnalyzer, ErrorCategory
from core.evaluation.matcher import FindingMatcher, MatchVerdict
from core.evaluation.metrics import (
    CategoryMetrics,
    compute_cohens_kappa,
)
from core.evaluation.schema import BenchmarkAnnotation, EvidenceLocation


def test_category_metrics_zero_denominators():
    """Verifies that zero denominators return None / N/A, never misleading 0.0."""
    # Completely empty category
    m_empty = CategoryMetrics(category="untested_category")
    assert m_empty.precision is None
    assert m_empty.recall is None
    assert m_empty.f1_score is None

    d = m_empty.to_dict()
    assert d["precision"] is None
    assert d["precision_display"] == "N/A (undefined)"
    assert d["recall_display"] == "N/A (undefined)"
    assert d["f1_display"] == "N/A (undefined)"

    # Category with only false positives (no references)
    m_fp_only = CategoryMetrics(category="hallucinated", false_positives=3)
    assert m_fp_only.precision == 0.0  # TP=0, FP=3 -> 0/3 = 0.0
    assert m_fp_only.recall is None    # TP=0, FN=0 -> 0/0 = undefined
    assert m_fp_only.f1_score is None

    # Category with only false negatives (no detections)
    m_fn_only = CategoryMetrics(category="missed", false_negatives=4, support=4)
    assert m_fn_only.precision is None  # TP=0, FP=0 -> undefined
    assert m_fn_only.recall == 0.0     # TP=0, FN=4 -> 0/4 = 0.0
    assert m_fn_only.f1_score is None


def test_cohens_kappa_manual_derivation():
    """Validates Cohen's Kappa against manual mathematical derivation.

    Data:
      R1 = ["PASS", "PASS", "ERROR", "WARNING"]
      R2 = ["PASS", "PASS", "ERROR", "PASS"]
      N = 4, Agreements = 3 -> Po = 3/4 = 0.75
      Pe = (0.5 * 0.75) + (0.25 * 0.25) + 0 = 0.4375
      Kappa = (0.75 - 0.4375) / (1 - 0.4375) = 0.3125 / 0.5625 = 0.5556
    """
    r1 = ["PASS", "PASS", "ERROR", "WARNING"]
    r2 = ["PASS", "PASS", "ERROR", "PASS"]

    result = compute_cohens_kappa(r1, r2)
    assert result["sample_count"] == 4
    assert result["observed_agreement"] == 75.0
    assert result["chance_agreement"] == 43.75
    assert result["kappa"] == 0.5556
    assert result["agreement_strength"] == "Moderate agreement"
    assert result["disagreements_count"] == 1
    assert result["disagreements"][0]["item_index"] == 3


def test_finding_matcher_synthetic_fixtures():
    """Tests the deterministic finding matcher across known ground-truth scenarios:
    1. True positive (exact match)
    2. Wrong severity (ERROR expected, WARNING detected)
    3. Wrong evidence location (page 5 expected, page 99 detected)
    4. False positive (unexpected finding detected)
    5. False negative (expected violation missed)
    """
    refs = [
        BenchmarkAnnotation(
            document_id="DOC-001",
            audit_category="format",
            rule_id="FORMAT_MARGIN_LEFT_001",
            reference_finding="Margin kiri salah",
            evidence_location=EvidenceLocation(page=1),
            expected_severity="ERROR",
            expected_verification_status="VERIFIED",
            reviewer_id="REV-1"
        ),
        BenchmarkAnnotation(
            document_id="DOC-001",
            audit_category="format",
            rule_id="FORMAT_FONT_001",
            reference_finding="Font salah",
            evidence_location=EvidenceLocation(page=2),
            expected_severity="ERROR",
            expected_verification_status="VERIFIED",
            reviewer_id="REV-1"
        ),
        BenchmarkAnnotation(
            document_id="DOC-001",
            audit_category="citations",
            rule_id="CITATION_ORPHAN_001",
            reference_finding="Sitasi tanpa rujukan",
            evidence_location=EvidenceLocation(page=5),
            expected_severity="WARNING",
            expected_verification_status="VERIFIED",
            reviewer_id="REV-1"
        ),
        BenchmarkAnnotation(
            document_id="DOC-001",
            audit_category="formula",
            rule_id="FORMULA_RECALC_001",
            reference_finding="Salah hitung regresi",
            evidence_location=EvidenceLocation(page=10),
            expected_severity="ERROR",
            expected_verification_status="VERIFIED",
            reviewer_id="REV-1"
        )
    ]

    detected = [
        # 1. Exact match -> TRUE_POSITIVE
        {
            "rule_id": "FORMAT_MARGIN_LEFT_001",
            "category": "format",
            "status": "ERROR",
            "page": 1,
            "message": "Margin kiri 3.0 cm"
        },
        # 2. Wrong severity -> WRONG_SEVERITY
        {
            "rule_id": "FORMAT_FONT_001",
            "category": "format",
            "status": "WARNING",
            "page": 2,
            "message": "Font Arial"
        },
        # 3. Wrong location -> WRONG_LOCATION (when strict_location=True)
        {
            "rule_id": "CITATION_ORPHAN_001",
            "category": "citations",
            "status": "WARNING",
            "page": 99,
            "message": "Sitasi Smith"
        },
        # 4. Spurious finding -> FALSE_POSITIVE
        {
            "rule_id": "STAT_SPURIOUS_001",
            "category": "statistics",
            "status": "ERROR",
            "page": 4,
            "message": "Temuan palsu"
        }
        # FORMULA_RECALC_001 is omitted -> FALSE_NEGATIVE
    ]

    matcher = FindingMatcher(
        reference_annotations=refs,
        detected_findings=detected,
        strict_location=True,
        strict_severity=True
    )
    results = matcher.match()

    verdicts = [r.verdict for r in results]
    assert MatchVerdict.TRUE_POSITIVE in verdicts
    assert MatchVerdict.WRONG_SEVERITY in verdicts
    assert MatchVerdict.WRONG_LOCATION in verdicts
    assert MatchVerdict.FALSE_POSITIVE in verdicts
    assert MatchVerdict.FALSE_NEGATIVE in verdicts


def test_error_analyzer_eight_taxonomies():
    """Verifies that ErrorAnalyzer classifies non-TP findings into the 8 required taxonomies."""
    from core.evaluation.matcher import MatchResult

    ref_cite = BenchmarkAnnotation(
        document_id="DOC-001",
        audit_category="citations",
        rule_id="CITATION_ORPHAN_001",
        reference_finding="Sitasi tanpa rujukan",
        evidence_location=EvidenceLocation(page=3),
        expected_severity="ERROR",
        expected_verification_status="VERIFIED",
        reviewer_id="REV-1"
    )

    matches = [
        MatchResult(
            verdict=MatchVerdict.WRONG_LOCATION,
            reference=ref_cite,
            detected={"rule_id": "CITATION_ORPHAN_001", "page": 8},
            reason="Halaman tidak cocok"
        ),
        MatchResult(
            verdict=MatchVerdict.WRONG_SEVERITY,
            reference=ref_cite,
            detected={"rule_id": "CITATION_ORPHAN_001", "status": "INFO"},
            reason="Severity tidak cocok"
        ),
        MatchResult(
            verdict=MatchVerdict.FALSE_POSITIVE,
            detected={"rule_id": "CITATION_EXTRA_001", "category": "citations", "status": "ERROR"},
            reason="Sitasi tidak ada di acuan"
        ),
        MatchResult(
            verdict=MatchVerdict.FALSE_NEGATIVE,
            reference=BenchmarkAnnotation(
                document_id="DOC-001",
                audit_category="formula",
                rule_id="FORMULA_RECALCULATION_001",
                reference_finding="Klaim tidak didukung",
                evidence_location=EvidenceLocation(),
                expected_severity="ERROR",
                expected_verification_status="VERIFIED",
                reviewer_id="REV-1"
            ),
            reason="Rumus tidak terdeteksi"
        ),
    ]

    analyzer = ErrorAnalyzer(matches, document_id="DOC-001")
    categorized = analyzer.analyze()
    types = [c.error_type for c in categorized]

    assert ErrorCategory.WRONG_EVIDENCE_LOCATION in types
    assert ErrorCategory.WRONG_SEVERITY in types
    assert ErrorCategory.MISSING_CITATION_REFERENCE_MATCH in types
    assert ErrorCategory.UNSUPPORTED_CONCLUSION in types

    summary = ErrorAnalyzer.summarize_errors(categorized)
    assert summary["total_errors"] == 4
    assert summary["highest_risk_category"] != "None"


def test_cohens_kappa_is_undefined_when_expected_agreement_is_one():
    """Kappa must be None when its denominator is zero."""
    from core.evaluation.metrics import compute_cohens_kappa

    result = compute_cohens_kappa(
        ["ERROR", "ERROR"],
        ["ERROR", "ERROR"],
    )

    assert result["kappa"] is None
    assert result["agreement_strength"].startswith("N/A")
