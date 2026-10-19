"""Unit tests for Manuscript Quality Gate."""

from __future__ import annotations

from core.evaluation.manuscript_quality_gate import (
    ManuscriptQualityGate,
    QualityGateDecision,
    QualityGateReport,
)


def test_complete_thesis_passes_quality_gate():
    complete_thesis = (
        "JUDUL: ANALISIS KOMUNIKASI PUBLIK\n\n"
        "ABSTRAK\nPenelitian ini menguji efektivitas komunikasi publik...\n\n"
        "ABSTRACT\nThis research examines the effectiveness of public communication...\n\n"
        "BAB I PENDAHULUAN\nLatar belakang penelitian mencakup dinamika komunikasi...\n\n"
        "BAB II TINJAUAN PUSTAKA\nKajian pustaka berlandaskan teori agenda setting...\n\n"
        "BAB III METODE PENELITIAN\nMetode penelitian menggunakan pendekatan kuantitatif...\n\n"
        "BAB IV HASIL DAN PEMBAHASAN\nHasil survei membuktikan hipotesis pertama...\n\n"
        "BAB V PENUTUP\nKesimpulan penelitian menyimpulkan bahwa...\n\n"
        "DAFTAR PUSTAKA\nHabermas, J. (1984). The Theory of Communicative Action.\n"
    )

    report = ManuscriptQualityGate.evaluate(complete_thesis)

    assert isinstance(report, QualityGateReport)
    assert report.decision in (QualityGateDecision.PASS, QualityGateDecision.PASS_WITH_WARNINGS)
    assert report.score >= 85
    assert report.can_export is True
    assert len(report.missing_chapters) == 0


def test_missing_mandatory_chapters_fails_or_warns():
    incomplete_thesis = (
        "JUDUL: ANALISIS KOMUNIKASI PUBLIK\n\n"
        "BAB I PENDAHULUAN\nLatar belakang penelitian...\n\n"
        "BAB II TINJAUAN PUSTAKA\nKajian teori...\n"
        # Missing Bab 3, 4, 5, and Daftar Pustaka
    )

    report = ManuscriptQualityGate.evaluate(incomplete_thesis)

    assert report.decision == QualityGateDecision.FAIL
    assert report.can_export is False
    assert any("Bab III" in ch for ch in report.missing_chapters)
    assert any("Bab IV" in ch for ch in report.missing_chapters)


def test_draft_placeholders_detected():
    draft_thesis = (
        "BAB I PENDAHULUAN\n"
        "TODO: lengkapi latar belakang terkait fenomena Pilkada.\n"
        "Menurut data terbaru [insert citation here], tren terus meningkat.\n"
        "Teks berikut adalah dummy: lorem ipsum dolor sit amet.\n\n"
        "BAB II TINJAUAN PUSTAKA\nTBD teori yang akan dipakai.\n\n"
        "BAB III METODE PENELITIAN\nSampel penelitian berjumlah XXX responden.\n\n"
        "BAB IV HASIL DAN PEMBAHASAN\nHasil analisis menunjukkan efektivitas sebesar XX%.\n\n"
        "BAB V PENUTUP\nKesimpulan akhir.\n\n"
        "DAFTAR PUSTAKA\nSusanto, B. (2020). Jurnal Komunikasi.\n"
    )

    report = ManuscriptQualityGate.evaluate(draft_thesis)

    assert len(report.placeholders_found) >= 3
    placeholder_texts = [p.raw for p in report.placeholders_found]
    assert any("TODO" in p for p in placeholder_texts)
    assert any("insert citation" in p.lower() for p in placeholder_texts)
    assert any("lorem ipsum" in p.lower() for p in placeholder_texts)


def test_table_figure_caption_integrity():
    text_with_orphaned_table_ref = (
        "BAB IV HASIL DAN PEMBAHASAN\n"
        "Sebagaimana ditunjukkan pada Tabel 4.1 berikut, distribusi frekuensi responden merata. "
        "Namun tidak ada keterangan judul tabel resmi yang dicantumkan."
    )

    report = ManuscriptQualityGate.evaluate(text_with_orphaned_table_ref)
    assert len(report.unpaired_captions) >= 1
    assert any("4.1" in c for c in report.unpaired_captions)
