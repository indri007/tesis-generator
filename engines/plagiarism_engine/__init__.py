from __future__ import annotations

from .orchestrator import PlagiarismOrchestrator, PlagiarismReport
from .base_checker import BaseChecker, CheckResult
from .lexical_checker import LexicalChecker
from .semantic_checker import SemanticChecker
from .ai_detector import AIDetector
from .source_repository import SourceRepository

__all__ = [
    "PlagiarismOrchestrator",
    "PlagiarismReport",
    "BaseChecker",
    "CheckResult",
    "LexicalChecker",
    "SemanticChecker",
    "AIDetector",
    "SourceRepository",
]
