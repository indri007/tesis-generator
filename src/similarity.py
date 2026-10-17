"""Pure-Python similarity shim and API compatibility facade.

Delegates to `core.clones.similarity_plagiarism.compute_cosine_similarity`.
This measures lexical token frequency similarity, NOT semantic comprehension.
"""

from core.clones.similarity_plagiarism import (
    SentenceTransformersAdapter,
    compute_cosine_similarity,
    normalize_and_tokenize,
)


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

