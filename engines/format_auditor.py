"""Format & Layout Auditor for checking typography, margins, spacing, and pagination."""

from __future__ import annotations

from typing import Any

from models.document_model import ParsedDocument


class FormatAuditor:
    """Performs deep format and layout auditing against MIKOM 2026 rules."""

    def __init__(self, document: ParsedDocument):
        self.doc = document

    def audit(self) -> list[dict[str, Any]]:
        findings = []
        fmt = self.doc.format_data

        # 1. Paper Margins Check
        left_m = fmt.get("left_margin_cm")
        top_m = fmt.get("top_margin_cm")
        bottom_m = fmt.get("bottom_margin_cm")
        right_m = fmt.get("right_margin_cm")

        if left_m is not None and abs(left_m - 4.0) > 0.2:
            findings.append({
                "rule_id": "FORMAT_MARGIN_LEFT_001",
                "category": "Format",
                "status": "ERROR",
                "field": "format.left_margin_cm",
                "actual": f"{left_m} cm",
                "expected": "4,0 cm",
                "message": f"Margin kiri tidak sesuai: {left_m} cm (seharusnya 4,0 cm).",
                "recommendation": "Ubah margin kiri menjadi 4,0 cm pada Page Setup.",
                "page": 1,
                "section": "Pengaturan Halaman"
            })

        if top_m is not None and abs(top_m - 4.0) > 0.2:
            findings.append({
                "rule_id": "FORMAT_MARGIN_TOP_001",
                "category": "Format",
                "status": "ERROR",
                "field": "format.top_margin_cm",
                "actual": f"{top_m} cm",
                "expected": "4,0 cm",
                "message": f"Margin atas tidak sesuai: {top_m} cm (seharusnya 4,0 cm).",
                "recommendation": "Ubah margin atas menjadi 4,0 cm pada Page Setup.",
                "page": 1,
                "section": "Pengaturan Halaman"
            })

        if bottom_m is not None and abs(bottom_m - 3.0) > 0.2:
            findings.append({
                "rule_id": "FORMAT_MARGIN_BOTTOM_001",
                "category": "Format",
                "status": "ERROR",
                "field": "format.bottom_margin_cm",
                "actual": f"{bottom_m} cm",
                "expected": "3,0 cm",
                "message": f"Margin bawah tidak sesuai: {bottom_m} cm (seharusnya 3,0 cm).",
                "recommendation": "Ubah margin bawah menjadi 3,0 cm pada Page Setup.",
                "page": 1,
                "section": "Pengaturan Halaman"
            })

        if right_m is not None and abs(right_m - 3.0) > 0.2:
            findings.append({
                "rule_id": "FORMAT_MARGIN_RIGHT_001",
                "category": "Format",
                "status": "ERROR",
                "field": "format.right_margin_cm",
                "actual": f"{right_m} cm",
                "expected": "3,0 cm",
                "message": f"Margin kanan tidak sesuai: {right_m} cm (seharusnya 3,0 cm).",
                "recommendation": "Ubah margin kanan menjadi 3,0 cm pada Page Setup.",
                "page": 1,
                "section": "Pengaturan Halaman"
            })

        # 2. Typography check (Font family, size, line spacing)
        font_family = fmt.get("font_family")
        if font_family and font_family.lower() not in ["times new roman", "times"]:
            findings.append({
                "rule_id": "FORMAT_FONT_FAMILY_001",
                "category": "Format",
                "status": "ERROR",
                "field": "typography.font_family",
                "actual": font_family,
                "expected": "Times New Roman",
                "message": f"Jenis huruf ({font_family}) tidak sesuai pedoman.",
                "recommendation": "Ubah font seluruh naskah menjadi Times New Roman.",
                "page": 1,
                "section": "Tipografi"
            })

        # 3. Page Count Limit Check (Batasan 175 halaman dihilangkan)
        if self.doc.page_count is not None:
            findings.append({
                "rule_id": "FORMAT_PAGE_LIMIT_001",
                "category": "Format",
                "status": "PASS",
                "field": "page_count",
                "actual": f"{self.doc.page_count} halaman",
                "expected": "Panjang naskah fleksibel",
                "message": f"Jumlah halaman naskah terverifikasi: {self.doc.page_count} halaman.",
                "recommendation": "Pertahankan kedalaman pembahasan materi.",
                "page": self.doc.page_count,
                "section": "Batas Naskah"
            })

        # 4. Target Volume Kata Bab I–V (40.000 – 60.000 Kata, Tanpa Gambar & Tabel)
        body_words = getattr(self.doc, "body_word_count", None)
        if body_words is not None:
            if body_words < 40000:
                wc_status = "ERROR"
                wc_msg = f"Volume naskah Bab I–V ({body_words:,} kata) di bawah batas minimal 40.000 kata."
                wc_rec = "Tambahkan pembahasan substantif pada Bab IV dan pengayaan kajian pustaka Bab II."
            elif body_words > 60000:
                wc_status = "WARNING"
                wc_msg = f"Volume naskah Bab I–V ({body_words:,} kata) melebihi batas rekomendasi 60.000 kata."
                wc_rec = "Lakukan pemadatan dan peringkasan pada narasi deskriptif."
            else:
                wc_status = "PASS"
                wc_msg = f"Volume naskah Bab I–V ({body_words:,} kata) memenuhi standar target MIKOM 2026."
                wc_rec = "Pertahankan proporsi pembahasan."

            findings.append({
                "rule_id": "FORMAT_WORD_COUNT_001",
                "category": "Format",
                "status": wc_status,
                "field": "body_word_count",
                "actual": f"{body_words:,} kata",
                "expected": "40.000 – 60.000 kata",
                "message": wc_msg,
                "recommendation": wc_rec,
                "page": 1,
                "section": "Volume Naskah Bab I–V"
            })

        return findings
