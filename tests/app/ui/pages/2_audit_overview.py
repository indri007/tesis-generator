import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Ringkasan Audit", page_icon="📊", layout="wide")

st.title("📊 Ringkasan Eksekutif & Kepatuhan Tesis")
st.caption("Evaluasi Kepatuhan Naskah Berdasarkan Pedoman Penulisan Tesis MIKOM 2026")

# ─────────────────────────────────────────────
# 0. VALIDASI STATE
# ─────────────────────────────────────────────
meta = st.session_state.get("audit_metadata", st.session_state.get("doc_info", {}))
format_findings = st.session_state.get("format_findings", [])
structure_findings = st.session_state.get("structure_findings", [])
citation_findings = st.session_state.get("citation_findings", [])
method_findings = st.session_state.get("method_findings", [])
meta_findings = st.session_state.get("meta_findings", [])
writing_findings = st.session_state.get("writing_findings", [])
plag_report = st.session_state.get("plagiarism_report", None)
counts = st.session_state.get("summary_counts", {
    "PASS": 0,
    "ERROR": len(format_findings) + len(structure_findings),
    "WARNING": 0,
    "UNVERIFIED": 0,
})

if not meta and not format_findings and not structure_findings:
    st.info("ℹ️ Belum ada hasil audit yang dimuat. Unggah dan audit naskah tesis di halaman utama terlebih dahulu.")
    st.stop()

# ─────────────────────────────────────────────
# 1. KPI & SKOR UTAMA
# ─────────────────────────────────────────────
overall_score = st.session_state.get("overall_score", 85.0)

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.metric("Skor Kepatuhan", f"{overall_score}/100")
with col2:
    st.metric("✅ Lolos (Pass)", counts.get("PASS", 0))
with col3:
    st.metric("❌ Pelanggaran (Error)", counts.get("ERROR", len(format_findings)), delta_color="inverse")
with col4:
    st.metric("⚠️ Peringatan (Warn)", counts.get("WARNING", 0), delta_color="inverse")
with col5:
    st.metric("❓ Perlu Verifikasi", counts.get("UNVERIFIED", 0))

st.progress(max(0.0, min(1.0, overall_score / 100.0)), text=f"Indeks Integritas Naskah: {overall_score:.1f}%")
st.divider()

# ─────────────────────────────────────────────
# 2. METADATA DOKUMEN
# ─────────────────────────────────────────────
st.subheader("📄 Informasi Naskah")
mcol1, mcol2, mcol3, mcol4 = st.columns(4)
mcol1.markdown(f"**Nama Berkas:** `{meta.get('filename', 'tesis.docx')}`")
mcol2.markdown(f"**Format:** `{meta.get('file_type', 'DOCX')}`")
mcol3.markdown(f"**Jumlah Halaman:** `{meta.get('page_count', '-')}` halaman")
mcol4.markdown(f"**Estimasi Kata:** `{meta.get('total_words', meta.get('word_count', '-'))}`")

st.divider()

# ─────────────────────────────────────────────
# 3. DISTRIBUSI KATEGORI TEMUAN
# ─────────────────────────────────────────────
st.subheader("📈 Distribusi Temuan Berdasarkan Kategori")

cat_data = [
    {"Kategori": "Format & Tipografi", "Jumlah Temuan": len(format_findings)},
    {"Kategori": "Sistematika Struktur", "Jumlah Temuan": len(structure_findings)},
    {"Kategori": "Sitasi & Bibliografi", "Jumlah Temuan": len(citation_findings)},
    {"Kategori": "Desain Riset & Statistik", "Jumlah Temuan": len(method_findings)},
    {"Kategori": "Meta-Analisis (PRISMA)", "Jumlah Temuan": len(meta_findings)},
    {"Kategori": "Kaidah Bahasa & Diksi", "Jumlah Temuan": len(writing_findings)},
]
if plag_report:
    cat_data.append({"Kategori": "Plagiarisme & AI", "Jumlah Temuan": len(getattr(plag_report, "findings", []))})

cdf = pd.DataFrame(cat_data)

c_col1, c_col2 = st.columns(2)
with c_col1:
    fig_bar = px.bar(
        cdf,
        x="Kategori",
        y="Jumlah Temuan",
        color="Kategori",
        title="Jumlah Pelanggaran per Modul",
        color_discrete_sequence=["#3B82F6", "#F59E0B", "#10B981", "#8B5CF6", "#EC4899", "#14B8A6", "#6366F1"]
    )
    st.plotly_chart(fig_bar, use_container_width=True)

