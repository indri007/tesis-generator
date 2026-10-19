"""Unit tests for Oxford-standard MIKOM 2026 Auditors:
1. ResearchMethodsAuditor (Research Design & Biostatistics)
2. MetaAnalysisAuditor (PRISMA 2020 & Effect Size Synthesis)
3. AcademicWritingAuditor (KBBI Diksi, Impersonal Viewpoint, & Scholarly Paragraphs)
"""

from __future__ import annotations

import pytest

from engines.academic_writing_auditor import AcademicWritingAuditor
from engines.meta_analysis_auditor import MetaAnalysisAuditor
from engines.research_methods_auditor import ResearchMethodsAuditor
from models.document_model import ParsedDocument, ParsedParagraph


def make_doc_from_text(text: str) -> ParsedDocument:
    doc = ParsedDocument(filename="tesis_mikom_test.docx", file_type="docx")
    doc.paragraphs = [ParsedParagraph(text=line) for line in text.splitlines()]
    return doc


# ══════════════════════════════════════════════════════════════════
# 1. ResearchMethodsAuditor Tests
# ══════════════════════════════════════════════════════════════════

def test_research_methods_quantitative_compliant():
    text = """
    BAB III METODOLOGI PENELITIAN
    3.1 Pendekatan Penelitian
    Penelitian ini menggunakan pendekatan kuantitatif dengan metode survei eksplanatif.
    
    3.5 Populasi, Sampel dan Teknik Penarikan Sampel
    Populasi dalam penelitian ini berjumlah 1.500 konsumen. Penentuan ukuran sampel dihitung
    menggunakan rumus Slovin dengan margin of error 5%, sehingga diperoleh sampel sebanyak 316 responden.
    Teknik sampling menggunakan probability sampling dengan proportionate stratified random sampling.
    
    3.6 Uji Validitas dan Reliabilitas Instrumen
    Uji validitas instrumen menggunakan korelasi Pearson Product Moment dengan kriteria r hitung > r tabel.
    Seluruh butir kuesioner terbukti valid. Uji reliabilitas menunjukkan koefisien Cronbach's Alpha sebesar 0.884,
    sehingga instrumen dikategorikan sangat reliabel (di atas batas ambang 0.70).
    
    BAB IV HASIL DAN PEMBAHASAN
    4.2 Analisis Data dan Uji Asumsi Klasik
    Uji normalitas menggunakan uji Kolmogorov-Smirnov menghasilkan nilai signifikansi 0.200 (p > 0.05).
    Uji multikolinearitas menunjukkan nilai VIF sebesar 1.84 (VIF < 10) dan tolerance 0.543.
    Uji heteroskedastisitas dengan uji Glejser menunjukkan nilai p > 0.05.
    Uji hipotesis regresi linear berganda menghasilkan nilai F hitung 45.2 (p-value 0.001 < 0.05)
    dengan koefisien determinasi R-Square sebesar 0.624.
    """
    doc = make_doc_from_text(text)
    auditor = ResearchMethodsAuditor(doc)
    findings = auditor.audit()

    rule_ids = {f["rule_id"] for f in findings}
    assert "METHOD_DESIGN_IDENTIFIED_001" in rule_ids
    assert "METHOD_SAMPLE_SIZE_001" in rule_ids
    assert "METHOD_CRONBACH_ALPHA_001" in rule_ids

    # Check that sample size and alpha passed
    cronbach_f = next(f for f in findings if f["rule_id"] == "METHOD_CRONBACH_ALPHA_001")
    assert cronbach_f["status"] == "PASS"

    sample_f = next(f for f in findings if f["rule_id"] == "METHOD_SAMPLE_SIZE_001")
    assert sample_f["status"] == "PASS"


def test_research_methods_unspecified_design_and_low_sample():
    text = """
    BAB III METODOLOGI
    Penelitian dilaksanakan di Surabaya pada bulan Januari 2026.
    Peneliti mendatangi 15 orang karyawan di lokasi kantor untuk pengumpulan data awal.
    """
    doc = make_doc_from_text(text)
    auditor = ResearchMethodsAuditor(doc)
    findings = auditor.audit()

    rule_ids = {f["rule_id"] for f in findings}
    assert "METHOD_DESIGN_UNDEFINED_001" in rule_ids


