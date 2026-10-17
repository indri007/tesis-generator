# Design Specification: Full Institutional Tooling & Cloning Suite for Academic Platform

**Date:** 2026-10-16  
**Status:** Approved  
**Author:** Antigravity AI  
**Repository:** `AI-Thesis-Generator` (UPN Veteran Jawa Timur, FISIP MIKOM 2026)

---

## 1. Overview & Objective

This specification details the architecture, contracts, and deterministic execution of the comprehensive tool-cloning suite requested by the user under binary command execution (**"dlm perintah binner"** / **BIT 17**).

The system clones and implements the operational capabilities of top-tier academic, software engineering, testing, and observability platforms:
1. **Academic Similarity & Plagiarism Checking**: Turnitin, iThenticate, Copyleaks, Ouriginal, Grammarly.
2. **Code & Data Duplication Detection**: jscpd, Pylint (duplicate checker), Ruff, SonarQube, Simian, DataComPy, Dedupe, pandas duplication.
3. **Scientific Literature & Research AI**: Perplexity, Elicit, Consensus, SciSpace, ResearchRabbit, Semantic Scholar, OpenAlex, Crossref.
4. **Python Testing, Quality & Security**: pytest, Hypothesis, mutmut, Coverage.py, Ruff, Mypy, Pyright, Bandit, Pylint, pre-commit.
5. **Observability, MLOps & Data Validation**: Sentry, Logfire, DVC, MLflow, Weights & Biases (W&B), Pandera, Pydantic, Crossref.

All clones are implemented in **pure, deterministic Python** with zero cloud credentials required, designed to operate offline in reproducible research environments while producing real, verified metrics and outputs.

---

## 2. Architectural Pillars & Module Layout

### Pillar 1: Similarity & Plagiarism Clones (`core/clones/similarity_plagiarism.py`)
- **TurnitinClone**:
  - Implements n-gram shingling (e.g. 5-gram token sequences) and Jaccard / Overlap similarity calculation.
  - Generates Similarity Index (%) with color bands:
    - Blue: 0%
    - Green: 1%–24%
    - Yellow: 25%–49%
    - Orange: 50%–74%
    - Red: 75%–100%
  - Filters out direct quotations enclosed in quotation marks and bibliography sections.
- **iThenticateClone**:
  - Publication-grade plagiarism checking excluding standard methodology formulas and acknowledgments.
- **CopyleaksClone**:
  - Sentence rearrangement detection and AI-synthesized text likelihood scoring (perplexity & burstiness variance).
- **OuriginalClone**:
  - Document-to-document verbatim and paraphrase match matrix.
- **GrammarlyClone**:
  - Text quality auditing: Academic formality score, passive voice ratio, wordiness flags, punctuation anomalies.

### Pillar 2: Duplication Detection Clones (`core/clones/duplication_detector.py`)
- **JscpdClone / SimianClone**:
  - Token-level duplicate code finder for Python ASTs (ignoring comments and whitespace).
- **SonarQubeClone**:
  - Measures cognitive complexity, code smell index, and percentage of duplicated lines.
- **DataComPyClone**:
  - Compares two structured datasets (dicts or pandas DataFrames) and details row/column matches and value drifts.
- **DedupeClone**:
  - Record linkage and entity deduplication on author names and publication titles.
- **PandasDuplicationClone**:
  - Tabular duplicate detection for dataset rows with subset key checks.

### Pillar 3: Scientific Literature & Research AI (`core/integrations/scientific_engines.py`)
- **PerplexityEngine**:
  - Synthesizes search queries into answers with numbered inline citations `[1]`, `[2]` mapped to grounded sources.
- **ElicitEngine**:
  - Extracts research questions, study design (RCT, Meta-analysis, Empirical), sample size ($n$), and key findings.
- **ConsensusEngine**:
  - Evaluates research claims and calculates Consensus Meter percentages (e.g. 85% Yes, 10% Possibly, 5% No).
