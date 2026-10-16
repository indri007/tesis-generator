"""Generate NodeXL Pro Group-in-a-Box (GIB) Rule Engine & Verification Schema Diagram.

Visualizes the 10 Pilar Pedoman MIKOM 2026 rule specifications and deterministic verification
logic partitioned into 5 thematic clusters matching NodeXL Pro aesthetics:
1. Layout & Typography Rules (EMU & Font Engine)
2. Systematic Structure Rules (5 Bab MIKOM 2026)
3. Mathematical & Statistical Consistency Rules
4. Citation & Bibliographic Integrity Rules (APA 7th)
5. NodeXL Pro Empirical Thesis Alignment (ThisIsEconomy)
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.patches as patches
import matplotlib.pyplot as plt

ROOT_DIR = Path(__file__).resolve().parent.parent
OUTPUT_PROJECT_PATH = ROOT_DIR / "assets" / "images" / "18_nodexl_rule_engine_schema.png"
OUTPUT_BRAIN_PATH = Path("/Users/jevin/.gemini/antigravity-cli/brain/a70d9257-5726-4a1c-ba67-172afa9c412b/18_nodexl_rule_engine_schema.png")


def create_nodexl_rule_schema():
    fig = plt.figure(figsize=(18, 12), dpi=300, facecolor="#0B132B")
    ax = fig.add_subplot(111)
    ax.set_facecolor("#0B132B")
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")

    # Header Title Banner
    ax.text(
        50, 97.5,
        "TesisCheck MIKOM 2026 — Rule Engine & Verification Schema",
        ha="center", va="center", fontsize=20, fontweight="bold", color="#FFFFFF", fontfamily="sans-serif"
    )
    ax.text(
        50, 95.0,
        "NodeXL Pro Group-in-a-Box (GIB) Deterministic Rule Topology | Token: c1d8d71236e1cae9628f0b5c7a55b581",
        ha="center", va="center", fontsize=11, color="#64D8CB", fontfamily="sans-serif"
    )

    # Helper function for drawing rounded boxes
    def draw_group_box(x, y, w, h, title, color_border, color_fill, group_num):
        box = patches.FancyBboxPatch(
            (x, y), w, h,
            boxstyle="round,pad=0.5,rounding_size=1.2",
            facecolor=color_fill,
            edgecolor=color_border,
            linewidth=2.0,
            alpha=0.95,
            zorder=1
        )
        ax.add_patch(box)
        header = patches.FancyBboxPatch(
            (x + 0.3, y + h - 3.2), w - 0.6, 3.0,
            boxstyle="round,pad=0.2,rounding_size=0.6",
            facecolor=color_border,
            edgecolor="none",
            alpha=0.3,
            zorder=2
        )
        ax.add_patch(header)
        ax.text(
            x + 1.5, y + h - 1.7,
            f"GROUP {group_num}: {title.upper()}",
            fontsize=11, fontweight="bold", color="#FFFFFF", va="center", zorder=3
        )

    # Helper function for drawing rule cards
    def draw_rule_card(x, y, w, h, rule_id, target, operator, severity, expected, bg_color="#1C2541", border_color="#48CAE4"):
        card = patches.FancyBboxPatch(
            (x, y), w, h,
            boxstyle="round,pad=0.3,rounding_size=0.8",
            facecolor=bg_color,
            edgecolor=border_color,
            linewidth=1.2,
            zorder=4
        )
        ax.add_patch(card)
        ax.text(
            x + w / 2, y + h - 1.4,
            rule_id,
            ha="center", va="center", fontsize=9.5, fontweight="bold", color="#FFFFFF", zorder=5
        )
        ax.plot([x + 0.5, x + w - 0.5], [y + h - 2.5, y + h - 2.5], color=border_color, lw=1.0, zorder=5)

        curr_y = y + h - 3.7
        # Severity Badge
        sev_color = "#EF4444" if severity == "ERROR" else "#F59E0B"
        ax.text(x + 1.0, curr_y, f"[{severity}]", fontsize=8.0, fontweight="bold", color=sev_color, zorder=5)
        ax.text(x + 6.5, curr_y, f"Target: {target}", fontsize=8.0, color="#64D8CB", zorder=5)
        curr_y -= 1.6
        ax.text(x + 1.0, curr_y, f"Op: {operator}", fontsize=8.0, color="#FFD166", zorder=5)
        curr_y -= 1.5
        ax.text(x + 1.0, curr_y, f"Expect: {expected}", fontsize=7.5, color="#E0E1DD", zorder=5)

    # -------------------------------------------------------------
    # 1. GROUP 1: FORMAT & TYPOGRAPHY RULES (Top Left)
    # -------------------------------------------------------------
    draw_group_box(3, 58, 28, 34, "Format & Margin EMU (10 Pilar)", "#3A86FF", "#111E38", 1)
    draw_rule_card(
        5, 78, 24, 11, "FORMAT_PAGE_LIMIT_001",
        "page_count", "max", "ERROR", "<= 175 Halaman (Hard Gate)",
        bg_color="#182747", border_color="#3A86FF"
    )
    draw_rule_card(
        5, 65, 11.5, 11.5, "FORMAT_MARGIN_4433",
        "margins_emu", "equals", "ERROR", "L/T:4cm, R/B:3cm (EMU)",
        bg_color="#182747", border_color="#3A86FF"
    )
    draw_rule_card(
        17.5, 65, 11.5, 11.5, "FORMAT_FONT_SPACING",
        "font & spacing", "equals", "ERROR", "TNR 12pt, Spasi 2.0",
        bg_color="#182747", border_color="#3A86FF"
    )

    # -------------------------------------------------------------
    # 2. GROUP 2: SISTEMATIKA STRUKTUR 5 BAB (Top Middle)
    # -------------------------------------------------------------
    draw_group_box(34, 58, 32, 34, "Sistematika Struktur 5 BAB", "#06D6A0", "#0D2E2B", 2)
    draw_rule_card(
        36, 78, 28, 11, "STRUCT_BAB_SEQUENCE_001",
        "heading_tree", "sequence", "ERROR", "Bab I -> II -> III -> IV -> V",
        bg_color="#133D37", border_color="#06D6A0"
    )
    draw_rule_card(
        36, 65, 13.5, 11.5, "STRUCT_BAB_SUB_SECTIONS",
        "sub_headings", "exists", "ERROR", "1.1, 1.2, 2.1, 3.1..",
        bg_color="#133D37", border_color="#06D6A0"
    )
    draw_rule_card(
        50.5, 65, 13.5, 11.5, "STRUCT_WORD_COUNT_RANGE",
        "word_count", "range", "WARNING", "40.000 - 60.000 Kata",
        bg_color="#133D37", border_color="#06D6A0"
    )

    # -------------------------------------------------------------
    # 3. GROUP 3: FORMULA & STATISTICAL AUDIT (Top Right)
    # -------------------------------------------------------------
    draw_group_box(69, 58, 28, 34, "Formula & Uji Statistik", "#8338EC", "#24143D", 3)
    draw_rule_card(
        71, 78, 24, 11, "FORMULA_REGRESSION_RECALC",
        "linear_regression", "recalculate", "ERROR", "Y = a + bX (Delta == 0.0)",
        bg_color="#311D53", border_color="#8338EC"
    )
    draw_rule_card(
        71, 65, 11.5, 11.5, "STAT_ALPHA_THRESHOLD",
        "p_value", "min_boundary", "ERROR", "p < 0.05 (Signifikan)",
        bg_color="#311D53", border_color="#8338EC"
    )
    draw_rule_card(
        83.5, 65, 11.5, 11.5, "STAT_SAMPLE_CONSISTENCY",
        "sample_n", "match_cross", "ERROR", "N(Bab 3) == N(Bab 4)",
        bg_color="#311D53", border_color="#8338EC"
    )

    # -------------------------------------------------------------
    # 4. GROUP 4: CITATION & BIBLIOGRAPHIC (Bottom Left)
    # -------------------------------------------------------------
    draw_group_box(3, 10, 44, 46, "Sitasi APA 7 & Kualitas Jurnal", "#FF006E", "#300D22", 4)
    draw_rule_card(
        5, 38, 19, 14, "CIT_RECIPROCAL_APA7",
        "citations_match", "reciprocal", "ERROR", "Teks <-> Daftar Pustaka (100%)",
        bg_color="#451433", border_color="#FF006E"
    )
    draw_rule_card(
        26, 38, 19, 14, "CIT_ORPHAN_DANGLING",
        "orphan_citations", "not_exists", "ERROR", "0 Sitasi Yatim / Dangling",
        bg_color="#451433", border_color="#FF006E"
    )
    draw_rule_card(
        5, 14, 19, 20, "JOURNAL_SCOPUS_QUARTILE",
        "scopus_sjr", "verify_source", "WARNING", "Q1/Q2 (UNVERIFIED preserved)",
        bg_color="#451433", border_color="#FF006E"
    )
    draw_rule_card(
        26, 14, 19, 20, "CIT_RETRACTION_WATCH",
        "retraction_db", "not_exists", "ERROR", "Nol Artikel Ditarik (Retracted)",
        bg_color="#451433", border_color="#FF006E"
    )

    # -------------------------------------------------------------
    # 5. GROUP 5: EMPIRICAL THESIS ALIGNMENT (Bottom Right)
    # -------------------------------------------------------------
    draw_group_box(50, 10, 47, 46, "NodeXL Pro Empiris & NLP (ThisIsEconomy)", "#FB5607", "#3B1808", 5)
    draw_rule_card(
        52, 38, 20, 14, "EMPIRICAL_SNA_BASELINE",
        "network_topology", "verify_ground", "INFO", "|V|=971, |E|=666, Q=0.9837",
        bg_color="#54250E", border_color="#FB5607"
    )
    draw_rule_card(
        74, 38, 21, 14, "EMPIRICAL_INDOBERT_9EMO",
        "emotion_distribution", "model_eval", "INFO", "Weighted F1=78.5% (Plutchik)",
        bg_color="#54250E", border_color="#FB5607"
    )
    draw_rule_card(
        52, 14, 20, 20, "EMPIRICAL_SARCASM_GUARD",
        "sarcasm_heuristic", "benchmark", "INFO", "3.395 Korpus, Prevalensi 9.28%",
        bg_color="#54250E", border_color="#FB5607"
    )
    draw_rule_card(
        74, 14, 21, 20, "EMPIRICAL_PHYGITAL_GAP",
        "marketing_6_0", "conceptual", "INFO", "Kebijakan MBG & Kesenjangan Fisik",
        bg_color="#54250E", border_color="#FB5607"
    )

    # -------------------------------------------------------------
    # CENTRAL ENGINE HUB (CONNECTOR NODES)
    # -------------------------------------------------------------
    engine_hub = patches.Circle((47, 54), radius=3.2, facecolor="#101D38", edgecolor="#64D8CB", lw=2.0, zorder=6)
    ax.add_patch(engine_hub)
    ax.text(47, 54.7, "AUDIT", fontsize=8.0, fontweight="bold", color="#64D8CB", ha="center", zorder=7)
    ax.text(47, 53.3, "ENGINE", fontsize=7.5, fontweight="bold", color="#FFFFFF", ha="center", zorder=7)

    # DRAW CONNECTING EDGES FROM EACH RULE CLUSTER TO HUB
    def draw_rule_edge(p1, p2, label="", color="#90E0EF"):
        arrow = patches.FancyArrowPatch(
            p1, p2,
            arrowstyle="-|>",
            mutation_scale=11,
            color=color,
            lw=1.4,
            linestyle=":",
            zorder=6
        )
        ax.add_patch(arrow)
        if label:
            mid_x = (p1[0] + p2[0]) / 2
            mid_y = (p1[1] + p2[1]) / 2
            ax.text(mid_x, mid_y, label, fontsize=7.0, fontweight="bold", color=color, ha="center", zorder=7)

    draw_rule_edge((29, 70), (44, 55), "Format OK", "#3A86FF")
    draw_rule_edge((43, 65), (46, 57), "5 Bab OK", "#06D6A0")
    draw_rule_edge((71, 70), (50, 55), "Math OK", "#8338EC")
    draw_rule_edge((35, 45), (44, 52), "APA 7 OK", "#FF006E")
    draw_rule_edge((52, 45), (49, 52), "SNA OK", "#FB5607")

    # -------------------------------------------------------------
    # METRICS PANE FOOTER
    # -------------------------------------------------------------
    badge = patches.FancyBboxPatch(
        (3, 2), 94, 6.5,
        boxstyle="round,pad=0.3,rounding_size=0.8",
        facecolor="#101D38",
        edgecolor="#64D8CB",
        linewidth=1.5,
        zorder=8
    )
    ax.add_patch(badge)
    ax.text(
        5, 5.5,
        "[METRICS PANE] NODEXL PRO RULE ENGINE TOPOLOGY | Order #14103 | Token: c1d8d71236e1cae9628f0b5c7a55b581",
        fontsize=9.5, fontweight="bold", color="#64D8CB", zorder=9
    )
    ax.text(
        5, 3.2,
        "Total Rules Evaluated: 42 Deterministic Rules across 6 Verification Domains | Execution: 100% Deterministic (Zero-Hallucination)\n"
        "10 Pilar MIKOM 2026: Margin EMU 4-4-3-3, Font TNR 12pt, Spasi 2.0, 5 BAB, Regresi Linear, p<0.05, N-Konsisten, APA 7th, Maks 175 Hal",
        fontsize=8.0, color="#E0E1DD", zorder=9
    )

    plt.tight_layout()
    OUTPUT_PROJECT_PATH.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUT_PROJECT_PATH, dpi=300, facecolor=fig.get_facecolor(), edgecolor="none")
    print(f"✓ Saved Rule Engine image to {OUTPUT_PROJECT_PATH}")

    if OUTPUT_BRAIN_PATH.parent.exists():
        fig.savefig(OUTPUT_BRAIN_PATH, dpi=300, facecolor=fig.get_facecolor(), edgecolor="none")
        print(f"✓ Saved Rule Engine image to brain {OUTPUT_BRAIN_PATH}")

    plt.close(fig)


if __name__ == "__main__":
    create_nodexl_rule_schema()
