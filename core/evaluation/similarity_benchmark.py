"""Academic Similarity Benchmark Evaluation Framework & Golden Dataset.

Provides reproducible evaluation of lexical similarity and shingling engines:
- Standardized, labeled academic thesis test pairs (Identical, Reordered, Paraphrase,
  Boilerplate, Indonesian Synonyms, Partial Overlap, Disjoint, Empty).
- Multi-threshold sensitivity evaluation (Precision, Recall, F1, Accuracy).
- Metric breakdown highlighting the scientific boundaries of purely lexical detection.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from core.evaluation.document_integrity_engine import (
    compute_cosine_similarity,
    compute_shingle_jaccard,
    normalize_and_tokenize,
)


@dataclass
class BenchmarkPair:
    """A labeled pair of academic text excerpts for evaluation."""

    pair_id: str
    text_a: str
    text_b: str
    expected_similar: bool  # True if pair represents substantive similarity/overlap
    category: str
    description: str


@dataclass
class ThresholdMetric:
    """Classification performance metrics for a specific similarity threshold."""

    threshold: float
    tp: int
    fp: int
    tn: int
    fn: int
    precision: float | None
    recall: float | None
    f1: float | None
    accuracy: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "threshold": self.threshold,
            "tp": self.tp,
            "fp": self.fp,
            "tn": self.tn,
            "fn": self.fn,
            "precision": self.precision,
            "recall": self.recall,
            "f1": self.f1,
            "accuracy": self.accuracy,
        }


GOLDEN_SIMILARITY_DATASET: list[BenchmarkPair] = [
    BenchmarkPair(
        pair_id="PAIR-001-IDENTICAL",
        category="IDENTICAL",
        expected_similar=True,
        description="Identik kata-per-kata dari cuplikan bab metodologi penelitian komunikasi.",
        text_a=(
            "Penelitian ini menggunakan pendekatan kuantitatif dengan metode survei eksplanatif. "
            "Populasi penelitian mencakup seluruh mahasiswa program magister ilmu komunikasi yang aktif. "
            "Teknik pengambilan sampel dilakukan dengan metode stratified random sampling dengan toleransi kesalahan 5%."
        ),
        text_b=(
            "Penelitian ini menggunakan pendekatan kuantitatif dengan metode survei eksplanatif. "
            "Populasi penelitian mencakup seluruh mahasiswa program magister ilmu komunikasi yang aktif. "
            "Teknik pengambilan sampel dilakukan dengan metode stratified random sampling dengan toleransi kesalahan 5%."
        ),
    ),
    BenchmarkPair(
        pair_id="PAIR-002-REORDERED",
        category="REORDERED",
        expected_similar=True,
        description="Paragraf dan struktur kalimat diacak ulang tanpa mengubah kosakata substansial.",
        text_a=(
            "Media sosial telah mengubah pola konsumsi informasi publik secara radikal. "
            "Algoritma kurasi konten cenderung memperkuat ruang gema dan polarisasi pandangan masyarakat. "
            "Fenomena ini menimbulkan tantangan serius bagi demokrasi deliberatif kontemporer."
        ),
        text_b=(
            "Fenomena ini menimbulkan tantangan serius bagi demokrasi deliberatif kontemporer. "
            "Pola konsumsi informasi publik telah diubah secara radikal oleh media sosial. "
            "Ruang gema dan polarisasi pandangan masyarakat cenderung diperkuat oleh algoritma kurasi konten."
        ),
    ),
    BenchmarkPair(
        pair_id="PAIR-003-LIGHT-PARAPHRASE",
        category="LIGHT_PARAPHRASE",
        expected_similar=True,
        description="Parafrase ringan dengan penggantian partikel atau sinonim minor.",
        text_a=(
            "Hasil analisis regresi linear berganda menunjukkan bahwa variabel kredibilitas komunikator "
            "memiliki pengaruh positif dan signifikan terhadap tingkat kepatuhan audiens dalam program sosialisasi kebijakan."
        ),
        text_b=(
            "Hasil uji analisis regresi linear berganda memperlihatkan bahwa variabel kredibilitas dari komunikator "
            "memberikan pengaruh yang positif serta signifikan pada tingkat kepatuhan audiens di dalam sosialisasi kebijakan."
        ),
    ),
    BenchmarkPair(
        pair_id="PAIR-004-BOILERPLATE",
        category="BOILERPLATE",
        expected_similar=False,
        description="Format standar formalitas akademik (ucapan terima kasih / pembuka tesis).",
        text_a=(
            "Puji dan syukur penulis panjatkan ke hadirat Tuhan Yang Maha Esa atas limpahan rahmat, taufik, "
            "dan hidayah-Nya sehingga penulis dapat menyelesaikan naskah tesis ini dengan lancar dan tepat waktu."
        ),
        text_b=(
            "Segala puji dan syukur kami panjatkan ke hadirat Tuhan Yang Maha Esa karena atas berkat dan rahmat-Nya "
            "penyusunan laporan tugas akhir ini dapat diselesaikan dengan baik sesuai target waktu yang ditentukan."
        ),
    ),
    BenchmarkPair(
        pair_id="PAIR-005-SYNONYMS",
        category="SYNONYMS",
        expected_similar=False,
        description="Ekuivalensi semantik konseptual menggunakan leksikon berbeda (batasan evaluasi TF-IDF).",
        text_a=(
            "Pemberitaan media daring memicu perdebatan sengit di kalangan warganet mengenai kebijakan subsidi BBM."
        ),
        text_b=(
            "Liputan pers siber menimbulkan silang pendapat tajam di antara pengguna internet terkait bantuan tunai energi."
        ),
    ),
    BenchmarkPair(
        pair_id="PAIR-006-PARTIAL-OVERLAP",
        category="PARTIAL_OVERLAP",
        expected_similar=True,
        description="Naskah memiliki satu paragraf identik di antara bagian yang berbeda.",
        text_a=(
            "Latar belakang riset ini berfokus pada dinamika komunikasi antarpribadi di era hibrida. "
            "Dalam kerangka teori pertukaran sosial, individu mengevaluasi hubungan interpersonal melalui kalkulasi biaya dan ganjaran. "
            "Oleh karena itu, kepuasan relasional ditentukan oleh ekspektasi timbal balik para pihak."
        ),
        text_b=(
            "Studi ini menyelidiki kepemimpinan transformasional di korporasi perbankan syariah. "
            "Dalam kerangka teori pertukaran sosial, individu mengevaluasi hubungan interpersonal melalui kalkulasi biaya dan ganjaran. "
            "Budaya organisasi menjadi variabel intervening yang memoderasi efektivitas kinerja karyawan."
        ),
    ),
    BenchmarkPair(
        pair_id="PAIR-007-DISJOINT",
        category="DISJOINT",
        expected_similar=False,
        description="Topik yang sepenuhnya berbeda: komunikasi politik vs algoritma jaringan komputer.",
        text_a=(
            "Partisipasi politik warga negara dalam pemilihan umum dipengaruhi oleh diskursus opini publik di televisi swasta."
        ),
        text_b=(
            "Protokol routing Open Shortest Path First menggunakan algoritma Dijkstra untuk menentukan jalur paket data optimal."
        ),
    ),
    BenchmarkPair(
        pair_id="PAIR-008-EMPTY",
        category="EMPTY",
        expected_similar=False,
        description="Input teks kosong atau spasi kosong.",
        text_a="",
        text_b="",
    ),
    BenchmarkPair(
        pair_id="PAIR-009-DISJOINT-ACADEMIC",
        category="DISJOINT",
        expected_similar=False,
        description="Dua topik akademik berbeda: analisis wacana kritis vs perancangan database relasional.",
        text_a=(
            "Analisis wacana kritis model Fairclough membedah teks melalui dimensi tekstual, praksis diskursif, dan praksis sosial."
        ),
        text_b=(
            "Normalisasi basis data tingkat ketiga (3NF) mensyaratkan setiap atribut non-kunci bergantung secara fungsional penuh pada primary key."
        ),
    ),
    BenchmarkPair(
        pair_id="PAIR-010-TYPOS",
        category="LIGHT_PARAPHRASE",
        expected_similar=True,
        description="Teks serupa dengan variasi ejaan atau salah tik tipografis.",
        text_a=(
            "Konsep efikasi diri menurut Bandura mencerminkan keyakinan individu terhadap kapasitas mereka dalam mencapai tujuan."
        ),
        text_b=(
            "Konsep efikasi-diri menurut Bandura mencerminkan keyakinan individu terhadap kapasitasnya didalam menggapai tujuan."
        ),
    ),
]


def evaluate_similarity_thresholds(
    pairs: list[BenchmarkPair] | None = None,
    thresholds: list[float] | None = None,
    metric_type: str = "cosine",
) -> list[ThresholdMetric]:
    """Evaluates classification accuracy of similarity metric across multiple thresholds."""
    if pairs is None:
        pairs = GOLDEN_SIMILARITY_DATASET
    if thresholds is None:
        thresholds = [0.40, 0.50, 0.60, 0.70, 0.80, 0.85]

    results: list[ThresholdMetric] = []

    for thr in thresholds:
        tp = fp = tn = fn = 0

        for pair in pairs:
            if metric_type == "cosine":
                score = compute_cosine_similarity(pair.text_a, pair.text_b)
            elif metric_type == "shingle":
                tok_a = normalize_and_tokenize(pair.text_a)
                tok_b = normalize_and_tokenize(pair.text_b)
                score = compute_shingle_jaccard(tok_a, tok_b, n=3)
            else:
                score = compute_cosine_similarity(pair.text_a, pair.text_b)

            predicted_similar = score >= thr

            if predicted_similar and pair.expected_similar:
                tp += 1
            elif predicted_similar and not pair.expected_similar:
                fp += 1
            elif not predicted_similar and not pair.expected_similar:
                tn += 1
            else:
                fn += 1

        total = tp + fp + tn + fn
        precision = round(tp / (tp + fp), 4) if (tp + fp) > 0 else None
        recall = round(tp / (tp + fn), 4) if (tp + fn) > 0 else None
        accuracy = round((tp + tn) / total, 4) if total > 0 else 0.0

        if precision is not None and recall is not None and (precision + recall) > 0:
            f1 = round(2 * (precision * recall) / (precision + recall), 4)
        else:
            f1 = None

        results.append(
            ThresholdMetric(
                threshold=thr,
                tp=tp,
                fp=fp,
                tn=tn,
                fn=fn,
                precision=precision,
                recall=recall,
                f1=f1,
                accuracy=accuracy,
            )
        )

    return results


def format_benchmark_summary(metrics: list[ThresholdMetric]) -> str:
    """Formats benchmark results as a GitHub Markdown table."""
    lines = [
        "| Threshold | TP | FP | TN | FN | Precision | Recall | F1-Score | Accuracy |",
        "|:---------:|:--:|:--:|:--:|:--:|:---------:|:------:|:--------:|:--------:|",
    ]
    for m in metrics:
        p_str = f"{m.precision * 100:.1f}%" if m.precision is not None else "N/A"
        r_str = f"{m.recall * 100:.1f}%" if m.recall is not None else "N/A"
        f1_str = f"{m.f1 * 100:.1f}%" if m.f1 is not None else "N/A"
        acc_str = f"{m.accuracy * 100:.1f}%"
        lines.append(
            f"| {m.threshold:.2f} | {m.tp:2d} | {m.fp:2d} | {m.tn:2d} | {m.fn:2d} | "
            f"{p_str} | {r_str} | {f1_str} | {acc_str} |"
        )
    return "\n".join(lines)
