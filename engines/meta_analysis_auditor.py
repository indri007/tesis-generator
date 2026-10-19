"""Meta-Analysis & Systematic Review Auditor for MIKOM 2026 UPN Veteran Jawa Timur.

Evaluates:
1. PRISMA 2020 4-phase compliance (Identification, Screening, Eligibility, Included).
2. Multi-database search strategy (Scopus, WoS, SINTA/Garuda, DOAJ, etc.).
3. Effect size synthesis (Cohen's d, Pearson's r, Hedges' g, Odds Ratio, Risk Ratio).
4. Heterogeneity assessment (Cochran's Q, I^2 statistic, model selection).
5. Publication bias testing (Funnel plot, Egger's regression test, Begg's test).
6. Quality appraisal / Risk of bias tool (RoB 2, Newcastle-Ottawa, JBI, MMAT).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from models.document_model import ParsedDocument


@dataclass
class MetaAnalysisFinding:
    rule_id: str
    category: str
    status: str  # "PASS" | "WARNING" | "ERROR" | "INFO"
    severity: str
    message: str
    actual: str
    expected: str
    recommendation: str
    evidence_query: str = ""
    location: str = "Metodologi Meta-Analisis"
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


class MetaAnalysisAuditor:
    """Auditor metodologis kajian Meta-Analisis & Systematic Literature Review (SLR)

    sesuai standar PRISMA 2020 dan Pedoman Tesis MIKOM UPN 2026.
    """

    DATABASES = [
        "scopus", "web of science", "wos", "sinta", "garuda", "doaj",
        "google scholar", "sciencedirect", "springer", "taylor & francis",
        "sage", "emerald", "ieee", "pubmed"
    ]

    QUALITY_TOOLS = [
        "cochrane", "rob 2", "robins-i", "newcastle-ottawa", "jbi",
        "mmat", "casp", "prisma", "quadas"
    ]

    def __init__(self, document: ParsedDocument | str):
        if isinstance(document, str):
            self.text = document
        else:
            self.text = document.get_text()

        # Deteksi apakah naskah mengadopsi pendekatan Meta-Analisis / Systematic Review
        lower_text = self.text.lower()
        self.is_meta_analysis = any(
            kw in lower_text for kw in [
                "meta-analisis", "meta analisis", "meta-analysis",
                "systematic literature review", "systematic review",
                "tinjauan sistematis", "prisma 2020", "forest plot",
                "funnel plot", "effect size", "ukuran efek"
            ]
        )

    def audit(self) -> list[dict[str, Any]]:
        findings: list[dict[str, Any]] = []
        if not self.is_meta_analysis:
            return findings

        lower_text = self.text.lower()

        # 1. PRISMA Flow Protocol Verification (Identification -> Screening -> Eligibility -> Included)
        prisma_keywords = ["identifikasi", "penyaringan", "kelayakan", "eksklusi", "inklusi", "prisma"]
        found_prisma = [kw for kw in prisma_keywords if kw in lower_text]
        if len(found_prisma) < 3:
            findings.append(
                MetaAnalysisFinding(
                    rule_id="META_PRISMA_FLOW_001",
                    category="Meta-Analisis",
                    status="ERROR",
                    severity="ERROR",
                    message="Bagan alir PRISMA 2020 (Identification, Screening, Eligibility, Included) belum terdokumentasi lengkap.",
                    actual=f"Ditemukan {len(found_prisma)}/6 elemen alir seleksi studi",
                    expected="Menampilkan 4 tahapan diagram alir PRISMA 2020 lengkap dengan jumlah artikel di setiap fase",
                    recommendation="Sertakan diagram alir PRISMA 2020 yang merinci jumlah rekaman yang teridentifikasi, disaring, dieksklusi beserta alasannya, dan artikel final yang dianalisis.",
                    evidence_query="PRISMA",
                ).to_dict()
            )
        else:
            findings.append(
                MetaAnalysisFinding(
                    rule_id="META_PRISMA_FLOW_001",
                    category="Meta-Analisis",
                    status="PASS",
                    severity="INFO",
                    message="Tahapan seleksi artikel terdokumentasi sesuai protokol PRISMA.",
                    actual="Protokol seleksi artikel teridentifikasi",
                    expected="Protokol PRISMA transparan",
                    recommendation="Pertahankan transparansi kriteria inklusi dan eksklusi.",
                    evidence_query="PRISMA",
                ).to_dict()
            )

        # 2. Database Search Strategy Protocol (Minimal 2 database terindeks bereputasi)
        found_dbs = [db for db in self.DATABASES if db in lower_text]
        if len(found_dbs) < 2:
            findings.append(
                MetaAnalysisFinding(
                    rule_id="META_DATABASE_DIVERSITY_001",
                    category="Meta-Analisis",
                    status="WARNING",
                    severity="WARNING",
                    message="Strategi penelusuran pangkalan data literatur terbatas (kurang dari 2 database ilmiah).",
                    actual=f"Database terdeteksi: {', '.join(found_dbs) if found_dbs else 'tidak terdefinisi'}",
                    expected="Penelusuran minimal pada 2 database ilmiah terindeks (misal: Scopus, SINTA/Garuda, Web of Science, DOAJ)",
                    recommendation="Perluas penelusuran artikel primer ke minimal 2 database ilmiah untuk mencegah selection bias dalam kajian komunikasi.",
                    evidence_query="database literatur",
                ).to_dict()
            )
        else:
            findings.append(
                MetaAnalysisFinding(
                    rule_id="META_DATABASE_DIVERSITY_001",
                    category="Meta-Analisis",
                    status="PASS",
                    severity="INFO",
                    message=f"Pencarian literatur mencakup pangkalan data bereputasi: {', '.join(found_dbs[:4])}.",
                    actual=f"{len(found_dbs)} database ilmiah teridentifikasi",
                    expected="Minimal 2 database ilmiah",
                    recommendation="Dokumentasikan kata kunci boolean (AND, OR, NOT) yang digunakan.",
                    evidence_query=found_dbs[0],
                ).to_dict()
            )

        # 3. Effect Size & Statistical Synthesis (Cohen's d, r, Hedges' g, Odds Ratio)
        effect_size_kws = ["effect size", "ukuran efek", "cohen's d", "hedges' g", "odds ratio", "korelasi r", "fisher's z"]
        has_effect_size = any(kw in lower_text for kw in effect_size_kws)
        if not has_effect_size:
            findings.append(
                MetaAnalysisFinding(
                    rule_id="META_EFFECT_SIZE_001",
                    category="Meta-Analisis",
                    status="ERROR",
                    severity="ERROR",
                    message="Metrik Effect Size (ukuran efek) sintesis statistik belum dilaporkan secara eksplisit.",
                    actual="Tidak ditemukan pelaporan metrik effect size baku (r, Cohen's d, Hedges' g, atau Odds Ratio)",
                    expected="Pelaporan nilai ukuran efek gabungan (summary effect size) disertai 95% Confidence Interval (CI)",
                    recommendation="Hitung dan sajikan summary effect size beserta interval kepercayaan 95% dari studi-studi primer komunikasi yang dianalisis.",
                    evidence_query="effect size",
                ).to_dict()
            )
        else:
            findings.append(
                MetaAnalysisFinding(
                    rule_id="META_EFFECT_SIZE_001",
                    category="Meta-Analisis",
                    status="PASS",
                    severity="INFO",
                    message="Metrik Effect Size (ukuran efek) sintesis statistik dilaporkan secara eksplisit.",
                    actual="Metrik effect size teridentifikasi",
                    expected="Pelaporan nilai ukuran efek gabungan",
                    recommendation="Pertahankan pelaporan CI 95% dan p-value.",
                    evidence_query="effect size",
                ).to_dict()
            )

        # 4. Heterogeneity Assessment (Cochran's Q & I^2 statistic)
        hetero_kws = ["heterogenitas", "cochran", "i^2", "i-squared", "i2", "fixed effect", "random effect", "efek acak"]
        has_hetero = any(kw in lower_text for kw in hetero_kws)
        if not has_hetero:
            findings.append(
                MetaAnalysisFinding(
                    rule_id="META_HETEROGENEITY_001",
                    category="Meta-Analisis",
                    status="WARNING",
                    severity="WARNING",
                    message="Uji heterogenitas (Cochran's Q atau statistik I^2) belum dicantumkan dalam sintesis meta-analisis.",
                    actual="Uji heterogenitas tidak terdeteksi",
                    expected="Uji heterogenitas I^2 dan justifikasi pemilihan model (Fixed-Effect Model vs Random-Effects Model)",
                    recommendation="Laporkan nilai persentase heterogenitas I^2 (25% rendah, 50% moderat, 75% tinggi) untuk menjustifikasi model efek acak atau tetap.",
                    evidence_query="heterogenitas",
                ).to_dict()
            )
        else:
            findings.append(
                MetaAnalysisFinding(
                    rule_id="META_HETEROGENEITY_001",
                    category="Meta-Analisis",
                    status="PASS",
                    severity="INFO",
                    message="Uji heterogenitas Cochran's Q / I^2 terverifikasi dalam analisis.",
                    actual="Uji heterogenitas terdeteksi",
                    expected="Uji heterogenitas dilaporkan",
                    recommendation="Pertahankan justifikasi pemilihan model efek tetap/acak.",
                    evidence_query="heterogenitas",
                ).to_dict()
            )

        # Check high heterogeneity model discrepancy
        i2_match = re.search(r"i(?:-squared|\^2|2)?\s*(?:sebesar|=)?\s*([0-9]+[.,]?[0-9]*)\s*%", lower_text)
        if i2_match:
            try:
                i2_val = float(i2_match.group(1).replace(",", "."))
                if i2_val > 50.0 and ("fixed-effect" in lower_text or "fixed effect" in lower_text):
                    findings.append(
                        MetaAnalysisFinding(
                            rule_id="META_HETEROGENEITY_MODEL_001",
                            category="Meta-Analisis",
                            status="ERROR",
                            severity="ERROR",
                            message=f"Heterogenitas antar-studi tinggi (I^2 = {i2_val:.1f}% > 50%), namun menggunakan fixed-effect model. Seharusnya menerapkan random-effects model.",
                            actual=f"I^2 = {i2_val:.1f}%, Model Efek Tetap",
                            expected="Random-effects model jika I^2 > 50%",
                            recommendation="Gunakan random-effects model (DerSimonian-Laird atau REML) untuk mengakomodasi variansi substansial antar-studi komunikasi.",
                            evidence_query="fixed-effect",
                        ).to_dict()
                    )
            except ValueError:
                pass

        # 5. Publication Bias Assessment (Funnel Plot, Egger's Regression, Begg's Test)
        bias_kws = ["funnel plot", "bias publikasi", "egger", "begg", "trim and fill", "plot corong"]
        has_bias_test = any(kw in lower_text for kw in bias_kws)
        if not has_bias_test:
            findings.append(
                MetaAnalysisFinding(
                    rule_id="META_PUB_BIAS_001",
                    category="Meta-Analisis",
                    status="WARNING",
                    severity="WARNING",
                    message="Evaluasi bias publikasi (Funnel Plot atau Uji Regresi Egger) tidak ditemukan.",
                    actual="Evaluasi bias publikasi belum dilaporkan",
                    expected="Analisis asimetri Funnel Plot atau uji statistik Egger/Begg untuk menguji potensi bias publikasi",
                    recommendation="Sertakan visualisasi funnel plot atau hasil uji Egger guna membuktikan keabsahan temuan dari bias studi berukuran kecil.",
                    evidence_query="bias publikasi",
                ).to_dict()
            )
        else:
            findings.append(
                MetaAnalysisFinding(
                    rule_id="META_PUB_BIAS_001",
                    category="Meta-Analisis",
                    status="PASS",
                    severity="INFO",
                    message="Evaluasi bias publikasi (Funnel Plot / Uji Egger) terverifikasi.",
                    actual="Evaluasi bias publikasi dilaporkan",
                    expected="Analisis bias publikasi",
                    recommendation="Pertahankan interpretasi simetri funnel plot.",
                    evidence_query="bias publikasi",
                ).to_dict()
            )

        # 6. Critical Appraisal / Quality Assessment Tool
        has_tool = any(tool in lower_text for tool in self.QUALITY_TOOLS)
        if not has_tool:
            findings.append(
                MetaAnalysisFinding(
                    rule_id="META_QUALITY_APPRAISAL_001",
                    category="Meta-Analisis",
                    status="WARNING",
                    severity="WARNING",
                    message="Instrumen penilaian kualitas metodologis studi primer (Risk of Bias / Critical Appraisal) belum disebutkan.",
                    actual="Instrumen telaah kritis tidak terdeteksi",
                    expected="Penggunaan instrumen telaah kritis standar (misal: JBI, MMAT, CASP, RoB 2, atau NOS)",
                    recommendation="Gunakan instrumen baku telaah kritis untuk mengevaluasi validitas internal artikel primer sebelum sintesis.",
                    evidence_query="kualitas studi",
                ).to_dict()
            )

        return findings