- **SciSpaceEngine**:
  - Simplifies complex papers into plain-language takeaways and methodology breakdowns.
- **ResearchRabbitEngine**:
  - Constructs citation network graphs (nodes and edges) from seed DOIs.
- **SemanticScholarEngine**:
  - Calculates influential citation counts and generates automated TLDR summaries.
- **OpenAlexEngine**:
  - Maps publications to global concept trees, Open Access status, and institution ROR IDs.
- **CrossrefEngine**:
  - Strictly validates international DOI formats (`10.xxxx/...`) and enforces 5-year currency (2021–2026).

### Pillar 4: Python Testing, Quality & Security (`core/clones/quality_and_testing.py`)
- **PytestRunner**: Discovers and runs tests with timing and failure diagnostic reporting.
- **HypothesisClone**: Property-based input generator validating invariants under fuzz inputs.
- **MutmutClone**: Performs AST mutations (e.g., swapping `>` for `<=`, `==` for `!=`) to test test-suite resilience.
- **CoverageClone**: Measures line-by-line statement execution coverage.
- **RuffClone / BanditClone**: Static syntax analysis and security vulnerability scan (e.g., checking for `eval`, hardcoded secrets, wildcard imports).
- **MypyPyrightClone**: Inspects type annotations on functions and classes.
- **PreCommitRunner**: Orchestrates sequential pre-commit quality hooks.

### Pillar 5: Observability, MLOps & Data Validation (`core/clones/observability_mlops.py`)
- **SentryClone**: Captures exceptions, stack traces, breadcrumb trails, environment tags, and generates unique event IDs.
- **LogfireClone**: Context manager `span(name)` profiling latency in milliseconds with structured logging.
- **DVCClone**: Tracks dataset versions, calculates SHA256 hashes, generates `.dvc` tracking records, and defines pipeline stages.
- **MLflowClone**: Context manager `start_run()`, logs parameters, metrics over steps, and saves artifact paths.
- **WandBClone**: `wandb.init()`, logs step-by-step metric dictionaries, updates `summary`, and finalizes runs.
- **PanderaClone**: `DataFrameSchema` enforcing column dtypes, nullability, and custom value constraints.
- **PydanticClone**: `BaseModelClone` providing typed schema enforcement, type coercion, and JSON serialization.

---

## 3. Integration with 50-Gate Rayyan Consensus

Fix Gate 13 positional argument mismatch in `core/evaluation/rayyan_consensus_50_gates.py` and hook Gates 43–50 to Pillar 5:
- Gate 43: Sentry exception capture & trace verification.
- Gate 44: Logfire execution span & latency observability.
- Gate 45: DVC dataset hash integrity verification.
- Gate 46: MLflow experiment run & metric tracking.
- Gate 47: WandB telemetry & summary scoring.
- Gate 48: Pandera schema & quality validation.
- Gate 49: Pydantic document metadata validation.
- Gate 50: Crossref DOI standard & currency verification.

---

## 4. Binary Execution Script: `BIT17_FULL_CLONING_SUITE.sh`

A standalone, executable shell script (`chmod +x`) located at the repository root that:
1. Validates virtual environment (`.venv-test/bin/python`).
2. Executes live demonstrations and assertion checks for all 5 pillars.
3. Runs the automated test suites (`tests/unit/test_cloning_observability_mlops.py`, `tests/unit/test_similarity_and_duplication_clones.py`, `tests/unit/test_scientific_engines.py`, `tests/unit/test_rayyan_consensus_50_gates.py`).
4. Writes formatted execution logs to `workspace/BIT17_FULL_CLONING_SUITE.txt`.
5. Exits cleanly with status code 0 on complete pass.

---

## 5. Verification Plan

- Unit test coverage for every clone.
- End-to-end execution of `BIT17_FULL_CLONING_SUITE.sh`.
- Regression check of all existing tests (`pytest`).
