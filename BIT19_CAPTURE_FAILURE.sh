#!/bin/bash
set -u

mkdir -p workspace
OUT="workspace/BIT19_FAILURE_DIAGNOSTIC.txt"

{
  echo "=== BIT 19: FAILURE DIAGNOSTIC ==="
  date

  echo
  echo "=== 1. RINGKASAN BIT 18 ==="
  if [ -f workspace/BIT18_DIAGNOSE_FIX_REGRESSION_DEPLOY_GATE.txt ]; then
    grep -n -A 12 -B 8 -E \
      'FAILED|ERROR|AssertionError|ImportError|ModuleNotFoundError|initial_test_exit|full_regression_exit|pip_check_exit|LOCAL_GATE|E +' \
      workspace/BIT18_DIAGNOSE_FIX_REGRESSION_DEPLOY_GATE.txt || true
  else
    echo "Laporan BIT 18 tidak ditemukan."
  fi

  echo
  echo "=== 2. TES PERTAMA YANG GAGAL ==="
  .venv/bin/python3 -m pytest tests/ -x -vv --tb=long --showlocals
  echo "FIRST_FAILURE_EXIT=$?"

  echo
  echo "=== 3. VALIDASI DEPENDENSI ==="
  .venv/bin/python3 -m pip check
  echo "PIP_CHECK_EXIT=$?"

  echo
  echo "=== 4. STATUS WORKTREE ==="
  git status --short

  echo
  echo "=== END BIT 19 ==="
} 2>&1 | tee "$OUT"

echo
echo "Laporan tersimpan: $OUT"
