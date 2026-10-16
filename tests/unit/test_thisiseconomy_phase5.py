"""Unit Tests for Phase 5 (ThisIsEconomy Research Monorepo Integration & Section I Features).

Covers all 23 items of Section I (Tesis-Specific Mapping #138 - #160):
- SNA, IndoBERT, BERT-family, Emotion, Sarcasm, ABSA, Emoji, Hashtag
- Community, Louvain, Centrality, Topic modeling, Sentiment
- Marketing 6.0, Phygital, Metamarketing, Policy Communication, Public Communication
- MBG context, Platform X comparison, Telegram comparison
- Thesis alignment score, Component coverage
- Macro topology, Tri-layer architecture, and Offline fallback safety
"""

from __future__ import annotations

from pathlib import Path

from core.integrations.thisiseconomy_bridge import ThisIsEconomyBridge


def test_macro_topology_canonical_baseline() -> None:
    """Verifies that the macro topology metrics match the canonical NodeXL & NetworkX analysis."""
    bridge = ThisIsEconomyBridge()
    topo = bridge.baseline.macro_topology

    assert topo["total_vertices"] == 971
    assert topo["unique_directed_edges"] == 666
    assert topo["modularity_louvain_q"] == 0.9837
    assert topo["graph_density"] == 0.000707
    assert topo["network_diameter"] == 9
    assert "0.0120" in topo["reciprocity"]
    assert bridge.baseline.echo_chambers_internal_edge_pct >= 99.0
    assert bridge.baseline.communities_detected >= 300


def test_indobert_9_emotions_and_benchmarks() -> None:
    """Verifies 9-class Plutchik emotion metrics and IndoBERT fine-tuning benchmarks."""
    bridge = ThisIsEconomyBridge()
    b = bridge.baseline

    assert b.indobert_accuracy >= 0.85
    assert b.indobert_f1_macro >= 0.85
    assert b.indobert_f1_weighted >= 0.85

    for emo in ["Marah", "Jijik", "Takut", "Bahagia", "Percaya", "Netral", "Sedih", "Tertarik", "Kaget"]:
        assert emo in b.indobert_9_emotions_metrics
        assert b.indobert_9_emotions_metrics[emo]["f1"] > 0.50

    # Percaya (Trust) achieved perfect F1 1.000
    assert b.indobert_9_emotions_metrics["Percaya"]["f1"] == 1.000
    # Jijik (Disgust) achieved high F1 0.909
    assert b.indobert_9_emotions_metrics["Jijik"]["f1"] >= 0.90


def test_sarcasm_and_emoji_heuristics() -> None:
    """Verifies semiotic sarcasm heuristics, 11 sarcasm emojis, and prevalence rate."""
    bridge = ThisIsEconomyBridge()
    b = bridge.baseline

    assert b.sarcasm_instances_analyzed == 3395
    assert b.sarcasm_prevalence_pct == 9.28
    assert "🤡" in b.sarcasm_emojis
    assert "🙃" in b.sarcasm_emojis
    assert "🤮" in b.sarcasm_emojis
    assert len(b.sarcasm_emojis) == 11


def test_absa_aspect_category_benchmarks() -> None:
    """Verifies Aspect-Based Sentiment Analysis categories (A1 Budget, A2 Logistics, A3 Nutrition)."""
    bridge = ThisIsEconomyBridge()
    aspects = bridge.baseline.absa_aspect_categories

    assert len(aspects) == 3
    aspect_ids = [a["aspect_id"] for a in aspects]
    assert "A1" in aspect_ids
    assert "A2" in aspect_ids
    assert "A3" in aspect_ids

    # Nutrition quality has highest mentions
    nutrition = next(a for a in aspects if a["aspect_id"] == "A3")
    assert nutrition["mentions"] == 1344
    assert nutrition["disgust_pct"] > 70.0


def test_cross_platform_affordance_matrix() -> None:
    """Verifies Platform X vs Telegram affordances across policy surveillance and EWS latency."""
    bridge = ThisIsEconomyBridge()
    affordances = bridge.baseline.cross_platform_matrix

    assert len(affordances) == 5
    dims = [a["dimension"] for a in affordances]
    assert "Primary Communicative Mode" in dims
    assert "Crisis Response Latency (EWS Sensor Efficacy)" in dims


