"""Academic Quality Benchmark Test & Report Generator.

Executes full-scale evaluation across the evaluation set, verifies metric assertions,
computes inter-annotator agreement, and exports official JSON and Markdown benchmark reports.
"""

from __future__ import annotations

import json
from pathlib import Path

from core.evaluation.benchmark_runner import AcademicBenchmarkRunner
from core.evaluation.schema import EvaluatorConfig
from engines.audit_engine import audit_thesis
from engines.document_parser import parse_document
from golden_dataset.generator import generate_golden_dataset


def test_reproducible_academic_benchmark(tmp_path):
    """Executes the benchmark evaluation on the evaluation split and exports reports."""
    benchmark_docs_dir = tmp_path / 'documents'
    benchmark_docs_dir.mkdir(parents=True, exist_ok=True)
    git_metadata = {
        'commit': __import__('subprocess').run(
            ['git', 'rev-parse', 'HEAD'], cwd=Path(__file__).resolve().parents[2],
            capture_output=True, text=True, check=True
        ).stdout.strip(),
        'dirty': bool(__import__('subprocess').run(
            ['git', 'status', '--porcelain'], cwd=Path(__file__).resolve().parents[2],
            capture_output=True, text=True, check=True
        ).stdout.strip()),
    }
    # 1. Load the evaluation ground-truth dataset
    eval_dataset_path = Path(__file__).resolve().parent.parent.parent / "data" / "benchmark" / "evaluation_set.json"
    assert eval_dataset_path.exists(), f"Evaluation dataset not found at {eval_dataset_path}"

    with open(eval_dataset_path, "r", encoding="utf-8") as f:
        eval_data = json.load(f)

    # 2. Generate actual test documents
    golden_docs = generate_golden_dataset(output_dir=benchmark_docs_dir)
    from golden_dataset.generator import create_base_thesis_text, save_test_docx

    # Dedicated document for EVAL-007 (unused reference in bibliography)
    text_unused = create_base_thesis_text(
        bib_entries=[
            "Smith, J. (2022). Digital Communication and Media Technologies. Academic Press.",
            "Rahmawati, A. (2023). Strategic Marketing in Communication Age. Media Nusantara.",
            "Kurniawan, B. (2021). Media Sosial dan Partisipasi Publik. Pustaka Ilmu."
        ],
        pad_to_40k=True
    )
    p_unused = benchmark_docs_dir / "TEST-011_unused_reference.docx"
    save_test_docx(text_unused, p_unused)

    # Mapping evaluation items to synthetic test cases
    doc_mapping = {
        "DOC-ANON-EVAL-001": golden_docs["TEST-001"],
        "DOC-ANON-EVAL-002": golden_docs["TEST-006"],
        "DOC-ANON-EVAL-003": golden_docs["TEST-007"],
        "DOC-ANON-EVAL-004": golden_docs["TEST-008"],
        "DOC-ANON-EVAL-005": golden_docs["TEST-009"],
        "DOC-ANON-EVAL-006": golden_docs["TEST-010"],
        "DOC-ANON-EVAL-007": {"file": str(p_unused)},
    }

    dataset_eval_items = []

    for item in eval_data["items"]:
        doc_id = item["document_id"]
        doc_entry = doc_mapping.get(doc_id)
        assert doc_entry is not None, f"Mapping missing for {doc_id}"

        # Parse and execute audit
        parsed_doc = parse_document(doc_entry["file"])
        if doc_entry.get("journal_file"):
            parsed_doc.journal_document = parse_document(doc_entry["journal_file"])

        rule_input = parsed_doc.to_rule_input()
        audit_res = audit_thesis(rule_input)

        detected_findings = list(audit_res.findings)

        # Deduplicate detected findings by rule_id
        seen = set()
        dedup = []
        for d in detected_findings:
            if d.get("rule_id") not in seen:
                seen.add(d.get("rule_id"))
                dedup.append(d)

        dataset_eval_items.append({
            "document_id": doc_id,
            "description": item["description"],
            "reference_annotations": item["reference_annotations"],
            "detected_findings": dedup,
            "reviewer_1_labels": item.get("reviewer_1_labels", []),
            "reviewer_2_labels": item.get("reviewer_2_labels", []),
        })

    # 3. Execute Benchmark Evaluation Runner
    config = EvaluatorConfig(
        base_commit=git_metadata["commit"],
        code_version=git_metadata["commit"],
        working_tree_dirty=git_metadata["dirty"],
        dataset_version="2026.1",
        ruleset_id="MIKOM_2026",
        ruleset_version="2026.1.0",
        split="evaluation",
        offline_mode=True
    )
    runner = AcademicBenchmarkRunner(config=config, output_dir=tmp_path / "reports")

    summary, errors, agreement = runner.evaluate_dataset(
        dataset_eval_items,
        strict_location=False,
        strict_severity=True
    )

    # 4. Generate Reports (JSON and Markdown)
    json_path, md_path = runner.generate_reports(summary, errors, agreement)
    assert json_path.exists()
    assert md_path.exists()
    assert json_path.stat().st_size > 500
    assert md_path.stat().st_size > 500

    # 5. Quality Gate Assertions
    micro = summary.micro_metrics
    assert micro["precision"] is not None
    assert micro["recall"] is not None
    assert micro["f1_score"] is not None

    # Quality Gate requires >= 85% Precision, Recall, and F1
    assert micro["precision"] >= 85.0, f"Precision {micro['precision']}% below 85%"
    assert micro["recall"] >= 85.0, f"Recall {micro['recall']}% below 85%"
    assert micro["f1_score"] >= 85.0, f"F1-score {micro['f1_score']}% below 85%"

    # Inter-annotator agreement assertions
    assert agreement["sample_count"] > 0
    assert agreement["observed_agreement"] is not None
    assert agreement["kappa"] is not None
    # Kappa should reflect substantial to high agreement between standardized reviewers
    assert agreement["kappa"] >= 0.60, f"Cohen's Kappa {agreement['kappa']} below 0.60"

    print("\n" + "=" * 60)
    print(f"BENCHMARK RUN COMPLETED: {summary.total_documents} documents evaluated.")
    print(f"Micro Precision : {micro['precision']}%")
    print(f"Micro Recall    : {micro['recall']}%")
    print(f"Micro F1-Score  : {micro['f1_score']}%")
    print(f"Cohen's Kappa   : {agreement['kappa']} ({agreement['agreement_strength']})")
    print(f"Reports saved to:\n  {json_path}\n  {md_path}")
    print("=" * 60)
