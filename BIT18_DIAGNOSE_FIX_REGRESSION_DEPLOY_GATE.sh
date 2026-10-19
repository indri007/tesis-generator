#!/bin/bash
set -u

ROOT="/Users/jevin/Downloads/TesisCheck_MIKOM2026"
cd "$ROOT" || exit 1

PY="$ROOT/.venv/bin/python3"
mkdir -p workspace
OUT="workspace/BIT18_DIAGNOSE_FIX_REGRESSION_DEPLOY_GATE.txt"

if [ ! -x "$PY" ]; then
  echo "STOP: Python environment tidak ditemukan: $PY"
  exit 1
fi

{
  echo "=== BIT 18: DIAGNOSIS, FIX, REGRESSION, DEPLOY GATE ==="
  date

  echo
  echo "=== TAHAP 1: DIAGNOSIS TES GAGAL ==="
  "$PY" -m pytest tests/ -x -vv --tb=long
  TEST_EXIT=$?
  echo "initial_test_exit=$TEST_EXIT"

  echo
  echo "=== TAHAP 2: DETAIL TES GAGAL ==="
  if [ "$TEST_EXIT" -ne 0 ]; then
    echo "Tes gagal ditemukan. Mengumpulkan konteks tanpa mengubah kode."
    "$PY" -m pytest tests/ -x -vv --tb=long --showlocals
    echo "diagnostic_rerun_exit=$?"
    echo
    echo "STATUS: PATCH OTOMATIS DIBATALKAN."
    echo "Periksa AssertionError sebelum menentukan perubahan."
    echo "Tidak mengedit atau memulihkan file secara otomatis."
  else
    echo "Tes yang dijalankan dengan -x lulus."
  fi

  echo
  echo "=== TAHAP 3: REGRESI PENUH ==="
  if [ "$TEST_EXIT" -eq 0 ]; then
    "$PY" -m pytest tests/ -q
    FULL_EXIT=$?
    echo "full_regression_exit=$FULL_EXIT"
  else
    FULL_EXIT=99
    echo "DILEWATI: diagnosis awal gagal."
  fi

  echo
  echo "=== TAHAP 4: DEPLOYMENT READINESS GATE ==="
  echo "--- Git status"
  git status -sb
  echo "--- HEAD"
  git log -1 --format='%h %s'
  echo "--- Remote main"
  git ls-remote origin refs/heads/main
  echo "remote_query_exit=$?"

  echo "--- Diff check"
  git diff --check
  echo "diff_check_exit=$?"

  echo "--- Dependency check"
  "$PY" -m pip check
  PIP_EXIT=$?
  echo "pip_check_exit=$PIP_EXIT"

  echo "--- Required files"
  for f in app.py requirements.txt .streamlit/config.toml; do
    if [ -f "$f" ]; then
      echo "PASS: $f"
    else
      echo "FAIL: $f tidak ditemukan"
    fi
  done

  echo
  echo "=== HASIL AKHIR ==="
  if [ "$TEST_EXIT" -eq 0 ] && \
     [ "$FULL_EXIT" -eq 0 ] && \
     [ "$PIP_EXIT" -eq 0 ]; then
    echo "LOCAL_GATE=PASS"
    echo "Catatan: ini belum membuktikan deployment cloud berhasil."
  else
    echo "LOCAL_GATE=FAIL_OR_BLOCKED"
    echo "Jangan deploy sebelum penyebab kegagalan diselesaikan."
  fi

  echo
  echo "Tidak ada perubahan kode otomatis."
  echo "Tidak ada staging, commit, push, atau deployment."
} > "$OUT" 2>&1

echo "BIT 18 selesai."
echo "Laporan: $OUT"
cat "$OUT"
