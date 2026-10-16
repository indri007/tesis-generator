"""Document processing package for AI Thesis Generator & Reviewer."""

from core.document_processing.unified_extractor import (
    UnifiedDocumentExtractor,
    DocumentValidationError,
)

__all__ = ["UnifiedDocumentExtractor", "DocumentValidationError"]
