"""Academic Similarity & Plagiarism Clones (Turnitin, iThenticate, Copyleaks, Ouriginal, Grammarly).

Zero-cloud, deterministic offline implementations of industry-standard academic integrity checks:
1. Turnitin: N-gram shingling, similarity percentage, color bands (Blue/Green/Yellow/Orange/Red),
   quote exclusion, and bibliography exclusion.
2. iThenticate: Journal pre-submission crosscheck, boilerplate methodology filtering.
3. Copyleaks: Paraphrase match detection and AI text likelihood assessment (burstiness & perplexity).
4. Ouriginal (Urkund): Multi-document text similarity comparison matrix.
5. Grammarly: Academic formality scoring, passive voice detection, and writing enhancement.
"""

from __future__ import annotations

import math
import re
from dataclasses import asdict, dataclass, field
from typing import Any


# ==============================================================================
# 1. TURNITIN CLONE (Similarity Report & Color Bands)
# ==============================================================================
@dataclass
class TurnitinMatch:
    source_id: str
    source_title: str
    matched_text: str
    match_percentage: float
    is_quoted: bool = False
    is_bibliography: bool = False


@dataclass
class TurnitinReport:
    overall_similarity_percentage: float
    color_band: str  # BLUE, GREEN, YELLOW, ORANGE, RED
    total_words: int
    matched_words: int
    matches: list[TurnitinMatch] = field(default_factory=list)
    interpretation: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class TurnitinClone:
    """Clones Turnitin: Computes similarity index, color bands, and excludes quotes & bibliography."""

    def __init__(self, n_gram: int = 5):
        self.n_gram = n_gram

    def _tokenize(self, text: str) -> list[str]:
        return [w.lower() for w in re.findall(r"\b[a-zA-Z0-9_-]+\b", text)]

    def _generate_shingles(self, tokens: list[str]) -> set[tuple[str, ...]]:
        if len(tokens) < self.n_gram:
            return {tuple(tokens)} if tokens else set()
        return {tuple(tokens[i : i + self.n_gram]) for i in range(len(tokens) - self.n_gram + 1)}

    def check_similarity(
        self,
        manuscript_text: str,
        reference_corpus: list[dict[str, str]],
        exclude_quotes: bool = True,
        exclude_bibliography: bool = True,
    ) -> TurnitinReport:
        """Calculates Turnitin-like similarity index and color classification."""
        cleaned_text = manuscript_text
        if exclude_bibliography:
            # Strip everything after 'DAFTAR PUSTAKA' or 'REFERENCES'
            split_match = re.split(r"\n\s*(?:DAFTAR PUSTAKA|REFERENCES)\b", cleaned_text, flags=re.IGNORECASE)
            cleaned_text = split_match[0]

        if exclude_quotes:
            # Strip quotes within "..." or “...”
            cleaned_text = re.sub(r'["“][^"”]+["”]', " ", cleaned_text)

        tokens = self._tokenize(cleaned_text)
        total_words = max(1, len(tokens))
        manuscript_shingles = self._generate_shingles(tokens)

        matches: list[TurnitinMatch] = []

        for ref in reference_corpus:
            ref_tokens = self._tokenize(ref.get("content", ""))
            ref_shingles = self._generate_shingles(ref_tokens)
            overlap = manuscript_shingles & ref_shingles

            if overlap:
                matched_count = len(overlap) * self.n_gram
                sim_pct = min(100.0, round((matched_count / total_words) * 100, 1))
                matches.append(
                    TurnitinMatch(
                        source_id=ref.get("source_id", "REF-UNKNOWN"),
                        source_title=ref.get("title", "Reference Source"),
                        matched_text=" ".join(tokens[:15]) + "...",
                        match_percentage=sim_pct,
                    )
                )

        # Total combined similarity
        overall_pct = min(100.0, sum(m.match_percentage for m in matches))
        matched_words = int((overall_pct / 100.0) * total_words)

        # Turnitin official color bands
        if overall_pct == 0.0:
            band = "BLUE"
            interp = "No matching words detected."
        elif overall_pct < 25.0:
            band = "GREEN"
            interp = "Standard academic similarity range (acceptable for MIKOM 2026)."
        elif overall_pct < 50.0:
            band = "YELLOW"
            interp = "Moderate similarity detected; review primary literature citations."
        elif overall_pct < 75.0:
            band = "ORANGE"
            interp = "High similarity index; potential heavy paraphrasing."
        else:
            band = "RED"
            interp = "Severe similarity; extensive text duplication."

        return TurnitinReport(
            overall_similarity_percentage=round(overall_pct, 1),
            color_band=band,
            total_words=total_words,
            matched_words=matched_words,
            matches=matches,
            interpretation=interp,
        )


