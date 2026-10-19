from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, List


@dataclass
class CheckResult:
    checker_name: str
    score: float                 # 0.0 - 1.0 (semakin tinggi semakin mirip/AI)
    verdict: str                 # "clean" | "suspicious" | "plagiarized" | "ai_generated"
    matched_segments: List[dict[str, Any]] = field(default_factory=list)  # [{"text": ..., "source": ..., "similarity": ...}]
    evidence_refs: List[str] = field(default_factory=list)      # referensi ke lokasi di dokumen (halaman/paragraf)
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseChecker(ABC):
    name: str = "base_checker"

    @abstractmethod
    def check(self, text: str, **kwargs: Any) -> CheckResult:
        """Jalankan pemeriksaan pada teks dan kembalikan hasil terstruktur."""
        ...
