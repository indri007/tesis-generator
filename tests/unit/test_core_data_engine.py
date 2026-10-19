"""Unit Tests for Core Literature Data Engine (Phase 1).

Covers all 30 items of Section A and foundational items of Section B and Section F:
- Canonical Data Models & Deterministic ID (#6, #7, #8, #9, #10)
- Text Processor & Inverted Index Reconstruction (#89, #90, #91, #92, #94, #95)
- DOI Verifier & Conflict Detection (#31, #32, #33, #34, #35-#38, #41, #42, #46)
- Multi-tier Deduplication & Preprint Matching (#11, #12, #13, #14, #15, #16, #20, #21)
- Query Registry & Snapshot (#2, #3, #25, #297)
- Core Pipeline Orchestration, Screening & Audit Manifest (#1-#30, #367, #368, #388, #389)
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from core.sources import (
    CanonicalPaperRecord,
    CoreDataEngine,
    DeduplicationEngine,
    DocumentType,
    DuplicateStatus,
    EvidenceLevel,
    PipelineConfig,
    QueryExecutionEntry,
    QueryRegistry,
    SearchProvenance,
    check_doi_resolution,
    clean_abstract,
    detect_language,
    generate_doi_audit_report,
    normalize_doi,
    reconstruct_openalex_inverted_index,
    segment_sentences,
    validate_doi_syntax,
)


class TestCanonicalDataModels:
    def test_deterministic_record_id_consistency(self):
        # With DOI
        id1 = CanonicalPaperRecord.generate_record_id("10.1016/j.tele.2023.102045", "Test Title")
        id2 = CanonicalPaperRecord.generate_record_id("10.1016/j.tele.2023.102045", "Another Title")
        assert id1 == id2
        assert id1.startswith("rec_")

        # Without DOI (based on title, first author, year)
        id_no_doi_1 = CanonicalPaperRecord.generate_record_id(None, "SNA Analysis on Telegram", ["Utomo, Indri"], 2024)
        id_no_doi_2 = CanonicalPaperRecord.generate_record_id(None, "SNA Analysis on Telegram", ["Utomo, Indri"], 2024)
        assert id_no_doi_1 == id_no_doi_2
        assert id_no_doi_1.startswith("rec_")

    def test_quality_score_calculation(self):
        rec = CanonicalPaperRecord(
            record_id="rec_001",
            title="Analysis of Social Media Networks in Indonesian Public Communication",
            authors=["Utomo, Indri", "Santoso, Budi"],
            year=2024,
            doi="10.1016/j.pubrel.2024.101234",
            journal="Public Relations Review",
            abstract="This study investigates the communication dynamics surrounding the MBG policy using IndoBERT and SNA.",
        )
        score = rec.calculate_quality_score()
        assert score == 100.0

        # Partial record
        sparse_rec = CanonicalPaperRecord(record_id="rec_002", title="Short title")
        sparse_score = sparse_rec.calculate_quality_score()
        assert sparse_score == 20.0

    def test_evidence_level_inference(self):
        slr_rec = CanonicalPaperRecord(record_id="rec_slr", title="Systematic literature review on digital media PRISMA")
        assert slr_rec.infer_evidence_level() == EvidenceLevel.LEVEL_1_SYSTEMATIC_REVIEW

        quant_rec = CanonicalPaperRecord(record_id="rec_quant", title="Social network analysis and IndoBERT sentiment classification")
        assert quant_rec.infer_evidence_level() == EvidenceLevel.LEVEL_2_EMPIRICAL_QUANT

        qual_rec = CanonicalPaperRecord(record_id="rec_qual", title="A qualitative case study on government communication")
        assert qual_rec.infer_evidence_level() == EvidenceLevel.LEVEL_3_EMPIRICAL_QUAL

        theory_rec = CanonicalPaperRecord(record_id="rec_theory", title="Marketing 6.0 and phygital metamarketing framework")
        assert theory_rec.infer_evidence_level() == EvidenceLevel.LEVEL_4_CONCEPTUAL_THEORY

    def test_to_and_from_dict_serialization(self):
        rec = CanonicalPaperRecord(
            record_id="rec_serialize",
            title="Serialized Paper Title",
            authors=["Author, Test"],
            year=2025,
            doi="10.1000/182",
            journal="Journal of Testing",
            doc_type=DocumentType.JOURNAL_ARTICLE,
            provenance=SearchProvenance(source_database="OpenAlex", search_query="test query"),
        )
        d = rec.to_dict()
        assert d["doc_type"] == "journal-article"
        assert d["provenance"]["source_database"] == "OpenAlex"

        loaded = CanonicalPaperRecord.from_dict(d)
        assert loaded.record_id == rec.record_id
        assert loaded.doc_type == DocumentType.JOURNAL_ARTICLE
        assert loaded.provenance.source_database == "OpenAlex"


class TestTextProcessor:
    def test_reconstruct_openalex_inverted_index(self):
        inv_index = {
            "IndoBERT": [0],
            "is": [1],
            "used": [2],
            "for": [3],
            "sentiment": [4],
            "analysis": [5],
            "in": [6],
            "Indonesia": [7],
        }
        reconstructed = reconstruct_openalex_inverted_index(inv_index)
        assert reconstructed == "IndoBERT is used for sentiment analysis in Indonesia"

    def test_clean_abstract_html_and_entities(self):
        raw = "   <p>This study uses <i>IndoBERT</i> &amp; SNA for &lt;policy&gt; evaluation.</p>   "
        cleaned = clean_abstract(raw)
        assert cleaned == "This study uses IndoBERT & SNA for <policy> evaluation."

    def test_language_detection(self):
        id_text = "Penelitian ini menggunakan metode analisis jaringan komunikasi pada media sosial untuk kebijakan publik."
        en_text = "This study employs social network analysis and deep learning for digital media communication."
        assert detect_language(id_text) == "id"
        assert detect_language(en_text) == "en"

    def test_sentence_segmentation(self):
        text = (
            "According to Utomo et al. (2024), social bots distort policy narratives. "
            "However, IndoBERT achieves 89.4% F1-score. "
            "Further research is required in Indonesia."
        )
        sentences = segment_sentences(text)
        assert len(sentences) == 3
        assert "According to Utomo et al." in sentences[0]


class TestDOIVerifier:
    def test_normalize_doi(self):
        assert normalize_doi("https://doi.org/10.1016/j.tele.2023.102045") == "10.1016/j.tele.2023.102045"
        assert normalize_doi("http://dx.doi.org/10.1000/182.") == "10.1000/182"
        assert normalize_doi("doi: 10.1145/3308558.3313645;") == "10.1145/3308558.3313645"
        assert normalize_doi("invalid-doi-format") is None

    def test_validate_doi_syntax(self):
        assert validate_doi_syntax("10.1016/j.tele.2023.102045") is True
        assert validate_doi_syntax("10.1000/182") is True
        assert validate_doi_syntax("invalid_prefix/12345") is False

    def test_doi_resolution_offline(self):
        res = check_doi_resolution("10.1016/j.tele.2023.102045", live=False)
        assert res["resolution_status"] == "OFFLINE_VALIDATED"
        assert res["is_valid"] is True

        res_bad = check_doi_resolution("bad_doi", live=False)
        assert res_bad["resolution_status"] == "INVALID_SYNTAX"
        assert res_bad["is_valid"] is False

    def test_generate_doi_audit_report(self):
        r1 = CanonicalPaperRecord(record_id="r1", title="Paper 1", doi="10.1016/j.1")
        r2 = CanonicalPaperRecord(record_id="r2", title="Paper 2", doi=None)
        r3 = CanonicalPaperRecord(record_id="r3", title="Paper 3", doi="bad_doi")
        r4 = CanonicalPaperRecord(record_id="r4", title="Paper 4", doi="10.1016/j.1")  # Duplicate DOI

        report = generate_doi_audit_report([r1, r2, r3, r4])
        assert report["total_records"] == 4
        assert report["records_with_doi"] == 3
        assert report["records_without_doi"] == 1
        assert report["records_with_broken_doi"] == 1
        assert report["duplicate_doi_count"] == 1


class TestDeduplicationEngine:
    def test_exact_doi_deduplication_and_merging(self):
        r1 = CanonicalPaperRecord(
            record_id="r1",
            title="Communication Dynamics on Telegram",
            doi="10.1016/j.comm.2024.001",
            year=2024,
            journal="Journal of Communication",
            abstract="Abstract is present in record 1.",
        )
        r2 = CanonicalPaperRecord(
            record_id="r2",
            title="Communication Dynamics on Telegram",
            doi="10.1016/j.comm.2024.001",
            year=2024,
            journal=None,
            abstract=None,
            cited_by_count=42,
        )

        engine = DeduplicationEngine()
        uniques, summary = engine.deduplicate([r1, r2])

        assert len(uniques) == 1
        assert summary.exact_duplicates == 1
        assert uniques[0].cited_by_count == 42  # Enriched from r2

    def test_preprint_to_journal_matching(self):
        preprint = CanonicalPaperRecord(
            record_id="p1",
            title="Deep Learning and Social Network Analysis in Indonesian Politics",
            authors=["Utomo, Indri"],
            year=2023,
            doc_type=DocumentType.PREPRINT,
            journal="arXiv:2301.00123",
        )
        journal_pub = CanonicalPaperRecord(
            record_id="j1",
            title="Deep Learning and Social Network Analysis in Indonesian Politics",
            authors=["Utomo, Indri"],
            year=2024,
            doc_type=DocumentType.JOURNAL_ARTICLE,
            journal="Telematics and Informatics",
            doi="10.1016/j.tele.2024.102",
        )

        engine = DeduplicationEngine()
        uniques, summary = engine.deduplicate([journal_pub, preprint])

        assert len(uniques) == 1
        assert summary.preprints_matched_to_journal == 1
        assert preprint.duplicate_status == DuplicateStatus.EXACT_DUPLICATE
        assert preprint.canonical_record_id == journal_pub.record_id

    def test_candidate_duplicate_manual_review_queue(self):
        r1 = CanonicalPaperRecord(
            record_id="r1",
            title="Digital Media Literacy in Indonesian High Schools: A Case Study in Surabaya",
            year=2024,
        )
        r2 = CanonicalPaperRecord(
            record_id="r2",
            title="Digital Media Literacy in Indonesian High Schools: A Survey in East Java",
            year=2024,
        )

        engine = DeduplicationEngine(exact_threshold=0.90, candidate_threshold=0.70)
        uniques, summary = engine.deduplicate([r1, r2])

        # Borderline match should be added to manual review queue
        assert summary.candidate_duplicates >= 1
        assert len(summary.manual_review_queue) >= 1
        assert summary.manual_review_queue[0]["action_required"] == "Confirm or Reject Merge"


class TestQueryRegistry:
    def test_register_and_snapshot(self, tmp_path):
        registry = QueryRegistry()
        entry = QueryExecutionEntry.create(
            query_text="social network analysis Indonesia",
            target_database="Crossref",
            filters={"rows": 100},
            records_retrieved=85,
            execution_duration_sec=1.234,
        )
        registry.register(entry)

        summary = registry.get_summary()
        assert summary["total_queries_executed"] == 1
        assert summary["total_records_retrieved"] == 85
        assert summary["retrieval_by_database"]["Crossref"] == 85

        snapshot_file = tmp_path / "query_snapshot.json"
        registry.save_snapshot(snapshot_file)
        assert snapshot_file.exists()
        with open(snapshot_file) as f:
            data = json.load(f)
            assert data["total_queries_executed"] == 1


class TestCoreDataEnginePipeline:
    def test_full_pipeline_run_and_exports(self, tmp_path):
        config = PipelineConfig(
            min_year=2021,
            max_year=2026,
            allowed_doc_types=["journal-article", "conference-paper"],
            required_quality_score=35.0,
            output_dir=str(tmp_path),
        )
        engine = CoreDataEngine(config=config)

        raw_dataset = [
            # 1. Valid, included modern article
            {
                "doi": "10.1016/j.tele.2023.102045",
                "title": "Public sentiment and network dynamics in Indonesian social media",
                "author": [{"family": "Utomo", "given": "Indri"}],
                "published": {"date-parts": [[2023, 5, 12]]},
                "container-title": ["Telematics and Informatics"],
                "type": "journal-article",
                "abstract": "We analyze public sentiment and interaction patterns using IndoBERT and SNA.",
            },
            # 2. Duplicate of item 1 (different provider format)
            {
                "doi": "https://doi.org/10.1016/j.tele.2023.102045",
                "title": "Public sentiment and network dynamics in Indonesian social media",
                "authors": ["Utomo, Indri"],
                "publication_year": 2023,
                "journal": "Telematics and Informatics",
                "type": "article",
            },
            # 3. Outdated paper (Year 2018 < 2021 threshold) -> Should be EXCLUDED
            {
                "doi": "10.1145/old.2018.111",
                "title": "Legacy communication analysis in digital newspapers",
                "authors": ["Pratama, Agus"],
                "year": 2018,
                "journal": "ACM Digital Library",
                "type": "proceedings-article",
                "abstract": "Older historical analysis of print media transitions.",
            },
            # 4. OpenAlex record with inverted index abstract
            {
                "doi": "10.1080/01292986.2024.123",
                "title": "Media literacy and policy communication in Southeast Asia",
                "authors": ["Santoso, Budi"],
                "publication_year": 2024,
                "journal": "Asian Journal of Communication",
                "type": "journal-article",
                "abstract_inverted_index": {
                    "Media": [0],
                    "literacy": [1],
                    "is": [2],
                    "crucial": [3],
                    "for": [4],
                    "combating": [5],
                    "misinformation": [6],
                },
            },
        ]

        manifest = engine.run_pipeline(raw_dataset, source_database="TestAggregator", output_dir=tmp_path)

        assert manifest["input_records_count"] == 4
        assert manifest["unique_canonical_count"] == 3  # Item 2 deduplicated against Item 1
        assert manifest["included_count"] == 2          # Item 1 and Item 4 included
        assert manifest["excluded_count"] == 1          # Item 3 excluded due to year 2018

        # Verify output files exist and are non-empty (#368, #387)
        jsonl_path = Path(manifest["output_files"]["master_jsonl"]["path"])
        csv_path = Path(manifest["output_files"]["master_csv"]["path"])
        rev_path = Path(manifest["output_files"]["manual_review_queue"]["path"])

        assert jsonl_path.exists() and jsonl_path.stat().st_size > 0
        assert csv_path.exists() and csv_path.stat().st_size > 0
        assert rev_path.exists()

        # Check Pandas readability (#367)
        df = pd.read_csv(csv_path)
        assert len(df) == 3
        assert "record_id" in df.columns
        assert "inclusion_status" in df.columns

        # Check SHA256 checksums are populated (#389)
        assert len(manifest["output_files"]["master_csv"]["sha256"]) == 64
        assert len(manifest["output_files"]["master_jsonl"]["sha256"]) == 64

    def test_doi_consistency_verification(self):
        from core.sources.doi_verifier import verify_doi_consistency

        local = CanonicalPaperRecord(
            record_id="rec_loc",
            title="Social Media Analysis in Indonesian Government",
            authors=["Utomo, Indri"],
            year=2024,
            journal="Telematics and Informatics",
            doi="10.1016/j.tele.2024.101",
        )

        # Consistent metadata
        consistent_meta = {
            "title": "Social Media Analysis in Indonesian Government",
            "year": 2024,
            "journal": "Telematics and Informatics",
        }
        res_ok = verify_doi_consistency(local, consistent_meta)
        assert res_ok["is_consistent"] is True
        assert len(res_ok["conflicts"]) == 0

        # Inconsistent metadata (year mismatch & journal mismatch)
        inconsistent_meta = {
            "title": "Unrelated Physics Quantum mechanics",
            "year": 2015,
            "journal": "Physical Review Letters",
        }
        res_bad = verify_doi_consistency(local, inconsistent_meta)
        assert res_bad["is_consistent"] is False
        assert len(res_bad["conflicts"]) >= 2

    def test_process_all_raw_metadata_integration(self, tmp_path, monkeypatch):
        import core.sources.process_metadata as pm

        raw_dir = tmp_path / "raw"
        processed_file = tmp_path / "processed" / "clean_references.jsonl"
        raw_dir.mkdir(parents=True)

        sample_item = {
            "doi": "10.1016/j.tele.2023.102045",
            "title": "Public sentiment and network dynamics in Indonesian social media",
            "authors": ["Utomo, Indri"],
            "published": 2023,
            "journal": "Telematics and Informatics",
            "type": "journal-article",
        }
        with open(raw_dir / "sample.jsonl", "w", encoding="utf-8") as f:
            f.write(json.dumps(sample_item) + "\n")

        monkeypatch.setattr(pm, "RAW_DIR", raw_dir)
        monkeypatch.setattr(pm, "PROCESSED_FILE", processed_file)

        res = pm.process_all_raw_metadata()
        assert res["total_raw"] == 1
        assert res["unique_saved"] == 1
        assert processed_file.exists()

