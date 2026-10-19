"""Error Analysis & Failure Taxonomy Engine.

Categorizes audit discrepancies into standard failure modes:
1. FALSE_POSITIVE
2. FALSE_NEGATIVE
3. WRONG_EVIDENCE_LOCATION
4. WRONG_SEVERITY
5. UNSUPPORTED_CONCLUSION
6. MISSING_CITATION_REFERENCE_MATCH
7. EXTRACTION_FAILURE
8. AMBIGUOUS_ACADEMIC_INTERPRETATION
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from core.evaluation.matcher import MatchResult, MatchVerdict


class ErrorCategory(str, Enum):
    FALSE_POSITIVE = "FALSE_POSITIVE"
    FALSE_NEGATIVE = "FALSE_NEGATIVE"
    WRONG_EVIDENCE_LOCATION = "WRONG_EVIDENCE_LOCATION"
    WRONG_SEVERITY = "WRONG_SEVERITY"
    UNSUPPORTED_CONCLUSION = "UNSUPPORTED_CONCLUSION"
    MISSING_CITATION_REFERENCE_MATCH = "MISSING_CITATION_REFERENCE_MATCH"
    EXTRACTION_FAILURE = "EXTRACTION_FAILURE"
    AMBIGUOUS_ACADEMIC_INTERPRETATION = "AMBIGUOUS_ACADEMIC_INTERPRETATION"


@dataclass
class CategorizedError:
    error_type: ErrorCategory
    rule_id: str
    audit_category: str
    document_id: str
    description: str
    evidence_snippet: str
    suggested_action: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "error_type": self.error_type.value,
            "rule_id": self.rule_id,
            "audit_category": self.audit_category,
            "document_id": self.document_id,
            "description": self.description,
            "evidence_snippet": self.evidence_snippet,
            "suggested_action": self.suggested_action,
        }


class ErrorAnalyzer:
    """Classifies and synthesizes benchmark discrepancies into structured failure modes."""

    def __init__(self, match_results: list[MatchResult], document_id: str = "DOC-ANON"):
        self.results = match_results
        self.doc_id = document_id

    def analyze(self) -> list[CategorizedError]:
        """Classifies each non-TP match result into one of the 8 standard failure modes."""
        categorized: list[CategorizedError] = []

        for m in self.results:
            if m.verdict == MatchVerdict.TRUE_POSITIVE:
                continue

            rule_id = ""
            cat = ""
            desc = m.reason
            snippet = ""

            if m.reference:
                rule_id = m.reference.rule_id
                cat = m.reference.audit_category
                snippet = m.reference.reference_finding
            elif m.detected:
                rule_id = m.detected.get("rule_id", "UNKNOWN")
                cat = m.detected.get("category", "General")
                snippet = str(m.detected.get("message") or m.detected.get("description") or "")[:200]

            if m.verdict == MatchVerdict.WRONG_LOCATION:
                err_type = ErrorCategory.WRONG_EVIDENCE_LOCATION
                action = "Perbaiki pemetaan paragraf/halaman pada parser dan evidence_mapper."
            elif m.verdict == MatchVerdict.WRONG_SEVERITY:
                err_type = ErrorCategory.WRONG_SEVERITY
                action = "Sesuaikan tingkat keparahan (ERROR vs WARNING) pada rule definition atau auditor."
            elif m.verdict == MatchVerdict.FALSE_POSITIVE:
                # Dissect false positives
                if "CITATION" in rule_id or "BIB" in rule_id:
                    err_type = ErrorCategory.MISSING_CITATION_REFERENCE_MATCH
                    action = "Periksa regex pemisahan nama sitasi naratif atau entri daftar pustaka."
                elif "UNVERIFIED" in str(m.detected):
                    err_type = ErrorCategory.EXTRACTION_FAILURE
                    action = "Tingkatkan ketahanan ekstraksi parser untuk format naskah."
                elif "AMBIGUOUS" in str(m.detected):
                    err_type = ErrorCategory.AMBIGUOUS_ACADEMIC_INTERPRETATION
                    action = "Eskalasi temuan ambigu ke mekanisme review manusia."
                else:
                    err_type = ErrorCategory.FALSE_POSITIVE
                    action = "Tinjau ambang batas dan kondisi aturan agar tidak memicu alarm palsu."
            elif m.verdict == MatchVerdict.FALSE_NEGATIVE:
                # Dissect false negatives
                if "RECALCULATION" in rule_id or "STAT" in rule_id:
                    err_type = ErrorCategory.UNSUPPORTED_CONCLUSION
                    action = "Tingkatkan ekstraksi formula atau pendeteksi p-value pada naskah."
                elif "EXTRACTION" in rule_id or "PARSER" in rule_id:
                    err_type = ErrorCategory.EXTRACTION_FAILURE
                    action = "Periksa kelengkapan teks hasil parsing pada dokumen."
                else:
                    err_type = ErrorCategory.FALSE_NEGATIVE
                    action = "Perluas cakupan regex atau aturan auditor untuk mendeteksi pelanggaran ini."
            else:
                err_type = ErrorCategory.AMBIGUOUS_ACADEMIC_INTERPRETATION
                action = "Periksa interpretasi pedoman penulisan tesis."

            categorized.append(
                CategorizedError(
                    error_type=err_type,
                    rule_id=rule_id,
                    audit_category=cat,
                    document_id=self.doc_id,
                    description=desc,
                    evidence_snippet=snippet,
                    suggested_action=action,
                )
            )

        return categorized

    @staticmethod
    def summarize_errors(errors: list[CategorizedError]) -> dict[str, Any]:
        """Provides a statistical breakdown of failure modes and highlights high-risk areas."""
        counts: dict[str, int] = {}
        for e in errors:
            key = e.error_type.value
            counts[key] = counts.get(key, 0) + 1

        # Determine highest risk category
        high_risk = sorted(counts.items(), key=lambda x: x[1], reverse=True)
        high_risk_name = high_risk[0][0] if high_risk else "None"

        return {
            "total_errors": len(errors),
            "breakdown": counts,
            "highest_risk_category": high_risk_name,
            "samples": [e.to_dict() for e in errors[:10]],  # First 10 samples
        }
