"""Unit tests for Academic Similarity, Plagiarism & Duplication Clones."""

import pytest
from core.clones.similarity_plagiarism import (
    CopyleaksClone,
    GrammarlyClone,
    OuriginalClone,
    TurnitinClone,
    iThenticateClone,
)
from core.clones.duplication_detector import (
    DataComPyClone,
    DedupeClone,
    JscpdClone,
    PandasDuplicationClone,
    SonarQubeClone,
)


def test_turnitin_clone_similarity_and_color_bands():
    turnitin = TurnitinClone(n_gram=4)
    manuscript = """
    Kecerdasan buatan dalam jurnalisme meningkatkan efisiensi produksi berita harian di redaksi.
    "Ini adalah kutipan langsung yang harus dikecualikan."
    DAFTAR PUSTAKA
    Santoso, B. (2023). AI Journalism.
    """
    corpus = [
        {
            "source_id": "SRC-01",
            "title": "Jurnalisme AI 2023",
            "content": "Kecerdasan buatan dalam jurnalisme meningkatkan efisiensi produksi berita harian di redaksi modern.",
        }
    ]

    report = turnitin.check_similarity(manuscript, corpus)
    assert report.total_words > 0
    assert report.overall_similarity_percentage > 0.0
    assert report.color_band in ("GREEN", "YELLOW", "ORANGE", "RED")
    assert len(report.matches) >= 1
    assert report.matches[0].source_id == "SRC-01"


def test_ithenticate_clone_manuscript_check():
    ith = iThenticateClone()
    manuscript = "Data dikumpulkan melalui kuesioner dan kecerdasan buatan dalam jurnalisme meningkatkan efisiensi redaksi."
    corpus = [
        {
            "source_id": "JRN-01",
            "title": "Journal Paper",
            "content": "kecerdasan buatan dalam jurnalisme meningkatkan efisiensi redaksi secara terukur.",
        }
    ]
    res = ith.verify_manuscript(manuscript, corpus)
    assert "journal_similarity_score" in res
    assert res["boilerplate_filtered"] is True
    assert res["target_standard"] == "Scopus / Elsevier / MIKOM 2026"


def test_copyleaks_clone_burstiness_and_ai_detection():
    cpl = CopyleaksClone()
    human_text = "Penelitian ini menguji algoritma baru. Hasilnya mengejutkan! Kita melihat lompatan efisiensi yang luar biasa pada jurnalis."
    res = cpl.detect_ai_and_paraphrase(human_text)
    assert res["sentence_count"] == 3
    assert res["burstiness_index"] > 0
    assert res["classification"] in ("HUMAN_ORIGINAL", "MIXED", "AI_GENERATED")


def test_ouriginal_clone_document_comparison():
    ouri = OuriginalClone()
    doc_a = "Sistem otomatisasi penulisan tesis magister ilmu komunikasi."
    doc_b = "Sistem otomatisasi naskah tesis magister ilmu komunikasi modern."
    res = ouri.compare_documents(doc_a, doc_b)
    assert res["overlap_ratio"] > 0.5
    assert res["shared_word_count"] >= 4


def test_grammarly_clone_academic_tone():
    gram = GrammarlyClone()
    clean_academic = "Penelitian ini dilakukan untuk menguji pengaruh implementasi teknologi digital."
    res_clean = gram.audit_academic_writing(clean_academic)
    assert res_clean["academic_formality_score"] >= 85
    assert res_clean["meets_mikom_standard"] is True

    informal_text = "Penelitian ini hasilnya keren banget dan kayak nggak ada masalah sama sekali."
    res_inf = gram.audit_academic_writing(informal_text)
    assert len(res_inf["informal_words_detected"]) >= 2
    assert res_inf["meets_mikom_standard"] is False


def test_jscpd_clone_duplicate_code_blocks():
    jscpd = JscpdClone(min_tokens=10, min_lines=3)
    files = {
        "module_a.py": """
def process_data(data):
    clean = [x.strip() for x in data]
    validated = [x for x in clean if x]
    return validated
""",
        "module_b.py": """
def helper_process(items):
    clean = [x.strip() for x in data]
    validated = [x for x in clean if x]
    return validated
""",
    }
    dups = jscpd.find_code_duplicates(files)
    assert len(dups) >= 1
    assert dups[0].lines_count >= 3


def test_sonarqube_clone_cognitive_complexity():
    sonar = SonarQubeClone()
    code = """
def complex_function(a, b, c):
    if a > 0:
        for x in b:
            if x in c:
                while a < 10:
                    a += 1
    return a
"""
    res = sonar.audit_code_quality(code)
    assert res["cognitive_complexity"] > 0
    assert res["maintainability_rating"] in ("A", "B", "C")


def test_datacompy_clone_dataset_comparison():
    dc = DataComPyClone()
    df1 = [{"id": 1, "name": "Alice", "score": 90}, {"id": 2, "name": "Bob", "score": 85}]
    df2 = [{"id": 1, "name": "Alice", "score": 90}, {"id": 2, "name": "Bob", "score": 88}]  # score drift

    res = dc.compare(df1, df2, join_columns=["id"])
    assert res["datasets_match"] is False
    assert res["value_mismatches"] == 1
    assert res["intersect_rows"] == 2


def test_dedupe_clone_fuzzy_clustering():
    dedupe = DedupeClone()
    records = [
        {"id": 1, "title": "Effect of Artificial Intelligence on Journalistic Writing"},
        {"id": 2, "title": "Effect of Artificial Intelligence on Journalistic Writing: A Study"},
        {"id": 3, "title": "Strategic Communication in Modern Organizations"},
    ]
    clusters = dedupe.deduplicate(records, key_field="title", threshold=0.8)
    assert len(clusters) == 2
    # First cluster should have merged record 1 and 2
    assert clusters[0]["duplicate_count"] == 1


def test_pandas_duplication_clone():
    records = [
        {"doc_id": "D1", "author": "Santoso", "year": 2023},
        {"doc_id": "D2", "author": "Santoso", "year": 2023},
        {"doc_id": "D3", "author": "Smith", "year": 2022},
    ]
    annotated = PandasDuplicationClone.identify_duplicates(records, subset=["author", "year"])
    assert annotated[0]["is_duplicate"] is False
    assert annotated[1]["is_duplicate"] is True
    assert annotated[2]["is_duplicate"] is False
