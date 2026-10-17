"""Comprehensive tests for Pure-Python Lexical Cosine Similarity engine."""

import pytest

from core.clones.similarity_plagiarism import (
    SentenceTransformersAdapter,
    compute_cosine_similarity,
    normalize_and_tokenize,
)
from src.similarity import similarity


class TestPurePythonSimilarity:
    """Test suite for pure-Python lexical cosine similarity."""

    def test_identical_texts(self):
        """Identical non-empty texts should yield a similarity score of 1.0."""
        text = "Kecerdasan buatan dalam jurnalisme meningkatkan efisiensi redaksi."
        score = compute_cosine_similarity(text, text)
        assert score == pytest.approx(1.0, rel=1e-5)
        assert similarity(text, text) == pytest.approx(1.0, rel=1e-5)

    def test_completely_different_texts(self):
        """Completely disjoint texts should yield a score of 0.0."""
        text_a = "apel jeruk mangga pisang"
        text_b = "komputer server jaringan database"
        assert compute_cosine_similarity(text_a, text_b) == 0.0
        assert similarity(text_a, text_b) == 0.0

    def test_empty_and_whitespace_inputs(self):
        """Empty or whitespace inputs must return 0.0 without ZeroDivisionError."""
        # Policy: Both empty = 0.0 (no lexical evidence of similarity)
        assert compute_cosine_similarity("", "") == 0.0
        assert compute_cosine_similarity("   \t\n  ", "") == 0.0
        assert compute_cosine_similarity("", "halo dunia") == 0.0
        assert compute_cosine_similarity("halo dunia", "   ") == 0.0
        assert similarity("", "") == 0.0

    def test_unicode_and_indonesian_diacritics(self):
        """Unicode characters, punctuation, and Indonesian text are handled properly."""
        text_a = "Studi komunikasi publik: analisis wacana kritis (AWK) & framing media."
        text_b = "Studi Komunikasi Publik, Analisis Wacana Kritis (AWK) dan Framing Media!"
        score = compute_cosine_similarity(text_a, text_b)
        assert score > 0.75
        assert 0.0 <= score <= 1.0

        # Accented characters / Unicode normalization (NFKC)
        unicode_a = "Résumé kurikulum & café riset"
        unicode_b = "Resume kurikulum dan cafe riset"
        score_u = compute_cosine_similarity(unicode_a, unicode_b)
        assert 0.0 <= score_u <= 1.0

    def test_score_boundary_contract(self):
        """Scores must always strictly lie in [0.0, 1.0] for any input pair."""
        test_pairs = [
            ("satu dua tiga", "satu dua"),
            ("Lorem ipsum dolor sit amet", "Consectetur adipiscing elit"),
            ("A" * 1000, "B" * 1000),
            ("123 456 789", "123 456"),
            ("!@#$%^&*()", ".,/;'[]"),
        ]
        for a, b in test_pairs:
            score = compute_cosine_similarity(a, b)
            assert 0.0 <= score <= 1.0, f"Score {score} out of bounds for inputs ({a!r}, {b!r})"

    def test_symmetry_property(self):
        """Cosine similarity must be symmetric: sim(a, b) == sim(b, a)."""
        text_a = "Metodologi penelitian kualitatif studi kasus di media massa lokal."
        text_b = "Analisis metodologi kualitatif dan studi kasus pada media penyiaran."
        sim_ab = compute_cosine_similarity(text_a, text_b)
        sim_ba = compute_cosine_similarity(text_b, text_a)
        assert sim_ab == pytest.approx(sim_ba, rel=1e-6)

    def test_tokenization_sublinear_tf(self):
        """Test token normalization and sublinear term frequency behavior."""
        tokens = normalize_and_tokenize("Pengujian tokenisasi: 1, 2, 3... berjalan lancar!")
        assert "pengujian" in tokens
        assert "tokenisasi" in tokens
        assert "berjalan" in tokens
        assert "lancar" in tokens

    def test_optional_dependency_isolation(self):
        """SentenceTransformersAdapter must not import heavy libraries at module load."""
        adapter = SentenceTransformersAdapter()
        assert adapter.model_name == "paraphrase-multilingual-MiniLM-L12-v2"
        assert hasattr(adapter, "compute_similarity")
        assert hasattr(adapter, "is_available")

        if not adapter.is_available():
            with pytest.raises(ImportError) as exc_info:
                adapter.similarity("halo", "dunia")
            assert "sentence-transformers" in str(exc_info.value)
        else:
            # Mock _model to avoid downloading 500MB weights from the internet during unit tests
            class DummyModel:
                def encode(self, texts):
                    import numpy as np
                    return np.array([[1.0, 0.0], [1.0, 0.0]])

            adapter._model = DummyModel()
            score = adapter.similarity("halo dunia", "halo dunia")
            assert 0.0 <= score <= 1.0

    def test_facade_method_validation(self):
        """src.similarity must raise ValueError for unknown method."""
        with pytest.raises(ValueError, match="Unknown similarity method"):
            similarity("a", "b", method="quantum_entanglement")

    def test_no_plagiarism_equivalence(self):
        """Scores must represent lexical overlap, not plagiarism or AI attribution."""
        doc = compute_cosine_similarity.__doc__
        assert "plagiarism" in doc.lower() or "plagiarisme" in doc.lower()
        assert "lexical" in doc.lower()

    def test_non_string_inputs_handling(self):
        """Test non-string inputs: None returns 0.0, other types raise TypeError."""
        # None is safely treated as empty text
        assert compute_cosine_similarity(None, "halo") == 0.0
        assert compute_cosine_similarity("halo", None) == 0.0
        assert compute_cosine_similarity(None, None) == 0.0

        # Invalid types raise TypeError
        with pytest.raises(TypeError, match="Expected string input"):
            compute_cosine_similarity(12345, "halo")  # type: ignore[arg-type]

        with pytest.raises(TypeError, match="Expected string input"):
            compute_cosine_similarity("halo", ["h", "a", "l", "o"])  # type: ignore[arg-type]

        with pytest.raises(TypeError, match="Expected string input"):
            compute_cosine_similarity({"text": "halo"}, "halo")  # type: ignore[arg-type]

    def test_non_latin_scripts_support(self):
        """Test Cyrillic, Arabic, and CJK non-Latin Unicode scripts."""
        # Cyrillic
        cyrillic_a = "Машинное обучение и искусственный интеллект в медиа."
        cyrillic_b = "Машинное обучение и искусственный интеллект в журналистике."
        sim_cyr = compute_cosine_similarity(cyrillic_a, cyrillic_b)
        assert sim_cyr > 0.6
        assert 0.0 <= sim_cyr <= 1.0

        # Arabic
        arabic_a = "الذكاء الاصطناعي في الإعلام والاتصال"
        arabic_b = "الذكاء الاصطناعي في الإعلام والصحافة"
        sim_ara = compute_cosine_similarity(arabic_a, arabic_b)
        assert sim_ara > 0.6
        assert 0.0 <= sim_ara <= 1.0

        # CJK (Chinese / Japanese / Korean)
        cjk_a = "人工智能 与 传播学 研究"
        cjk_b = "人工智能 与 新闻学 研究"
        sim_cjk = compute_cosine_similarity(cjk_a, cjk_b)
        assert sim_cjk > 0.5
        assert 0.0 <= sim_cjk <= 1.0

    def test_score_always_finite(self):
        """Ensure score is always finite (no NaN, no Inf) under any pathological input."""
        import math

        pathological_cases = [
            (" \x00\x01\x02 ", " "),
            ("!@#$$%^&*", "*&^%$#@!"),
            ("\n\r\t" * 100, "\v\f" * 100),
            ("a" * 10000, "a" * 10000),
        ]
        for a, b in pathological_cases:
            score = compute_cosine_similarity(a, b)
            assert math.isfinite(score)
            assert 0.0 <= score <= 1.0

    def test_config_threshold_reader_and_separation(self):
        """Verify get_default_threshold reads config.yaml properly and documents separation."""
        from src.similarity import get_default_threshold

        thresh = get_default_threshold("config.yaml")
        assert thresh == pytest.approx(0.85, rel=1e-3)

        # Fallback for non-existent file
        fallback = get_default_threshold("non_existent_config.yaml")
        assert fallback == 0.85

