"""Query Registry, Execution Snapshot, and Central Configuration Engine.

Implements Phase 1 & Section A requirements:
- Multi-query search support (#2)
- Query registry (#3)
- Search provenance (#4)
- Configuration YAML/JSON (#25)
- Query snapshot (#297)
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class QueryExecutionEntry:
    """Individual registered query execution entry."""

    query_id: str
    query_text: str
    target_database: str
    filters: dict[str, Any] = field(default_factory=dict)
    executed_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    records_retrieved: int = 0
    execution_duration_sec: float = 0.0
    status: str = "SUCCESS"
    error_message: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def create(
        cls,
        query_text: str,
        target_database: str,
        filters: dict[str, Any] | None = None,
        records_retrieved: int = 0,
        execution_duration_sec: float = 0.0,
        status: str = "SUCCESS",
        error_message: str | None = None,
    ) -> QueryExecutionEntry:
        q_norm = query_text.strip().lower()
        db_norm = target_database.strip().lower()
        qid = hashlib.sha256(f"{q_norm}:{db_norm}".encode("utf-8")).hexdigest()[:8]
        return cls(
            query_id=f"qry_{qid}",
            query_text=query_text.strip(),
            target_database=target_database,
            filters=filters or {},
            records_retrieved=records_retrieved,
            execution_duration_sec=round(execution_duration_sec, 3),
            status=status,
            error_message=error_message,
        )


@dataclass
class PipelineConfig:
    """Central configuration for literature harvesting and auditing (#25)."""

    queries: list[str] = field(default_factory=lambda: [
        "communication studies",
        "social media communication",
        "social network analysis",
        "political communication Indonesia",
        "media literacy digital",
    ])
    target_databases: list[str] = field(default_factory=lambda: [
        "Crossref",
        "OpenAlex",
        "SemanticScholar",
    ])
    min_year: int = 2021  # MIKOM 5-year currency standard
    max_year: int = 2026
    allowed_doc_types: list[str] = field(default_factory=lambda: [
        "journal-article",
        "conference-paper",
    ])
    required_quality_score: float = 40.0
    rate_limit_delay_sec: float = 1.0
    max_retries: int = 3
    backoff_factor: float = 1.5
    cache_enabled: bool = True
    output_dir: str = "data/processed"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PipelineConfig:
        return cls(
            queries=list(data.get("queries", [])),
            target_databases=list(data.get("target_databases", [])),
            min_year=int(data.get("min_year", 2021)),
            max_year=int(data.get("max_year", 2026)),
            allowed_doc_types=list(data.get("allowed_doc_types", ["journal-article", "conference-paper"])),
            required_quality_score=float(data.get("required_quality_score", 40.0)),
            rate_limit_delay_sec=float(data.get("rate_limit_delay_sec", 1.0)),
            max_retries=int(data.get("max_retries", 3)),
            backoff_factor=float(data.get("backoff_factor", 1.5)),
            cache_enabled=bool(data.get("cache_enabled", True)),
            output_dir=str(data.get("output_dir", "data/processed")),
        )

    def save_json(self, path: Path | str) -> None:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load_json(cls, path: Path | str) -> PipelineConfig:
        p = Path(path)
        if not p.exists():
            return cls()
        with open(p, "r", encoding="utf-8") as f:
            return cls.from_dict(json.load(f))


class QueryRegistry:
    """Manages executed query history and snapshots (#3, #297)."""

    def __init__(self) -> None:
        self.entries: list[QueryExecutionEntry] = []

    def register(self, entry: QueryExecutionEntry) -> None:
        self.entries.append(entry)

    def get_summary(self) -> dict[str, Any]:
        total_queries = len(self.entries)
        total_retrieved = sum(e.records_retrieved for e in self.entries)
        by_db: dict[str, int] = {}
        for e in self.entries:
            by_db[e.target_database] = by_db.get(e.target_database, 0) + e.records_retrieved

        return {
            "total_queries_executed": total_queries,
            "total_records_retrieved": total_retrieved,
            "retrieval_by_database": by_db,
            "queries": [e.to_dict() for e in self.entries],
        }

    def save_snapshot(self, path: Path | str) -> None:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(self.get_summary(), f, indent=2)
