"""Unit Tests for Consensus AI Evidence Synthesizer and VOSviewer Integration.

Tests:
- Scientific claim polarity evaluation (Yes / No / Possibly / Inconclusive)
- Quantitative Consensus Meter calculation (% Yes, % No, % Possibly)
- Study design and sample size extraction
- Rigor stars and weighted consensus score
- Academic synthesis narrative generation with in-text APA citations
- Standard Consensus CSV export
- VOSviewer build_from_canonical_records integration
"""

from __future__ import annotations

import csv

from core.clones.consensus_ai import (
    ConsensusAIClone,
    ConsensusVerdict,
    StudyDesign,
)
from core.clones.vosviewer_bibliometrics import VOSviewerClone
from core.sources.data_models import CanonicalPaperRecord, DocumentType


class TestConsensusAIClone:
    def test_evaluate_claim_positive(self):
        engine = ConsensusAIClone()
        query = "Does social network analysis improve communication crisis detection?"
        text = (
            "This study investigates social network analysis in crisis communication. "
            "Our empirical findings demonstrate that SNA algorithms significantly improve "
            "early anomaly detection with 92% precision."
        )
        verdict, conf, quote, takeaway = engine.evaluate_claim(query, text)
        assert verdict == ConsensusVerdict.YES
        assert conf > 0.6
        assert "significantly improve" in quote.lower()
        assert "positif" in takeaway.lower()

    def test_evaluate_claim_negative(self):
        engine = ConsensusAIClone()
        query = "Does social media engagement directly increase policy compliance?"
        text = (
            "We examined whether high engagement on government social media leads to policy compliance. "
            "Statistical regression shows no significant difference between high and low engagement groups. "
            "The hypothesized correlation fails to materialize."
        )
        verdict, conf, quote, takeaway = engine.evaluate_claim(query, text)
        assert verdict == ConsensusVerdict.NO
        assert "no significant difference" in quote.lower() or "fails to" in quote.lower()

    def test_evaluate_claim_nuanced(self):
        engine = ConsensusAIClone()
        query = "Is automated messaging effective for public health campaigns?"
        text = (
            "We analyzed automated messaging across regional demographics. "
            "Results show mixed results: effectiveness depends on the digital literacy of the target population."
        )
        verdict, conf, quote, takeaway = engine.evaluate_claim(query, text)
        assert verdict == ConsensusVerdict.POSSIBLY
        assert "mixed results" in quote.lower() or "depends on" in quote.lower()

    def test_study_design_and_sample_extraction(self):
        engine = ConsensusAIClone()
        text_slr = "A systematic review and PRISMA meta-analysis of digital media communication."
        assert engine.extract_study_design(text_slr) == StudyDesign.SYSTEMATIC_REVIEW

        text_sna = "This empirical study employs social network analysis and IndoBERT across n = 25000 tweets."
        assert engine.extract_study_design(text_sna) == StudyDesign.EMPIRICAL_QUANTITATIVE
        assert engine.extract_sample_size(text_sna) == 25000

    def test_full_corpus_synthesis_and_meter(self):
        engine = ConsensusAIClone()
        query = "Apakah penggunaan IndoBERT meningkatkan akurasi analisis sentimen kebijakan MBG?"

        corpus = [
            {
                "title": "Analisis Sentimen Kebijakan MBG Menggunakan IndoBERT",
                "authors": ["Utomo, Indri", "Santoso, Budi"],
                "year": 2024,
                "journal": "Jurnal Komunikasi Indonesia",
                "doi": "10.1016/j.jki.2024.101",
                "abstract": "Penelitian ini menggunakan IndoBERT dengan sampel n = 15000 cuitan. Hasil pengujian membuktikan bahwa IndoBERT berhasil meningkatkan akurasi klasifikasi hingga 91.4% dibanding baseline.",
                "cited_by_count": 35,
            },
            {
                "title": "Evaluasi Komparatif Model NLP untuk Teks Informal Bahasa Indonesia",
                "authors": ["Pratama, Agus"],
                "year": 2023,
                "journal": "Telematics and Informatics",
                "doi": "10.1016/j.tele.2023.202",
                "abstract": "Studi eksperimen menunjukkan IndoBERT terbukti efektif dan memperkuat deteksi polaritas opini publik secara signifikan.",
                "cited_by_count": 48,
            },
            {
                "title": "Tantangan Deteksi Sarkasme pada Percakapan Telegram",
                "authors": ["Wijaya, Hendra"],
                "year": 2024,
                "journal": "Asian Journal of Communication",
                "doi": "10.1080/ajc.2024.303",
                "abstract": "Pengujian model pada teks sarkastik menghasilkan hasil campuran: akurasi tinggi tercapai pada teks formal, namun efektivitas tergantung pada keberadaan emoji kontekstual.",
                "cited_by_count": 12,
            },
            {
                "title": "Kelemahan Model Berbasis Kata Kunci Sederhana pada Opini Publik",
                "authors": ["Kusuma, Dian"],
                "year": 2022,
                "journal": "Media dan Masyarakat",
                "doi": "10.1000/mdm.2022.404",
                "abstract": "Metode lexicon konvensional gagal menangkap ambivalensi sentimen dan tidak berpengaruh nyata terhadap ketepatan prediksi.",
                "cited_by_count": 8,
            },
        ]

        result = engine.analyze_corpus(query, corpus)

        assert result.meter.total_studies == 4
        assert result.meter.yes_count == 2
        assert result.meter.possibly_count == 1
        assert result.meter.no_count == 1
        assert result.meter.yes_percentage == 50.0
        assert result.meter.weighted_consensus_score > 0.0

        # Verify synthesis narrative
        assert "Utomo et al., 2024" in result.synthesis_narrative
        assert "konsensus" in result.synthesis_narrative.lower()

        # Verify Markdown export
        md = result.to_markdown()
        assert "# Consensus Scientific Synthesis" in md
        assert "Consensus Meter" in md
        assert "Matriks Bukti Ilmiah" in md

    def test_export_consensus_csv(self, tmp_path):
        engine = ConsensusAIClone()
        query = "Does AI improve literature synthesis?"
        corpus = [
            {
                "title": "Automated Literature Synthesis using AI",
                "authors": ["Smith, John"],
                "year": 2024,
                "journal": "Scientometrics",
                "doi": "10.1007/s11192-024-001",
                "abstract": "AI methods significantly improve research synthesis speed and precision.",
                "cited_by_count": 25,
            }
        ]
        result = engine.analyze_corpus(query, corpus)
        out_csv = tmp_path / "consensus_export.csv"
        engine.export_consensus_csv(result, out_csv)

        assert out_csv.exists()
        with open(out_csv, encoding="utf-8") as f:
            reader = list(csv.reader(f))
            assert len(reader) == 2  # Header + 1 row
            assert reader[0][0] == "Query"
            assert reader[1][6] == "Yes"  # Consensus meter column


class TestVOSviewerCanonicalIntegration:
    def test_build_from_canonical_records(self):
        r1 = CanonicalPaperRecord(
            record_id="rec_1",
            title="Social network analysis and communication bots on Telegram",
            abstract="We investigate communication dynamics, misinformation, and network centralities in Telegram groups.",
            year=2024,
            doc_type=DocumentType.JOURNAL_ARTICLE,
            cited_by_count=45,
        )
        r2 = CanonicalPaperRecord(
            record_id="rec_2",
            title="IndoBERT sentiment analysis and misinformation detection in Indonesia",
            abstract="Applying IndoBERT and deep learning for misinformation classification on social networks.",
            year=2024,
            doc_type=DocumentType.JOURNAL_ARTICLE,
            cited_by_count=30,
        )

        vos = VOSviewerClone(min_cluster_size=1, resolution=1.0)
        summary = vos.build_from_canonical_records([r1, r2], min_occurrences=1)

        assert summary["total_items"] > 0
        assert summary["total_links"] >= 0
        assert len(vos.items) > 0

        # Check export capabilities
        json_export = vos.get_vosviewer_online_json()
        assert "network" in json_export
        assert "items" in json_export["network"]
        assert len(json_export["network"]["items"]) == summary["total_items"]
