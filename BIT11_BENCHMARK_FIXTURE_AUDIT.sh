#!/bin/bash
set -u

cd /Users/jevin/AI-Thesis-Generator || exit 1
mkdir -p workspace
OUT="workspace/BIT11_BENCHMARK_FIXTURE_AUDIT.txt"
PY=".venv-test/bin/python"

{
  echo "=== BIT 11: BENCHMARK DAN FIXTURE AUDIT ==="
  date

  echo
  echo "=== 1. JALANKAN BENCHMARK SECARA LANGSUNG ==="
  "$PY" -m pytest -s -vv tests/golden_dataset/test_academic_benchmark.py
  echo "benchmark_test_exit=$?"

  echo
  echo "=== 2. IMPLEMENTASI METRIK ==="
  sed -n '1,300p' core/evaluation/metrics.py

  echo
  echo "=== 3. LOGIKA BENCHMARK ==="
  sed -n '1,300p' core/evaluation/benchmark_runner.py

  echo
  echo "=== 4. SUMBER KAPPA DAN ANOTASI ==="
  grep -nE \
    'def .*kappa|cohen|observed_agreement|expected_agreement|reviewer_1|reviewer_2|reference_annotations|agreement|sample_count' \
    core/evaluation/*.py tests/golden_dataset/test_academic_benchmark.py

  echo
  echo "=== 5. BANDINGKAN ISI DOCX DENGAN BASELINE GIT ==="
  "$PY" - <<'PY'
import io
import subprocess
from pathlib import Path

try:
    from docx import Document
except ImportError:
    print("python-docx tidak tersedia; perbandingan DOCX dilewati.")
    raise SystemExit(0)

paths = sorted(Path("golden_dataset/documents").glob("*.docx"))
print("Jumlah fixture DOCX:", len(paths))

def extract_docx(blob):
    doc = Document(io.BytesIO(blob))
    result = []
    for p in doc.paragraphs:
        text = p.text.strip()
        if text:
            result.append("P:" + text)
    for ti, table in enumerate(doc.tables):
        for ri, row in enumerate(table.rows):
            result.append(
                f"T{ti}R{ri}:" +
                " | ".join(cell.text.strip() for cell in row.cells)
            )
    return result

for path in paths:
    current = path.read_bytes()
    proc = subprocess.run(
        ["git", "show", f"HEAD:{path.as_posix()}"],
        capture_output=True,
        check=False
    )
    if proc.returncode != 0:
        print(f"\n{path.name}: TIDAK ADA BASELINE DI HEAD")
        continue

    try:
        old = extract_docx(proc.stdout)
        new = extract_docx(current)
    except Exception as exc:
        print(f"\n{path.name}: gagal membaca DOCX: {exc}")
        continue

    print(f"\n{path.name}")
    print("  baseline paragraf/baris tabel:", len(old))
    print("  working paragraf/baris tabel:", len(new))
    print("  isi tekstual sama:", old == new)

    if old != new:
        old_set, new_set = set(old), set(new)
        print("  baris lama yang hilang:", len(old_set - new_set))
        print("  baris baru/berubah:", len(new_set - old_set))
        for line in list(old_set - new_set)[:3]:
            print("  - BASELINE:", line[:180])
        for line in list(new_set - old_set)[:3]:
            print("  + WORKING:", line[:180])

print("\nCatatan: teks yang sama tidak membuktikan margin, font, style, atau format identik.")
PY

  echo
  echo "=== 6. STATUS AKHIR TANPA MODIFIKASI GIT ==="
  git status -sb
  echo
  echo "Tidak ada staging, commit, push, atau deployment."
} > "$OUT" 2>&1

echo "Audit selesai. Laporan: $OUT"
cat "$OUT"
