"""Academic Evaluation Metrics & Inter-Annotator Agreement Engine.

Computes precision, recall, F1-score, support, confusion counts per category,
and inter-annotator agreement (Cohen's Kappa & Percent Agreement) with rigorous
handling of zero denominators (displaying undefined / None instead of deceptive 0.0).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from core.evaluation.matcher import MatchResult, MatchVerdict, normalize_category


@dataclass
class CategoryMetrics:
    category: str
    true_positives: int = 0
    false_positives: int = 0
    false_negatives: int = 0
    wrong_locations: int = 0
    wrong_severities: int = 0
    support: int = 0  # Number of reference ground truth items

    @property
    def precision(self) -> float | None:
        """Precision = TP / (TP + FP). Returns None if denominator is 0."""
        denom = self.true_positives + self.false_positives
        if denom == 0:
            return None
        return round(self.true_positives / denom, 4)

    @property
    def recall(self) -> float | None:
        """Recall = TP / (TP + FN). Returns None if denominator is 0."""
        denom = self.true_positives + self.false_negatives
        if denom == 0:
            return None
        return round(self.true_positives / denom, 4)

    @property
    def f1_score(self) -> float | None:
        """F1 = 2 * (P * R) / (P + R). Returns None if undefined or denominator is 0."""
        p = self.precision
        r = self.recall
        if p is None or r is None or (p + r) == 0:
            return None
        return round(2 * (p * r) / (p + r), 4)

    def to_dict(self) -> dict[str, Any]:
        p = self.precision
        r = self.recall
        f1 = self.f1_score
        return {
            "category": self.category,
            "true_positives": self.true_positives,
            "false_positives": self.false_positives,
            "false_negatives": self.false_negatives,
            "wrong_locations": self.wrong_locations,
            "wrong_severities": self.wrong_severities,
            "support": self.support,
            "precision": round(p * 100, 2) if p is not None else None,
            "recall": round(r * 100, 2) if r is not None else None,
            "f1_score": round(f1 * 100, 2) if f1 is not None else None,
            "precision_display": f"{p * 100:.1f}%" if p is not None else "N/A (undefined)",
            "recall_display": f"{r * 100:.1f}%" if r is not None else "N/A (undefined)",
            "f1_display": f"{f1 * 100:.1f}%" if f1 is not None else "N/A (undefined)",
        }


@dataclass
class BenchmarkEvaluationSummary:
    total_documents: int
    total_reference_findings: int
    total_detected_findings: int
    per_category: dict[str, CategoryMetrics]
    micro_metrics: dict[str, Any]
    macro_metrics: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_documents": self.total_documents,
            "total_reference_findings": self.total_reference_findings,
            "total_detected_findings": self.total_detected_findings,
            "per_category": {k: v.to_dict() for k, v in self.per_category.items()},
            "micro_metrics": self.micro_metrics,
            "macro_metrics": self.macro_metrics,
        }


def compute_category_metrics(match_results: list[MatchResult]) -> dict[str, CategoryMetrics]:
    """Computes category-wise confusion and performance metrics."""
    categories: dict[str, CategoryMetrics] = {}

    def get_cat_metrics(cat_name: str) -> CategoryMetrics:
        c = normalize_category(cat_name)
        if c not in categories:
            categories[c] = CategoryMetrics(category=c)
        return categories[c]

    for m in match_results:
        cat_str = "general"
        if m.reference:
            cat_str = m.reference.audit_category
        elif m.detected:
            cat_str = m.detected.get("category", "general")

        metric = get_cat_metrics(cat_str)

        if m.verdict == MatchVerdict.TRUE_POSITIVE:
            metric.true_positives += 1
            metric.support += 1
        elif m.verdict == MatchVerdict.FALSE_POSITIVE:
            metric.false_positives += 1
        elif m.verdict == MatchVerdict.FALSE_NEGATIVE:
            metric.false_negatives += 1
            metric.support += 1
        elif m.verdict == MatchVerdict.WRONG_LOCATION:
            metric.wrong_locations += 1
            # Wrong location counts as false positive + false negative
            metric.false_positives += 1
            metric.false_negatives += 1
            metric.support += 1
        elif m.verdict == MatchVerdict.WRONG_SEVERITY:
            metric.wrong_severities += 1
            metric.false_positives += 1
            metric.false_negatives += 1
            metric.support += 1

    return categories


def compute_micro_macro_metrics(category_metrics: dict[str, CategoryMetrics]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Calculates micro-averaged and macro-averaged metrics across all categories."""
    total_tp = sum(m.true_positives for m in category_metrics.values())
    total_fp = sum(m.false_positives for m in category_metrics.values())
    total_fn = sum(m.false_negatives for m in category_metrics.values())
    total_support = sum(m.support for m in category_metrics.values())

    # Micro averages
    micro_p = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else None
    micro_r = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else None
    micro_f1 = (
        2 * micro_p * micro_r / (micro_p + micro_r)
        if (micro_p is not None and micro_r is not None and (micro_p + micro_r) > 0)
        else None
    )

    micro = {
        "true_positives": total_tp,
        "false_positives": total_fp,
        "false_negatives": total_fn,
        "support": total_support,
        "precision": round(micro_p * 100, 2) if micro_p is not None else None,
        "recall": round(micro_r * 100, 2) if micro_r is not None else None,
        "f1_score": round(micro_f1 * 100, 2) if micro_f1 is not None else None,
        "precision_display": f"{micro_p * 100:.1f}%" if micro_p is not None else "N/A",
        "recall_display": f"{micro_r * 100:.1f}%" if micro_r is not None else "N/A",
        "f1_display": f"{micro_f1 * 100:.1f}%" if micro_f1 is not None else "N/A",
    }

    # Macro averages (average over categories that have defined metrics)
    defined_p = [m.precision for m in category_metrics.values() if m.precision is not None]
    defined_r = [m.recall for m in category_metrics.values() if m.recall is not None]
    defined_f1 = [m.f1_score for m in category_metrics.values() if m.f1_score is not None]

    macro_p = sum(defined_p) / len(defined_p) if defined_p else None
    macro_r = sum(defined_r) / len(defined_r) if defined_r else None
    macro_f1 = sum(defined_f1) / len(defined_f1) if defined_f1 else None

    macro = {
        "categories_evaluated": len(category_metrics),
        "precision": round(macro_p * 100, 2) if macro_p is not None else None,
        "recall": round(macro_r * 100, 2) if macro_r is not None else None,
        "f1_score": round(macro_f1 * 100, 2) if macro_f1 is not None else None,
        "precision_display": f"{macro_p * 100:.1f}%" if macro_p is not None else "N/A",
        "recall_display": f"{macro_r * 100:.1f}%" if macro_r is not None else "N/A",
        "f1_display": f"{macro_f1 * 100:.1f}%" if macro_f1 is not None else "N/A",
    }

    return micro, macro


