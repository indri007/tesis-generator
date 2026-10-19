"""Audit Executive Summary Dashboard with radar chart and revision roadmap."""

from __future__ import annotations

from typing import Any
import streamlit as st


def render_audit_dashboard(
    format_findings: list[dict[str, Any]],
    word_count: int,
    word_status: str,
    structure_score: int,
    citation_score: int,
    plag_score: int
) -> None:
    st.markdown("### 📊 Executive Summary")

    # ─────────────────────────────────────────────
    # 1. HITUNG SKOR (0 - 100)
    # ─────────────────────────────────────────────
    format_penalty = sum(10 for f in format_findings if f.get("severity") == "ERROR" or f.get("status") == "ERROR")
    format_score = max(0, 100 - format_penalty)

    # Skor Kepatuhan Word Count (40k - 60k)
    if word_status == "PASS":
        word_score = 100
    elif word_status == "WARNING":
        word_score = 70
    else:
        word_score = 40  # ERROR (<40k)

    # ─────────────────────────────────────────────
    # 2. SCORECARDS (METRICS)
    # ─────────────────────────────────────────────
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="Format & Layout",
            value=f"{format_score}/100",
            delta="Lulus" if format_score >= 80 else "Perlu Revisi",
            delta_color="normal" if format_score >= 80 else "inverse"
        )
    with col2:
        st.metric(
            label="Volume Kata",
            value=f"{word_count:,}",
            delta=word_status,
            delta_color="normal" if word_status == "PASS" else "inverse"
        )
    with col3:
        st.metric(
            label="Struktur Bab",
            value=f"{structure_score}/100",
            delta_color="off"
        )
    with col4:
        st.metric(
            label="Kemiripan (Plagiasi)",
            value=f"{plag_score}%",
            delta="Aman" if plag_score < 20 else "Waspada",
            delta_color="normal" if plag_score < 20 else "inverse"
        )

    st.divider()

    # ─────────────────────────────────────────────
    # 3. RADAR CHART (KESEHATAN TESIS)
    # ─────────────────────────────────────────────
    st.markdown("#### 🕸️ Radar Kualitas Tesis")

    categories = ["Format", "Struktur", "Sitasi", "Volume Kata", "Anti-Plagiasi"]
    scores = [format_score, structure_score, citation_score, word_score, max(0, 100 - plag_score)]

    categories_closed = categories + [categories[0]]
    scores_closed = scores + [scores[0]]

    try:
        import plotly.graph_objects as go

        fig = go.Figure()

        # Garis Target Kelulusan (80)
        fig.add_trace(go.Scatterpolar(
            r=[80] * 6,
            theta=categories_closed,
            mode="lines",
            line=dict(color="rgba(239, 68, 68, 0.5)", width=2, dash="dash"),
            name="Target Minimum (80)"
        ))

        # Garis Skor Aktual
        fig.add_trace(go.Scatterpolar(
            r=scores_closed,
            theta=categories_closed,
            fill="toself",
            fillcolor="rgba(99, 102, 241, 0.35)",
            line=dict(color="rgb(99, 102, 241)", width=3),
            name="Skor Anda"
        ))

        fig.update_layout(
            polar=dict(
                radialaxis=dict(visible=True, range=[0, 100], showticklabels=False),
                bgcolor="rgba(15, 23, 42, 0.6)"
            ),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#E2E8F0"),
            showlegend=True,
            margin=dict(l=40, r=40, t=40, b=40),
            height=400
        )

        c_left, c_mid, c_right = st.columns([1, 2, 1])
        with c_mid:
            st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.info(f"Radar kualitas tesis: Format={format_score}, Struktur={structure_score}, Sitasi={citation_score}, Kata={word_score}, Orisinalitas={100 - plag_score}")

    st.divider()

    # ─────────────────────────────────────────────
    # 4. PRIORITAS REVISI (ROADMAP)
    # ─────────────────────────────────────────────
    st.markdown("#### 🎯 Prioritas Revisi")

    dimensions = list(zip(categories, scores))
    dimensions.sort(key=lambda x: x[1])  # Urutkan ascending (terendah dulu)

    for dim, score in dimensions:
        if score >= 90:
            st.success(f"✅ **{dim}** ({score}/100) - Sangat Baik")
        elif score >= 75:
            st.info(f"ℹ️ **{dim}** ({score}/100) - Memadai, tapi bisa ditingkatkan.")
        elif score >= 50:
            st.warning(f"⚠️ **{dim}** ({score}/100) - Butuh perbaikan signifikan.")
        else:
            st.error(f"❌ **{dim}** ({score}/100) - Kritis! Harus segera diperbaiki.")