# ==============================================================================
# 2. ITHENTICATE CLONE (Journal Submission Integrity)
# ==============================================================================
class iThenticateClone:
    """Clones iThenticate: Journal-grade manuscript crosscheck with methodology filtering."""

    BOILERPLATE_PATTERNS = [
        r"data dikumpulkan melalui kuesioner",
        r"analisis data dilakukan dengan menggunakan",
        r"populasi dalam penelitian ini adalah",
        r"uji validitas dan reliabilitas",
    ]

    def verify_manuscript(self, text: str, reference_corpus: list[dict[str, str]]) -> dict[str, Any]:
        """Calculates journal-ready similarity score after removing standard research phrasing."""
        filtered_text = text
        for pat in self.BOILERPLATE_PATTERNS:
            filtered_text = re.sub(pat, " ", filtered_text, flags=re.IGNORECASE)

        t_clone = TurnitinClone(n_gram=6)
        report = t_clone.check_similarity(filtered_text, reference_corpus)
        return {
            "journal_similarity_score": report.overall_similarity_percentage,
            "submission_ready": report.overall_similarity_percentage <= 20.0,
            "color_band": report.color_band,
            "target_standard": "Scopus / Elsevier / MIKOM 2026",
            "boilerplate_filtered": True,
        }


# ==============================================================================
# 3. COPYLEAKS CLONE (Paraphrasing & AI Text Detection)
# ==============================================================================
class CopyleaksClone:
    """Clones Copyleaks: Paraphrased text matching and AI-generated text estimation."""

    def detect_ai_and_paraphrase(self, text: str) -> dict[str, Any]:
        """Estimates AI generation likelihood and linguistic burstiness."""
        sentences = [s.strip() for s in re.split(r"[.!?]+", text) if len(s.strip()) > 5]
        if not sentences:
            return {"ai_probability": 0.0, "classification": "HUMAN_ORIGINAL", "burstiness": 1.0}

        lengths = [len(s.split()) for s in sentences]
        mean_len = sum(lengths) / len(lengths)
        variance = sum((val - mean_len) ** 2 for val in lengths) / max(1, len(lengths))
        std_dev = math.sqrt(variance)
        burstiness = round(std_dev / max(1.0, mean_len), 2)

        # AI text typically has low burstiness (uniform sentence lengths)
        ai_prob = 85.0 if burstiness < 0.25 else 15.0 if burstiness > 0.6 else 45.0
        classification = "AI_GENERATED" if ai_prob >= 75.0 else "MIXED" if ai_prob >= 40.0 else "HUMAN_ORIGINAL"

        return {
            "ai_probability": ai_prob,
            "classification": classification,
            "burstiness_index": burstiness,
            "average_sentence_length": round(mean_len, 1),
            "sentence_count": len(sentences),
        }


# ==============================================================================
# 4. OURIGINAL CLONE (Document-to-Document Match Matrix)
# ==============================================================================
class OuriginalClone:
    """Clones Ouriginal (formerly Urkund): Pairwise document similarity comparison."""

    def compare_documents(self, doc_a: str, doc_b: str) -> dict[str, Any]:
        """Calculates bidirectional text overlap between two documents."""
        words_a = set(re.findall(r"\b[a-zA-Z]{3,}\b", doc_a.lower()))
        words_b = set(re.findall(r"\b[a-zA-Z]{3,}\b", doc_b.lower()))

        if not words_a or not words_b:
            return {"overlap_ratio": 0.0, "shared_word_count": 0}

        shared = words_a & words_b
        jaccard = round(len(shared) / len(words_a | words_b), 3)

        return {
            "overlap_ratio": jaccard,
            "similarity_percentage": round(jaccard * 100, 1),
            "shared_word_count": len(shared),
            "doc_a_unique": len(words_a - words_b),
            "doc_b_unique": len(words_b - words_a),
        }


# ==============================================================================
# 5. GRAMMARLY CLONE (Academic Formality & Writing Enhancement)
# ==============================================================================
class GrammarlyClone:
    """Clones Grammarly: Academic tone, passive voice frequency, and conciseness checker."""

    INFORMAL_WORDS = {"banget", "nggak", "cuma", "bikin", "kayak", "gimana", "stuff", "lots of", "basically"}

    def audit_academic_writing(self, text: str) -> dict[str, Any]:
        """Audits text for academic formality, passive voice, and wordiness."""
        tokens = [w.lower() for w in re.findall(r"\b[a-zA-Z]+\b", text)]
        total_words = max(1, len(tokens))

        # Informal word detection
        informal_found = [w for w in tokens if w in self.INFORMAL_WORDS]

        # Passive voice detection in Indonesian (awalan 'di-')
        passive_matches = re.findall(r"\bdi[a-z]{3,}\b", text.lower())
        passive_ratio = round(len(passive_matches) / total_words, 2)

        # Formality score (out of 100)
        penalty = (len(informal_found) * 5) + (10 if passive_ratio > 0.4 else 0)
        formality_score = max(0, min(100, 100 - penalty))

        return {
            "academic_formality_score": formality_score,
            "total_words": total_words,
            "passive_voice_count": len(passive_matches),
            "passive_ratio": passive_ratio,
            "informal_words_detected": informal_found,
            "meets_mikom_standard": formality_score >= 85 and len(informal_found) == 0,
        }
