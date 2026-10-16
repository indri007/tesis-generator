# PRODUCT REQUIREMENTS DOCUMENT (PRD) — 2026
## AI Thesis Generator & Scientific Reviewer (TesisCheck MIKOM 2026)
### Standard Architecture, 7-Tier Tooling, Academic Connectors & Cloud CI

> **Version:** 2.2.0 (Post-CircleCI & Public Repo Upgrade)  
> **Status:** APPROVED & IMPLEMENTED (152 Unit & Regression Tests Passing)  
> **Repository:** `indri007/tesis-generator` (GitHub Public)  
> **Web Deployment:** `https://tesis-generator-s.streamlit.app/`  
> **Target Audience:** Mahasiswa Pascasarjana Magister Ilmu Komunikasi (MIKOM), Dosen Pembimbing, Reviewer Akademik, QA Engineers.

---

## 1. Executive Summary & Vision

TesisCheck MIKOM 2026 adalah sistem audit kepatuhan, verifikasi orisinalitas, dan asistensi penulisan manuskrip ilmiah berstandar pascasarjana. Produk ini dibangun di atas prinsip dasar:
1. **Local-First & Data Privacy:** Dokumen riset diolah secara mandiri di komputer lokal tanpa mengekspos naskah ke server proprietary.
2. **Deterministic-First (Zero-Hallucination):** Verifikasi format dokumen (margin EMU, spasi, font), rekalkulasi rumus regresi ($Y=a+bX$), dan pencocokan sitasi dua arah dijalankan 100% menggunakan kode Python deterministik, bukan inferensi probabilistik LLM.
3. **Transparent Academic Heuristics:** Deteksi kemiripan lokal diberi label jujur `"heuristik internal (n-gram overlap)"` dan secara eksplisit tidak mengklaim sebagai "setara Turnitin" demi menegakkan integritas akademik kampus.
4. **Standard Open-Source Tooling:** Menolak kloning tiruan mandiri (*mock clones*); memanfaatkan kakas resmi open-source standar industri dan API metadata publik.

---

## 2. Problem Statement & User Personas

### 2.1 Masalah Utama
1. **Tingginya Kesalahan Format Dokumen:** Format margin 4-4-3-3 cm, spasi 2.0, font Times New Roman 12, dan struktur bab yang kerap keliru sehingga menyita waktu bimbingan tesis.
2. **Sitasi Yatim & Halusinasi Rujukan:** Sitasi dalam naskah yang tidak tercantum di Daftar Pustaka (atau sebaliknya), serta rujukan buatan AI tanpa DOI valid.
3. **Ketidaksesuaian Statistik & Sintesis Riset:** Ketidakkonsistenan jumlah sampel antar-bab ($N$), kesalahan interpretasi $p$-value vs $\alpha=0.05$, dan ketiadaan kerangka metodologi yang terstruktur (PICO).
4. **Plagiarism Score Confusion:** Kebingungan membedakan antara skrining duplikasi referensi (*screening deduplication*) vs audit plagiarisme resmi.

### 2.2 User Personas & JTBD
- **Mahasiswa Magister:** Membutuhkan validasi mandiri cepat sebelum menyerahkan naskah ke dosen, auto-fixer layout DOCX presisi, dan deteksi dini sitasi yatim.
- **Dosen Pembimbing:** Membutuhkan kartu skor audit (*executive scorecard*) yang merangkum konsistensi sampel, kebenaran kalkulasi rumus, dan kepatuhan pedoman 2026.
- **Tim Penguji / Reviewer:** Memerlukan verifikasi bibliometrik (VOSviewer), sintesis konsensus ilmiah (Consensus/Elsevier), dan validasi DOI Crossref/OpenAlex.

---

## 3. Product Scope & Functional Requirements

### FR-01: Multi-Format Document Ingestion & Parsing
- Menerima berkas input `.docx` dan `.pdf` dengan batasan maksimal **175 halaman** (naskah $\ge 176$ halaman memicu `FATAL_ERROR`).
- Mengekstrak teks per-paragraf, tabel, gambar, formula, dan memetakan nomor halaman nyata (dengan toleransi PDF metadata fallback).

### FR-02: 10 Pilar Pedoman Tesis MIKOM 2026
1. Kertas A4 (21.0 x 29.7 cm).
2. Margin Presisi: Kiri 4 cm, Atas 4 cm, Kanan 3 cm, Bawah 3 cm (konversi EMU Word $1\text{ cm} = 360.000\text{ EMUs}$).
3. Font: Times New Roman 12 pt pada paragraf tubuh.
4. Line Spacing: Spasi ganda (2.0) pada teks utama.
5. Indentasi Paragraf: Baris pertama menjorok 1.0 - 1.27 cm.
6. Struktur 5 BAB: Pendahuluan, Tinjauan Pustaka, Metode Penelitian, Hasil & Pembahasan, Penutup.
7. Rekalkulasi Rumus: Verifikasi otomatis rumus regresi sederhana $Y=a+bX$.
8. Uji Signifikansi: Evaluasi nilai $p$-value terhadap ambang $\alpha=0.05$.
9. Validitas Sampel: Pencocokan konsistensi jumlah sampel $N$ di Bab III dan Bab IV.
10. Batas Maksimal 175 Halaman.

