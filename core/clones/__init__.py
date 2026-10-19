"""Core Academic Tooling & Integration Platform Modules.

Includes pure-Python deterministic implementations of:
- Academic Similarity & Plagiarism (Turnitin, iThenticate, Copyleaks, Ouriginal, Grammarly)
- Duplication Detectors (jscpd, Simian, SonarQube, DataComPy, Dedupe, pandas)
- Quality & Testing (pytest, Hypothesis, mutmut, Coverage.py, Ruff/Bandit, Mypy/Pyright, pre-commit)
- Observability & MLOps (Sentry, Logfire, DVC, MLflow, Weights & Biases, Pandera, Pydantic, Crossref)
- Bibliometric Mapping (VOSviewer)
"""

from core.clones.consensus_ai import (
    ConsensusAIClone,
    ConsensusClaim,
    ConsensusMeter,
    ConsensusSynthesisResult,
    ConsensusVerdict,
    StudyDesign,
)
from core.clones.doclaynet_layout import (
    BoundingBox,
    DocLayNetCategory,
    DocLayNetClone,
    DocLayNetElement,
    LayoutAnalysisReport,
)
from core.clones.duplication_detector import (
    DataComPyClone,
    DedupeClone,
    DuplicateCloneBlock,
    JscpdClone,
    PandasDuplicationClone,
    SimianClone,
    SonarQubeClone,
)
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
from core.clones.quality_and_testing import (
    CoverageClone,
    HypothesisClone,
    LintIssue,
    Mutant,
    MutmutClone,
    MypyPyrightClone,
    PreCommitClone,
    PytestClone,
    RuffBanditClone,
    TestResult,
)
from core.clones.similarity_plagiarism import (
    CopyleaksClone,
    GrammarlyClone,
    OuriginalClone,
    SentenceTransformersAdapter,
    TurnitinClone,
    TurnitinMatch,
    TurnitinReport,
    compute_cosine_similarity,
    iThenticateClone,
    normalize_and_tokenize,
)
from core.clones.vosviewer_bibliometrics import (
    BibliometricCluster,
    BibliometricItem,
    BibliometricLink,
    VOSviewerClone,
)

__all__ = [
    # Similarity
    "compute_cosine_similarity",
    "normalize_and_tokenize",
    "SentenceTransformersAdapter",
    "TurnitinClone",
    "iThenticateClone",
    "CopyleaksClone",
    "OuriginalClone",
    "GrammarlyClone",
    "TurnitinMatch",
    "TurnitinReport",
    # Duplication
    "JscpdClone",
    "SimianClone",
    "SonarQubeClone",
    "DataComPyClone",
    "DedupeClone",
    "PandasDuplicationClone",
    "DuplicateCloneBlock",
    # Quality & Testing
    "PytestClone",
    "HypothesisClone",
    "MutmutClone",
    "CoverageClone",
    "RuffBanditClone",
    "MypyPyrightClone",
    "PreCommitClone",
    "TestResult",
    "Mutant",
    "LintIssue",
    # Observability & MLOps
    "SentryClone",
    "LogfireClone",
    "DVCClone",
    "MLflowClone",
    "WandBClone",
    "PanderaClone",
    "PydanticModel",
    "CrossrefClone",
    # Bibliometric
    "VOSviewerClone",
    "BibliometricItem",
    "BibliometricLink",
    "BibliometricCluster",
    # Consensus AI Scientific Synthesizer
    "ConsensusAIClone",
    "ConsensusVerdict",
    "StudyDesign",
    "ConsensusClaim",
    "ConsensusMeter",
    "ConsensusSynthesisResult",
    # DocLayNet Layout
    "BoundingBox",
    "DocLayNetCategory",
    "DocLayNetClone",
    "DocLayNetElement",
    "LayoutAnalysisReport",
]
