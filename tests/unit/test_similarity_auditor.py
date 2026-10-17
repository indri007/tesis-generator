"""Unit and integration tests for Academic Similarity Auditor Engine."""

from __future__ import annotations

import pytest

from engines.similarity_auditor import (
    compute_jaccard_similarity,
    export_similarity_summary_csv,
    export_similarity_summary_txt,
    extract_text_from_uploaded_bytes,
    run_similarity_analysis,
)


class TestSimilarityAuditorEngine:
    """Test suite for similarity auditor business logic and file processing."""

    def test_identical_texts_analysis(self):
        """Identical texts should have 100% cosine similarity and 100% Jaccard index."""
        text = "Metodologi penelitian kualitatif komunikasi publik di era transformasi digital."
        res = run_similarity_analysis(text, text, label_a="Naskah 1", label_b="Naskah 2")

        assert res.cosine_percentage == pytest.approx(100.0, rel=1e-3)
        assert res.jaccard_percentage == pytest.approx(100.0, rel=1e-3)
        assert res.tokens_count_a == res.tokens_count_b
        assert res.shared_tokens_count > 0
        assert len(res.top_shared_terms) > 0

    def test_completely_different_texts_analysis(self):
        """Disjoint texts should have 0% similarity."""
        text_a = "kucing anjing burung kelinci"
        text_b = "komputer server database memori"
        res = run_similarity_analysis(text_a, text_b, label_a="Fauna", label_b="Teknologi")

        assert res.cosine_percentage == 0.0
        assert res.jaccard_percentage == 0.0
        assert res.shared_tokens_count == 0
        assert len(res.top_shared_terms) == 0

    def test_empty_and_whitespace_texts(self):
        """Empty texts return 0% without zero division error."""
        res_empty = run_similarity_analysis("", "   \t\n  ")
        assert res_empty.cosine_percentage == 0.0
        assert res_empty.jaccard_percentage == 0.0
        assert res_empty.shared_tokens_count == 0

    def test_extract_text_txt_success(self):
        """Plain text extraction from UTF-8 bytes."""
        sample_bytes = "Analisis isi kuantitatif portal berita media siber.".encode("utf-8")
        text = extract_text_from_uploaded_bytes(sample_bytes, "manuscript.txt")
        assert "Analisis isi kuantitatif" in text

    def test_extract_text_empty_file_validation(self):
        """Empty file bytes must raise ValueError."""
        with pytest.raises(ValueError, match="kosong"):
            extract_text_from_uploaded_bytes(b"", "empty_doc.docx")

    def test_extract_text_unsupported_format(self):
        """Unsupported file extensions must raise ValueError with clear message."""
        with pytest.raises(ValueError, match="tidak didukung"):
            extract_text_from_uploaded_bytes(b"dummy data", "archive.zip")

        with pytest.raises(ValueError, match="tidak didukung"):
            extract_text_from_uploaded_bytes(b"dummy data", "image.png")

    def test_extract_text_corrupted_file(self):
        """Corrupted file bytes must raise ValueError safely without internal traceback crash."""
        corrupted_bytes = b"This is not a real PDF or DOCX file content binary data"
        with pytest.raises(ValueError, match="Gagal mengekstrak teks"):
            extract_text_from_uploaded_bytes(corrupted_bytes, "corrupt.pdf")

    def test_jaccard_similarity_edge_cases(self):
        """Jaccard similarity boundary behavior."""
        assert compute_jaccard_similarity([], []) == 0.0
        assert compute_jaccard_similarity(["a", "b"], []) == 0.0
        assert compute_jaccard_similarity(["a", "b"], ["a", "b"]) == 1.0
        assert compute_jaccard_similarity(["a"], ["b"]) == 0.0

    def test_export_txt_contains_metadata_and_disclaimer(self):
        """TXT export contains metrics, shared terms, and academic disclaimer, but no full text."""
        text_a = "Sistem komunikasi publik dan media siber."
        text_b = "Sistem regulasi komunikasi publik dan penyiaran."
        res = run_similarity_analysis(text_a, text_b, "Naskah A", "Naskah B")

        txt = export_similarity_summary_txt(res)
        assert "LAPORAN RINGKASAN AUDIT KEMIRIPAN TEKS" in txt
        assert "Skor Cosine Similarity" in txt
        assert "CATATAN & PERINGATAN INTEGRITAS AKADEMIK" in txt
        assert "BUKAN persentase plagiarisme" in txt
        assert "komunikasi" in txt

    def test_export_csv_contains_tabular_shared_terms(self):
        """CSV export contains valid CSV rows with shared terms counts."""
        text_a = "teori agenda setting dalam jurnalisme investigasi."
        text_b = "penerapan agenda setting pada jurnalisme data."
        res = run_similarity_analysis(text_a, text_b, "Doc1", "Doc2")

        csv_content = export_similarity_summary_csv(res)
        assert "Cosine Similarity (%)" in csv_content
        assert "agenda" in csv_content
        assert "setting" in csv_content

    def test_no_plagiarism_claim_in_result(self):
        """Audit result disclaimer must explicitly disclaim plagiarism proof."""
        res = run_similarity_analysis("teks a", "teks b")
        assert "BUKAN persentase plagiarisme" in res.disclaimer
        assert "BUKAN bukti pelanggaran" in res.disclaimer

    def test_isolation_no_cross_session_leakage(self):
        """Subsequent analysis runs must not retain or leak previous document tokens."""
        res1 = run_similarity_analysis("rahasia proyek alfa", "rahasia proyek alfa")
        assert "alfa" in [t[0] for t in res1.top_shared_terms]

        res2 = run_similarity_analysis("studi komunikasi massa", "studi komunikasi publik")
        shared_res2 = [t[0] for t in res2.top_shared_terms]
        assert "alfa" not in shared_res2
        assert "komunikasi" in shared_res2
