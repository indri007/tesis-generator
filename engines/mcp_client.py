"""Re-export of MCPClientWrapper in engines package."""

from core.integrations.mcp_client import (
    MCPClientWrapper,
    ScopusPaperResult,
    SintaJournalResult,
)

__all__ = ["MCPClientWrapper", "ScopusPaperResult", "SintaJournalResult"]
