"""Unit tests for Similarity Benchmark Evaluation Framework & Golden Dataset."""

from __future__ import annotations

from core.evaluation.similarity_benchmark import (
    GOLDEN_SIMILARITY_DATASET,
    BenchmarkPair,
    ThresholdMetric,
    evaluate_similarity_thresholds,
    format_benchmark_summary,
)


def test_golden_dataset_categories_and_completeness():
    assert len(GOLDEN_SIMILARITY_DATASET) >= 8

    categories = {pair.category for pair in GOLDEN_SIMILARITY_DATASET}
    required_categories = {
        "IDENTICAL",
        "REORDERED",
        "LIGHT_PARAPHRASE",
        "BOILERPLATE",
        "SYNONYMS",
        "PARTIAL_OVERLAP",
        "DISJOINT",
        "EMPTY",
    }
    assert required_categories.issubset(categories)

    for pair in GOLDEN_SIMILARITY_DATASET:
        assert isinstance(pair, BenchmarkPair)
        assert pair.pair_id
        assert pair.category
        assert isinstance(pair.expected_similar, bool)


def test_evaluate_similarity_thresholds():
    thresholds = [0.40, 0.60, 0.70, 0.80]
    metrics = evaluate_similarity_thresholds(
        pairs=GOLDEN_SIMILARITY_DATASET,
        thresholds=thresholds,
    )

    assert len(metrics) == len(thresholds)

    for m in metrics:
        assert isinstance(m, ThresholdMetric)
        assert m.threshold in thresholds
        total = m.tp + m.fp + m.tn + m.fn
        assert total == len(GOLDEN_SIMILARITY_DATASET)

        # Precision calculation consistency
        if (m.tp + m.fp) > 0:
            assert m.precision == round(m.tp / (m.tp + m.fp), 4)
        else:
            assert m.precision is None

        # Recall calculation consistency
        if (m.tp + m.fn) > 0:
            assert m.recall == round(m.tp / (m.tp + m.fn), 4)
        else:
            assert m.recall is None


def test_format_benchmark_summary_output():
    metrics = evaluate_similarity_thresholds(
        pairs=GOLDEN_SIMILARITY_DATASET,
        thresholds=[0.60, 0.70],
    )
    summary_md = format_benchmark_summary(metrics)

    assert "Threshold" in summary_md
    assert "Precision" in summary_md
    assert "Recall" in summary_md
    assert "F1-Score" in summary_md
    assert "0.6" in summary_md
    assert "0.7" in summary_md
