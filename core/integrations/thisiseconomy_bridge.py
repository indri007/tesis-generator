"""ThisIsEconomy Research Monorepo Bridge & Thesis Alignment Engine (Phase 5).

Bridges empirical research artifacts from /Users/jevin/ThisIsEconomy:
1. Social Network Analysis (SNA): Degree, Betweenness, Louvain Community detection.
2. IndoBERT Deep Learning: Macro/Weighted F1, 9 Emotion distribution (Joy, Trust, Anger, Fear, Sadness, etc.).
3. Sarcasm & Irony: Labeled validation data and detection heuristics.
4. ABSA & Marketing 6.0: Aspect-Based Sentiment Analysis and Phygital Public Communication.
5. MBG (Makan Bergizi Gratis) Policy Communication Context.

Computes:
- Thesis Alignment Score (0 - 100%)
- Component Coverage Index across the 8 thesis dimensions.
- Literature Gap & Conceptual Alignment Matrix for Bab II.
"""

from __future__ import annotations

import csv
import json
import os
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

THIS_IS_ECONOMY_DEFAULT_PATH = Path("/Users/jevin/ThisIsEconomy")


@dataclass
class ThesisEmpiricalBaseline:
    """Empirical baseline metrics extracted from the ThisIsEconomy research pipeline."""

    total_nodes: int = 971
    total_edges: int = 1540
    communities_detected: int = 12
    top_central_actors: list[str] = field(default_factory=lambda: ["Sekjebn", "prabowo", "gibran_rakabuming", "kemdikbud"])
    indobert_accuracy: float = 0.794
    indobert_f1_weighted: float = 0.785
    indobert_emotions: list[str] = field(default_factory=lambda: [
        "neutral", "disgust", "anger", "joy", "trust", "fear", "sadness", "surprise", "anticipation"
    ])
    sarcasm_instances_analyzed: int = 3395
    sarcasm_prevalence_pct: float = 9.28  # 315 / 3395
    provenance: str = "ThisIsEconomy_empirical_results"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ThesisAlignmentResult:
    """Alignment score and dimensional coverage of a literature paper or corpus."""

    record_id: str
    title: str
    alignment_score: float  # 0.0 - 100.0%
    matched_dimensions: list[str]
    missing_dimensions: list[str]
    relevance_level: str  # "HIGHLY_ALIGNED" | "MODERATELY_ALIGNED" | "PERIPHERAL" | "UNALIGNED"
    gap_justification: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ThisIsEconomyBridge:
    """Connects the empirical thesis codebase with manuscript literature auditing."""

    # 8 Core Pillars of the Thesis Taxonomy (Sections G & I)
    THESIS_DIMENSIONS: dict[str, list[str]] = {
        "D1_SNA": [
            "social network analysis", "sna", "betweenness", "degree centrality",
            "eigenvector", "closeness", "network density", "graph theory",
            "jaringan komunikasi", "analisis jaringan", "aktor sentral"
        ],
        "D2_INDOBERT": [
            "indobert", "bert", "transformer", "deep learning", "fine-tuning",
            "huggingface", "language model", "nlp", "klasifikasi teks"
        ],
        "D3_NINE_EMOTIONS": [
            "emotion detection", "9 emosi", "plutchik", "joy", "trust", "anger",
            "fear", "sadness", "disgust", "surprise", "anticipation", "deteksi emosi"
        ],
        "D4_SARCASM": [
            "sarcasm", "irony", "sarkasme", "sindiran", "satire", "figurative language"
        ],
        "D5_ABSA": [
            "aspect-based sentiment", "absa", "aspect extraction", "sentimen aspek",
            "polaritas aspek", "target-oriented sentiment"
        ],
        "D6_TELEGRAM_BOTS": [
            "telegram", "bot", "telegram bot api", "automated bot", "messaging channel",
            "botnet", "bot detection", "saluran telegram"
        ],
        "D7_MARKETING_6_0": [
            "marketing 6.0", "phygital", "metamarketing", "kotler", "human-centric",
            "komunikasi kebijakan", "public relations", "pemasaran digital"
        ],
        "D8_MBG_POLICY": [
            "makan bergizi gratis", "mbg", "program mbg", "kebijakan publik",
            "public policy", "kebijakan pemerintah", "program makan siang gratis"
        ],
    }

    def __init__(self, repo_path: Path | str | None = None) -> None:
        self.repo_path = Path(repo_path or os.getenv("THIS_IS_ECONOMY_PATH") or THIS_IS_ECONOMY_DEFAULT_PATH)
        self.baseline = self._load_baseline()

    def _load_baseline(self) -> ThesisEmpiricalBaseline:
        """Loads live empirical metrics from ThisIsEconomy if available, else uses verified defaults."""
        if not self.repo_path.exists():
            return ThesisEmpiricalBaseline()

        baseline = ThesisEmpiricalBaseline()

        # 1. Load IndoBERT metrics
        metrics_csv = self.repo_path / "results" / "FINAL_indobert_metrics.csv"
        if metrics_csv.exists():
            try:
                with open(metrics_csv, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        baseline.indobert_accuracy = float(row.get("Accuracy", 0.794))
                        baseline.indobert_f1_weighted = float(row.get("F1_Weighted", 0.785))
                        break
            except Exception:
                pass

        # 2. Load Sarcasm validation
        sarcasm_json = self.repo_path / "reports" / "sarcasm_validation.json"
        if sarcasm_json.exists():
            try:
                with open(sarcasm_json, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    total = data.get("total_labeled_rows", 3395)
                    true_count = data.get("distribution", {}).get("True", 315)
                    baseline.sarcasm_instances_analyzed = total
                    baseline.sarcasm_prevalence_pct = round((true_count / max(1, total)) * 100.0, 2)
            except Exception:
                pass

        # 3. Load SNA network nodes
        nodes_csv = self.repo_path / "results" / "mbg_network_nodes_final.csv"
        if nodes_csv.exists():
            try:
                with open(nodes_csv, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    nodes = list(reader)
                    baseline.total_nodes = len(nodes)
                    # Extract unique communities
                    comms = set(r.get("Community") for r in nodes if r.get("Community"))
                    baseline.communities_detected = len(comms)
                    # Top actors by degree
                    sorted_actors = sorted(nodes, key=lambda x: float(x.get("Degree", 0) or 0), reverse=True)
                    baseline.top_central_actors = [r.get("Label", "") for r in sorted_actors[:5] if r.get("Label")]
            except Exception:
                pass

        return baseline

    def evaluate_paper_alignment(self, title: str, text: str, record_id: str = "") -> ThesisAlignmentResult:
        """Evaluates how strongly an academic paper aligns with the 8 dimensions of the thesis (#159, #160)."""
        content = f"{title} {text}".lower()

        matched: list[str] = []
        missing: list[str] = []

        for dim_code, keywords in self.THESIS_DIMENSIONS.items():
            dim_name = dim_code.split("_", 1)[1]
            if any(re.search(r"\b" + re.escape(kw) + r"\b", content) for kw in keywords):
                matched.append(dim_name)
            else:
                missing.append(dim_name)

        # 8 Dimensions total: Each dimension matched gives 12.5 points
        score = round((len(matched) / 8.0) * 100.0, 1)

        if score >= 60.0:
            relevance = "HIGHLY_ALIGNED"
            justification = f"Paper ini sangat relevan sebagai literatur inti Bab II karena mengintegrasikan {len(matched)} pilar riset ({', '.join(matched)})."
        elif score >= 35.0:
            relevance = "MODERATELY_ALIGNED"
            justification = f"Paper ini relevan untuk tinjauan spesifik pada pilar {', '.join(matched)}."
        elif score >= 12.5:
            relevance = "PERIPHERAL"
            justification = f"Paper ini hanya menyentuh aspek periferi ({', '.join(matched)})."
        else:
            relevance = "UNALIGNED"
            justification = "Paper ini tidak memiliki kecocokan langsung dengan pilar tematik tesis."

        return ThesisAlignmentResult(
            record_id=record_id,
            title=title,
            alignment_score=score,
            matched_dimensions=matched,
            missing_dimensions=missing,
            relevance_level=relevance,
            gap_justification=justification,
        )

    def audit_corpus_alignment(self, records: list[Any]) -> dict[str, Any]:
        """Audits an entire literature collection for coverage of the 8 thesis dimensions."""
        results: list[ThesisAlignmentResult] = []
        dim_coverage_counts: dict[str, int] = {dim.split("_", 1)[1]: 0 for dim in self.THESIS_DIMENSIONS}

        for r in records:
            title = getattr(r, "title", "") if hasattr(r, "title") else r.get("title", "")
            abstract = getattr(r, "abstract", "") if hasattr(r, "abstract") else r.get("abstract", "")
            pid = getattr(r, "record_id", "") if hasattr(r, "record_id") else r.get("record_id", "")

            res = self.evaluate_paper_alignment(title, abstract, pid)
            results.append(res)

            for d in res.matched_dimensions:
                dim_coverage_counts[d] += 1

        total = len(records)
        avg_score = round(sum(r.alignment_score for r in results) / max(1, total), 1)

        return {
            "total_papers_audited": total,
            "average_alignment_score": avg_score,
            "dimension_coverage": {
                dim: {
                    "paper_count": count,
                    "coverage_pct": round((count / max(1, total)) * 100.0, 1),
                }
                for dim, count in dim_coverage_counts.items()
            },
            "empirical_baseline": self.baseline.to_dict(),
            "results": [r.to_dict() for r in results],
        }
