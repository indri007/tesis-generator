# Full Institutional Tooling & Cloning Suite Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and integrate pure-Python, deterministic clones for 8 observability/MLOps tools, 5 academic similarity platforms, 6 duplication detectors, 8 scientific AI engines, and testing frameworks under a master executable binary script (`BIT17_FULL_CLONING_SUITE.sh`).

**Architecture:** Create dedicated clone modules under `core/clones/` with zero-cloud dependencies. Wire them into `core/evaluation/rayyan_consensus_50_gates.py` for comprehensive 50-gate verification. Provide an executable bash script that runs tests, outputs execution metrics to `workspace/BIT17_...txt`, and executes automated pytests.

**Tech Stack:** Python 3.11+, bash shell script, standard library (`ast`, `re`, `hashlib`, `json`, `dataclasses`, `difflib`, `contextlib`), pytest.

## Global Constraints
- Deterministic, zero-cloud dependency (no paid API keys required).
- Maintain existing tests and codebase integrity.
- Use `.venv-test/bin/python` for execution in the virtual environment.

---

### Task 1: Implement Observability & MLOps Clones (Tools 43–50)
**Files to create/modify:** `core/clones/observability_mlops.py`, `tests/unit/test_cloning_observability_mlops.py`

- [ ] Write `core/clones/observability_mlops.py` implementing `SentryClone`, `LogfireClone`, `DVCClone`, `MLflowClone`, `WandBClone`, `PanderaClone`, `PydanticClone`, `CrossrefClone`.
- [ ] Write unit tests `tests/unit/test_cloning_observability_mlops.py` verifying each of the 8 tools.
- [ ] Run pytest on `tests/unit/test_cloning_observability_mlops.py` and ensure 100% pass.
- [ ] Commit changes.

---

### Task 2: Implement Academic Similarity, Plagiarism & Duplication Clones
**Files to create/modify:** `core/clones/similarity_plagiarism.py`, `core/clones/duplication_detector.py`, `tests/unit/test_similarity_and_duplication_clones.py`

- [ ] Write `core/clones/similarity_plagiarism.py` implementing `TurnitinClone`, `iThenticateClone`, `CopyleaksClone`, `OuriginalClone`, `GrammarlyClone`.
- [ ] Write `core/clones/duplication_detector.py` implementing `JscpdClone`, `SimianClone`, `SonarQubeClone`, `DataComPyClone`, `DedupeClone`, `PandasDuplicationClone`.
- [ ] Write tests in `tests/unit/test_similarity_and_duplication_clones.py`.
- [ ] Run pytest to verify all plagiarism and duplication tests pass.
- [ ] Commit changes.

---

### Task 3: Expand Scientific Literature AI Clones
**Files to create/modify:** `core/integrations/scientific_engines.py`, `tests/unit/test_scientific_engines.py`

- [ ] Add `PerplexityEngine` to `core/integrations/scientific_engines.py` supporting grounded numbered citations and source URLs.
- [ ] Verify `ElicitEngine`, `ConsensusEngine`, `SciSpaceEngine`, `ResearchRabbitEngine`, `SemanticScholarEngine`, `OpenAlexEngine`, `CrossrefEngine`.
- [ ] Add unit tests in `tests/unit/test_scientific_engines.py` for `PerplexityEngine`.
- [ ] Run pytest on `tests/unit/test_scientific_engines.py`.
- [ ] Commit changes.

---

### Task 4: Implement Quality, Testing & CI Clones
**Files to create/modify:** `core/clones/quality_and_testing.py`, `tests/unit/test_quality_and_testing.py`

- [ ] Write `core/clones/quality_and_testing.py` implementing `HypothesisClone`, `MutmutClone`, `CoverageClone`, `RuffBanditClone`, `MypyPyrightClone`, `PreCommitRunner`.
- [ ] Write unit tests in `tests/unit/test_quality_and_testing.py`.
- [ ] Run pytest to verify all tests pass.
- [ ] Commit changes.

---

### Task 5: Fix Gate 13 & Hook Gates 43–50 in Rayyan Consensus 50 Gates
**Files to modify:** `core/evaluation/rayyan_consensus_50_gates.py`, `tests/unit/test_rayyan_consensus_50_gates.py`

- [ ] Fix Gate 13 positional argument call for `DatabaseManager.register_document()`.
- [ ] Connect Gates 43–50 to use `core/clones/observability_mlops.py`.
- [ ] Run `test_rayyan_consensus_50_gates.py` and verify all 50 gates PASS (50/50).
- [ ] Commit changes.

---

### Task 6: Master Binary Command Runner (`BIT17_FULL_CLONING_SUITE.sh`)
**Files to create:** `BIT17_FULL_CLONING_SUITE.sh`

- [ ] Write standalone executable bash script `BIT17_FULL_CLONING_SUITE.sh`.
- [ ] Set executable permission (`chmod +x BIT17_FULL_CLONING_SUITE.sh`).
- [ ] Execute the binary script and verify execution in `workspace/BIT17_FULL_CLONING_SUITE.txt`.
- [ ] Verify full test suite passes without regressions.
- [ ] Commit changes.
