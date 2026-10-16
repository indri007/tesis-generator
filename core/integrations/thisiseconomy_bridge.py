"""ThisIsEconomy Research Monorepo Bridge & Thesis Alignment Engine (Phase 5).

Bridges empirical research artifacts from /Users/jevin/ThisIsEconomy:
1. Social Network Analysis (SNA): Degree, Betweenness, Louvain Community detection (Q=0.9837).
2. IndoBERT Deep Learning: Macro/Weighted F1 (0.866), 9 Emotion distribution (Plutchik: Marah, Jijik, Takut, Bahagia, Percaya, Netral, Sedih, Tertarik, Kaget).
3. Sarcasm & Irony: Labeled validation data (N=3,395, 9.28% sarcasm), 11 sarcasm emojis, and semiotic markers.
4. ABSA & Marketing 6.0: Aspect-Based Sentiment Analysis (Budget, Logistics, Nutrition) and Phygital Public Communication.
5. MBG (Makan Bergizi Gratis) Policy Communication Context & Cross-Platform Affordances (Platform X vs Telegram).

Features Covered (Section I #138 - #160):
- 138: SNA detection
- 139: IndoBERT detection
- 140: BERT-family detection
- 141: Emotion detection
- 142: Sarcasm detection
- 143: ABSA detection
- 144: Emoji analysis
- 145: Hashtag analysis
- 146: Community detection
- 147: Louvain detection
- 148: Centrality detection
- 149: Topic modeling
- 150: Sentiment analysis
- 151: Marketing 6.0
- 152: Phygital
- 153: Metamarketing
- 154: Policy communication
- 155: Public communication
- 156: MBG context
- 157: Twitter/X comparison
- 158: Telegram-vs-X comparison
- 159: Thesis alignment score
- 160: Thesis component coverage
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

# Canonical Sarcasm Emojis identified in ThisIsEconomy empirical research
CANONICAL_SARCASM_EMOJIS = ["🤡", "🙃", "🤮", "🤢", "😒", "💀", "😤", "🤬", "🤦", "😅", "🙄"]

# Canonical 9 Plutchik Emotions & IndoBERT F1 Performance Benchmarks
CANONICAL_9_EMOTIONS_METRICS: dict[str, dict[str, float]] = {
    "Marah": {"precision": 0.889, "recall": 0.800, "f1": 0.842, "support": 10.0},
    "Jijik": {"precision": 0.833, "recall": 1.000, "f1": 0.909, "support": 10.0},
    "Takut": {"precision": 1.000, "recall": 0.700, "f1": 0.824, "support": 10.0},
    "Bahagia": {"precision": 0.800, "recall": 0.400, "f1": 0.533, "support": 10.0},
    "Percaya": {"precision": 1.000, "recall": 1.000, "f1": 1.000, "support": 10.0},
    "Netral": {"precision": 0.909, "recall": 1.000, "f1": 0.952, "support": 10.0},
    "Sedih": {"precision": 0.769, "recall": 1.000, "f1": 0.870, "support": 10.0},
    "Tertarik": {"precision": 0.833, "recall": 1.000, "f1": 0.909, "support": 10.0},
    "Kaget": {"precision": 0.909, "recall": 1.000, "f1": 0.952, "support": 10.0},
}

# Canonical Macro Topology Metrics (NodeXL & NetworkX Canonical Pipeline)
CANONICAL_MACRO_TOPOLOGY: dict[str, Any] = {
    "graph_type": "Directed (Asymmetric Mention & Reply Network)",
    "total_vertices": 971,
    "unique_directed_edges": 666,
    "total_edges": 692,
    "graph_density": 0.000707,
    "network_diameter": 9,
    "average_geodesic_distance": 3.6731,
    "modularity_louvain_q": 0.9837,
    "reciprocity": "0.0120 (1.20%)",
    "giant_component_size": "89 simpul (9.17% dari total populasi)",
    "average_clustering_coefficient": 0.0171,
    "power_law_scaling_alpha": 2.168,
}

# Canonical ABSA Aspect Benchmarks
CANONICAL_ABSA_ASPECTS: list[dict[str, Any]] = [
    {
        "aspect_id": "A1",
        "aspect_name": "Budget & Procurement (Anggaran & Vendor)",
        "mentions": 535,
        "share_pct": 23.44,
        "disgust_pct": 77.01,
        "span_f1": 0.862,
    },
    {
        "aspect_id": "A2",
        "aspect_name": "Logistics & Distribution (Logistik & Distribusi)",
        "mentions": 403,
        "share_pct": 17.66,
        "disgust_pct": 78.91,
        "span_f1": 0.840,
    },
    {
        "aspect_id": "A3",
        "aspect_name": "Nutritional Quality & Hygiene (Kualitas Gizi & Higienitas)",
        "mentions": 1344,
        "share_pct": 58.90,
        "disgust_pct": 71.13,
        "span_f1": 0.901,
    },
]

# Canonical Cross-Platform Affordance Matrix (Platform X vs Telegram / Meta / TikTok)
CANONICAL_CROSS_PLATFORM_AFFORDANCES: list[dict[str, str]] = [
    {
        "dimension": "Primary Communicative Mode",
        "platform_x": "Textual-Deliberative & Paralinguistic Sarcasm (280+ chars, emojis, quote-tweets)",
        "telegram": "Semi-Public Broadcasting & Channel Discussions (Asynchronous, Bot-Augmented)",
        "policy_salience": "High: Policy critique requires syntactic nuance, sarcasm, and document citations",
    },
    {
        "dimension": "Algorithmic Political Exposure",
        "platform_x": "High Real-Time Crisis Trending (Zero friction for political controversy and breaking news)",
        "telegram": "Chronological Feeds & Opt-In Subscription (No algorithmic demotion or shadowban)",
        "policy_salience": "Critical: Platform X and Telegram provide uncensored real-time public telemetry",
    },
    {
        "dimension": "Public Scrutiny & Direct Institutional Accountability",
        "platform_x": "High Asymmetry & Tagging (@prabowo, @kemdikbud_ri, @grok directly mentioned in quote chains)",
        "telegram": "Channel Admins & Broadcast Bot Alerts (Targeted notifications without direct tag chains)",
        "policy_salience": "High: Allows citizens to directly challenge state leaders and conversational AI",
    },
    {
        "dimension": "Network Topological Openness",
        "platform_x": "Public Directed Graph (Follow, Reply, Quote, Retweet open APIs; graph mathematically modelable)",
        "telegram": "Channel-Forward Graph (Forwarding chains and bot subscriber counts modelable)",
        "policy_salience": "Methodological Prerequisite: Enables rigorous directed Social Network Analysis (SNA)",
    },
    {
        "dimension": "Crisis Response Latency (EWS Sensor Efficacy)",
        "platform_x": "Minutes (Real-time citizen reporting of school poisoning within 15–30 minutes)",
        "telegram": "Instant Push Telemetry (Automated EWS alert delivery directly to subscriber inboxes)",
        "policy_salience": "Vital: Early Warning Systems require real-time, low-latency telemetry",
    },
]


@dataclass
class ThesisEmpiricalBaseline:
    """Empirical baseline metrics extracted from the ThisIsEconomy research pipeline."""

    total_nodes: int = 971
    total_edges: int = 666
    unique_directed_edges: int = 666
    communities_detected: int = 342
    modularity_q: float = 0.9837
    graph_density: float = 0.000707
    network_diameter: int = 9
    echo_chambers_internal_edge_pct: float = 99.86
    top_central_actors: list[str] = field(
        default_factory=lambda: ["@grok", "@4Y4NKZ", "@newIding30", "@prabowo", "@dbdbidip"]
    )
    top_central_actors_detailed: list[dict[str, Any]] = field(
        default_factory=lambda: [
            {"id": "grok", "label": "@grok", "role": "Algorithmic Oracle (AI Fact-Checker)", "degree": 42, "betweenness": 0.005941},
            {"id": "4Y4NKZ", "label": "@4Y4NKZ", "role": "Secondary Influencer (Akun Penggerak)", "degree": 16, "betweenness": 0.000161},
            {"id": "newIding30", "label": "@newIding30", "role": "Information Broadcaster (Penyebar Wacana)", "degree": 15, "betweenness": 0.000097},
            {"id": "prabowo", "label": "@prabowo", "role": "Target Sink (Otoritas Kebijakan)", "degree": 15, "betweenness": 0.005413},
            {"id": "dbdbidip", "label": "@dbdbidip", "role": "Citizen Broadcaster", "degree": 13, "betweenness": 0.000166},
        ]
    )
    indobert_accuracy: float = 0.878
    indobert_f1_macro: float = 0.866
    indobert_f1_weighted: float = 0.866
    indobert_emotions: list[str] = field(
        default_factory=lambda: [
            "neutral", "disgust", "anger", "joy", "trust", "fear", "sadness", "surprise", "anticipation",
            "Marah", "Jijik", "Takut", "Bahagia", "Percaya", "Netral", "Sedih", "Tertarik", "Kaget"
        ]
    )
    indobert_9_emotions_metrics: dict[str, dict[str, float]] = field(
        default_factory=lambda: CANONICAL_9_EMOTIONS_METRICS.copy()
    )
    sarcasm_instances_analyzed: int = 3395
    sarcasm_prevalence_pct: float = 9.28  # 315 / 3395
    sarcasm_emojis: list[str] = field(
        default_factory=lambda: CANONICAL_SARCASM_EMOJIS.copy()
    )
    absa_aspect_categories: list[dict[str, Any]] = field(
        default_factory=lambda: list(CANONICAL_ABSA_ASPECTS)
    )
    cross_platform_matrix: list[dict[str, str]] = field(
        default_factory=lambda: list(CANONICAL_CROSS_PLATFORM_AFFORDANCES)
    )
    macro_topology: dict[str, Any] = field(
        default_factory=lambda: CANONICAL_MACRO_TOPOLOGY.copy()
    )
    zenodo_doi: str = "10.5281/zenodo.11029482"
    zenodo_title: str = "Communication Network Analysis of Sarcasm in MBG Discourse: Decoding Emotion Behind the Network"
    authors: list[str] = field(
        default_factory=lambda: [
            "Indri Anjar Kartika Sari",
            "Catur Suratnoaji",
            "Agus Widiyarta",
        ]
    )
    affiliation: str = "UPN 'Veteran' Jawa Timur"
    provenance: str = "ThisIsEconomy_verified_production_artifacts"

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
    features_detected: dict[str, bool] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ThisIsEconomyBridge:
    """Connects the empirical thesis codebase with manuscript literature auditing."""

    # 8 Core Pillars of the Thesis Taxonomy (Sections G & I)
    THESIS_DIMENSIONS: dict[str, list[str]] = {
        "D1_SNA": [
            "social network analysis", "sna", "betweenness", "degree centrality",
            "eigenvector", "closeness", "network density", "graph theory",
            "jaringan komunikasi", "analisis jaringan", "aktor sentral",
            "louvain", "modularity", "komunitas", "echo chamber"
        ],
        "D2_INDOBERT": [
            "indobert", "bert", "roberta", "transformer", "deep learning", "fine-tuning",
            "huggingface", "language model", "nlp", "klasifikasi teks", "neural network"
        ],
        "D3_NINE_EMOTIONS": [
            "emotion detection", "9 emosi", "plutchik", "joy", "trust", "anger",
            "fear", "sadness", "disgust", "surprise", "anticipation", "deteksi emosi",
            "marah", "jijik", "takut", "bahagia", "percaya", "kaget"
        ],
        "D4_SARCASM": [
            "sarcasm", "irony", "sarkasme", "sindiran", "satire", "figurative language",
            "paralinguistik", "semiotika"
        ],
        "D5_ABSA": [
            "aspect-based sentiment", "absa", "aspect extraction", "sentimen aspek",
            "polaritas aspek", "target-oriented sentiment", "acsa", "ate"
        ],
        "D6_TELEGRAM_BOTS": [
            "telegram", "bot", "telegram bot api", "automated bot", "messaging channel",
            "botnet", "bot detection", "saluran telegram", "ews bot"
        ],
        "D7_MARKETING_6_0": [
            "marketing 6.0", "phygital", "metamarketing", "kotler", "human-centric",
            "komunikasi kebijakan", "public relations", "pemasaran digital",
            "touchpoint", "phygital gap"
        ],
        "D8_MBG_POLICY": [
            "makan bergizi gratis", "mbg", "program mbg", "kebijakan publik",
            "public policy", "kebijakan pemerintah", "program makan siang gratis",
            "food security", "school feeding"
        ],
    }

    # Granular Regex Matchers for the 23 Features of Section I (#138 to #160)
    SECTION_I_RULES: dict[str, list[str]] = {
        "138_sna": [r"\bsna\b", r"social network analysis", r"analisis jaringan komunikasi"],
        "139_indobert": [r"\bindobert\b", r"indobert-base"],
        "140_bert_family": [r"\bbert\b", r"\broberta\b", r"\btransformer\b", r"language model"],
        "141_emotion": [r"\bemotion\b", r"\bemosi\b", r"\bplutchik\b", r"\bdisgust\b", r"\bjijik\b", r"\bmarah\b", r"\banger\b"],
        "142_sarcasm": [r"\bsarcasm\b", r"\bsarkasme\b", r"\bsindiran\b", r"\birony\b", r"\bsatire\b"],
        "143_absa": [r"\babsa\b", r"aspect-based sentiment", r"sentimen aspek", r"aspect extraction"],
        "144_emoji": [r"\bemoji\b", r"\bemoticon\b", r"🤡|🙃|🤮|🤢|😒|💀|😤|🤬|🤦|😅|🙄"],
        "145_hashtag": [r"#\w+", r"\bhashtag\b", r"\btagar\b"],
        "146_community": [r"\bcommunity\b", r"\bkomunitas\b", r"echo chamber", r"klaster wacana"],
        "147_louvain": [r"\blouvain\b", r"\bmodularity\b", r"modularity\s*\(?q\)?", r"\bq\s*=\s*0\.\d+"],
        "148_centrality": [r"\bcentrality\b", r"\bbetweenness\b", r"\bdegree\b", r"\beigenvector\b", r"\bcloseness\b", r"\bpagerank\b"],
        "149_topic_modeling": [r"topic model", r"\blda\b", r"\bbertopic\b", r"pemodelan topik"],
        "150_sentiment": [r"\bsentiment\b", r"\bsentimen\b", r"\bpolarity\b", r"\bpolaritas\b"],
        "151_marketing_6_0": [r"marketing 6\.0", r"pemasaran 6\.0", r"kotler"],
        "152_phygital": [r"\bphygital\b", r"physical-digital", r"kesenjangan fisik-digital"],
        "153_metamarketing": [r"\bmetamarketing\b", r"\bmeta-marketing\b"],
        "154_policy_communication": [r"policy communication", r"komunikasi kebijakan", r"kebijakan publik"],
        "155_public_communication": [r"public communication", r"komunikasi publik", r"komunikasi.*publik", r"hubungan masyarakat", r"\bpr\b", r"opini publik", r"ruang publik"],
        "156_mbg_context": [r"\bmbg\b", r"makan bergizi gratis", r"makan siang gratis"],
        "157_twitter_comparison": [r"\btwitter\b", r"platform x", r"\bx\.com\b", r"\btweet\b"],
        "158_telegram_comparison": [r"\btelegram\b", r"telegram bot", r"telegram channel"],
    }

    def __init__(self, repo_path: Path | str | None = None) -> None:
        self.repo_path = Path(repo_path or os.getenv("THIS_IS_ECONOMY_PATH") or THIS_IS_ECONOMY_DEFAULT_PATH)
        self.baseline = self._load_baseline()

    def _load_baseline(self) -> ThesisEmpiricalBaseline:
        """Loads live empirical metrics from ThisIsEconomy if available, else uses verified canonical defaults."""
        if not self.repo_path.exists():
            return ThesisEmpiricalBaseline()

        baseline = ThesisEmpiricalBaseline()

        # 1. Load Macro Topology if present
        macro_json = self.repo_path / "results" / "macro_topology_metrics.json"
        if macro_json.exists():
            try:
                with open(macro_json, "r", encoding="utf-8") as f:
                    macro_dict = json.load(f)
                    baseline.total_nodes = int(macro_dict.get("Total Vertices (|V|)", baseline.total_nodes))
                    baseline.unique_directed_edges = int(macro_dict.get("Unique Directed Edges", baseline.unique_directed_edges))
                    baseline.total_edges = baseline.unique_directed_edges
                    mod_str = str(macro_dict.get("Modularity Louvain (Q)", "0.9837")).split()[0]
                    baseline.modularity_q = float(mod_str)
                    baseline.graph_density = float(str(macro_dict.get("Graph Density (Directed)", "0.000707")).split()[0])
                    baseline.network_diameter = int(macro_dict.get("Network Diameter (Giant Component)", baseline.network_diameter))
                    baseline.macro_topology.update(macro_dict)
            except Exception:
                pass

        # 2. Load Echo Chambers & Communities
        echo_json = self.repo_path / "results" / "community_echo_chambers.json"
        if echo_json.exists():
            try:
                with open(echo_json, "r", encoding="utf-8") as f:
                    echo_data = json.load(f)
                    baseline.communities_detected = int(echo_data.get("num_communities", baseline.communities_detected))
                    baseline.echo_chambers_internal_edge_pct = float(echo_data.get("internal_pct", baseline.echo_chambers_internal_edge_pct))
            except Exception:
                pass

        # 3. Load Top Actors Centrality
        actor_json = self.repo_path / "results" / "actor_centrality_top15.json"
        if actor_json.exists():
            try:
                with open(actor_json, "r", encoding="utf-8") as f:
                    act_data = json.load(f)
                    top_list = act_data.get("top_total_degree", [])
                    if top_list:
                        baseline.top_central_actors = [item.get("Label", "") for item in top_list[:5] if item.get("Label")]
                        baseline.top_central_actors_detailed = [
                            {
                                "id": item.get("Id", ""),
                                "label": item.get("Label", ""),
                                "role": item.get("Communication_Role", "Actor"),
                                "degree": item.get("Total_Degree", 0),
                                "betweenness": item.get("Betweenness_Centrality", 0.0),
                            }
                            for item in top_list[:5]
                        ]
            except Exception:
                pass

        # 4. Load IndoBERT 9-class Metrics
        metrics_csv = self.repo_path / "results" / "per_class_metrics_9_class.csv"
        if metrics_csv.exists():
            try:
                with open(metrics_csv, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        cls_name = row.get("", "") or row.get("Unnamed: 0", "")
                        if cls_name == "accuracy":
                            baseline.indobert_accuracy = float(row.get("f1-score", baseline.indobert_accuracy))
                        elif cls_name == "macro avg":
                            baseline.indobert_f1_macro = float(row.get("f1-score", baseline.indobert_f1_macro))
                        elif cls_name == "weighted avg":
                            baseline.indobert_f1_weighted = float(row.get("f1-score", baseline.indobert_f1_weighted))
                        elif cls_name in baseline.indobert_9_emotions_metrics:
                            baseline.indobert_9_emotions_metrics[cls_name] = {
                                "precision": float(row.get("precision", 0.0)),
                                "recall": float(row.get("recall", 0.0)),
                                "f1": float(row.get("f1-score", 0.0)),
                                "support": float(row.get("support", 10.0)),
                            }
            except Exception:
                pass

        # 5. Load Sarcasm validation
        sarcasm_json = self.repo_path / "reports" / "sarcasm_validation.json"
        if sarcasm_json.exists():
            try:
                with open(sarcasm_json, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    total = data.get("total_labeled_rows", baseline.sarcasm_instances_analyzed)
                    true_count = data.get("distribution", {}).get("True", 315)
                    baseline.sarcasm_instances_analyzed = total
                    baseline.sarcasm_prevalence_pct = round((true_count / max(1, total)) * 100.0, 2)
            except Exception:
                pass

        return baseline

    def detect_thesis_components(self, text: str, title: str = "") -> dict[str, Any]:
        """Exhaustively evaluates text for all 23 features of Section I (#138 to #160)."""
        content = f"{title} {text}".lower()

        detections: dict[str, bool] = {}
        for feature_key, patterns in self.SECTION_I_RULES.items():
            matched = any(re.search(pat, content, re.IGNORECASE) for pat in patterns)
            detections[feature_key] = matched

        # Feature #159: Thesis alignment score (0 - 100%)
        active_feature_count = sum(1 for k, v in detections.items() if v)
        alignment_score = round((active_feature_count / max(1, len(self.SECTION_I_RULES))) * 100.0, 1)

        # Feature #160: Thesis component coverage
        component_coverage = {
            "total_section_i_features": len(self.SECTION_I_RULES),
            "features_detected_count": active_feature_count,
            "coverage_percentage": alignment_score,
            "detected_list": [k for k, v in detections.items() if v],
            "missing_list": [k for k, v in detections.items() if not v],
        }

        return {
            "features": detections,
            "thesis_alignment_score": alignment_score,
            "component_coverage": component_coverage,
            "is_empirically_aligned": alignment_score >= 35.0,
        }

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

        comp_detections = self.detect_thesis_components(text, title)["features"]

        return ThesisAlignmentResult(
            record_id=record_id,
            title=title,
            alignment_score=score,
            matched_dimensions=matched,
            missing_dimensions=missing,
            relevance_level=relevance,
            gap_justification=justification,
            features_detected=comp_detections,
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

    def get_tri_layer_summary(self) -> dict[str, Any]:
        """Returns the definitive tri-layer computational architecture of the MIKOM 2026 thesis."""
        return {
            "layer_1_macro": {
                "title": "Layer 1: Directed Social Network Analysis (SNA)",
                "method": "Asymmetric mention/reply directed graph via NetworkX & Louvain community detection",
                "topology": {
                    "vertices": self.baseline.total_nodes,
                    "edges": self.baseline.total_edges,
                    "modularity_q": self.baseline.modularity_q,
                    "density": self.baseline.graph_density,
                    "echo_chambers_internal_pct": self.baseline.echo_chambers_internal_edge_pct,
                },
                "key_actors": self.baseline.top_central_actors_detailed,
            },
            "layer_2_meso": {
                "title": "Layer 2: IndoBERT 9 Plutchik Emotions & Semiotic Sarcasm Detection",
                "method": "Fine-tuned IndoBERT-base-p1 on 9 emotion classes with emoji paralinguistic markers",
                "metrics": {
                    "accuracy": self.baseline.indobert_accuracy,
                    "f1_macro": self.baseline.indobert_f1_macro,
                    "f1_weighted": self.baseline.indobert_f1_weighted,
                    "sarcasm_prevalence_pct": self.baseline.sarcasm_prevalence_pct,
                    "sarcasm_emojis": self.baseline.sarcasm_emojis,
                },
                "per_class_f1": {k: v["f1"] for k, v in self.baseline.indobert_9_emotions_metrics.items()},
            },
            "layer_3_micro": {
                "title": "Layer 3: Aspect-Based Sentiment Analysis (ABSA) & Phygital Gap",
                "method": "Bio-tagged aspect term extraction (ATE) & category sentiment analysis (ACSA)",
                "aspects": self.baseline.absa_aspect_categories,
                "framework": "Philip Kotler Marketing 6.0 (Metamarketing & Phygital Public Communication)",
            },
            "cross_platform_affordances": self.baseline.cross_platform_matrix,
            "doi": self.baseline.zenodo_doi,
            "authors": self.baseline.authors,
            "affiliation": self.baseline.affiliation,
        }
