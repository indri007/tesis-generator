#!/usr/bin/env bash
set -Eeuo pipefail

# TesisCheck MIKOM 2026
# Safe audit, backup, test, and deployment-readiness workflow.
# Does not commit, push, deploy, or overwrite tracked files intentionally.

ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || {
  echo "ERROR: Direktori ini bukan repositori Git."
  exit 1
}
cd "$ROOT"

STAMP="$(date +%Y%m%d_%H%M%S)"
AUDIT_DIR="$ROOT/workspace/tesischeck_final_$STAMP"
BACKUP_DIR="$AUDIT_DIR/backup"
REPORT_DIR="$AUDIT_DIR/reports"
mkdir -p "$BACKUP_DIR" "$REPORT_DIR"

log() { printf '\n[%s] %s\n' "$(date '+%H:%M:%S')" "$*"; }
warn() { printf '\n[WARNING] %s\n' "$*" >&2; }
fail() { printf '\n[ERROR] %s\n' "$*" >&2; exit 1; }

log "TAHAP 1 — IDENTITAS REPOSITORI"
printf 'Root: %s\n' "$ROOT"
printf 'Branch: '
git branch --show-current
printf 'Commit: '
git rev-parse HEAD
printf 'Python: '
python3 --version 2>&1 || true

log "TAHAP 2 — BACKUP PERUBAHAN LOKAL"
git status --short > "$REPORT_DIR/git_status_before.txt"
git diff --binary > "$BACKUP_DIR/tracked_changes.patch"
git diff --cached --binary > "$BACKUP_DIR/staged_changes.patch"

# Backup modified and untracked files without touching source files.
# Excludes virtual environments and Git internals.
python3 - "$ROOT" "$BACKUP_DIR/files" <<'PY'
import subprocess, sys, shutil
from pathlib import Path

root = Path(sys.argv[1]).resolve()
dest = Path(sys.argv[2]).resolve()
dest.mkdir(parents=True, exist_ok=True)

result = subprocess.run(
    ["git", "status", "--porcelain", "-z"],
    cwd=root, capture_output=True, check=True
)
entries = result.stdout.decode("utf-8", "surrogateescape").split("\0")
paths = []
i = 0
while i < len(entries):
    entry = entries[i]
    i += 1
    if not entry:
        continue
    path = entry[3:]
    # Rename/copy records can contain a second path.
    if entry[:2].strip() in {"R", "C"} and i < len(entries):
        i += 1
    p = (root / path).resolve()
    try:
        p.relative_to(root)
    except ValueError:
        print(f"SKIP outside repository: {path}")
        continue
    if any(part in {".git", ".venv", "venv", "__pycache__"} for part in p.parts):
        continue
    if p.is_file():
        paths.append((p, path))

copied = 0
for src, rel in paths:
    target = dest / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, target)
    copied += 1

print(f"File perubahan lokal yang dicadangkan: {copied}")
print(f"Lokasi: {dest}")
PY

# Save checksums of copied files.
if command -v shasum >/dev/null 2>&1; then
  find "$BACKUP_DIR/files" -type f -print0 |
    while IFS= read -r -d '' f; do
      shasum -a 256 "$f"
    done > "$REPORT_DIR/backup_sha256.txt"
fi

log "TAHAP 3 — STATUS DAN DIFF RINGKAS"
git status --short | tee "$REPORT_DIR/git_status.txt"
git diff --stat | tee "$REPORT_DIR/git_diff_stat.txt"
git diff --cached --stat | tee "$REPORT_DIR/git_staged_diff_stat.txt"

log "TAHAP 4 — AUDIT STRUKTUR APLIKASI"
for f in \
  requirements.txt \
  pyproject.toml \
  pytest.ini \
  .streamlit/config.toml \
  .gitignore \
  golden_dataset/generator.py \
  tests/golden_dataset/test_academic_benchmark.py \
  core/evaluation/schema.py \
  core/evaluation/benchmark_runner.py
do
  if [ -f "$f" ]; then
    printf 'FOUND  %s\n' "$f"
  else
    printf 'MISSING %s\n' "$f"
  fi
done | tee "$REPORT_DIR/structure_audit.txt"

log "TAHAP 5 — AUDIT RISIKO GENERATOR DAN OUTPUT"
rg -n \
  'generate_golden_dataset|save_test_docx|DOCS_DIR|output/reports/benchmark|base_commit|code_version|working_tree_dirty|strict_location|strict_severity' \
  golden_dataset tests core 2>/dev/null \
  > "$REPORT_DIR/benchmark_write_risks.txt" || true
cat "$REPORT_DIR/benchmark_write_risks.txt"

log "TAHAP 6 — CEK SYNTAX PYTHON"
PYTHON_BIN="${PYTHON_BIN:-python3}"
if [ -x ".venv/bin/python" ]; then
  PYTHON_BIN=".venv/bin/python"
