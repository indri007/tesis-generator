"""Academic Similarity Auditor Engine & Streamlit UI Component.

Pure-Python lexical similarity analysis module providing:
- Two-text comparison mode.
- Two-document upload mode (.docx, .pdf, .txt) reusing engines.document_parser.
- Input validation (empty, corrupted, unsupported format, zero-division).
- Lexical metrics: Cosine Similarity, Jaccard Index, token counts, shared vocabulary.
- Privacy-first: strictly local, no external API transmission, no persistent text storage.
- Summary export (CSV / TXT) without exporting full manuscript texts.
"""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

try:
    from core.clones.similarity_plagiarism import (
        compute_cosine_similarity,
        normalize_and_tokenize,
    )
except ImportError:
    import math
    import unicodedata
    from collections import Counter

    def normalize_and_tokenize(text: str) -> list[str]:
        if text is None:
            return []
        if not isinstance(text, str):
            raise TypeError(f"Expected string input, got {type(text).__name__}")
        if not text.strip():
            return []
        normalized = unicodedata.normalize("NFKC", text)
        return re.findall(r"\b[\w-]+\b", normalized.lower(), flags=re.UNICODE)

    def compute_cosine_similarity(text_a: str, text_b: str) -> float:
        tokens_a = normalize_and_tokenize(text_a)
        tokens_b = normalize_and_tokenize(text_b)
        if not tokens_a or not tokens_b:
            return 0.0
        if tokens_a == tokens_b:
            return 1.0
        vec_a = Counter(tokens_a)
        vec_b = Counter(tokens_b)
        common_keys = set(vec_a.keys()) & set(vec_b.keys())
        if not common_keys:
            return 0.0
        dot_product = sum(vec_a[k] * vec_b[k] for k in common_keys)
        sum_a = sum(v * v for v in vec_a.values())
        sum_b = sum(v * v for v in vec_b.values())
        denom = math.sqrt(sum_a) * math.sqrt(sum_b)
        if denom <= 0.0 or not math.isfinite(denom):
            return 0.0
        score = dot_product / denom
        if not math.isfinite(score):
            return 0.0
        return max(0.0, min(1.0, float(score)))

try:
    from core.evaluation.document_integrity_engine import (
        CitationReconciliationItem,
        run_academic_integrity_audit,
    )
except ImportError:
    @dataclass
    class CitationReconciliationItem:
        author_year: str
        status: str
        location: str
        context: str = ""

    def run_academic_integrity_audit(
        text_doc: str,
        text_ref: str,
        exclude_bib: bool = False,
        exclude_quotes: bool = False,
        shingle_n: int = 3,
    ) -> Any:
        tokens_a = normalize_and_tokenize(text_doc)
        tokens_b = normalize_and_tokenize(text_ref)
        cos_sim = compute_cosine_similarity(text_doc, text_ref)
        set_a, set_b = set(tokens_a), set(tokens_b)
        jaccard = len(set_a & set_b) / max(1, len(set_a | set_b)) if (set_a or set_b) else 0.0
        
        class _Report:
            total_tokens_doc = len(tokens_a)
            total_tokens_ref = len(tokens_b)
            unique_tokens_doc = len(set_a)
            unique_tokens_ref = len(set_b)
            shared_tokens_count = len(set_a & set_b)
            cosine_similarity = cos_sim
            token_jaccard = jaccard
            top_shared_terms = []
            shingle_jaccard = 0.0
            citations_reconciliation = []
            excluded_sections = []
            direct_quotes_excluded_count = 0
        return _Report()

from engines.document_parser import parse_document


