# TesisCheck MIKOM 2026 — Conversation / Project Context

## Catatan

File ini adalah rekonstruksi konteks proyek yang tersedia untuk sesi ini, bukan export mentah internal seluruh riwayat ChatGPT. Saya tidak memiliki API untuk mengekspor hidden/raw conversation transcript secara langsung.

## User request 1

Saya sedang menulis tesis tetapi dosen mengatakan tidak sesuai format. Saya ingin membuat aplikasi otomatis untuk mengecek tesis, berdasarkan pedoman, dan meminta detail lengkap untuk perintah pembangunan aplikasi.

## User request 2

Aplikasi diinginkan online menggunakan Streamlit. Pengguna cukup memasukkan Word/PDF maksimal 175 halaman. Sistem menganalisis mana yang sesuai dan tidak sesuai, apa yang harus direvisi, serta memeriksa rumus yang tidak konsisten/tidak benar. Kasus penting: jurnal pengguna sudah terbit tetapi dosen mengatakan isinya tidak sesuai dengan tesis.

## Product direction

Aplikasi harus menjadi:

Evidence-based Thesis Compliance & Consistency Auditor

Bukan sekadar grammar checker atau format checker.

Fitur inti:
- upload DOCX/PDF, max 175 pages
- audit Pedoman Penulisan Tesis MIKOM 2026
- format audit
- structure audit
- word count
- chapter proportions
- citation/reference audit
- table/figure audit
- variable consistency
- formula extraction and consistency
- deterministic arithmetic recalculation
- statistical consistency
- method ↔ result consistency
- result ↔ conclusion consistency
- research-question ↔ conclusion consistency
- contradiction detection across chapters
- optional journal ↔ thesis comparison
- evidence-based findings
- revision recommendations
- report export

## Important source file

PEDOMAN PENULISAN TESIS MIKOM 2026 (1).pdf

## Additional source file

Lampiran-lampiran_tesis_A4_format.docx.md

## Rules already extracted from the MIKOM guideline

- Main thesis body: 40,000–60,000 words.
- Chapter proportions:
  - BAB I: 15%, 6,000–9,000 words
  - BAB II: 25%, 10,000–15,000
  - BAB III: 15%, 6,000–9,000
  - BAB IV: 35%, 14,000–21,000
  - BAB V: 10%, 4,000–6,000
- APA 7 for bibliography.
- A4 paper: 21.5 cm × 29.0 cm.
- Margins: top 4 cm, left 4 cm, bottom 3 cm, right 3 cm.
- Times New Roman 12 pt.
- Main body line spacing 2; special sections such as abstract, quotations, table/figure titles and references use 1 spacing as specified.
- Main text justified.
- Preliminary pages use lowercase Roman numerals; main thesis uses Arabic numbering.
- Abstract: 150–250 words plus keywords.
- Quantitative and qualitative thesis structures differ and should be audited accordingly.
- Similarity/plagiarism should not be faked or claimed to replace Turnitin.

## Core architecture

```text
Streamlit
  -> file validation
  -> DOCX/PDF parser
  -> document structure model
  -> deterministic rule engine
  -> semantic AI audit
  -> cross-section consistency engine
  -> optional journal/thesis comparator
  -> evidence-based report
```

## Critical design principle

For deterministic checks, use Python/rule engine rather than an LLM.

LLM is for semantic interpretation.

Never silently alter research results. Suggested formula or content revisions must be presented for user confirmation.

