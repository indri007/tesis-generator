"""Consensus AI Scientific Evidence Synthesizer & Consensus Meter Clone.
Pure-Python implementation of Consensus.app capabilities:
1. Natural language scientific question analysis & hypothesis verification.
2. Quantitative Consensus Meter (% Yes, % No, % Possibly, % Inconclusive).
3. Study Snapshot extraction (Study Design, Sample Size n=..., Key Finding Quote).
4. Rigor-Weighted Consensus Quality Index (CQI).
5. Academic literature synthesis narrative generation with in-text APA citations.
6. Standard Consensus CSV and JSON export compatibility.
"""

from __future__ import annotations

import csv
import re
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class ConsensusVerdict(str, Enum):
    """Consensus verdict for an individual scientific study."""

    YES = "Yes"
    NO = "No"
    POSSIBLY = "Possibly"
    INCONCLUSIVE = "Inconclusive"


class StudyDesign(str, Enum):
    """Hierarchy of study design rigor."""

    SYSTEMATIC_REVIEW = "Systematic Literature Review / Meta-Analysis"
    RCT = "Randomized Controlled Trial (RCT)"
    EMPIRICAL_QUANTITATIVE = "Empirical Quantitative (SNA / ML / Experiment)"
    OBSERVATIONAL_SURVEY = "Survey / Observational"
    EMPIRICAL_QUALITATIVE = "Qualitative Case Study / Interview"
    CONCEPTUAL = "Conceptual / Theoretical Framework"
    OTHER = "Other Empirical Study"


@dataclass
class ConsensusClaim:
    """Individual paper evidence claim and study snapshot."""

    paper_id: str
    title: str
    authors: list[str]
    year: int | None
    journal: str | None
    doi: str | None
    verdict: ConsensusVerdict
    confidence: float
    study_design: StudyDesign
    sample_size: int | None
    key_quote: str
    takeaway: str
    rigor_stars: int
    citation_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["verdict"] = self.verdict.value
        d["study_design"] = self.study_design.value
        return d


@dataclass
class ConsensusMeter:
    """Quantitative consensus distribution across evaluated studies."""

    total_studies: int
    yes_count: int
    no_count: int
    possibly_count: int
    inconclusive_count: int
    yes_percentage: float
    no_percentage: float
    possibly_percentage: float
    weighted_consensus_score: float  # -1.0 (All No) to +1.0 (All Yes)
    summary_headline: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ConsensusSynthesisResult:
    """Comprehensive consensus synthesis report."""

    query: str
    meter: ConsensusMeter
    claims: list[ConsensusClaim]
    synthesis_narrative: str
    evidence_matrix: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "meter": self.meter.to_dict(),
            "claims": [c.to_dict() for c in self.claims],
            "synthesis_narrative": self.synthesis_narrative,
            "evidence_matrix": self.evidence_matrix,
        }

    def to_markdown(self) -> str:
        """Renders consensus synthesis into formatted academic Markdown."""
        lines = [
            f"# Consensus Scientific Synthesis: {self.query}",
            "",
            "## 1. Consensus Meter",
            f"- **Ringkasan Konsensus**: {self.meter.summary_headline}",
            f"- **Yes (Mendukung)**: {self.meter.yes_percentage}% ({self.meter.yes_count}/{self.meter.total_studies} studi)",
            f"- **Possibly (Sebagian/Campuran)**: {self.meter.possibly_percentage}% ({self.meter.possibly_count}/{self.meter.total_studies} studi)",
            f"- **No (Membantah)**: {self.meter.no_percentage}% ({self.meter.no_count}/{self.meter.total_studies} studi)",
            f"- **Skor Konsensus Terbobot**: {self.meter.weighted_consensus_score:+.2f} (Skala -1.0 s/d +1.0)",
            "",
            "## 2. Sintesis Naratif Akademik (Bab II Tesis)",
            self.synthesis_narrative,
            "",
            "## 3. Matriks Bukti Ilmiah (Study Snapshot Table)",
            "| # | Penulis & Tahun | Judul Paper | Desain Studi | Sampel | Putusan Konsensus | Temuan Kunci & Kutipan |",
            "|---|---|---|---|:---:|:---:|---|",
        ]
        for idx, c in enumerate(self.claims, start=1):
            auth = c.authors[0] if c.authors else "Anonim"
            yr = str(c.year or "n.d.")
            sample = f"n={c.sample_size:,}" if c.sample_size else "N/A"
            lines.append(
                f"| {idx} | {auth} et al. ({yr}) | {c.title} | {c.study_design.value} | {sample} | **{c.verdict.value}** ({c.rigor_stars}★) | \"{c.key_quote}\" |"
            )
        return "\n".join(lines)