def compute_cohens_kappa(
    reviewer_1_labels: list[str],
    reviewer_2_labels: list[str],
) -> dict[str, Any]:
    """Computes Cohen's Kappa coefficient of inter-annotator agreement between two reviewers.

    Kappa = (Po - Pe) / (1 - Pe)
    where:
      Po = relative observed agreement among raters
      Pe = hypothetical probability of chance agreement
    """
    if len(reviewer_1_labels) != len(reviewer_2_labels) or len(reviewer_1_labels) == 0:
        return {
            "sample_count": len(reviewer_1_labels),
            "observed_agreement": None,
            "chance_agreement": None,
            "kappa": None,
            "agreement_strength": "N/A (insufficient or mismatched data)",
            "disagreements": [],
        }

    n = len(reviewer_1_labels)
    agreements = sum(1 for a, b in zip(reviewer_1_labels, reviewer_2_labels) if a == b)
    po = agreements / n

    # Find unique labels
    all_labels = sorted(list(set(reviewer_1_labels + reviewer_2_labels)))

    # Compute marginal probabilities
    pe = 0.0
    for label in all_labels:
        p1 = sum(1 for a in reviewer_1_labels if a == label) / n
        p2 = sum(1 for b in reviewer_2_labels if b == label) / n
        pe += p1 * p2

    # Kappa tidak terdefinisi jika peluang kesepakatan acak = 1.
    # Jangan mengubah kondisi matematis ini menjadi skor 0 atau 1.
    if pe >= 1.0 or (1.0 - pe) <= 1e-12:
        kappa = None
        strength = "N/A (kappa undefined: expected agreement is 1)"
    else:
        kappa = (po - pe) / (1.0 - pe)

        # Landis & Koch (1977) interpretation; descriptive, not universal.
        if kappa < 0:
            strength = "Poor (less than chance agreement)"
        elif kappa <= 0.20:
            strength = "Slight agreement"
        elif kappa <= 0.40:
            strength = "Fair agreement"
        elif kappa <= 0.60:
            strength = "Moderate agreement"
        elif kappa <= 0.80:
            strength = "Substantial agreement"
        else:
            strength = "Almost perfect agreement"

    disagreements = [
        {"item_index": idx, "reviewer_1": a, "reviewer_2": b}
        for idx, (a, b) in enumerate(zip(reviewer_1_labels, reviewer_2_labels))
        if a != b
    ]

    return {
        "sample_count": n,
        "observed_agreement": round(po * 100, 2),
        "chance_agreement": round(pe * 100, 2),
        "kappa": round(kappa, 4) if kappa is not None else None,
        "agreement_strength": strength,
        "disagreements_count": len(disagreements),
        "disagreements": disagreements,
    }