@dataclass
class SimilarityAuditResult:
    """Structured result of lexical similarity and academic document integrity analysis."""

    label_a: str
    label_b: str
    tokens_count_a: int
    tokens_count_b: int
    unique_tokens_a: int
    unique_tokens_b: int
    shared_tokens_count: int
    cosine_similarity: float  # [0.0, 1.0]
    jaccard_similarity: float  # [0.0, 1.0]
    top_shared_terms: list[tuple[str, int, int]]  # (term, count_a, count_b)
    shingle_jaccard: float = 0.0  # [0.0, 1.0]
    citations_reconciliation: list[CitationReconciliationItem] = field(default_factory=list)
    excluded_sections: list[str] = field(default_factory=list)
    quotes_excluded_count: int = 0
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    method: str = "Pure-Python Lexical Cosine + 3-Gram Shingling"
    disclaimer: str = (
        "Skor kemiripan leksikal semata-mata mengukur tumpang-tindih frekuensi kata/istilah "
        "antara dua dokumen. Skor ini BUKAN persentase plagiarisme, BUKAN bukti pelanggaran "
        "integritas akademik, dan BUKAN probabilitas naskah dibuat oleh AI. Naskah dalam "
        "disiplin ilmu yang sama secara alami memiliki kosakata teknis yang serupa."
    )

    @property
    def cosine_percentage(self) -> float:
        """Percentage format [0.0, 100.0]."""
        return round(self.cosine_similarity * 100.0, 2)

    @property
    def jaccard_percentage(self) -> float:
        """Percentage format [0.0, 100.0]."""
        return round(self.jaccard_similarity * 100.0, 2)

    @property
    def shingle_percentage(self) -> float:
        """Percentage format [0.0, 100.0]."""
        return round(self.shingle_jaccard * 100.0, 2)


def compute_jaccard_similarity(tokens_a: list[str], tokens_b: list[str]) -> float:
    """Computes Jaccard vocabulary similarity between two token sequences."""
    set_a = set(tokens_a)
    set_b = set(tokens_b)
    if not set_a or not set_b:
        return 0.0
    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    if union == 0:
        return 0.0
    return max(0.0, min(1.0, float(intersection) / float(union)))


def run_similarity_analysis(
    text_a: str,
    text_b: str,
    label_a: str = "Teks A",
    label_b: str = "Teks B",
    exclude_bib: bool = False,
    exclude_quotes: bool = False,
    shingle_n: int = 3,
) -> SimilarityAuditResult:
    """Executes pure-Python lexical and shingling comparison between two texts."""
    report = run_academic_integrity_audit(
        text_doc=text_a,
        text_ref=text_b,
        exclude_bib=exclude_bib,
        exclude_quotes=exclude_quotes,
        shingle_n=shingle_n,
    )

    return SimilarityAuditResult(
        label_a=label_a,
        label_b=label_b,
        tokens_count_a=report.total_tokens_doc,
        tokens_count_b=report.total_tokens_ref,
        unique_tokens_a=report.unique_tokens_doc,
        unique_tokens_b=report.unique_tokens_ref,
        shared_tokens_count=report.shared_tokens_count,
        cosine_similarity=report.cosine_similarity,
        jaccard_similarity=report.token_jaccard,
        top_shared_terms=report.top_shared_terms,
        shingle_jaccard=report.shingle_jaccard,
        citations_reconciliation=report.citations_reconciliation,
        excluded_sections=report.excluded_sections,
        quotes_excluded_count=report.direct_quotes_excluded_count,
    )



def extract_text_from_uploaded_bytes(file_bytes: bytes, filename: str) -> str:
    """Extracts text content from uploaded file bytes without permanent disk storage.

    Supports:
        - .docx: via engines.document_parser (python-docx)
        - .pdf: via engines.document_parser (pypdf/fitz)
        - .txt: via UTF-8 decoding (fallback to latin-1)
    """
    if not file_bytes:
        raise ValueError(f"Berkas '{filename}' kosong (0 byte).")

    suffix = Path(filename).suffix.lower()
    if suffix not in (".docx", ".pdf", ".txt"):
        raise ValueError(
            f"Format berkas '{suffix}' tidak didukung. Harap unggah berkas .docx, .pdf, atau .txt."
        )

    if suffix == ".txt":
        try:
            return file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            return file_bytes.decode("latin-1")

    # For docx and pdf, use engines.document_parser in a secure temporary directory
    import tempfile

    from utils.security import sanitize_filename

    with tempfile.TemporaryDirectory() as tmp_dir:
        safe_name = sanitize_filename(Path(filename).name)
        temp_file = Path(tmp_dir) / f"upload_{safe_name}"
        temp_file.write_bytes(file_bytes)
        try:
            parsed = parse_document(str(temp_file))
            extracted = parsed.get_text()
            if not extracted or not extracted.strip():
                raise ValueError(
                    f"Tidak ada teks terbaca dari berkas '{filename}'. "
                    "Pastikan berkas tidak kosong atau terkunci kata sandi."
                )
            return extracted
        except Exception as err:
            if isinstance(err, ValueError):
                raise
            raise ValueError(f"Gagal mengekstrak teks dari '{filename}': {err}") from err


