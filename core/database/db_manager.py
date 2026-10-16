"""Database Manager: SQLite local-first storage with enforced foreign keys and WAL mode.

Complies with the approved schema specification in ADR-02 and Section 4 of Master Design.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

DEFAULT_DB_PATH = Path.home() / "AI-Thesis-Generator" / "workspace" / "tesis_check.db"

DDL_SCHEMA = """
PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;

CREATE TABLE IF NOT EXISTS guideline_profiles (
    profile_id TEXT PRIMARY KEY,
    university_name TEXT NOT NULL,
    faculty_name TEXT NOT NULL,
    program_study TEXT NOT NULL,
    version TEXT NOT NULL,
    effective_date DATE NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1 CHECK(is_active IN (0, 1)),
    config_json TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS rule_definitions (
    rule_id TEXT PRIMARY KEY,
    profile_id TEXT NOT NULL,
    category TEXT NOT NULL CHECK(category IN ('Format', 'Structure', 'Citation', 'Formula', 'Statistic', 'Journal')),
    severity TEXT NOT NULL CHECK(severity IN ('ERROR', 'WARNING', 'INFO')),
    field_target TEXT NOT NULL,
    operator TEXT NOT NULL CHECK(operator IN ('equals', 'not_equals', 'exists', 'min', 'max', 'range', 'regex', 'recalculate')),
    expectation_json TEXT NOT NULL,
    citation_source TEXT,
    page_reference INTEGER,
    FOREIGN KEY (profile_id) REFERENCES guideline_profiles(profile_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_rules_profile_cat ON rule_definitions(profile_id, category);

CREATE TABLE IF NOT EXISTS projects (
    project_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    author_name TEXT NOT NULL,
    nim TEXT,
    guideline_id TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (guideline_id) REFERENCES guideline_profiles(profile_id)
);

CREATE TABLE IF NOT EXISTS documents (
    document_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    version_number INTEGER NOT NULL DEFAULT 1,
    file_name TEXT NOT NULL,
    file_type TEXT NOT NULL CHECK(file_type IN ('DOCX', 'PDF')),
    total_pages INTEGER NOT NULL CHECK(total_pages <= 175),
    word_count INTEGER NOT NULL,
    storage_path TEXT NOT NULL,
    sha256_hash TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1 CHECK(is_active IN (0, 1)),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_docs_project ON documents(project_id);

CREATE TABLE IF NOT EXISTS in_text_citations (
    citation_id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL,
    raw_citation TEXT NOT NULL,
    author_key TEXT NOT NULL,
    publication_year INTEGER,
    page_number INTEGER,
    paragraph_index INTEGER,
    excerpt_text TEXT,
    FOREIGN KEY (document_id) REFERENCES documents(document_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_cit_doc_key ON in_text_citations(document_id, author_key);

CREATE TABLE IF NOT EXISTS reference_masters (
    doi TEXT PRIMARY KEY,
    clean_title TEXT NOT NULL,
    authors_json TEXT NOT NULL,
    publication_year INTEGER,
    journal_name TEXT,
    verification_status TEXT NOT NULL CHECK(verification_status IN ('VERIFIED_LOCAL', 'VERIFIED_ONLINE', 'UNVERIFIED')),
    source_origin TEXT NOT NULL,
    last_verified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_ref_title ON reference_masters(clean_title);

CREATE TABLE IF NOT EXISTS audit_sessions (
    session_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    document_id TEXT NOT NULL,
    compliance_score REAL NOT NULL CHECK(compliance_score BETWEEN 0.0 AND 100.0),
    total_findings INTEGER NOT NULL,
    errors_count INTEGER NOT NULL,
    warnings_count INTEGER NOT NULL,
    unverified_count INTEGER NOT NULL,
    execution_time_ms INTEGER NOT NULL,
    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE,
    FOREIGN KEY (document_id) REFERENCES documents(document_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS audit_findings (
    finding_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    rule_id TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('PASS', 'ERROR', 'WARNING', 'INFO', 'UNVERIFIED')),
    category TEXT NOT NULL,
    page_number INTEGER,
    section_name TEXT,
    actual_value TEXT,
    expected_value TEXT,
    excerpt TEXT,
    recommendation TEXT NOT NULL,
    FOREIGN KEY (session_id) REFERENCES audit_sessions(session_id) ON DELETE CASCADE,
    FOREIGN KEY (rule_id) REFERENCES rule_definitions(rule_id)
);
CREATE INDEX IF NOT EXISTS idx_findings_session_status ON audit_findings(session_id, status);

CREATE TABLE IF NOT EXISTS revision_proposals (
    proposal_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    policy_tier TEXT NOT NULL CHECK(policy_tier IN ('LOW_RISK_AUTO', 'SUBSTANTIVE_APPROVED')),
    resulting_document_id TEXT,
    status TEXT NOT NULL CHECK(status IN ('PENDING', 'APPROVED', 'REJECTED')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES audit_sessions(session_id) ON DELETE CASCADE,
    FOREIGN KEY (resulting_document_id) REFERENCES documents(document_id)
);

CREATE TABLE IF NOT EXISTS change_logs (
    log_id TEXT PRIMARY KEY,
    proposal_id TEXT NOT NULL,
    rule_id TEXT NOT NULL,
    action_type TEXT NOT NULL,
    target_location TEXT NOT NULL,
    before_state TEXT NOT NULL,
    after_state TEXT NOT NULL,
    applied_by TEXT NOT NULL CHECK(applied_by IN ('SYSTEM_AUTO', 'HUMAN_APPROVER')),
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (proposal_id) REFERENCES revision_proposals(proposal_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS schema_migrations (
    version INTEGER PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT NOT NULL
);
"""


class DatabaseManager:
    """Manages SQLite database operations with WAL and foreign key enforcement."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = Path(db_path or DEFAULT_DB_PATH)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_db()

    def get_connection(self) -> sqlite3.Connection:
        """Create connection and unconditionally enable foreign key constraints."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA journal_mode = WAL;")
        return conn

    def init_db(self) -> None:
        """Initialize database schema and migration baseline."""
        with self.get_connection() as conn:
            conn.executescript(DDL_SCHEMA)
            # Record initial migration if empty
            cur = conn.cursor()
            cur.execute(
                "INSERT OR IGNORE INTO schema_migrations (version, description) VALUES (?, ?)",
                (1, "Baseline schema for AI Thesis Generator & Reviewer"),
            )
            conn.commit()

    def register_guideline_profile(
        self,
        profile_id: str,
        university: str,
        faculty: str,
        program: str,
        version: str,
        effective_date: str,
        config: Dict[str, Any],
    ) -> None:
        """Insert or replace an institutional guideline profile."""
        with self.get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO guideline_profiles
                (profile_id, university_name, faculty_name, program_study, version, effective_date, is_active, config_json)
                VALUES (?, ?, ?, ?, ?, ?, 1, ?)
                """,
                (profile_id, university, faculty, program, version, effective_date, json.dumps(config)),
            )
            conn.commit()

    def create_project(
        self,
        project_id: str,
        title: str,
        author_name: str,
        nim: Optional[str],
        guideline_id: str,
    ) -> None:
        """Create a new thesis project bound to a guideline profile."""
        with self.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO projects (project_id, title, author_name, nim, guideline_id)
                VALUES (?, ?, ?, ?, ?)
                """,
                (project_id, title, author_name, nim, guideline_id),
            )
            conn.commit()

    def register_document(
        self,
        document_id: str,
        project_id: str,
        file_name: str,
        file_type: str,
        total_pages: int,
        word_count: int,
        storage_path: str,
        sha256_hash: str,
        version_number: int = 1,
    ) -> None:
        """Register a thesis document. Fails if total_pages > 175."""
        if total_pages > 175:
            raise ValueError(f"Document exceeds 175 pages hard limit ({total_pages} pages)")

        with self.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO documents
                (document_id, project_id, version_number, file_name, file_type, total_pages, word_count, storage_path, sha256_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (document_id, project_id, version_number, file_name, file_type, total_pages, word_count, storage_path, sha256_hash),
            )
            conn.commit()

    def record_audit_session(
        self,
        session_id: str,
        project_id: str,
        document_id: str,
        compliance_score: float,
        findings: List[Dict[str, Any]],
        execution_time_ms: int = 0,
    ) -> None:
        """Atomically record an audit session and all of its categorized findings."""
        errors_count = sum(1 for f in findings if f.get("status") == "ERROR")
        warnings_count = sum(1 for f in findings if f.get("status") == "WARNING")
        unverified_count = sum(1 for f in findings if f.get("status") == "UNVERIFIED")

        with self.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO audit_sessions
                (session_id, project_id, document_id, compliance_score, total_findings, errors_count, warnings_count, unverified_count, execution_time_ms)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (session_id, project_id, document_id, compliance_score, len(findings), errors_count, warnings_count, unverified_count, execution_time_ms),
            )

            for idx, f in enumerate(findings):
                finding_id = f"{session_id}_f{idx:03d}"
                conn.execute(
                    """
                    INSERT INTO audit_findings
                    (finding_id, session_id, rule_id, status, category, page_number, section_name, actual_value, expected_value, excerpt, recommendation)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        finding_id,
                        session_id,
                        f.get("rule_id", "GENERAL_RULE"),
                        f.get("status", "INFO"),
                        f.get("category", "General"),
                        f.get("page"),
                        f.get("section"),
                        str(f.get("actual", "")),
                        str(f.get("expected", "")),
                        str(f.get("excerpt", "")),
                        str(f.get("recommendation", "")),
                    ),
                )
            conn.commit()

    def get_project_summary(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve project information, active document, and latest audit score."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT p.*, g.university_name, g.version as guideline_version
                FROM projects p
                JOIN guideline_profiles g ON p.guideline_id = g.profile_id
                WHERE p.project_id = ?
                """,
                (project_id,),
            )
            row = cur.fetchone()
            if not row:
                return None
            result = dict(row)

            # Get latest session
            cur.execute(
                """
                SELECT session_id, compliance_score, total_findings, errors_count, warnings_count, executed_at
                FROM audit_sessions
                WHERE project_id = ?
                ORDER BY executed_at DESC LIMIT 1
                """,
                (project_id,),
            )
            sess = cur.fetchone()
            result["latest_audit"] = dict(sess) if sess else None
            return result