def test_research_methods_low_reliability_and_high_vif():
    text = """
    BAB III METODOLOGI PENELITIAN
    Pendekatan penelitian ini adalah kuantitatif dengan survei 120 responden.
    Hasil uji reliabilitas instrumen menghasilkan Cronbach's Alpha sebesar 0.52.
    
    BAB IV HASIL DAN PEMBAHASAN
    Uji multikolinearitas menemukan nilai VIF sebesar 14.5 pada variabel X1.
    """
    doc = make_doc_from_text(text)
    auditor = ResearchMethodsAuditor(doc)
    findings = auditor.audit()

    # Low Cronbach's alpha
    cronbach_f = next((f for f in findings if f["rule_id"] == "METHOD_CRONBACH_ALPHA_001"), None)
    assert cronbach_f is not None
    assert cronbach_f["status"] == "ERROR"

    # Multicollinearity violation
    vif_f = next((f for f in findings if f["rule_id"] == "METHOD_MULTICOLLINEARITY_001"), None)
    assert vif_f is not None
    assert vif_f["status"] == "ERROR"


def test_research_methods_qualitative_triangulation():
    text = """
    BAB III METODOLOGI PENELITIAN
    3.1 Pendekatan Penelitian
    Penelitian ini menggunakan pendekatan kualitatif dengan paradigma konstruktivisme dan studi kasus.
    
    3.4 Informan dan Teknik Pengumpulan Data
    Pemilihan informan dilakukan secara purposive sampling.
    Keabsahan data diuji melalui triangulasi sumber dan triangulasi teknik.
    Analisis data menggunakan model interaktif Miles dan Huberman.
    """
    doc = make_doc_from_text(text)
    auditor = ResearchMethodsAuditor(doc)
    findings = auditor.audit()

    rule_ids = {f["rule_id"] for f in findings}
    assert "METHOD_DESIGN_IDENTIFIED_001" in rule_ids
    assert "METHOD_QUAL_TRIANGULATION_001" in rule_ids

    tri_f = next(f for f in findings if f["rule_id"] == "METHOD_QUAL_TRIANGULATION_001")
    assert tri_f["status"] == "PASS"


# ══════════════════════════════════════════════════════════════════
# 2. MetaAnalysisAuditor Tests
# ══════════════════════════════════════════════════════════════════

def test_meta_analysis_fully_compliant():
    text = """
    BAB I PENDAHULUAN
    Penelitian ini merupakan studi meta-analisis dan systematic literature review mengenai efektivitas komunikasi pemasaran digital.
    
    BAB III METODOLOGI META-ANALISIS
    Protokol penyaringan artikel mengikuti pedoman PRISMA 2020 melalui empat tahap: identifikasi, penyaringan, kelayakan, dan inklusi final.
    Pencarian literatur komprehensif dilakukan pada database Scopus, Web of Science, dan SINTA Kemdikbudristek.
    Kualitas metodologis setiap studi dinilai menggunakan instrumen JBI Critical Appraisal Tools.
    
    BAB IV HASIL DAN SINTESIS EFEK
    Sintesis ukuran efek dihitung dengan Hedges' g dan odds ratio.
    Uji heterogenitas menghasilkan nilai Cochran's Q dengan I-squared sebesar 38.5% (I^2 < 50%),
    sehingga model sintesis yang digunakan adalah fixed-effect model.
    Pemeriksaan bias publikasi divisualisasikan melalui funnel plot yang simetris dan
    dikonfirmasi dengan uji regresi linear Egger (p > 0.05).
    """
    doc = make_doc_from_text(text)
    auditor = MetaAnalysisAuditor(doc)
    assert auditor.is_meta_analysis is True

    findings = auditor.audit()
    rule_ids = {f["rule_id"] for f in findings}

    assert "META_PRISMA_FLOW_001" in rule_ids
    assert "META_DATABASE_DIVERSITY_001" in rule_ids
    assert "META_EFFECT_SIZE_001" in rule_ids
    assert "META_HETEROGENEITY_001" in rule_ids
    assert "META_PUB_BIAS_001" in rule_ids

    # All should be PASS in a compliant document
    for f in findings:
        assert f["status"] == "PASS"


def test_meta_analysis_non_meta_returns_empty():
    text = """
    BAB I PENDAHULUAN
    Penelitian kuantitatif pengaruh citra merek terhadap keputusan pembelian produk fashion di Surabaya.
    """
    doc = make_doc_from_text(text)
    auditor = MetaAnalysisAuditor(doc)
    assert auditor.is_meta_analysis is False
    findings = auditor.audit()
    assert len(findings) == 0


