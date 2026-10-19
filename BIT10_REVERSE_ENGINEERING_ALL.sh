#!/bin/bash
set -u

cd /Users/jevin/AI-Thesis-Generator || exit 1
mkdir -p workspace
OUT="workspace/BIT10_REVERSE_ENGINEERING_ALL.txt"
PY=".venv-test/bin/python"

if [ ! -x "$PY" ]; then
  echo "ERROR: $PY tidak ditemukan. Hentikan audit."
  exit 1
fi

{
  echo "=================================================="
  echo "BIT 10 — REVERSE ENGINEERING & RELEASE READINESS"
  date
  echo "=================================================="

  echo
  echo "=== 1. STATUS GIT DAN DIFF ==="
  git status -sb
  git diff --check
  echo "diff_check_exit=$?"

  echo
  echo "=== 2. VALIDASI BENCHMARK JSON DAN ANOTASI ==="
  "$PY" - <<'PY'
import json
from pathlib import Path
from collections import Counter

base = Path("data/benchmark")
files = [base / "annotated_schema.json",
         base / "development_set.json",
         base / "evaluation_set.json"]
errors = []
sets = {}

for path in files:
    print(f"\n--- {path} ---")
    if not path.exists():
        errors.append(f"File hilang: {path}")
        print("MISSING")
        continue
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"JSON invalid: {path}: {exc}")
        print("JSON INVALID:", exc)
        continue

    print("JSON valid: YES")
    if path.name == "annotated_schema.json":
        try:
            import jsonschema
            jsonschema.Draft7Validator.check_schema(obj)
            print("JSON Schema valid: YES")
        except ImportError:
            print("JSON Schema check: SKIPPED (jsonschema tidak tersedia)")
        except Exception as exc:
            errors.append(f"Schema invalid: {exc}")
            print("JSON Schema valid: NO:", exc)
        continue

    print("split:", obj.get("split"))
    print("dataset_id:", obj.get("dataset_id"))
    print("schema_version:", obj.get("schema_version"))
    items = obj.get("items")
    if not isinstance(items, list):
        errors.append(f"items bukan list: {path}")
        continue

    ids = []
    reviewer_pairs = []
    label_counts = Counter()
    missing = 0

    for i, item in enumerate(items, 1):
        if not isinstance(item, dict):
            errors.append(f"{path.name}: item {i} bukan object")
            continue

        doc_id = item.get("document_id")
        if not doc_id:
            errors.append(f"{path.name}: item {i} tidak punya document_id")
        else:
            ids.append(doc_id)

        refs = item.get("reference_annotations")
        if refs is None:
            missing += 1
            errors.append(f"{path.name}: {doc_id} tidak punya reference_annotations")
        elif not isinstance(refs, (list, dict)):
            errors.append(f"{path.name}: reference_annotations bukan list/object: {doc_id}")
        elif isinstance(refs, list) and not refs:
            print(f"WARNING: reference_annotations kosong untuk {doc_id}")

        for field in ("reviewer_1_labels", "reviewer_2_labels"):
            value = item.get(field)
            if value is None:
                print(f"WARNING: {doc_id} tidak memiliki {field}")
            elif not isinstance(value, list):
                errors.append(f"{path.name}: {field} bukan list untuk {doc_id}")
            else:
                label_counts.update(str(x) for x in value)

        a, b = item.get("reviewer_1_labels"), item.get("reviewer_2_labels")
        if isinstance(a, list) and isinstance(b, list):
            reviewer_pairs.append((doc_id, a, b))

    duplicates = [x for x, n in Counter(ids).items() if n > 1]
    if duplicates:
        errors.append(f"{path.name}: document_id duplikat: {duplicates}")

    sets[obj.get("split", path.stem)] = set(ids)
    print("item count:", len(items))
    print("unique document IDs:", len(set(ids)))
    print("items missing references:", missing)
    print("label frequency:", dict(label_counts))
    print("reviewer label pairs available:", len(reviewer_pairs))

    disagreements = [
        doc_id for doc_id, a, b in reviewer_pairs if a != b
    ]
    print("reviewer label list disagreements:", len(disagreements))
    if disagreements:
        print("disagreement IDs:", disagreements)
        print("NOTE: list mismatch is not itself a Cohen's kappa score.")

if "development" in sets and "evaluation" in sets:
    overlap = sets["development"] & sets["evaluation"]
    print("\n=== SPLIT OVERLAP ===")
    print("development IDs:", len(sets["development"]))
    print("evaluation IDs:", len(sets["evaluation"]))
    print("overlap count:", len(overlap))
    if overlap:
        print("OVERLAP IDS:", sorted(overlap))
        errors.append("Development/evaluation document IDs overlap")

print("\n=== BENCHMARK STRUCTURAL RESULT ===")
print("ERROR COUNT:", len(errors))
for err in errors:
    print("ERROR:", err)
print("Catatan: validitas anotasi manusia tidak dapat dibuktikan hanya dengan JSON.")
PY
  echo "benchmark_script_exit=$?"

  echo
  echo "=== 3. AUDIT METRIK DAN KAPPA ==="
  grep -nE \
    'def .*kappa|cohen|observed_agreement|expected_agreement|micro_metrics|macro_metrics|precision|recall|f1_score|85\.0|0\.60' \
    core/evaluation/metrics.py \
    core/evaluation/benchmark_runner.py \
    core/evaluation/schema.py \
    tests/golden_dataset/test_academic_benchmark.py 2>/dev/null || true

  echo
  echo "=== 4. DEPENDENSI ==="
  "$PY" -m pip check
  echo "pip_check_exit=$?"

  "$PY" -m pip_audit
  echo "pip_audit_exit=$?"

  echo
  echo "=== 5. REGRESI TES ==="
  "$PY" -m pytest -q
  echo "pytest_exit=$?"

  echo
  echo "=== 6. BATAS HALAMAN DAN UPLOAD ==="
  grep -nE \
    'file_uploader|maxUploadSize|page_count|175|TemporaryDirectory|mkdtemp|unlink|remove\(' \
    app.py core engines models utils .streamlit/config.toml 2>/dev/null || true

  echo
  echo "=== 7. PERUBAHAN FIXTURE ==="
  git diff --numstat -- golden_dataset/documents
  echo "Periksa apakah perubahan DOCX memang disengaja sebelum commit."

  echo
  echo "=== 8. STATUS RILIS ==="
  echo "Tes dan audit di atas adalah bukti lokal, bukan bukti deployment."
  echo "Jangan klaim akurasi >=85% atau kappa >=0.60 sebelum metrik aktual diverifikasi."
  echo "Jangan commit fixture yang berubah tanpa pemeriksaan."
  echo "Tidak ada staging, commit, push, atau deployment."
} > "$OUT" 2>&1

echo "Audit selesai."
echo "Laporan: $OUT"
echo
cat "$OUT"
