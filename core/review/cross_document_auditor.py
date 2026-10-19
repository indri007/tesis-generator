"""Cross Document Auditor: Compares published journal/article against thesis."""

from __future__ import annotations

import re
from typing import Any

from models.document_model import ParsedDocument


class CrossDocumentAuditor:
    """Audits consistency between published journal article and thesis manuscript."""

    def __init__(self, thesis_doc: ParsedDocument, journal_doc: ParsedDocument):
        self.thesis = thesis_doc
        self.journal = journal_doc
        self.t_text = thesis_doc.get_text()
        self.j_text = journal_doc.get_text()

    def audit(self) -> tuple[list[dict[str, Any]], list[dict[str, Any]], float]:
        """Returns (findings, comparison_table, alignment_score)."""
        findings = []
        table = []

        scores = []

        # 1. Sample Size Comparison
        t_samples = re.findall(r"(?:sampel|responden)\s*(?:sebanyak|sebesar|=)?\s*(\d{2,4})", self.t_text, re.IGNORECASE)
        j_samples = re.findall(r"(?:sampel|responden|sample)\s*(?:sebanyak|sebesar|=)?\s*(\d{2,4})", self.j_text, re.IGNORECASE)

        t_sample_val = t_samples[0] if t_samples else "Tidak terdeteksi"
        j_sample_val = j_samples[0] if j_samples else "Tidak terdeteksi"

        if t_samples and j_samples:
            if t_samples[0] == j_samples[0]:
                table.append({
                    "element": "Jumlah Sampel",
                    "thesis": f"{t_sample_val} responden",
                    "journal": f"{j_sample_val} responden",
                    "status": "PASS",
                    "notes": "Jumlah responden identik antara tesis dan jurnal."
                })
                scores.append(100.0)
            else:
                table.append({
                    "element": "Jumlah Sampel",
                    "thesis": f"{t_sample_val} responden",
                    "journal": f"{j_sample_val} responden",
                    "status": "ERROR",
                    "notes": f"Sampel berbeda ({t_sample_val} vs {j_sample_val}) tanpa catatan subset."
                })
                scores.append(40.0)
                findings.append({
                    "rule_id": "JOURNAL_ALIGNMENT_SAMPLE_001",
                    "category": "Journal vs Tesis",
                    "status": "ERROR",
                    "field": "journal_comparison.sample_match",
                    "actual": f"Tesis: {t_sample_val}, Jurnal: {j_sample_val}",
                    "expected": f"Jumlah sampel konsisten ({t_sample_val} responden)",
                    "message": f"Jumlah sampel pada artikel jurnal ({j_sample_val}) berbeda dengan naskah tesis ({t_sample_val}).",
                    "evidence_query": f"{j_sample_val} responden",
                    "recommendation": "Pastikan artikel jurnal mencantumkan justifikasi bahwa data jurnal merupakan subset/kelompok responden tertentu dari tesis.",
                    "source": {"title": "Komponen Publikasi Ilmiah Tesis (3 SKS)", "page": 3, "verified": True}
                })
        else:
            table.append({
                "element": "Jumlah Sampel",
                "thesis": t_sample_val,
                "journal": j_sample_val,
                "status": "UNVERIFIED",
                "notes": "Informasi sampel tidak dapat diekstrak otomatis."
            })
            scores.append(70.0)

        # 2. Main Variables Comparison
        # Look for X1, X2, Y in both
        t_vars = set(re.findall(r"\b([XYZ]\d?)\b", self.t_text))
        j_vars = set(re.findall(r"\b([XYZ]\d?)\b", self.j_text))
        common_vars = t_vars.intersection(j_vars)

        if common_vars:
            table.append({
                "element": "Variabel Penelitian",
                "thesis": ", ".join(sorted(t_vars)[:4]),
                "journal": ", ".join(sorted(j_vars)[:4]),
                "status": "PASS" if t_vars == j_vars else "WARNING",
                "notes": "Variabel utama selaras." if t_vars == j_vars else "Sebagian variabel berbeda notasi."
            })
            scores.append(90.0 if t_vars == j_vars else 75.0)
        else:
            table.append({
                "element": "Variabel Penelitian",
                "thesis": "Konstruk Tesis",
                "journal": "Konstruk Jurnal",
                "status": "UNVERIFIED",
                "notes": "Perlu verifikasi manual konstruk teoretis."
            })
            scores.append(75.0)

        # 3. Method Comparison
        t_is_quant = "kuantitatif" in self.t_text.lower() or "regresi" in self.t_text.lower()
        j_is_quant = "kuantitatif" in self.j_text.lower() or "regresi" in self.j_text.lower()

        if t_is_quant == j_is_quant:
            table.append({
                "element": "Pendekatan Penelitian",
                "thesis": "Kuantitatif" if t_is_quant else "Kualitatif",
                "journal": "Kuantitatif" if j_is_quant else "Kualitatif",
                "status": "PASS",
                "notes": "Pendekatan metodologi selaras."
            })
            scores.append(100.0)
        else:
            table.append({
                "element": "Pendekatan Penelitian",
                "thesis": "Kuantitatif" if t_is_quant else "Kualitatif",
                "journal": "Kuantitatif" if j_is_quant else "Kualitatif",
                "status": "ERROR",
                "notes": "Terdapat perbedaan paradigma metode penelitian."
            })
            scores.append(30.0)
            findings.append({
                "rule_id": "JOURNAL_ALIGNMENT_METHOD_001",
                "category": "Journal vs Tesis",
                "status": "ERROR",
                "field": "journal_comparison.method_match",
                "actual": "Metode berbeda",
                "expected": "Metode penelitian selaras",
                "message": "Metode penelitian pada jurnal dan tesis terindikasi berbeda.",
                "evidence_query": "kuantitatif",
                "recommendation": "Samakan orientasi paradigma dan instrumen metodologi antara naskah publikasi dan tesis.",
                "source": {"title": "Pedoman Penulisan Tesis MIKOM 2026", "page": 3, "verified": True}
            })

        # Calculate alignment score
        alignment_score = round(sum(scores) / max(1, len(scores)), 1)
        return findings, table, alignment_score
