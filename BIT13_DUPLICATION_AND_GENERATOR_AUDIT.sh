#!/bin/bash
set -u
cd /Users/jevin/AI-Thesis-Generator || exit 1
mkdir -p workspace
OUT="workspace/BIT13_DUPLICATION_AND_GENERATOR_AUDIT.txt"

{
  echo "=== BIT 13: DUPLIKASI FIXTURE DAN GENERATOR ==="
  date

  echo
  echo "=== 1. PEMERIKSAAN PARAGRAF BERULANG ==="
  .venv-test/bin/python - <<'PY'
from collections import Counter
from pathlib import Path
from docx import Document

for path in sorted(Path("golden_dataset/documents").glob("*.docx")):
    try:
        doc = Document(path)
        paragraphs = [
            " ".join(p.text.split())
            for p in doc.paragraphs
            if p.text.strip()
        ]
        counts = Counter(paragraphs)
        repeated = [(text, n) for text, n in counts.items() if n > 1]
        repeated.sort(key=lambda item: item[1], reverse=True)
        total = len(paragraphs)
        duplicate_excess = sum(n - 1 for _, n in repeated)

        print(f"\n{path.name}")
        print(f"  paragraf berisi teks: {total}")
        print(f"  teks unik: {len(counts)}")
        print(f"  teks berulang berbeda: {len(repeated)}")
        print(f"  kemunculan duplikat berlebih: {duplicate_excess}")

        for text, n in repeated[:3]:
            print(f"  [{n}x] {text[:180]}")
    except Exception as exc:
        print(f"\n{path.name}: ERROR {exc!r}")
PY

  echo
  echo "=== 2. LOGIKA GENERATOR DATASET ==="
  grep -nE -C 4 \
    'repeat|duplicate|paragraph|paragraf|range\\(|for .* in|TEST-00|TEST-01|save\\(|output_dir|generated_golden_dataset' \
    golden_dataset/generator.py

  echo
  echo "=== 3. RIWAYAT PERUBAHAN GENERATOR ==="
  git diff -- golden_dataset/generator.py

  echo
  echo "=== 4. RINGKASAN PERUBAHAN FIXTURE TERHADAP HEAD ==="
  git status --short -- golden_dataset/documents
  git diff --stat -- golden_dataset/documents

  echo
  echo "=== 5. STATUS FILE DAN DATASET ==="
  git status -sb
  echo
  echo "Audit read-only selesai. Tidak ada file yang diubah."
} > "$OUT" 2>&1

echo "Laporan tersimpan di: $OUT"
cat "$OUT"
