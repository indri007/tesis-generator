"""Generate NodeXL Pro Group-in-a-Box (GIB) Entity-Relationship Diagram (ERD).

Visualizes the relational database schema of TesisCheck MIKOM 2026, structured into
5 thematic treemap partition boxes matching NodeXL Pro aesthetics:
1. Guideline & Rule Engine Cluster
2. Manuscript & Document Cluster
3. Academic Literature & Verification Cluster
4. Audit & Auto-Revision Cluster
5. NodeXL Pro Empirical SNA Cluster
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.patches as patches
import matplotlib.pyplot as plt

ROOT_DIR = Path(__file__).resolve().parent.parent
OUTPUT_PROJECT_PATH = ROOT_DIR / "assets" / "images" / "17_erd_nodexl_database_schema.png"
OUTPUT_BRAIN_PATH = Path("/Users/jevin/.gemini/antigravity-cli/brain/a70d9257-5726-4a1c-ba67-172afa9c412b/17_erd_nodexl_database_schema.png")


def create_nodexl_erd():
    fig = plt.figure(figsize=(18, 12), dpi=300, facecolor="#0B132B")
    ax = fig.add_subplot(111)
    ax.set_facecolor("#0B132B")
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")

    # Header Title Banner
    ax.text(
        50, 97.5,
        "TesisCheck MIKOM 2026 — Entity-Relationship Diagram (ERD)",
        ha="center", va="center", fontsize=20, fontweight="bold", color="#FFFFFF", fontfamily="sans-serif"
    )
    ax.text(
        50, 95.0,
        "NodeXL Pro Group-in-a-Box (GIB) Relational Schema Partitioning | Token: c1d8d71236e1cae9628f0b5c7a55b581",
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
        # Group Header Banner
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

    # Helper function for drawing table entities
    def draw_entity(x, y, w, h, name, pk, fks, fields, bg_color="#1C2541", border_color="#48CAE4"):
        # Card background
        card = patches.FancyBboxPatch(
            (x, y), w, h,
            boxstyle="round,pad=0.3,rounding_size=0.8",
            facecolor=bg_color,
            edgecolor=border_color,
            linewidth=1.2,
            zorder=4
        )
        ax.add_patch(card)
        # Header title
        ax.text(
            x + w / 2, y + h - 1.4,
            name,
            ha="center", va="center", fontsize=10, fontweight="bold", color="#FFFFFF", zorder=5
        )
        # Divider line
        ax.plot([x + 0.5, x + w - 0.5], [y + h - 2.5, y + h - 2.5], color=border_color, lw=1.0, zorder=5)

        # Field list
        curr_y = y + h - 3.7
        # PK
        ax.text(x + 1.0, curr_y, f"[PK] {pk}", fontsize=8.5, fontweight="bold", color="#FFD166", zorder=5)
        curr_y -= 1.6
        # FKs
        for fk in fks:
            ax.text(x + 1.0, curr_y, f"[FK] {fk}", fontsize=8.0, color="#64D8CB", zorder=5)
            curr_y -= 1.5
        # Regular fields
        for f in fields:
            ax.text(x + 1.0, curr_y, f"• {f}", fontsize=7.5, color="#E0E1DD", zorder=5)
            curr_y -= 1.4

    # -------------------------------------------------------------
    # 1. GROUP 1: GUIDELINE & RULE DEFINITION (Top Left)
    # -------------------------------------------------------------
    draw_group_box(3, 62, 28, 30, "Pedoman & Rule Engine", "#3A86FF", "#111E38", 1)
    draw_entity(
        5, 78, 24, 11, "guideline_profiles",
        "profile_id (TEXT)", [], ["university_name", "program_study (MIKOM)", "version (2026.1)", "config_json"],
        bg_color="#182747", border_color="#3A86FF"
    )
    draw_entity(
        5, 64, 24, 11, "rule_definitions",
        "rule_id (TEXT)", ["profile_id (FK)"], ["category (Format, Cit, ...)", "severity (ERR, WARN)", "operator (recalculate)"],
        bg_color="#182747", border_color="#3A86FF"
    )

    # -------------------------------------------------------------
    # 2. GROUP 2: MANUSCRIPT & DOCUMENT (Top Middle)
    # -------------------------------------------------------------
    draw_group_box(34, 58, 32, 34, "Naskah & Sitasi Teks", "#06D6A0", "#0D2E2B", 2)
    draw_entity(
        36, 77, 28, 12, "projects",
        "project_id (TEXT)", ["guideline_id (FK)"], ["title", "author_name", "nim", "created_at"],
        bg_color="#133D37", border_color="#06D6A0"
    )
    draw_entity(
        36, 61, 13.5, 13, "documents",
        "document_id (TEXT)", ["project_id (FK)"], ["file_type (DOCX/PDF)", "total_pages (<=175)", "sha256_hash"],
        bg_color="#133D37", border_color="#06D6A0"
    )
    draw_entity(
        50.5, 61, 13.5, 13, "in_text_citations",
        "citation_id (TEXT)", ["document_id (FK)"], ["raw_citation", "author_key", "publication_year", "paragraph_idx"],
        bg_color="#133D37", border_color="#06D6A0"
    )

    # -------------------------------------------------------------
    # 3. GROUP 3: ACADEMIC LITERATURE & VERIFICATION (Top Right)
    # -------------------------------------------------------------
    draw_group_box(69, 58, 28, 34, "Verifikasi Literatur & Q1", "#8338EC", "#24143D", 3)
    draw_entity(
        71, 78, 24, 11.5, "reference_masters",
        "doi (TEXT PK)", [], ["clean_title", "authors_json", "publication_year", "verification_status"],
        bg_color="#311D53", border_color="#8338EC"
    )
    draw_entity(
        71, 65, 11.5, 10.5, "scopus_records",
        "issn_l (PK)", [], ["journal_title", "quartile (Q1-Q4)", "is_verified"],
        bg_color="#311D53", border_color="#8338EC"
    )
    draw_entity(
        83.5, 65, 11.5, 10.5, "consensus_claims",
        "claim_id (PK)", ["doi (FK)"], ["consensus_yes_pct", "study_design"],
        bg_color="#311D53", border_color="#8338EC"
    )

    # -------------------------------------------------------------
    # 4. GROUP 4: AUDIT SESSIONS & REVISION (Bottom Left)
    # -------------------------------------------------------------
    draw_group_box(3, 10, 44, 46, "Sesi Audit & Auto-Revisi Dokumen", "#FF006E", "#300D22", 4)
    draw_entity(
        5, 38, 19, 14, "audit_sessions",
        "session_id (TEXT)", ["project_id (FK)", "document_id (FK)"], ["compliance_score (0-100)", "errors_count", "unverified_count"],
        bg_color="#451433", border_color="#FF006E"
    )
    draw_entity(
        26, 38, 19, 14, "audit_findings",
        "finding_id (TEXT)", ["session_id (FK)", "rule_id (FK)"], ["status (PASS, ERROR)", "recommendation", "excerpt"],
        bg_color="#451433", border_color="#FF006E"
    )
    draw_entity(
        5, 14, 19, 20, "revision_proposals",
        "proposal_id (TEXT)", ["session_id (FK)", "resulting_doc_id (FK)"], ["policy_tier (AUTO, APP)", "status (PENDING, APP)"],
        bg_color="#451433", border_color="#FF006E"
    )
    draw_entity(
        26, 14, 19, 20, "change_logs",
        "log_id (TEXT)", ["proposal_id (FK)"], ["rule_id", "action_type", "before_state", "after_state", "applied_by"],
        bg_color="#451433", border_color="#FF006E"
    )

    # -------------------------------------------------------------
    # 5. GROUP 5: NODEXL EMPIRICAL SNA CLUSTER (Bottom Right)
    # -------------------------------------------------------------
    draw_group_box(50, 10, 47, 46, "NodeXL Pro SNA Empirical Network (ThisIsEconomy)", "#FB5607", "#3B1808", 5)
    draw_entity(
        52, 38, 20, 14, "nodexl_snapshots",
        "token (TEXT PK)", [], ["total_nodes (971)", "total_edges (666)", "modularity (0.9837)", "graph_density (0.00071)"],
        bg_color="#54250E", border_color="#FB5607"
    )
    draw_entity(
        74, 38, 21, 14, "nodexl_communities",
        "community_id (PK)", ["token (FK)"], ["cluster_name", "dominant_topic", "member_count", "dominant_emotion"],
        bg_color="#54250E", border_color="#FB5607"
    )
    draw_entity(
        52, 14, 20, 20, "nodexl_nodes",
        "actor_id (TEXT PK)", ["token (FK)", "comm_id (FK)"], ["label (@grok, @prabowo)", "degree_centrality", "betweenness", "dominant_emotion"],
        bg_color="#54250E", border_color="#FB5607"
    )
    draw_entity(
        74, 14, 21, 20, "nodexl_edges",
        "edge_id (TEXT PK)", ["token (FK)", "src_id (FK)", "tgt_id (FK)"], ["rel_type (mention, reply)", "weight", "is_bridge_edge"],
        bg_color="#54250E", border_color="#FB5607"
    )

    # -------------------------------------------------------------
    # DRAW INTER-CLUSTER & INTRA-CLUSTER RELATIONSHIP LINES (EDGES)
    # -------------------------------------------------------------
    def draw_edge(p1, p2, label="", rad=0.2, color="#90E0EF"):
        arrow = patches.FancyArrowPatch(
            p1, p2,
            connectionstyle=f"arc3,rad={rad}",
            arrowstyle="-|>",
            mutation_scale=12,
            color=color,
            lw=1.5,
            linestyle="--",
            zorder=6
        )
        ax.add_patch(arrow)
        if label:
            mid_x = (p1[0] + p2[0]) / 2
            mid_y = (p1[1] + p2[1]) / 2 + (rad * 4)
            ax.text(mid_x, mid_y, label, fontsize=7.5, fontweight="bold", color=color, ha="center", zorder=7)

    # 1. guideline -> rules
    draw_edge((17, 78), (17, 75), "1:N", rad=0.0, color="#3A86FF")
    # 2. guideline -> projects
    draw_edge((29, 83), (36, 83), "1:N", rad=-0.1, color="#64D8CB")
    # 3. projects -> documents
    draw_edge((43, 77), (43, 74), "1:N", rad=0.0, color="#06D6A0")
    # 4. documents -> in_text_citations
    draw_edge((49.5, 68), (50.5, 68), "1:N", rad=0.0, color="#06D6A0")
    # 5. in_text_citations -> reference_masters
    draw_edge((64, 70), (71, 80), "N:1 (DOI)", rad=-0.15, color="#8338EC")
    # 6. reference_masters -> scopus_records
    draw_edge((76, 78), (76, 75.5), "N:1 (ISSN)", rad=0.0, color="#8338EC")
    # 7. reference_masters -> consensus_claims
    draw_edge((89, 78), (89, 75.5), "1:N (DOI)", rad=0.0, color="#8338EC")
    # 8. projects -> audit_sessions
    draw_edge((36, 79), (24, 48), "1:N", rad=0.15, color="#FF006E")
    # 9. documents -> audit_sessions
    draw_edge((36, 64), (20, 52), "1:N", rad=-0.1, color="#FF006E")
    # 10. audit_sessions -> audit_findings
    draw_edge((24, 44), (26, 44), "1:N", rad=0.0, color="#FF006E")
    # 11. rule_definitions -> audit_findings
    draw_edge((29, 66), (32, 52), "1:N", rad=0.1, color="#3A86FF")
    # 12. audit_sessions -> revision_proposals
    draw_edge((14, 38), (14, 34), "1:N", rad=0.0, color="#FF006E")
    # 13. revision_proposals -> change_logs
    draw_edge((24, 24), (26, 24), "1:N", rad=0.0, color="#FF006E")
    # 14. audit_sessions -> nodexl_snapshots (Empirical Link)
    draw_edge((24, 41), (52, 41), "1:1 Bridge", rad=0.1, color="#FB5607")
    # 15. nodexl_snapshots -> nodexl_communities
    draw_edge((72, 45), (74, 45), "1:N", rad=0.0, color="#FB5607")
    # 16. nodexl_snapshots -> nodexl_nodes
    draw_edge((62, 38), (62, 34), "1:N", rad=0.0, color="#FB5607")
    # 17. nodexl_snapshots -> nodexl_edges
    draw_edge((68, 38), (76, 34), "1:N", rad=-0.1, color="#FB5607")
    # 18. nodexl_communities -> nodexl_nodes
    draw_edge((78, 38), (68, 34), "1:N", rad=0.1, color="#FFBE0B")

    # -------------------------------------------------------------
    # NODEXL METRICS PANE (Standard NodeXL Pro Corner Badge)
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
        "[METRICS PANE] NODEXL PRO GRAPH METRICS PANE | Academic Order #14103 | Token: c1d8d71236e1cae9628f0b5c7a55b581",
        fontsize=9.5, fontweight="bold", color="#64D8CB", zorder=9
    )
    ax.text(
        5, 3.2,
        "Total Entities: 16 Tables | Relational Edges: 18 Foreign Keys | Treemap Clusters: 5 Groups | Layout: Group-in-a-Box (GIB)\n"
        "SNA Baseline: |V|=971 Nodes, |E|=666 Edges, Modularity Q=0.9837, Density=0.00071 | Database: SQLite 3 WAL with Foreign Keys Enforced",
        fontsize=8.0, color="#E0E1DD", zorder=9
    )

    plt.tight_layout()
    # Save to both paths
    OUTPUT_PROJECT_PATH.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUT_PROJECT_PATH, dpi=300, facecolor=fig.get_facecolor(), edgecolor="none")
    print(f"✓ Saved ERD image to {OUTPUT_PROJECT_PATH}")

    if OUTPUT_BRAIN_PATH.parent.exists():
        fig.savefig(OUTPUT_BRAIN_PATH, dpi=300, facecolor=fig.get_facecolor(), edgecolor="none")
        print(f"✓ Saved ERD image to brain {OUTPUT_BRAIN_PATH}")

    plt.close(fig)


if __name__ == "__main__":
    create_nodexl_erd()