### FR-03: PICO Extraction & Systematic Review Integration
- Ekstraksi kerangka PICO (*Population, Intervention/Independent Variable, Comparison, Outcome/Dependent Variable*) dari teks abstrak/pendahuluan.
- Importer data skrining **Rayyan** (CSV dan RIS) dengan deduplikasi judul ternormalisasi dan status *Included/Excluded/Maybe*.
- Integrasi **Consensus Meter** untuk sintesis klaim ilmiah berdasarkan literatur yang telah ditinjau sejawat (*peer-reviewed*).
- Integrasi indeks sitasi **Elsevier / Scopus / ScienceDirect** (CSV/RIS) untuk tracking kuartil jurnal (Q1/Q2).

### FR-04: 7-Tier Standard Tooling Architecture
Sistem mengadopsi taksonomi 7-tier terverifikasi tanpa kloning tiruan:
- **Tier 1 (Core QA & Static Analysis):** `pytest`, `Hypothesis`, `mutmut`, `Coverage.py`, `Ruff`, `Mypy`, `Pyright`, `Bandit`, `Pylint`, `pre-commit`, `Pydantic`, `Pandera`.
- **Tier 2 (Academic Public Metadata APIs):** Integrasi API publik gratis dengan *polite mailto header* dan *local CI fixture caching*:
  - Crossref REST API (`https://api.crossref.org/works/`)
  - OpenAlex API (`https://api.openalex.org/works/`)
  - Semantic Scholar S2 Graph API (`https://api.semanticscholar.org/graph/v1/paper/`)
- **Tier 3 (Local Experiment Tracking & Versioning):** Mode lokal 100% offline tanpa biaya cloud:
  - MLflow (`sqlite:///workspace/mlflow.db`)
  - W&B (`WANDB_MODE=offline`)
  - DVC (`dvc local remote`)
- **Tier 4 (Observability):** `Sentry` dan `Logfire` dinonaktifkan secara bawaan (*disabled by default*), hanya aktif jika token/DSN disediakan secara eksplisit.
- **Tier 5 (Code & Data Deduplication):** `DataComPy`, `Pylint (duplicate-code)`, `Dedupe`.
- **Tier 6 (Proprietary AI Literature Services):** Adapter tipis (*thin adapters*) membaca API key dari environment (`CONSENSUS_API_KEY`, `PERPLEXITY_API_KEY`) dengan fallback anggun ke ekspor manual (Elicit, SciSpace, ResearchRabbit).
- **Tier 7 (Originality & Plagiarism Assessment):** Perhitungan n-gram overlap lokal dengan label transparan `"heuristik internal (n-gram overlap)"` dan checklist resmi Turnitin kampus.

### FR-05: VOSviewer Bibliometric Mapping Suite (BIT 18)
- Ekstraksi graf ko-sitasi (*co-citation*), hubungan antar-penulis (*co-authorship*), dan ko-kejadian kata kunci (*co-occurrence*).
- Algoritma klasterisasi Louvain / modularitas ilmiah.
- Ekspor jaringan bibliometrik ke format Pajek (`.net`) dan file JSON VOSviewer (*map/network*).

### FR-06: Multi-Tier Revision & Precision Auto-Fixer
- **Tier 1 (Deterministic Auto-Fixer):** Mengoreksi margin Word secara presisi, spasi paragraf, dan jenis font via `DocxAutoFixer`.
- **Tier 2 (Human-in-the-Loop):** Rekomendasi perbaikan redaksional, rekalkulasi formula, dan penyesuaian sampel yang wajib disetujui pengguna.
- Menghasilkan berkas baru bertanda versi (`*_revised_vX.docx`) dengan prinsip dokumen asli tetap *read-only*.

---

## 4. Non-Functional Requirements (NFR)

- **NFR-01 (Kecepatan & Performa):** Analisis kepatuhan naskah 100 halaman selesai dalam $< 10\text{ detik}$ pada prosesor M-series Mac.
- **NFR-02 (Aksesibilitas Visual):** Memenuhi standar W3C WCAG 2.2 Level AA dengan tema Material Design 3 (rasio kontras visual $\ge 4.5:1$).
- **NFR-03 (Efisiensi Ruang Penyimpanan):** Jejak runtime paket Python dijaga di bawah $1.0\text{ GB}$ menggunakan varian `mlflow-skinny` dan pembersihan berkala `pip cache purge`.
- **NFR-04 (Integritas Pengujian):** Suite regresi wajib memiliki $\ge 150\text{ unit tests}$ dengan status 100% lolos (zero failure tolerance).

