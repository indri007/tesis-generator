#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(git rev-parse --show-toplevel)" || exit 1
cd "$ROOT"

STAMP="$(date +%Y%m%d_%H%M%S)"
SAFE="$ROOT/workspace/bit_patch_$STAMP"
mkdir -p "$SAFE/backup" "$SAFE/reports"

echo "=================================================="
echo "TesisCheck — PATCH ISOLASI BENCHMARK"
echo "Root: $ROOT"
echo "Backup: $SAFE/backup"
echo "=================================================="

# Jangan menyentuh secrets atau memulihkan perubahan secara otomatis.
for f in \
  golden_dataset/generator.py \
  tests/golden_dataset/test_academic_benchmark.py \
  tests/test_golden_dataset.py \
  core/evaluation/schema.py \
  core/evaluation/benchmark_runner.py \
  requirements.txt pyproject.toml
do
  if [ -f "$f" ]; then
    mkdir -p "$SAFE/backup/$(dirname "$f")"
    cp -p "$f" "$SAFE/backup/$f"
  fi
done

git status --short > "$SAFE/reports/git_status_before.txt"
git diff --binary > "$SAFE/backup/tracked_changes.patch"
git diff --cached --binary > "$SAFE/backup/staged_changes.patch"

# Simpan hash fixture sebelum patch.
find golden_dataset/documents -maxdepth 1 -type f -name '*.docx' -print0 |
  while IFS= read -r -d '' f; do shasum -a 256 "$f"; done \
  > "$SAFE/reports/docx_hashes_before.txt"

echo
echo "[1/5] Memeriksa pola kode dan membuat patch terarah..."

python3 - "$ROOT" <<'PY'
import ast
import re
import sys
from pathlib import Path

root = Path(sys.argv[1])
gen_path = root / "golden_dataset/generator.py"
test_path = root / "tests/golden_dataset/test_academic_benchmark.py"
regression_path = root / "tests/unit/test_generator_isolation.py"

gen = gen_path.read_text(encoding="utf-8")
test = test_path.read_text(encoding="utf-8")

# Preflight: jangan menerka bila struktur berbeda.
if 'DOCS_DIR = BASE_DIR / "documents"' not in gen:
    raise SystemExit(
        "STOP: deklarasi DOCS_DIR berbeda dari yang diharapkan. "
        "Tidak ada file kode yang diubah."
    )

if "def generate_golden_dataset()" not in gen:
    raise SystemExit(
        "STOP: signature generate_golden_dataset() berbeda. "
        "Tidak ada file kode yang diubah."
    )

if "generate_golden_dataset()" not in test:
    raise SystemExit(
        "STOP: pemanggilan generator di tes benchmark tidak ditemukan."
    )

if 'output_dir="output/reports/benchmark"' not in test:
    raise SystemExit(
        "STOP: pola output_dir benchmark tidak ditemukan."
    )

if 'base_commit="1c34578"' not in test or \
   'code_version="1c34578"' not in test:
    raise SystemExit(
        "STOP: metadata commit tidak sesuai pola yang diharapkan."
    )

# Patch generator di memori.
gen = gen.replace(
    'DOCS_DIR = BASE_DIR / "documents"',
    'DOCS_DIR = BASE_DIR.parent / "workspace" / "generated_golden_dataset"',
    1,
)

gen_tree = ast.parse(gen)
func = next(
    (n for n in gen_tree.body
     if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
     and n.name == "generate_golden_dataset"),
    None,
)
if func is None:
    raise SystemExit("STOP: fungsi generator tidak dapat dipetakan.")

lines = gen.splitlines(keepends=True)
start = func.lineno - 1
end = func.end_lineno

# Tambahkan parameter output_dir.
lines[start] = lines[start].replace(
    "def generate_golden_dataset()",
    "def generate_golden_dataset(output_dir=None)",
    1,
)

# Ubah referensi DOCS_DIR / di dalam fungsi saja.
for i in range(start + 1, end):
    lines[i] = lines[i].replace("DOCS_DIR /", "docs_dir /")

# Sisipkan inisialisasi setelah docstring bila ada.
new_gen = "".join(lines)
tree_after_signature = ast.parse(new_gen)
func_after = next(
    n for n in tree_after_signature.body
    if isinstance(n, ast.FunctionDef)
    and n.name == "generate_golden_dataset"
)
insert_at = func_after.lineno
if func_after.body and isinstance(func_after.body[0], ast.Expr) \
        and isinstance(func_after.body[0].value, ast.Constant) \
        and isinstance(func_after.body[0].value.value, str):
    insert_at = func_after.body[0].end_lineno + 1

