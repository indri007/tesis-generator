"""Reproducible Benchmark Runner and Academic Quality Evaluation Reporter.

Executes deterministic evaluation across annotated thesis datasets, computes comprehensive
metrics, performs taxonomy error analysis, and exports structured JSON and Markdown reports.
"""

from __future__ import annotations

import datetime
import json
from pathlib import Path
from typing import Any

from core.evaluation.error_analysis import CategorizedError, ErrorAnalyzer
from core.evaluation.matcher import FindingMatcher, MatchResult
from core.evaluation.metrics import (
    BenchmarkEvaluationSummary,
    compute_category_metrics,
    compute_cohens_kappa,
    compute_micro_macro_metrics,
)
from core.evaluation.schema import BenchmarkAnnotation, EvaluatorConfig


class AcademicBenchmarkRunner:
    """Executes evaluation benchmarks and generates quality audit reports."""

    def __init__(
        self,
        config: EvaluatorConfig | None = None,
        output_dir: str | Path = "output/reports/benchmark",
    ):
        self.config = config or EvaluatorConfig()
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def evaluate_dataset(
        self,
        dataset_items: list[dict[str, Any]],
        strict_location: bool = False,
        strict_severity: bool = True,
    ) -> tuple[BenchmarkEvaluationSummary, list[CategorizedError], dict[str, Any]]:
        """Evaluates a collection of annotated test items.
        
        Each item in dataset_items should have:
        - "document_id": str (anonymous)
        - "reference_annotations": list[dict or BenchmarkAnnotation]
        - "detected_findings": list[dict]
        - optional "reviewer_1_labels": list[str]
        - optional "reviewer_2_labels": list[str]
        """
        all_matches: list[MatchResult] = []
        all_errors: list[CategorizedError] = []

        total_ref_count = 0
        total_det_count = 0

        r1_all_labels: list[str] = []
        r2_all_labels: list[str] = []

        for item in dataset_items:
            doc_id = item.get("document_id", "DOC-ANON")
            raw_refs = item.get("reference_annotations", [])
            raw_dets = item.get("detected_findings", [])

            # Parse references into BenchmarkAnnotation objects
            refs: list[BenchmarkAnnotation] = []
            for r in raw_refs:
                if isinstance(r, BenchmarkAnnotation):
                    refs.append(r)
                elif isinstance(r, dict):
                    refs.append(BenchmarkAnnotation.from_dict(r))

            total_ref_count += len(refs)
            total_det_count += len(raw_dets)

            matcher = FindingMatcher(
                reference_annotations=refs,
                detected_findings=raw_dets,
                strict_location=strict_location,
                strict_severity=strict_severity,
            )
            matches = matcher.match()
            all_matches.extend(matches)

            # Error analysis
            analyzer = ErrorAnalyzer(matches, document_id=doc_id)
            all_errors.extend(analyzer.analyze())

            # Reviewer agreement data if present
            if "reviewer_1_labels" in item and "reviewer_2_labels" in item:
                r1_all_labels.extend(item["reviewer_1_labels"])
                r2_all_labels.extend(item["reviewer_2_labels"])

        # Compute category-wise and micro/macro metrics
        cat_metrics = compute_category_metrics(all_matches)
        micro_metrics, macro_metrics = compute_micro_macro_metrics(cat_metrics)

        summary = BenchmarkEvaluationSummary(
            total_documents=len(dataset_items),
            total_reference_findings=total_ref_count,
            total_detected_findings=total_det_count,
            per_category=cat_metrics,
            micro_metrics=micro_metrics,
            macro_metrics=macro_metrics,
        )

        # Compute inter-annotator agreement if reviewer labels were collected
        agreement = compute_cohens_kappa(r1_all_labels, r2_all_labels)

        return summary, all_errors, agreement

    def generate_reports(
        self,
        summary: BenchmarkEvaluationSummary,
        errors: list[CategorizedError],
        agreement: dict[str, Any],
        report_prefix: str = "thesis_audit_benchmark",
    ) -> tuple[Path, Path]:
        """Exports both JSON and Markdown benchmark evaluation reports."""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        error_summary = ErrorAnalyzer.summarize_errors(errors)

        # Quality Gate Assessment
        micro_f1 = summary.micro_metrics.get("f1_score")
        micro_p = summary.micro_metrics.get("precision")
        micro_r = summary.micro_metrics.get("recall")

        gate_passed = (
            micro_f1 is not None and micro_f1 >= 85.0
            and micro_p is not None and micro_p >= 85.0
            and micro_r is not None and micro_r >= 85.0
        )

        quality_gate = {
            "status": "PASSED" if gate_passed else "FAILED",
            "threshold_target": ">= 85.0%",
            "micro_f1": f"{micro_f1}%" if micro_f1 is not None else "N/A",
            "micro_precision": f"{micro_p}%" if micro_p is not None else "N/A",
            "micro_recall": f"{micro_r}%" if micro_r is not None else "N/A",
        }

        # 1. Structure JSON Report
        json_data = {
            "metadata": {
                "report_title": "LAPORAN EVALUASI BENCHMARK AKADEMIK AUDITOR TESIS MIKOM 2026",
                "evaluation_timestamp": timestamp,
                "base_commit": getattr(self.config, "base_commit", self.config.code_version),
                "code_version": self.config.code_version,
                "working_tree_dirty": getattr(self.config, "working_tree_dirty", True),
                "dataset_version": self.config.dataset_version,
                "ruleset_id": self.config.ruleset_id,
                "ruleset_version": self.config.ruleset_version,
                "split": self.config.split,
                "deterministic": True,
                "offline_compatible": self.config.offline_mode,
            },
            "quality_gate": quality_gate,
            "evaluation_summary": summary.to_dict(),
            "inter_annotator_agreement": agreement,
            "error_analysis": error_summary,
            "evaluation_limitations": [
                "Sifat Dataset: Evaluasi ini menggunakan dataset terstandarisasi berbasis skenario untuk menguji konsistensi dan determinisme penegakan aturan formal pada naskah tesis. Hasilnya belum dapat digeneralisasi ke seluruh variasi dokumen tesis mahasiswa tanpa pengujian empiris tambahan pada dokumen nyata yang dianonimkan.",
                "Cakupan Sistem yang Dievaluasi: Benchmark berfokus pada komponen audit berbasis aturan, termasuk pemeriksaan pola teks, geometri atau tata letak dokumen, validasi formula, dan keselarasan antardokumen. Evaluasi ini tidak mengukur halusinasi pada generative Large Language Models (LLM), dan tidak membuktikan bahwa seluruh komponen aplikasi bebas dari kesalahan.",
                "Pemisahan Dataset dan Potensi Data Leakage: Dataset pengembangan dan evaluasi dimaksudkan untuk memiliki fungsi yang terpisah. Namun, klaim bebas data leakage memerlukan verifikasi terhadap duplikasi dokumen, kesamaan contoh, serta penggunaan informasi evaluasi dalam pengembangan aturan. Pemisahan tersebut tidak dianggap tervalidasi hanya berdasarkan label split.",
                "Ukuran Sampel dan Representativitas: Jumlah dokumen dan temuan referensi pada benchmark ini terbatas. Oleh karena itu, nilai Precision, Recall, F1-score, dan kesepakatan antarpenilai hanya menggambarkan performa pada sampel evaluasi yang diuji. Nilai tersebut tidak boleh ditafsirkan sebagai estimasi akurasi populasi seluruh naskah tesis.",
                "Kecocokan Lokasi dan Tingkat Keparahan: Evaluasi dengan strict_location=False tidak menguji kesesuaian halaman secara ketat. Ketepatan lokasi dan tingkat keparahan perlu dilaporkan secara terpisah, dengan pengujian tambahan ketika informasi halaman pada anotasi referensi tersedia.",
                "Kebutuhan Validasi Lanjutan: Sebelum digunakan sebagai bukti validasi eksternal atau dasar klaim kinerja publikasi ilmiah, benchmark perlu diperluas menggunakan dokumen yang representatif, anotasi independen dari penilai yang kompeten, prosedur adjudikasi atas perbedaan penilaian, serta pengujian reproduksibilitas pada lingkungan yang bersih."
            ]
        }

        json_path = self.output_dir / f"{report_prefix}_{self.config.split}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)

        # 2. Markdown Report
        md_content = self._render_markdown_report(
            timestamp=timestamp,
            quality_gate=quality_gate,
            summary=summary,
            agreement=agreement,
            error_summary=error_summary,
        )

        md_path = self.output_dir / f"{report_prefix}_{self.config.split}.md"
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_content)

        return json_path, md_path

    def _render_markdown_report(
        self,
        timestamp: str,
        quality_gate: dict[str, Any],
        summary: BenchmarkEvaluationSummary,
        agreement: dict[str, Any],
        error_summary: dict[str, Any],
    ) -> str:
        """Renders an academic Markdown report."""
        # Render category table
        cat_rows = []
        for cat, m in summary.per_category.items():
            cat_rows.append(
                f"| `{cat}` | {m.support} | {m.true_positives} | {m.false_positives} | {m.false_negatives} | "
                f"{m.to_dict()['precision_display']} | {m.to_dict()['recall_display']} | {m.to_dict()['f1_display']} |"
            )
        table_cats = "\n".join(cat_rows) if cat_rows else "| - | - | - | - | - | - | - | - |"

        # Render error breakdown
        err_breakdown_rows = []
        for err_type, count in error_summary.get("breakdown", {}).items():
            err_breakdown_rows.append(f"- **{err_type}**: {count} kasus")
        err_list = "\n".join(err_breakdown_rows) if err_breakdown_rows else "- Tidak ada error terdeteksi."

        gate_badge = "🟢 **PASSED**" if quality_gate["status"] == "PASSED" else "🔴 **FAILED**"

        return f"""# LAPORAN EVALUASI BENCHMARK AKADEMIK AUDITOR TESIS (MIKOM 2026)

**Tanggal Evaluasi:** {timestamp}  
**Commit Acuan:** `{getattr(self.config, 'base_commit', self.config.code_version)}` (working tree dirty: {getattr(self.config, 'working_tree_dirty', True)})  
**Versi Dataset:** `{self.config.dataset_version}` ({self.config.split} split)  
**Aturan Acuan:** `{self.config.ruleset_id} v{self.config.ruleset_version}`  
**Mode Eksekusi:** Deterministik & Offline (100% Bebas Akses Internet)

---

## 1. Status Quality Gate

| Parameter | Target Ambang Batas | Hasil Aktual | Status |
|---|:---:|:---:|:---:|
| **Status Rilis** | Standar Kualitas Rilis | {quality_gate['status']} | {gate_badge} |
| **Micro Precision** | >= 85.0% | {quality_gate['micro_precision']} | {'✓' if quality_gate['status'] == 'PASSED' else '❌'} |
| **Micro Recall** | >= 85.0% | {quality_gate['micro_recall']} | {'✓' if quality_gate['status'] == 'PASSED' else '❌'} |
| **Micro F1-Score** | >= 85.0% | {quality_gate['micro_f1']} | {'✓' if quality_gate['status'] == 'PASSED' else '❌'} |

---

## 2. Ringkasan Kinerja & Evaluasi Per Kategori

- **Total Dokumen Teranotasi:** {summary.total_documents}
- **Total Temuan Referensi (Ground Truth):** {summary.total_reference_findings}
- **Total Temuan Terdeteksi:** {summary.total_detected_findings}

### Tabel Metrik per Kategori Audit

| Kategori Audit | Support (Ref) | TP | FP | FN | Precision | Recall | F1-Score |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
{table_cats}

### Ringkasan Rata-Rata Agregat

- **Micro Average:** Precision: {summary.micro_metrics['precision_display']} | Recall: {summary.micro_metrics['recall_display']} | F1: {summary.micro_metrics['f1_display']}
- **Macro Average:** Precision: {summary.macro_metrics['precision_display']} | Recall: {summary.macro_metrics['recall_display']} | F1: {summary.macro_metrics['f1_display']}

---

## 3. Kesepakatan Antar-Penilai (Inter-Annotator Agreement)

- **Jumlah Sampel Evaluasi Penilai:** {agreement.get('sample_count', 0)}
- **Persentase Kesepakatan ($P_o$):** {agreement.get('observed_agreement', 'N/A')}%
- **Peluang Kesepakatan Acak ($P_e$):** {agreement.get('chance_agreement', 'N/A')}%
- **Koefisien Cohen's Kappa (κ):** {agreement.get('kappa', 'N/A')}
- **Tingkat Kekuatan Kesepakatan:** {agreement.get('agreement_strength', 'N/A')}
- **Jumlah Perbedaan Penilaian:** {agreement.get('disagreements_count', 0)}

---

## 4. Taksonomi & Analisis Kesalahan (Error Analysis)

- **Total Kesalahan Teridentifikasi:** {error_summary.get('total_errors', 0)}
- **Kategori Risiko Tertinggi:** `{error_summary.get('highest_risk_category', 'None')}`

### Rincian Kegagalan:
{err_list}

---

## 5. Batasan Evaluasi (*Evaluation Limitations*)

1. **Sifat Dataset.** Evaluasi ini menggunakan dataset terstandarisasi berbasis skenario untuk menguji konsistensi dan determinisme penegakan aturan formal pada naskah tesis. Hasilnya belum dapat digeneralisasi ke seluruh variasi dokumen tesis mahasiswa tanpa pengujian empiris tambahan pada dokumen nyata yang dianonimkan.

2. **Cakupan Sistem yang Dievaluasi.** Benchmark berfokus pada komponen audit berbasis aturan, termasuk pemeriksaan pola teks, geometri atau tata letak dokumen, validasi formula, dan keselarasan antardokumen. Evaluasi ini tidak mengukur halusinasi pada generative Large Language Models (LLM), dan tidak membuktikan bahwa seluruh komponen aplikasi bebas dari kesalahan.

3. **Pemisahan Dataset dan Potensi *Data Leakage*.** Dataset pengembangan dan evaluasi dimaksudkan untuk memiliki fungsi yang terpisah. Namun, klaim bebas *data leakage* memerlukan verifikasi terhadap duplikasi dokumen, kesamaan contoh, serta penggunaan informasi evaluasi dalam pengembangan aturan. Pemisahan tersebut tidak dianggap tervalidasi hanya berdasarkan label split.

4. **Ukuran Sampel dan Representativitas.** Jumlah dokumen dan temuan referensi pada benchmark ini terbatas. Oleh karena itu, nilai Precision, Recall, F1-score, dan kesepakatan antarpenilai hanya menggambarkan performa pada sampel evaluasi yang diuji. Nilai tersebut tidak boleh ditafsirkan sebagai estimasi akurasi populasi seluruh naskah tesis.

5. **Kecocokan Lokasi dan Tingkat Keparahan.** Evaluasi dengan `strict_location=False` tidak menguji kesesuaian halaman secara ketat. Ketepatan lokasi dan tingkat keparahan perlu dilaporkan secara terpisah, dengan pengujian tambahan ketika informasi halaman pada anotasi referensi tersedia.

6. **Kebutuhan Validasi Lanjutan.** Sebelum digunakan sebagai bukti validasi eksternal atau dasar klaim kinerja publikasi ilmiah, benchmark perlu diperluas menggunakan dokumen yang representatif, anotasi independen dari penilai yang kompeten, prosedur adjudikasi atas perbedaan penilaian, serta pengujian reproduksibilitas pada lingkungan yang bersih.
"""
