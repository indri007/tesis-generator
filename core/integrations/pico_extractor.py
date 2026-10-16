"""PICO (Population, Intervention, Comparison, Outcome) Extraction Engine.

Extracts research question components from abstract, problem statements (Rumusan Masalah),
and methodology sections with verifiable source text quotes and confidence scoring.
Strictly avoids hallucination by returning None for unmentioned components.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class PICOComponent:
    name: str  # Population | Intervention | Comparison | Outcome
    value: str | None
    source_quote: str
    confidence: float
    is_present: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class PICOResult:
    population: PICOComponent
    intervention: PICOComponent
    comparison: PICOComponent
    outcome: PICOComponent
    source_text_snippet: str
    is_complete: bool  # True if all 4 are present

    def to_dict(self) -> dict[str, Any]:
        return {
            "population": self.population.to_dict(),
            "intervention": self.intervention.to_dict(),
            "comparison": self.comparison.to_dict(),
            "outcome": self.outcome.to_dict(),
            "is_complete": self.is_complete,
            "source_text_snippet": self.source_text_snippet,
        }


def extract_pico_from_text(text: str) -> PICOResult:
    """Extracts PICO components with exact quote ground-truth verification."""
    def empty_comp(name: str) -> PICOComponent:
        return PICOComponent(
            name=name, value=None, source_quote="", confidence=0.0, is_present=False
        )
    if not text or not text.strip():
        return PICOResult(
            population=empty_comp("Population"),
            intervention=empty_comp("Intervention"),
            comparison=empty_comp("Comparison"),
            outcome=empty_comp("Outcome"),
            source_text_snippet="",
            is_complete=False,
        )

    pop_val: str | None = None
    pop_quote: str = ""
    int_val: str | None = None
    int_quote: str = ""
    comp_val: str | None = None
    comp_quote: str = ""
    out_val: str | None = None
    out_quote: str = ""

    # Phase 1: Syntactic-semantic relationship parsing ("pengaruh X terhadap Y [dibandingkan C] [pada P]")
    rel_match = re.search(
        r"(?:pengaruh|dampak|efektivitas|hubungan\s+antara)\s+(?P<intervention>.+?)\s+(?:terhadap|dan)\s+(?P<rest>[^\.\n;\?]+)",
        text,
        re.IGNORECASE,
    )
    if rel_match:
        full_match_text = rel_match.group(0).strip()
        i_cand = rel_match.group("intervention").strip().strip(".,;:()")
        rest = rel_match.group("rest").strip()

        int_val = i_cand
        int_quote = full_match_text

        # Check for comparison clause ("dibandingkan dengan C")
        m_comp = re.search(
            r"\s+(?:dibandingkan\s+dengan|dibandingkan|versus|vs\.?)\s+(?P<comp>.+)",
            rest,
            re.IGNORECASE,
        )
        if m_comp:
            out_val = rest[: m_comp.start()].strip().strip(".,;:()")
            out_quote = full_match_text
            comp_rest = m_comp.group("comp").strip()

            # In comparison rest, check for population clause ("pada P")
            m_pop = re.search(r"\s+(?:pada|kepada|di\s+kalangan)\s+(?P<pop>.+)", comp_rest, re.IGNORECASE)
            if m_pop:
                comp_val = comp_rest[: m_pop.start()].strip().strip(".,;:()")
                comp_quote = m_comp.group(0).strip()
                pop_val = m_pop.group("pop").strip().strip(".,;:()")
                pop_quote = m_pop.group(0).strip()
            else:
                comp_val = comp_rest.strip().strip(".,;:()")
                comp_quote = m_comp.group(0).strip()
        else:
            # Check for population clause in rest
            m_pop = re.search(r"\s+(?:pada|kepada|di\s+kalangan)\s+(?P<pop>.+)", rest, re.IGNORECASE)
            if m_pop:
                out_val = rest[: m_pop.start()].strip().strip(".,;:()")
                out_quote = full_match_text
                pop_val = m_pop.group("pop").strip().strip(".,;:()")
                pop_quote = m_pop.group(0).strip()
            else:
                out_val = rest.strip().strip(".,;:()")
                out_quote = full_match_text

    # Phase 2: Independent population extraction if not yet discovered
    if not pop_val:
        pop_patterns = [
            r"(?:populasi|sampel|responden|partisipan|subyek)\s*(?:penelitian)?\s*(?:terdiri\s+dari|adalah|yaitu|yakni|sebanyak)?\s*([^\.\n;]{4,80}(?:orang|responden|mahasiswa|pengguna|audiens|masyarakat|pelanggan)?)",
            r"(?:kepada|pada|di\s+kalangan)\s+([^\.\n;]{4,60}(?:mahasiswa|audiens|pengguna|pelanggan|konsumen|karyawan|masyarakat)[^\.\n;]{0,30})",
            r"(?:among|in|with)\s+([^\.\n;]{4,60}(?:patients|students|users|consumers|audiences|respondents|participants))",
            r"(?:population|sample)\s*(?:consisted\s+of|is|was)\s*([^\.\n;]{4,80})",
        ]
        for pat in pop_patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                cand = m.group(1).strip().strip(".,;:()")
                if len(cand) >= 4 and m.group(0) in text:
                    pop_val = cand
                    pop_quote = m.group(0).strip()
                    break

    # Phase 3: Independent comparison extraction if not yet discovered
    if not comp_val:
        comp_patterns = [
            r"(?:dibandingkan\s+dengan|daripada|dibandingkan)\s+([^\.\n;]{4,60})",
            r"(?:kelompok\s+kontrol|metode\s+konvensional|kondisi\s+kontrol|tanpa\s+perlakuan)",
            r"(?:compared\s+to|compared\s+with|versus|vs\.?)\s+([^\.\n;]{4,60})",
            r"(?:control\s+group|conventional\s+method|placebo)",
        ]
        for pat in comp_patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                cand = m.group(1).strip().strip(".,;:()") if m.lastindex and m.lastindex >= 1 else m.group(0).strip()
                if len(cand) >= 3 and m.group(0) in text:
                    comp_val = cand
                    comp_quote = m.group(0).strip()
                    break

    # Assemble components with strict evidence verification
    pop_comp = (
        PICOComponent(name="Population", value=pop_val, source_quote=pop_quote, confidence=0.85, is_present=True)
        if pop_val and pop_quote in text
        else empty_comp("Population")
    )
    int_comp = (
        PICOComponent(name="Intervention", value=int_val, source_quote=int_quote, confidence=0.90, is_present=True)
        if int_val and int_quote in text
        else empty_comp("Intervention")
    )
    comp_comp = (
        PICOComponent(name="Comparison", value=comp_val, source_quote=comp_quote, confidence=0.80, is_present=True)
        if comp_val and comp_quote in text
        else empty_comp("Comparison")
    )
    out_comp = (
        PICOComponent(name="Outcome", value=out_val, source_quote=out_quote, confidence=0.90, is_present=True)
        if out_val and out_quote in text
        else empty_comp("Outcome")
    )

    is_complete = (
        pop_comp.is_present
        and int_comp.is_present
        and comp_comp.is_present
        and out_comp.is_present
    )

    return PICOResult(
        population=pop_comp,
        intervention=int_comp,
        comparison=comp_comp,
        outcome=out_comp,
        source_text_snippet=text[:250].strip(),
        is_complete=is_complete,
    )
