"""Canonical Citation & Reference Extraction Engine (APA 7).

Provides unified segmentation, in-text citation extraction, bibliography parsing,
and hardened citation-reference reciprocity matching for both ParsedDocument
and CitationAuditor.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class InTextCitation:
    raw: str
    author: str
    surname: str
    year: str
    initials: str = ""
    is_narrative: bool = False
    section: str = "body"


@dataclass
class BibliographyEntry:
    raw: str
    author_section: str
    surnames: list[str]
    initials: list[str]
    year: str
    title_and_rest: str


@dataclass
class DocumentSegmentation:
    body_text: str
    bib_text: str
    appendix_text: str
    bib_present: bool
    appendix_present: bool
    boundaries_reliable: bool
    unreliable_reason: str | None = None


@dataclass
class CitationAuditResult:
    body_citations: list[InTextCitation]
    appendix_citations: list[InTextCitation]
    references: list[BibliographyEntry]
    orphaned_citations: list[InTextCitation]
    unused_references: list[BibliographyEntry]
    matched_pairs: list[tuple[InTextCitation, BibliographyEntry]]
    segmentation: DocumentSegmentation


DISCOURSE_PREFIXES_REGEX = (
    r"^(?:menurut|berdasarkan|kajian|studi|penelitian|artikel|buku|tulisan|"
    r"pendapat|pandangan|temuan|hasil|teori|model|oleh|dalam|pada|dari|"
    r"sebagaimana|seperti|yaitu|yakni)\s+"
)


def parse_author_tokens(raw: str) -> tuple[str, str]:
    """Extracts normalized (surname, initials) from an in-text author string.

    Examples:
        'Smith' -> ('smith', '')
        'A. Smith' -> ('smith', 'a')
        'Smith, A.' -> ('smith', 'a')
        'Smith et al.' -> ('smith', '')
        'Menurut Rahmawati' -> ('rahmawati', '')
        'Penelitian Smith' -> ('smith', '')
        'Levi-Strauss' -> ('levi-strauss', '')
    """
    clean = raw.strip()

    # Iteratively strip discourse marker prefixes
    changed = True
    while changed:
        changed = False
        m_prefix = re.match(DISCOURSE_PREFIXES_REGEX, clean, flags=re.IGNORECASE)
        if m_prefix:
            clean = clean[m_prefix.end() :].strip()
            changed = True

    clean = re.sub(r"\b(dkk\.|et\s+al\.|dan|and)\b", "", clean, flags=re.IGNORECASE).strip()

    # Match initials prefix: "A. Smith" or "A. B. Smith" (requires dot)
    init_prefix_match = re.match(r"^((?:[A-Z]\.\s*)+)\s*([A-Za-z\-–]+)$", clean)
    if init_prefix_match:
        initials = re.sub(r"[^a-zA-Z]", "", init_prefix_match.group(1)).lower()
        surname = init_prefix_match.group(2).lower()
        return surname, initials

    # Match inverted initials: "Smith, A."
    inv_match = re.match(r"^([A-Za-z\-–]+),\s*((?:[A-Z]\.?\s*)+)$", clean)
    if inv_match:
        surname = inv_match.group(1).lower()
        initials = re.sub(r"[^a-zA-Z]", "", inv_match.group(2)).lower()
        return surname, initials

    # Standard single word or compound author
    words = [w.strip(".,;:()") for w in clean.split() if w.strip(".,;:()")]
    if not words:
        return "", ""
    return words[0].lower(), ""


def segment_document(full_text: str) -> DocumentSegmentation:
    """Segments document text into body, bibliography, and appendix sections.

    Enforces structural ordering:
    Body -> Bibliography -> Appendix.
    If boundaries cannot be reliably determined, marks boundaries_reliable=False.
    """
    bib_regex = re.compile(
        r"(?:^|\n)[ \t]*(?:BAB\s+[IVXLCDM]+\s*[\.:\-]*)?[ \t]*(DAFTAR\s+PUSTAKA|DAFTAR\s+RUJUKAN|REFERENCES|BIBLIOGRAPHY)\b",
        re.IGNORECASE,
    )
    app_regex = re.compile(
        r"(?:^|\n)[ \t]*(LAMPIRAN|APPENDICES|APPENDIX)(?:\s+[A-Z0-9]+|\s*[:\-]|\b)",
        re.IGNORECASE,
    )

    bib_match = bib_regex.search(full_text)
    app_match_in_full = app_regex.search(full_text)

    # Anomaly: Appendix heading occurs before Bibliography
    if bib_match and app_match_in_full and app_match_in_full.start() < bib_match.start():
        return DocumentSegmentation(
            body_text=full_text,
            bib_text="",
            appendix_text="",
            bib_present=True,
            appendix_present=True,
            boundaries_reliable=False,
            unreliable_reason="Non-standard document structure: Appendix detected before Bibliography.",
        )

    if not bib_match:
        # No bibliography section found
        if app_match_in_full:
            body_text = full_text[: app_match_in_full.start()].strip()
            appendix_text = full_text[app_match_in_full.start() :].strip()
            return DocumentSegmentation(
                body_text=body_text,
                bib_text="",
                appendix_text=appendix_text,
                bib_present=False,
                appendix_present=True,
                boundaries_reliable=True,
            )
        return DocumentSegmentation(
            body_text=full_text.strip(),
            bib_text="",
            appendix_text="",
            bib_present=False,
            appendix_present=False,
            boundaries_reliable=True,
        )

    # Bibliography is present
    bib_header_start = bib_match.start()
    bib_content_start = bib_match.end()

    body_text = full_text[:bib_header_start].strip()
    text_after_bib = full_text[bib_content_start:]

    app_match = app_regex.search(text_after_bib)
    if app_match:
        bib_text = text_after_bib[: app_match.start()].strip()
        appendix_text = text_after_bib[app_match.start() :].strip()
        return DocumentSegmentation(
            body_text=body_text,
            bib_text=bib_text,
            appendix_text=appendix_text,
            bib_present=True,
            appendix_present=True,
            boundaries_reliable=True,
        )

    return DocumentSegmentation(
        body_text=body_text,
        bib_text=text_after_bib.strip(),
        appendix_text="",
        bib_present=True,
        appendix_present=False,
        boundaries_reliable=True,
    )


def extract_citations_from_text(text: str, section: str = "body") -> list[InTextCitation]:
    """Extracts APA 7 parenthetical and narrative citations from a specific section."""
    citations: list[InTextCitation] = []

    # 1. Parenthetical citations: (Smith, 2020), (Smith, 2020; Jones, 2021), (Smith, 2020a, 2020b)
    # Exclude newlines inside inner block to prevent multi-line cross-paragraph bleed
    paren_pattern = re.compile(r"\((?P<inner>[A-Z][^()\n]*?(?:19|20)\d{2}[a-z]?[^()\n]*?)\)")
    for m in paren_pattern.finditer(text):
        inner = m.group("inner").strip()
        # Split compound citations separated by semicolon
        entries = [e.strip() for e in inner.split(";") if e.strip()]
        for entry in entries:
            # Check for multiple years for same author, e.g. "Smith, 2020a, 2020b"
            years = re.findall(r"\b((?:19|20)\d{2}[a-z]?)\b", entry)
            if not years:
                continue

            author_part_match = re.search(r"^(?P<author>[A-Za-z\s\.\-–]+?)(?:,\s*(?:19|20)\d{2}|$)", entry)
            if not author_part_match:
                continue

            author_raw = author_part_match.group("author").strip()
            surname, initials = parse_author_tokens(author_raw)
            if not surname or len(surname) < 2:
                continue

            for y in years:
                citations.append(
                    InTextCitation(
                        raw=f"{author_raw}, {y}",
                        author=author_raw,
                        surname=surname,
                        year=y,
                        initials=initials,
                        is_narrative=False,
                        section=section,
                    )
                )

    # 2. Narrative citations: Author (Year), Author et al. (Year), Menurut Author (Year), Penelitian Author (Year)
    # [ \t]+ enforces horizontal whitespace only (never match across line breaks or headings)
    narrative_pattern = re.compile(
        r"(?P<discourse>\b(?:menurut|berdasarkan|kajian|studi|penelitian|artikel|buku|tulisan|"
        r"pendapat|pandangan|temuan|hasil|teori|model|oleh|dalam|pada|dari)\s+)?"
        r"(?P<author>[A-Z][A-Za-z\.\-–]+(?:[ \t]+(?:[A-Z][A-Za-z\.\-–]+|et\s+al\.|dkk\.|\&|dan|and)){0,4})"
        r"[ \t]*\((?P<years>(?:19|20)\d{2}[a-z]?(?:[ \t]*,[ \t]*(?:19|20)\d{2}[a-z]?)*)\)"
    )
    for m in narrative_pattern.finditer(text):
        author_raw = m.group("author").strip()
        years_str = m.group("years").strip()
        surname, initials = parse_author_tokens(author_raw)
        if not surname or len(surname) < 2:
            continue

        years = re.findall(r"\b((?:19|20)\d{2}[a-z]?)\b", years_str)
        for y in years:
            citations.append(
                InTextCitation(
                    raw=f"{author_raw} ({y})",
                    author=author_raw,
                    surname=surname,
                    year=y,
                    initials=initials,
                    is_narrative=True,
                    section=section,
                )
            )

    return citations


def parse_bibliography_entries(bib_text: str) -> list[BibliographyEntry]:
    """Parses individual bibliography entries formatted according to APA 7.

    Extracts author section, distinct author surnames, author initials, publication year,
    and trailing content (title, source). Author names in title are strictly excluded
    from author matching.
    """
    if not bib_text.strip():
        return []

    lines = [line.strip() for line in bib_text.splitlines() if len(line.strip()) > 10]
    entries: list[BibliographyEntry] = []

    for line in lines:
        # In APA 7, publication year is enclosed in parentheses: (2020), (2020a)
        year_match = re.search(r"\(((?:19|20)\d{2}[a-z]?)\)", line)
        if not year_match:
            # Fallback for references without parentheses around year
            year_match = re.search(r"\b((?:19|20)\d{2}[a-z]?)\b", line)

        if not year_match:
            continue

        year = year_match.group(1).strip()
        author_section = line[: year_match.start()].strip()
        title_and_rest = line[year_match.end() :].strip()

        # Parse surnames and initials strictly from author_section
        surnames: list[str] = []
        initials: list[str] = []

        tokens = re.split(r"[,;&]|\band\b|\bdan\b", author_section)
        for tok in tokens:
            t = tok.strip()
            if not t:
                continue
            # Check if token is initials e.g. "J. A.", "M.", "B", "A.B."
            if re.match(r"^(?:[A-Z]\.?\s*)+$", t) and (len(re.sub(r"[^a-zA-Z]", "", t)) <= 3 or "." in t):
                clean_init = re.sub(r"[^a-zA-Z]", "", t).lower()
                if clean_init:
                    initials.append(clean_init)
            else:
                words = re.findall(r"[A-Za-z\-–]+", t)
                for w in words:
                    w_lower = w.lower()
                    if len(w_lower) > 1 and w_lower not in (
                        "dkk", "et", "al", "and", "dan", "the", "ed", "eds", "editor"
                    ):
                        surnames.append(w_lower)

        entries.append(
            BibliographyEntry(
                raw=line,
                author_section=author_section,
                surnames=surnames,
                initials=initials,
                year=year,
                title_and_rest=title_and_rest,
            )
        )

    return entries


def citation_matches_reference(citation: InTextCitation, reference: BibliographyEntry) -> bool:
    """Verifies whether an in-text citation correctly matches a bibliography reference entry.

    Hardened matching rules:
    1. Publication year must match (exact match or letter suffix match).
    2. Citation surname must match a surname in the reference's author section (word boundary).
    3. If citation specifies author initials (e.g. 'A. Smith'), reference initials must match.
    4. Reference title and source text are NEVER used for author matching.
    """
    # 1. Year matching:
    cit_year = citation.year
    ref_year = reference.year
    if cit_year != ref_year:
        return False

    # 2. Author surname matching:
    if citation.surname not in reference.surnames:
        pattern = rf"\b{re.escape(citation.surname)}\b"
        if not re.search(pattern, reference.author_section, re.IGNORECASE):
            return False

    # 3. Disambiguation by initials if present in citation:
    if citation.initials:
        cit_init_clean = re.sub(r"[^a-z]", "", citation.initials.lower())
        ref_inits_clean = [re.sub(r"[^a-z]", "", i.lower()) for i in reference.initials]
        if not any(
            cit_init_clean.startswith(r) or r.startswith(cit_init_clean)
            for r in ref_inits_clean
        ):
            return False

    return True


def audit_citations(full_text: str) -> CitationAuditResult:
    """Executes full canonical citation and reference audit on document text."""
    segmentation = segment_document(full_text)

    body_citations = extract_citations_from_text(segmentation.body_text, section="body")
    appendix_citations = extract_citations_from_text(segmentation.appendix_text, section="appendix")
    references = parse_bibliography_entries(segmentation.bib_text)

    matched_pairs: list[tuple[InTextCitation, BibliographyEntry]] = []
    orphaned_citations: list[InTextCitation] = []

    # Check each body citation for a matching reference
    for cit in body_citations:
        matching_ref = None
        for ref in references:
            if citation_matches_reference(cit, ref):
                matching_ref = ref
                break

        if matching_ref is not None:
            matched_pairs.append((cit, matching_ref))
        else:
            orphaned_citations.append(cit)

    # Check each reference for usage in body text
    unused_references: list[BibliographyEntry] = []
    for ref in references:
        cited_in_body = any(citation_matches_reference(cit, ref) for cit in body_citations)
        if not cited_in_body:
            unused_references.append(ref)

    return CitationAuditResult(
        body_citations=body_citations,
        appendix_citations=appendix_citations,
        references=references,
        orphaned_citations=orphaned_citations,
        unused_references=unused_references,
        matched_pairs=matched_pairs,
        segmentation=segmentation,
    )
