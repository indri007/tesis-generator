#!/bin/bash
set -u
cd /Users/jevin/AI-Thesis-Generator || exit 1
mkdir -p workspace
OUT="workspace/BIT14_SAFE_BENCHMARK_GATE.txt"
PY=".venv-test/bin/python"

{
  echo "=== BIT 14: SAFE BENCHMARK GATE ==="
  date

  echo
  echo "=== 1. STATUS REPOSITORY ==="
  git status -sb

  echo
  echo "=== 2. DUPLIKASI PARAGRAF FIXTURE ==="
  "$PY" - <<'PY'
from collections import Counter
from pathlib import Path
from docx import Document

for path in sorted(Path("golden_dataset/documents").glob("TEST-*.docx")):
    try:
        doc = Document(path)
        paragraphs = [
            " ".join(p.text.split())
            for p in doc.paragraphs
            if p.text.strip()
        ]
        counts = Counter(paragraphs)
        excess = sum(n - 1 for n in counts.values() if n > 1)
        ratio = excess / max(len(paragraphs), 1)
        print(
            f"{path.name}: paragraphs={len(paragraphs)}, "
            f"unique={len(counts)}, duplicate_excess={excess}, "
            f"duplicate_ratio={ratio:.1%}"
        )
        for text, n in counts.most_common(2):
            if n > 1:
                print(f"  DUPLICATE [{n}x]: {text[:140]}")
    except Exception as exc:
        print(f"{path.name}: READ_ERROR={exc!r}")
PY

  echo
  echo "=== 3. GENERATOR: ISI DAN TUJUAN SKENARIO ==="
  sed -n '1,300p' golden_dataset/generator.py

  echo
  echo "=== 4. TEST BENCHMARK ==="
  "$PY" -m pytest -q tests/golden_dataset/test_academic_benchmark.py
  echo "benchmark_exit=$?"

  echo
  echo "=== 5. TEST SUITE ==="
  "$PY" -m pytest -q
  echo "full_test_exit=$?"

  echo
  echo "=== 6. DIFF CHECK ==="
  git diff --check
  echo "diff_check_exit=$?"

  echo
  echo "=== AKHIR ==="
  echo "Skrip ini hanya memeriksa dan menjalankan tes."
  echo "Tidak ada restore, penghapusan, staging, commit, push, atau deployment."
} > "$OUT" 2>&1

echo "Laporan: $OUT"
cat "$OUT"
