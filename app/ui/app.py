"""TesisCheck MIKOM 2026 — AI Thesis Compliance & Consistency Auditor.

Online Web Application based on PEDOMAN PENULISAN TESIS MIKOM 2026.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import streamlit as st

from engines.audit_engine import audit_thesis
from engines.citation_auditor import CitationAuditor
from engines.cross_document_auditor import CrossDocumentAuditor
from engines.document_parser import parse_document
from engines.evidence_mapper import map_finding_to_evidence
from engines.format_auditor import FormatAuditor
from engines.formula_auditor import FormulaAuditor
from engines.reference_auditor import ReferenceAuditor
from engines.report_engine import ReportEngine
from engines.revision_engine import RevisionEngine
from engines.statistical_auditor import StatisticalAuditor
from engines.structure_auditor import StructureAuditor
from utils.number_utils import check_formula_recalculation

st.set_page_config(
    page_title="TesisCheck MIKOM 2026",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for polished typography & dashboard cards
st.markdown("""
<style>
    .reportview-container { background: #0F172A; }
    .card-metric {
        background: #1E293B;
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 16px;
        text-align: center;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .metric-value { font-size: 28px; font-weight: bold; color: #F8FAFC; }
    .metric-label { font-size: 13px; color: #94A3B8; text-transform: uppercase; margin-top: 4px; }
    .finding-card {
        background: #1E293B;
        border-left: 4px solid #3B82F6;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 12px;
    }
    .finding-error { border-left-color: #EF4444; }
    .finding-warning { border-left-color: #F59E0B; }
    .finding-pass { border-left-color: #10B981; }
    .finding-unverified { border-left-color: #6B7280; }
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/graduation-cap.png", width=64)
    st.title("TesisCheck")
    st.markdown("**MIKOM 2026 Auditor**")
    st.caption("UPN Veteran Jawa Timur")
    st.divider()

    st.markdown("### 📘 Pedoman Acuan")
    st.info("PEDOMAN PENULISAN TESIS MIKOM 2026\n*Buku Pedoman Resmi Program Studi Magister Ilmu Komunikasi FISBP*")

    st.markdown("### ⚙️ Batasan & Standar")
    st.markdown("""
    - **Maksimal:** 175 Halaman
    - **Target Kata:** 40.000 – 60.000
    - **Margin:** 4 - 4 - 3 - 3 cm
    - **Font:** Times New Roman 12 pt
    - **Spasi:** 2.0 (Double)
    - **Gaya Sitasi:** APA 7th Edition
    """)
    st.divider()
    st.caption("Privacy: File diproses di buffer memory dan dibersihkan otomatis.")

# Header
st.title("🎓 TesisCheck MIKOM 2026")
st.markdown("### *AI Thesis Compliance & Consistency Auditor*")
st.markdown("Sistem audit otomatis kepatuhan format, sistematika struktur, validitas matematis, dan konsistensi naskah tesis Magister Ilmu Komunikasi.")

# File Upload Section
col_upload_1, col_upload_2 = st.columns(2)

with col_upload_1:
    st.subheader("1. File Tesis (Wajib)")
    uploaded_thesis = st.file_uploader(
        "Unggah naskah tesis lengkap (.docx atau .pdf, maks. 175 halaman)",
        type=["docx", "pdf"],
        key="thesis_uploader"
    )

with col_upload_2:
    st.subheader("2. Artikel Jurnal (Opsional)")
    uploaded_journal = st.file_uploader(
        "Unggah naskah publikasi jurnal untuk verifikasi konsistensi tesis ↔ jurnal",
        type=["docx", "pdf"],
        key="journal_uploader"
    )

col_cfg1, col_cfg2 = st.columns([2, 1])
with col_cfg1:
    research_type = st.radio(
        "Jenis Pendekatan Penelitian:",
        ["Auto Detect", "Kuantitatif", "Kualitatif"],
        horizontal=True
    )

with col_cfg2:
    st.write("")
    st.write("")
    start_btn = st.button("🚀 MULAI AUDIT LENGKAP", type="primary", use_container_width=True)

# Main Processing Flow
if start_btn:
    if not uploaded_thesis:
        st.error("⚠️ Harap unggah file naskah tesis terlebih dahulu.")
        st.stop()

    suffix_thesis = Path(uploaded_thesis.name).suffix.lower()
    suffix_journal = Path(uploaded_journal.name).suffix.lower() if uploaded_journal else None

    with st.spinner("🔍 Memproses dan mengaudit naskah tesis..."):
        with tempfile.TemporaryDirectory() as temp_dir:
            thesis_path = Path(temp_dir) / f"thesis{suffix_thesis}"
            thesis_path.write_bytes(uploaded_thesis.getvalue())

            journal_path = None
            if uploaded_journal:
                journal_path = Path(temp_dir) / f"journal{suffix_journal}"
                journal_path.write_bytes(uploaded_journal.getvalue())

            try:
                # 1. Parse Thesis
                doc_thesis = parse_document(str(thesis_path))

                # Page count limit check (Requirement #1: max 175 pages)
                if doc_thesis.page_count is not None and doc_thesis.page_count > 175:
                    st.error(f"❌ ERROR — Dokumen melebihi batas maksimum 175 halaman ({doc_thesis.page_count} halaman terdeteksi).")
                    st.stop()

                # Parse Journal if provided
                doc_journal = None
                if journal_path:
                    doc_journal = parse_document(str(journal_path))
                    doc_thesis.journal_document = doc_journal

                # 2. Execute Rule Engine
                rule_input = doc_thesis.to_rule_input()
                audit_res = audit_thesis(rule_input)

                # 3. Specialized Modular Audits
                format_auditor = FormatAuditor(doc_thesis)
                structure_auditor = StructureAuditor(doc_thesis)
                citation_auditor = CitationAuditor(doc_thesis)
                ref_auditor = ReferenceAuditor(doc_thesis)
                formula_auditor = FormulaAuditor(doc_thesis)
                stat_auditor = StatisticalAuditor(doc_thesis)

                additional_findings = (
                    format_auditor.audit() +
                    structure_auditor.audit() +
                    citation_auditor.audit() +
                    ref_auditor.audit() +
                    formula_auditor.audit() +
                    stat_auditor.audit()
                )

                # Cross-document check if journal uploaded
                journal_table = []
                journal_score = None
                if doc_journal:
                    cross_auditor = CrossDocumentAuditor(doc_thesis, doc_journal)
                    j_findings, journal_table, journal_score = cross_auditor.audit()
                    additional_findings.extend(j_findings)

                # Combine all unique findings
                all_raw_findings = audit_res.findings + additional_findings
                unique_findings = []
                seen_keys = set()
                for f in all_raw_findings:
                    key = (f.get("rule_id", ""), f.get("field", ""), f.get("status", ""))
                    if key not in seen_keys:
                        seen_keys.add(key)
                        unique_findings.append(f)

                # 4. Map Evidence
                mapped_findings = [map_finding_to_evidence(f, doc_thesis) for f in unique_findings]

                # 5. Calculate Score strictly (UNVERIFIED is NOT treated as PASS)
                error_count = sum(1 for f in mapped_findings if f.get("finding_status") == "ERROR")
                warn_count = sum(1 for f in mapped_findings if f.get("finding_status") == "WARNING")
                pass_count = audit_res.summary.get("PASS", 0)
                unverified_count = sum(1 for f in mapped_findings if f.get("finding_status") == "UNVERIFIED")

                penalty = (error_count * 15.0) + (warn_count * 5.0) + (unverified_count * 2.0)
                overall_score = max(0.0, min(100.0, 100.0 - penalty))

                # 6. Revision Engine Checklist
                rev_engine = RevisionEngine(mapped_findings)
                checklist = rev_engine.generate_checklist()

                # Save into session state for persistence
                st.session_state["audit_completed"] = True
                st.session_state["doc_info"] = {
                    "filename": doc_thesis.filename,
                    "file_type": doc_thesis.file_type.upper(),
                    "page_count": doc_thesis.page_count or "Perlu rendering DOCX",
                    "total_words": len(doc_thesis.get_text().split()),
                    "has_journal": doc_journal is not None
                }
                st.session_state["summary_counts"] = {
                    "PASS": pass_count,
                    "ERROR": error_count,
                    "WARNING": warn_count,
                    "UNVERIFIED": unverified_count
                }
                st.session_state["overall_score"] = round(overall_score, 1)
                st.session_state["mapped_findings"] = mapped_findings
                st.session_state["checklist"] = checklist
                st.session_state["journal_table"] = journal_table
                st.session_state["journal_score"] = journal_score
                st.session_state["thesis_path"] = str(thesis_path)

            except Exception as e:
                st.error(f"❌ Terjadi kesalahan selama proses audit: {e}")
                st.stop()

# Display Results if Audit Completed
if st.session_state.get("audit_completed"):
    doc_info = st.session_state["doc_info"]
    counts = st.session_state["summary_counts"]
    overall_score = st.session_state["overall_score"]
    findings = st.session_state["mapped_findings"]
    checklist = st.session_state["checklist"]
    journal_table = st.session_state["journal_table"]
    journal_score = st.session_state["journal_score"]

    st.success("✅ Audit naskah selesai diproses!")

    # Summary Cards
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    with c1:
        st.metric("Halaman", doc_info["page_count"])
    with c2:
        st.metric("Total Kata", f"{doc_info['total_words']:,}")
    with c3:
        st.metric("ERROR", counts["ERROR"], delta=f"-{counts['ERROR']}" if counts["ERROR"] > 0 else "0", delta_color="inverse")
    with c4:
        st.metric("WARNING", counts["WARNING"], delta=f"-{counts['WARNING']}" if counts["WARNING"] > 0 else "0", delta_color="inverse")
    with c5:
        st.metric("PASS", counts["PASS"])
    with c6:
        st.metric("UNVERIFIED", counts["UNVERIFIED"])

    # Score Gauge
    score_color = "#10B981" if overall_score >= 80 else ("#F59E0B" if overall_score >= 60 else "#EF4444")
    st.markdown(f"""
    <div style="background: #1E293B; border: 1px solid #334155; border-radius: 12px; padding: 20px; margin: 20px 0; display: flex; align-items: center; justify-content: space-between;">
        <div>
            <h2 style="margin: 0; color: #F8FAFC;">THESIS COMPLIANCE & CONSISTENCY SCORE</h2>
            <p style="margin: 5px 0 0 0; color: #94A3B8;">Berdasarkan Pedoman Penulisan Tesis MIKOM 2026 (Status UNVERIFIED tidak dihitung sebagai lulus)</p>
        </div>
        <div style="text-align: right;">
            <span style="font-size: 42px; font-weight: bold; color: {score_color};">{overall_score}</span>
            <span style="font-size: 20px; color: #94A3B8;"> / 100</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Priority Revision Section
    st.markdown("### 📋 Prioritas Perbaikan Naskah")
    with st.expander("Lihat Rencana Revisi Terprioritas", expanded=True):
        for priority_title, items in checklist.items():
            st.markdown(f"#### {priority_title}")
            if not items:
                st.caption("✓ Tidak ada temuan pada kelompok ini.")
            else:
                for idx, itm in enumerate(items, 1):
                    st.markdown(f"**{idx}. [{itm.get('finding_status')}] {itm.get('rule_id')}** — {itm.get('description')}")
                    st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;*Lokasi:* Halaman {itm.get('page') or '-'} | *Aktual:* `{itm.get('actual')}`")
                    st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;*Rekomendasi:* {itm.get('recommendation')}")

    # Tabs for detailed inspection
    st.markdown("### 🔍 Error Explorer & Kategori Temuan")
    tabs = st.tabs([
        "Semua Temuan",
        "Format & Layout",
        "Struktur & Proporsi",
        "Sitasi & Referensi",
        "Rumus & Perhitungan",
        "Statistik & Sampel",
        "Journal ↔ Tesis",
        "Kalkulator Simulasi"
    ])

    with tabs[0]:
        st.subheader("Semua Temuan Hasil Audit")
        for f in findings:
            st_color = "finding-error" if f.get("finding_status") == "ERROR" else ("finding-warning" if f.get("finding_status") == "WARNING" else "finding-unverified")
            excerpt_text = f.get("excerpt", "")
            excerpt_html = f"<div><b>Bukti Kutipan:</b> <i>'{excerpt_text}'</i></div>" if excerpt_text else ""
            st.markdown(f"""
            <div class="finding-card {st_color}">
                <div style="display: flex; justify-content: space-between;">
                    <b>[{f.get('finding_status')}] {f.get('rule_id')} — {f.get('category')}</b>
                    <span style="color: #94A3B8;">Halaman: {f.get('page') or 'N/A'}</span>
                </div>
                <p style="margin: 8px 0;">{f.get('description')}</p>
                <div style="font-size: 0.9em; background: #0F172A; padding: 10px; border-radius: 6px;">
                    <div><b>Kondisi Aktual:</b> {f.get('actual')}</div>
                    <div><b>Ekspektasi:</b> {f.get('expected')}</div>
                    {excerpt_html}
                </div>
                <p style="margin: 8px 0 0 0; color: #60A5FA;">💡 <b>Rekomendasi:</b> {f.get('recommendation')}</p>
            </div>
            """, unsafe_allow_html=True)

    with tabs[1]:
        st.subheader("Pemeriksaan Format & Tata Letak")
        fmt_findings = [f for f in findings if f.get("category") == "Format"]
        if not fmt_findings:
            st.success("✓ Seluruh format halaman, margin, dan tipografi telah memenuhi Pedoman MIKOM 2026.")
        for f in fmt_findings:
            st.error(f"[{f.get('finding_status')}] {f.get('description')} — {f.get('recommendation')}")

    with tabs[2]:
        st.subheader("Sistematika BAB & Proporsi Kata")
        struct_findings = [f for f in findings if f.get("category") == "Struktur"]
        if not struct_findings:
            st.success("✓ Sistematika 5 BAB dan proporsi kata telah sesuai standar.")
        for f in struct_findings:
            st.warning(f"[{f.get('finding_status')}] {f.get('description')} | Aktual: {f.get('actual')}")

    with tabs[3]:
        st.subheader("Audit Sitasi & Daftar Pustaka (APA 7)")
        cit_findings = [f for f in findings if f.get("category") in ["Sitasi", "Referensi"]]
        if not cit_findings:
            st.success("✓ Seluruh sitasi memiliki rujukan dan sesuai kaidah APA 7.")
        for f in cit_findings:
            st.markdown(f"**[{f.get('finding_status')}] {f.get('description')}**\n- *Aktual:* {f.get('actual')}\n- *Rekomendasi:* {f.get('recommendation')}")

    with tabs[4]:
        st.subheader("Audit Rumus & Konsistensi Matematis")
        form_findings = [f for f in findings if f.get("category") == "Formula"]
        if not form_findings:
            st.success("✓ Persamaan matematis dan hasil perhitungan substitusi telah terverifikasi konsisten.")
        for f in form_findings:
            st.error(f"⚠️ {f.get('description')}\n- Aktual pada teks: `{f.get('actual')}`\n- Seharusnya: `{f.get('expected')}`\n- Rekomendasi: {f.get('recommendation')}")

    with tabs[5]:
        st.subheader("Konsistensi Sampel & Statistik Inferensial")
        stat_findings = [f for f in findings if f.get("category") == "Statistik"]
        if not stat_findings:
            st.success("✓ Jumlah responden dan kesimpulan nilai p terhadap alpha terverifikasi konsisten.")
        for f in stat_findings:
            st.error(f"[{f.get('finding_status')}] {f.get('description')}\n- {f.get('actual')}\n- Rekomendasi: {f.get('recommendation')}")

    with tabs[6]:
        st.subheader("Journal ↔ Thesis Consistency Comparison")
        if not doc_info["has_journal"]:
            st.info("ℹ️ Artikel jurnal tidak diunggah. Unggah file jurnal pada kolom opsional untuk mengaktifkan audit komparasi.")
        else:
            st.metric("Journal Alignment Score", f"{journal_score}%")
            if journal_table:
                st.dataframe(journal_table, use_container_width=True)

    with tabs[7]:
        st.subheader("🧮 Interactive Formula Recalculation Simulator")
        st.markdown("Uji kebenaran aritmetika rumus secara langsung (contoh uji kasus: `Y = 2,5 + 0,4X` pada `X = 10`):")
        calc_c1, calc_c2, calc_c3 = st.columns(3)
        with calc_c1:
            form_expr = st.text_input("Rumus (ekspresi)", value="2,5 + 0,4X")
        with calc_c2:
            input_val = st.number_input("Nilai Input X", value=10.0)
        with calc_c3:
            claimed_res = st.number_input("Nilai Tertulis di Naskah Y", value=7.5)

        recalc_btn = st.button("Hitung & Bandingkan")
        if recalc_btn:
            eval_out = check_formula_recalculation("Y", form_expr, {"X": input_val}, claimed_res)
            if eval_out["status"] == "PASS":
                st.success(f"✓ VALID: Hasil kalkulasi ({eval_out['expected']}) sama dengan klaim naskah ({claimed_res}).")
            else:
                st.error(f"❌ KESALAHAN HITUNG TERDETEKSI: Ekspektasi hitungan adalah {eval_out['expected']}, namun di naskah tertulis {claimed_res} (selisih {eval_out['delta']}).")

    # Download & Export Reports
    st.divider()
    st.subheader("📥 Unduh Laporan Audit & Revisi")

    rep_engine = ReportEngine(
        summary=counts,
        findings=findings,
        document_info=doc_info,
        checklist=checklist,
        overall_score=overall_score
    )

    col_d1, col_d2, col_d3, col_d4 = st.columns(4)
    with col_d1:
        st.download_button(
            "📄 Download Laporan (HTML)",
            data=rep_engine.to_html(),
            file_name=f"audit_report_{doc_info['filename']}.html",
            mime="text/html",
            use_container_width=True
        )
    with col_d2:
        st.download_button(
            "📑 Download Laporan (DOCX)",
            data=rep_engine.to_docx_bytes(),
            file_name=f"audit_report_{doc_info['filename']}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True
        )
    with col_d3:
        st.download_button(
            "📊 Download Laporan (JSON)",
            data=rep_engine.to_json(),
            file_name=f"audit_report_{doc_info['filename']}.json",
            mime="application/json",
            use_container_width=True
        )
    with col_d4:
        # Export checklist
        checklist_text = "CHECKLIST REVISI TESIS MIKOM 2026\n" + "=" * 40 + "\n\n"
        for p_title, items in checklist.items():
            checklist_text += f"{p_title}\n" + "-" * 30 + "\n"
            for itm in items:
                checklist_text += f"[ ] {itm.get('rule_id')}: {itm.get('description')}\n    Rekomendasi: {itm.get('recommendation')}\n\n"
        st.download_button(
            "📋 Export Checklist (.txt)",
            data=checklist_text,
            file_name=f"checklist_revisi_{doc_info['filename']}.txt",
            mime="text/plain",
            use_container_width=True
        )
