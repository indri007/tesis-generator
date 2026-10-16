"""Rule loading and validation against RULE_SCHEMA."""

from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator

RULE_SCHEMA = {
    "type": "object",
    "required": ["rule_set_id", "version", "rules"],
    "properties": {
        "rule_set_id": {"type": "string"},
        "version": {"type": "string"},
        "rules": {
            "type": "array",
            "items": {
                "type": "object",
                "required": [
                    "id", "category", "description",
                    "severity", "field", "operator",
                    "expected", "recommendation"
                ],
                "properties": {
                    "id": {"type": "string"},
                    "category": {"type": "string"},
                    "description": {"type": "string"},
                    "severity": {
                        "enum": [
                            "ERROR", "WARNING", "INFO"
                        ]
                    },
                    "field": {"type": "string"},
                    "operator": {
                        "enum": [
                            "equals", "not_equals",
                            "exists", "not_empty",
                            "min", "max", "regex"
                        ]
                    },
                    "expected": {},
                    "recommendation": {"type": "string"},
                    "source": {"type": "object"}
                }
            }
        }
    }
}


def load_rules(path: str = "rules/mikom_2026.json") -> dict:
    rule_path = Path(path)

    if not rule_path.is_file():
        raise FileNotFoundError(
            f"File aturan tidak ditemukan: {rule_path}"
        )

    with rule_path.open("r", encoding="utf-8") as file:
        ruleset = json.load(file)

    errors = sorted(
        Draft202012Validator(RULE_SCHEMA).iter_errors(ruleset),
        key=lambda error: list(error.path)
    )

    if errors:
        details = "; ".join(
            f"{list(error.path)}: {error.message}"
            for error in errors
        )
        raise ValueError(f"Rule set tidak valid: {details}")

    rule_ids = [rule["id"] for rule in ruleset["rules"]]

    if len(rule_ids) != len(set(rule_ids)):
        raise ValueError("ID aturan harus unik.")

    return ruleset