with c_col2:
    fig_pie = px.pie(
        cdf,
        names="Kategori",
        values="Jumlah Temuan",
        title="Proporsi Temuan Kepatuhan",
        color_discrete_sequence=["#3B82F6", "#F59E0B", "#10B981", "#8B5CF6", "#EC4899", "#14B8A6", "#6366F1"]
    )
    st.plotly_chart(fig_pie, use_container_width=True)

st.divider()

# ─────────────────────────────────────────────
# 4. ROADMAP PERBAIKAN PRIORITAS TINGGI
# ─────────────────────────────────────────────
st.subheader("🎯 Prioritas Perbaikan Naskah")
all_findings = []
for f in format_findings:
    all_findings.append({
        "Kategori": "Format",
        "Aturan": getattr(f, "rule_id", "FORMAT") if not isinstance(f, dict) else f.get("rule_id", "FORMAT"),
        "Status": getattr(f, "severity", "WARNING") if not isinstance(f, dict) else f.get("severity", "WARNING"),
        "Deskripsi": getattr(f, "message", getattr(f, "description", str(f))) if not isinstance(f, dict) else f.get("message", str(f)),
        "Rekomendasi": getattr(f, "recommendation", "Sesuaikan dengan pedoman format MIKOM 2026") if not isinstance(f, dict) else f.get("recommendation", "Sesuaikan pedoman format"),
    })
for f in structure_findings:
    all_findings.append({
        "Kategori": "Struktur",
        "Aturan": getattr(f, "rule_id", "STRUCTURE") if not isinstance(f, dict) else f.get("rule_id", "STRUCTURE"),
        "Status": getattr(f, "severity", "ERROR") if not isinstance(f, dict) else f.get("severity", "ERROR"),
        "Deskripsi": getattr(f, "message", getattr(f, "description", str(f))) if not isinstance(f, dict) else f.get("message", str(f)),
        "Rekomendasi": getattr(f, "recommendation", "Lengkapi komponen struktur bab wajib") if not isinstance(f, dict) else f.get("recommendation", "Lengkapi komponen struktur"),
    })
for f in method_findings:
    all_findings.append({
        "Kategori": "Metodologi",
        "Aturan": getattr(f, "rule_id", "METHOD") if not isinstance(f, dict) else f.get("rule_id", "METHOD"),
        "Status": getattr(f, "severity", "WARNING") if not isinstance(f, dict) else f.get("severity", "WARNING"),
        "Deskripsi": getattr(f, "message", getattr(f, "description", str(f))) if not isinstance(f, dict) else f.get("message", str(f)),
        "Rekomendasi": getattr(f, "recommendation", "Perjelas desain riset dan uji biostatistika") if not isinstance(f, dict) else f.get("recommendation", "Perjelas metodologi"),
    })
for f in meta_findings:
    all_findings.append({
        "Kategori": "Meta-Analisis",
        "Aturan": getattr(f, "rule_id", "META") if not isinstance(f, dict) else f.get("rule_id", "META"),
        "Status": getattr(f, "severity", "WARNING") if not isinstance(f, dict) else f.get("severity", "WARNING"),
        "Deskripsi": getattr(f, "message", getattr(f, "description", str(f))) if not isinstance(f, dict) else f.get("message", str(f)),
        "Rekomendasi": getattr(f, "recommendation", "Lengkapi protokol PRISMA dan sintesis efek") if not isinstance(f, dict) else f.get("recommendation", "Lengkapi PRISMA"),
    })
for f in writing_findings:
    all_findings.append({
        "Kategori": "Tata Tulis",
        "Aturan": getattr(f, "rule_id", "ACAD") if not isinstance(f, dict) else f.get("rule_id", "ACAD"),
        "Status": getattr(f, "severity", "WARNING") if not isinstance(f, dict) else f.get("severity", "WARNING"),
        "Deskripsi": getattr(f, "message", getattr(f, "description", str(f))) if not isinstance(f, dict) else f.get("message", str(f)),
        "Rekomendasi": getattr(f, "recommendation", "Gunakan kosakata baku KBBI dan netralitas kalimat") if not isinstance(f, dict) else f.get("recommendation", "Gunakan kata baku KBBI"),
    })

if all_findings:
    st.dataframe(pd.DataFrame(all_findings), use_container_width=True, hide_index=True)
else:
    st.success("🎉 Tidak ada temuan pelanggaran format dan struktur kritis!")
