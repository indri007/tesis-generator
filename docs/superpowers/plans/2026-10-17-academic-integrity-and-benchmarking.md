# Academic Document Integrity Engine & Quality Gate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the Academic Document Integrity Engine, Benchmark Evaluation Framework, and Manuscript Quality Gate for `/Users/jevin/AI-Thesis-Generator` with zero heavy model downloads, reproducible evaluation, and backward-compatible Streamlit UI integration.

**Architecture:**
The solution extends the pure-Python lexical engine by introducing:
1. `core/evaluation/document_integrity_engine.py` to handle document section segmentation, citation reconciliation via `parsers/citation_parser.py`, n-gram shingle Jaccard, and selective section exclusion (bibliography & direct quotes).
2. `core/evaluation/similarity_benchmark.py` providing a golden academic evaluation dataset and threshold sensitivity matrix.
3. `core/evaluation/manuscript_quality_gate.py` providing structural, placeholder, and caption integrity gates prior to export.
4. Seamless Streamlit UI wiring in `engines/similarity_auditor.py` and `app.py`.

**Tech Stack:** Python 3.12, pytest, python-docx, pypdf/pymupdf, Streamlit, dataclasses, standard library regex & collections.

## Global Constraints

- Strictly NO commits, pushes, tags, or remote deployments ("Jangan commit atau push").
- No new third-party dependencies added to requirements.txt or pyproject.toml.
- Zero neural network model downloads during test execution or local runtime.
- Maintain 100% backward compatibility with all 238 existing passing tests.
- Maintain academic disclaimer: lexical metrics must never be labeled as "proof of plagiarism" or "AI probability".
- Evidence before assertions: test results must reflect executed CLI command outputs.

---

### Task 1: Academic Document Integrity Engine Core

**Files:**
- Create: `core/evaluation/document_integrity_engine.py`
- Test: `tests/unit/test_document_integrity_engine.py`

**Interfaces:**
- Consumes:
  - `core.clones.similarity_plagiarism.compute_cosine_similarity`
  - `core.clones.similarity_plagiarism.normalize_and_tokenize`
  - `parsers.citation_parser.audit_citations`
  - `parsers.citation_parser.CitationAuditResult`
- Produces:
  - `SectionSegment(name: str, text: str, is_excluded: bool)`
  - `CitationReconciliationItem(author_year: str, status: str, location: str, context: str)`
  - `AcademicIntegrityReport(cosine_sim: float, shingle_jaccard: float, token_jaccard: float, ...)`
  - `run_academic_integrity_audit(text_doc: str, text_ref: str | None = None, exclude_bib: bool = True, exclude_quotes: bool = False) -> AcademicIntegrityReport`

- [ ] **Step 1: Write unit tests for document integrity engine**
Create `tests/unit/test_document_integrity_engine.py` verifying section segmentation, direct quote stripping, n-gram shingling, citation reconciliation, and report generation.

- [ ] **Step 2: Run test to verify it fails**
Run: `pytest tests/unit/test_document_integrity_engine.py -q`
Expected: FAIL with ModuleNotFoundError or ImportError.

- [ ] **Step 3: Implement core/evaluation/document_integrity_engine.py**
Implement section parsing, quote filtering, n-gram word shingling Jaccard, citation audit hook, and structured reporting.

- [ ] **Step 4: Run test to verify it passes**
Run: `pytest tests/unit/test_document_integrity_engine.py -q`
Expected: PASS

---

### Task 2: Similarity Benchmark Framework & Golden Evaluation Dataset

**Files:**
- Create: `core/evaluation/similarity_benchmark.py`
- Test: `tests/unit/test_similarity_benchmark.py`

**Interfaces:**
- Consumes:
  - `core.evaluation.document_integrity_engine.run_academic_integrity_audit`
  - `core.clones.similarity_plagiarism.compute_cosine_similarity`
- Produces:
  - `BenchmarkPair(pair_id: str, text_a: str, text_b: str, expected_similar: bool, category: str, description: str)`
  - `ThresholdMetric(threshold: float, tp: int, fp: int, tn: int, fn: int, precision: float, recall: float, f1: float, accuracy: float)`
  - `GOLDEN_SIMILARITY_DATASET: list[BenchmarkPair]`
  - `evaluate_similarity_thresholds(pairs: list[BenchmarkPair] | None = None, thresholds: list[float] | None = None) -> list[ThresholdMetric]`

