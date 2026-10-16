"""Unified Research & Manuscript Audit Pipeline.

Integrates Rayyan systematic review deduplication, PICO research question extraction,
and Consensus scientific literature consensus into the thesis auditing workflow.
Maintains full backward and forward compatibility with CitationAuditor and ParsedDocument.
Strictly separates reference deduplication from plagiarism and citation mismatch findings.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from core.integrations.consensus_importer import (
    ConsensusSearchResult,
    parse_consensus_csv,
)
from core.integrations.elsevier_client import (
    ElsevierClient,
    ElsevierSearchResult,
    parse_elsevier_ris,
    parse_scopus_csv,
)
from core.integrations.pico_extractor import extract_pico_from_text
from core.integrations.rayyan_importer import (
    RayyanRecord,
    deduplicate_records,
    parse_rayyan_csv,
    parse_rayyan_ris,
)
from engines.citation_auditor import CitationAuditor
from models.document_model import ParsedDocument


@dataclass
class UnifiedAuditReport:
    pico: dict[str, Any]
    rayyan_summary: dict[str, Any]
    consensus_summary: dict[str, Any]
    citation_findings: list[dict[str, Any]]
    rule_input: dict[str, Any]
    gate_status: dict[str, bool]
    elsevier_summary: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "pico": self.pico,
            "rayyan_summary": self.rayyan_summary,
            "consensus_summary": self.consensus_summary,
            "elsevier_summary": self.elsevier_summary,
            "citation_findings": self.citation_findings,
            "rule_input": self.rule_input,
            "gate_status": self.gate_status,
        }


class UnifiedResearchPipeline:
    """Orchestrates Rayyan, PICO, and Consensus modules with manuscript compliance."""

    def __init__(self, document: ParsedDocument):
        self.doc = document
        self.full_text = document.get_text()

    def audit(
        self,
        rayyan_content: str | None = None,
        rayyan_format: str = "csv",
        consensus_content: str | None = None,
        elsevier_content: str | None = None,
        elsevier_format: str = "csv",
        elsevier_query: str | None = None,
    ) -> UnifiedAuditReport:
        # 1. PICO Extraction from Abstract / Bab I
        pico_res = extract_pico_from_text(self.full_text)

        # 2. Rayyan Deduplication (if export content provided)
        rayyan_records: list[RayyanRecord] = []
        if rayyan_content:
            if rayyan_format.lower() == "ris":
                rayyan_records = parse_rayyan_ris(rayyan_content)
            else:
                rayyan_records = parse_rayyan_csv(rayyan_content)
            rayyan_records = deduplicate_records(rayyan_records)

        exact_dups = [r for r in rayyan_records if r.duplicate_status == "EXACT_DUPLICATE"]
        cand_dups = [r for r in rayyan_records if r.duplicate_status == "CANDIDATE_DUPLICATE"]
        uniques = [r for r in rayyan_records if r.duplicate_status == "UNIQUE"]

        rayyan_summary = {
            "total_records": len(rayyan_records),
            "exact_duplicates": len(exact_dups),
            "candidate_duplicates": len(cand_dups),
            "unique_records": len(uniques),
            "records": [r.to_dict() for r in rayyan_records],
        }

        # 3. Consensus Integration (if export content provided)
        consensus_res: ConsensusSearchResult | None = None
        if consensus_content:
            consensus_res = parse_consensus_csv(consensus_content)

        consensus_summary = (
            consensus_res.to_dict()
            if consensus_res
            else {
                "query": "Not provided",
                "total_results": 0,
                "consensus_summary": "No Consensus literature export provided.",
                "api_status": "OFFLINE_NO_DATA",
                "papers": [],
            }
        )

        # 4. Elsevier ScienceDirect / Scopus Integration
        elsevier_res: ElsevierSearchResult | None = None
        if elsevier_content:
            if elsevier_format.lower() == "ris":
                elsevier_res = parse_elsevier_ris(elsevier_content, query=elsevier_query or "")
            else:
                elsevier_res = parse_scopus_csv(elsevier_content, query=elsevier_query or "")
        elif elsevier_query:
            client = ElsevierClient()
            elsevier_res = client.search_articles(elsevier_query)

        elsevier_summary = (
            elsevier_res.to_dict()
            if elsevier_res
            else {
                "query": elsevier_query or "Not provided",
                "total_results": 0,
                "q1_count": 0,
                "q2_count": 0,
                "open_access_count": 0,
                "avg_citations": 0.0,
                "api_status": "OFFLINE_NO_DATA",
                "articles": [],
            }
        )

        # 5. Standard Citation Auditor (APA 7)
        auditor = CitationAuditor(self.doc)
        citation_findings = auditor.audit()

        # 6. Rule input parity
        rule_input = self.doc.to_rule_input()

        # Gate Verification
        gate_status = {
            "pico_verified": pico_res.population.is_present or pico_res.intervention.is_present or pico_res.outcome.is_present,
            "rayyan_dedup_completed": True if not rayyan_content or len(rayyan_records) > 0 else False,
            "consensus_verified": True if not consensus_content or (consensus_res and consensus_res.total_results > 0) else False,
            "elsevier_verified": True if not (elsevier_content or elsevier_query) or (elsevier_res and elsevier_res.total_results > 0) else False,
            "citations_passed": not any(f["status"] == "ERROR" for f in citation_findings),
        }

        return UnifiedAuditReport(
            pico=pico_res.to_dict(),
            rayyan_summary=rayyan_summary,
            consensus_summary=consensus_summary,
            elsevier_summary=elsevier_summary,
            citation_findings=citation_findings,
            rule_input=rule_input,
            gate_status=gate_status,
        )
