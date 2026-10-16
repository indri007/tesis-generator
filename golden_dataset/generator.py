"""Golden test dataset generator producing 10 standardized synthetic thesis documents."""

from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Pt

BASE_DIR = Path(__file__).resolve().parent
DOCS_DIR = BASE_DIR / "documents"
DOCS_DIR.mkdir(parents=True, exist_ok=True)


def create_base_thesis_text(
    chap1: str | None = None,
    chap2: str | None = None,
    chap3: str | None = None,
    chap4: str | None = None,
    chap5: str | None = None,
    include_bib: bool = True,
    bib_entries: list[str] | None = None,
    include_abstract: bool = True,
    sample_b3: int = 120,
    sample_b4: int = 120,
    var_x1_b2: str = "Kualitas Sistem",
    var_x1_b3: str = "Kualitas Sistem",
    p_val: float = 0.032,
    p_conclusion: str = "berpengaruh signifikan",
    formula_claim: float = 6.5,
    pad_to_40k: bool = True,
) -> str:
    """Builds synthetic thesis text body."""
    abstract_text = ""
    if include_abstract:
        abstract_body = (
            "Penelitian ini bertujuan untuk menganalisis efektivitas komunikasi pemasaran digital terhadap loyalitas audiens pada platform media sosial. "
            "Pendekatan yang diterapkan adalah metode kuantitatif eksplanatif dengan teknik survei terstruktur kepada responden terpilih di lingkungan akademik dan industri kreatif. "
            "Pengumpulan data primer dilakukan melalui instrumen kuesioner yang telah teruji validitas dan reliabilitasnya secara menyeluruh. "
            "Teknik analisis data menggunakan pemodelan persamaan struktural dan analisis regresi linier untuk menguji signifikansi hubungan antarvariabel pokok penelitian. "
            "Hasil penelitian membuktikan secara empiris bahwa seluruh hipotesis yang diajukan terbukti memiliki arah pengaruh positif dan signifikan terhadap konstruk terikat. "
            "Kualitas konten komunikasi dan frekuensi interaksi digital terbukti menjadi prediktor utama dalam memperkuat keterikatan psikologis audiens. "
            "Kesimpulan dari penelitian ini menegaskan pentingnya perumusan strategi integrasi pesan komunikasi dalam membangun citra merek yang berkelanjutan serta meningkatkan retensi pengguna aktif pada kanal komunikasi digital modern masa kini. "
            "Implikasi penelitian ini diharapkan dapat memberikan kontribusi konseptual bagi literatur ilmu komunikasi pemasaran digital dan panduan praktis bagi praktisi media komunikasi kontemporer."
        )
        abstract_text = (
            f"ABSTRAK\n{abstract_body}\n\n"
            "Kata Kunci: Komunikasi Digital, Kualitas Sistem, Loyalitas Audiens, Media Sosial\n\n"
            f"ABSTRACT\n{abstract_body}\n\n"
            "Keywords: Digital Communication, System Quality, Audience Loyalty, Social Media\n\n"
        )

    b1 = chap1 or (
        "BAB I PENDAHULUAN\n"
        "1.1 Latar Belakang Masalah\n"
        "Perkembangan teknologi komunikasi digital telah mengubah lanskap interaksi masyarakat secara menyeluruh. "
        "Komunikasi pemasaran digital memerlukan kejelasan pesan dan platform yang reliabel dalam menyampaikan informasi.\n"
        "1.2 Rumusan Masalah\n"
        "Bagaimana pengaruh kualitas sistem terhadap kepuasan pengguna?\n"
        "1.3 Tujuan Penelitian\n"
        "Untuk menguji pengaruh kualitas sistem terhadap kepuasan pengguna.\n"
        "1.4 Manfaat Penelitian\n"
        "Manfaat teoritis dan praktis bagi pengembangan ilmu komunikasi.\n"
    )

    b2 = chap2 or (
        "BAB II TINJAUAN PUSTAKA\n"
        "2.1 Penelitian Terdahulu\n"
        "Kajian terdahulu oleh Smith (2022) mengemukakan pentingnya infrastruktur digital dalam menunjang interaksi pengguna.\n"
        "2.2 Tinjauan Pustaka\n"
        f"Variabel penelitian terdiri dari X1 adalah {var_x1_b2}. Konstruk ini mencakup kemudahan, keandalan, dan stabilitas operasional sistem dalam menunjang transmisi pesan.\n"
        "2.3 Kerangka Berpikir\n"
        "Kerangka konseptual menghubungkan variabel bebas dengan variabel terikat secara terarah.\n"
        "2.4 Hipotesis\n"
        "H1: Terdapat pengaruh positif dan signifikan antara X1 terhadap Y.\n"
    )

    b3 = chap3 if chap3 is not None else (
        "BAB III METODE PENELITIAN\n"
        "3.1 Pendekatan Penelitian\n"
        "Penelitian ini menggunakan pendekatan kuantitatif eksplanatif.\n"
        "3.2 Definisi dan Operasionalisasi Variabel\n"
        f"Variabel X1 adalah {var_x1_b3}.\n"
        "3.3 Lokasi dan Waktu Penelitian\n"
        "Penelitian dilakukan di Surabaya selama enam bulan.\n"
        "3.4 Populasi dan Sampel\n"
        f"Jumlah sampel sebanyak {sample_b3} responden yang dipilih dengan metode purposive sampling.\n"
        "3.5 Teknik Analisis Data\n"
        "Analisis data menggunakan regresi linier sederhana dengan model:\n"
        "Y = 2,5 + 0,4X\n"
    )

    b4 = chap4 or (
        "BAB IV HASIL DAN PEMBAHASAN\n"
        "4.1 Gambaran Umum Subyek Penelitian\n"
        f"Data responden yang dianalisis sebanyak {sample_b4} responden.\n"
        "4.2 Penyajian dan Analisis Data\n"
        "Hasil estimasi persamaan regresi linier:\n"
        "Y = 2,5 + 0,4X\n"
        "X = 10\n"
        f"Y = {str(formula_claim).replace('.', ',')}\n"
        f"Hasil uji hipotesis menunjukkan nilai p = {str(p_val).replace('.', ',')} terhadap alpha 0,05. "
        f"Oleh karena itu, hipotesis H1 dinyatakan {p_conclusion}.\n"
        "4.3 Pembahasan\n"
        "Temuan ini mendukung kajian terdahulu dan teori yang digunakan dalam memperkuat relasi komunikatif.\n"
    )

    b5 = chap5 or (
        "BAB V SIMPULAN DAN SARAN\n"
        "5.1 Simpulan\n"
        "Penelitian ini menyimpulkan bahwa terdapat pengaruh signifikan antara variabel yang diteliti.\n"
        "5.2 Saran\n"
        "Disarankan bagi peneliti selanjutnya untuk memperluas cakupan obyek penelitian.\n"
    )

    # Optional word padding to reach 40.500 words for standard compliant tests
    if pad_to_40k:
        dummy_par = (
            "Analisis mendalam mengenai dinamika komunikasi menunjukkan adanya kesinambungan yang konsisten antara ekspektasi pesan dengan respon kognitif audiens sasaran. "
            "Secara metodologis setiap indikator konstruk diuji melalui parameter reliabilitas komposit yang memenuhi batas keterandalan statistik secara optimal. "
        ) * 15
        # Repeat paragraphs to distribute ~41.000 words across chapters
        b1 += "\n" + (dummy_par + "\n\n") * 15
        b2 += "\n" + (dummy_par + "\n\n") * 25
        if b3:
            b3 += "\n" + (dummy_par + "\n\n") * 15
        b4 += "\n" + (dummy_par + "\n\n") * 35
        b5 += "\n" + (dummy_par + "\n\n") * 10

    bib_text = ""
    if include_bib:
        entries = bib_entries or [
            "Smith, J. (2022). Digital Communication and Media Technologies. Academic Press.",
            "Rahmawati, A. (2023). Strategic Marketing in Communication Age. Media Nusantara."
        ]
        bib_text = "DAFTAR PUSTAKA\n" + "\n".join(entries) + "\n"

    return f"{abstract_text}\n{b1}\n{b2}\n{b3}\n{b4}\n{b5}\n{bib_text}"