class ConsensusAIClone:
    """Deterministic scientific consensus engine cloning Consensus.app."""

    POSITIVE_MARKERS = [
        "significantly improve", "significantly increase", "effectively detect", "outperform",
        "enhance", "positive effect", "positive impact", "confirms", "supports hypothesis",
        "high accuracy", "superior performance", "foster trust", "statistically significant correlation",
        "berhasil meningkatkan", "terbukti efektif", "berpengaruh signifikan", "meningkatkan akurasi",
        "memperkuat", "mempercepat", "akurasi tinggi", "hubungan positif",
    ]

    NEGATIVE_MARKERS = [
        "no significant difference", "fails to", "does not increase", "ineffective",
        "negative effect", "negative impact", "refutes", "no correlation", "worsens",
        "bias", "distorts", "decline in trust", "inferior",
        "tidak berpengaruh", "gagal", "berpengaruh negatif", "menurunkan", "memperburuk",
        "tidak ada perbedaan signifikan", "distorsi", "anomali",
    ]

    NUANCED_MARKERS = [
        "depends on", "mixed results", "contingent upon", "moderate effect", "varies",
        "conditional", "dual effect", "both positive and negative",
        "tergantung", "hasil campuran", "kondisional", "sebagian", "efek moderat",
    ]

    def analyze_corpus(
        self,
        query: str,
        papers: list[Any],
    ) -> ConsensusSynthesisResult:
        """Evaluates research papers against a query and generates Consensus synthesis."""
        claims: list[ConsensusClaim] = []

        for idx, p in enumerate(papers):
            # Extract common fields regardless of input type (dataclass or dict)
            title = getattr(p, "title", "") if hasattr(p, "title") else p.get("title", "")
            abstract = getattr(p, "abstract", "") if hasattr(p, "abstract") else p.get("abstract", "")
            authors = getattr(p, "authors", []) if hasattr(p, "authors") else p.get("authors", [])
            year = getattr(p, "year", None) if hasattr(p, "year") else p.get("year")
            journal = getattr(p, "journal", None) if hasattr(p, "journal") else p.get("journal")
            doi = getattr(p, "doi", None) if hasattr(p, "doi") else p.get("doi")
            cits = int(getattr(p, "cited_by_count", 0) if hasattr(p, "cited_by_count") else p.get("cited_by_count", 0) or 0)
            pid = getattr(p, "record_id", f"paper_{idx+1}") if hasattr(p, "record_id") else p.get("record_id", f"paper_{idx+1}")

            full_content = f"{title}. {abstract or ''}"

            verdict, confidence, quote, takeaway = self.evaluate_claim(query, full_content)
            design = self.extract_study_design(full_content)
            sample_size = self.extract_sample_size(full_content)
            rigor = self.compute_rigor_stars(design, sample_size, cits)

            claim = ConsensusClaim(
                paper_id=str(pid),
                title=title,
                authors=authors if isinstance(authors, list) else [str(authors)],
                year=int(year) if year else None,
                journal=journal,
                doi=doi,
                verdict=verdict,
                confidence=round(confidence, 2),
                study_design=design,
                sample_size=sample_size,
                key_quote=quote,
                takeaway=takeaway,
                rigor_stars=rigor,
                citation_count=cits,
            )
            claims.append(claim)

        meter = self._calculate_consensus_meter(claims)
        narrative = self._generate_synthesis_narrative(query, meter, claims)

        evidence_matrix = [
            {
                "paper_id": c.paper_id,
                "title": c.title,
                "citation": f"{c.authors[0] if c.authors else 'Anonymous'} ({c.year or 'n.d.'})",
                "verdict": c.verdict.value,
                "confidence": c.confidence,
                "study_design": c.study_design.value,
                "sample_size": c.sample_size,
                "rigor_stars": c.rigor_stars,
                "key_quote": c.key_quote,
            }
            for c in claims
        ]

        return ConsensusSynthesisResult(
            query=query,
            meter=meter,
            claims=claims,
            synthesis_narrative=narrative,
            evidence_matrix=evidence_matrix,
        )

    def evaluate_claim(self, query: str, text: str) -> tuple[ConsensusVerdict, float, str, str]:
        """Classifies the claim polarity and extracts key supportive quote."""
        t_low = text.lower()

        pos_score = sum(1 for m in self.POSITIVE_MARKERS if m in t_low)
        neg_score = sum(1 for m in self.NEGATIVE_MARKERS if m in t_low)
        nuance_score = sum(1 for m in self.NUANCED_MARKERS if m in t_low)

        # Extract sentences for quote extraction
        sentences = [s.strip() for s in re.split(r"(?<=[.?!])\s+", text) if len(s.strip()) > 15]

        # Determine verdict
        if pos_score > neg_score and pos_score >= nuance_score:
            verdict = ConsensusVerdict.YES
            confidence = min(0.95, 0.65 + (pos_score * 0.08))
            quote = self._find_best_sentence(sentences, self.POSITIVE_MARKERS)
            takeaway = "Studi memberikan bukti empiris positif yang mendukung pertanyaan penelitian."
        elif neg_score > pos_score and neg_score >= nuance_score:
            verdict = ConsensusVerdict.NO
            confidence = min(0.95, 0.65 + (neg_score * 0.08))
            quote = self._find_best_sentence(sentences, self.NEGATIVE_MARKERS)
            takeaway = "Studi menemukan ketiadaan dampak signifikan atau membantah hipotesis."
        elif nuance_score > 0:
            verdict = ConsensusVerdict.POSSIBLY
            confidence = min(0.88, 0.60 + (nuance_score * 0.08))
            quote = self._find_best_sentence(sentences, self.NUANCED_MARKERS)
            takeaway = "Temuan menunjukkan pengaruh bersyarat yang bervariasi bergantung pada konteks penerapan."
        else:
            verdict = ConsensusVerdict.INCONCLUSIVE
            confidence = 0.50
            quote = sentences[0] if sentences else text[:100]
            takeaway = "Bukti ilmiah dalam naskah belum menunjukkan kesimpulan arah yang definitif."

        if not quote and sentences:
            quote = sentences[0]

        return verdict, confidence, quote, takeaway

    @staticmethod
    def _find_best_sentence(sentences: list[str], markers: list[str]) -> str:
        for s in sentences:
            s_low = s.lower()
            if any(m in s_low for m in markers):
                return s
        return sentences[0] if sentences else ""

    @staticmethod
    def extract_study_design(text: str) -> StudyDesign:
        t_low = text.lower()
        if any(k in t_low for k in ["meta-analysis", "systematic review", "prisma", "tinjauan sistematis"]):
            return StudyDesign.SYSTEMATIC_REVIEW
        if any(k in t_low for k in ["randomized controlled", "rct", "randomized trial"]):
            return StudyDesign.RCT
        if any(k in t_low for k in ["social network analysis", "sna", "indobert", "deep learning", "machine learning", "quasi-experiment", "eksperimen"]):
            return StudyDesign.EMPIRICAL_QUANTITATIVE
        if any(k in t_low for k in ["survey", "kuesioner", "survei", "cross-sectional", "observational"]):
            return StudyDesign.OBSERVATIONAL_SURVEY
        if any(k in t_low for k in ["case study", "studi kasus", "wawancara mendalam", "in-depth interview", "kualitatif"]):
            return StudyDesign.EMPIRICAL_QUALITATIVE
        if any(k in t_low for k in ["conceptual framework", "perspektif teoritis", "marketing 6.0", "phygital"]):
            return StudyDesign.CONCEPTUAL
        return StudyDesign.OTHER

    @staticmethod
    def extract_sample_size(text: str) -> int | None:
        patterns = [
            r"\b(?:n\s*=\s*|sampel\s+(?:sebanyak\s+)?|sample\s+size\s+of\s+|sebanyak\s+)(\d{1,7})\b",
            r"\b(\d{1,7})\s+(?:tweets|cuitan|posts|responden|participants|peserta|mahasiswa|records|dokumen)\b",
        ]
        for pat in patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                try:
                    val = int(m.group(1))
                    if 10 <= val <= 10_000_000:
                        return val
                except ValueError:
                    continue
        return None

    @staticmethod
    def compute_rigor_stars(design: StudyDesign, sample_size: int | None, citations: int) -> int:
        stars = 2
        # Design bonus
        if design in [StudyDesign.SYSTEMATIC_REVIEW, StudyDesign.RCT]:
            stars += 2
        elif design in [StudyDesign.EMPIRICAL_QUANTITATIVE]:
            stars += 1

        # Sample size bonus
        if sample_size and sample_size >= 500:
            stars += 1

        # Citation impact bonus
        if citations >= 30:
            stars += 1

        return min(5, max(1, stars))

    def _calculate_consensus_meter(self, claims: list[ConsensusClaim]) -> ConsensusMeter:
        total = len(claims)
        if total == 0:
            return ConsensusMeter(
                total_studies=0,
                yes_count=0,
                no_count=0,
                possibly_count=0,
                inconclusive_count=0,
                yes_percentage=0.0,
                no_percentage=0.0,
                possibly_percentage=0.0,
                weighted_consensus_score=0.0,
                summary_headline="Tidak ada studi yang dianalisis.",
            )

        yes_c = sum(1 for c in claims if c.verdict == ConsensusVerdict.YES)
        no_c = sum(1 for c in claims if c.verdict == ConsensusVerdict.NO)
        poss_c = sum(1 for c in claims if c.verdict == ConsensusVerdict.POSSIBLY)
        incon_c = sum(1 for c in claims if c.verdict == ConsensusVerdict.INCONCLUSIVE)

        yes_pct = round((yes_c / total) * 100.0, 1)
        no_pct = round((no_c / total) * 100.0, 1)
        poss_pct = round((poss_c / total) * 100.0, 1)

        # Weighted score computation based on rigor stars
        weighted_sum = 0.0
        total_weights = 0.0
        for c in claims:
            w = c.rigor_stars * c.confidence
            total_weights += w
            if c.verdict == ConsensusVerdict.YES:
                weighted_sum += w * 1.0
            elif c.verdict == ConsensusVerdict.NO:
                weighted_sum += w * (-1.0)
            elif c.verdict == ConsensusVerdict.POSSIBLY:
                weighted_sum += w * 0.25

        score = weighted_sum / max(1.0, total_weights)

        # Consensus Headline synthesis
        if yes_pct >= 60.0:
            headline = f"Mayoritas studi ({yes_pct}%) mengonfirmasi secara positif (YES)."
        elif no_pct >= 60.0:
            headline = f"Mayoritas studi ({no_pct}%) membantah hipotesis (NO)."
        elif (yes_pct + poss_pct) >= 65.0:
            headline = f"Literatur cenderung positif dengan variasi bersyarat ({yes_pct}% Yes, {poss_pct}% Possibly)."
        else:
            headline = "Temuan literatur terbagi seimbang / belum mencapai konsensus definitif."

        return ConsensusMeter(
            total_studies=total,
            yes_count=yes_c,
            no_count=no_c,
            possibly_count=poss_c,
            inconclusive_count=incon_c,
            yes_percentage=yes_pct,
            no_percentage=no_pct,
            possibly_percentage=poss_pct,
            weighted_consensus_score=round(score, 2),
            summary_headline=headline,
        )

    def _generate_synthesis_narrative(
        self,
        query: str,
        meter: ConsensusMeter,
        claims: list[ConsensusClaim],
    ) -> str:
        """Synthesizes academic paragraph linking claims with APA references."""
        if not claims:
            return "Belum ada literatur pembanding yang dianalisis."

        yes_papers = [c for c in claims if c.verdict == ConsensusVerdict.YES]
        poss_papers = [c for c in claims if c.verdict == ConsensusVerdict.POSSIBLY]
        no_papers = [c for c in claims if c.verdict == ConsensusVerdict.NO]

        narrative_parts = [
            f"Berdasarkan telaah sintesis ilmiah terhadap pertanyaan penelitian *'{query}'*, "
            f"literatur peer-reviewed menunjukkan bahwa {meter.summary_headline.lower()} "
            f"dengan skor konsensus terbobot {meter.weighted_consensus_score:+.2f}."
        ]

        def _get_surname(author_str: str) -> str:
            if not author_str:
                return "Anonim"
            if "," in author_str:
                return author_str.split(",")[0].strip()
            tokens = author_str.strip().split()
            return tokens[-1] if tokens else "Anonim"

        if yes_papers:
            citations = []
            for p in yes_papers[:3]:
                auth = _get_surname(p.authors[0]) if p.authors else "Anonim"
                citations.append(f"{auth} et al., {p.year or '2024'}")
            cit_str = "; ".join(citations)
            narrative_parts.append(
                f"Secara konsisten, bukti empiris dari studi berbobot tinggi ({cit_str}) membuktikan bahwa "
                f"variabel yang diteliti memberikan pengaruh signifikan, seperti ditegaskan oleh temuan kunci: "
                f"\"{yes_papers[0].key_quote}\"."
            )

        if poss_papers:
            p_cit = [f"{_get_surname(p.authors[0]) if p.authors else 'Anonim'}, {p.year or '2024'}" for p in poss_papers[:2]]
            narrative_parts.append(
                f"Di sisi lain, sebagian riset mengidentifikasi adanya batasan kontekstual ({'; '.join(p_cit)}), "
                f"di mana efektivitas bergantung pada karakteristik audiens dan platform komunikasi digital."
            )

        if no_papers:
            n_cit = [f"{_get_surname(p.authors[0]) if p.authors else 'Anonim'}, {p.year or '2024'}" for p in no_papers[:2]]
            narrative_parts.append(
                f"Adapun penelitian yang mencatat ketiadaan dampak signifikan ({'; '.join(n_cit)}) menggarisbawahi "
                f"perlunya pengawasan ketat terhadap anomali metodologis."
            )

        narrative_parts.append(
            "Temuan sintesis ini memberikan landasan teoretis dan justifikasi empiris yang kokoh "
            "bagi pengembangan kerangka konseptual serta perumusan hipotesis pada tesis ini."
        )

        return " ".join(narrative_parts)

    def export_consensus_csv(self, result: ConsensusSynthesisResult, output_path: Path | str) -> None:
        """Exports Consensus synthesis to standard Consensus.app CSV export format."""
        p = Path(output_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        headers = [
            "Query", "Paper Title", "Authors", "Year", "Journal", "DOI",
            "Consensus Meter", "Study Snapshot", "Key Takeaway", "Sample Size",
            "Study Design", "Rigor Stars", "Citation Count"
        ]
        with open(p, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            for c in result.claims:
                writer.writerow([
                    result.query,
                    c.title,
                    "; ".join(c.authors),
                    c.year or "",
                    c.journal or "",
                    c.doi or "",
                    c.verdict.value,
                    c.key_quote,
                    c.takeaway,
                    c.sample_size or "",
                    c.study_design.value,
                    c.rigor_stars,
                    c.citation_count,
                ])
