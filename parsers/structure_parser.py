"""Structure parser for identifying chapters, subbabs, preliminaries, bibliography, and word counts."""

from __future__ import annotations

import re
from typing import Any


class DocumentStructure:
    """Hierarchical document model representing thesis structure."""

    def __init__(self, raw_text: str, pages_data: list[dict[str, Any]] | None = None):
        self.raw_text = raw_text
        self.pages_data = pages_data or []
        self.chapters: dict[str, dict[str, Any]] = {}
        self.preliminaries: dict[str, Any] = {}
        self.bibliography: dict[str, Any] = {}
        self.appendices: dict[str, Any] = {}
        self.total_body_words = 0
        self.detected_type: str = "Auto"
        self._parse()

    def _parse(self) -> None:
        """Parses the document into chapters, sub-headings, and special sections."""
        # Split text into lines
        lines = [line.strip() for line in self.raw_text.splitlines() if line.strip()]

        current_section = "PRELIMINARY"
        sections_content: dict[str, list[str]] = {
            "PRELIMINARY": [],
            "BAB I": [],
            "BAB II": [],
            "BAB III": [],
            "BAB IV": [],
            "BAB V": [],
            "DAFTAR PUSTAKA": [],
            "LAMPIRAN": []
        }

        # Regex patterns for chapter headers
        chap_patterns = {
            "BAB I": re.compile(r"^BAB\s+I\b[\s\.:\-]*(PENDAHULUAN)?", re.IGNORECASE),
            "BAB II": re.compile(r"^BAB\s+II\b[\s\.:\-]*(TINJAUAN\s+PUSTAKA|LANDASAN\s+TEORI)?", re.IGNORECASE),
            "BAB III": re.compile(r"^BAB\s+III\b[\s\.:\-]*(METODE\s+PENELITIAN|METODOLOGI)?", re.IGNORECASE),
            "BAB IV": re.compile(r"^BAB\s+IV\b[\s\.:\-]*(HASIL\s+DAN\s+PEMBAHASAN|ANALISIS\s+DATA)?", re.IGNORECASE),
            "BAB V": re.compile(r"^BAB\s+V\b[\s\.:\-]*(KESIMPULAN|SIMPULAN|PENUTUP)?", re.IGNORECASE),
            "DAFTAR PUSTAKA": re.compile(r"^(DAFTAR\s+PUSTAKA|DAFTAR\s+RUJUKAN|REFERENCES)\b", re.IGNORECASE),
            "LAMPIRAN": re.compile(r"^(LAMPIRAN|APPENDICES)\b", re.IGNORECASE),
        }

        for line in lines:
            matched_chap = None
            for chap_key, pattern in chap_patterns.items():
                if pattern.match(line):
                    matched_chap = chap_key
                    break

            if matched_chap:
                current_section = matched_chap
                sections_content[current_section].append(line)
            else:
                sections_content.setdefault(current_section, []).append(line)

        # Build chapter structures and word counts
        body_words = 0
        for ch_key in ["BAB I", "BAB II", "BAB III", "BAB IV", "BAB V"]:
            text_lines = sections_content.get(ch_key, [])
            text_str = " ".join(text_lines)
            words = text_str.split()
            word_count = len(words)
            if text_lines:
                body_words += word_count
                subbabs = self._extract_subbabs(text_lines)
                self.chapters[ch_key] = {
                    "title": text_lines[0] if text_lines else ch_key,
                    "text": text_str,
                    "lines": text_lines,
                    "word_count": word_count,
                    "subbabs": subbabs,
                    "is_present": True
                }
            else:
                self.chapters[ch_key] = {
                    "title": ch_key,
                    "text": "",
                    "lines": [],
                    "word_count": 0,
                    "subbabs": [],
                    "is_present": False
                }

        self.total_body_words = body_words
        self.preliminaries = {
            "text": " ".join(sections_content.get("PRELIMINARY", [])),
            "word_count": len(" ".join(sections_content.get("PRELIMINARY", [])).split()),
            "abstract_id": self._extract_abstract("ID"),
            "abstract_en": self._extract_abstract("EN")
        }
        self.bibliography = {
            "text": " ".join(sections_content.get("DAFTAR PUSTAKA", [])),
            "lines": sections_content.get("DAFTAR PUSTAKA", []),
            "word_count": len(" ".join(sections_content.get("DAFTAR PUSTAKA", [])).split()),
            "is_present": len(sections_content.get("DAFTAR PUSTAKA", [])) > 0
        }
        self.appendices = {
            "text": " ".join(sections_content.get("LAMPIRAN", [])),
            "is_present": len(sections_content.get("LAMPIRAN", [])) > 0
        }

        # Auto-detect research type (Kuantitatif vs Kualitatif)
        self.detected_type = self._detect_research_type()

    def _extract_subbabs(self, lines: list[str]) -> list[dict[str, str]]:
        """Find subheadings like 1.1, 1.2, 1.2.1, 2.1 etc."""
        subbabs = []
        sub_pattern = re.compile(r"^(\d+\.\d+(?:\.\d+)?)\s+([A-Za-z].*)$")
        for line in lines:
            m = sub_pattern.match(line)
            if m:
                subbabs.append({
                    "number": m.group(1),
                    "title": m.group(2).strip(),
                    "raw": line
                })
        return subbabs

    def _extract_abstract(self, lang: str = "ID") -> dict[str, Any]:
        """Extracts Indonesian or English abstract text and keyword count."""
        raw = self.raw_text
        if lang == "ID":
            m = re.search(r"\bABSTRAK\b(.*?)(?=\bABSTRACT\b|\bBAB\s+I\b|\bDAFTAR\s+ISI\b|$)", raw, re.DOTALL | re.IGNORECASE)
        else:
            m = re.search(r"\bABSTRACT\b(.*?)(?=\bBAB\s+I\b|\bDAFTAR\s+ISI\b|$)", raw, re.DOTALL | re.IGNORECASE)

        if not m:
            return {"is_present": False, "word_count": 0, "text": "", "keywords": []}

        content = m.group(1).strip()
        words = content.split()

        # Keywords regex
        kw_match = re.search(r"(?:Kata\s*Kunci|Keywords?)\s*[:：](.*?)(?=\n\n|$)", content, re.IGNORECASE)
        keywords = []
        if kw_match:
            kw_raw = kw_match.group(1)
            keywords = [k.strip() for k in re.split(r"[,;]", kw_raw) if k.strip()]

        return {
            "is_present": True,
            "word_count": len(words),
            "text": content,
            "keywords": keywords,
            "keyword_count": len(keywords)
        }

    def _detect_research_type(self) -> str:
        """Determines if research is Quantitative, Qualitative, or Unspecified."""
        text_lower = self.raw_text.lower()
        quant_signals = ["kuantitatif", "regresi", "hipotesis", "p-value", "sampel", "koefisien", "f-hitung", "t-hitung", "uji t", "uji f", "spss", "smartpls", "sem"]
        qual_signals = ["kualitatif", "fenomenologi", "etnografi", "studi kasus", "informan", "triangulasi", "analisis tematik", "wawancara mendalam", "konstruktivisme"]

        quant_score = sum(text_lower.count(s) for s in quant_signals)
        qual_score = sum(text_lower.count(s) for s in qual_signals)

        if quant_score > qual_score * 1.5 and quant_score > 5:
            return "Kuantitatif"
        elif qual_score > quant_score * 1.5 and qual_score > 5:
            return "Kualitatif"
        return "Auto Detect (Tidak Pasti)"
