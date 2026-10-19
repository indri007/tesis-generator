from __future__ import annotations

import logging
from typing import Any, List

from .base_checker import BaseChecker, CheckResult
from .preprocessing import split_into_sentences

logger = logging.getLogger(__name__)

try:
    from sentence_transformers import SentenceTransformer, util
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logger.info("sentence-transformers not installed. SemanticChecker running in mock/fallback mode.")


class SemanticChecker(BaseChecker):
    """Pemeriksa kesamaan semantik menggunakan model Sentence-BERT multilingual."""

    name = "semantic_sbert"
    THRESHOLD = 0.85

    def __init__(
        self,
        reference_corpus: list[str],
        model_name: str = "paraphrase-multilingual-MiniLM-L12-v2",
    ):
        self.reference_corpus = [c for c in reference_corpus if c.strip()]
        self.model_name = model_name

        if SENTENCE_TRANSFORMERS_AVAILABLE and self.reference_corpus:
            try:
                self.model = SentenceTransformer(model_name)
                self.corpus_emb = self.model.encode(self.reference_corpus, convert_to_tensor=True)
            except Exception as e:
                logger.warning("Could not load SentenceTransformer model '%s': %s", model_name, e)
                self.model = None
                self.corpus_emb = None
        else:
            self.model = None
            self.corpus_emb = None

    def check(self, text: str, **kwargs: Any) -> CheckResult:
        sentences = split_into_sentences(text)
        if not sentences or not self.reference_corpus:
            return CheckResult(
                checker_name=self.name,
                score=0.0,
                verdict="clean",
                matched_segments=[],
                evidence_refs=[],
            )

        # If sentence-transformers is not available or failed to load
        if not SENTENCE_TRANSFORMERS_AVAILABLE or self.model is None or self.corpus_emb is None:
            logger.info("Sentence-BERT unavailable; skipping dense semantic check.")
            return CheckResult(
                checker_name=self.name,
                score=0.0,
                verdict="clean",
                matched_segments=[],
                evidence_refs=[],
                metadata={"status": "sentence_transformers_not_installed"},
            )

        sent_emb = self.model.encode(sentences, convert_to_tensor=True)
        sims = util.cos_sim(sent_emb, self.corpus_emb)

        matches: List[dict[str, Any]] = []
        max_score = 0.0

        for i, sent in enumerate(sentences):
            best = sims[i].max().item()
            best_idx = int(sims[i].argmax().item())
            if best >= self.THRESHOLD:
                max_score = max(max_score, best)
                src_excerpt = self.reference_corpus[best_idx] if best_idx < len(self.reference_corpus) else ""
                matches.append({
                    "text": sent,
                    "source": src_excerpt[:120],
                    "similarity": round(best, 3),
                })

        verdict = "plagiarized" if max_score >= self.THRESHOLD else "clean"
        return CheckResult(
            checker_name=self.name,
            score=round(max_score, 4),
            verdict=verdict,
            matched_segments=matches,
            evidence_refs=[],
        )
