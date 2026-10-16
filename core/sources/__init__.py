"""Core Sources and Literature Ingestion Package."""

from core.sources.core_data_engine import CoreDataEngine
from core.sources.data_models import (
    CanonicalPaperRecord,
    DocumentType,
    DuplicateStatus,
    EvidenceLevel,
    InclusionStatus,
    SearchProvenance,
)
from core.sources.deduplicator import DeduplicationEngine, DeduplicationSummary
from core.sources.doi_verifier import (
    check_doi_resolution,
    generate_doi_audit_report,
    normalize_doi,
    validate_doi_syntax,
)
from core.sources.query_registry import PipelineConfig, QueryExecutionEntry, QueryRegistry
from core.sources.text_processor import (
    clean_abstract,
    detect_language,
    normalize_text,
    reconstruct_openalex_inverted_index,
    segment_sentences,
)

__all__ = [
    "CanonicalPaperRecord",
    "CoreDataEngine",
    "DeduplicationEngine",
    "DeduplicationSummary",
    "DocumentType",
    "DuplicateStatus",
    "EvidenceLevel",
    "InclusionStatus",
    "PipelineConfig",
    "QueryExecutionEntry",
    "QueryRegistry",
    "SearchProvenance",
    "check_doi_resolution",
    "clean_abstract",
    "detect_language",
    "generate_doi_audit_report",
    "normalize_doi",
    "normalize_text",
    "reconstruct_openalex_inverted_index",
    "segment_sentences",
    "validate_doi_syntax",
]
