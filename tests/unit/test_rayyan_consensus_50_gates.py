"""Unit tests for Rayyan Consensus 50-Layer Validation & QA framework and 35 international references."""

from __future__ import annotations

import pytest
from core.citations.international_bibliography import (
    INTERNATIONAL_BIBLIOGRAPHY_35,
    format_apa7,
    get_all_apa7_references,
    verify_bibliography_standards,
)
from core.evaluation.rayyan_consensus_50_gates import (
    RAYYAN_CONSENSUS_50_GATES_SPECS,
    RayyanConsensus50GatesAuditor,
)


def test_bibliography_has_at_least_35_entries():
    assert len(INTERNATIONAL_BIBLIOGRAPHY_35) >= 35
    apa_refs = get_all_apa7_references()
    assert len(apa_refs) >= 35
    for ref in apa_refs:
        assert "https://doi.org/10." in ref
        assert "(" in ref and ")" in ref


def test_bibliography_standards_currency_and_dois():
    audit = verify_bibliography_standards(min_count=35, min_year=2021, max_year=2026)
    assert audit["is_compliant"] is True
    assert audit["total_references"] >= 35
    assert audit["valid_dois_count"] == audit["total_references"]
    assert audit["valid_years_count"] == audit["total_references"]
    assert audit["q1_count"] + audit["q2_count"] == audit["total_references"]
    assert len(audit["invalid_entries"]) == 0


def test_rayyan_consensus_50_gates_specs():
    assert len(RAYYAN_CONSENSUS_50_GATES_SPECS) == 50
    gate_nos = [g["gate_no"] for g in RAYYAN_CONSENSUS_50_GATES_SPECS]
    assert gate_nos == list(range(1, 51))


def test_rayyan_consensus_50_gates_execution():
    auditor = RayyanConsensus50GatesAuditor()
    results = auditor.run_all_gates()

    assert results["total_gates"] == 50
    assert results["passed_gates"] == 50
    assert results["failed_gates"] == 0
    assert results["compliance_percentage"] == 100.0
    assert results["final_verdict"] == "RELEASE_APPROVED_50_OF_50_PASS"
