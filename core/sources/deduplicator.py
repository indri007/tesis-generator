"""Multi-Tier Deduplication, Record Lineage, and Preprint-Journal Matching Engine.

Implements Phase 1 & Section A requirements:
- Deduplication by DOI (#11, #33)
- Deduplication by title (#12)
- Semantic duplicate detection (#13)
- Preprint -> journal matching (#14)
- Conference -> journal matching (#15)
- Record lineage (#16)
- Data lineage (#17)
- Manual-review queue (#20)
- Conflict detection (#21)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from core.sources.data_models import (
    CanonicalPaperRecord,
    DocumentType,
    DuplicateStatus,
)
from core.sources.doi_verifier import normalize_doi


def clean_title_for_comparison(title: str) -> str:
    """Normalizes title string by stripping punctuation, numbers, and multiple spaces."""
    if not title:
        return ""
    cleaned = re.sub(r"[^\w\s]", " ", title.lower())
    return re.sub(r"\s+", " ", cleaned).strip()


def calculate_jaccard_similarity(s1: str, s2: str) -> float:
    """Calculates token Jaccard similarity between two strings (#13)."""
    t1 = set(clean_title_for_comparison(s1).split())
    t2 = set(clean_title_for_comparison(s2).split())
    if not t1 or not t2:
        return 0.0
    return len(t1.intersection(t2)) / len(t1.union(t2))


def calculate_token_overlap_ratio(s1: str, s2: str) -> float:
    """Calculates directional token overlap ratio."""
    t1 = set(clean_title_for_comparison(s1).split())
    t2 = set(clean_title_for_comparison(s2).split())
    if not t1 or not t2:
        return 0.0
    intersection = len(t1.intersection(t2))
    return (2.0 * intersection) / (len(t1) + len(t2))


@dataclass
class DeduplicationSummary:
    total_input_records: int
    unique_records: int
    exact_duplicates: int
    candidate_duplicates: int
    preprints_matched_to_journal: int
    conferences_matched_to_journal: int
    conflicts_detected: int
    manual_review_queue: list[dict[str, Any]] = field(default_factory=list)
    audit_trail: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_input_records": self.total_input_records,
            "unique_records": self.unique_records,
            "exact_duplicates": self.exact_duplicates,
            "candidate_duplicates": self.candidate_duplicates,
            "preprints_matched_to_journal": self.preprints_matched_to_journal,
            "conferences_matched_to_journal": self.conferences_matched_to_journal,
            "conflicts_detected": self.conflicts_detected,
            "manual_review_queue_count": len(self.manual_review_queue),
            "manual_review_queue": self.manual_review_queue,
            "audit_trail": self.audit_trail,
        }


