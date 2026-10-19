from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List, Literal

from auditors.finding import Finding, PriorityType, SeverityType


@dataclass
class PlagiarismFinding(Finding):
    """Model temuan khusus pelanggaran integritas akademik (Plagiarisme & Kemiripan Teks)."""

    similarity_score: float = 0.0
    matched_source: str = ""
    detection_method: str = "lexical_tfidf"  # "lexical_tfidf" | "semantic_sbert" | "aegis"
    matched_segments: List[dict[str, Any]] = field(default_factory=list)

    def __post_init__(self):
        self.category = "plagiarism"
        # Auto-assign severity & priority berdasarkan skor kemiripan
        if self.similarity_score >= 0.75:
            self.severity = "ERROR"
            self.priority = "PRIORITAS 1"
        elif self.similarity_score >= 0.40:
            self.severity = "WARNING"
            self.priority = "PRIORITAS 2"
        else:
            self.severity = "INFO"
            self.priority = "INFO/PASS"


@dataclass
class AIGenerationFinding(Finding):
    """Model temuan khusus indikasi teks hasil generasi AI (AI-Generated Content)."""

    ai_probability: float = 0.0
    perplexity_score: float = 0.0
    burstiness_score: float = 0.0
    detection_method: str = "perplexity_burstiness"

    def __post_init__(self):
        self.category = "ai_generated"
        if self.ai_probability >= 0.70:
            self.severity = "ERROR"
            self.priority = "PRIORITAS 1"
        elif self.ai_probability >= 0.40:
            self.severity = "WARNING"
            self.priority = "PRIORITAS 2"
        else:
            self.severity = "INFO"
            self.priority = "INFO/PASS"
