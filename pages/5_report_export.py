import streamlit as st
import pandas as pd
import json

st.set_page_config(page_title="Ekspor Laporan", page_icon="📄", layout="wide")

st.title("📄 Ekspor Laporan Audit")
st.caption("Kompilasi seluruh temuan menjadi laporan resmi")

# ─────────────────────────────────────────────
# 0. VALIDASI STATE
# ─────────────────────────────────────────────
REQUIRED = ["audit_metadata", "format_findings", "structure_findings",
            "citation_findings", "plagiarism_report"]
missing = [k for k in REQUIRED if k not in st.session_state]
if missing:
    st.warning("Audit belum lengkap. Selesaikan audit di halaman sebelumnya.")
    st.info(f"Data hilang: {', '.join(missing)}")
    st.stop()

meta = st.session_state["audit_metadata"]
format_f = st.session_state["format_findings"]
struct_f = st.session_state["structure_findings"]
cite_f = st.session_state["citation_findings"]
plag_r = st.session_state["plagiarism_report"]

# ─────────────────────────────────────────────
# 1. KONFIGURASI LAPORAN
# ─────────────────────────────────────────────
st.subheader("⚙️ Konfigurasi Laporan")

c1, c2 = st.columns(2)
with c1:
    include_sections = st.multiselect(
        "Bagian yang disertakan",
        ["Ringkasan Eksekutif", "Format", "Struktur",
         "Sitasi", "Plagiarisme", "Lampiran Detail"],
        default=["Ringkasan Eksekutif", "Format", "Struktur",
                 "Sitasi", "Plagiarisme"],
    )
with c2:
    report_lang = st.radio("Bahasa", ["Indonesia", "English"], horizontal=True)
    include_evidence = st.checkbox("Sertakan bukti (kutipan & lokasi)", value=True)

report_title = st.text_input(
    "Judul Laporan",
    value=f"Laporan Audit Tesis — {meta.get('filename', 'Dokumen')}",
)
author_name = st.text_input("Nama Penyusun (opsional)", value="")

# ─────────────────────────────────────────────
# 2. PRATINJAU RINGKASAN
# ─────────────────────────────────────────────
st.divider()
st.subheader("👁️ Pratinjau Isi Laporan")

preview_rows = []
if "Ringkasan Eksekutif" in include_sections:
    preview_rows.append({"Bagian": "Ringkasan Eksekutif",
                         "Isi": "Skor keseluruhan + roadmap prioritas"})
if "Format" in include_sections:
    preview_rows.append({"Bagian": "Format",
                         "Isi": f"{len(format_f)} temuan"})
if "Struktur" in include_sections:
    preview_rows.append({"Bagian": "Struktur",
                         "Isi": f"{len(struct_f)} temuan"})
if "Sitasi" in include_sections:
    preview_rows.append({"Bagian": "Sitasi",
                         "Isi": f"{len(cite_f)} sitasi diverifikasi"})
if "Plagiarisme" in include_sections:
    plag_s = getattr(plag_r, "overall_plagiarism_score", 0.0) * 100
    ai_s = getattr(plag_r, "overall_ai_score", 0.0) * 100
    preview_rows.append({"Bagian": "Plagiarisme",
                         "Isi": f"Skor {plag_s:.0f}%, AI {ai_s:.0f}%"})
if "Lampiran Detail" in include_sections:
    total_detail = len(format_f) + len(struct_f) + len(cite_f)
    preview_rows.append({"Bagian": "Lampiran Detail",
                         "Isi": f"{total_detail} temuan terperinci"})

st.dataframe(pd.DataFrame(preview_rows), use_container_width=True,
             hide_index=True)

# ─────────────────────────────────────────────
# 3. GENERATE PDF & DOCX
# ─────────────────────────────────────────────
st.divider()
st.subheader("📥 Unduh Laporan")

gen_col1, gen_col2 = st.columns(2)

with gen_col1:
    if st.button("📄 Buat Laporan PDF Lengkap", type="primary"):
        with st.spinner("Menyusun PDF…"):
            from engines.report_engine import generate_full_report
            pdf = generate_full_report(
                meta=meta,
                format_findings=format_f,
                structure_findings=struct_f,
                citation_findings=cite_f,
                plagiarism_report=plag_r,
                sections=include_sections,
                title=report_title,
                author=author_name,
                language=report_lang,
                include_evidence=include_evidence,
            )
            st.session_state["_full_pdf"] = pdf
            st.success("PDF siap diunduh.")
    if "_full_pdf" in st.session_state:
        st.download_button(
            "⬇️ Unduh PDF",
            st.session_state["_full_pdf"],
            f"laporan_audit_{meta.get('filename', 'dokumen')}.pdf",
            "application/pdf",
        )

with gen_col2:
    if st.button("📝 Buat Laporan DOCX"):
        with st.spinner("Menyusun DOCX…"):
            from engines.report_engine import generate_full_report_docx
            docx_bytes = generate_full_report_docx(
                meta=meta,
                format_findings=format_f,
                structure_findings=struct_f,
                citation_findings=cite_f,
                plagiarism_report=plag_r,
                sections=include_sections,
                title=report_title,
                author=author_name,
            )
            st.session_state["_full_docx"] = docx_bytes
            st.success("DOCX siap diunduh.")
    if "_full_docx" in st.session_state:
        st.download_button(
            "⬇️ Unduh DOCX",
            st.session_state["_full_docx"],
            f"laporan_audit_{meta.get('filename', 'dokumen')}.docx",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )

# ─────────────────────────────────────────────
# 4. ARSIP JSON (untuk integrasi / audit trail)
# ─────────────────────────────────────────────
st.divider()
st.subheader("🗂️ Arsip JSON (Audit Trail)")

archive = {
    "metadata": meta,
    "scores": {
        "format": len(format_f),
        "structure": len(struct_f),
        "citation": len(cite_f),
        "plagiarism": getattr(plag_r, "overall_plagiarism_score", 0.0),
        "ai": getattr(plag_r, "overall_ai_score", 0.0),
        "verdict": getattr(plag_r, "verdict", "clean"),
    },
    "findings": {
        "format": [f.__dict__ if hasattr(f, "__dict__") else f for f in format_f],
        "structure": [f.__dict__ if hasattr(f, "__dict__") else f for f in struct_f],
        "citation": [f.__dict__ if hasattr(f, "__dict__") else f for f in cite_f],
        "plagiarism": getattr(plag_r, "findings", []),
    },
}
st.download_button(
    "⬇️ Unduh Arsip JSON Lengkap",
    json.dumps(archive, indent=2, default=str, ensure_ascii=False).encode("utf-8"),
    "audit_archive.json", "application/json",
)
st.caption(
    "Arsip JSON ini dapat digunakan untuk integrasi dengan sistem lain "
    "atau sebagai audit trail yang tidak dapat diubah."
)