new_lines = new_gen.splitlines(keepends=True)
new_lines.insert(
    insert_at - 1,
    "    docs_dir = Path(output_dir) if output_dir is not None else DOCS_DIR\n"
    "    docs_dir.mkdir(parents=True, exist_ok=True)\n",
)
new_gen = "".join(new_lines)

# Pastikan generator hasil patch masih valid Python.
ast.parse(new_gen)

# Patch benchmark test: lokasi dokumen dan laporan bersifat sementara.
test_tree = ast.parse(test)
candidate = None
for node in ast.walk(test_tree):
    if isinstance(node, ast.FunctionDef) and any(
        isinstance(child, ast.Call)
        and isinstance(child.func, ast.Name)
        and child.func.id == "generate_golden_dataset"
        for child in ast.walk(node)
    ):
        candidate = node
        break

if candidate is None:
    raise SystemExit("STOP: fungsi tes pemanggil generator tidak ditemukan.")

test_lines = test.splitlines(keepends=True)
fn_index = candidate.lineno - 1
signature = test_lines[fn_index]

if "tmp_path" not in signature:
    signature = signature.replace("()", "(tmp_path)", 1)
    test_lines[fn_index] = signature

# Sisipkan konfigurasi sementara setelah docstring fungsi bila ada.
test_modified = "".join(test_lines)
tree2 = ast.parse(test_modified)
candidate2 = next(
    n for n in tree2.body
    if isinstance(n, ast.FunctionDef) and n.name == candidate.name
)
insert_at = candidate2.lineno
if candidate2.body and isinstance(candidate2.body[0], ast.Expr) \
        and isinstance(candidate2.body[0].value, ast.Constant) \
        and isinstance(candidate2.body[0].value.value, str):
    insert_at = candidate2.body[0].end_lineno + 1

test_lines = test_modified.splitlines(keepends=True)
test_lines.insert(
    insert_at - 1,
    "    benchmark_docs_dir = tmp_path / 'documents'\n"
    "    benchmark_docs_dir.mkdir(parents=True, exist_ok=True)\n"
    "    git_metadata = {\n"
    "        'commit': __import__('subprocess').run(\n"
    "            ['git', 'rev-parse', 'HEAD'], cwd=Path(__file__).resolve().parents[2],\n"
    "            capture_output=True, text=True, check=True\n"
    "        ).stdout.strip(),\n"
    "        'dirty': bool(__import__('subprocess').run(\n"
    "            ['git', 'status', '--porcelain'], cwd=Path(__file__).resolve().parents[2],\n"
    "            capture_output=True, text=True, check=True\n"
    "        ).stdout.strip()),\n"
    "    }\n",
)
new_test = "".join(test_lines)

# Sesuaikan import DOCS_DIR dan output generator.
new_test = new_test.replace(", DOCS_DIR", "")
new_test = new_test.replace(
    "generate_golden_dataset()",
    "generate_golden_dataset(output_dir=benchmark_docs_dir)",
)
new_test = new_test.replace(
    "DOCS_DIR /",
    "benchmark_docs_dir /",
)
new_test = new_test.replace(
    'base_commit="1c34578"',
    'base_commit=git_metadata["commit"]',
)
new_test = new_test.replace(
    'code_version="1c34578"',
    'code_version=git_metadata["commit"]',
)
new_test = new_test.replace(
    "working_tree_dirty=True",
    'working_tree_dirty=git_metadata["dirty"]',
)
new_test = new_test.replace(
    'output_dir="output/reports/benchmark"',
    'output_dir=tmp_path / "reports"',
)

# Uji sintaks sebelum menulis apa pun.
ast.parse(new_test)

# Tambahkan tes regresi isolasi.
regression = '''"""Regression tests: benchmark generation must not overwrite fixtures."""
import hashlib
from pathlib import Path

from golden_dataset.generator import generate_golden_dataset


def test_generator_writes_to_requested_directory_and_preserves_fixtures(tmp_path):
    root = Path(__file__).resolve().parents[2]
    fixtures = root / "golden_dataset" / "documents"
    before = {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in fixtures.glob("*.docx")
    }

    output_dir = tmp_path / "generated_docs"
    output_dir.mkdir()
    generate_golden_dataset(output_dir=output_dir)

    generated = list(output_dir.glob("*.docx"))
    assert generated, "Generator tidak menghasilkan dokumen DOCX."

    after = {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in fixtures.glob("*.docx")
    }
    assert after == before, "Fixture DOCX sumber berubah saat generator berjalan."
'''

