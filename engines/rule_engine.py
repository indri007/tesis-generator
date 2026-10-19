"""Rule engine evaluating schema rules against extracted document models."""

from __future__ import annotations

import re
from typing import Any


def get_nested_field(doc: dict, field_path: str) -> tuple[bool, Any]:
    """Retrieve a nested field using dot notation.
    Returns (found: bool, value: Any).
    """
    parts = field_path.split(".")
    current: Any = doc
    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return False, None
    return True, current


def evaluate_rule(rule: dict, document: dict) -> dict:
    """Evaluates a single rule against the document data.
    Returns structured evaluation with status: PASS, ERROR, WARNING, INFO, or UNVERIFIED.
    """
    field_path = rule.get("field", "")
    operator = rule.get("operator", "equals")
    expected = rule.get("expected")
    severity = rule.get("severity", "ERROR")

    found, actual = get_nested_field(document, field_path)

    # Missing field evaluates to UNVERIFIED as per test specification
    if not found or actual is None:
        return {
            "rule_id": rule["id"],
            "category": rule["category"],
            "description": rule.get("description", ""),
            "severity": severity,
            "status": "UNVERIFIED",
            "field": field_path,
            "actual": None,
            "expected": expected,
            "evidence_query": rule.get("evidence_query", ""),
            "recommendation": rule.get("recommendation", ""),
            "source": rule.get("source", {}),
            "message": f"Data field '{field_path}' tidak ditemukan pada dokumen atau tidak dapat diverifikasi."
        }

    # Evaluate operator
    is_pass = False
    try:
        if operator == "equals":
            # Handle float tolerances if both are numeric
            if isinstance(actual, (int, float)) and isinstance(expected, (int, float)):
                is_pass = abs(actual - expected) < 1e-4
            else:
                is_pass = actual == expected
        elif operator == "not_equals":
            is_pass = actual != expected
        elif operator == "exists":
            is_pass = actual is not None
        elif operator == "not_empty":
            if isinstance(actual, str):
                is_pass = len(actual.strip()) > 0
            elif isinstance(actual, (list, dict, set, tuple)):
                is_pass = len(actual) > 0
            else:
                is_pass = bool(actual)
        elif operator == "min":
            is_pass = float(actual) >= float(expected)
        elif operator == "max":
            is_pass = float(actual) <= float(expected)
        elif operator == "regex":
            is_pass = bool(re.search(str(expected), str(actual)))
    except Exception:
        is_pass = False

    status = "PASS" if is_pass else severity

    return {
        "rule_id": rule["id"],
        "category": rule["category"],
        "description": rule.get("description", ""),
        "severity": severity,
        "status": status,
        "field": field_path,
        "actual": actual,
        "expected": expected,
        "evidence_query": rule.get("evidence_query", ""),
        "recommendation": rule.get("recommendation", ""),
        "source": rule.get("source", {}),
        "message": (
            f"Kesesuaian terpenuhi: {actual}"
            if is_pass
            else f"Ketidaksesuaian terdeteksi pada '{field_path}': nilai aktual {actual}, diharapkan {expected}."
        )
    }