def export_similarity_summary_txt(result: SimilarityAuditResult) -> str:
    """Generates a text summary export (metadata and scores only, no full text)."""
    lines = [
        "================================================================================",
        "LAPORAN RINGKASAN AUDIT KEMIRIPAN TEKS (SIMILARITY AUDIT REPORT)",
        "TesisCheck MIKOM 2026 — Pure-Python Lexical Similarity Engine",
        "================================================================================",
        f"Waktu Audit         : {result.timestamp}",
        f"Metode Komputasi    : {result.method}",
        f"Dokumen/Teks 1      : {result.label_a}",
        f"Dokumen/Teks 2      : {result.label_b}",
        "--------------------------------------------------------------------------------",
        "HASIL METRIK KEMIRIPAN LEKSIKAL:",
        f"  * Skor Cosine Similarity : {result.cosine_percentage}% (rentang 0.0% - 100.0%)",
        f"  * Indeks Shingle (3-Gram): {result.shingle_percentage}%",
        f"  * Indeks Jaccard (Vocab) : {result.jaccard_percentage}%",
        "",
        "STATISTIK TOKEN & KOSAKATA:",
        f"  * Total Kata/Token Dokumen 1 : {result.tokens_count_a} (Unik: {result.unique_tokens_a})",
        f"  * Total Kata/Token Dokumen 2 : {result.tokens_count_b} (Unik: {result.unique_tokens_b})",
        f"  * Kosakata Bersama (Shared) : {result.shared_tokens_count} kata",
    ]
    if result.excluded_sections:
        lines.append(f"  * Bagian Dikecualikan        : {', '.join(result.excluded_sections)}")
    if result.quotes_excluded_count > 0:
        lines.append(f"  * Kutipan Langsung Dihapus   : {result.quotes_excluded_count} kutipan")

    lines.extend([
        "",
        "ISTILAH TUMPANG-TINDIH UTAMA (TOP 20 SHARED TERMS):",
    ])
    for idx, (term, ca, cb) in enumerate(result.top_shared_terms[:20], start=1):
        lines.append(f"  {idx:2d}. {term:<24} | Dokumen 1: {ca:3d}x | Dokumen 2: {cb:3d}x")

    lines.extend([
        "",
        "--------------------------------------------------------------------------------",
        "CATATAN & PERINGATAN INTEGRITAS AKADEMIK:",
        result.disclaimer,
        "================================================================================",
    ])
    return "\n".join(lines)


def export_similarity_summary_csv(result: SimilarityAuditResult) -> str:
    """Generates a CSV summary export containing metadata and shared terms distribution."""
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(["Parameter", "Nilai"])
    writer.writerow(["Waktu Audit", result.timestamp])
    writer.writerow(["Metode", result.method])
    writer.writerow(["Dokumen A", result.label_a])
    writer.writerow(["Dokumen B", result.label_b])
    writer.writerow(["Cosine Similarity (%)", result.cosine_percentage])
    writer.writerow(["3-Gram Shingle Index (%)", result.shingle_percentage])
    writer.writerow(["Jaccard Index (%)", result.jaccard_percentage])
    writer.writerow(["Tokens Dokumen A", result.tokens_count_a])
    writer.writerow(["Tokens Dokumen B", result.tokens_count_b])
    writer.writerow(["Shared Vocabulary Count", result.shared_tokens_count])
    if result.excluded_sections:
        writer.writerow(["Bagian Dikecualikan", "; ".join(result.excluded_sections)])
    writer.writerow([])
    writer.writerow(["Istilah Bersama (Term)", "Frekuensi di Dokumen A", "Frekuensi di Dokumen B"])
    for term, ca, cb in result.top_shared_terms:
        writer.writerow([term, ca, cb])

    return output.getvalue()



