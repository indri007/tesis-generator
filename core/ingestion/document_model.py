from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from parsers.formula_parser import FormulaParser
from parsers.structure_parser import DocumentStructure
from utils.number_utils import check_formula_recalculation, parse_id_number


@dataclass
class ParsedParagraph:
    text: str
    page: int | None = None
    section: str | None = None
    style: str | None = None
    source_type: str = "paragraph"


@dataclass
class ParsedTable:
    rows: list[list[str]]
    page: int | None = None


@dataclass
class ParsedDocument:
    filename: str
    file_type: str
    page_count: int | None = None

    paragraphs: list[ParsedParagraph] = field(
        default_factory=list
    )
    tables: list[ParsedTable] = field(
        default_factory=list
    )

    metadata: dict[str, Any] = field(
        default_factory=dict
    )
    format_data: dict[str, Any] = field(
        default_factory=dict
    )
    warnings: list[str] = field(
        default_factory=list
    )
    journal_document: ParsedDocument | None = None

    def get_text(self) -> str:
        return "\n".join(
            p.text for p in self.paragraphs
        )

    def get_effective_page_count(self) -> int:
        """Returns a guaranteed positive integer page count, calculating academic word density for DOCX if missing."""
        if isinstance(self.page_count, int) and self.page_count > 0:
            return self.page_count
        words = len(self.get_text().split())
        estimated = max(1, round(words / 275)) if words > 0 else 1
        self.page_count = estimated
        return estimated

    def to_rule_input(self) -> dict:
        full_text = self.get_text()

        # 1. Structure Analysis
        struct = DocumentStructure(full_text)

        # 2. Extract citations
        # e.g., (Smith, 2022) or Smith (2022)
        citation_pattern = re.compile(
            r"(?:\((?P<cit_paren>[A-Z][a-zA-Z\s\-–]+(?:,\s*(?:19|20)\d{2}|[a-zA-Z\s]+,\s*(?:19|20)\d{2}))\)|(?P<cit_narrative>[A-Z][a-zA-Z\s\-–]+)\s*\((?P<cit_year>(?:19|20)\d{2})\))"
        )
        found_citations = []
        for m in citation_pattern.finditer(full_text):
            cit_text = m.group("cit_paren") or f"{m.group('cit_narrative')}, {m.group('cit_year')}"
            author = cit_text.split(",")[0].strip()
            found_citations.append({"raw": cit_text, "author": author})

        # 3. Extract bibliography entries
        bib_lines = struct.bibliography.get("lines", [])
        bib_text = struct.bibliography.get("text", "")
        orphaned_citations = 0
        if bib_lines:
            bib_lower = bib_text.lower()
            for c in found_citations:
                author_first = c["author"].split()[0].lower()
                if len(author_first) > 2 and author_first not in bib_lower:
                    orphaned_citations += 1

        unused_references = 0
        if bib_lines:
            body_before_bib = full_text[:full_text.lower().find("daftar pustaka")] if "daftar pustaka" in full_text.lower() else full_text
            body_lower = body_before_bib.lower()
            for line in bib_lines[1:]:
                words = line.split()
                if words and len(words[0]) > 2:
                    ref_author = words[0].strip(".,;:").lower()
                    if ref_author not in body_lower:
                        unused_references += 1

        # 4. Variable Consistency
        # Look for variable definitions like:
        # X1 = Kualitas Sistem
        # X1 adalah Kualitas Sistem
        var_pattern = re.compile(
            r"\b([XYZ]\d?)\s*(?:=|adalah|merupakan|yakni|yaitu)\s*([\"'‘“]?)([A-Za-z\s]+)\2",
            re.IGNORECASE
        )
        var_occurrences: dict[str, list[dict[str, Any]]] = {}
        for chap_name, chap_data in struct.chapters.items():
            chap_text = chap_data.get("text", "")
            for m in var_pattern.finditer(chap_text):
                var_key = m.group(1).upper()
                var_def = m.group(3).strip()
                if len(var_def) > 3 and len(var_def.split()) <= 5:
                    var_occurrences.setdefault(var_key, []).append({
                        "chapter": chap_name,
                        "definition": var_def
                    })

        var_inconsistency_count = 0
        for var_key, occurrences in var_occurrences.items():
            defs = {o["definition"].lower() for o in occurrences}
            if len(defs) > 1:
                var_inconsistency_count += 1

        # 5. Formula & Recalculation
        form_parser = FormulaParser(full_text)
        recalc_cases = form_parser.extract_recalculation_cases()
        arithmetic_error_count = 0
        evaluated_formulas = []
        for case in recalc_cases:
            dep_var = case["dependent_var"]
            f_body = case["formula_body"]
            input_v = case["input_var"]
            input_num = parse_id_number(case["input_value"])
            claimed_num = parse_id_number(case["claimed_result"])
            if input_num is not None and claimed_num is not None:
                recalc_res = check_formula_recalculation(
                    dep_var, f_body, {input_v: input_num}, claimed_num
                )
                evaluated_formulas.append(recalc_res)
                if recalc_res["status"] == "ERROR":
                    arithmetic_error_count += 1

        # Model consistency between BAB III and BAB IV
        model_mismatch_count = 0
        b3_text = struct.chapters.get("BAB III", {}).get("text", "")
        b4_text = struct.chapters.get("BAB IV", {}).get("text", "")
        if b3_text and b4_text:
            b3_formulas = form_parser.__class__(b3_text).extract_equations()
            b4_formulas = form_parser.__class__(b4_text).extract_equations()
            if b3_formulas and b4_formulas:
                b3_vars = set(b3_formulas[0]["variables"])
                b4_vars = set(b4_formulas[0]["variables"])
                if b3_vars != b4_vars and len(b3_vars) > 0 and len(b4_vars) > 0:
                    model_mismatch_count += 1

        # 6. Statistical Consistency
        # Detect sample sizes: "sampel sebanyak 120" vs "118 responden"
        sample_b3 = re.findall(r"(?:sebanyak|sebesar|=|\b)\s*(\d{2,4})\s*(?:orang|responden)", b3_text, re.IGNORECASE)
        sample_b4 = re.findall(r"(?:sebanyak|sebesar|=|\b)\s*(\d{2,4})\s*(?:orang|responden)", b4_text, re.IGNORECASE)
        sample_mismatch_count = 0
        if sample_b3 and sample_b4:
            s3 = int(sample_b3[0])
            s4 = int(sample_b4[0])
            if s3 != s4 and "dikeluarkan" not in b4_text.lower() and "drop" not in b4_text.lower():
                sample_mismatch_count += 1

        # Check p-value contradiction
        # e.g., p = 0.032 < 0.05 but text claims "tidak signifikan"
        p_matches = re.findall(r"\bp\s*(?:[=<]|value)\s*([0-9.,]+)", b4_text, re.IGNORECASE)
        contradiction_count = 0
        if p_matches:
            p_val = parse_id_number(p_matches[0])
            if p_val is not None:
                if p_val < 0.05 and any(phrase in b4_text.lower() for phrase in ["tidak signifikan", "tidak berpengaruh signifikan", "h1 ditolak"]) or p_val >= 0.05 and any(phrase in b4_text.lower() for phrase in ["berpengaruh signifikan", "h1 diterima"]):
                    contradiction_count += 1

        # 7. Journal vs Thesis Alignment
        journal_mismatch_count = 0
        if self.journal_document:
            j_text = self.journal_document.get_text()
            j_samples = re.findall(r"(?:sampel|responden|sample)\s*(?:sebanyak|sebesar|=)?\s*(\d{2,4})", j_text, re.IGNORECASE)
            if sample_b3 and j_samples:
                if int(sample_b3[0]) != int(j_samples[0]):
                    journal_mismatch_count += 1

        # Section margin fallback
        fmt = self.format_data
        left_m = fmt.get("left_margin_cm") or 4.0
        top_m = fmt.get("top_margin_cm") or 4.0
        bottom_m = fmt.get("bottom_margin_cm") or 3.0
        right_m = fmt.get("right_margin_cm") or 3.0

        return {
            "metadata": self.metadata,
            "format": self.format_data,
            "margins": {
                "top_cm": top_m,
                "left_cm": left_m,
                "bottom_cm": bottom_m,
                "right_cm": right_m,
            },
            "typography": {
                "font_family": fmt.get("font_family", "Times New Roman"),
                "font_size_pt": fmt.get("font_size_pt", 12),
                "line_spacing": fmt.get("line_spacing", 2.0),
                "alignment": fmt.get("alignment", "JUSTIFY"),
            },
            "page_count": self.page_count,
            "word_count": {
                "total_body_words": struct.total_body_words,
                "bab_1_words": struct.chapters.get("BAB I", {}).get("word_count", 0),
                "bab_2_words": struct.chapters.get("BAB II", {}).get("word_count", 0),
                "bab_3_words": struct.chapters.get("BAB III", {}).get("word_count", 0),
                "bab_4_words": struct.chapters.get("BAB IV", {}).get("word_count", 0),
                "bab_5_words": struct.chapters.get("BAB V", {}).get("word_count", 0),
            },
            "chapters": {
                "BAB_I": {"exists": struct.chapters.get("BAB I", {}).get("is_present", False)},
                "BAB_II": {"exists": struct.chapters.get("BAB II", {}).get("is_present", False)},
                "BAB_III": {"exists": struct.chapters.get("BAB III", {}).get("is_present", False)},
                "BAB_IV": {"exists": struct.chapters.get("BAB IV", {}).get("is_present", False)},
                "BAB_V": {"exists": struct.chapters.get("BAB V", {}).get("is_present", False)},
            },
            "bibliography": {
                "exists": struct.bibliography.get("is_present", False),
                "count": len(bib_lines),
            },
            "abstract": {
                "id": struct.preliminaries.get("abstract_id", {}),
                "en": struct.preliminaries.get("abstract_en", {})
            },
            "citations": {
                "count": len(found_citations),
                "orphaned_count": orphaned_citations
            },
            "references": {
                "count": len(bib_lines),
                "unused_count": unused_references
            },
            "variables": {
                "inconsistency_count": var_inconsistency_count,
                "items": var_occurrences
            },
            "formulas": {
                "recalculated_cases": evaluated_formulas,
                "arithmetic_error_count": arithmetic_error_count,
                "model_mismatch_count": model_mismatch_count
            },
            "statistics": {
                "contradiction_count": contradiction_count,
                "sample_mismatch_count": sample_mismatch_count
            },
            "journal_comparison": {
                "critical_mismatch_count": journal_mismatch_count
            },
            "content": {
                "text": full_text,
                "citations": [c["raw"] for c in found_citations],
                "paragraph_count": len(self.paragraphs),
                "table_count": len(self.tables),
            },
            "document": {
                "filename": self.filename,
                "file_type": self.file_type,
                "page_count": self.page_count,
            },
        }
