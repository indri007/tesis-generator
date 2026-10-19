import streamlit as st
import pandas as pd
import plotly.express as px
from collections import Counter

from engines.citation_auditor import CitationAuditor
from core.mcp_client import AcademicMCPClient, run_async
from core.config import get_mcp_config

st.set_page_config(page_title="Audit Sitasi", page_icon="📚", layout="wide")

# ─────────────────────────────────────────────
# 0. VALIDASI KONFIGURASI & STATE
# ─────────────────────────────────────────────
cfg = get_mcp_config()
if not cfg.get("scopus_url") and not cfg.get("sinta_script"):
    st.error("⚠️ Konfigurasi MCP belum lengkap. Periksa `.env` atau Streamlit Secrets.")
    st.stop()

if "citation_findings" not in st.session_state:
    st.info("Belum ada hasil audit. Unggah dokumen di halaman **Upload** terlebih dahulu.")
    st.stop()

findings: list = st.session_state["citation_findings"]

# ─────────────────────────────────────────────
# 1. HEADER & FILTER
# ─────────────────────────────────────────────
st.title("📚 Audit Verifikasi Sitasi")
st.caption("Verifikasi otomatis ke Scopus & SINTA via MCP")

fcol1, fcol2, fcol3 = st.columns(3)
with fcol1:
    status_filter = st.multiselect(
        "Status", ["verified", "metadata_mismatch", "not_found", "retracted"],
        default=["metadata_mismatch", "not_found", "retracted"],
    )
with fcol2:
    severity_filter = st.multiselect(
        "Severity", ["info", "warning", "critical"],
        default=["warning", "critical"],
    )
with fcol3:
    source_filter = st.multiselect(
        "Sumber", ["scopus", "sinta", "openalex", "unknown"],
        default=["scopus", "sinta", "openalex", "unknown"],
    )

filtered = [
    f for f in findings
    if getattr(f, "status", "unknown") in status_filter
    and getattr(f, "severity", "info") in severity_filter
    and getattr(f, "details", {}).get("source", "unknown") in source_filter
]

# ─────────────────────────────────────────────
# 2. KPI RINGKASAN
# ─────────────────────────────────────────────
status_counts = Counter(getattr(f, "status", "unknown") for f in findings)
total = len(findings)
verified = status_counts.get("verified", 0)
mismatch = status_counts.get("metadata_mismatch", 0)
not_found = status_counts.get("not_found", 0)
health = (verified / total * 100) if total else 0

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Total Sitasi", total)
k2.metric("✅ Terverifikasi", verified, f"{health:.0f}%")
k3.metric("⚠️ Metadata Salah", mismatch, delta_color="inverse")
k4.metric("❌ Tidak Ditemukan", not_found, delta_color="inverse")
k5.metric("🚫 Retracted", status_counts.get("retracted", 0), delta_color="inverse")

st.progress(health / 100, text=f"Kesehatan Sitasi: {health:.1f}%")
st.divider()

# ─────────────────────────────────────────────
# 3. TABEL TEMUAN
# ─────────────────────────────────────────────
st.subheader(f"Temuan ({len(filtered)} dari {total})")

df = pd.DataFrame([{
    "No": i + 1,
    "Lokasi": getattr(f, "evidence_ref", "-"),
    "Sitasi": getattr(f, "citation_text", str(f))[:70] + ("…" if len(getattr(f, "citation_text", str(f))) > 70 else ""),
    "Status": getattr(f, "status", "unknown"),
    "Severity": getattr(f, "severity", "info"),
    "Sumber": getattr(f, "details", {}).get("source", "-"),
} for i, f in enumerate(filtered)])

st.dataframe(df, use_container_width=True, hide_index=True)

# ─────────────────────────────────────────────
# 4. PANEL DETAIL PER TEMUAN
# ─────────────────────────────────────────────
st.divider()
st.subheader("🔍 Detail Temuan")

