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

from core.clones.similarity_plagiarism import (
    compute_cosine_similarity,
    normalize_and_tokenize,
)
from engines.document_parser import parse_document


@dataclass
class SimilarityAuditResult:
    """Structured result of lexical similarity analysis."""

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
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    method: str = "Pure-Python Lexical Cosine (TF-IDF / Sublinear)"
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
) -> SimilarityAuditResult:
    """Executes pure-Python lexical comparison between two texts."""
    from collections import Counter

    tokens_a = normalize_and_tokenize(text_a)
    tokens_b = normalize_and_tokenize(text_b)

    cosine_score = compute_cosine_similarity(text_a, text_b)
    jaccard_score = compute_jaccard_similarity(tokens_a, tokens_b)

    counts_a = Counter(tokens_a)
    counts_b = Counter(tokens_b)

    shared_vocab = set(counts_a.keys()) & set(counts_b.keys())
    # Sort shared terms by combined frequency descending
    ranked_shared = sorted(
        [(term, counts_a[term], counts_b[term]) for term in shared_vocab],
        key=lambda item: (item[1] + item[2]),
        reverse=True,
    )

    return SimilarityAuditResult(
        label_a=label_a,
        label_b=label_b,
        tokens_count_a=len(tokens_a),
        tokens_count_b=len(tokens_b),
        unique_tokens_a=len(counts_a),
        unique_tokens_b=len(counts_b),
        shared_tokens_count=len(shared_vocab),
        cosine_similarity=cosine_score,
        jaccard_similarity=jaccard_score,
        top_shared_terms=ranked_shared[:30],
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

    with tempfile.TemporaryDirectory() as tmp_dir:
        temp_file = Path(tmp_dir) / f"upload_{Path(filename).name}"
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
        f"  * Indeks Jaccard (Vocab) : {result.jaccard_percentage}%",
        "",
        "STATISTIK TOKEN & KOSAKATA:",
        f"  * Total Kata/Token Dokumen 1 : {result.tokens_count_a} (Unik: {result.unique_tokens_a})",
        f"  * Total Kata/Token Dokumen 2 : {result.tokens_count_b} (Unik: {result.unique_tokens_b})",
        f"  * Kosakata Bersama (Shared) : {result.shared_tokens_count} kata",
        "",
        "ISTILAH TUMPANG-TINDIH UTAMA (TOP 20 SHARED TERMS):",
    ]
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
    writer.writerow(["Jaccard Index (%)", result.jaccard_percentage])
    writer.writerow(["Tokens Dokumen A", result.tokens_count_a])
    writer.writerow(["Tokens Dokumen B", result.tokens_count_b])
    writer.writerow(["Shared Vocabulary Count", result.shared_tokens_count])
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
        with st.spinner("⚡ Menghitung kemiripan leksikal dan frekuensi istilah..."):
            result = run_similarity_analysis(text_a, text_b, label_a=label_a, label_b=label_b)

        st.markdown("---")
        st.subheader("📊 Hasil Evaluasi Kemiripan Leksikal")

        # Metric Cards
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        with col_m1:
            st.metric(
                label="Cosine Similarity",
                value=f"{result.cosine_percentage}%",
                help="Cosine similarity mengukur sudut kesamaan frekuensi kata (Term Frequency) dalam ruang vektor.",
            )
        with col_m2:
            st.metric(
                label="Jaccard Index",
                value=f"{result.jaccard_percentage}%",
                help="Rasio kosakata unik bersama terhadap gabungan seluruh kosakata unik.",
            )
        with col_m3:
            st.metric(
                label="Kosakata Bersama",
                value=f"{result.shared_tokens_count} kata",
                help="Jumlah istilah/kata yang muncul pada kedua dokumen sekaligus.",
            )
        with col_m4:
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
        tab_terms, tab_formula, tab_export = st.tabs([
            "🔤 Istilah Tumpang-Tindih (Shared Terms)",
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

        with tab_formula:
            st.markdown("""
            ### Rumus Cosine Similarity Berbasis Frekuensi Istilah (Term Frequency)
            Diberikan dua dokumen $A$ dan $B$, representasi vektor kata dihitung berdasarkan frekuensi kemunculan:
            $$S_{\\text{cos}}(A, B) = \\frac{\\mathbf{v}_A \\cdot \\mathbf{v}_B}{\\|\\mathbf{v}_A\\|_2 \\|\\mathbf{v}_B\\|_2} = \\frac{\\sum_{t \\in A \\cap B} \\text{tf}(t, A) \\cdot \\text{tf}(t, B)}{\\sqrt{\\sum_{t} \\text{tf}(t, A)^2} \\cdot \\sqrt{\\sum_{t} \\text{tf}(t, B)^2}}$$

            - **Normalisasi:** Token dinormalisasi ke bentuk Unicode NFKC, diubah ke huruf kecil (*lowercase*), dan tanda baca diabaikan.
            - **Proteksi Nol:** Jika salah satu atau kedua teks kosong, sistem secara aman mengembalikan skor `0.0%` tanpa error pembagian dengan nol.
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
