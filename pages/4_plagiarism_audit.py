import streamlit as st
import pandas as pd
import plotly.express as px
import html

st.set_page_config(page_title="Audit Plagiarisme & AI", page_icon="🤖", layout="wide")

st.title("🤖 Audit Plagiarisme & Konten AI")
st.caption("Deteksi kemiripan leksikal, semantik, dan indikasi teks AI")

# ─────────────────────────────────────────────
# 0. VALIDASI STATE
# ─────────────────────────────────────────────
if "plagiarism_report" not in st.session_state:
    st.info("Belum ada hasil audit. Unggah dokumen di halaman **Upload** terlebih dahulu.")
    st.stop()

report = st.session_state["plagiarism_report"]
document_text = st.session_state.get("document_text", "")
segments = st.session_state.get("plagiarism_segments", [])  # list of dict per kalimat

# ─────────────────────────────────────────────
# 1. KPI RINGKASAN
# ─────────────────────────────────────────────
def verdict_badge(v: str) -> str:
    return {
        "clean": "✅ Bersih",
        "suspicious": "⚠️ Mencurigakan",
        "rejected": "❌ Ditolak",
    }.get(v, v)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Skor Plagiarisme", f"{report.overall_plagiarism_score*100:.0f}%",
          delta_color="inverse")
c2.metric("Skor Konten AI", f"{report.overall_ai_score*100:.0f}%",
          delta_color="inverse")
c3.metric("Segmen Diperiksa", len(segments))
c4.metric("Status Akhir", verdict_badge(report.verdict))

if report.verdict == "rejected":
    st.error("❌ Dokumen ditandai **berisiko tinggi**. Perlu revisi signifikan sebelum submit.")
elif report.verdict == "suspicious":
    st.warning("⚠️ Ada indikasi kemiripan/AI. Tinjau segmen yang ditandai di bawah.")
else:
    st.success("✅ Tidak ada indikasi plagiarisme atau konten AI yang signifikan.")

st.divider()

# ─────────────────────────────────────────────
# 2. HEATMAP KALIMAT
# ─────────────────────────────────────────────
st.subheader("🔥 Heatmap Kalimat")
st.caption("Kalimat dengan latar merah = kemiripan tinggi; kuning = sedang; hijau = aman.")

def sentence_color(score: float) -> str:
    if score >= 0.85: return "#f8d7da"   # merah
    if score >= 0.65: return "#fff3cd"   # kuning
    if score >= 0.40: return "#fffbe6"   # kuning muda
    return "#e8f5e9"                      # hijau

if segments:
    parts = []
    for seg in segments:
        score = seg.get("score", 0.0)
        color = sentence_color(score)
        tooltip = f"Skor: {score*100:.0f}%"
        if seg.get("source"):
            tooltip += f" | Sumber: {seg['source'][:80]}…"
        parts.append(
            f"<span style='background-color:{color};padding:2px 4px;"
            f"border-radius:4px;margin:1px;' title='{html.escape(tooltip)}'>"
            f"{html.escape(seg['text'])}</span>"
        )
    st.markdown(
        f"<div style='line-height:2.2;font-size:15px;'>{' '.join(parts)}</div>",
        unsafe_allow_html=True,
    )

    # Legenda
    lg1, lg2, lg3, lg4 = st.columns(4)
    lg1.markdown("🟥 **≥85%** kemiripan")
    lg2.markdown("🟨 **65–85%**")
    lg3.markdown("🟨 **40–65%**")
    lg4.markdown("🟩 **<40%** aman")
else:
    st.info("Tidak ada segmen yang dianalisis. Pastikan korpus pembanding tersedia.")

st.divider()

# ─────────────────────────────────────────────
# 3. TABEL SEGMEN MIRIP
# ─────────────────────────────────────────────
st.subheader("📋 Segmen dengan Kemiripan Tinggi")

suspicious = [s for s in segments if s.get("score", 0) >= 0.40]
suspicious.sort(key=lambda s: s.get("score", 0), reverse=True)

if suspicious:
    df = pd.DataFrame([{
        "No": i + 1,
        "Kalimat": s["text"][:90] + ("…" if len(s["text"]) > 90 else ""),
        "Skor": f"{s['score']*100:.0f}%",
        "Sumber": (s.get("source") or "-")[:60],
        "Lokasi": s.get("location", "-"),
    } for i, s in enumerate(suspicious)])
    st.dataframe(df, use_container_width=True, hide_index=True)
