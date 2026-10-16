"""Text Processing, OpenAlex Inverted Index Reconstruction, and Language Detection.

Implements Phase 1 & Section F requirements:
- Abstract extraction (#89)
- OpenAlex inverted-index reconstruction (#90)
- Abstract cleaning (#91)
- Language detection (#92)
- Text normalization (#94)
- Sentence segmentation (#95)
"""

from __future__ import annotations

import html
import re
import unicodedata


def reconstruct_openalex_inverted_index(inverted_index: dict[str, list[int]] | None) -> str:
    """Reconstructs continuous text from OpenAlex inverted index format (#90).

    OpenAlex stores abstracts as: {"word": [pos1, pos2], ...}.
    This reverses the mapping into sorted, readable prose.
    """
    if not inverted_index or not isinstance(inverted_index, dict):
        return ""

    positions: list[tuple[int, str]] = []
    for word, pos_list in inverted_index.items():
        if isinstance(pos_list, list):
            for p in pos_list:
                if isinstance(p, int):
                    positions.append((p, word))

    positions.sort(key=lambda x: x[0])
    return " ".join(word for _, word in positions)


def clean_abstract(text: str | None) -> str:
    """Cleans abstract text by removing HTML tags and normalizing whitespace (#91)."""
    if not text:
        return ""

    # 1. Strip HTML tags first (e.g., <p>, <i>)
    no_html = re.sub(r"<[^>]+>", " ", text)
    # 2. Unescape HTML entities second (&lt; -> <, &amp; -> &)
    unescaped = html.unescape(no_html)
    # Remove control characters
    no_ctrl = "".join(ch for ch in unescaped if unicodedata.category(ch)[0] != "C" or ch in "\n\t")
    # Normalize multiple whitespace
    normalized = re.sub(r"\s+", " ", no_ctrl).strip()
    return normalized


def normalize_text(text: str, lowercase: bool = False) -> str:
    """General text normalization for academic content (#94)."""
    if not text:
        return ""
    # NFKD normalization to separate accents
    normalized = unicodedata.normalize("NFKD", text)
    # Re-encode to ASCII or clean unicode
    cleaned = "".join(c for c in normalized if not unicodedata.combining(c))
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned.lower() if lowercase else cleaned


# Indonesian stopwords and markers
INDONESIAN_MARKERS = {
    "yang", "dan", "di", "dari", "ini", "dengan", "untuk", "pada", "adalah",
    "sebagai", "dalam", "tidak", "akan", "oleh", "tersebut", "penelitian",
    "metode", "analisis", "komunikasi", "masyarakat", "hasil", "data", "media",
}

# English markers
ENGLISH_MARKERS = {
    "the", "and", "of", "in", "to", "a", "is", "that", "for", "as", "with",
    "by", "this", "study", "research", "method", "analysis", "communication",
    "results", "data", "media", "social",
}


def detect_language(text: str) -> str:
    """Heuristic language detection (id vs en) (#92)."""
    if not text or len(text.strip()) < 10:
        return "en"

    words = set(re.findall(r"\b[a-z]{3,}\b", text.lower()))
    if not words:
        return "en"

    id_count = len(words.intersection(INDONESIAN_MARKERS))
    en_count = len(words.intersection(ENGLISH_MARKERS))

    return "id" if id_count > en_count else "en"


ABBREVIATIONS = {
    "et al.", "i.e.", "e.g.", "vol.", "no.", "pp.", "fig.", "dr.", "prof.",
    "ph.d.", "m.si.", "ir.", "vs.", "ca.", "dept.", "ed.", "univ.",
}


def segment_sentences(text: str) -> list[str]:
    """Academic-aware sentence segmentation (#95).

    Avoids false splits on academic abbreviations like 'et al.', 'i.e.', 'vol.'.
    """
    if not text:
        return []

    cleaned = clean_abstract(text)
    # Mask known abbreviations
    masked = cleaned
    replacements: dict[str, str] = {}
    for idx, abbr in enumerate(ABBREVIATIONS):
        token = f"__ABBR_{idx}__"
        pattern = re.compile(re.escape(abbr), re.IGNORECASE)
        if pattern.search(masked):
            masked = pattern.sub(token, masked)
            replacements[token] = abbr

    # Split on sentence boundaries: period, question mark, exclamation mark followed by space + Capital
    raw_sentences = re.split(r"(?<=[.?!])\s+(?=[A-Z0-9])", masked)

    sentences: list[str] = []
    for s in raw_sentences:
        s_restored = s
        for token, original in replacements.items():
            s_restored = s_restored.replace(token, original)
        s_restored = s_restored.strip()
        if s_restored:
            sentences.append(s_restored)

    return sentences
