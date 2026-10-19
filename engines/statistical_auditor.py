"""Statistical Auditor: Verifies sample size consistency, alpha, p-values, and hypothesis decisions."""

from __future__ import annotations

import re
from typing import Any

from models.document_model import ParsedDocument
from utils.number_utils import parse_id_number


class StatisticalAuditor:
    """Audits inferential statistical consistency, sample sizes, and hypothesis conclusions."""

    def __init__(self, document: ParsedDocument):
        self.doc = document
        self.text = document.get_text()

    def audit(self) -> list[dict[str, Any]]:
        findings = []

        # 1. Sample Size Consistency between Bab III and Bab IV
        # Bab III: e.g. "sampel sebanyak 120 responden"
        # Bab IV: e.g. "responden yang dianalisis sebanyak 118"
        b3_match = re.search(r"BAB\s+III\b.*?(?=BAB\s+IV\b|$)", self.text, re.DOTALL | re.IGNORECASE)
        b4_match = re.search(r"BAB\s+IV\b.*?(?=BAB\s+V\b|$)", self.text, re.DOTALL | re.IGNORECASE)

        b3_text = b3_match.group(0) if b3_match else ""
        b4_text = b4_match.group(0) if b4_match else ""

        sample_b3_matches = re.findall(r"(?:sebanyak|sebesar|=|\b)\s*(\d{2,4})\s*(?:orang|responden)", b3_text, re.IGNORECASE)
        sample_b4_matches = re.findall(r"(?:sebanyak|sebesar|=|\b)\s*(\d{2,4})\s*(?:orang|responden)", b4_text, re.IGNORECASE)

        if sample_b3_matches and sample_b4_matches:
            s3 = int(sample_b3_matches[0])
            s4 = int(sample_b4_matches[0])
            if s3 != s4:
                # Check if exclusion / attrition was explained
                is_explained = any(w in b4_text.lower() for w in ["dikeluarkan", "drop", "gugur", "outlier", "cleaning"])
                if not is_explained:
                    findings.append({
                        "rule_id": "STAT_SAMPLE_CONSISTENCY_001",
                        "category": "Statistik",
                        "status": "ERROR",
                        "field": "statistics.sample_mismatch_count",
                        "actual": f"Bab III: {s3} responden, Bab IV: {s4} responden",
                        "expected": f"Jumlah sampel konsisten ({s3} responden) atau ada penjelasan eksklusi data",
                        "message": f"Inkonsistensi jumlah sampel responden: Bab III menyebutkan {s3}, sedangkan Bab IV menganalisis {s4} responden tanpa penjelasan eliminasi data.",
                        "evidence_query": f"{s4} responden",
                        "recommendation": f"Jelaskan alasan pengurangan sampel ({s3 - s4} responden tidak memenuhi kriteria/outlier) pada Bab IV, atau samakan jumlah sampel.",
                        "source": {"title": "Pedoman MIKOM 2026 Bab III.5 & Bab IV", "page": 35, "verified": True}
                    })
                else:
                    findings.append({
                        "rule_id": "STAT_SAMPLE_EXPLAINED_001",
                        "category": "Statistik",
                        "status": "PASS",
                        "field": "statistics.sample_mismatch_count",
                        "actual": f"{s3} responden awal, {s4} dianalisis (ada penjelasan eliminasi)",
                        "expected": "Perbedaan sampel terdokumentasi",
                        "message": "Perbedaan jumlah sampel terverifikasi memiliki justifikasi eliminasi/pembersihan data.",
                        "evidence_query": f"{s4} responden",
                        "recommendation": "Pertahankan dokumentasi kriteria inklusi dan eksklusi responden.",
                        "source": {"title": "Pedoman MIKOM 2026", "page": 35, "verified": True}
                    })

        # 2. Hypothesis Decision Consistency with p-value and Alpha (0.05)
        # e.g., p = 0.032 but text states "tidak signifikan" or "ditolak"
        p_matches = re.finditer(r"\bp\s*(?:[=<]|value)\s*([0-9.,]+)", b4_text, re.IGNORECASE)
        for pm in p_matches:
            p_val = parse_id_number(pm.group(1))
            if p_val is not None:
                snippet_around = b4_text[max(0, pm.start() - 100): min(len(b4_text), pm.end() + 200)].lower()
                if p_val < 0.05:
                    if any(term in snippet_around for term in ["tidak signifikan", "tidak berpengaruh signifikan", "h1 ditolak", "hipotesis ditolak"]):
                        findings.append({
                            "rule_id": "STAT_DECISION_CONSISTENCY_001",
                            "category": "Statistik",
                            "status": "ERROR",
                            "field": "statistics.contradiction_count",
                            "actual": f"p-value = {p_val} (< 0,05) namun disimpulkan 'tidak signifikan'",
                            "expected": "p < 0,05 disimpulkan berpengaruh signifikan (H1 diterima)",
                            "message": f"Kesimpulan pengujian hipotesis bertentangan! Dengan nilai p={p_val} (< 0,05), variabel terbukti signifikan namun narasi menyatakan tidak signifikan.",
                            "evidence_query": pm.group(0),
                            "recommendation": "Koreksi kesimpulan pengujian hipotesis: jika nilai signifikansi p < 0,05 maka hipotesis alternatif (H1) diterima dan berpengaruh signifikan.",
                            "source": {"title": "Statistika Inferensial MIKOM 2026", "page": 42, "verified": True}
                        })
                else:
                    if any(term in snippet_around for term in ["berpengaruh signifikan", "h1 diterima"]):
                        findings.append({
                            "rule_id": "STAT_DECISION_CONSISTENCY_001",
                            "category": "Statistik",
                            "status": "ERROR",
                            "field": "statistics.contradiction_count",
                            "actual": f"p-value = {p_val} (>= 0,05) namun disimpulkan 'berpengaruh signifikan'",
                            "expected": "p >= 0,05 disimpulkan tidak berpengaruh signifikan",
                            "message": f"Kesimpulan pengujian hipotesis bertentangan! Dengan nilai p={p_val} (>= 0,05), hipotesis tidak didukung secara empiris.",
                            "evidence_query": pm.group(0),
                            "recommendation": "Koreksi kesimpulan pengujian hipotesis: nilai p >= 0,05 berarti hipotesis tidak terbukti signifikan.",
                            "source": {"title": "Statistika Inferensial MIKOM 2026", "page": 42, "verified": True}
                        })

        return findings
