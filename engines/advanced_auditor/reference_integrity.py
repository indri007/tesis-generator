import difflib
import re
from typing import Any, Dict, List
from docx import Document


class ReferenceIntegrityAuditor:
    """Auditor integritas referensi: mendeteksi typo dan inkonsistensi nama penulis antara sitasi di teks dan Daftar Pustaka."""

    def __init__(self, similarity_threshold: float = 0.75):
        self.similarity_threshold = similarity_threshold

    def audit(self, docx_path: str) -> List[Dict[str, Any]]:
        findings = []
        try:
            doc = Document(docx_path)
        except Exception as e:
            return [{"type": "ERROR", "message": f"Gagal membaca dokumen docx: {e}"}]

        in_text_citations = []
        bib_authors = []
        inside_bib = False

        # Pola sitasi in-text: (Nama, 2023), (Nama & Nama, 2020), Nama (2023)
        cite_pattern_paren = re.compile(r"\(([A-Z][a-zA-Z\s\.\,\&]+?),\s*([12][09]\d{2}[a-z]?)\)")
        cite_pattern_narrative = re.compile(r"\b([A-Z][a-zA-Z]+(?:\s+(?:dan|&|and)\s+[A-Z][a-zA-Z]+)?)\s*\(([12][09]\d{2}[a-z]?)\)")

        # Ekstraksi paragraf teks vs daftar pustaka
        for para in doc.paragraphs:
            text = para.text.strip()
            if not text:
                continue

            if re.match(r"^DAFTAR PUSTAKA\b|^REFERENCES\b|^BIBLIOGRAPHY\b", text, re.I):
                inside_bib = True
                continue

            if inside_bib:
                # Format APA: NamaBelakang, Inisial. (Tahun)...
                match_author = re.match(r"^([A-Z][a-zA-Z\-]+(?:\s+[A-Z][a-zA-Z\-]+)?)", text)
                if match_author:
                    author_lead = match_author.group(1).strip()
                    # Ambil kata pertama (biasanya surname)
                    surname = author_lead.split()[0].replace(",", "")
                    if len(surname) > 2:
                        bib_authors.append(surname)
            else:
                # Cari in-text citations
                for m in cite_pattern_paren.finditer(text):
                    author_str = m.group(1).strip()
                    year = m.group(2).strip()
                    # Bersihkan et al, dkk
                    author_clean = re.sub(r"\b(et al\.|dkk\.|and|dan|&)\b", " ", author_str, flags=re.I)
                    for a in author_clean.split():
                        a_clean = a.strip(".,;: ")
                        if len(a_clean) > 2 and a_clean.isalpha():
                            in_text_citations.append({"name": a_clean, "year": year, "full": f"({author_str}, {year})"})

                for m in cite_pattern_narrative.finditer(text):
                    author_str = m.group(1).strip()
                    year = m.group(2).strip()
                    author_clean = re.sub(r"\b(et al\.|dkk\.|and|dan|&)\b", " ", author_str, flags=re.I)
                    for a in author_clean.split():
                        a_clean = a.strip(".,;: ")
                        if len(a_clean) > 2 and a_clean.isalpha():
                            in_text_citations.append({"name": a_clean, "year": year, "full": f"{author_str} ({year})"})

        bib_names_unique = list(set(bib_authors))

        # Bandingkan nama in-text dengan daftar pustaka
        seen_warnings = set()
        for cite in in_text_citations:
            name = cite["name"]
            if name.lower() in ["bab", "gambar", "tabel", "figure", "table", "hal", "halaman", "vol", "no"]:
                continue

            # Exact match (case insensitive)
            exact_match = any(b.lower() == name.lower() for b in bib_names_unique)
            if exact_match:
                continue

            # Cari kemungkinan typo menggunakan difflib
            matches = difflib.get_close_matches(name, bib_names_unique, n=1, cutoff=self.similarity_threshold)
            key = f"{name}_{cite['year']}"
            if key in seen_warnings:
                continue
            seen_warnings.add(key)

            if matches:
                closest = matches[0]
                ratio = round(difflib.SequenceMatcher(None, name.lower(), closest.lower()).ratio(), 2)
                findings.append({
                    "type": "AUTHOR_TYPO_MISMATCH",
                    "in_text_author": name,
                    "bib_suggested": closest,
                    "similarity": f"{ratio:.0%}",
                    "citation": cite["full"],
                    "message": f"Dugaan typo nama penulis: '{name}' dalam kutipan {cite['full']} mirip dengan '{closest}' di Daftar Pustaka ({ratio:.0%} match)."
                })
            else:
                findings.append({
                    "type": "MISSING_IN_BIBLIOGRAPHY",
                    "in_text_author": name,
                    "bib_suggested": "-",
                    "similarity": "0%",
                    "citation": cite["full"],
                    "message": f"Kutipan '{name}' dalam {cite['full']} tidak ditemukan entri rujukannya di Daftar Pustaka."
                })

        return findings
