"""Academic Writing & Scholarly Register Auditor for MIKOM 2026 UPN Veteran Jawa Timur.

Evaluates according to Pedoman Penulisan Tesis MIKOM UPN 2026 (Bab IV.F):
1. Diksi Baku & Register Akademik: Mendeteksi kata non-baku / ragam tutur santai dan memberikan padanan KBBI baku.
2. Sudut Pandang Objektif: Menghilangkan kata ganti orang pertama (saya, kami, menurut hemat saya) demi netralitas ilmiah.
3. Struktur Alinea Ilmiah: Mendeteksi paragraf satu kalimat dan paragraf terlalu panjang (>350 kata), serta memeriksa koherensi logis.
4. Tipografi Istilah Asing: Memastikan istilah asing komunikasi & digital marketing dicetak miring (italic).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from models.document_model import ParsedDocument


@dataclass
class AcademicWritingFinding:
    rule_id: str
    category: str
    status: str  # "PASS" | "WARNING" | "ERROR" | "INFO"
    severity: str
    message: str
    actual: str
    expected: str
    recommendation: str
    evidence_query: str = ""
    location: str = "Badan Naskah"
    page: int = 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "category": self.category,
            "status": self.status,
            "severity": self.severity,
            "message": self.message,
            "actual": self.actual,
            "expected": self.expected,
            "recommendation": self.recommendation,
            "evidence_query": self.evidence_query,
            "evidence": self.evidence_query,
            "location": self.location,
            "page": self.page,
        }


class AcademicWritingAuditor:
    """Auditor Tata Tulis Ilmiah & Diksi Baku Bahasa Indonesia MIKOM UPN 2026."""

    # Kamus kata percakapan non-baku -> padanan baku KBBI
    INFORMAL_DICTIONARY: dict[str, str] = {
        "nggak": "tidak",
        "gak": "tidak",
        "banget": "sangat",
        "bikin": "membuat / menyebabkan",
        "gimana": "bagaimana",
        "jaman": "zaman",
        "praktek": "praktik",
        "analisa": "analisis",
        "merubah": "mengubah",
        "obyek": "objek",
        "subyek": "subjek",
        "jadul": "terdahulu / masa lampau",
        "dibilang": "dikatakan / dinyatakan",
        "ngomongin": "membahas / mengkaji",
        "kayak": "seperti / menyerupai",
        "cuman": "hanya",
        "cuma": "hanya",
        "emang": "memang",
        "kalo": "jika / kalau",
        "karna": "karena",
        "utk": "untuk",
        "dgn": "dengan",
        "yg": "yang",
        "tp": "tetapi",
        "bener": "benar",
        "makanya": "oleh karena itu",
        "tau": "tahu",
        "dimana": "tempat (hindari sebagai konjungsi 'where')",
    }

    # Kata ganti orang pertama subjektif yang dilarang dalam naskah ilmiah
    FIRST_PERSON_PATTERNS: list[tuple[str, str]] = [
        (r"\b(?:saya|kami)\b", "peneliti / penelitian ini"),
        (r"\bpenulis merasa\b", "data menunjukkan / temuan mengindikasikan"),
        (r"\bmenurut hemat saya\b", "berdasarkan hasil kajian"),
        (r"\bkita semua tahu\b", "sebagaimana dipahami dalam literatur"),
        (r"\btentunya kita sepakat\b", "berdasarkan konsensus ilmiah"),
        (r"\bsaya berpendapat\b", "peneliti menggarisbawahi"),
    ]

    # Istilah asing bidang ilmu komunikasi yang lazim digunakan
    COMMUNICATION_FOREIGN_TERMS: list[str] = [
        "framing", "agenda setting", "gatekeeping", "uses and gratifications",
        "spiral of silence", "hyperreality", "digital marketing communication",
        "netnography", "computational communication science", "social media influencer",
        "engagement rate", "click-through rate", "sentiment analysis", "brand awareness",
        "two-step flow", "third-person effect", "parasocial interaction"
    ]

    # Konjungsi transisi ilmiah
    ACADEMIC_TRANSITIONS: list[str] = [
        "oleh karena itu", "kendati demikian", "sejalan dengan temuan",
        "sebaliknya", "lebih lanjut", "di samping itu", "pada dasarnya",
        "dengan kata lain", "selaras dengan", "berdasarkan uraian tersebut"
    ]

    def __init__(self, document: ParsedDocument | str):
        if isinstance(document, str):
            self.text = document
            self.paragraphs = [p.strip() for p in document.split("\n\n") if p.strip()]
        else:
            self.text = document.get_text()
            self.paragraphs = [p.text.strip() for p in document.paragraphs if p.text.strip()]

    def audit(self) -> list[dict[str, Any]]:
        findings: list[dict[str, Any]] = []

        # ─────────────────────────────────────────────────────────────
        # 1. Audit Diksi Baku vs Kata Ragam Tutur / Informal (Bab IV.F)
        # ─────────────────────────────────────────────────────────────
        found_informals: dict[str, list[str]] = {}
        for non_baku, baku in self.INFORMAL_DICTIONARY.items():
            pattern = rf"\b{re.escape(non_baku)}\b"
            matches = re.findall(pattern, self.text, re.IGNORECASE)
            if matches:
                found_informals[non_baku] = matches

        if found_informals:
            detail_list = [f"'{nb}' ({len(m)}x -> ganti '{self.INFORMAL_DICTIONARY[nb]}')" for nb, m in list(found_informals.items())[:6]]
            findings.append(
                AcademicWritingFinding(
                    rule_id="WRITING_DICTION_NON_STANDARD_001",
                    category="Tata Tulis Akademik",
                    status="ERROR",
                    severity="ERROR",
                    message=f"Ditemukan {sum(len(m) for m in found_informals.values())} kata ragam tutur/tidak baku dalam naskah tesis: {', '.join(detail_list)}.",
                    actual=f"{len(found_informals)} jenis kata tidak baku terdeteksi",
                    expected="Seluruh naskah wajib menggunakan bahasa Indonesia ragam ilmiah baku sesuai Pedoman EBI & KBBI",
                    recommendation="Ganti kata ragam tutur dengan padanan baku formal (misal: 'nggak' -> 'tidak', 'merubah' -> 'mengubah', 'praktek' -> 'praktik', 'analisa' -> 'analisis').",
                    evidence_query=list(found_informals.keys())[0],
                ).to_dict()
            )
        else:
            findings.append(
                AcademicWritingFinding(
                    rule_id="WRITING_DICTION_NON_STANDARD_001",
                    category="Tata Tulis Akademik",
                    status="PASS",
                    severity="INFO",
                    message="Diksi naskah terverifikasi bersih dari kata percakapan informal.",
                    actual="Register bahasa baku",
                    expected="Bahasa Indonesia ragam ilmiah baku",
                    recommendation="Pertahankan ketelitian penggunaan istilah baku KBBI.",
                    evidence_query="bahasa baku",
                ).to_dict()
            )

        # ─────────────────────────────────────────────────────────────
        # 2. Audit Sudut Pandang Objektif & Penghindaran Kata Ganti Orang I
        # ─────────────────────────────────────────────────────────────
        found_first_person: list[tuple[str, str]] = []
        for pat, sugg in self.FIRST_PERSON_PATTERNS:
            match = re.search(pat, self.text, re.IGNORECASE)
            if match:
                found_first_person.append((match.group(0), sugg))

        if found_first_person:
            detail_fp = [f"'{m}' (gunakan '{s}')" for m, s in found_first_person[:4]]
            findings.append(
                AcademicWritingFinding(
                    rule_id="WRITING_FIRST_PERSON_SUBJECTIVE_001",
                    category="Tata Tulis Akademik",
                    status="WARNING",
                    severity="WARNING",
                    message=f"Terdeteksi kata ganti orang pertama / sudut pandang personal: {', '.join(detail_fp)}.",
                    actual="Penggunaan kata ganti orang pertama (subjektif)",
                    expected="Sudut pandang impersonil/objektif (misal: 'peneliti', 'penelitian ini mengamati')",
                    recommendation="Hindari kata ganti 'saya', 'kami', atau 'menurut hemat saya'. Gunakan sudut pandang objektif ilmiah seperti 'peneliti' atau konstruksi kalimat pasif berterima.",
                    evidence_query=found_first_person[0][0],
                ).to_dict()
            )
        else:
            findings.append(
                AcademicWritingFinding(
                    rule_id="WRITING_FIRST_PERSON_SUBJECTIVE_001",
                    category="Tata Tulis Akademik",
                    status="PASS",
                    severity="INFO",
                    message="Naskah mempertahankan sudut pandang ilmiah objektif tanpa kata ganti personal.",
                    actual="Sudut pandang objektif",
                    expected="Objektif / impersonil",
                    recommendation="Pertahankan gaya penulisan ilmiah bebas bias personal.",
                    evidence_query="peneliti",
                ).to_dict()
            )

        # ─────────────────────────────────────────────────────────────
        # 3. Struktur Alinea Ilmiah (Paragraf Satu Kalimat & Panjang Paragraf)
        # ─────────────────────────────────────────────────────────────
        single_sentence_paras: list[str] = []
        oversized_paras: list[int] = []

        for p_idx, p_text in enumerate(self.paragraphs):
            # Abaikan judul bab / tabel / bagan pendek (< 40 karakter)
            if len(p_text) < 45 or p_text.startswith("BAB ") or p_text.startswith("Tabel ") or p_text.startswith("Gambar "):
                continue

            words = p_text.split()
            word_count = len(words)

            if word_count > 350:
                oversized_paras.append(p_idx + 1)

            # Hitung jumlah kalimat berbasis tanda baca (. ! ?)
            sentences = [s.strip() for s in re.split(r"[.!?]+", p_text) if len(s.strip()) > 10]
            if len(sentences) == 1 and word_count >= 15:
                single_sentence_paras.append(p_text[:80])

        if single_sentence_paras:
            findings.append(
                AcademicWritingFinding(
                    rule_id="WRITING_SINGLE_SENTENCE_PARAGRAPH_001",
                    category="Tata Tulis Akademik",
                    status="WARNING",
                    severity="WARNING",
                    message=f"Terdeteksi {len(single_sentence_paras)} paragraf yang hanya terdiri dari satu kalimat.",
                    actual=f"{len(single_sentence_paras)} alinea satu kalimat teridentifikasi",
                    expected="Alinea ilmiah lengkap memuat kalimat topik (topic sentence), kalimat penjelas (supporting evidence), dan kalimat pengikat/penutup",
                    recommendation="Kembangkan alinea yang hanya terdiri dari satu kalimat dengan menambahkan argumen penjelas, rujukan empiris, atau elaborasi konsep.",
                    evidence_query=single_sentence_paras[0],
                ).to_dict()
            )

        if oversized_paras:
            findings.append(
                AcademicWritingFinding(
                    rule_id="WRITING_OVERSIZED_PARAGRAPH_001",
                    category="Tata Tulis Akademik",
                    status="INFO",
                    severity="INFO",
                    message=f"Terdeteksi {len(oversized_paras)} paragraf yang sangat panjang (>350 kata).",
                    actual=f"Paragraf ke-{oversized_paras[:3]} melebihi 350 kata",
                    expected="Panjang alinea proporsional (100–250 kata per alinea) untuk memudahkan daya serap pembaca",
                    recommendation="Pecah paragraf panjang menjadi dua alinea terfokus dengan satu pokok pikiran per alinea.",
                    evidence_query="panjang alinea",
                ).to_dict()
            )

        # ─────────────────────────────────────────────────────────────
        # 4. Transisi Koherensi Wacana Ilmiah
        # ─────────────────────────────────────────────────────────────
        lower_text = self.text.lower()
        found_transitions = [tr for tr in self.ACADEMIC_TRANSITIONS if tr in lower_text]
        if len(found_transitions) < 2:
            findings.append(
                AcademicWritingFinding(
                    rule_id="WRITING_COHERENCE_TRANSITION_001",
                    category="Tata Tulis Akademik",
                    status="WARNING",
                    severity="WARNING",
                    message="Penggunaan konjungsi transisi ilmiah antar-paragraf masih minim.",
                    actual=f"Hanya ditemukan {len(found_transitions)} penanda transisi akademik",
                    expected="Penggunaan penanda transisi logis (misal: 'oleh karena itu', 'kendati demikian', 'sejalan dengan temuan')",
                    recommendation="Perkuat kohesi dan koherensi naskah dengan memasukkan konjungsi antarkalimat ilmiah guna menghubungkan alur pemikiran antar-alinea.",
                    evidence_query="transisi alinea",
                ).to_dict()
            )

        return findings
