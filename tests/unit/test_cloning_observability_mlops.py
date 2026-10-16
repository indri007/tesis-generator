"""Unit tests for Observability, MLOps, Data Quality & Metadata Clones (Tools 43–50)."""

import pytest
from core.clones.observability_mlops import (
    CrossrefClone,
    DVCClone,
    LogfireClone,
    MLflowClone,
    PanderaClone,
    PydanticModel,
    SentryClone,
    WandBClone,
)


def test_sentry_clone_exception_and_breadcrumbs():
    sentry = SentryClone(environment="test")
    sentry.add_breadcrumb(category="auth", message="User initiated login")
    sentry.add_breadcrumb(category="parser", message="Parsing document started")

    try:
        raise ValueError("Simulated parsing crash")
    except ValueError as err:
        event_id = sentry.capture_exception(err, tags={"document_id": "DOC-101"})

    events = sentry.get_events()
    assert len(events) == 1
    ev = events[0]
    assert ev["event_id"] == event_id
    assert ev["exception_type"] == "ValueError"
    assert "Simulated parsing crash" in ev["message"]
    assert len(ev["breadcrumbs"]) == 2
    assert ev["tags"]["document_id"] == "DOC-101"


def test_logfire_clone_tracing_spans_and_logs():
    logfire = LogfireClone()
    logfire.info("System initializing", component="test_suite")

    with logfire.span("evaluate_thesis_chapter", chapter=1, word_count=2500) as sp:
        # simulate work
        res = 40 + 2

    assert res == 42
    spans = logfire.get_spans()
    assert len(spans) == 1
    assert spans[0]["name"] == "evaluate_thesis_chapter"
    assert spans[0]["status"] == "OK"
    assert spans[0]["duration_ms"] >= 0.0
    assert spans[0]["attributes"]["chapter"] == 1


def test_dvc_clone_tracking_and_integrity():
    dvc = DVCClone()
    synthetic_data = "Chapter 1: Academic introduction text content."
    meta = dvc.track_file(synthetic_data, version="2.0")

    assert meta["version"] == "2.0"
    assert len(meta["sha256"]) == 64

    # Verify matching hash
    is_valid = dvc.verify_data_integrity(synthetic_data, meta["sha256"])
    assert is_valid is True

    # Verify corrupted data fails
    is_corrupted = dvc.verify_data_integrity("Altered content", meta["sha256"])
    assert is_corrupted is False

    # Pipeline stage registration
    stage = dvc.define_pipeline_stage("audit_eval", "python audit.py", deps=["doc.docx"], outs=["eval.json"])
    assert stage["cmd"] == "python audit.py"


def test_mlflow_clone_runs_and_metrics():
    mlflow = MLflowClone(experiment_name="Thesis_Accuracy_Benchmark")

    with mlflow.start_run("Epoch_Run_1") as run:
        mlflow.log_param("learning_rate", 0.001)
        mlflow.log_param("batch_size", 32)
        mlflow.log_metric("f1_score", 0.88, step=1)
        mlflow.log_metric("f1_score", 0.92, step=2)
        mlflow.log_artifact("workspace/benchmark.json")

    assert run.status == "FINISHED"
    assert run.params["learning_rate"] == 0.001
    assert len(run.metrics["f1_score"]) == 2
    assert run.metrics["f1_score"][1]["value"] == 0.92
    assert "workspace/benchmark.json" in run.artifacts


def test_wandb_clone_telemetry_and_summary():
    wandb = WandBClone()
    wandb.init(project="thesis-auditor", name="run-001", config={"model": "deepseek-r1"})
    assert wandb.is_active is True

    wandb.log({"accuracy": 89.5, "kappa": 0.65}, step=1)
    wandb.log({"accuracy": 92.1, "kappa": 0.72}, step=2)

    res = wandb.finish()
    assert res["project"] == "thesis-auditor"
    assert res["steps_logged"] == 2
    assert res["summary"]["accuracy"] == 92.1
    assert res["summary"]["kappa"] == 0.72


def test_pandera_clone_schema_validation():
    schema = PanderaClone.DataFrameSchema(
        columns={
            "finding_id": PanderaClone.Column(str),
            "severity_score": PanderaClone.Column(int, checks=[lambda x: 0 <= x <= 100]),
            "description": PanderaClone.Column(str, nullable=True),
        }
    )

    valid_rows = [
        {"finding_id": "F-01", "severity_score": 75, "description": "Margin mismatch"},
        {"finding_id": "F-02", "severity_score": 10, "description": None},
    ]
    is_valid, errors = schema.validate(valid_rows)
    assert is_valid is True
    assert len(errors) == 0

    invalid_rows = [
        {"finding_id": "F-03", "severity_score": 150, "description": "Out of range"},  # Check fails
        {"finding_id": 999, "severity_score": 20, "description": "Wrong type"},       # Type fails
    ]
    is_valid_inv, errors_inv = schema.validate(invalid_rows)
    assert is_valid_inv is False
    assert len(errors_inv) >= 2


def test_pydantic_clone_structure_and_coercion():
    class ThesisDocumentModel(PydanticModel):
        title: str
        pages: int
        is_published: bool
        doi: str = "10.1016/j.default.2024"

    doc = ThesisDocumentModel(
        title="AI Analysis in Journalism",
        pages="85",             # Tests auto-coercion from str to int
        is_published=True,
    )

    assert doc.pages == 85
    assert doc.doi == "10.1016/j.default.2024"

    dump = doc.model_dump()
    assert dump["title"] == "AI Analysis in Journalism"
    assert dump["pages"] == 85
    assert dump["is_published"] is True

    # Missing required field raises ValueError
    with pytest.raises(ValueError):
        ThesisDocumentModel(title="Incomplete")


def test_crossref_clone_doi_and_currency():
    # Valid DOIs
    assert CrossrefClone.validate_doi("10.1016/j.tele.2023.102045") is True
    assert CrossrefClone.validate_doi("https://doi.org/10.1016/j.ipm.2024.103688") is True

    # Invalid DOIs
    assert CrossrefClone.validate_doi("invalid_doi_123") is False
    assert CrossrefClone.validate_doi(None) is False

    # Currency verification (MIKOM 2021-2026)
    assert CrossrefClone.verify_publication_currency(2023) is True
    assert CrossrefClone.verify_publication_currency(2026) is True
    assert CrossrefClone.verify_publication_currency(2018) is False  # Older than 5 years

    # Offline deposit verification
    assert CrossrefClone.verify_deposit(
        doi="10.1016/j.tele.2023.102045",
        title="AI-Driven News Production in Digital Journalism",
        year=2023,
    ) is True