def render_similarity_tab() -> None:
    """Streamlit UI Component for Similarity Checker."""
    import streamlit as st

    st.title("📑 Similarity Checker — Analisis Kemiripan Leksikal Naskah")
    st.markdown(
        "Modul audit kemiripan naskah berbasis **Pure-Python Lexical Cosine Similarity**. "
        "Membandingkan frekuensi kemunculan token kata secara mandiri tanpa bergantung pada library neural berat atau pengunduhan model eksternal."
    )

    # Academic Disclaimer Alert
    st.warning(
        "⚖️ **Pemberitahuan Integritas Akademik & Batasan Metodologis**:\n\n"
        "- Skor kemiripan yang ditampilkan merupakan **kemiripan leksikal** (persentase tumpang-tindih kosakata dan frekuensi token).\n"
        "- Skor ini **BUKAN bukti plagiarisme**, bukan persentase pencurian karya, dan bukan probabilitas buatan kecerdasan buatan (AI).\n"
        "- Naskah yang membahas topik atau teori komunikasi yang sama secara alami memiliki kemiripan istilah teknis."
    )

    st.markdown("#### ⚙️ Pengaturan Integrasi & Pengecualian Bagian")
    col_opt1, col_opt2 = st.columns(2)
    exclude_bib = col_opt1.checkbox(
        "📚 Kecualikan Daftar Pustaka dari kalkulasi",
        value=True,
        help="Mencegah tumpang-tindih rujukan ilmiah menggelembungkan skor kemiripan substantif naskah.",
    )
    exclude_quotes = col_opt2.checkbox(
        "💬 Kecualikan Kutipan Langsung (\"...\") dari kalkulasi",
        value=False,
        help="Mengabaikan teks di dalam tanda petik untuk fokus pada orisinalitas argumen mandiri.",
    )

    mode = st.radio(
        "Pilih Mode Analisis:",
        ["✍️ Perbandingan Dua Teks Langsung", "📁 Unggah Dua Dokumen (.docx / .pdf / .txt)"],
        horizontal=True,
    )

    text_a = ""
    text_b = ""
    label_a = "Naskah A"
    label_b = "Naskah B"
    is_ready = False

    if mode == "✍️ Perbandingan Dua Teks Langsung":
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Naskah / Paragraf Pertama")
            text_a = st.text_area(
                "Masukkan teks pertama:",
                height=220,
                placeholder="Contoh: Penelitian ini bertujuan untuk menguji efektivitas komunikasi publik...",
                key="sim_text_a",
            )
            label_a = "Teks Input 1"

        with col2:
            st.subheader("Naskah / Paragraf Kedua")
            text_b = st.text_area(
                "Masukkan teks pembanding:",
                height=220,
                placeholder="Contoh: Studi ini meneliti efektivitas komunikasi publik pada instansi pemerintah...",
                key="sim_text_b",
            )
            label_b = "Teks Input 2"

        if st.button("🔍 Hitung Kemiripan Teks", type="primary", use_container_width=True):
            if not text_a.strip() or not text_b.strip():
                st.error("❌ Mohon isi kedua kolom teks sebelum menjalankan analisis kemiripan.")
            else:
                is_ready = True

    else:
        st.subheader("Unggah Dokumen Pembanding")
        col_up1, col_up2 = st.columns(2)
        with col_up1:
            file_a = st.file_uploader(
                "Dokumen Pertama (Tesis / Bab Naskah):",
                type=["docx", "pdf", "txt"],
                key="sim_file_a",
                help="Mendukung format Microsoft Word (.docx), PDF (.pdf), atau Plain Text (.txt).",
            )
        with col_up2:
            file_b = st.file_uploader(
                "Dokumen Kedua (Pembanding / Jurnal / Draf Lain):",
                type=["docx", "pdf", "txt"],
                key="sim_file_b",
                help="Mendukung format Microsoft Word (.docx), PDF (.pdf), atau Plain Text (.txt).",
            )

        if st.button("📁 Proses & Analisis Dokumen", type="primary", use_container_width=True):
            if not file_a or not file_b:
                st.error("❌ Harap unggah kedua berkas dokumen untuk dibandingkan.")
            else:
                with st.spinner("⏳ Membaca dan mengekstrak teks dokumen..."):
                    try:
                        text_a = extract_text_from_uploaded_bytes(file_a.getvalue(), file_a.name)
                        label_a = file_a.name
                    except Exception as err:
                        st.error(f"Gagal memproses Dokumen 1 ({file_a.name}): {err}")
                        return

                    try:
                        text_b = extract_text_from_uploaded_bytes(file_b.getvalue(), file_b.name)
                        label_b = file_b.name
                    except Exception as err:
                        st.error(f"Gagal memproses Dokumen 2 ({file_b.name}): {err}")
                        return

                is_ready = True

    if is_ready:
        with st.spinner("⚡ Menghitung kemiripan leksikal, shingling, dan rekonsiliasi sitasi..."):
            result = run_similarity_analysis(
                text_a,
                text_b,
                label_a=label_a,
                label_b=label_b,
                exclude_bib=exclude_bib,
                exclude_quotes=exclude_quotes,
            )

        st.markdown("---")
        st.subheader("📊 Hasil Evaluasi Kemiripan & Integritas Dokumen")

        if result.excluded_sections:
            st.info(f"ℹ️ **Pengecualian Bagian Aktif:** Bagian rujukan berikut dikeluarkan dari komputasi leksikal: `{', '.join(result.excluded_sections)}`.")
        if result.quotes_excluded_count > 0:
            st.caption(f"ℹ️ Sebanyak {result.quotes_excluded_count} kutipan langsung diabaikan dari perhitungan leksikal.")

        # Metric Cards (5 columns)
        col_m1, col_m2, col_m3, col_m4, col_m5 = st.columns(5)
        with col_m1:
            st.metric(
                label="Cosine Similarity",
                value=f"{result.cosine_percentage}%",
                help="Cosine similarity mengukur sudut kesamaan frekuensi kata (Term Frequency) dalam ruang vektor.",
            )
        with col_m2:
            st.metric(
                label="3-Gram Shingling",
                value=f"{result.shingle_percentage}%",
                help="Mengukur urutan 3 kata berturut-turut untuk mendeteksi verbatim / susunan kalimat serupa.",
            )
        with col_m3:
            st.metric(
                label="Jaccard Index",
                value=f"{result.jaccard_percentage}%",
                help="Rasio kosakata unik bersama terhadap gabungan seluruh kosakata unik.",
            )
        with col_m4:
            st.metric(
                label="Kosakata Bersama",
                value=f"{result.shared_tokens_count} kata",
                help="Jumlah istilah/kata yang muncul pada kedua dokumen sekaligus.",
            )
        with col_m5:
            st.metric(
                label="Total Kata (A | B)",
                value=f"{result.tokens_count_a} | {result.tokens_count_b}",
                help="Jumlah kata/token yang berhasil diekstrak dan dianalisis dari masing-masing dokumen.",
            )

        # Visual progress bar
        st.progress(
            min(1.0, max(0.0, result.cosine_similarity)),
            text=f"Indikator Kesamaan Leksikal: {result.cosine_percentage}%",
        )

        # Tabbed details
        tab_terms, tab_citations, tab_formula, tab_export = st.tabs([
            "🔤 Istilah Tumpang-Tindih (Shared Terms)",
            "📚 Rekonsiliasi Sitasi & Rujukan",
            "📐 Metodologi & Rumus",
            "💾 Ekspor Laporan Ringkasan",
        ])

        with tab_terms:
            st.markdown("**Top 30 Kata Bersama dengan Frekuensi Tertinggi:**")
            if result.top_shared_terms:
                table_data = [
                    {
                        "No": idx + 1,
                        "Kata / Istilah": term,
                        f"Frekuensi di '{result.label_a}'": ca,
                        f"Frekuensi di '{result.label_b}'": cb,
                        "Total Muncul": ca + cb,
                    }
                    for idx, (term, ca, cb) in enumerate(result.top_shared_terms)
                ]
                st.dataframe(table_data, use_container_width=True)
            else:
                st.info("Tidak ditemukan kata atau istilah yang tumpang tindih antara kedua dokumen.")

        with tab_citations:
            st.markdown("### 📚 Rekonsiliasi Sitasi Teks & Daftar Pustaka (APA 7th)")
            st.caption("Pemeriksaan timbal-balik (reciprocal consistency) antara sitasi dalam naskah dengan entri pada Daftar Pustaka.")

            matched = [c for c in result.citations_reconciliation if c.status == "MATCHED"]
            orphaned = [c for c in result.citations_reconciliation if c.status == "MISSING_IN_BIB"]
            unused = [c for c in result.citations_reconciliation if c.status == "UNUSED_BIB"]

            c_r1, c_r2, c_r3 = st.columns(3)
            with c_r1:
                st.metric("Sitasi Terverifikasi (Matched)", f"{len(matched)} item")
            with c_r2:
                st.metric("Sitasi Tanpa Rujukan (Orphan)", f"{len(orphaned)} item")
            with c_r3:
                st.metric("Rujukan Tidak Disitasi (Unused)", f"{len(unused)} item")

            if result.citations_reconciliation:
                cit_rows = [
                    {
                        "Penulis & Tahun": item.author_year,
                        "Status Integritas": "✓ MATCHED" if item.status == "MATCHED" else ("❌ MISSING_IN_BIB" if item.status == "MISSING_IN_BIB" else "⚠️ UNUSED_BIB"),
                        "Posisi Temuan": item.location,
                        "Konteks / Rujukan": item.context,
                    }
                    for item in result.citations_reconciliation
                ]
                st.dataframe(cit_rows, use_container_width=True)
            else:
                st.info("Tidak terdeteksi sitasi formal APA 7 pada teks pertama.")

        with tab_formula:
            st.markdown("""
            ### Rumus Cosine Similarity & N-Gram Word Shingling
            Diberikan dua dokumen $A$ dan $B$, representasi vektor kata dihitung berdasarkan frekuensi kemunculan:
            $$S_{\\text{cos}}(A, B) = \\frac{\\mathbf{v}_A \\cdot \\mathbf{v}_B}{\\|\\mathbf{v}_A\\|_2 \\|\\mathbf{v}_B\\|_2} = \\frac{\\sum_{t \\in A \\cap B} \\text{tf}(t, A) \\cdot \\text{tf}(t, B)}{\\sqrt{\\sum_{t} \\text{tf}(t, A)^2} \\cdot \\sqrt{\\sum_{t} \\text{tf}(t, B)^2}}$$

            - **N-Gram Shingling (3-Gram):** Menghitung rasio irisan 3-kata berturut-turut untuk mengevaluasi kesamaan urutan frasa verbatim.
            - **Pengecualian Cerdas:** Bagian *Daftar Pustaka* dapat dikecualikan agar kutipan literatur standar tidak menyebabkan *false positive* kemiripan.
            - **Normalisasi:** Token dinormalisasi ke bentuk Unicode NFKC, diubah ke huruf kecil (*lowercase*), dan tanda baca diabaikan.
            - **Privasi:** Proses analisis 100% lokal di memori Python, tidak ada data naskah yang dikirim ke internet.
            """)

        with tab_export:
            st.markdown("Unduh ringkasan hasil audit untuk dokumentasi naskah (tanpa membocorkan isi lengkap teks):")
            txt_report = export_similarity_summary_txt(result)
            csv_report = export_similarity_summary_csv(result)

            col_exp1, col_exp2 = st.columns(2)
            with col_exp1:
                st.download_button(
                    label="📄 Unduh Ringkasan Audit (.txt)",
                    data=txt_report,
                    file_name=f"similarity_audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain",
                    use_container_width=True,
                )
            with col_exp2:
                st.download_button(
                    label="📊 Unduh Data Istilah (.csv)",
                    data=csv_report,
                    file_name=f"similarity_terms_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True,
                )
