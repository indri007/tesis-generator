"""Evidence engine enriching findings with location, page, excerpts, and verification."""

from __future__ import annotations

from pydantic import BaseModel


class Evidence(BaseModel):
    rule_id: str
    status: str
    category: str

    page: int | None = None
    section: str | None = None
    excerpt: str | None = None

    actual: object = None
    expected: object = None

    source_title: str | None = None
    source_page: int | None = None

    recommendation: str
    evidence_verified: bool = False


def create_evidence(
    finding: dict,
    page: int | None = None,
    section: str | None = None,
    excerpt: str | None = None,
) -> dict:
    source = finding.get("source", {})

    evidence = Evidence(
        rule_id=finding["rule_id"],
        status=finding["status"],
        category=finding["category"],
        page=page,
        section=section,
        excerpt=excerpt,
        actual=finding.get("actual"),
        expected=finding.get("expected"),
        source_title=source.get("title") if isinstance(source, dict) else None,
        source_page=source.get("page") if isinstance(source, dict) else None,
        recommendation=finding.get("recommendation", ""),
        evidence_verified=(
            page is not None and excerpt is not None
        ),
    )

    return evidence.model_dump()
