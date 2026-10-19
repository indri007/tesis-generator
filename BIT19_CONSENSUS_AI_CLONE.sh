#!/usr/bin/env bash
# ==============================================================================
# BIT 19 — CONSENSUS AI SCIENTIFIC EVIDENCE SYNTHESIZER & CONSENSUS METER CLONE
# Reverse Engineering: Consensus.app (Consensus Meter, Study Rigor, Evidence Synthesis)
# Standar: MIKOM 2026 Academic Integrity & Evidence-Based Hypothesis Verification
# ==============================================================================
set -euo pipefail

cd /Users/jevin/AI-Thesis-Generator || exit 1
mkdir -p workspace
OUT="workspace/BIT19_CONSENSUS_AI_CLONE.txt"
PY=".venv-test/bin/python3"

if [ ! -x "$PY" ]; then
  echo "ERROR: Virtualenv $PY tidak ditemukan."
  exit 1
fi

{
  echo "======================================================================"
  echo "BIT 19: CONSENSUS AI EVIDENCE SYNTHESIS & CONSENSUS METER CLONE"
  date
  echo "======================================================================"

  echo
  echo "=== 1. STATUS REPOSITORY & ARSITEKTUR KLONING CONSENSUS AI ==="
  git status -sb
  for f in \
    core/clones/consensus_ai.py \
    core/clones/__init__.py \
    tests/unit/test_consensus_ai.py
  do
    if [ -f "$f" ]; then
      echo "[OK] $f ($(wc -l < "$f") baris, SHA256: $(shasum -a 256 "$f" | cut -d' ' -f1))"
    else
      echo "[MISSING] $f"
      exit 1
    fi
  done

  echo
  echo "=== 2. EKSEKUSI SINTESIS ILMIAH & CONSENSUS METER ==="
  "$PY" - << 'PY'
import json
from pathlib import Path
from core.clones.consensus_ai import ConsensusAIClone

query = "Apakah integrasi IndoBERT dan SNA efektif meningkatkan deteksi misinformasi kebijakan MBG?"

corpus = [
    {
        "title": "Deteksi Opini dan Misinformasi Kebijakan MBG Berbasis IndoBERT dan Social Network Analysis",
        "authors": ["Utomo, Indri", "Santoso, Budi"],
        "year": 2024,
        "journal": "Jurnal Komunikasi Indonesia",
        "doi": "10.1016/j.jki.2024.101",
        "abstract": "Penelitian ini menggunakan kombinasi IndoBERT dan social network analysis (SNA) dengan sampel sebanyak n = 28500 cuitan publik. Hasil pengujian empiris membuktikan bahwa integrasi model berhasil meningkatkan akurasi deteksi polaritas dan misinformasi hingga 93.8% dengan F1-score superior.",
        "cited_by_count": 42,
    },
    {
        "title": "Evaluasi Algoritma Komunitas Jaringan pada Kanal Telegram Indonesia",
        "authors": ["Pratama, Agus", "Wijaya, Hendra"],
        "year": 2023,
        "journal": "Telematics and Informatics",
        "doi": "10.1016/j.tele.2023.202",
        "abstract": "Studi kuantitatif membuktikan SNA terbukti efektif memetakan klaster polarisasi dan mempercepat identifikasi aktor sentral penyebar narasi manipulatif secara signifikan.",
        "cited_by_count": 35,
    },
    {
        "title": "Tantangan Analisis Sentimen Aspek (ABSA) pada Komunikasi Kebijakan Publik",
        "authors": ["Kusuma, Dian"],
        "year": 2024,
        "journal": "Asian Journal of Communication",
        "doi": "10.1080/ajc.2024.303",
        "abstract": "Hasil penelitian menunjukkan pengaruh bersyarat (mixed results): deteksi aspek berhasil tinggi pada teks deskriptif, namun efektivitas tergantung pada penanganan sarkasme dan emoji kontekstual.",
        "cited_by_count": 18,
    },
    {
        "title": "Kelemahan Model Ekstraksi Lexicon Konvensional pada Media Daring",
        "authors": ["Rahmawati, Siti"],
        "year": 2022,
        "journal": "Media dan Masyarakat",
        "doi": "10.1000/mdm.2022.404",
        "abstract": "Metode pencocokan kamus konvensional tidak berpengaruh nyata terhadap ketepatan klasifikasi dan gagal membedakan nuansa emosi pengguna.",
        "cited_by_count": 9,
    },
]

engine = ConsensusAIClone()
res = engine.analyze_corpus(query, corpus)

print(f"Pertanyaan Ilmiah : '{res.query}'")
print(f"Ringkasan Meter   : {res.meter.summary_headline}")
print(f"  - Yes (Mendukung)   : {res.meter.yes_percentage}% ({res.meter.yes_count}/{res.meter.total_studies} studi)")
print(f"  - Possibly (Campur) : {res.meter.possibly_percentage}% ({res.meter.possibly_count}/{res.meter.total_studies} studi)")
print(f"  - No (Membantah)    : {res.meter.no_percentage}% ({res.meter.no_count}/{res.meter.total_studies} studi)")
print(f"  - Skor Terbobot     : {res.meter.weighted_consensus_score:+.2f}")

# Export artifacts
report_md = Path("workspace/consensus_report.md")
export_csv = Path("workspace/consensus_export.csv")
synthesis_json = Path("workspace/consensus_synthesis.json")

report_md.write_text(res.to_markdown(), encoding="utf-8")
engine.export_consensus_csv(res, export_csv)
with open(synthesis_json, "w", encoding="utf-8") as f:
    json.dump(res.to_dict(), f, indent=2)

print(f"\n[OK] Laporan Sintesis Ilmiah (Markdown) : {report_md} ({report_md.stat().st_size} bytes)")
print(f"[OK] Standard Consensus Export (CSV)    : {export_csv} ({export_csv.stat().st_size} bytes)")
print(f"[OK] Consensus Synthesis Data (JSON)    : {synthesis_json} ({synthesis_json.stat().st_size} bytes)")
PY

  echo
  echo "=== 3. VERIFIKASI UNIT TEST REGRESI ==="
  "$PY" -m pytest tests/unit/test_consensus_ai.py tests/unit/test_vosviewer_bibliometrics.py -q --tb=short

  echo
  echo "=== 4. INTEGRASI CLEAN CODE & STATIC ANALYSIS ==="
  "$PY" -m ruff check core/clones/consensus_ai.py core/clones/vosviewer_bibliometrics.py tests/unit/test_consensus_ai.py
  "$PY" -m compileall -q core/clones/ tests/unit/test_consensus_ai.py
  echo "[OK] Clean code & kompilasi 100% verified."

  echo
  echo "======================================================================"
  echo "STATUS: ALL CLONES (VOSVIEWER & CONSENSUS AI) OPERASIONAL 100% PASS"
  echo "======================================================================"
} 2>&1 | tee "$OUT"
