from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, List, Optional

from .base_checker import CheckResult
from .lexical_checker import LexicalChecker
from .semantic_checker import SemanticChecker
from .ai_detector import AIDetector
from .source_repository import SourceRepository

logger = logging.getLogger(__name__)


@dataclass
class PlagiarismReport:
    """Hasil akhir audit orisinalitas naskah (plagiarisme & AI)."""
    overall_plagiarism_score: float
    overall_ai_score: float
    verdict: str  # "clean" | "suspicious" | "rejected"
    findings: List[dict[str, Any]] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)


class PlagiarismOrchestrator:
    """Mengorkestrasi seluruh checker integritas (Leksikal, Semantik, dan AI Detector)."""

    def __init__(
        self,
        reference_corpus: Optional[List[str]] = None,
        source_repo: Optional[SourceRepository] = None,
    ):
        if source_repo is not None:
            self.repo = source_repo
        else:
            self.repo = SourceRepository()
            if reference_corpus:
                for doc in reference_corpus:
                    if doc and doc.strip():
                        self.repo.add_document(doc)

        corpus = self.repo.get_all()
        if reference_corpus:
            corpus = list(dict.fromkeys(corpus + [d for d in reference_corpus if d and d.strip()]))

        self.lexical_checker = LexicalChecker(corpus)
        self.semantic_checker = SemanticChecker(corpus)
        self.ai_detector = AIDetector()

    def run(self, text: str) -> PlagiarismReport:
        """Menjalankan evaluasi leksikal, semantik, dan AI pada teks input."""
        if not text or not text.strip():
            return PlagiarismReport(
                overall_plagiarism_score=0.0,
                overall_ai_score=0.0,
                verdict="clean",
                findings=[
                    {"checker_name": self.lexical_checker.name, "score": 0.0, "verdict": "clean", "matched_segments": []},
                    {"checker_name": self.semantic_checker.name, "score": 0.0, "verdict": "clean", "matched_segments": []},
                    {"checker_name": self.ai_detector.name, "score": 0.0, "verdict": "clean", "matched_segments": []},
                ],
            )

        try:
            lex_res: CheckResult = self.lexical_checker.check(text)
        except Exception as e:
            logger.warning("Lexical check failed: %s", e)
            lex_res = CheckResult(checker_name=self.lexical_checker.name, score=0.0, verdict="clean")

        try:
            sem_res: CheckResult = self.semantic_checker.check(text)
        except Exception as e:
            logger.warning("Semantic check failed: %s", e)
            sem_res = CheckResult(checker_name=self.semantic_checker.name, score=0.0, verdict="clean")

        try:
            ai_res: CheckResult = self.ai_detector.check(text)
        except Exception as e:
            logger.warning("AI check failed: %s", e)
            ai_res = CheckResult(checker_name=self.ai_detector.name, score=0.0, verdict="clean")

        plag_score = max(lex_res.score, sem_res.score)
        ai_score = ai_res.score

        if plag_score >= 0.70 or ai_score >= 0.75:
            verdict = "rejected"
        elif plag_score >= 0.40 or ai_score >= 0.45:
            verdict = "suspicious"
        else:
            verdict = "clean"

        findings = [
            {
                "checker_name": lex_res.checker_name,
                "score": round(lex_res.score, 3),
                "verdict": lex_res.verdict,
                "matched_segments": lex_res.matched_segments,
                "evidence_refs": lex_res.evidence_refs,
            },
            {
                "checker_name": sem_res.checker_name,
                "score": round(sem_res.score, 3),
                "verdict": sem_res.verdict,
                "matched_segments": sem_res.matched_segments,
                "evidence_refs": sem_res.evidence_refs,
            },
            {
                "checker_name": ai_res.checker_name,
                "score": round(ai_res.score, 3),
                "verdict": ai_res.verdict,
                "matched_segments": ai_res.matched_segments,
                "evidence_refs": ai_res.evidence_refs,
            },
        ]

        return PlagiarismReport(
            overall_plagiarism_score=round(plag_score, 3),
            overall_ai_score=round(ai_score, 3),
            verdict=verdict,
            findings=findings,
        )
