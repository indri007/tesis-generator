from __future__ import annotations

import logging
import math
from collections import Counter
from typing import Any, List

from .base_checker import BaseChecker, CheckResult
from .preprocessing import preprocess_indonesian, split_into_sentences

logger = logging.getLogger(__name__)

# Check if sklearn is installed
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.info("scikit-learn not installed. Using pure-Python TF-IDF / Cosine Similarity fallback.")


def _pure_python_cosine_similarity(text_a: str, text_b: str) -> float:
    """Fallback cosine similarity computation without requiring scikit-learn."""
    tokens_a = text_a.split()
    tokens_b = text_b.split()
    if not tokens_a or not tokens_b:
        return 0.0

    vec_a = Counter(tokens_a)
    vec_b = Counter(tokens_b)

    common = set(vec_a.keys()) & set(vec_b.keys())
    if not common:
        return 0.0

    dot = sum(vec_a[k] * vec_b[k] for k in common)
    mag_a = math.sqrt(sum(v * v for v in vec_a.values()))
    mag_b = math.sqrt(sum(v * v for v in vec_b.values()))
    denom = mag_a * mag_b
    return (dot / denom) if denom > 0 else 0.0


class LexicalChecker(BaseChecker):
    """Memeriksa kesamaan leksikal teks menggunakan TF-IDF dan Cosine Similarity."""

    name = "lexical_tfidf"
    THRESHOLD = 0.75  # ambang batas kecurigaan

    def __init__(self, reference_corpus: list[str]):
        self.raw_corpus = reference_corpus or []
        self.corpus = [preprocess_indonesian(t) for t in self.raw_corpus if t.strip()]

        if not self.corpus:
            self.corpus = [""]

        if SKLEARN_AVAILABLE:
            try:
                self.vectorizer = TfidfVectorizer()
                self.corpus_matrix = self.vectorizer.fit_transform(self.corpus)
            except Exception as e:
                logger.warning("Failed to initialize TfidfVectorizer (%s). Falling back to pure Python.", e)
                self.vectorizer = None
                self.corpus_matrix = None
        else:
            self.vectorizer = None
            self.corpus_matrix = None

    def check(self, text: str, **kwargs: Any) -> CheckResult:
        sentences = split_into_sentences(text)
        matches: List[dict[str, Any]] = []
        max_score = 0.0

        if not self.corpus or self.corpus == [""]:
            return CheckResult(
                checker_name=self.name,
                score=0.0,
                verdict="clean",
                matched_segments=[],
                evidence_refs=[],
            )

        for sent in sentences:
            proc = preprocess_indonesian(sent)
            if not proc:
                continue

            if self.vectorizer is not None and self.corpus_matrix is not None:
                try:
                    vec = self.vectorizer.transform([proc])
                    sims = cosine_similarity(vec, self.corpus_matrix)[0]
                    idx = int(sims.argmax())
                    score = float(sims[idx])
                except Exception:
                    # Fallback to pure python
                    idx = 0
                    score = 0.0
                    for c_idx, c_doc in enumerate(self.corpus):
                        s = _pure_python_cosine_similarity(proc, c_doc)
                        if s > score:
                            score = s
                            idx = c_idx
            else:
                idx = 0
                score = 0.0
                for c_idx, c_doc in enumerate(self.corpus):
                    s = _pure_python_cosine_similarity(proc, c_doc)
                    if s > score:
                        score = s
                        idx = c_idx

            if score >= self.THRESHOLD:
                max_score = max(max_score, score)
                src_excerpt = self.raw_corpus[idx] if idx < len(self.raw_corpus) else self.corpus[idx]
                matches.append({
                    "text": sent,
                    "source": src_excerpt[:120],
                    "similarity": round(score, 3),
                })

        verdict = "plagiarized" if max_score >= self.THRESHOLD else "clean"
        return CheckResult(
            checker_name=self.name,
            score=round(max_score, 4),
            verdict=verdict,
            matched_segments=matches,
            evidence_refs=[],
        )
