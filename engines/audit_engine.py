"""Core audit engine executing rules against documents."""

from __future__ import annotations

from dataclasses import dataclass

from engines.finding_engine import build_findings, summarize
from engines.rule_engine import evaluate_rule
from engines.rule_loader import load_rules


@dataclass
class AuditResult:
    rule_set_id: str
    version: str
    summary: dict
    findings: list[dict]
    evaluations: list[dict]


def audit_thesis(
    document: dict,
    rules_path: str = "rules/mikom_2026.json",
) -> AuditResult:
    ruleset = load_rules(rules_path)

    evaluations = [
        evaluate_rule(rule, document)
        for rule in ruleset["rules"]
    ]

    findings = build_findings(evaluations)

    return AuditResult(
        rule_set_id=ruleset["rule_set_id"],
        version=ruleset["version"],
        summary=summarize(evaluations),
        findings=findings,
        evaluations=evaluations,
    )
