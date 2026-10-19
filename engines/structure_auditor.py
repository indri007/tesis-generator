"""Structure Auditor: Audits chapter presence, digital numbering, word counts, proportions, and abstract."""

from __future__ import annotations

from typing import Any

from models.document_model import ParsedDocument
from parsers.structure_parser import DocumentStructure


class StructureAuditor:
    """Audits structural integrity, chapter proportions, and sub-heading sequencing."""

    def __init__(self, document: ParsedDocument):
        self.doc = document
        self.text = document.get_text()
        self.structure = DocumentStructure(self.text)

    def audit(self) -> list[dict[str, Any]]:
        findings = []

        # 1. Check presence of 5 main chapters
        required_chapters = ["BAB I", "BAB II", "BAB III", "BAB IV", "BAB V"]
        for ch in required_chapters:
            ch_data = self.structure.chapters.get(ch, {})
            if not ch_data.get("is_present", False):
                findings.append({
                    "rule_id": f"STRUCT_CHAP_{ch.replace(' ', '')}_001",
                    "category": "Struktur",
                    "status": "ERROR",
                    "field": f"chapters.{ch.replace(' ', '_')}.exists",
                    "actual": "Tidak ditemukan",
                    "expected": f"Memuat {ch}",
                    "message": f"Struktur pokok {ch} tidak ditemukan dalam naskah tesis.",
                    "recommendation": f"Sertakan bagian {ch} sesuai sistematika Pedoman MIKOM 2026.",
                    "page": None,
                    "section": ch
                })

        # 2. Check total body word count (40.000 - 60.000)
        total_words = self.structure.total_body_words
        if total_words > 0:
            if total_words < 40000:
                shortage = 40000 - total_words
                findings.append({
                    "rule_id": "STRUCT_WORDS_MIN_001",
                    "category": "Struktur",
                    "status": "ERROR",
                    "field": "word_count.total_body_words",
                    "actual": f"{total_words:,} kata",
                    "expected": "Minimal 40.000 kata",
                    "message": f"Jumlah kata naskah utama ({total_words:,} kata) kurang {shortage:,} kata dari batas minimal 40.000 kata.",
                    "recommendation": "Perdalam kajian literatur dan analisis pembahasan agar memenuhi batas minimal 40.000 kata.",
                    "page": 1,
                    "section": "Badan Tesis"
                })
            elif total_words > 60000:
                excess = total_words - 60000
                findings.append({
                    "rule_id": "STRUCT_WORDS_MAX_001",
                    "category": "Struktur",
                    "status": "ERROR",
                    "field": "word_count.total_body_words",
                    "actual": f"{total_words:,} kata",
                    "expected": "Maksimal 60.000 kata",
                    "message": f"Jumlah kata naskah utama ({total_words:,} kata) melebihi {excess:,} kata dari batas maksimal 60.000 kata.",
                    "recommendation": "Ringkas dan padatkan analisis agar tidak melampaui 60.000 kata.",
                    "page": 1,
                    "section": "Badan Tesis"
                })

        # 3. Chapter Proportions Check
        expected_prop = {
            "BAB I": {"target": 15.0, "min": 6000, "max": 9000},
            "BAB II": {"target": 25.0, "min": 10000, "max": 15000},
            "BAB III": {"target": 15.0, "min": 6000, "max": 9000},
            "BAB IV": {"target": 35.0, "min": 14000, "max": 21000},
            "BAB V": {"target": 10.0, "min": 4000, "max": 6000},
        }

        if total_words >= 30000:
            for ch, rule in expected_prop.items():
                ch_words = self.structure.chapters.get(ch, {}).get("word_count", 0)
                actual_pct = round((ch_words / total_words) * 100.0, 1)
                target_pct = rule["target"]

                if actual_pct < (target_pct - 5.0) or actual_pct > (target_pct + 5.0):
                    findings.append({
                        "rule_id": f"PROP_{ch.replace(' ', '')}_001",
                        "category": "Struktur",
                        "status": "WARNING",
                        "field": f"word_count.{ch.lower().replace(' ', '_')}_proportion",
                        "actual": f"{actual_pct}% ({ch_words:,} kata)",
                        "expected": f"Target {target_pct}% ({rule['min']:,} - {rule['max']:,} kata)",
                        "message": f"Proporsi kata {ch} adalah {actual_pct}%, di luar proporsi ideal {target_pct}%.",
                        "recommendation": f"Sesuaikan proporsi {ch} ke rentang {rule['min']:,} - {rule['max']:,} kata.",
                        "page": 1,
                        "section": ch
                    })

        # 4. Check digital subbab numbering sequence
        for ch, data in self.structure.chapters.items():
            subbabs = data.get("subbabs", [])
            seen_nums = []
            for s in subbabs:
                parts = s["number"].split(".")
                if len(parts) >= 2 and parts[1].isdigit():
                    seen_nums.append(int(parts[1]))

            if seen_nums:
                sorted_unique = sorted(set(seen_nums))
                for exp in range(1, max(sorted_unique) + 1):
                    if exp not in sorted_unique:
                        findings.append({
                            "rule_id": "STRUCT_SUBBAB_SEQUENCE_001",
                            "category": "Struktur",
                            "status": "ERROR",
                            "field": "chapters.subbab_sequence",
                            "actual": f"Nomor {ch.split()[-1]}.{exp} terlewat",
                            "expected": "Penomoran subbab berurutan",
                            "message": f"Nomor subbab {ch.split()[-1]}.{exp} tidak ditemukan (lompatan penomoran).",
                            "recommendation": "Periksa penomoran subbab agar berurutan tanpa lompatan digit.",
                            "page": 1,
                            "section": ch
                        })

        # 5. Abstract Check
        abst_id = self.structure.preliminaries.get("abstract_id", {})
        if abst_id.get("is_present"):
            w_count = abst_id.get("word_count", 0)
            if w_count < 150 or w_count > 250:
                findings.append({
                    "rule_id": "ABST_WORDS_001",
                    "category": "Abstrak",
                    "status": "ERROR",
                    "field": "abstract.id.word_count",
                    "actual": f"{w_count} kata",
                    "expected": "150 - 250 kata",
                    "message": f"Panjang Abstrak ({w_count} kata) tidak sesuai rentang 150-250 kata.",
                    "recommendation": "Sesuaikan panjang abstrak Bahasa Indonesia agar berada di antara 150 hingga 250 kata.",
                    "page": 1,
                    "section": "Abstrak"
                })

            kw_count = abst_id.get("keyword_count", 0)
            if kw_count < 3 or kw_count > 5:
                findings.append({
                    "rule_id": "ABST_KEYWORDS_001",
                    "category": "Abstrak",
                    "status": "WARNING",
                    "field": "abstract.id.keyword_count",
                    "actual": f"{kw_count} kata kunci",
                    "expected": "3 - 5 kata kunci",
                    "message": f"Jumlah kata kunci abstrak ({kw_count}) tidak sesuai ketentuan (3-5 kata kunci).",
                    "recommendation": "Sertakan 3 sampai 5 kata kunci yang mewakili konsep penelitian.",
                    "page": 1,
                    "section": "Abstrak"
                })

        return findings
