# AI Thesis Generator & Scientific Auditor

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://tesis-generator-s.streamlit.app/)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://docs.python.org/3/)
[![Material Design 3](https://img.shields.io/badge/Design-Material%203-6750A4.svg)](https://m3.material.io/)
[![WCAG 2.2 AA](https://img.shields.io/badge/Accessibility-WCAG%202.2%20AA-success.svg)](https://www.w3.org/TR/WCAG22/)

Aplikasi riset ilmiah dan auditor kepatuhan tesis berbasis **Scientific RAG (*Retrieval-Augmented Generation*)** dan **Rule-Engine Deterministik**. Sistem ini dirancang untuk menyusun draf tesis berbasis bukti (*evidence-based*), mengaudit naskah tesis (DOCX/PDF) terhadap pedoman universitas, melakukan auto-revisi format, dan menerbitkan laporan audit berstandar QA akademik.

🔗 **Live Web Application:** [https://tesis-generator-s.streamlit.app/](https://tesis-generator-s.streamlit.app/)

---

## Standar Resmi & Dokumentasi Rujukan

Platform ini dibangun dengan mengacu pada standar resmi berikut:

1. **[Material Design 3 (M3)](https://m3.material.io/)** — Sistem desain antarmuka modern, *design tokens* semantik, palet warna dinamis (dark/light), dan pola interaksi pengguna yang responsif.
2. **[W3C WCAG 2.2 Recommendation](https://www.w3.org/TR/WCAG22/)** — Standar aksesibilitas web resmi W3C yang menjamin rasio kontras visual $\ge 4.5:1$ dan navigasi hierarki semantik.
3. **[Ollama Documentation](https://docs.ollama.com/)** — Referensi integrasi dan komunikasi REST API model bahasa dan model embedding lokal (`qwen2.5:7b` & `nomic-embed-text`).
4. **[Python 3 Documentation](https://docs.python.org/3/)** — Standar implementasi pustaka, evaluasi sintaks AST aman, dan penanganan format berkas.
5. **[SQLite Foreign Key Support](https://www.sqlite.org/foreignkeys.html)** — Penegakan integritas referensial dan konsistensi data relasional (`PRAGMA foreign_keys = ON;`).
6. **[GitHub Repositories Documentation](https://docs.github.com/en/repositories)** — Standar manajemen repositori, pelacakan branch, dan alur rilis berkesinambungan.

---

## Arsitektur Sistem

```text
AI-Thesis-Generator/
├── app/
│   ├── ui/                    # Dashboard Streamlit (app.py)
│   ├── projects/              # Manajemen metadata proyek
│   └── workflows/             # Alur audit dan review
├── core/
│   ├── ingestion/             # Parser DOCX, PDF, dan dokumen model
│   ├── sources/               # Kolektor metadata (Crossref, OpenAlex, scraping)
│   ├── parsing/               # Normalisasi teks dan evidence mapper
│   ├── retrieval/             # LlamaIndex + Ollama (nomic-embed-text / qwen2.5:7b)
│   ├── guidelines/            # Rule Engine & validasi JSON Schema pedoman kampus
│   ├── review/                # Engine audit tesis (Format, Bab, Rumus, Statistik)
│   ├── revision/              # DocxAutoFixer & Human-in-the-Loop review
│   ├── citations/             # Validasi sitasi APA 7, DOI lookup & offline cache
│   ├── evaluation/            # Metrik evaluasi RAGAS & precision/recall
│   └── export/                # Generator naskah akhir DOCX/PDF dan laporan QA
├── profiles/
│   ├── guidelines/            # Pedoman MIKOM 2026 (JSON & YAML)
│   └── policies/              # Matriks kebijakan risiko revisi
├── tests/
│   ├── unit/                  # Pengujian modul individual
│   ├── golden_dataset/        # 10 dokumen benchmark sintetis
│   └── regression/            # Uji regresi pasca-revisi
├── workspace/
│   └── projects/              # Direktori sandbox per naskah tesis
├── vendor/                    # Repositori pendukung lokal
├── pyproject.toml
└── requirements.txt
```

---

## Fitur Utama

1. **Deterministic Rule Engine (Nol Halusinasi):**
   - Margin presisi 4-4-3-3 cm (Word EMU standard: $1\text{ cm} = 360.000\text{ EMUs}$).
   - Tipografi Times New Roman 12pt, double spacing 2.0, A4, justification.
   - Kelengkapan struktur 5 BAB, subbab desimal digital, dan proporsi halaman.
   - Deteksi & rekalkulasi rumus regresi linear deterministik ($Y = a + bX$).
   - Konsistensi ukuran sampel ($N$) antar-bab dan uji signifikansi ($p$-value vs $\alpha=0.05$).
2. **Evidence-Based Citation & DOI Verification:**
   - Pencocokan resiprokal sitasi dalam teks $\leftrightarrow$ Daftar Pustaka (APA 7th).
   - Validasi DOI instan melalui cache lokal terdeduplikasi dan live Crossref REST API.
3. **Multi-Tier Revision Engine:**
   - **Risiko Rendah:** Auto-revisi layout dokumen Word (`DocxAutoFixer`).
   - **Substantif:** Rekomendasi perbaikan klaim/rumus dengan persetujuan pengguna (*Human-in-the-Loop*).
4. **Local LLM & RAG Integration:**
   - Terintegrasi langsung dengan Ollama lokal (`qwen2.5:7b` dan `nomic-embed-text`).
   - Evaluasi kualitas retrieval menggunakan metrik Ragas.

---

## Cara Menjalankan

### 1. Persiapan Environment
```bash
git clone https://github.com/indri007/tesis-generator.git
cd tesis-generator
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

### 2. Menjalankan Dashboard
```bash
streamlit run app.py
```

### 3. Menjalankan Pengujian
```bash
pytest tests/ -v
```