---

## 5. Cloud & CI/CD Strategy

### 5.1 CircleCI Cloud Pipeline
Karena GitHub Actions pada akun tertentu dapat mengalami kendala billing limit, sistem telah dilengkapi dengan pipeline independen di [`.circleci/config.yml`](file:///Users/jevin/AI-Thesis-Generator/.circleci/config.yml):
- Runner: Docker container `cimg/python:3.12`.
- Caching: Dependensi pip dicache berdasarkan checksum `requirements.txt`.
- Tahap Eksekusi:
  1. `Ruff lint`: `python -m ruff check .`
  2. `Compile Python`: `python -m compileall -q app.py core engines parsers models tests`
  3. `Regression tests`: `python -m pytest tests/ -q --tb=short`

### 5.2 GitHub Actions Status
- Repositori telah dialihkan menjadi **Public** (`indri007/tesis-generator`), mengaktifkan hak istimewa *Unlimited Free Minutes* untuk pelari Linux publik setelah pembaruan status akun.

### 5.3 Local Pre-Push Guard
- Skrip otomasi [`BIT_UNIFIED_TOOLING_AND_API_CONNECT.sh`](file:///Users/jevin/AI-Thesis-Generator/BIT_UNIFIED_TOOLING_AND_API_CONNECT.sh) berfungsi sebagai gerbang verifikasi mandiri sebelum commit/push dilakukan.

---

## 6. Originality & Plagiarism Policy (Disclaimer Standar)

Sistem memberlakukan format disclaimer wajib pada seluruh keluaran laporan audit kemiripan:

> **PERINGATAN RESMI ORISINALITAS:**  
> Skor kemiripan ini dihitung secara lokal berbasis overlap n-gram kata dan HANYA berfungsi sebagai deteksi awal mandiri. Skor ini BUKAN "setara Turnitin" atau iThenticate karena repositori pembanding resmi (database penerbit global & repositori skripsi/tesis nasional) hanya dimiliki oleh penyedia komersial terkait. Pemeriksaan resmi wajib dilakukan melalui layanan Perpustakaan / Program Studi kampus Anda.

### Checklist Resmi Pemeriksaan Kampus:
1. Pemeriksaan resmi wajib dilakukan via akun Turnitin / iThenticate resmi universitas.
2. Pastikan opsi *"Exclude bibliography"* dan *"Exclude quotes"* diaktifkan sesuai buku pedoman MIKOM.
3. Ambang batas kelulusan tesis MIKOM UPNVJT: **Maksimal 20% similarity score**.
4. Pastikan opsi penyimpanan naskah (*standard paper repository*) telah diatur dengan benar agar tidak terjadi *self-plagiarism* saat penerbitan naskah ke jurnal internasional.

---

## 7. Status Implementasi & Verifikasi Metrik

| Fitur / Modul | Status | Bukti Pengujian |
|---|---|---|
| Ingestion DOCX/PDF & 175 Page Limit | **PASS** | `tests/unit/test_document_processing.py` |
| 10 Pilar Pedoman MIKOM 2026 | **PASS** | `tests/test_engines.py`, `tests/test_rule_engine.py` |
| APA 7 Citation Auditor (Reciprocity) | **PASS** | `tests/unit/test_citation_auditor.py` |
| PICO Extraction Engine | **PASS** | `tests/unit/test_unified_research_pipeline.py` |
| Rayyan CSV/RIS Importer & Deduplication | **PASS** | `tests/unit/test_unified_research_pipeline.py` |
| Consensus Meter & Peer-Reviewed Client | **PASS** | `tests/unit/test_unified_research_pipeline.py` |
| Elsevier / Scopus / ScienceDirect Q1-Q4 | **PASS** | `tests/unit/test_elsevier_client.py` |
| VOSviewer Bibliometrics & Pajek Export | **PASS** | `tests/unit/test_vosviewer_bibliometrics.py` |
| Academic Public APIs (Crossref, OpenAlex, S2)| **PASS** | `tests/unit/test_academic_services.py` |
| Local Tracking (MLflow, DVC, W&B Offline) | **PASS** | `tests/unit/test_academic_services.py` |
| Precision Layout Auto-Fixer (DocxAutoFixer)| **PASS** | `tests/unit/test_revision_engine.py` |
| CircleCI Cloud Configuration | **PASS** | `.circleci/config.yml` (Merged on `main`) |
| **Total Test Suite** | **152 PASS** | `pytest tests/ -q` (6.52s) |
| **Linter & Type Cleanliness** | **0 Errors** | `ruff check .` (All checks passed) |

---
*Dokumen ini diperbarui secara resmi pada Oktober 2026 mengikuti pencapaian integrasi CircleCI, VOSviewer bibliometrics, dan 7-tier academic connectors.*
