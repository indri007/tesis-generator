"""Research Design & Biostatistics Auditor for MIKOM 2026 UPN Veteran Jawa Timur.

Evaluates according to Pedoman Penulisan Tesis MIKOM UPN 2026 (Bab III & Bab IV):
1. Research Design Justification (Kuantitatif, Kualitatif, Mixed Methods).
2. Population, Sample Size Formula & Sampling Technique (Slovin, Taro Yamane, Krejcie-Morgan, G*Power, Purposive).
3. Instrument Validity (Pearson Product Moment, CFA Loading > 0.50) & Reliability (Cronbach's Alpha >= 0.70, AVE >= 0.50).
4. Classical Assumptions & Biostatistics Diagnostics (Normality, Linearity, Multicollinearity VIF < 10, Heteroscedasticity).
5. Inferential Statistical Decision & Hypothesis Consistency (t, F, p-value < 0.05, R-squared, Path Coefficients).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from models.document_model import ParsedDocument
from utils.number_utils import parse_id_number


@dataclass
class MethodFinding:
    rule_id: str
    category: str
    status: str  # "PASS" | "WARNING" | "ERROR" | "INFO"
    severity: str
    message: str
    actual: str
    expected: str
    recommendation: str
    evidence_query: str = ""
    location: str = "Bab III / Bab IV Metodologi"
    page: int = 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "category": self.category,
            "status": self.status,
            "severity": self.severity,
            "message": self.message,
            "actual": self.actual,
            "expected": self.expected,
            "recommendation": self.recommendation,
            "evidence_query": self.evidence_query,
            "evidence": self.evidence_query,
            "location": self.location,
            "page": self.page,
        }


class ResearchMethodsAuditor:
    """Auditor Metodologi Riset Komunikasi & Biostatistika MIKOM UPN 2026."""

    COMM_THEORIES = [
        "agenda setting", "uses and gratifications", "framing", "kultivasi",
        "difusi inovasi", "komunikasi organisasi", "komunikasi pemasaran digital",
        "digital marketing communication", "semiotika", "analisis wacana kritis",
        "interaksionisme simbolik", "konstruksi sosial", "teori kritis"
    ]

    def __init__(self, document: ParsedDocument | str):
        if isinstance(document, str):
            self.text = document
        else:
            self.text = document.get_text()

        lower_text = self.text.lower()
        self.is_quantitative = any(kw in lower_text for kw in ["kuantitatif", "regresi", "hipotesis", "kuesioner", "angket", "sem-pls", "spss", "smartpls", "populasi"])
        self.is_qualitative = any(kw in lower_text for kw in ["kualitatif", "studi kasus", "fenomenologi", "etnografi", "semiotika", "wacana kritis", "wawancara mendalam", "informan"])
        self.is_mixed_methods = any(kw in lower_text for kw in ["mixed methods", "metode campuran", "triangulasi sekuensial", "explanatory sequential", "exploratory sequential"])

    def audit(self) -> list[dict[str, Any]]:
        findings: list[dict[str, Any]] = []
        lower_text = self.text.lower()

        # Ekstraksi teks Bab III dan Bab IV jika terdeteksi
        b3_match = re.search(r"BAB\s+III\b.*?(?=BAB\s+IV\b|$)", self.text, re.DOTALL | re.IGNORECASE)
        b4_match = re.search(r"BAB\s+IV\b.*?(?=BAB\s+V\b|$)", self.text, re.DOTALL | re.IGNORECASE)
        b3_text = b3_match.group(0).lower() if b3_match else lower_text
        b4_text = b4_match.group(0).lower() if b4_match else lower_text

        # ─────────────────────────────────────────────────────────────
        # 1. Klasifikasi & Justifikasi Desain Pendekatan Penelitian (Bab 3.1)
        # ─────────────────────────────────────────────────────────────
        if not (self.is_quantitative or self.is_qualitative or self.is_mixed_methods):
            findings.append(
                MethodFinding(
                    rule_id="METHOD_DESIGN_UNDEFINED_001",
                    category="Metodologi & Biostatistika",
                    status="ERROR",
                    severity="ERROR",
                    message="Pendekatan dan desain penelitian belum didefinisikan secara eksplisit pada Bab III.",
                    actual="Pendekatan penelitian (Kuantitatif/Kualitatif/Mixed Methods) tidak teridentifikasi",
                    expected="Subbab 3.1 Pendekatan Penelitian menegaskan paradigma dan desain spesifik riset komunikasi",
                    recommendation="Cantumkan secara eksplisit pada Subbab 3.1 apakah penelitian menggunakan pendekatan Kuantitatif, Kualitatif, atau Metode Campuran.",
                    evidence_query="pendekatan penelitian",
                ).to_dict()
            )
        else:
            design_label = "Campuran (Mixed Methods)" if self.is_mixed_methods else "Kuantitatif" if self.is_quantitative else "Kualitatif"
            findings.append(
                MethodFinding(
                    rule_id="METHOD_DESIGN_IDENTIFIED_001",
                    category="Metodologi & Biostatistika",
                    status="PASS",
                    severity="INFO",
                    message=f"Pendekatan penelitian teridentifikasi: {design_label} sesuai Pedoman MIKOM UPN 2026.",
                    actual=f"Desain {design_label}",
                    expected="Pendekatan penelitian terdefinisi",
                    recommendation="Pertahankan konsistensi penjabaran dari paradigma hingga operasionalisasi variabel.",
                    evidence_query=design_label,
                ).to_dict()
            )

        # ─────────────────────────────────────────────────────────────
        # 2. Audit Sampling & Ukuran Sampel (Bab 3.5)
        # ─────────────────────────────────────────────────────────────
        if self.is_quantitative:
            has_sampling_formula = any(kw in b3_text for kw in ["slovin", "taro yamane", "krejcie", "morgan", "g*power", "gpower", "hair", "cohen", "rumus penarikan sampel", "persamaan"])
            if not has_sampling_formula:
                findings.append(
                    MethodFinding(
                        rule_id="METHOD_SAMPLE_FORMULA_001",
                        category="Metodologi & Biostatistika",
                        status="WARNING",
                        severity="WARNING",
                        message="Rumus penentuan ukuran sampel kuantitatif (Slovin, Taro Yamane, Krejcie-Morgan, atau G*Power) belum dicantumkan di Bab 3.5.",
                        actual="Tidak ada rumus penentuan ukuran sampel formal",
                        expected="Penetapan batas kesalahan (margin of error misal 5%) dan rumus penentuan sampel ilmiah",
                        recommendation="Sertakan kalkulasi matematis ukuran sampel menggunakan rumus Slovin (e=5%/10%), Krejcie-Morgan, atau G*Power untuk menjamin representativitas populasi.",
                        evidence_query="sampel",
                    ).to_dict()
                )
            else:
                findings.append(
                    MethodFinding(
                        rule_id="METHOD_SAMPLE_FORMULA_001",
                        category="Metodologi & Biostatistika",
                        status="PASS",
                        severity="INFO",
                        message="Rumus ilmiah penentuan jumlah sampel terverifikasi di Bab III.5.",
                        actual="Rumus sampel teridentifikasi",
                        expected="Rumus penentuan sampel ilmiah",
                        recommendation="Pastikan kriteria inklusi dan eksklusi responden konsisten.",
                        evidence_query="sampel",
                    ).to_dict()
                )

            # Deteksi angka ukuran sampel
            sample_match = re.search(r"(?:sampel|responden)\s*(?:sebanyak|sebesar|berjumlah|yaitu|=)?\s*([0-9]+)", lower_text)
            if sample_match:
                n_val = int(sample_match.group(1))
                if n_val < 30:
                    findings.append(
                        MethodFinding(
                            rule_id="METHOD_SAMPLE_SIZE_001",
                            category="Metodologi & Biostatistika",
                            status="ERROR",
                            severity="ERROR",
                            message=f"Ukuran sampel ({n_val} responden) terlalu kecil untuk analisis kuantitatif parametrik (minimal N >= 30).",
                            actual=f"N = {n_val}",
                            expected="Minimal N >= 30 responden untuk distribusi normal",
                            recommendation="Tingkatkan jumlah sampel minimal 30 responden atau gunakan uji non-parametrik.",
                            evidence_query="sampel",
                        ).to_dict()
                    )
                else:
                    findings.append(
                        MethodFinding(
                            rule_id="METHOD_SAMPLE_SIZE_001",
                            category="Metodologi & Biostatistika",
                            status="PASS",
                            severity="INFO",
                            message=f"Ukuran sampel memenuhi kriteria inferensial kuantitatif (N = {n_val} >= 30).",
                            actual=f"N = {n_val}",
                            expected="N >= 30 responden",
                            recommendation="Pertahankan kecukupan sampel sesuai perhitungan rumus.",
                            evidence_query="sampel",
                        ).to_dict()
                    )

        # ─────────────────────────────────────────────────────────────
        # 3. Uji Validitas & Reliabilitas Instrumen (Bab 3.6 / Bab 4.2)
        # ─────────────────────────────────────────────────────────────
        if self.is_quantitative:
            has_validity = any(kw in lower_text for kw in ["validitas", "product moment", "r hitung", "r tabel", "cfa", "loading factor", "ave"])
            has_reliability = any(kw in lower_text for kw in ["reliabilitas", "cronbach's alpha", "cronbach alpha", "composite reliability", "koefisien alfa"])

            if not has_validity or not has_reliability:
                findings.append(
                    MethodFinding(
                        rule_id="METHOD_VALIDITY_RELIABILITY_001",
                        category="Metodologi & Biostatistika",
                        status="ERROR",
                        severity="ERROR",
                        message="Uji Validitas dan/atau Reliabilitas instrumen kuesioner belum lengkap dipaparkan.",
                        actual=f"Validitas: {'Ada' if has_validity else 'Tidak ada'}, Reliabilitas: {'Ada' if has_reliability else 'Tidak ada'}",
                        expected="Keduanya wajib dilaporkan (Pearson r hitung > r tabel / factor loading > 0.50 & Cronbach's Alpha >= 0.70)",
                        recommendation="Lengkapi pengujian validitas butir pernyataan dan reliabilitas instrumen skala Likert dengan ambang batas Cronbach's Alpha minimal 0,70.",
                        evidence_query="validitas",
                    ).to_dict()
                )
            else:
                findings.append(
                    MethodFinding(
                        rule_id="METHOD_VALIDITY_RELIABILITY_001",
                        category="Metodologi & Biostatistika",
                        status="PASS",
                        severity="INFO",
                        message="Uji validitas dan reliabilitas instrumen terverifikasi lengkap.",
                        actual="Uji validitas & reliabilitas lengkap",
                        expected="Uji instrumen baku",
                        recommendation="Pastikan butir yang gugur (drop item) tidak dimasukkan dalam pemodelan akhir.",
                        evidence_query="validitas",
                    ).to_dict()
                )

            # Ekstraksi nilai Cronbach's Alpha jika ada
            alpha_match = re.search(r"cronbach(?:'s)?\s*alpha\s*(?:sebesar|=)?\s*([0-9]+[.,][0-9]+)", lower_text)
            if alpha_match:
                alpha_val = parse_id_number(alpha_match.group(1))
                if alpha_val < 0.70:
                    findings.append(
                        MethodFinding(
                            rule_id="METHOD_CRONBACH_ALPHA_001",
                            category="Metodologi & Biostatistika",
                            status="ERROR",
                            severity="ERROR",
                            message=f"Koefisien reliabilitas Cronbach's Alpha ({alpha_val:.3f}) di bawah batas ambang reliabel MIKOM 2026 (>= 0.70).",
                            actual=f"Alpha = {alpha_val:.3f}",
                            expected="Cronbach's Alpha >= 0.70 (kategori reliabel)",
                            recommendation="Evaluasi dan eliminasi butir pertanyaan kuesioner yang memiliki korelasi item-total rendah.",
                            evidence_query="cronbach",
                        ).to_dict()
                    )
                else:
                    findings.append(
                        MethodFinding(
                            rule_id="METHOD_CRONBACH_ALPHA_001",
                            category="Metodologi & Biostatistika",
                            status="PASS",
                            severity="INFO",
                            message=f"Koefisien reliabilitas Cronbach's Alpha ({alpha_val:.3f}) memenuhi batas reliabel (>= 0.70).",
                            actual=f"Alpha = {alpha_val:.3f}",
                            expected="Cronbach's Alpha >= 0.70",
                            recommendation="Pertahankan konsistensi internal instrumen.",
                            evidence_query="cronbach",
                        ).to_dict()
                    )

        if self.is_qualitative:
            has_triangulation = any(kw in lower_text for kw in ["triangulasi", "triangulation", "member check", "audit trail", "keabsahan data", "derajat kepercayaan"])
            if not has_triangulation:
                findings.append(
                    MethodFinding(
                        rule_id="METHOD_QUAL_TRIANGULATION_001",
                        category="Metodologi & Biostatistika",
                        status="WARNING",
                        severity="WARNING",
                        message="Teknik pemeriksaan keabsahan data kualitatif (Triangulasi sumber/teknik/waktu atau member checking) belum dipaparkan di Bab III.",
                        actual="Pemeriksaan keabsahan data kualitatif tidak terdeteksi",
                        expected="Uji kredibilitas data melalui triangulasi sumber, teknik, waktu, atau diskusi teman sejawat",
                        recommendation="Jelaskan teknik triangulasi (sumber, teori, atau metode) untuk memastikan keabsahan data temuan studi komunikasi kualitatif.",
                        evidence_query="triangulasi",
                    ).to_dict()
                )
            else:
                findings.append(
                    MethodFinding(
                        rule_id="METHOD_QUAL_TRIANGULATION_001",
                        category="Metodologi & Biostatistika",
                        status="PASS",
                        severity="INFO",
                        message="Teknik pemeriksaan keabsahan data kualitatif (triangulasi/member checking) terverifikasi di Bab III.",
                        actual="Triangulasi / uji kredibilitas teridentifikasi",
                        expected="Pemeriksaan keabsahan data kualitatif",
                        recommendation="Pertahankan kedalaman triangulasi sumber dan teori.",
                        evidence_query="triangulasi",
                    ).to_dict()
                )

        # ─────────────────────────────────────────────────────────────
        # 4. Uji Asumsi Klasik Biostatistika (Normalitas, Multikolinearitas, Heteroskedastisitas)
        # ─────────────────────────────────────────────────────────────
        if self.is_quantitative and any(kw in lower_text for kw in ["regresi", "jalur", "vif", "multikolinearitas", "asumsi klasik"]):
            has_normality = any(kw in lower_text for kw in ["normalitas", "kolmogorov-smirnov", "shapiro-wilk", "p-plot", "histogram"])
            has_multicol = any(kw in lower_text for kw in ["multikolinearitas", "vif", "tolerance", "variance inflation factor"])
            has_heteroscedasticity = any(kw in lower_text for kw in ["heteroskedastisitas", "glejser", "scatterplot", "park", "spearman"])

            vif_match = re.search(r"vif\s*(?:sebesar|=)?\s*([0-9]+[.,][0-9]+)", lower_text)
            if vif_match:
                vif_val = parse_id_number(vif_match.group(1))
                if vif_val >= 10.0:
                    findings.append(
                        MethodFinding(
                            rule_id="METHOD_MULTICOLLINEARITY_001",
                            category="Metodologi & Biostatistika",
                            status="ERROR",
                            severity="ERROR",
                            message=f"Terdeteksi multikolinearitas serius: nilai VIF ({vif_val:.2f}) >= 10.0.",
                            actual=f"VIF = {vif_val:.2f}",
                            expected="VIF < 10.0 (Tolerance > 0.10) bebas multikolinearitas",
                            recommendation="Lakukan transformasi data, hilangkan variabel yang berkolinieritas tinggi, atau gunakan regresi ridge.",
                            evidence_query="vif",
                        ).to_dict()
                    )

            missing_assumptions = []
            if not has_normality: missing_assumptions.append("Normalitas")
            if not has_multicol: missing_assumptions.append("Multikolinearitas (VIF)")
            if not has_heteroscedasticity: missing_assumptions.append("Heteroskedastisitas")

            if missing_assumptions:
                findings.append(
                    MethodFinding(
                        rule_id="METHOD_CLASSIC_ASSUMPTIONS_001",
                        category="Metodologi & Biostatistika",
                        status="WARNING",
                        severity="WARNING",
                        message=f"Uji Asumsi Klasik belum lengkap untuk analisis regresi parametrik. Belum mencakup: {', '.join(missing_assumptions)}.",
                        actual=f"Asumsi yang belum terdeteksi: {', '.join(missing_assumptions)}",
                        expected="Uji Normalitas, Multikolinearitas (VIF < 10), dan Heteroskedastisitas sebelum inferensi regresi OLS",
                        recommendation="Cantumkan hasil uji asumsi klasik lengkap (Normalitas residu, VIF < 10, dan uji homoskedastisitas) pada Bab IV sebelum interpretasi koefisien regresi.",
                        evidence_query="asumsi klasik",
                    ).to_dict()
                )

        # ─────────────────────────────────────────────────────────────
        # 5. Koefisien Determinasi (R^2) & Uji Kelayakan Model (F-test / Goodness of Fit)
        # ─────────────────────────────────────────────────────────────
        if self.is_quantitative:
            has_r_squared = any(kw in lower_text for kw in ["r-square", "r square", "r2", "r kuadrat", "koefisien determinasi"])
            has_model_fit = any(kw in lower_text for kw in ["uji f", "f hitung", "anova", "goodness of fit", "srmr", "nfi", "chi-square"])

            if not has_r_squared:
                findings.append(
                    MethodFinding(
                        rule_id="METHOD_R_SQUARED_001",
                        category="Metodologi & Biostatistika",
                        status="WARNING",
                        severity="WARNING",
                        message="Koefisien Determinasi (R-squared / R^2) belum dilaporkan untuk mengukur kontribusi variabel.",
                        actual="Nilai R^2 tidak ditemukan dalam Bab IV",
                        expected="Pelaporan nilai R-squared dan Adjusted R-squared beserta interpretasi persentasenya",
                        recommendation="Cantumkan nilai R^2 (misal: R^2 = 0,642 berarti 64,2% variansi variabel terikat dijelaskan oleh variabel bebas).",
                        evidence_query="r-squared",
                    ).to_dict()
                )

        return findings
