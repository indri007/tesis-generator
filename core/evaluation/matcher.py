"""Finding Matching Engine for Thesis Audit Evaluation.

Applies explicit, deterministic matching rules between detected auditor findings
and reference ground-truth annotations without subjective or fuzzy heuristics.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from core.evaluation.schema import BenchmarkAnnotation


class MatchVerdict(str, Enum):
    TRUE_POSITIVE = "TRUE_POSITIVE"
    FALSE_POSITIVE = "FALSE_POSITIVE"
    FALSE_NEGATIVE = "FALSE_NEGATIVE"
    WRONG_LOCATION = "WRONG_LOCATION"
    WRONG_SEVERITY = "WRONG_SEVERITY"


def normalize_category(category_str: str) -> str:
    """Normalizes various category strings to standard canonical form."""
    c = category_str.lower().strip()
    if any(k in c for k in ["format", "margin", "font", "typography"]):
        return "format"
    if any(k in c for k in ["struct", "bab", "word", "abstrak", "halaman"]):
        return "structure"
    if any(k in c for k in ["citat", "sitasi", "referensi", "bib"]):
        return "citations"
    if any(k in c for k in ["formula", "rumus", "recalculat"]):
        return "formula"
    if any(k in c for k in ["stat", "sample", "variabel", "variable", "uji"]):
        return "statistics"
    if any(k in c for k in ["journal", "jurnal", "cross_doc"]):
        return "journal_alignment"
    return c


@dataclass
class MatchResult:
    verdict: MatchVerdict
    reference: BenchmarkAnnotation | None = None
    detected: dict[str, Any] | None = None
    reason: str = ""


class FindingMatcher:
    """Matches detected findings against reference annotations for a document."""

    def __init__(
        self,
        reference_annotations: list[BenchmarkAnnotation],
        detected_findings: list[dict[str, Any]],
        strict_location: bool = False,
        strict_severity: bool = True,
    ):
        self.references = reference_annotations
        self.detected = detected_findings
        self.strict_location = strict_location
        self.strict_severity = strict_severity

    def match(self) -> list[MatchResult]:
        """Evaluates detected findings against reference annotations.
        Returns a list of MatchResult with exact matching semantics.
        """
        results: list[MatchResult] = []
        unmatched_refs = list(self.references)
        unmatched_detected = list(self.detected)

        # 1. Match detected findings against references
        matched_pairs: list[tuple[BenchmarkAnnotation, dict[str, Any]]] = []

        for det in list(unmatched_detected):
            det_rule = det.get("rule_id", "")
            det_cat = normalize_category(det.get("category", ""))

            # Look for exact rule_id and category match in references
            matched_ref: BenchmarkAnnotation | None = None
            for ref in unmatched_refs:
                ref_cat = normalize_category(ref.audit_category)
                if ref.rule_id == det_rule and ref_cat == det_cat:
                    matched_ref = ref
                    break

            if matched_ref:
                unmatched_refs.remove(matched_ref)
                unmatched_detected.remove(det)
                matched_pairs.append((matched_ref, det))

        # 2. Evaluate matched pairs for exactness (severity and location)
        for ref, det in matched_pairs:
            det_sev = (det.get("status") or det.get("severity") or "INFO").upper()
            ref_sev = ref.expected_severity.upper()

            # Location verification
            loc_matched = True
            ref_loc = ref.evidence_location
            if self.strict_location and ref_loc.page is not None:
                det_page = det.get("page")
                if det_page is None or det_page != ref_loc.page:
                    loc_matched = False

            if not loc_matched:
                results.append(
                    MatchResult(
                        verdict=MatchVerdict.WRONG_LOCATION,
                        reference=ref,
                        detected=det,
                        reason=f"Halaman bukti berbeda: referensi hal. {ref_loc.page}, terdeteksi hal. {det.get('page')}",
                    )
                )
            elif self.strict_severity and det_sev != ref_sev:
                results.append(
                    MatchResult(
                        verdict=MatchVerdict.WRONG_SEVERITY,
                        reference=ref,
                        detected=det,
                        reason=f"Tingkat keparahan berbeda: diharapkan {ref_sev}, terdeteksi {det_sev}",
                    )
                )
            else:
                results.append(
                    MatchResult(
                        verdict=MatchVerdict.TRUE_POSITIVE,
                        reference=ref,
                        detected=det,
                        reason="Temuan sesuai dengan aturan, kategori, lokasi, dan keparahan referensi.",
                    )
                )

        # 3. Remaining unmatched detected findings are False Positives
        for det in unmatched_detected:
            # Skip PASS or INFO items if they are not error/warning violations
            det_status = (det.get("status") or det.get("severity") or "").upper()
            if det_status == "PASS":
                continue

            results.append(
                MatchResult(
                    verdict=MatchVerdict.FALSE_POSITIVE,
                    reference=None,
                    detected=det,
                    reason=f"Temuan '{det.get('rule_id')}' terdeteksi namun tidak ada pada ground truth referensi.",
                )
            )

        # 4. Remaining unmatched references are False Negatives
        for ref in unmatched_refs:
            results.append(
                MatchResult(
                    verdict=MatchVerdict.FALSE_NEGATIVE,
                    reference=ref,
                    detected=None,
                    reason=f"Pelanggaran '{ref.rule_id}' diharapkan pada dokumen namun tidak terdeteksi oleh auditor.",
                )
            )

        return results
