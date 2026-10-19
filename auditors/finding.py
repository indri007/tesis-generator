"""Finding and AuditResult data classes, plus RuleLoader."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

SeverityType = Literal["ERROR", "WARNING", "INFO", "PASS", "UNVERIFIED"]
PriorityType = Literal["PRIORITAS 1", "PRIORITAS 2", "PRIORITAS 3", "INFO/PASS"]


@dataclass
class Finding:
    """Represents an evidence-backed compliance or consistency finding."""
    rule_id: str
    rule_name: str
    category: str
    severity: SeverityType
    message: str
    location: str
    evidence: str
    expected: str
    actual: str
    recommendation: str
    source_ref: str = "Pedoman Penulisan Tesis MIKOM 2026"
    confidence: float = 1.0  # 0.0 to 1.0
    priority: PriorityType = "PRIORITAS 2"

    def __post_init__(self):
        # Auto-assign priority based on severity and category
        if self.severity == "ERROR":
            if self.category in [
                "formula_recalculation", "formula_consistency", "variable_consistency",
                "statistical_consistency", "sample_consistency", "hypothesis_decision",
                "journal_thesis_alignment", "contradiction",
                "plagiarism", "ai_generated", "academic_integrity"
            ]:
                self.priority = "PRIORITAS 1"
            else:
                self.priority = "PRIORITAS 2"
        elif self.severity == "WARNING":
            if self.category in ["margins", "font_family", "font_size", "line_spacing", "alignment"]:
                self.priority = "PRIORITAS 3"
            else:
                self.priority = "PRIORITAS 2"
        else:
            self.priority = "INFO/PASS"


@dataclass
class AuditResult:
    """Unified result container for full thesis audit."""
    document_name: str
    page_count: int
    total_words: int
    research_type: str
    is_scanned: bool = False
    findings: list[Finding] = field(default_factory=list)
    category_scores: dict[str, float] = field(default_factory=dict)
    overall_score: float = 0.0
    journal_evaluated: bool = False
    journal_alignment_score: float | None = None
    journal_comparison_table: list[dict[str, Any]] = field(default_factory=list)

    @property
    def counts(self) -> dict[str, int]:
        c = {"ERROR": 0, "WARNING": 0, "PASS": 0, "INFO": 0, "UNVERIFIED": 0}
        for f in self.findings:
            if f.severity in c:
                c[f.severity] += 1
        return c

    @property
    def priority_checklist(self) -> dict[str, list[Finding]]:
        checklist: dict[str, list[Finding]] = {
            "PRIORITAS 1": [],
            "PRIORITAS 2": [],
            "PRIORITAS 3": []
        }
        for f in self.findings:
            if f.priority in checklist and f.severity in ["ERROR", "WARNING"]:
                checklist[f.priority].append(f)
        return checklist

    def compute_scores(self) -> None:
        """Compute category scores and overall audit compliance score."""
        categories = {f.category for f in self.findings}
        if not categories:
            self.overall_score = 100.0
            return

        cat_scores: dict[str, float] = {}
        for cat in categories:
            cat_findings = [f for f in self.findings if f.category == cat]
            total = len(cat_findings)
            if total == 0:
                continue
            errors = sum(1 for f in cat_findings if f.severity == "ERROR")
            warnings = sum(1 for f in cat_findings if f.severity == "WARNING")
            unverified = sum(1 for f in cat_findings if f.severity == "UNVERIFIED")

            penalty = (errors * 20.0) + (warnings * 8.0) + (unverified * 4.0)
            score = max(0.0, min(100.0, 100.0 - penalty))
            cat_scores[cat] = round(score, 1)

        self.category_scores = cat_scores
        # Overall weighted score
        self.overall_score = round(sum(cat_scores.values()) / max(1, len(cat_scores)), 1)


class RuleLoader:
    """Loads and provides access to MIKOM 2026 rules."""

    def __init__(self, rules_path: str | Path | None = None):
        if rules_path is None:
            base_dir = Path(__file__).resolve().parent.parent
            rules_path = base_dir / "rules" / "mikom_2026.json"
        self.rules_path = Path(rules_path)
        self.data: dict[str, Any] = {}
        self.rules_by_id: dict[str, dict[str, Any]] = {}
        self.load()

    def load(self) -> None:
        if self.rules_path.exists():
            with open(self.rules_path, "r", encoding="utf-8") as f:
                self.data = json.load(f)
                for r in self.data.get("rules", []):
                    self.rules_by_id[r["rule_id"]] = r

    def get_rule(self, rule_id: str) -> dict[str, Any]:
        return self.rules_by_id.get(rule_id, {
            "rule_id": rule_id,
            "name": rule_id,
            "category": "general",
            "severity": "WARNING",
            "source": "Pedoman Penulisan Tesis MIKOM 2026",
            "page_ref": "Ketentuan Umum"
        })
