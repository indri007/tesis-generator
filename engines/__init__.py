"""Engines package for TesisCheck MIKOM 2026."""

from engines.audit_engine import AuditResult, audit_thesis
from engines.evidence_engine import Evidence, create_evidence
from engines.finding_engine import build_findings, summarize
from engines.rule_engine import evaluate_rule
from engines.rule_loader import load_rules

from engines.academic_writing_auditor import AcademicWritingAuditor
from engines.meta_analysis_auditor import MetaAnalysisAuditor
from engines.research_methods_auditor import ResearchMethodsAuditor

__all__ = [
    "AcademicWritingAuditor",
    "AuditResult",
    "Evidence",
    "MetaAnalysisAuditor",
    "ResearchMethodsAuditor",
    "audit_thesis",
    "build_findings",
    "create_evidence",
    "evaluate_rule",
    "load_rules",
    "summarize"
]

