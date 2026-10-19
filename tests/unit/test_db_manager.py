"""Unit tests for DatabaseManager: SQLite foreign key enforcement, limits, and audit tracking."""

import sqlite3
from pathlib import Path

import pytest

from core.database.db_manager import DatabaseManager


@pytest.fixture
def temp_db(tmp_path: Path) -> DatabaseManager:
    """Fixture providing an isolated temporary SQLite database."""
    db_file = tmp_path / "test_thesis.db"
    mgr = DatabaseManager(db_path=db_file)
    # Register default guideline profile
    mgr.register_guideline_profile(
        profile_id="TEST_MIKOM_2026",
        university="UPN Veteran Jawa Timur",
        faculty="FISIP",
        program="Magister Ilmu Komunikasi",
        version="2026.1",
        effective_date="2026-01-01",
        config={"max_pages": 175, "margin_cm": 4.0},
    )
    return mgr


def test_foreign_key_enforcement(temp_db: DatabaseManager):
    """Verify that inserting a project with non-existent guideline_id fails due to foreign key constraint."""
    with pytest.raises(sqlite3.IntegrityError):
        temp_db.create_project(
            project_id="PROJ-001",
            title="Pengaruh Komunikasi Digital",
            author_name="Budi Santoso",
            nim="2401234567",
            guideline_id="NON_EXISTENT_GUIDELINE",
        )


def test_document_page_limit_enforcement(temp_db: DatabaseManager):
    """Verify that documents exceeding the 175-page limit are rejected."""
    temp_db.create_project(
        project_id="PROJ-001",
        title="Pengaruh Komunikasi Digital",
        author_name="Budi Santoso",
        nim="2401234567",
        guideline_id="TEST_MIKOM_2026",
    )

    # Valid document (120 pages) -> Succeeds
    temp_db.register_document(
        document_id="DOC-001",
        project_id="PROJ-001",
        file_name="tesis_valid.docx",
        file_type="DOCX",
        total_pages=120,
        word_count=42000,
        storage_path="/path/to/valid.docx",
        sha256_hash="abc123hash",
    )

    # Document exceeding limit (176 pages) -> Raises ValueError and CHECK constraint
    with pytest.raises(ValueError, match="exceeds 175 pages hard limit"):
        temp_db.register_document(
            document_id="DOC-002",
            project_id="PROJ-001",
            file_name="tesis_tebal.docx",
            file_type="DOCX",
            total_pages=176,
            word_count=65000,
            storage_path="/path/to/tebal.docx",
            sha256_hash="def456hash",
        )


def test_audit_session_and_findings_persistence(temp_db: DatabaseManager):
    """Verify recording of audit findings and computation of summary metrics."""
    temp_db.create_project(
        project_id="PROJ-001",
        title="Pengaruh Komunikasi Digital",
        author_name="Budi Santoso",
        nim="2401234567",
        guideline_id="TEST_MIKOM_2026",
    )
    temp_db.register_document(
        document_id="DOC-001",
        project_id="PROJ-001",
        file_name="tesis_valid.docx",
        file_type="DOCX",
        total_pages=100,
        word_count=40000,
        storage_path="/path/to/valid.docx",
        sha256_hash="abc123hash",
    )

    # Register rule in rule_definitions
    with temp_db.get_connection() as conn:
        conn.execute(
            """
            INSERT INTO rule_definitions (rule_id, profile_id, category, severity, field_target, operator, expectation_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            ("FORMAT_MARGIN_001", "TEST_MIKOM_2026", "Format", "ERROR", "margins.left", "equals", '{"left": 4.0}'),
        )
        conn.commit()

    sample_findings = [
        {
            "rule_id": "FORMAT_MARGIN_001",
            "category": "Format",
            "status": "ERROR",
            "page": 1,
            "section": "BAB I",
            "actual": "3.0 cm",
            "expected": "4.0 cm",
            "excerpt": "Margin kiri 3.0 cm",
            "recommendation": "Set margin kiri ke 4.0 cm",
        },
        {
            "rule_id": "FORMAT_MARGIN_001",
            "category": "Format",
            "status": "WARNING",
            "page": 2,
            "section": "BAB I",
            "actual": "Spasi 1.5",
            "expected": "Spasi 2.0",
            "excerpt": "Line spacing 1.5",
            "recommendation": "Set line spacing ke 2.0",
        },
    ]

    temp_db.record_audit_session(
        session_id="SESS-001",
        project_id="PROJ-001",
        document_id="DOC-001",
        compliance_score=85.5,
        findings=sample_findings,
        execution_time_ms=120,
    )

    summary = temp_db.get_project_summary("PROJ-001")
    assert summary is not None
    assert summary["title"] == "Pengaruh Komunikasi Digital"
    assert summary["university_name"] == "UPN Veteran Jawa Timur"
    assert summary["latest_audit"] is not None
    assert summary["latest_audit"]["compliance_score"] == 85.5
    assert summary["latest_audit"]["errors_count"] == 1
    assert summary["latest_audit"]["warnings_count"] == 1


def test_init_db_idempotency_and_migration_integrity(tmp_path: Path):
    """Verify that init_db() can be called repeatedly without throwing UNIQUE constraint errors."""
    db_file = tmp_path / "idempotent_test.db"
    mgr1 = DatabaseManager(db_path=db_file)
    # Subsequent calls (such as on Streamlit app re-runs) must be safe and idempotent
    mgr1.init_db()
    mgr1.init_db()

    # Re-instantiating another manager pointing to the same DB must succeed
    mgr2 = DatabaseManager(db_path=db_file)
    mgr2.init_db()

    with mgr2.get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT version, description FROM schema_migrations WHERE version = 1")
        row = cur.fetchone()
        assert row is not None
        assert row[0] == 1
        assert "Baseline" in row[1]

