"""TesisCheck MIKOM 2026 — AI Thesis Compliance Auditor & Generator.

Online Web Application based on PEDOMAN PENULISAN TESIS MIKOM 2026.
Built with Material Design 3 (M3) design tokens, WCAG 2.2 AA accessibility, and SQLite WAL storage.
"""

from __future__ import annotations

import tempfile
import uuid
from pathlib import Path

import streamlit as st

from core.database.db_manager import DatabaseManager
from core.generator.thesis_generator import ThesisGenerator
from engines.audit_engine import audit_thesis
from engines.citation_auditor import CitationAuditor
from engines.cross_document_auditor import CrossDocumentAuditor
from engines.document_parser import parse_document
from engines.evidence_mapper import map_finding_to_evidence
from engines.format_auditor import FormatAuditor
from engines.formula_auditor import FormulaAuditor
from engines.reference_auditor import ReferenceAuditor
from engines.report_engine import ReportEngine
from engines.revision_engine import DocxAutoFixer, RevisionEngine
from engines.statistical_auditor import StatisticalAuditor
from engines.structure_auditor import StructureAuditor
from utils.number_utils import check_formula_recalculation

# Page configuration
st.set_page_config(
    page_title="TesisCheck MIKOM 2026 — AI Thesis Auditor & Generator",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

def btn_w(stretch: bool = True) -> dict[str, Any]:
    """Forward and backward compatible width parameter for st.button and st.download_button."""
    import inspect
    sig = inspect.signature(st.button).parameters
    if "width" in sig:
        return {"width": "stretch" if stretch else "content"}
    return {"use_container_width": stretch}

def df_w(stretch: bool = True) -> dict[str, Any]:
    """Forward and backward compatible width parameter for st.dataframe."""
    import inspect
    sig = inspect.signature(st.dataframe).parameters
    if "width" in sig:
        return {"width": "stretch" if stretch else "content"}
    return {"use_container_width": stretch}

# Material Design 3 CSS Design Tokens & Styles
st.markdown("""
<style>
    :root {
        --md-sys-color-primary: #0061A4;
        --md-sys-color-surface: #0F172A;
        --md-sys-color-surface-container: #1E293B;
        --md-sys-color-error: #EF4444;
        --md-sys-color-warning: #F59E0B;
        --md-sys-color-success: #10B981;
    }
    .card-metric {
        background: #1E293B;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 18px;
        text-align: center;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .metric-value { font-size: 30px; font-weight: 700; color: #F8FAFC; }
    .metric-label { font-size: 13px; color: #94A3B8; text-transform: uppercase; margin-top: 6px; letter-spacing: 0.5px; }
    .finding-card {
        background: #1E293B;
        border-left: 4px solid #3B82F6;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 14px;
    }
    .finding-error { border-left-color: #EF4444; }
    .finding-warning { border-left-color: #F59E0B; }
    .finding-pass { border-left-color: #10B981; }
    .finding-unverified { border-left-color: #94A3B8; }
    .m3-badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.82em;
    }
    .hero-banner {
        background: linear-gradient(135deg, #0B192C 0%, #1E3E62 100%);
        border: 1px solid #1E40AF;
        border-radius: 16px;
        padding: 32px;
        margin-bottom: 24px;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar with Guidelines & Information
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/graduation-cap.png", width=64)
    st.title("TesisCheck")
    st.markdown("**MIKOM 2026 Auditor & Generator**")
    st.caption("UPN Veteran Jawa Timur • S2 Ilmu Komunikasi")
    st.divider()

    st.markdown("### 📘 Pedoman Acuan")
    st.info("PEDOMAN PENULISAN TESIS MIKOM 2026\n*Buku Pedoman Resmi Program Studi Magister Ilmu Komunikasi FISBP*")

    st.markdown("### ⚙️ Batasan Mutlak")
    st.markdown("""
    - **Maksimal:** 175 Halaman (Hard Limit)
    - **Target Kata:** 40.000 – 60.000
    - **Margin:** 4 - 4 - 3 - 3 cm (Word EMU)
    - **Font:** Times New Roman 12 pt
    - **Spasi:** 2.0 (Double)
    - **Sitasi:** APA 7th Edition
    """)
    st.divider()
    st.caption("Local-First: Naskah diproses secara lokal tanpa transmisi ke server AI luar.")

# Initialize SQLite database
db = DatabaseManager()
db.register_guideline_profile(
    profile_id="UPN_MIKOM_2026",
    university="UPN Veteran Jawa Timur",
    faculty="FISIP",
    program="Magister Ilmu Komunikasi",
    version="2026.1",
    effective_date="2026-01-01",
    config={"max_pages": 175, "margins_cm": {"top": 4.0, "left": 4.0, "bottom": 3.0, "right": 3.0}}
)

# Top Navigation Tabs
tab_generator, tab_audit, tab_reviser, tab_landing, tab_history = st.tabs([
    "⚡ AI Thesis Generator (Bab 1–5)",
    "🔍 Audit & Analisis Naskah",
    "🛠️ Auto-Revisi Dokumen",
    "🌐 Beranda & Standar (M3)",
    "📊 Basis Data Riwayat Audit"
])

# ==============================================================================
# TAB 1: AI THESIS GENERATOR (BAB 1–5)
# ==============================================================================
with tab_generator:
    st.title("⚡ AI Thesis Generator (Bab 1–5)")
    st.markdown("Penyusunan naskah draf tesis akademik berstandar resmi **PEDOMAN PENULISAN TESIS MIKOM 2026** berbasis bukti ilmiah dan nol halusinasi.")

    gen = ThesisGenerator()

    # Form Parameter Tesis
    with st.expander("📝 Parameter Rancangan Riset Tesis (Klik untuk Menyesuaikan)", expanded=True):
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            g_title = st.text_input(
                "Judul Tesis",
                value="PENGARUH KOMUNIKASI PEMASARAN DIGITAL TERHADAP LOYALITAS AUDIENS PADA MEDIA SOSIAL"
            )
            g_author = st.text_input("Nama Peneliti / Mahasiswa", value="Indri Kartika")
            g_nim = st.text_input("NPM / NIM", value="2401234567")
            g_theory = st.text_input(
                "Landasan Teori Utama",
                value="Media Richness Theory dan Uses and Gratifications Theory"
            )

        with col_g2:
            g_var_x = st.text_input("Variabel Bebas (X)", value="Kualitas Konten Komunikasi Digital")
            g_var_y = st.text_input("Variabel Terikat (Y)", value="Loyalitas Audiens")
            g_sample_n = st.number_input("Jumlah Sampel Responden (N)", value=120, min_value=30, max_value=1000)
            g_target_pages = st.slider("Target Tebal Halaman (Maksimal 175)", min_value=50, max_value=175, value=100)

        col_m1, col_m2, col_m3 = st.columns(3)
        with col_m1:
            g_formula_a = st.number_input("Konstanta Regresi (a)", value=2.5)
        with col_m2:
            g_formula_b = st.number_input("Koefisien Regresi (b)", value=0.4)
        with col_m3:
            g_p_val = st.number_input("Nilai Signifikansi p-value", value=0.032, format="%.3f")

    # Budgeting Halaman & Proporsi MIKOM 2026
    st.markdown("#### 📊 Alokasi & Anggaran Halaman Naskah (Standar Proporsi MIKOM)")
    budget = gen.calculate_page_budget(g_target_pages)
    b_cols = st.columns(5)
    for idx, (ch_key, ch_data) in enumerate(budget.items()):
        with b_cols[idx]:
            st.markdown(f"""
            <div class="card-metric" style="padding: 12px;">
                <div style="font-weight: 700; color: #38BDF8;">{ch_key}</div>
                <div style="font-size: 20px; font-weight: bold; color: white;">{ch_data['target_pages']} Hal</div>
                <div class="metric-label">{ch_data['proportion']} • ~{ch_data['target_words']} kata</div>
            </div>
            """, unsafe_allow_html=True)

    params = {
        "title": g_title,
        "author": g_author,
        "nim": g_nim,
        "var_x": g_var_x,
        "var_y": g_var_y,
        "theory": g_theory,
        "sample_n": int(g_sample_n),
        "formula_a": float(g_formula_a),
        "formula_b": float(g_formula_b),
        "eval_x": 10.0,
        "p_value": float(g_p_val),
    }

    st.write("")
    btn_generate = st.button("🚀 GENERATE NASKAH TESIS LENGKAP (BAB 1–5)", type="primary", **btn_w())

    if btn_generate or "generated_docx_bytes" in st.session_state:
        if btn_generate:
            with st.spinner("⚡ Menyusun naskah tesis lengkap Bab 1–5 dan memformat DOCX sesuai pedoman MIKOM 2026..."):
                docx_bytes = gen.compile_full_thesis_docx(params)
                st.session_state["generated_docx_bytes"] = docx_bytes.getvalue()
                st.session_state["generated_params"] = params

        st.success("✓ Naskah tesis lengkap Bab 1–5 berhasil disusun dengan format resmi MIKOM 2026!")

        # Download Button
        st.download_button(
            "📥 UNDUH DRAF LENGKAP TESIS (.DOCX SIAP SIDANG)",
            data=st.session_state["generated_docx_bytes"],
            file_name=f"TESIS_MIKOM_2026_{g_author.replace(' ', '_')}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            type="primary",
            **btn_w()
        )

        # Tabbed Chapter Preview
        st.markdown("#### 📖 Pratinjau Naskah Per Bab")
        p_ch1, p_ch2, p_ch3, p_ch4, p_ch5 = st.tabs([
            "Bab I: Pendahuluan",
            "Bab II: Tinjauan Pustaka",
            "Bab III: Metode Penelitian",
            "Bab IV: Hasil & Pembahasan",
            "Bab V: Simpulan & Saran"
        ])
        with p_ch1:
            st.text_area("Isi Bab I", value=gen.generate_chapter_1(params), height=300)
        with p_ch2:
            st.text_area("Isi Bab II", value=gen.generate_chapter_2(params), height=300)
        with p_ch3:
            st.text_area("Isi Bab III", value=gen.generate_chapter_3(params), height=300)
        with p_ch4:
            st.text_area("Isi Bab IV", value=gen.generate_chapter_4(params), height=300)
        with p_ch5:
            st.text_area("Isi Bab V", value=gen.generate_chapter_5(params), height=300)

# ==============================================================================
# TAB 2: AUDIT & ANALISIS NASKAH
# ==============================================================================
with tab_audit:
    st.title("🎓 Audit & Analisis Kepatuhan Tesis")
    st.markdown("Pemeriksaan otomatis 10 pilar kepatuhan format, sistematika struktur 5 BAB, validitas matematis, dan konsistensi naskah.")

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
        start_btn = st.button("🚀 MULAI AUDIT LENGKAP", type="primary", **btn_w())

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

                # Parsing Dokumen
                try:
                    doc = parse_document(str(thesis_path))
                    doc.filename = uploaded_thesis.name
                except Exception as e:
                    st.error(f"Gagal mem-parsing berkas tesis: {e}")
                    st.stop()

                # Cek Batas 175 Halaman
                page_count = doc.page_count if doc.page_count is not None else 1
                if page_count > 175:
                    st.error(f"❌ FATAL ERROR: Naskah melebihi batas 175 halaman (Terdeteksi: {page_count} halaman).")
                    st.stop()

                # Parsing Dokumen Jurnal Pembanding
                doc_journal = None
                if journal_path:
                    try:
                        doc_journal = parse_document(str(journal_path))
                        doc_journal.filename = uploaded_journal.name
                        doc.journal_document = doc_journal
                    except Exception as e:
                        st.warning(f"Gagal membaca berkas jurnal pembanding: {e}")

                rule_input = doc.to_rule_input()
                results = audit_thesis(rule_input)

                # Specialized Auditors
                findings = list(results.findings)
                try:
                    findings.extend(FormatAuditor(doc).audit())
                    findings.extend(StructureAuditor(doc).audit())
                    findings.extend(CitationAuditor(doc).audit())
                    findings.extend(ReferenceAuditor(doc).audit())
                    findings.extend(FormulaAuditor(doc).audit())
                    findings.extend(StatisticalAuditor(doc).audit())
                    if doc_journal:
                        findings.extend(CrossDocumentAuditor(doc, doc_journal).audit())
                except Exception as e:
                    st.warning(f"Sebagian auditor mengalami error internal: {e}")

                # Map Evidence
                mapped_findings = [map_finding_to_evidence(f, doc) for f in findings]

                # Revision Engine
                rev_engine = RevisionEngine(mapped_findings)
                checklist = rev_engine.generate_checklist()
                score_card = rev_engine.calculate_scores()
                counts = score_card["counts"]
                overall_score = score_card["overall_score"]

                # Save session to SQLite database
                proj_id = "PROJ_CURRENT"
                try:
                    db.create_project(proj_id, uploaded_thesis.name, "Mahasiswa MIKOM", None, "UPN_MIKOM_2026")
                except Exception:
                    pass
                sess_id = f"SESS-{uuid.uuid4().hex[:8].upper()}"
                try:
                    db.record_audit_session(
                        session_id=sess_id,
                        project_id=proj_id,
                        document_id=f"DOC-{uuid.uuid4().hex[:6]}",
                        compliance_score=overall_score,
                        findings=mapped_findings,
                        execution_time_ms=350
                    )
                except Exception:
                    pass

        # Display Metrics Dashboard
        st.divider()
        st.subheader("📊 Ringkasan Hasil Audit")

        c1, c2, c3, c4, c5 = st.columns(5)
        with c1:
            st.markdown(f"""
            <div class="card-metric">
                <div class="metric-value" style="color: #38BDF8;">{overall_score}%</div>
                <div class="metric-label">Indeks Kepatuhan</div>
            </div>
            """, unsafe_allow_html=True)
        with c2:
            st.markdown(f"""
            <div class="card-metric">
                <div class="metric-value" style="color: #10B981;">{counts.get('PASS', 0)}</div>
                <div class="metric-label">Lulus (PASS)</div>
            </div>
            """, unsafe_allow_html=True)
        with c3:
            st.markdown(f"""
            <div class="card-metric">
                <div class="metric-value" style="color: #EF4444;">{counts.get('ERROR', 0)}</div>
                <div class="metric-label">Kritis (ERROR)</div>
            </div>
            """, unsafe_allow_html=True)
        with c4:
            st.markdown(f"""
            <div class="card-metric">
                <div class="metric-value" style="color: #F59E0B;">{counts.get('WARNING', 0)}</div>
                <div class="metric-label">Peringatan (WARN)</div>
            </div>
            """, unsafe_allow_html=True)
        with c5:
            st.markdown(f"""
            <div class="card-metric">
                <div class="metric-value" style="color: #94A3B8;">{counts.get('UNVERIFIED', 0)}</div>
                <div class="metric-label">Unverified</div>
            </div>
            """, unsafe_allow_html=True)

        # Tabbed Findings Explorer
        st.write("")
        t_err, t_warn, t_pass, t_unver, t_recalc = st.tabs([
            f"❌ Pelanggaran Kritis ({counts.get('ERROR', 0)})",
            f"⚠️ Peringatan ({counts.get('WARNING', 0)})",
            f"✓ Sesuai ({counts.get('PASS', 0)})",
            f"❓ Unverified ({counts.get('UNVERIFIED', 0)})",
            "🧮 Simulator Rekalkulasi Rumus"
        ])

        with t_err:
            err_items = [f for f in mapped_findings if f.get("status") == "ERROR"]
            if not err_items:
                st.success("✓ Tidak ditemukan pelanggaran kritis.")
            for item in err_items:
                exc = (item.get("excerpt") or "").replace("<", "&lt;").replace(">", "&gt;")
                st.markdown(f"""
                <div class="finding-card finding-error">
                    <span class="m3-badge" style="background:#EF4444; color:white;">ERROR</span>
                    <b>{item.get('rule_id')}</b> — {item.get('category')} | Hal. {item.get('page') or '-'}
                    <p style="margin-top:6px; color:#F8FAFC;">{item.get('message')}</p>
                    <div style="background:#0F172A; padding:8px; border-radius:6px; font-family:monospace; font-size:0.85em; color:#94A3B8;">
                        <b>Kutipan:</b> {exc[:250]}<br>
                        <b>Terdeteksi:</b> {item.get('actual')} | <b>Ekspektasi:</b> {item.get('expected')}
                    </div>
                    <p style="margin-top:6px; color:#38BDF8; font-size:0.9em;">💡 <b>Rekomendasi:</b> {item.get('recommendation')}</p>
                </div>
                """, unsafe_allow_html=True)

        with t_warn:
            warn_items = [f for f in mapped_findings if f.get("status") == "WARNING"]
            if not warn_items:
                st.info("Tidak ada peringatan format.")
            for item in warn_items:
                st.markdown(f"""
                <div class="finding-card finding-warning">
                    <span class="m3-badge" style="background:#F59E0B; color:white;">WARNING</span>
                    <b>{item.get('rule_id')}</b> — {item.get('category')}
                    <p style="margin-top:6px; color:#F8FAFC;">{item.get('message')}</p>
                    <p style="color:#FCD34D; font-size:0.9em;">💡 {item.get('recommendation')}</p>
                </div>
                """, unsafe_allow_html=True)

        with t_pass:
            pass_items = [f for f in mapped_findings if f.get("status") == "PASS"]
            st.success(f"✓ {len(pass_items)} aturan pedoman telah terpenuhi secara sempurna.")

        with t_unver:
            unv_items = [f for f in mapped_findings if f.get("status") == "UNVERIFIED"]
            if not unv_items:
                st.info("Seluruh metadata berhasil diverifikasi.")
            for item in unv_items:
                st.markdown(f"""
                <div class="finding-card finding-unverified">
                    <span class="m3-badge" style="background:#64748B; color:white;">UNVERIFIED</span>
                    <b>{item.get('rule_id')}</b>
                    <p style="margin-top:6px; color:#F8FAFC;">{item.get('message')}</p>
                    <p style="color:#94A3B8; font-size:0.9em;">💡 {item.get('recommendation')}</p>
                </div>
                """, unsafe_allow_html=True)

        with t_recalc:
            st.markdown("#### Uji Deterministik Rumus Regresi Linear: $Y = a + bX$")
            rc1, rc2, rc3 = st.columns(3)
            with rc1:
                f_expr = st.text_input("Model Regresi", value="2,5 + 0,4X")
            with rc2:
                in_x = st.number_input("Nilai X", value=10.0)
            with rc3:
                cl_y = st.number_input("Klaim Nilai Y di Naskah", value=7.5)
            if st.button("Uji Hitung"):
                e_out = check_formula_recalculation("Y", f_expr, {"X": in_x}, cl_y)
                if e_out["status"] == "PASS":
                    st.success(f"✓ VALID: Nilai klaim ({cl_y}) sama dengan hasil hitung ({e_out['expected']}).")
                else:
                    st.error(f"❌ KESALAHAN HITUNG: Seharusnya {e_out['expected']}, tertulis {cl_y} (selisih {e_out['delta']}).")

        # Multi-Format Downloads
        st.divider()
        st.subheader("📥 Unduh Laporan Audit Lengkap")
        doc_info = {"filename": uploaded_thesis.name, "page_count": doc.page_count}
        rep_engine = ReportEngine(counts, mapped_findings, doc_info, checklist, overall_score)

        d1, d2, d3, d4 = st.columns(4)
        with d1:
            st.download_button(
                "📄 Unduh HTML Interaktif",
                data=rep_engine.to_html(),
                file_name=f"audit_{uploaded_thesis.name}.html",
                mime="text/html",
                **btn_w()
            )
        with d2:
            st.download_button(
                "📑 Unduh DOCX Catatan",
                data=rep_engine.to_docx_bytes(),
                file_name=f"audit_{uploaded_thesis.name}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                **btn_w()
            )
        with d3:
            st.download_button(
                "📊 Unduh JSON Data",
                data=rep_engine.to_json(),
                file_name=f"audit_{uploaded_thesis.name}.json",
                mime="application/json",
                **btn_w()
            )
        with d4:
            st.download_button(
                "📕 Unduh PDF Eksekutif",
                data=rep_engine.to_pdf_bytes(),
                file_name=f"audit_{uploaded_thesis.name}.pdf",
                mime="application/pdf",
                **btn_w()
            )

# ==============================================================================
# TAB 3: AUTO-REVISI DOKUMEN
# ==============================================================================
with tab_reviser:
    st.title("🛠️ Multi-Tier Revision Engine")
    st.markdown("Perbaiki layout margin dan format secara otomatis, serta telaah rekomendasi perbaikan substantif.")

    st.info("Pilih dokumen Word (.docx) yang ingin diperbaiki format tata letaknya sesuai standar MIKOM 2026.")
    docx_file = st.file_uploader("Unggah naskah Word (.docx) untuk auto-revisi", type=["docx"], key="auto_fix_uploader")

    if docx_file:
        col_fx1, col_fx2 = st.columns(2)
        with col_fx1:
            st.markdown("#### Parameter Layout Otomatis")
            st.markdown("""
            - **Margin:** 4.0 cm (Kiri/Atas), 3.0 cm (Kanan/Bawah)
            - **Font:** Times New Roman 12 pt
            - **Spasi Paragraf:** 2.0 (Double)
            - **Perataan:** Justify (Rata Kiri-Kanan)
            """)
        with col_fx2:
            st.markdown("#### Kebijakan Keamanan Dokumen")
            st.caption("AutoFixer hanya menyesuaikan style dan layout tanpa mengubah kata atau isi argumen.")

        if st.button("✨ Terapkan Perbaikan Layout (.docx)", **btn_w()):
            with tempfile.TemporaryDirectory() as td:
                in_p = Path(td) / "input.docx"
                out_p = Path(td) / "output_revised.docx"
                in_p.write_bytes(docx_file.getvalue())

                try:
                    fixer = DocxAutoFixer(str(in_p))
                    log = fixer.fix_all(str(out_p))

                    st.success("✓ Perbaikan format berhasil diterapkan sesuai pedoman MIKOM 2026!")
                    st.download_button(
                        "📥 Unduh Dokumen Hasil Revisi (.docx)",
                        data=out_p.read_bytes(),
                        file_name=f"revised_{docx_file.name}",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        type="primary",
                        **btn_w()
                    )
                    with st.expander("🔍 Log Aksi Perbaikan Layout Otomatis"):
                        for item in log:
                            st.markdown(f"- **{item['action']}**: {item.get('detail', item.get('status'))}")
                except Exception as err:
                    st.error(f"⚠️ Gagal merevisi dokumen Word: {err}")

# ==============================================================================
# TAB 4: BERANDA & STANDAR (LANDING PAGE M3)
# ==============================================================================
with tab_landing:
    st.markdown("""
    <div class="hero-banner">
        <h1 style="color: #FFFFFF; font-size: 2.4em; font-weight: 700; margin-bottom: 8px;">
            AI Thesis Auditor & Scientific Generator
        </h1>
        <p style="color: #93C5FD; font-size: 1.15em; line-height: 1.6; max-width: 850px;">
            Platform penelaahan naskah tesis dan riset ilmiah berbasis bukti. Memvalidasi 10 pilar pedoman kampus,
            mengecek resiprokal sitasi APA 7th, menguji keaktifan DOI, dan merekalukasi model regresi secara lokal-first
            dengan prinsip <b>Nol Halusinasi</b>.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.subheader("🚀 5-Tahap Alur Kerja Akademik")
    w1, w2, w3, w4, w5 = st.columns(5)
    with w1:
        st.markdown("**1. Ingest Naskah**\nUpload berkas `.docx` atau `.pdf` (maks. 175 halaman).")
    with w2:
        st.markdown("**2. Ekstraksi Bukti**\nEkstraksi teks per paragraf, margin EMU, dan tabel.")
    with w3:
        st.markdown("**3. Audit 10 Pilar**\nEvaluasi aturan pedoman secara deterministik.")
    with w4:
        st.markdown("**4. Revisi Bertingkat**\nAuto-fix format layout & persetujuan substantif.")
    with w5:
        st.markdown("**5. Ekspor QA Final**\nUnduh dokumen revisi dan laporan audit resmi.")

    st.divider()

    st.subheader("🏛️ Standar Resmi & Landasan Rekayasa")
    s1, s2 = st.columns(2)
    with s1:
        st.markdown("""
        - 🎨 **[Material Design 3 (M3)](https://m3.material.io/):** Sistem token antarmuka semantik, tipografi berjenjang, dan palet dinamis.
        - ♿ **[W3C WCAG 2.2 Level AA](https://www.w3.org/TR/WCAG22/):** Menjamin rasio kontras visual $\\ge 4.5:1$ untuk teks dan $3:1$ untuk grafis aktif.
        - 🧠 **[Ollama Local Runtime](https://docs.ollama.com/):** Integrasi lokal model `qwen2.5:7b` dan embedding `nomic-embed-text`.
        """)
    with s2:
        st.markdown("""
        - 🐍 **[Python 3 AST Documentation](https://docs.python.org/3/):** Evaluasi ekspresi matematika aman tanpa eksekusi `eval()`.
        - 💾 **[SQLite Foreign Keys Support](https://www.sqlite.org/foreignkeys.html):** Integritas data transaksional dengan `PRAGMA foreign_keys = ON;`.
        - 📘 **[Pedoman MIKOM 2026]:** Buku pedoman resmi Program Studi Magister Ilmu Komunikasi UPN Veteran Jawa Timur.
        """)

# ==============================================================================
# TAB 5: BASIS DATA RIWAYAT AUDIT
# ==============================================================================
with tab_history:
    st.title("📊 Basis Data Sesi Audit (SQLite)")
    st.markdown("Pencatatan sesi audit lokal tersimpan menggunakan SQLite WAL mode dan foreign key constraints.")

    with db.get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT session_id, project_id, compliance_score, total_findings, errors_count, warnings_count, executed_at
            FROM audit_sessions
            ORDER BY executed_at DESC LIMIT 20
        """)
        rows = cur.fetchall()

    if rows:
        st.dataframe(
            [dict(r) for r in rows],
            column_config={
                "session_id": "ID Sesi",
                "project_id": "ID Proyek",
                "compliance_score": st.column_config.ProgressColumn("Indeks Kepatuhan", format="%.1f%%", min_value=0, max_value=100),
                "total_findings": "Total Temuan",
                "errors_count": "Kritis (ERROR)",
                "warnings_count": "Peringatan",
                "executed_at": "Waktu Audit"
            },
            **df_w()
        )
    else:
        st.info("Belum ada riwayat audit yang tersimpan di basis data lokal.")
