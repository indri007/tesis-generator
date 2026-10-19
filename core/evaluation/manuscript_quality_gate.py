"""Manuscript Quality Gate & Pre-Export Structural Validator.

Audits academic thesis drafts prior to final export or submission:
- Systematic verification of mandatory chapters (Bab 1-5, Daftar Pustaka).
- Exhaustive regex detection of unresolved drafting placeholders (TODO, TBD, [insert ...], lorem ipsum).
- Cross-reference pairing of table and figure mentions against explicit captions.
- Actionable quality scoring and gating decision (PASS, PASS_WITH_WARNINGS, FAIL).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class QualityGateDecision(str, Enum):
    PASS = "PASS"
    PASS_WITH_WARNINGS = "PASS_WITH_WARNINGS"
    FAIL = "FAIL"


@dataclass
class PlaceholderOccurrence:
    """Details of a leftover drafting placeholder found in the manuscript."""

    raw: str
    category: str
    line_number: int | None
    preview: str


@dataclass
class QualityGateReport:
    """Pre-export evaluation report with actionable findings and checklist."""

    decision: QualityGateDecision
    score: int
    can_export: bool
    missing_chapters: list[str]
    placeholders_found: list[PlaceholderOccurrence]
    unpaired_captions: list[str]
    structural_checks: dict[str, bool]
    checklist_items: list[dict[str, Any]] = field(default_factory=list)
    summary_message: str = ""


class ManuscriptQualityGate:
    """Engine verifying manuscript completeness, academic layout integrity, and draft cleanliness."""

    MANDATORY_CHAPTERS: list[tuple[str, str]] = [
        ("Bab I (Pendahuluan)", r"\b(?:BAB\s+(?:I\b|1\b)|PENDAHULUAN)\b"),
        ("Bab II (Tinjauan Pustaka)", r"\b(?:BAB\s+(?:II\b|2\b)|TINJAUAN\s+PUSTAKA|LANDASAN\s+TEORI)\b"),
        ("Bab III (Metode Penelitian)", r"\b(?:BAB\s+(?:III\b|3\b)|METODE\s+PENELITIAN)\b"),
        ("Bab IV (Hasil dan Pembahasan)", r"\b(?:BAB\s+(?:IV\b|4\b)|HASIL\s+DAN\s+PEMBAHASAN)\b"),
        ("Bab V (Penutup / Kesimpulan)", r"\b(?:BAB\s+(?:V\b|5\b)|PENUTUP|KESIMPULAN)\b"),
        ("Daftar Pustaka", r"\b(?:DAFTAR\s+PUSTAKA|REFERENCES)\b"),
    ]

    PLACEHOLDER_RULES: list[tuple[str, str]] = [
        ("EXPLICIT_TODO", r"\b(?:TODO|TBD|FIXME|XXX)\b"),
        ("INSERT_DIRECTIVE", r"\[(?:insert|isi|tulis|masukkan|tambahkan)[^\]]*\]"),
        ("DUMMY_LOREM", r"\b(?:lorem\s+ipsum|dolor\s+sit\s+amet)\b"),
        ("UNRESOLVED_METRIC", r"\b(?:XX%|YY%|0\.000)\b"),
    ]

    @classmethod
    def evaluate(cls, text: str) -> QualityGateReport:
        if not text or not text.strip():
            return QualityGateReport(
                decision=QualityGateDecision.FAIL,
                score=0,
                can_export=False,
                missing_chapters=[name for name, _ in cls.MANDATORY_CHAPTERS],
                placeholders_found=[],
                unpaired_captions=[],
                structural_checks={name: False for name, _ in cls.MANDATORY_CHAPTERS},
                summary_message="Naskah kosong atau tidak dapat diekstraksi teksnya.",
            )

        # 1. Structural checks
        missing: list[str] = []
        checks: dict[str, bool] = {}
        checklist: list[dict[str, Any]] = []

        for name, pattern in cls.MANDATORY_CHAPTERS:
            present = bool(re.search(pattern, text, re.IGNORECASE))
            checks[name] = present
            checklist.append({
                "item": name,
                "status": "PASS" if present else "ERROR",
                "detail": "Ditemukan pada naskah" if present else "Tidak ditemukan pada naskah",
            })
            if not present:
                missing.append(name)

        # 2. Scanning for draft placeholders
        placeholders: list[PlaceholderOccurrence] = []
        lines = text.splitlines()

        for line_idx, line in enumerate(lines, start=1):
            for category, pat in cls.PLACEHOLDER_RULES:
                for match in re.finditer(pat, line, re.IGNORECASE):
                    placeholders.append(
                        PlaceholderOccurrence(
                            raw=match.group(0),
                            category=category,
                            line_number=line_idx,
                            preview=line.strip()[:100],
                        )
                    )

        # 3. Caption and Figure/Table cross-referencing
        # Find in-text mentions: "Tabel 4.1", "Gambar 2.3", "Bagan 1.2"
        mentions = set(re.findall(r"\b(?:Tabel|Gambar|Bagan)\s+(\d+\.\d+)\b", text, re.IGNORECASE))
        # Find explicit caption declarations: "Tabel 4.1: Distribusi..." or "Tabel 4.1. ..."
        captions = set(re.findall(r"(?m)^\s*(?:Tabel|Gambar|Bagan)\s+(\d+\.\d+)\s*[:\.]", text, re.IGNORECASE))

        unpaired: list[str] = []
        for m in sorted(mentions):
            if m not in captions:
                unpaired.append(f"Tabel/Gambar {m}")

        # 4. Scoring calculation
        # Max score: 100
        score = 100
        # Missing chapter penalty: 15 pts each
        score -= len(missing) * 15
        # Placeholder penalty: 5 pts each (capped at 25)
        score -= min(25, len(placeholders) * 5)
        # Unpaired caption penalty: 4 pts each (capped at 15)
        score -= min(15, len(unpaired) * 4)

        score = max(0, min(100, score))

        # 5. Gating Decision
        # Missing Bab 1-5 or score < 60 constitutes a FAIL that blocks final thesis submission
        critical_missing = [ch for ch in missing if "Bab" in ch]
        if critical_missing or score < 60:
            decision = QualityGateDecision.FAIL
            can_export = False
            summary = (
                f"Naskah belum memenuhi standar kelulusan quality gate (Skor {score}/100). "
                f"Bab wajib berikut belum lengkap: {', '.join(critical_missing)}."
            )
        elif score < 85 or placeholders:
            decision = QualityGateDecision.PASS_WITH_WARNINGS
            can_export = True
            summary = (
                f"Naskah memenuhi syarat minimal ekspor dengan catatan (Skor {score}/100). "
                f"Terdapat {len(placeholders)} placeholder draf yang perlu ditinjau sebelum sidang."
            )
        else:
            decision = QualityGateDecision.PASS
            can_export = True
            summary = f"Naskah lulus Quality Gate secara prima (Skor {score}/100) tanpa cacat struktural kritis."

        return QualityGateReport(
            decision=decision,
            score=score,
            can_export=can_export,
            missing_chapters=missing,
            placeholders_found=placeholders,
            unpaired_captions=unpaired,
            structural_checks=checks,
            checklist_items=checklist,
            summary_message=summary,
        )
