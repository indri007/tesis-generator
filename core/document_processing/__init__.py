"""Document processing package for AI Thesis Generator & Reviewer."""

from core.document_processing.unified_extractor import (
    DocumentValidationError,
    UnifiedDocumentExtractor,
)

__all__ = ["UnifiedDocumentExtractor", "DocumentValidationError"]