def test_meta_analysis_high_heterogeneity_wrong_model():
    text = """
    Kajian ini merupakan meta-analisis publikasi ilmiah.
    Pencarian hanya dilakukan pada Google Scholar.
    Nilai heterogenitas I^2 sebesar 78.4% (tinggi), namun peneliti menerapkan fixed-effect model.
    """
    doc = make_doc_from_text(text)
    auditor = MetaAnalysisAuditor(doc)
    findings = auditor.audit()

    db_f = next((f for f in findings if f["rule_id"] == "META_DATABASE_DIVERSITY_001"), None)
    assert db_f is not None
    assert db_f["status"] == "WARNING"

    het_f = next((f for f in findings if f["rule_id"] == "META_HETEROGENEITY_MODEL_001"), None)
    assert het_f is not None
    assert het_f["status"] == "ERROR"


# ══════════════════════════════════════════════════════════════════
# 3. AcademicWritingAuditor Tests
# ══════════════════════════════════════════════════════════════════

def test_academic_writing_informal_diksi_detected():
    text = """
    Penelitian ini nggak menggunakan metode kualitatif karena sangat susah.
    Dampaknya bikin engagement akun instagram tersebut naik banget.
    Gimana cara merubah pola komunikasi organisasi tersebut menjadi lebih efektif?
    Praktek komunikasi di era jaman modern membutuhkan analisa mendalam.
    """
    doc = make_doc_from_text(text)
    auditor = AcademicWritingAuditor(doc)
    findings = auditor.audit()

    informal_f = next((f for f in findings if f["rule_id"] == "WRITING_DICTION_NON_STANDARD_001"), None)
    assert informal_f is not None
    assert informal_f["status"] == "ERROR"
    # Check that replacements are recommended in the finding actual/message
    assert "nggak" in informal_f["actual"].lower() or "nggak" in informal_f["message"].lower()
    assert "banget" in informal_f["actual"].lower() or "banget" in informal_f["message"].lower()


def test_academic_writing_subjective_viewpoint_detected():
    text = """
    Dalam penelitian ini, saya berpendapat bahwa strategi komunikasi digital sangat krusial.
    Menurut hemat saya, kita semua tahu bahwa media sosial telah mendominasi ruang publik.
    Kami mengamati fenomena ini secara cermat.
    """
    doc = make_doc_from_text(text)
    auditor = AcademicWritingAuditor(doc)
    findings = auditor.audit()

    subj_f = next((f for f in findings if f["rule_id"] == "WRITING_FIRST_PERSON_SUBJECTIVE_001"), None)
    assert subj_f is not None
    assert subj_f["status"] == "WARNING"
    assert "objektif" in subj_f["recommendation"].lower()


def test_academic_writing_single_sentence_paragraph_detected():
    text = """
    Strategi komunikasi pemasaran digital di era disrupsi menuntut integrasi kanal omni yang terstruktur dan adaptif terhadap dinamika audiens.
    """
    doc = make_doc_from_text(text)
    auditor = AcademicWritingAuditor(doc)
    findings = auditor.audit()

    para_f = next((f for f in findings if f["rule_id"] == "WRITING_SINGLE_SENTENCE_PARAGRAPH_001"), None)
    assert para_f is not None
    assert para_f["status"] == "WARNING"


def test_academic_writing_compliant_scholarly_paragraph():
    text = """
    Perkembangan teknologi informasi telah mendorong transformasi signifikan dalam ekosistem komunikasi pemasaran digital kontemporer.
    Oleh karena itu, organisasi dituntut untuk merumuskan strategi komunikasi yang tidak hanya adaptif melainkan juga berbasis data empiris.
    Berdasarkan temuan terdahulu, adopsi kanal digital yang terintegrasi mampu meningkatkan keterikatan audiens secara substansial.
    Dengan kata lain, efektivitas pesan komunikasi sangat ditentukan oleh ketepatan pemilihan medium serta personalisasi konten yang disajikan.
    """
    doc = make_doc_from_text(text)
    auditor = AcademicWritingAuditor(doc)
    findings = auditor.audit()

    # Should have no ERROR findings
    error_findings = [f for f in findings if f["status"] == "ERROR"]
    assert len(error_findings) == 0

    # KBBI diksi should be PASS
    diksi_f = next((f for f in findings if f["rule_id"] == "WRITING_DICTION_NON_STANDARD_001"), None)
    assert diksi_f is not None
    assert diksi_f["status"] == "PASS"
