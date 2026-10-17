"""Academic Document Integrity Engine.

Provides deep academic manuscript integrity auditing:
- Robust multi-section document segmentation (Bab 1-5, Daftar Pustaka, Lampiran).
- Selective exclusion of Daftar Pustaka and direct quotations to prevent artificial lexical inflation.
- Multi-metric lexical analysis: Lexical Cosine, N-Gram Word Shingling, and Token Jaccard.
- Citation-Reference reciprocity reconciliation (linking in-text citations with bibliography entries).
- Strictly local computation with zero external network leakage.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime

try:
    from core.clones.similarity_plagiarism import (
        compute_cosine_similarity,
        normalize_and_tokenize,
    )
except ImportError:
    import math
    import unicodedata
    from collections import Counter

    def normalize_and_tokenize(text: str) -> list[str]:
        if text is None:
            return []
        if not isinstance(text, str):
            raise TypeError(f"Expected string input, got {type(text).__name__}")
        if not text.strip():
            return []
        normalized = unicodedata.normalize("NFKC", text)
        return re.findall(r"\b[\w-]+\b", normalized.lower(), flags=re.UNICODE)

    def compute_cosine_similarity(text_a: str, text_b: str) -> float:
        tokens_a = normalize_and_tokenize(text_a)
        tokens_b = normalize_and_tokenize(text_b)
        if not tokens_a or not tokens_b:
            return 0.0
        if tokens_a == tokens_b:
            return 1.0
        vec_a = Counter(tokens_a)
        vec_b = Counter(tokens_b)
        common_keys = set(vec_a.keys()) & set(vec_b.keys())
        if not common_keys:
            return 0.0
        dot_product = sum(vec_a[k] * vec_b[k] for k in common_keys)
        sum_a = sum(v * v for v in vec_a.values())
        sum_b = sum(v * v for v in vec_b.values())
        denom = math.sqrt(sum_a) * math.sqrt(sum_b)
        if denom <= 0.0 or not math.isfinite(denom):
            return 0.0
        score = dot_product / denom
        if not math.isfinite(score):
            return 0.0
        return max(0.0, min(1.0, float(score)))

from parsers.citation_parser import audit_citations


@dataclass
class SectionSegment:
    """Represents a structural section of an academic manuscript."""

    name: str
    start_char: int
    end_char: int
    text: str
    is_bibliography: bool = False
    is_appendix: bool = False


@dataclass
class CitationReconciliationItem:
    """Represents a matched, orphaned, or unused citation record."""

    author_year: str
    status: str  # "MATCHED" | "MISSING_IN_BIB" | "UNUSED_BIB"
    location: str  # "in-text" | "bibliography"
    context: str = ""


@dataclass
class AcademicIntegrityReport:
    """Consolidated document integrity and similarity audit report."""

    cosine_similarity: float
    shingle_jaccard: float
    token_jaccard: float
    total_tokens_doc: int
    total_tokens_ref: int
    shared_tokens_count: int
    total_in_text_citations: int
    total_bibliography_entries: int
    citations_reconciliation: list[CitationReconciliationItem]
    unique_tokens_doc: int = 0
    unique_tokens_ref: int = 0
    excluded_sections: list[str] = field(default_factory=list)
    direct_quotes_excluded_count: int = 0
    top_shared_terms: list[tuple[str, int, int]] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    disclaimer: str = (
        "Skor kemiripan leksikal dan shingling semata-mata mengukur tumpang-tindih frekuensi kata "
        "dan frasa antar naskah. Skor ini BUKAN bukti plagiarisme dan BUKAN vonis pelanggaran akademik. "
        "Daftar Pustaka dan kutipan langsung dapat dikecualikan untuk evaluasi substantif yang lebih akurat."
    )

    @property
    def cosine_percentage(self) -> float:
        return round(self.cosine_similarity * 100.0, 2)

    @property
    def shingle_percentage(self) -> float:
        return round(self.shingle_jaccard * 100.0, 2)

    @property
    def token_jaccard_percentage(self) -> float:
        return round(self.token_jaccard * 100.0, 2)


_SECTION_HEADING_REGEX = re.compile(
    r"(?m)^(?:\s*)"
    r"(?:"
    r"(?:BAB\s+[IVXLCDM\d]+[^\n]*)|"
    r"(?:CHAPTER\s+[IVXLCDM\d]+[^\n]*)|"
    r"(?:DAFTAR\s+PUSTAKA[^\n]*)|"
    r"(?:REFERENCES[^\n]*)|"
    r"(?:BIBLIOGRAPHY[^\n]*)|"
    r"(?:LAMPIRAN[^\n]*)|"
    r"(?:APPENDIX[^\n]*)|"
    r"(?:ABSTRAK[^\n]*)|"
    r"(?:ABSTRACT[^\n]*)|"
    r"(?:PENDAHULUAN[^\n]*)"
    r")",
    re.IGNORECASE,
)

_DIRECT_QUOTE_REGEX = re.compile(
    r'(?:"([^"]{5,})")|(?:“([^”]{5,})”)|(?:«([^»]{5,})»)',
    re.MULTILINE,
)


def segment_document_sections(text: str) -> list[SectionSegment]:
    """Divides academic text into discrete structural sections based on recognized headings."""
    if not text or not text.strip():
        return []

    matches = list(_SECTION_HEADING_REGEX.finditer(text))
    if not matches:
        return [
            SectionSegment(
                name="Badan Naskah (Utuh)",
                start_char=0,
                end_char=len(text),
                text=text,
                is_bibliography=False,
                is_appendix=False,
            )
        ]

    segments: list[SectionSegment] = []

    # Handle preamble before the first explicit heading if present
    first_start = matches[0].start()
    if first_start > 0:
        preamble_text = text[:first_start].strip()
        if preamble_text:
            segments.append(
                SectionSegment(
                    name="Bagian Awal / Judul",
                    start_char=0,
                    end_char=first_start,
                    text=preamble_text,
                    is_bibliography=False,
                    is_appendix=False,
                )
            )

    for i, match in enumerate(matches):
        start_char = match.start()
        end_char = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        heading_line = match.group(0).strip()
        sec_text = text[start_char:end_char].strip()

        is_bib = bool(re.search(r"\b(?:DAFTAR\s+PUSTAKA|REFERENCES|BIBLIOGRAPHY)\b", heading_line, re.I))
        is_app = bool(re.search(r"\b(?:LAMPIRAN|APPENDIX)\b", heading_line, re.I))

        segments.append(
            SectionSegment(
                name=heading_line,
                start_char=start_char,
                end_char=end_char,
                text=sec_text,
                is_bibliography=is_bib,
                is_appendix=is_app,
            )
        )

    return segments


def strip_direct_quotes(text: str) -> tuple[str, list[tuple[int, int, str]]]:
    """Extracts and strips direct quotations enclosed in quotation marks from the text."""
    spans: list[tuple[int, int, str]] = []

    def _replace_quote(match: re.Match[str]) -> str:
        quote_text = match.group(1) or match.group(2) or match.group(3) or ""
        spans.append((match.start(), match.end(), quote_text))
        return " "  # replace with whitespace to preserve surrounding token boundaries

    cleaned = _DIRECT_QUOTE_REGEX.sub(_replace_quote, text)
    return cleaned, spans


def compute_ngram_shingles(tokens: list[str], n: int = 3) -> list[str]:
    """Generates contiguous n-gram word shingles from a token sequence."""
    if len(tokens) < n:
        return [" ".join(tokens)] if tokens else []
    return [" ".join(tokens[i : i + n]) for i in range(len(tokens) - n + 1)]


def compute_shingle_jaccard(tokens_a: list[str], tokens_b: list[str], n: int = 3) -> float:
    """Computes Jaccard similarity over n-gram word shingles."""
    shingles_a = set(compute_ngram_shingles(tokens_a, n=n))
    shingles_b = set(compute_ngram_shingles(tokens_b, n=n))

    if not shingles_a or not shingles_b:
        return 0.0

    intersection = len(shingles_a & shingles_b)
    union = len(shingles_a | shingles_b)
    if union == 0:
        return 0.0
    return max(0.0, min(1.0, float(intersection) / float(union)))


def run_academic_integrity_audit(
    text_doc: str,
    text_ref: str | None = None,
    exclude_bib: bool = True,
    exclude_quotes: bool = False,
    shingle_n: int = 3,
) -> AcademicIntegrityReport:
    """Runs a complete academic integrity and similarity audit across one or two texts."""
    from collections import Counter

    excluded_names: list[str] = []
    quotes_count = 0

    # 1. Citation audit on primary document
    citation_audit_res = audit_citations(text_doc)
    reconciled_items: list[CitationReconciliationItem] = []

    for cit, ref in citation_audit_res.matched_pairs:
        reconciled_items.append(
            CitationReconciliationItem(
                author_year=f"{cit.surname.capitalize()} ({cit.year})",
                status="MATCHED",
                location="in-text & bib",
                context=f"Sitasi: {cit.raw} | Rujukan: {ref.raw[:70]}...",
            )
        )

    for orphan in citation_audit_res.orphaned_citations:
        reconciled_items.append(
            CitationReconciliationItem(
                author_year=f"{orphan.surname.capitalize()} ({orphan.year})",
                status="MISSING_IN_BIB",
                location="in-text only",
                context=orphan.raw,
            )
        )

    for unused in citation_audit_res.unused_references:
        first_author = unused.surnames[0] if unused.surnames else "Anonim"
        reconciled_items.append(
            CitationReconciliationItem(
                author_year=f"{first_author.capitalize()} ({unused.year})",
                status="UNUSED_BIB",
                location="bibliography only",
                context=unused.raw[:80],
            )
        )

    # 2. Section segmentation & filtering
    segments_doc = segment_document_sections(text_doc)
    doc_text_parts: list[str] = []

    for seg in segments_doc:
        if exclude_bib and seg.is_bibliography:
            excluded_names.append(seg.name)
            continue
        doc_text_parts.append(seg.text)

    processed_doc = "\n\n".join(doc_text_parts) if doc_text_parts else text_doc

    if exclude_quotes:
        processed_doc, q_spans = strip_direct_quotes(processed_doc)
        quotes_count += len(q_spans)

    # 3. If reference text is provided, perform comparative metrics
    processed_ref = ""
    if text_ref is not None:
        segments_ref = segment_document_sections(text_ref)
        ref_text_parts: list[str] = []
        for seg in segments_ref:
            if exclude_bib and seg.is_bibliography:
                continue
            ref_text_parts.append(seg.text)
        processed_ref = "\n\n".join(ref_text_parts) if ref_text_parts else text_ref
        if exclude_quotes:
            processed_ref, q_ref = strip_direct_quotes(processed_ref)
            quotes_count += len(q_ref)

    tokens_doc = normalize_and_tokenize(processed_doc)
    tokens_ref = normalize_and_tokenize(processed_ref) if processed_ref else []

    cosine_sim = compute_cosine_similarity(processed_doc, processed_ref) if processed_ref else 0.0
    shingle_sim = compute_shingle_jaccard(tokens_doc, tokens_ref, n=shingle_n) if processed_ref else 0.0

    set_doc = set(tokens_doc)
    set_ref = set(tokens_ref)
    token_jaccard = (
        float(len(set_doc & set_ref)) / float(len(set_doc | set_ref))
        if (set_doc and set_ref and len(set_doc | set_ref) > 0)
        else 0.0
    )

    counts_doc = Counter(tokens_doc)
    counts_ref = Counter(tokens_ref)
    shared_vocab = set(counts_doc.keys()) & set(counts_ref.keys())
    top_shared = sorted(
        [(term, counts_doc[term], counts_ref[term]) for term in shared_vocab],
        key=lambda item: (item[1] + item[2]),
        reverse=True,
    )[:30]

    return AcademicIntegrityReport(
        cosine_similarity=cosine_sim,
        shingle_jaccard=shingle_sim,
        token_jaccard=token_jaccard,
        total_tokens_doc=len(tokens_doc),
        total_tokens_ref=len(tokens_ref),
        unique_tokens_doc=len(counts_doc),
        unique_tokens_ref=len(counts_ref),
        shared_tokens_count=len(shared_vocab),
        total_in_text_citations=len(citation_audit_res.body_citations),
        total_bibliography_entries=len(citation_audit_res.references),
        citations_reconciliation=reconciled_items,
        excluded_sections=excluded_names,
        direct_quotes_excluded_count=quotes_count,
        top_shared_terms=top_shared,
    )