elif [ -x ".venv/bin/python3" ]; then
  PYTHON_BIN=".venv/bin/python3"
fi

printf 'Interpreter: '
"$PYTHON_BIN" --version

"$PYTHON_BIN" -m compileall -q core engines models tests golden_dataset \
  > "$REPORT_DIR/compileall.txt" 2>&1 || {
    cat "$REPORT_DIR/compileall.txt"
    warn "Pemeriksaan syntax gagal. Lanjutkan audit; jangan anggap aplikasi lulus."
  }

log "TAHAP 7 — JALANKAN TES UNIT SAJA"
# Deliberately do not run tests/golden_dataset here:
# that test currently regenerates tracked DOCX fixtures and writes reports.
if [ -d tests/unit ]; then
  set +e
  "$PYTHON_BIN" -m pytest -q tests/unit \
    --junitxml="$REPORT_DIR/unit_tests.xml" \
    > "$REPORT_DIR/unit_tests.log" 2>&1
  UNIT_RC=$?
  set -e
  cat "$REPORT_DIR/unit_tests.log"
  printf '%s\n' "$UNIT_RC" > "$REPORT_DIR/unit_tests_exit_code.txt"
  if [ "$UNIT_RC" -ne 0 ]; then
    warn "Tes unit gagal atau dependensi belum lengkap."
  fi
else
  warn "Direktori tests/unit tidak ditemukan; tes unit dilewati."
fi

log "TAHAP 8 — AUDIT INPUT WORD/PDF DAN BATAS HALAMAN"
rg -n -i \
  'pdf|docx|page_count|pages|175|max_pages|upload|file_uploader|magic|pypdf|pdfplumber|python-docx|timeout|file_size|size_limit' \
  app.py dashboard core engines models requirements.txt 2>/dev/null \
  > "$REPORT_DIR/document_input_audit.txt" || true
cat "$REPORT_DIR/document_input_audit.txt"

log "TAHAP 9 — AUDIT DEPLOYMENT DAN KEAMANAN"
rg -n -i \
  'st\.secrets|os\.environ|dotenv|api[_-]?key|password|token|secret|tempfile|NamedTemporaryFile|unlink|remove\(|delete\(' \
  app.py dashboard core engines models .streamlit requirements.txt 2>/dev/null \
  > "$REPORT_DIR/deployment_security_audit.txt" || true
cat "$REPORT_DIR/deployment_security_audit.txt"

log "TAHAP 10 — AUDIT BENCHMARK YANG SUDAH ADA"
"$PYTHON_BIN" - "$ROOT" "$REPORT_DIR" <<'PY'
import json, sys
from pathlib import Path

root = Path(sys.argv[1])
out = Path(sys.argv[2])
report_dir = root / "output/reports/benchmark"

for name in (
    "thesis_audit_benchmark_evaluation.json",
    "reproducibility_manifest.json",
    "environment_manifest.json",
):
    p = report_dir / name
    if not p.exists():
        print(f"MISSING: {p.relative_to(root)}")
        continue
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"INVALID JSON: {p.name}: {exc}")
        continue
    print(f"\nFILE: {p.relative_to(root)}")
    if name.startswith("thesis_audit"):
        meta = data.get("metadata", {})
        summary = data.get("evaluation_summary", {})
        print("  base_commit:", meta.get("base_commit"))
        print("  code_version:", meta.get("code_version"))
        print("  working_tree_dirty:", meta.get("working_tree_dirty"))
        print("  split:", meta.get("split"))
        print("  total_documents:", summary.get("total_documents"))
        print("  total_reference_findings:", summary.get("total_reference_findings"))
        print("  total_detected_findings:", summary.get("total_detected_findings"))
        print("  limitations:", len(data.get("evaluation_limitations", [])))
    else:
        print("  JSON valid; keys:", ", ".join(list(data.keys())[:20]))

log "TAHAP 11 — STATUS AKHIR"
git status --short > "$REPORT_DIR/git_status_after.txt"
printf 'Laporan audit: %s\n' "$REPORT_DIR"
printf 'Backup lokal: %s\n' "$BACKUP_DIR"
printf 'Commit HEAD: '
git rev-parse HEAD
printf '\n'
cat "$REPORT_DIR/git_status_after.txt"

cat <<EOF

AUDIT SELESAI — BUKAN BERARTI SELURUH FITUR SUDAH LULUS.
- Tidak melakukan commit/push/deploy.
- Tes benchmark yang diketahui menulis ulang DOCX sengaja tidak dijalankan.
- Periksa laporan sebelum melakukan patch.
- Simpan lokasi berikut untuk tahap selanjutnya:
  $AUDIT_DIR
EOF
