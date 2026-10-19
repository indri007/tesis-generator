"""Golden Dataset Evaluation Test: Runs audit on 10 synthetic test cases and computes Precision, Recall, and Accuracy."""


import pytest

from engines.audit_engine import audit_thesis
from engines.document_parser import parse_document
from golden_dataset.generator import generate_golden_dataset


@pytest.fixture(scope="module")
def golden_dataset():
    """Generates the 10 golden test documents."""
    return generate_golden_dataset()


def test_golden_dataset_evaluation(golden_dataset):
    """Evaluates the 10 golden test cases against ground-truth labels."""
    true_positives = 0
    false_positives = 0
    false_negatives = 0
    true_negatives = 0

    domain_eval = {
        "formula": {"tp": 0, "fp": 0, "fn": 0, "tn": 0},
        "variable": {"tp": 0, "fp": 0, "fn": 0, "tn": 0},
        "citation": {"tp": 0, "fp": 0, "fn": 0, "tn": 0},
        "statistics": {"tp": 0, "fp": 0, "fn": 0, "tn": 0},
        "journal": {"tp": 0, "fp": 0, "fn": 0, "tn": 0},
        "format_structure": {"tp": 0, "fp": 0, "fn": 0, "tn": 0},
    }

    results_summary = []

    for test_id, item in golden_dataset.items():
        thesis_path = item["file"]
        journal_path = item.get("journal_file")
        expected_errors = set(item.get("expected_errors", []))

        # Parse and audit
        doc = parse_document(thesis_path)
        if journal_path:
            doc_j = parse_document(journal_path)
            doc.journal_document = doc_j

        rule_input = doc.to_rule_input()
        audit_res = audit_thesis(rule_input)

        # Mapped findings
        detected_errors = set()
        for f in audit_res.findings:
            if f["status"] == "ERROR":
                detected_errors.add(f["rule_id"])

        # Check accuracy for this test case
        matched = expected_errors.intersection(detected_errors)
        missed = expected_errors - detected_errors
        unexpected = detected_errors - expected_errors

        tp = len(matched)
        fn = len(missed)
        fp = len(unexpected)
        tn = 1 if len(expected_errors) == 0 and len(detected_errors) == 0 else 0

        true_positives += tp
        false_positives += fp
        false_negatives += fn
        true_negatives += tn

        # Domain categorization
        for err in expected_errors:
            if "FORMULA" in err:
                if err in detected_errors:
                    domain_eval["formula"]["tp"] += 1
                else:
                    domain_eval["formula"]["fn"] += 1
            elif "VARIABLE" in err:
                if err in detected_errors:
                    domain_eval["variable"]["tp"] += 1
                else:
                    domain_eval["variable"]["fn"] += 1
            elif "CITATION" in err or "BIB" in err:
                if err in detected_errors:
                    domain_eval["citation"]["tp"] += 1
                else:
                    domain_eval["citation"]["fn"] += 1
            elif "STAT" in err:
                if err in detected_errors:
                    domain_eval["statistics"]["tp"] += 1
                else:
                    domain_eval["statistics"]["fn"] += 1
            elif "JOURNAL" in err:
                if err in detected_errors:
                    domain_eval["journal"]["tp"] += 1
                else:
                    domain_eval["journal"]["fn"] += 1
            else:
                if err in detected_errors:
                    domain_eval["format_structure"]["tp"] += 1
                else:
                    domain_eval["format_structure"]["fn"] += 1

        results_summary.append({
            "test_id": test_id,
            "description": item["description"],
            "expected_errors": list(expected_errors),
            "detected_errors": list(detected_errors),
            "is_correct": len(missed) == 0 and len(unexpected) == 0
        })

    # Compute overall metrics
    precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 1.0
    recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 1.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 1.0

    print("\n" + "=" * 60)
    print("GOLDEN DATASET BENCHMARK EVALUATION (10 TEST CASES)")
    print("=" * 60)
    for r in results_summary:
        status_sym = "✓ PASS" if r["is_correct"] else "❌ MISMATCH"
        print(f"[{r['test_id']}] {status_sym} - {r['description']}")
        if not r["is_correct"]:
            print(f"    Expected: {r['expected_errors']}")
            print(f"    Detected: {r['detected_errors']}")

    print("-" * 60)
    print(f"True Positives  : {true_positives}")
    print(f"False Positives : {false_positives}")
    print(f"False Negatives : {false_negatives}")
    print(f"Precision       : {precision * 100:.1f}%")
    print(f"Recall          : {recall * 100:.1f}%")
    print(f"F1 Score        : {f1 * 100:.1f}%")
    print("=" * 60)

    # Verification criteria
    assert recall >= 0.85, f"Recall {recall} is below target 85%"
    assert precision >= 0.85, f"Precision {precision} is below target 85%"
