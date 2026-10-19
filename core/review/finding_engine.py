"""Finding engine filtering and summarizing evaluation outcomes."""

from __future__ import annotations

from collections import Counter

VALID_STATUSES = {
    "PASS", "ERROR", "WARNING", "INFO", "UNVERIFIED"
}


def build_findings(evaluations: list[dict]) -> list[dict]:
    """Filters evaluations to keep non-PASS items as findings."""
    findings = []

    for result in evaluations:
        if result["status"] not in VALID_STATUSES:
            raise ValueError(
                f"Status tidak dikenal: {result['status']}"
            )

        if result["status"] == "PASS":
            continue

        findings.append(result)

    return findings


def summarize(evaluations: list[dict]) -> dict:
    """Summarizes counts of each status in evaluations."""
    counts = Counter(item["status"] for item in evaluations)

    return {
        "total_rules": len(evaluations),
        "PASS": counts["PASS"],
        "ERROR": counts["ERROR"],
        "WARNING": counts["WARNING"],
        "INFO": counts["INFO"],
        "UNVERIFIED": counts["UNVERIFIED"],
    }
