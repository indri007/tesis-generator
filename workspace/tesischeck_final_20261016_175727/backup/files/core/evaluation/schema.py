"""Annotated Benchmark Schema & Data Structures for Academic Thesis Audit.

Provides standardized, anonymized data schemas for evaluating thesis audit accuracy,
ensuring zero data leakage between development and evaluation datasets.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class AuditCategory(str, Enum):
    FORMAT = "format"
    STRUCTURE = "structure"
    CITATIONS = "citations"
    FORMULA = "formula"
    STATISTICS = "statistics"
    JOURNAL_ALIGNMENT = "journal_alignment"


class SeverityLevel(str, Enum):
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"


class VerificationStatus(str, Enum):
    VERIFIED = "VERIFIED"
    UNVERIFIED = "UNVERIFIED"
    AMBIGUOUS = "AMBIGUOUS"


class AdjudicationStatus(str, Enum):
    CONSENSUS = "CONSENSUS"
    ADJUDICATED = "ADJUDICATED"
    DISPUTED = "DISPUTED"


@dataclass
class EvidenceLocation:
    page: int | None = None
    section: str | None = None
    excerpt_query: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "page": self.page,
            "section": self.section,
            "excerpt_query": self.excerpt_query,
        }


@dataclass
class BenchmarkAnnotation:
    """Represents a single reference ground-truth annotation."""
    document_id: str
    audit_category: str
    rule_id: str
    reference_finding: str
    evidence_location: EvidenceLocation
    expected_severity: str
    expected_verification_status: str
    reviewer_id: str
    adjudication_status: str = AdjudicationStatus.CONSENSUS.value
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "document_id": self.document_id,
            "audit_category": self.audit_category,
            "rule_id": self.rule_id,
            "reference_finding": self.reference_finding,
            "evidence_location": self.evidence_location.to_dict(),
            "expected_severity": self.expected_severity,
            "expected_verification_status": self.expected_verification_status,
            "reviewer_id": self.reviewer_id,
            "adjudication_status": self.adjudication_status,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BenchmarkAnnotation:
        loc_data = data.get("evidence_location", {})
        loc = EvidenceLocation(
            page=loc_data.get("page"),
            section=loc_data.get("section"),
            excerpt_query=loc_data.get("excerpt_query"),
        )
        return cls(
            document_id=data["document_id"],
            audit_category=data["audit_category"],
            rule_id=data["rule_id"],
            reference_finding=data["reference_finding"],
            evidence_location=loc,
            expected_severity=data.get("expected_severity", SeverityLevel.ERROR.value),
            expected_verification_status=data.get(
                "expected_verification_status", VerificationStatus.VERIFIED.value
            ),
            reviewer_id=data.get("reviewer_id", "REV-ANON"),
            adjudication_status=data.get(
                "adjudication_status", AdjudicationStatus.CONSENSUS.value
            ),
            notes=data.get("notes", ""),
        )


@dataclass
class EvaluatorConfig:
    """Configuration for reproducible offline benchmark evaluation."""
    base_commit: str = "1c34578"
    code_version: str = "1c34578"
    working_tree_dirty: bool = True
    dataset_version: str = "2026.1"
    ruleset_id: str = "MIKOM_2026"
    ruleset_version: str = "2026.1.0"
    random_seed: int = 42
    offline_mode: bool = True
    split: str = "evaluation"  # "development" | "evaluation"
