"""Single Source of Truth re-export for ParsedDocument models.
Prevents model drift between core.ingestion and models.
"""

from models.document_model import (
    ParsedDocument,
    ParsedParagraph,
    ParsedTable,
)

__all__ = ["ParsedDocument", "ParsedParagraph", "ParsedTable"]
