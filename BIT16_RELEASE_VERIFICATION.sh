#!/bin/bash
set -u

ROOT="/Users/jevin/Downloads/TesisCheck_MIKOM2026"
cd "$ROOT" || exit 1
mkdir -p workspace
OUT="workspace/BIT16_RELEASE_VERIFICATION.txt"
PY="$ROOT/.venv/bin/python3"

{
  echo "=== BIT 16: RELEASE VERIFICATION ==="
  date

  echo
  echo "=== 1. REPOSITORY DAN COMMIT LOKAL ==="
  git remote -v
  git branch --show-current
  git rev-parse HEAD
  git log -1 --format='%h %s'
  git status -sb

  echo
  echo "=== 2. STATUS REMOTE MAIN ==="
  git ls-remote origin refs/heads/main
  echo "remote_check_exit=$?"

  echo
  echo "=== 3. KEBERSIHAN DIFF ==="
  git diff --check
  echo "working_diff_check_exit=$?"
  git diff --cached --check
  echo "staged_diff_check_exit=$?"

  echo
  echo "=== 4. DEPENDENSI ==="
  "$PY" --version
  "$PY" -m pip check
  echo "pip_check_exit=$?"

  echo
  echo "=== 5. TEST SUITE ==="
  "$PY" -m pytest tests/ -q
  echo "pytest_exit=$?"

  echo
  echo "=== 6. STREAMLIT DAN FILE ENTRYPOINT ==="
  "$PY" -m streamlit --version
  echo "streamlit_version_exit=$?"

  for f in app.py requirements.txt .streamlit/config.toml; do
    if [ -f "$f" ]; then
      echo "FOUND: $f"
    else
      echo "MISSING: $f"
    fi
  done

  echo
  echo "=== 7. DEPLOYMENT CONFIG REFERENCES ==="
  grep -RInE \
    'streamlit\.app|streamlitapp|appName|repository|branch|mainModule' \
    README.md .streamlit 2>/dev/null || true

  echo
  echo "=== END BIT 16 ==="
  echo "Tidak melakukan commit, push, atau deployment."
} > "$OUT" 2>&1

echo "Laporan: $OUT"
cat "$OUT"
