#!/bin/bash
set -u
cd /Users/jevin/AI-Thesis-Generator || exit 1

mkdir -p workspace/bit15_backups
OUT="workspace/BIT15_CONTROLLED_REPAIR_PRECHECK.txt"
PY=".venv-test/bin/python"

{
  echo "=== BIT 15: CONTROLLED REPAIR PRECHECK ==="
  date

  echo
  echo "=== 1. PYTHON ENVIRONMENT ==="
  "$PY" --version
  "$PY" -m pip check

  echo
  echo "=== 2. GENERATOR AND BENCHMARK FILES ==="
  for f in \
    golden_dataset/generator.py \
    core/evaluation/benchmark_runner.py \
    core/evaluation/metrics.py \
    core/evaluation/matcher.py \
    tests/golden_dataset/test_academic_benchmark.py
  do
    if [ -f "$f" ]; then
      echo "--- $f"
      wc -l "$f"
      shasum -a 256 "$f"
    else
      echo "--- MISSING: $f"
    fi
  done

  echo
  echo "=== 3. DUPLICATE CONTENT SUMMARY ==="
  "$PY" - <<'PY'
from collections import Counter
from pathlib import Path
from docx import Document

for path in sorted(Path("golden_dataset/documents").glob("TEST-*.docx")):
    try:
        doc = Document(path)
        texts = [
            " ".join(p.text.split())
            for p in doc.paragraphs
            if p.text.strip()
        ]
        counts = Counter(texts)
        repeated = [(text, n) for text, n in counts.items() if n > 1]
        repeated.sort(key=lambda x: x[1], reverse=True)
        excess = sum(n - 1 for _, n in repeated)
        print(
            f"{path.name}: total={len(texts)}, unique={len(counts)}, "
            f"duplicate_excess={excess}"
        )
        for text, n in repeated[:2]:
            print(f"  {n}x: {text[:120]}")
    except Exception as e:
        print(f"{path.name}: ERROR {e!r}")
PY

  echo
  echo "=== 4. BENCHMARK TEST ==="
  "$PY" -m pytest -q tests/golden_dataset/test_academic_benchmark.py
  echo "benchmark_exit=$?"

  echo
  echo "=== 5. FULL REGRESSION ==="
  "$PY" -m pytest -q
  echo "regression_exit=$?"

  echo
  echo "=== 6. STREAMLIT ENTRYPOINT ==="
  if [ -f app.py ]; then
    "$PY" -m py_compile app.py
    echo "app_compile_exit=$?"
  else
    echo "app.py tidak ditemukan di root."
  fi

  echo
  echo "=== 7. FINAL DIFF CHECK ==="
  git diff --check
  echo "diff_check_exit=$?"

  echo
  echo "=== 8. GIT STATUS ==="
  git status -sb

  echo
  echo "=== END ==="
  echo "Precheck tidak mengubah fixture, kode aplikasi, atau riwayat Git."
  echo "Tidak melakukan staging, commit, push, atau deployment."
} > "$OUT" 2>&1

echo "Selesai. Laporan: $OUT"
cat "$OUT"
