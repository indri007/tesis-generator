"""Canonical Data Models and Schema Normalization for Literature Ingestion.

Implements Phase 1 taxonomic requirements:
- Persistent Record ID (#6)
- Schema Normalization (#7)
- Publication-Year Normalization (#8)
- Missing-Value Normalization (#9)
- Type Normalization (#10)
- Search Provenance (#4)
- Retrieval Timestamp (#5)
- Evidence-Level Tagging (#23)
- Data Quality Scoring (#22)
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class DocumentType(str, Enum):
    """Normalized document types."""

    JOURNAL_ARTICLE = "journal-article"
    CONFERENCE_PAPER = "conference-paper"
    PREPRINT = "preprint"
    BOOK_CHAPTER = "book-chapter"
    THESIS = "thesis"
    REPORT = "report"
    OTHER = "other"

    @classmethod
    def from_raw(cls, raw: str | None) -> DocumentType:
        if not raw:
            return cls.OTHER
        raw_norm = raw.lower().strip()
        if any(k in raw_norm for k in ["journal", "article", "paper", "works"]):
            return cls.JOURNAL_ARTICLE
        if any(k in raw_norm for k in ["proceedings", "conference", "inproceedings"]):
            return cls.CONFERENCE_PAPER
        if any(k in raw_norm for k in ["preprint", "arxiv", "biorxiv", "ssrn", "medrxiv"]):
            return cls.PREPRINT
        if any(k in raw_norm for k in ["chapter", "book"]):
            return cls.BOOK_CHAPTER
        if any(k in raw_norm for k in ["thesis", "dissertation", "skripsi", "tesis"]):
            return cls.THESIS
        if "report" in raw_norm:
            return cls.REPORT
        return cls.OTHER


class InclusionStatus(str, Enum):
    """PRISMA and review screening status."""

    INCLUDED = "INCLUDED"
    EXCLUDED = "EXCLUDED"
    PENDING_REVIEW = "PENDING_REVIEW"


class DuplicateStatus(str, Enum):
    """Deduplication classification status."""

    UNIQUE = "UNIQUE"
    EXACT_DUPLICATE = "EXACT_DUPLICATE"
    CANDIDATE_DUPLICATE = "CANDIDATE_DUPLICATE"


class EvidenceLevel(str, Enum):
    """Academic hierarchy of evidence tagging."""

    LEVEL_1_SYSTEMATIC_REVIEW = "LEVEL_1_SYSTEMATIC_REVIEW"  # SLR, Meta-analysis, PRISMA
    LEVEL_2_EMPIRICAL_QUANT = "LEVEL_2_EMPIRICAL_QUANT"      # SNA, IndoBERT, Experiments, Survey
    LEVEL_3_EMPIRICAL_QUAL = "LEVEL_3_EMPIRICAL_QUAL"        # Case study, In-depth Interview, FGD
    LEVEL_4_CONCEPTUAL_THEORY = "LEVEL_4_CONCEPTUAL_THEORY"  # Marketing 6.0 conceptual, Framework
    UNKNOWN = "UNKNOWN"


@dataclass
class SearchProvenance:
    """Provenance audit metadata for literature retrieval."""

    source_database: str
    search_query: str
    provider_record_id: str = ""
    retrieved_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SearchProvenance:
        return cls(
            source_database=str(data.get("source_database", "unknown")),
            search_query=str(data.get("search_query", "")),
            provider_record_id=str(data.get("provider_record_id", "")),
            retrieved_at=str(data.get("retrieved_at", datetime.now(timezone.utc).isoformat())),
        )


@dataclass
class CanonicalPaperRecord:
    """Canonical schema for research papers across all academic sources."""

    record_id: str
    title: str
    authors: list[str] = field(default_factory=list)
    year: int | None = None
    doi: str | None = None
    journal: str | None = None
    issn: list[str] = field(default_factory=list)
    publisher: str | None = None
    doc_type: DocumentType = DocumentType.OTHER
    abstract: str | None = None
    language: str = "en"
    url: str | None = None
    cited_by_count: int = 0
    provenance: SearchProvenance = field(
        default_factory=lambda: SearchProvenance(source_database="unknown", search_query="")
    )
    data_quality_score: float = 0.0
    evidence_level: EvidenceLevel = EvidenceLevel.UNKNOWN
    inclusion_status: InclusionStatus = InclusionStatus.PENDING_REVIEW
    exclusion_reasons: list[str] = field(default_factory=list)
    duplicate_status: DuplicateStatus = DuplicateStatus.UNIQUE
    canonical_record_id: str | None = None
    metadata_conflicts: list[dict[str, Any]] = field(default_factory=list)
    raw_metadata: dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def generate_record_id(
        doi: str | None,
        title: str,
        authors: list[str] | None = None,
        year: int | None = None,
    ) -> str:
        """Deterministic persistent record ID generation (Persistent record ID #6)."""
        if doi and doi.strip():
            norm_doi = doi.lower().strip()
            digest = hashlib.sha256(f"doi:{norm_doi}".encode("utf-8")).hexdigest()[:16]
            return f"rec_{digest}"

        norm_title = re.sub(r"[^\w\s]", "", (title or "").lower()).strip()
        first_author = (authors[0].lower().strip() if authors else "")
        yr = str(year) if year else ""
        content_key = f"title:{norm_title}|author:{first_author}|year:{yr}"
        digest = hashlib.sha256(content_key.encode("utf-8")).hexdigest()[:16]
        return f"rec_{digest}"

    def calculate_quality_score(self) -> float:
        """Calculates completeness index from 0.0 to 100.0 (Data-quality score #22)."""
        score = 0.0
        # Title (20 pts)
        if self.title and len(self.title.strip()) > 5:
            score += 20.0
        # Authors (20 pts)
        if self.authors and len(self.authors) > 0 and self.authors[0] != "Unknown":
            score += 20.0
        # Publication Year (15 pts)
        if self.year and 1900 <= self.year <= 2030:
            score += 15.0
        # Valid DOI (15 pts)
        if self.doi and re.match(r"^10\.\d{4,9}/[-._;()/:A-Za-z0-9]+$", self.doi):
            score += 15.0
        # Journal / Venue (15 pts)
        if self.journal and len(self.journal.strip()) > 2:
            score += 15.0
        # Abstract (15 pts)
        if self.abstract and len(self.abstract.strip()) > 30:
            score += 15.0

        self.data_quality_score = round(score, 1)
        return self.data_quality_score

    def infer_evidence_level(self) -> EvidenceLevel:
        """Infers academic evidence level based on title, abstract, and keywords (#23)."""
        text = f"{self.title or ''} {self.abstract or ''}".lower()

        # Level 1: Systematic Reviews
        if any(k in text for k in ["systematic review", "meta-analysis", "prisma", "systematic literature review"]):
            self.evidence_level = EvidenceLevel.LEVEL_1_SYSTEMATIC_REVIEW
        # Level 2: Quantitative Empirical
        elif any(k in text for k in [
            "social network analysis", "sna", "indobert", "sentiment analysis", "absa",
            "machine learning", "regression", "survey", "dataset", "empirical study", "experiment"
        ]):
            self.evidence_level = EvidenceLevel.LEVEL_2_EMPIRICAL_QUANT
        # Level 3: Qualitative Empirical
        elif any(k in text for k in ["case study", "in-depth interview", "fgd", "wawancara mendalam", "etnografi"]):
            self.evidence_level = EvidenceLevel.LEVEL_3_EMPIRICAL_QUAL
        # Level 4: Conceptual Theory
        elif any(k in text for k in ["marketing 6.0", "phygital", "conceptual framework", "theoretical framework", "perspektif teoritis"]):
            self.evidence_level = EvidenceLevel.LEVEL_4_CONCEPTUAL_THEORY
        else:
            self.evidence_level = EvidenceLevel.UNKNOWN

        return self.evidence_level

    def to_dict(self) -> dict[str, Any]:
        """Convert record to dictionary, serializing enums and dataclasses."""
        data = asdict(self)
        data["doc_type"] = self.doc_type.value
        data["inclusion_status"] = self.inclusion_status.value
        data["duplicate_status"] = self.duplicate_status.value
        data["evidence_level"] = self.evidence_level.value
        data["provenance"] = self.provenance.to_dict()
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CanonicalPaperRecord:
        """Create a CanonicalPaperRecord from dictionary with missing-value normalization (#9)."""
        prov_data = data.get("provenance", {})
        provenance = SearchProvenance.from_dict(prov_data) if isinstance(prov_data, dict) else SearchProvenance(source_database="unknown", search_query="")

        # Missing-value normalization (#9)
        title = str(data.get("title") or "").strip()
        doi = data.get("doi")
        if doi:
            doi = str(doi).strip().lower()
            if doi in ["none", "null", "n/a", ""]:
                doi = None

        authors_raw = data.get("authors") or []
        authors: list[str] = []
        if isinstance(authors_raw, list):
            authors = [str(a).strip() for a in authors_raw if str(a).strip()]

        year = data.get("year")
        if year is not None:
            try:
                year = int(year)
                if not (1900 <= year <= 2030):
                    year = None
            except (ValueError, TypeError):
                year = None

        journal = data.get("journal")
        if journal:
            journal = str(journal).strip()
            if journal.lower() in ["none", "null", "n/a", ""]:
                journal = None

        issn_raw = data.get("issn") or []
        issn = [str(i).strip() for i in issn_raw if str(i).strip()] if isinstance(issn_raw, list) else []

        doc_type_raw = data.get("doc_type")
        doc_type = DocumentType(doc_type_raw) if doc_type_raw in [e.value for e in DocumentType] else DocumentType.from_raw(str(doc_type_raw))

        record_id = str(data.get("record_id") or "")
        if not record_id:
            record_id = cls.generate_record_id(doi, title, authors, year)

        record = cls(
            record_id=record_id,
            title=title,
            authors=authors,
            year=year,
            doi=doi,
            journal=journal,
            issn=issn,
            publisher=data.get("publisher"),
            doc_type=doc_type,
            abstract=data.get("abstract"),
            language=str(data.get("language", "en")),
            url=data.get("url"),
            cited_by_count=int(data.get("cited_by_count", 0)),
            provenance=provenance,
            data_quality_score=float(data.get("data_quality_score", 0.0)),
            evidence_level=EvidenceLevel(data.get("evidence_level", EvidenceLevel.UNKNOWN.value)),
            inclusion_status=InclusionStatus(data.get("inclusion_status", InclusionStatus.PENDING_REVIEW.value)),
            exclusion_reasons=list(data.get("exclusion_reasons", [])),
            duplicate_status=DuplicateStatus(data.get("duplicate_status", DuplicateStatus.UNIQUE.value)),
            canonical_record_id=data.get("canonical_record_id"),
            metadata_conflicts=list(data.get("metadata_conflicts", [])),
            raw_metadata=dict(data.get("raw_metadata", {})),
        )

        if record.data_quality_score == 0.0:
            record.calculate_quality_score()
        if record.evidence_level == EvidenceLevel.UNKNOWN:
            record.infer_evidence_level()

        return record