# Tulis file setelah semua preflight lolos.
gen_path.write_text(new_gen, encoding="utf-8")
test_path.write_text(new_test, encoding="utf-8")
regression_path.parent.mkdir(parents=True, exist_ok=True)
regression_path.write_text(regression, encoding="utf-8")

print("PASS: generator menerima output_dir.")
print("PASS: direktori default generator dipisahkan dari fixture.")
print("PASS: benchmark diarahkan ke tmp_path.")
print("PASS: metadata benchmark mengambil commit/status Git aktual.")
print("PASS: tes regresi isolasi dibuat.")
PY

echo
echo "[2/5] Validasi sintaks Python..."
PYTHON_BIN="python3"
if [ -x ".venv/bin/python" ]; then PYTHON_BIN=".venv/bin/python"; fi

"$PYTHON_BIN" -m compileall -q \
  golden_dataset/generator.py \
  tests/golden_dataset/test_academic_benchmark.py \
  tests/unit/test_generator_isolation.py \
  core/evaluation models engines \
  > "$SAFE/reports/compileall.log" 2>&1 || {
    cat "$SAFE/reports/compileall.log"
    echo "ERROR: syntax check gagal. Backup tersedia di $SAFE/backup"
    exit 1
  }
echo "PASS: compileall"

echo
echo "[3/5] Memeriksa Python 3.11 untuk lingkungan uji terpisah..."
if command -v python3.11 >/dev/null 2>&1; then
  TEST_PYTHON="$(command -v python3.11)"
else
  TEST_PYTHON=""
fi

if [ -z "$TEST_PYTHON" ]; then
  echo "Python 3.11 tidak ditemukan."
  echo "Tidak membuat .venv-test dengan Python 3.14 secara otomatis."
  echo "Pasang Python 3.11 terlebih dahulu, lalu jalankan skrip ini lagi hanya"
  echo "setelah meninjau patch yang sudah diterapkan."
else
  TEST_ENV="$ROOT/.venv-test"
  if [ -e "$TEST_ENV" ]; then
    echo "Lingkungan $TEST_ENV sudah ada; tidak ditimpa."
  else
    "$TEST_PYTHON" -m venv "$TEST_ENV"
    echo "Lingkungan dibuat: $TEST_ENV"
  fi

  if [ -f requirements.txt ]; then
    echo
    echo "[4/5] Memasang requirements proyek + pytest ke .venv-test..."
    set +e
    "$TEST_ENV/bin/python" -m pip install --upgrade pip
    PIP_UPGRADE_RC=$?
    "$TEST_ENV/bin/python" -m pip install -r requirements.txt pytest
    PIP_INSTALL_RC=$?
    set -e
    printf 'pip_upgrade_rc=%s\npip_install_rc=%s\n' \
      "$PIP_UPGRADE_RC" "$PIP_INSTALL_RC" \
      > "$SAFE/reports/pip_status.txt"

    if [ "$PIP_INSTALL_RC" -eq 0 ]; then
      echo
      echo "[5/5] Menjalankan tes terisolasi..."
      set +e
      "$TEST_ENV/bin/python" -m pytest -q \
        tests/unit/test_generator_isolation.py \
        tests/golden_dataset/test_academic_benchmark.py \
        --junitxml="$SAFE/reports/isolated_tests.xml" \
        > "$SAFE/reports/isolated_tests.log" 2>&1
      TEST_RC=$?
      set -e
      cat "$SAFE/reports/isolated_tests.log"
      echo "$TEST_RC" > "$SAFE/reports/isolated_tests_exit_code.txt"
      if [ "$TEST_RC" -ne 0 ]; then
        echo "WARNING: tes gagal. Lihat log; jangan deploy dahulu."
      fi
    else
      echo "WARNING: instalasi dependensi gagal; tes tidak dijalankan."
    fi
  else
    echo "ERROR: requirements.txt tidak ditemukan."
  fi
fi

echo
echo "=== RINGKASAN PATCH ==="
git diff --stat
git status --short

echo
echo "=== LOKASI LAPORAN DAN BACKUP ==="
echo "$SAFE"
echo
echo "Tidak ada commit, push, atau deployment otomatis."