- [ ] **Step 1: Write unit tests for similarity benchmark**
Create `tests/unit/test_similarity_benchmark.py` asserting dataset completeness (all categories present: identical, reordered, paraphrase, synonyms, boilerplate, disjoint, empty) and evaluation matrix calculation.

- [ ] **Step 2: Run test to verify it fails**
Run: `pytest tests/unit/test_similarity_benchmark.py -q`
Expected: FAIL.

- [ ] **Step 3: Implement core/evaluation/similarity_benchmark.py**
Implement dataset of academic thesis pairs, classification metric calculations, and threshold sensitivity analysis.

- [ ] **Step 4: Run test to verify it passes**
Run: `pytest tests/unit/test_similarity_benchmark.py -q`
Expected: PASS

---

### Task 3: Manuscript Quality Gate

**Files:**
- Create: `core/evaluation/manuscript_quality_gate.py`
- Test: `tests/unit/test_manuscript_quality_gate.py`

**Interfaces:**
- Consumes:
  - Text from `models.document_model.ParsedDocument` or raw manuscript string
- Produces:
  - `QualityGateStatus(Enum: PASS, PASS_WITH_WARNINGS, FAIL)`
  - `QualityCheckItem(check_id: str, name: str, status: str, message: str, details: list[str])`
  - `QualityGateReport(status: QualityGateStatus, score: int, items: list[QualityCheckItem], can_export: bool)`
  - `ManuscriptQualityGate.evaluate(text: str) -> QualityGateReport`

- [ ] **Step 1: Write unit tests for manuscript quality gate**
Create `tests/unit/test_manuscript_quality_gate.py` testing complete manuscripts, manuscripts missing Bab 4/5, draft manuscripts with `TODO`/`[insert citation]`/`lorem ipsum`, and uncaptioned figures.

- [ ] **Step 2: Run test to verify it fails**
Run: `pytest tests/unit/test_manuscript_quality_gate.py -q`
Expected: FAIL.

- [ ] **Step 3: Implement core/evaluation/manuscript_quality_gate.py**
Implement regex and structural scanners for required thesis chapters, draft placeholders, and caption integrity.

- [ ] **Step 4: Run test to verify it passes**
Run: `pytest tests/unit/test_manuscript_quality_gate.py -q`
Expected: PASS

---

### Task 4: Streamlit UI Integration

**Files:**
- Modify: `engines/similarity_auditor.py`
- Modify: `app.py`
- Test: `tests/unit/test_similarity_auditor.py`

**Interfaces:**
- Consumes:
  - `core.evaluation.document_integrity_engine.run_academic_integrity_audit`
  - `core.evaluation.manuscript_quality_gate.ManuscriptQualityGate`
- Produces:
  - UI options: exclusion checkboxes for Bibliography & Direct Quotes
  - UI metric card: 3-gram Shingle Jaccard
  - UI tab: Citation & Bibliography Reconciliation
  - Quality Gate audit expander before export in Tab 5 (Auto-Reviser)

- [ ] **Step 1: Update test_similarity_auditor.py to cover new options and export fields**
Add test cases for section exclusion, shingle jaccard computation, and citation reconciliation summary.

- [ ] **Step 2: Enhance engines/similarity_auditor.py and app.py**
Wire `document_integrity_engine` and `manuscript_quality_gate` into Streamlit components.

- [ ] **Step 3: Run pytest on test_similarity_auditor.py**
Run: `pytest tests/unit/test_similarity_auditor.py -q`
Expected: PASS

---

### Task 5: End-to-End Regression, Linter, and Final Certification

- [ ] **Step 1: Run full pytest suite across entire repository**
Run: `pytest -q`
Expected: 245+ passed, 0 failures.

- [ ] **Step 2: Run ruff check and compileall**
Run: `PYENV_VERSION=3.12.7 ruff check .` and `python3 -m compileall -q app.py core engines`
Expected: 0 errors.

- [ ] **Step 3: Check git status and diff**
Verify no unwanted files, no git commits made, working tree clean of untracked junk.