if filtered:
    labels = [f"{i+1}. [{getattr(f, 'status', 'unknown')}] {getattr(f, 'citation_text', str(f))[:50]}…"
              for i, f in enumerate(filtered)]
    idx = st.selectbox("Pilih temuan", range(len(filtered)),
                       format_func=lambda i: labels[i])
    f = filtered[idx]

    d1, d2 = st.columns([2, 1])
    with d1:
        st.markdown(f"**Sitasi asli:**\n> {getattr(f, 'citation_text', str(f))}")
        st.markdown(f"**Lokasi:** `{getattr(f, 'evidence_ref', '-')}`")
        if getattr(f, "details", {}).get("mismatches"):
            st.warning("**Ketidaksesuaian metadata:**\n- " +
                       "\n- ".join(getattr(f, "details", {})["mismatches"]))
        if getattr(f, "details", {}).get("reason"):
            st.error(f"**Alasan:** {getattr(f, 'details', {})['reason']}")

    with d2:
        st.metric("Status", str(getattr(f, "status", "unknown")).upper())
        st.metric("Severity", str(getattr(f, "severity", "info")).upper())
        st.metric("Sumber", str(getattr(f, "details", {}).get("source", "-")).upper())

        if getattr(f, "details", {}).get("scopus_id"):
            st.link_button(
                "🔗 Buka di Scopus",
                f"https://www.scopus.com/record/display.uri?eid={getattr(f, 'details', {})['scopus_id']}"
            )
        if st.button("🔄 Verifikasi ulang", key=f"reverify_{idx}"):
            with st.spinner("Memverifikasi ulang…"):
                auditor = CitationAuditor(
                    scopus_client=AcademicMCPClient(scopus_url=cfg.get("scopus_url"))
                )
                from engines.document_parser import parse_single_citation
                cite = parse_single_citation(getattr(f, "citation_text", str(f)))
                new = auditor.audit([cite])
                if new:
                    findings[findings.index(f)] = new[0]
                    st.session_state["citation_findings"] = findings
                    st.success("Selesai! Memuat ulang…")
                    st.rerun()

# ─────────────────────────────────────────────
# 5. VISUALISASI & EKSPOR
# ─────────────────────────────────────────────
st.divider()

v1, v2 = st.columns(2)
with v1:
    st_df = pd.DataFrame(status_counts.items(), columns=["Status", "Jumlah"])
    fig = px.pie(st_df, names="Status", values="Jumlah",
                 color="Status",
                 color_discrete_map={
                     "verified": "#28a745",
                     "metadata_mismatch": "#ffc107",
                     "not_found": "#dc3545",
                     "retracted": "#6c757d",
                 },
                 title="Distribusi Status Sitasi")
    st.plotly_chart(fig, use_container_width=True)

with v2:
    src_counts = Counter(getattr(f, "details", {}).get("source", "unknown") for f in findings)
    src_df = pd.DataFrame(src_counts.items(), columns=["Sumber", "Jumlah"])
    fig = px.bar(src_df, x="Sumber", y="Jumlah",
                 title="Sumber Verifikasi",
                 color="Sumber",
                 color_discrete_sequence=["#0d6efd", "#fd7e14", "#6c757d"])
    st.plotly_chart(fig, use_container_width=True)

st.subheader("💾 Ekspor Hasil")
e1, e2, e3 = st.columns(3)
with e1:
    st.download_button("⬇️ CSV", df.to_csv(index=False).encode("utf-8"),
                       "citation_audit.csv", "text/csv")
with e2:
    st.download_button("⬇️ JSON",
                       pd.DataFrame([getattr(f, "__dict__", f) for f in findings])
                       .to_json(orient="records", indent=2).encode("utf-8"),
                       "citation_audit.json", "application/json")
with e3:
    if st.button("📄 Laporan PDF"):
        from engines.report_engine import generate_citation_report
        pdf = generate_citation_report(findings)
        st.download_button("⬇️ Unduh", pdf,
                           "citation_audit_report.pdf", "application/pdf")