class DeduplicationEngine:
    """Executes multi-tier academic literature deduplication with metadata merging."""

    def __init__(self, exact_threshold: float = 0.88, candidate_threshold: float = 0.72):
        self.exact_threshold = exact_threshold
        self.candidate_threshold = candidate_threshold

    def deduplicate(self, records: list[CanonicalPaperRecord]) -> tuple[list[CanonicalPaperRecord], DeduplicationSummary]:
        exact_dups = 0
        candidate_dups = 0
        preprints_matched = 0
        conf_matched = 0
        conflicts_count = 0
        audit_trail: list[str] = []
        manual_review_queue: list[dict[str, Any]] = []

        # Master records kept as unique canonical representatives
        canonical_pool: list[CanonicalPaperRecord] = []
        # Fast lookup indices
        doi_to_canonical: dict[str, CanonicalPaperRecord] = {}
        title_to_canonical: dict[str, CanonicalPaperRecord] = {}

        for record in records:
            norm_doi = normalize_doi(record.doi)
            norm_title = clean_title_for_comparison(record.title)

            matched_canonical: CanonicalPaperRecord | None = None
            match_reason = ""

            # -------------------------------------------------------------
            # Tier 1: Exact DOI Matching (#11, #33)
            # -------------------------------------------------------------
            if norm_doi and norm_doi in doi_to_canonical:
                matched_canonical = doi_to_canonical[norm_doi]
                match_reason = f"Exact DOI Match ({norm_doi})"

            # -------------------------------------------------------------
            # Tier 2: Exact Normalized Title Matching (#12)
            # -------------------------------------------------------------
            if not matched_canonical and norm_title and norm_title in title_to_canonical:
                matched_canonical = title_to_canonical[norm_title]
                match_reason = "Exact Normalized Title Match"

            # -------------------------------------------------------------
            # Tier 3: Fuzzy / Semantic Duplicate Detection (#13)
            # -------------------------------------------------------------
            if not matched_canonical and len(norm_title) > 15:
                for cand in canonical_pool:
                    sim = calculate_token_overlap_ratio(record.title, cand.title)
                    if sim >= self.exact_threshold:
                        # Cross-check author surname or publication year
                        author_match = False
                        if record.authors and cand.authors:
                            rec_auth = record.authors[0].lower()
                            cand_auth = cand.authors[0].lower()
                            author_match = (rec_auth in cand_auth) or (cand_auth in rec_auth)

                        year_match = (
                            record.year is not None
                            and cand.year is not None
                            and abs(record.year - cand.year) <= 1
                        )

                        if author_match or year_match or sim >= 0.95:
                            matched_canonical = cand
                            match_reason = f"Fuzzy Title Similarity ({sim:.2f})"
                            break
                    elif sim >= self.candidate_threshold:
                        # Candidate duplicate for human review (#20)
                        candidate_dups += 1
                        record.duplicate_status = DuplicateStatus.CANDIDATE_DUPLICATE
                        record.canonical_record_id = cand.record_id
                        manual_review_queue.append({
                            "candidate_record_id": record.record_id,
                            "candidate_title": record.title,
                            "candidate_source": record.provenance.source_database,
                            "matched_canonical_id": cand.record_id,
                            "matched_canonical_title": cand.title,
                            "similarity_score": round(sim, 2),
                            "action_required": "Confirm or Reject Merge",
                        })
                        audit_trail.append(
                            f"[CANDIDATE] '{record.title[:40]}...' matches '{cand.title[:40]}...' (sim: {sim:.2f})"
                        )
                        break

            # Process duplicate if match confirmed
            if matched_canonical:
                exact_dups += 1
                record.duplicate_status = DuplicateStatus.EXACT_DUPLICATE
                record.canonical_record_id = matched_canonical.record_id

                # Tier 4 & 5: Preprint/Conference -> Journal Matching (#14, #15)
                if record.doc_type == DocumentType.PREPRINT and matched_canonical.doc_type == DocumentType.JOURNAL_ARTICLE:
                    preprints_matched += 1
                    audit_trail.append(
                        f"[PREPRINT->JOURNAL] Linked preprint {record.record_id} to journal article {matched_canonical.record_id}"
                    )
                elif record.doc_type == DocumentType.CONFERENCE_PAPER and matched_canonical.doc_type == DocumentType.JOURNAL_ARTICLE:
                    conf_matched += 1
                    audit_trail.append(
                        f"[CONF->JOURNAL] Linked conference paper {record.record_id} to journal article {matched_canonical.record_id}"
                    )

                # Conflict Detection & Metadata Enrichment (#21, #16, #17)
                self._detect_conflicts_and_enrich(matched_canonical, record)
                if record.metadata_conflicts:
                    conflicts_count += len(record.metadata_conflicts)

                audit_trail.append(
                    f"[MERGED] {record.record_id} -> {matched_canonical.record_id} via {match_reason}"
                )
            else:
                # Unique record
                if record.duplicate_status != DuplicateStatus.CANDIDATE_DUPLICATE:
                    record.duplicate_status = DuplicateStatus.UNIQUE
                record.canonical_record_id = record.record_id
                canonical_pool.append(record)

                if norm_doi:
                    doi_to_canonical[norm_doi] = record
                if norm_title:
                    title_to_canonical[norm_title] = record

        summary = DeduplicationSummary(
            total_input_records=len(records),
            unique_records=len(canonical_pool),
            exact_duplicates=exact_dups,
            candidate_duplicates=candidate_dups,
            preprints_matched_to_journal=preprints_matched,
            conferences_matched_to_journal=conf_matched,
            conflicts_detected=conflicts_count,
            manual_review_queue=manual_review_queue,
            audit_trail=audit_trail,
        )

        return canonical_pool, summary

    @staticmethod
    def _detect_conflicts_and_enrich(canonical: CanonicalPaperRecord, duplicate: CanonicalPaperRecord) -> None:
        """Detects discrepancies between records and enriches canonical metadata (#21)."""
        conflicts: list[dict[str, Any]] = []

        # 1. Year discrepancy
        if canonical.year and duplicate.year and canonical.year != duplicate.year:
            conflicts.append({
                "field": "year",
                "canonical_val": canonical.year,
                "duplicate_val": duplicate.year,
                "source_duplicate": duplicate.provenance.source_database,
            })

        # 2. Journal discrepancy
        if canonical.journal and duplicate.journal and canonical.journal.lower() != duplicate.journal.lower():
            conflicts.append({
                "field": "journal",
                "canonical_val": canonical.journal,
                "duplicate_val": duplicate.journal,
                "source_duplicate": duplicate.provenance.source_database,
            })

        # Enrich missing fields in canonical from duplicate
        if not canonical.abstract and duplicate.abstract:
            canonical.abstract = duplicate.abstract
        if not canonical.doi and duplicate.doi:
            canonical.doi = duplicate.doi
        if not canonical.journal and duplicate.journal:
            canonical.journal = duplicate.journal
        if canonical.cited_by_count == 0 and duplicate.cited_by_count > 0:
            canonical.cited_by_count = duplicate.cited_by_count
        if not canonical.url and duplicate.url:
            canonical.url = duplicate.url

        # Store conflicts in duplicate for audit lineage (#16)
        duplicate.metadata_conflicts = conflicts
        # Re-evaluate quality score after enrichment
        canonical.calculate_quality_score()