def save_test_docx(
    text: str,
    path: Path,
    top_cm: float = 4.0,
    left_cm: float = 4.0,
    bottom_cm: float = 3.0,
    right_cm: float = 3.0,
    font_name: str = "Times New Roman",
    font_size: int = 12
) -> None:
    doc = Document()
    s = doc.sections[0]
    s.top_margin = Cm(top_cm)
    s.left_margin = Cm(left_cm)
    s.bottom_margin = Cm(bottom_cm)
    s.right_margin = Cm(right_cm)

    for paragraph_text in text.split("\n\n"):
        p_clean = paragraph_text.strip()
        if not p_clean:
            continue
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.line_spacing = 2.0
        run = p.add_run(p_clean)
        run.font.name = font_name
        run.font.size = Pt(font_size)

    doc.save(str(path))


def generate_golden_dataset() -> dict[str, dict]:
    """Generates the 10 golden test cases."""
    dataset = {}

    # TEST-001: Tesis Normal (Semua valid)
    t1_text = create_base_thesis_text(pad_to_40k=True)
    t1_path = DOCS_DIR / "TEST-001_normal.docx"
    save_test_docx(t1_text, t1_path)
    dataset["TEST-001"] = {
        "file": str(t1_path),
        "description": "Tesis normal sesuai standar MIKOM 2026",
        "expected_errors": []
    }

    # TEST-002: Margin Salah (Left margin 3.0 cm bukannya 4.0 cm)
    t2_path = DOCS_DIR / "TEST-002_margin_salah.docx"
    save_test_docx(t1_text, t2_path, left_cm=3.0)
    dataset["TEST-002"] = {
        "file": str(t2_path),
        "description": "Margin kiri salah (3.0 cm)",
        "expected_errors": ["FORMAT_MARGIN_LEFT_001"]
    }

    # TEST-003: Font Salah (Arial bukannya Times New Roman)
    t3_path = DOCS_DIR / "TEST-003_font_salah.docx"
    save_test_docx(t1_text, t3_path, font_name="Arial")
    dataset["TEST-003"] = {
        "file": str(t3_path),
        "description": "Font salah (Arial)",
        "expected_errors": ["FORMAT_FONT_FAMILY_001"]
    }

    # TEST-004: BAB III Hilang
    t4_text = create_base_thesis_text(chap3="", pad_to_40k=True)
    t4_path = DOCS_DIR / "TEST-004_bab3_hilang.docx"
    save_test_docx(t4_text, t4_path)
    dataset["TEST-004"] = {
        "file": str(t4_path),
        "description": "BAB III hilang",
        "expected_errors": ["STRUCT_CHAP_BAB3_001"]
    }

    # TEST-005: Citation Tanpa Reference
    t5_text = create_base_thesis_text(
        bib_entries=["Rahmawati, A. (2023). Strategic Marketing in Communication Age. Media Nusantara."],
        pad_to_40k=True
    )
    t5_path = DOCS_DIR / "TEST-005_citation_missing_bib.docx"
    save_test_docx(t5_text, t5_path)
    dataset["TEST-005"] = {
        "file": str(t5_path),
        "description": "Sitasi Smith (2022) tidak ada di Daftar Pustaka",
        "expected_errors": ["CITATION_ORPHAN_001"]
    }

    # TEST-006: X1 Berubah Definisi (Bab II: Kualitas Sistem, Bab III: Kualitas Informasi)
    t6_text = create_base_thesis_text(
        var_x1_b2="Kualitas Sistem",
        var_x1_b3="Kualitas Informasi",
        pad_to_40k=True
    )
    t6_path = DOCS_DIR / "TEST-006_variable_mutation.docx"
    save_test_docx(t6_text, t6_path)
    dataset["TEST-006"] = {
        "file": str(t6_path),
        "description": "Definisi variabel X1 berubah antara Bab II dan Bab III",
        "expected_errors": ["VARIABLE_CONSISTENCY_001"]
    }

    # TEST-007: Rumus Salah Hitung (Y = 2,5 + 0,4X pada X=10 menghasilkan 7,5 bukannya 6,5)
    t7_text = create_base_thesis_text(formula_claim=7.5, pad_to_40k=True)
    t7_path = DOCS_DIR / "TEST-007_formula_error.docx"
    save_test_docx(t7_text, t7_path)
    dataset["TEST-007"] = {
        "file": str(t7_path),
        "description": "Kesalahan hitung aritmetika rumus (Y diklaim 7,5 padahal 6,5)",
        "expected_errors": ["FORMULA_RECALCULATION_001"]
    }

    # TEST-008: p-value Bertentangan dengan Kesimpulan (p=0.032 tetapi dinyatakan tidak signifikan)
    t8_text = create_base_thesis_text(p_val=0.032, p_conclusion="tidak signifikan", pad_to_40k=True)
    t8_path = DOCS_DIR / "TEST-008_stat_contradiction.docx"
    save_test_docx(t8_text, t8_path)
    dataset["TEST-008"] = {
        "file": str(t8_path),
        "description": "Kesimpulan statistik kontradiktif dengan p-value (p=0,032 dinyatakan tidak signifikan)",
        "expected_errors": ["STAT_DECISION_CONSISTENCY_001"]
    }

    # TEST-009: Jumlah Responden Berbeda (Bab III: 120, Bab IV: 118)
    t9_text = create_base_thesis_text(sample_b3=120, sample_b4=118, pad_to_40k=True)
    t9_path = DOCS_DIR / "TEST-009_sample_mismatch.docx"
    save_test_docx(t9_text, t9_path)
    dataset["TEST-009"] = {
        "file": str(t9_path),
        "description": "Perbedaan jumlah responden antara Bab III (120) dan Bab IV (118)",
        "expected_errors": ["STAT_SAMPLE_CONSISTENCY_001"]
    }

    # TEST-010: Jurnal Berbeda dengan Tesis (Tesis sampel 120, Jurnal sampel 100)
    t10_thesis_text = create_base_thesis_text(sample_b3=120, sample_b4=120, pad_to_40k=True)
    t10_journal_text = (
        "ARTIKEL JURNAL ILMIAH\n"
        "Pengaruh Komunikasi Digital Terhadap Loyalitas Pengguna\n\n"
        "ABSTRAK\n"
        "Penelitian ini menguji model komunikasi dengan jumlah sampel sebanyak 100 responden terpilih.\n"
        "Metode: Survei dengan sampel sebanyak 100 responden.\n"
    )
    t10_thesis_path = DOCS_DIR / "TEST-010_thesis.docx"
    t10_journal_path = DOCS_DIR / "TEST-010_journal.docx"

    save_test_docx(t10_thesis_text, t10_thesis_path)
    save_test_docx(t10_journal_text, t10_journal_path)

    dataset["TEST-010"] = {
        "file": str(t10_thesis_path),
        "journal_file": str(t10_journal_path),
        "description": "Perbedaan sampel antara publikasi jurnal (100) dan tesis (120)",
        "expected_errors": ["JOURNAL_ALIGNMENT_SAMPLE_001"]
    }

    return dataset