def test_section_i_exhaustive_component_detection() -> None:
    """Verifies that all 23 items of Section I (#138 to #160) are systematically detected."""
    bridge = ThisIsEconomyBridge()

    comprehensive_text = (
        "Analisis Jaringan Komunikasi (SNA) kebijakan MBG (Makan Bergizi Gratis) menggunakan IndoBERT "
        "dan arsitektur BERT-family transformer. Deteksi emosi Plutchik (disgust dan marah), serta "
        "analisis sarkasme dengan emoji 🤡 dan hashtag #MakanBergiziGratis. Komunitas wacana diidentifikasi "
        "menggunakan algoritma Louvain dengan modularity Q=0.9837, serta pengukuran degree dan betweenness centrality. "
        "Topic modeling LDA dan sentiment analysis polaritas sentimen menunjukkan evaluasi ABSA aspek gizi. "
        "Kajian ini merujuk Marketing 6.0 Kotler, konsep phygital dan metamarketing dalam komunikasi kebijakan dan komunikasi publik "
        "serta perbandingan diskursus antara Twitter (Platform X) dan bot saluran Telegram."
    )

    detection_result = bridge.detect_thesis_components(comprehensive_text, title="Tesis MIKOM MBG")
    features = detection_result["features"]

    # Check that key features fired
    assert features["138_sna"] is True
    assert features["139_indobert"] is True
    assert features["140_bert_family"] is True
    assert features["141_emotion"] is True
    assert features["142_sarcasm"] is True
    assert features["143_absa"] is True
    assert features["144_emoji"] is True
    assert features["145_hashtag"] is True
    assert features["146_community"] is True
    assert features["147_louvain"] is True
    assert features["148_centrality"] is True
    assert features["149_topic_modeling"] is True
    assert features["150_sentiment"] is True
    assert features["151_marketing_6_0"] is True
    assert features["152_phygital"] is True
    assert features["153_metamarketing"] is True
    assert features["154_policy_communication"] is True
    assert features["155_public_communication"] is True
    assert features["156_mbg_context"] is True
    assert features["157_twitter_comparison"] is True
    assert features["158_telegram_comparison"] is True

    # Feature #159 & #160
    assert detection_result["thesis_alignment_score"] >= 90.0
    assert detection_result["is_empirically_aligned"] is True
    cov = detection_result["component_coverage"]
    assert cov["features_detected_count"] >= 20


def test_tri_layer_summary_structure() -> None:
    """Verifies that get_tri_layer_summary outputs all three empirical layers."""
    bridge = ThisIsEconomyBridge()
    tri_layer = bridge.get_tri_layer_summary()

    assert "layer_1_macro" in tri_layer
    assert "layer_2_meso" in tri_layer
    assert "layer_3_micro" in tri_layer

    assert tri_layer["layer_1_macro"]["topology"]["modularity_q"] == 0.9837
    assert tri_layer["layer_2_meso"]["metrics"]["accuracy"] >= 0.85
    assert len(tri_layer["layer_3_micro"]["aspects"]) == 3
    assert tri_layer["doi"] == "10.5281/zenodo.11029482"


def test_offline_fallback_safety_for_streamlit_cloud() -> None:
    """Ensures bridge operates seamlessly without disk artifacts (Streamlit Cloud simulation)."""
    fake_path = Path("/tmp/non_existent_cloud_env_dir_12345")
    bridge = ThisIsEconomyBridge(repo_path=fake_path)

    # Must not raise exceptions and must yield verified canonical baselines
    assert bridge.baseline.total_nodes == 971
    assert bridge.baseline.unique_directed_edges == 666
    assert bridge.baseline.modularity_q == 0.9837
    assert bridge.baseline.indobert_accuracy >= 0.85
    assert len(bridge.baseline.sarcasm_emojis) == 11
    assert bridge.baseline.zenodo_doi == "10.5281/zenodo.11029482"
