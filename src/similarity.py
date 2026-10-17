"""Pure-Python similarity shim and API compatibility facade.

Delegates to `core.clones.similarity_plagiarism.compute_cosine_similarity`.
This measures lexical token frequency similarity, NOT semantic comprehension.
"""

try:
    from core.clones.similarity_plagiarism import (
        SentenceTransformersAdapter,
        compute_cosine_similarity,
        normalize_and_tokenize,
    )
except ImportError:
    try:
        from core.evaluation.document_integrity_engine import (
            compute_cosine_similarity,
            normalize_and_tokenize,
        )
        SentenceTransformersAdapter = None  # type: ignore[assignment, misc]
    except ImportError:
        import math
        import re
        import unicodedata
        from collections import Counter

        def normalize_and_tokenize(text: str) -> list[str]:
            if text is None:
                return []
            if not isinstance(text, str):
                raise TypeError(f"Expected string input, got {type(text).__name__}")
            if not text.strip():
                return []
            normalized = unicodedata.normalize("NFKC", text)
            return re.findall(r"\b[\w-]+\b", normalized.lower(), flags=re.UNICODE)

        def compute_cosine_similarity(text_a: str, text_b: str) -> float:
            tokens_a = normalize_and_tokenize(text_a)
            tokens_b = normalize_and_tokenize(text_b)
            if not tokens_a or not tokens_b:
                return 0.0
            if tokens_a == tokens_b:
                return 1.0
            vec_a = Counter(tokens_a)
            vec_b = Counter(tokens_b)
            common_keys = set(vec_a.keys()) & set(vec_b.keys())
            if not common_keys:
                return 0.0
            dot_product = sum(vec_a[k] * vec_b[k] for k in common_keys)
            sum_a = sum(v * v for v in vec_a.values())
            sum_b = sum(v * v for v in vec_b.values())
            denom = math.sqrt(sum_a) * math.sqrt(sum_b)
            if denom <= 0.0 or not math.isfinite(denom):
                return 0.0
            score = dot_product / denom
            if not math.isfinite(score):
                return 0.0
            return max(0.0, min(1.0, float(score)))

        SentenceTransformersAdapter = None  # type: ignore[assignment, misc]


def similarity(text_a: str, text_b: str, method: str = "lexical") -> float:
    """Compute text similarity score strictly in [0.0, 1.0].

    Note:
        - Lexical cosine similarity measures lexical token frequency overlap,
          NOT semantic understanding or paraphrase comprehension.
        - Similarity scores must NOT be equated with plagiarism percentages,
          proof of plagiarism, or AI-generated probability.
    """
    if method == "lexical":
        return compute_cosine_similarity(text_a, text_b)
    elif method == "semantic":
        # Opt-in lazy adapter requiring external sentence-transformers package
        adapter = SentenceTransformersAdapter()
        return adapter.similarity(text_a, text_b)
    else:
        raise ValueError(f"Unknown similarity method: {method}. Use 'lexical' or 'semantic'.")


def get_default_threshold(config_path: str = "config.yaml") -> float:
    """Reads the uncalibrated initial threshold from config if present, or returns default 0.85.

    Note:
        This is an uncalibrated lexical heuristic and must NOT be used as an automated
        plagiarism verdict or definitive academic integrity decision.
    """
    try:
        from pathlib import Path

        import yaml

        p = Path(config_path)
        if p.exists():
            with open(p, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            sim_cfg = data.get("similarity", {})
            val = sim_cfg.get("initial_uncalibrated_threshold", 0.85)
            return float(val)
    except Exception:
        pass
    return 0.85


__all__ = [
    "similarity",
    "compute_cosine_similarity",
    "normalize_and_tokenize",
    "SentenceTransformersAdapter",
    "get_default_threshold",
]