else:
    st.success("Tidak ada segmen dengan kemiripan ≥40%.")

st.divider()

# ─────────────────────────────────────────────
# 4. DETAIL PER SEGMEN
# ─────────────────────────────────────────────
if suspicious:
    st.subheader("🔍 Detail Segmen")
    labels = [f"{i+1}. [{s['score']*100:.0f}%] {s['text'][:60]}…"
              for i, s in enumerate(suspicious)]
    idx = st.selectbox("Pilih segmen", range(len(suspicious)),
                       format_func=lambda i: labels[i])
    s = suspicious[idx]

    d1, d2 = st.columns([2, 1])
    with d1:
        st.markdown(f"**Kalimat:**\n> {s['text']}")
        if s.get("source"):
            st.markdown(f"**Sumber mirip:**\n> {s['source']}")
        if s.get("matched_text"):
            st.markdown(f"**Teks sumber asli:**\n> {s['matched_text']}")
    with d2:
        st.metric("Skor Kemiripan", f"{s['score']*100:.0f}%")
        st.metric("Lokasi", s.get("location", "-"))
        if s.get("checker"):
            st.metric("Metode", s["checker"].upper())

st.divider()

# ─────────────────────────────────────────────
# 5. VISUALISASI DISTRIBUSI SKOR
# ─────────────────────────────────────────────
st.subheader("📊 Distribusi Skor Kemiripan")

if segments:
    scores = [s.get("score", 0) * 100 for s in segments]
    fig = px.histogram(
        x=scores, nbins=20,
        labels={"x": "Skor Kemiripan (%)", "y": "Jumlah Kalimat"},
        title="Sebaran Skor per Kalimat",
        color_discrete_sequence=["#4f46e5"],
    )
    fig.add_vline(x=85, line_dash="dash", line_color="red",
                  annotation_text="Ambang kritis")
    fig.add_vline(x=65, line_dash="dash", line_color="orange",
                  annotation_text="Ambang waspada")
    st.plotly_chart(fig, use_container_width=True)

# ─────────────────────────────────────────────
# 6. INDIKATOR AI
# ─────────────────────────────────────────────
st.divider()
st.subheader("🧠 Indikator Konten AI")

ai_finding = next(
    (f for f in report.findings if "ai" in f.get("checker_name", "")), None
)
if ai_finding:
    a1, a2, a3 = st.columns(3)
    a1.metric("Skor AI", f"{ai_finding['score']*100:.0f}%",
              delta_color="inverse")
    detail = ai_finding.get("matched_segments", [{}])[0]
    a2.metric("Perplexity Rata-rata",
              f"{detail.get('avg_perplexity', 0):.1f}")
    a3.metric("Burstiness", f"{detail.get('burstiness', 0):.3f}")

    st.caption(
        "Teks AI cenderung memiliki **perplexity rendah** (mudah diprediksi) "
        "dan **burstiness rendah** (variasi kalimat seragam)."
    )
else:
    st.info("Detektor AI tidak dijalankan pada audit ini.")

# ─────────────────────────────────────────────
# 7. EKSPOR
# ─────────────────────────────────────────────
st.divider()
st.subheader("💾 Ekspor Hasil")

e1, e2, e3 = st.columns(3)
with e1:
    if segments:
        exp_df = pd.DataFrame(segments)
        st.download_button("⬇️ CSV Segmen",
                           exp_df.to_csv(index=False).encode("utf-8"),
                           "plagiarism_segments.csv", "text/csv")
with e2:
    st.download_button("⬇️ JSON Laporan",
                       pd.DataFrame([report.__dict__]).to_json(
                           orient="records", indent=2).encode("utf-8"),
                       "plagiarism_report.json", "application/json")
with e3:
    if st.button("📄 Laporan PDF Plagiarisme"):
        from engines.report_engine import generate_plagiarism_report
        pdf = generate_plagiarism_report(report, segments)
        st.download_button("⬇️ Unduh", pdf,
                           "plagiarism_report.pdf", "application/pdf")
