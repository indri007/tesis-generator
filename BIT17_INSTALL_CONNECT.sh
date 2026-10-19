#!/usr/bin/env bash
# =============================================================================
# BIT17_INSTALL_CONNECT.sh
# Pasang tools QA/riset, simpan API key dengan aman, uji koneksi secara jujur.
#
# Prinsip:
#   - Status hanya PASS / FAIL / WARN / SKIPPED. Tidak ada "PASS palsu".
#   - API key hanya ke .env (chmod 600, di-ignore git), tidak pernah dicetak.
#   - Layanan tertutup (Turnitin, iThenticate, Copyleaks, Grammarly, dst.)
#     tidak di-clone; pemeriksaan resminya manual lewat kampus/penerbit.
#
# Pemakaian: jalankan dari root repo AI-Thesis-Generator
#   chmod +x BIT17_INSTALL_CONNECT.sh
#   ./BIT17_INSTALL_CONNECT.sh --configure-keys
#   ./BIT17_INSTALL_CONNECT.sh
# =============================================================================
set -uo pipefail
umask 077

usage() {
  cat <<'EOF'
Pemakaian: ./BIT17_INSTALL_CONNECT.sh [opsi]
  --configure-keys  isi API key interaktif (ke .env, chmod 600, input tidak tampil)
  --with-extras     pasang paket opsional: datacompy, dedupe, sentry-sdk, logfire, jscpd (jika ada npm)
  --live-paid       izinkan uji koneksi berbayar (Perplexity)
  --mutation        jalankan mutmut (lambat)
  --skip-install    lewati pemasangan paket
  -h, --help        tampilkan bantuan
EOF
}

CONFIGURE=0; WITH_EXTRAS=0; LIVE_PAID=0; MUTATION=0; SKIP_INSTALL=0
for a in "$@"; do
  case "$a" in
    --configure-keys) CONFIGURE=1 ;;
    --with-extras)    WITH_EXTRAS=1 ;;
    --live-paid)      LIVE_PAID=1 ;;
    --mutation)       MUTATION=1 ;;
    --skip-install)   SKIP_INSTALL=1 ;;
    -h|--help)        usage; exit 0 ;;
    *) echo "Opsi tidak dikenal: $a"; usage; exit 2 ;;
  esac
done

cd "$(dirname "${BASH_SOURCE[0]}")" || exit 2
ROOT="$(pwd -P)"

# --- Pengaman: pastikan ini repo yang benar (bukan repo di home directory) ---
TOP="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [ "$TOP" != "$ROOT" ]; then
  echo "[ABORT] Folder ini bukan root git sendiri (root git: ${TOP:-tidak ada})."
  echo "        Jalankan dari /Users/jevin/AI-Thesis-Generator."
  exit 3
fi
REMOTE="$(git remote get-url origin 2>/dev/null || true)"
case "$REMOTE" in
  *indri007/tesis-generator*) ;;
  *) echo "[ABORT] Remote origin bukan indri007/tesis-generator: ${REMOTE:-kosong}"; exit 3 ;;
esac

LOG_DIR="$ROOT/workspace"; mkdir -p "$LOG_DIR"
LOG="$LOG_DIR/BIT17_INSTALL_CONNECT.txt"
exec > >(tee "$LOG") 2>&1

VENV="${VENV:-$ROOT/.venv-test}"
FAILS=0
INSTALL_FAILED=""

echo "BIT17 install+connect | $(date '+%Y-%m-%d %H:%M:%S %z')"
echo "Repo   : $ROOT"
echo "Remote : $REMOTE"

# --- 1. Virtualenv ------------------------------------------------------------
if [ ! -x "$VENV/bin/python3" ] && [ ! -x "$VENV/bin/python" ]; then
  echo "Membuat venv di $VENV"
  python3 -m venv "$VENV" || { echo "[ABORT] gagal membuat venv"; exit 4; }
fi
PY="$VENV/bin/python3"; [ -x "$PY" ] || PY="$VENV/bin/python"
export PATH="$VENV/bin:$PATH"
echo "Python : $("$PY" --version 2>&1)"
git check-ignore -q "$VENV" || echo "[WARN   ] $VENV belum ada di .gitignore; jangan di-commit."

# --- 2. Pemasangan paket (satu per satu; kegagalan dicatat, tidak menghentikan) ---
pip_install() {
  for p in "$@"; do
    if "$PY" -m pip install -q "$p" >/dev/null 2>&1; then
      echo "  ok     $p"
    else
      echo "  GAGAL  $p"
      INSTALL_FAILED="$INSTALL_FAILED $p"
    fi
  done
}

if [ "$SKIP_INSTALL" -eq 0 ]; then
  echo; echo "== Pemasangan paket =="
  "$PY" -m pip install -q --upgrade pip >/dev/null 2>&1
  echo "[Kualitas & pengujian]"
  pip_install pytest pytest-cov hypothesis coverage mutmut ruff mypy pyright bandit pylint pre-commit
  echo "[Validasi data]"
  pip_install pydantic pandas pandera
  echo "[Riset & MLOps]"
  pip_install requests mlflow dvc wandb
  if [ "$WITH_EXTRAS" -eq 1 ]; then
    echo "[Opsional]"
    pip_install datacompy dedupe sentry-sdk logfire
    if command -v npm >/dev/null 2>&1; then
      if npm install -g jscpd >/dev/null 2>&1; then echo "  ok     jscpd"; else echo "  GAGAL  jscpd (npm global)"; INSTALL_FAILED="$INSTALL_FAILED jscpd"; fi
    else
      echo "  [SKIPPED] jscpd: npm tidak ditemukan"
    fi
  fi
  if [ -n "$INSTALL_FAILED" ]; then
    echo "[FAIL   ] Paket gagal terpasang:$INSTALL_FAILED"
    FAILS=$((FAILS+1))
  else
    echo "[PASS   ] Semua paket terpasang"
  fi
else
  echo; echo "[SKIPPED] Pemasangan paket (--skip-install)"
fi

# --- 3. .env, .env.example, .gitignore ----------------------------------------
echo; echo "== Konfigurasi .env =="
KEYS="CONTACT_EMAIL PERPLEXITY_API_KEY SEMANTIC_SCHOLAR_API_KEY OPENALEX_API_KEY WANDB_API_KEY SENTRY_DSN LOGFIRE_TOKEN ELICIT_API_KEY CONSENSUS_API_KEY"

touch .env.example
for k in $KEYS; do
  grep -q "^${k}=" .env.example || echo "${k}=" >> .env.example
done
grep -qxF '.env' .gitignore 2>/dev/null || echo '.env' >> .gitignore

if git ls-files --error-unmatch .env >/dev/null 2>&1; then
  echo "[FAIL   ] .env sudah ter-track git! Jalankan: git rm --cached .env  lalu ganti semua key."
  FAILS=$((FAILS+1))
fi

upsert_env() {
  local k="$1" v="$2" tmp
  case "$v" in
    *"'"*|*$'\n'*) echo "  [WARN] $k ditolak: nilai tidak boleh berisi tanda kutip tunggal atau baris baru"; return 1 ;;
  esac
  tmp="$(mktemp)"
  if [ -f .env ]; then grep -v "^${k}=" .env > "$tmp" || true; fi
  printf "%s='%s'\n" "$k" "$v" >> "$tmp"
  mv "$tmp" .env
  chmod 600 .env
}

prompt_key() {
  local k="$1" desc="$2" v
  if [ "$k" = "CONTACT_EMAIL" ]; then
    read -r -p "  $k ($desc) [Enter = lewati]: " v
  else
    read -r -s -p "  $k ($desc) [Enter = lewati]: " v; echo
  fi
  if [ -n "$v" ]; then upsert_env "$k" "$v" && echo "  tersimpan: $k"; fi
}

if [ "$CONFIGURE" -eq 1 ]; then
  echo "Isi key yang Anda punya. Kosongkan jika tidak. Input tidak ditampilkan."
  prompt_key CONTACT_EMAIL         "email untuk polite pool Crossref/OpenAlex"
  prompt_key PERPLEXITY_API_KEY    "Perplexity API, berbayar"
  prompt_key SEMANTIC_SCHOLAR_API_KEY "opsional, menaikkan rate limit"
  prompt_key OPENALEX_API_KEY      "opsional"
  prompt_key WANDB_API_KEY         "opsional, hanya jika pakai W&B online"
  prompt_key SENTRY_DSN            "opsional"
  prompt_key LOGFIRE_TOKEN         "opsional"
  prompt_key ELICIT_API_KEY        "hanya jika akun Anda punya akses API"
  prompt_key CONSENSUS_API_KEY     "hanya jika akun Anda punya akses API"
fi

if [ -f .env ]; then
  chmod 600 .env
  set -a; . ./.env; set +a
  echo "Key terisi di .env:"
  for k in $KEYS; do
    eval "val=\${$k:-}"
    if [ -n "$val" ]; then echo "  [x] $k"; else echo "  [ ] $k"; fi
  done
else
  echo "Belum ada .env. Jalankan dengan --configure-keys atau salin .env.example ke .env."
fi

# --- 4. Uji koneksi (Python; hasil nyata, bukan tiruan) -----------------------
echo; echo "== Uji koneksi & integrasi lokal =="
CHECKER="$(mktemp -t bit17check.XXXXXX).py"
cat > "$CHECKER" <<'PYEOF'
import json, os, re, shutil, subprocess, sys, tempfile
import urllib.error, urllib.parse, urllib.request

EMAIL = os.environ.get("CONTACT_EMAIL", "").strip()
UA = "BIT17-check/1.0" + (f" (mailto:{EMAIL})" if EMAIL else "")
LIVE_PAID = os.environ.get("BIT17_LIVE_PAID") == "1"
DOI, TITLE_HINT = "10.1038/nature14539", "deep learning"
fails = 0


def rec(status, name, detail=""):
    global fails
    if status == "FAIL":
        fails += 1
    print(f"[{status:<7}] {name}" + (f": {detail}" if detail else ""))


def has(k):
    return bool(os.environ.get(k, "").strip())


def http(url, headers=None, body=None, timeout=25):
    h = {"User-Agent": UA}
    h.update(headers or {})
    req = urllib.request.Request(url, headers=h, data=body)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, json.loads(r.read().decode("utf-8", "replace"))


def net_err(name, e):
    if isinstance(e, urllib.error.HTTPError):
        if e.code in (401, 403):
            rec("FAIL", name, f"HTTP {e.code}: key ditolak atau tidak punya akses")
        elif e.code == 429:
            rec("WARN", name, "HTTP 429 rate limit; isi API key atau coba lagi nanti")
        else:
            rec("FAIL", name, f"HTTP {e.code}")
    elif isinstance(e, (urllib.error.URLError, TimeoutError, OSError)):
        rec("WARN", name, "tidak ada koneksi internet / timeout; tidak diverifikasi")
    else:
        rec("FAIL", name, f"{type(e).__name__}: {e}")


def check_crossref():
    q = "?" + urllib.parse.urlencode({"mailto": EMAIL}) if EMAIL else ""
    try:
        _, j = http(f"https://api.crossref.org/works/{DOI}{q}")
        t = (j["message"].get("title") or [""])[0]
        ok = TITLE_HINT in t.lower()
        rec("PASS" if ok else "FAIL", "Crossref (DOI cocok judul)", t[:50])
    except Exception as e:
        net_err("Crossref", e)


def check_openalex():
    p = {}
    if EMAIL:
        p["mailto"] = EMAIL
    if has("OPENALEX_API_KEY"):
        p["api_key"] = os.environ["OPENALEX_API_KEY"].strip()
    q = "?" + urllib.parse.urlencode(p) if p else ""
    try:
        _, j = http(f"https://api.openalex.org/works/doi:{DOI}{q}")
        t = j.get("display_name", "")
        ok = TITLE_HINT in t.lower()
        rec("PASS" if ok else "FAIL", "OpenAlex (DOI cocok judul)", t[:50])
    except Exception as e:
        net_err("OpenAlex", e)


def check_s2():
    h = {"x-api-key": os.environ["SEMANTIC_SCHOLAR_API_KEY"].strip()} if has("SEMANTIC_SCHOLAR_API_KEY") else {}
    try:
        _, j = http(f"https://api.semanticscholar.org/graph/v1/paper/DOI:{DOI}?fields=title,year", h)
        ok = TITLE_HINT in (j.get("title") or "").lower()
        rec("PASS" if ok else "FAIL", "Semantic Scholar (DOI cocok judul)", (j.get("title") or "")[:50])
    except Exception as e:
        net_err("Semantic Scholar", e)


def check_perplexity():
    if not has("PERPLEXITY_API_KEY"):
        rec("SKIPPED", "Perplexity", "PERPLEXITY_API_KEY kosong")
        return
    if not LIVE_PAID:
        rec("SKIPPED", "Perplexity", "key terisi; uji nyata berbayar, jalankan dengan --live-paid")
        return
    body = json.dumps({"model": "sonar", "messages": [{"role": "user", "content": "ping"}], "max_tokens": 1}).encode()
    h = {"Authorization": "Bearer " + os.environ["PERPLEXITY_API_KEY"].strip(), "Content-Type": "application/json"}
    try:
        s, _ = http("https://api.perplexity.ai/chat/completions", h, body)
        rec("PASS" if s == 200 else "FAIL", "Perplexity (panggilan nyata)", f"HTTP {s}")
    except Exception as e:
        net_err("Perplexity", e)


def check_wandb_online():
    if not has("WANDB_API_KEY"):
        rec("SKIPPED", "W&B online", "WANDB_API_KEY kosong (mode offline tetap diuji di bawah)")
        return
    try:
        import wandb
        user = wandb.Api(api_key=os.environ["WANDB_API_KEY"].strip()).viewer.username
        rec("PASS", "W&B online", f"login sebagai {user}")
    except Exception as e:
        rec("FAIL", "W&B online", f"{type(e).__name__}: {str(e)[:80]}")


def check_dsn_tokens():
    dsn = os.environ.get("SENTRY_DSN", "").strip()
    if not dsn:
        rec("SKIPPED", "Sentry", "SENTRY_DSN kosong (opsional)")
    elif re.match(r"^https://[^@\s]+@[^/\s]+/\d+$", dsn):
        rec("WARN", "Sentry", "format DSN valid; TIDAK diuji online")
    else:
        rec("FAIL", "Sentry", "format DSN tidak valid")
    if has("LOGFIRE_TOKEN"):
        rec("WARN", "Logfire", "token terisi; TIDAK diuji online")
    else:
        rec("SKIPPED", "Logfire", "LOGFIRE_TOKEN kosong (opsional)")


def check_mlflow():
    d = tempfile.mkdtemp()
    try:
        import mlflow
        os.environ["MLFLOW_ALLOW_FILE_STORE"] = "true"
        mlflow.set_tracking_uri(f"file://{d}/mlruns")
        exp = mlflow.create_experiment("bit17", artifact_location=d)
        with mlflow.start_run(experiment_id=exp) as r:
            mlflow.log_param("k", "v")
            mlflow.log_metric("m", 0.5)
        run = mlflow.get_run(r.info.run_id)
        ok = run.data.params.get("k") == "v" and run.data.metrics.get("m") == 0.5 and run.info.status == "FINISHED"
        rec("PASS" if ok else "FAIL", "MLflow lokal (file)", "param/metrik terbaca ulang" if ok else "data tidak cocok")
    except ImportError:
        rec("FAIL", "MLflow lokal", "mlflow tidak terpasang")
    except Exception as e:
        rec("FAIL", "MLflow lokal", f"{type(e).__name__}: {str(e)[:80]}")
    finally:
        shutil.rmtree(d, ignore_errors=True)


def check_dvc():
    exe = shutil.which("dvc")
    if not exe:
        rec("FAIL", "DVC lokal", "dvc tidak terpasang")
        return
    d = tempfile.mkdtemp()
    try:
        with open(os.path.join(d, "data.txt"), "w") as f:
            f.write("hello")
        r1 = subprocess.run([exe, "init", "--no-scm"], cwd=d, capture_output=True, text=True)
        r2 = subprocess.run([exe, "add", "data.txt"], cwd=d, capture_output=True, text=True)
        ok = r1.returncode == 0 and r2.returncode == 0 and os.path.exists(os.path.join(d, "data.txt.dvc"))
        rec("PASS" if ok else "FAIL", "DVC lokal (init + add)", "" if ok else (r2.stderr or r1.stderr)[:80])
    finally:
        shutil.rmtree(d, ignore_errors=True)


def check_wandb_offline():
    d = tempfile.mkdtemp()
    old = {k: os.environ.get(k) for k in ("WANDB_MODE", "WANDB_SILENT")}
    os.environ["WANDB_MODE"], os.environ["WANDB_SILENT"] = "offline", "true"
    try:
        import wandb
        run = wandb.init(project="bit17", dir=d)
        run.log({"f1": 0.9})
        run.finish()
        rec("PASS", "W&B offline", "run dicatat lokal")
    except ImportError:
        rec("FAIL", "W&B offline", "wandb tidak terpasang")
    except Exception as e:
        rec("FAIL", "W&B offline", f"{type(e).__name__}: {str(e)[:80]}")
    finally:
        for k, v in old.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        shutil.rmtree(d, ignore_errors=True)


def check_pydantic():
    try:
        from pydantic import BaseModel, ValidationError

        class M(BaseModel):
            year: int

        coerced = M(year="2021").year == 2021
        try:
            M(year="abc")
            rejected = False
        except ValidationError:
            rejected = True
        rec("PASS" if coerced and rejected else "FAIL", "Pydantic", "coercion + penolakan data salah")
    except ImportError:
        rec("FAIL", "Pydantic", "tidak terpasang")


def check_pandera():
    try:
        try:
            import pandera.pandas as pa
        except ImportError:
            import pandera as pa
        import pandas as pd
        schema = pa.DataFrameSchema({"year": pa.Column(int, pa.Check.ge(2000))})
        schema.validate(pd.DataFrame({"year": [2021]}))
        try:
            schema.validate(pd.DataFrame({"year": [1990]}))
            rejected = False
        except Exception:
            rejected = True
        rec("PASS" if rejected else "FAIL", "Pandera", "skema menolak data di luar batas")
    except ImportError:
        rec("FAIL", "Pandera", "pandera/pandas tidak terpasang")


print("-- API eksternal --")
check_crossref()
check_openalex()
check_s2()
check_perplexity()
check_wandb_online()
check_dsn_tokens()
for n in ("Elicit", "Consensus", "SciSpace", "ResearchRabbit"):
    rec("SKIPPED", n, "belum ada adapter di repo ini; gunakan checklist manual")
print("-- Integrasi lokal --")
check_mlflow()
check_dvc()
check_wandb_offline()
check_pydantic()
check_pandera()
sys.exit(1 if fails else 0)
PYEOF

BIT17_LIVE_PAID="$LIVE_PAID" "$PY" "$CHECKER"
CRC=$?
rm -f "$CHECKER"
if [ "$CRC" -ne 0 ]; then FAILS=$((FAILS+1)); fi

# --- 5. QA kode ------------------------------------------------------------------
echo; echo "== QA kode =="
SRC=""
for d in core engines parsers models; do [ -d "$d" ] && SRC="$SRC $d"; done

run_step() {
  local name="$1"; shift
  echo; echo "-- $name --"
  "$@"
  local rc=$?
  if [ "$rc" -eq 0 ]; then
    echo "[PASS   ] $name"
  else
    echo "[FAIL   ] $name (exit $rc)"
    FAILS=$((FAILS+1))
  fi
}

if [ -d tests ]; then
  run_step "pytest + coverage (hypothesis ikut berjalan)" "$PY" -m coverage run -m pytest tests -q -W default
  run_step "coverage report" "$PY" -m coverage report
else
  echo "[SKIPPED] pytest: folder tests/ tidak ada"
fi

if [ -n "$SRC" ]; then
  run_step "ruff"    "$PY" -m ruff check $SRC
  run_step "mypy"    "$PY" -m mypy $SRC
  run_step "pyright" "$VENV/bin/pyright" $SRC
  run_step "bandit"  "$PY" -m bandit -q -r $SRC
  run_step "pylint (errors only)" "$PY" -m pylint --recursive=y --errors-only $SRC
else
  echo "[SKIPPED] linter/type/security: tidak ada folder core/engines/parsers/models"
fi

if [ -f .pre-commit-config.yaml ]; then
  run_step "pre-commit install" "$VENV/bin/pre-commit" install
else
  echo "[SKIPPED] pre-commit: .pre-commit-config.yaml belum ada"
fi

if [ "$MUTATION" -eq 1 ]; then
  run_step "mutmut" "$VENV/bin/mutmut" run
else
  echo "[SKIPPED] mutmut: lambat, aktifkan dengan --mutation"
fi

if [ "$WITH_EXTRAS" -eq 1 ] && command -v jscpd >/dev/null 2>&1 && [ -n "$SRC" ]; then
  run_step "jscpd (duplikasi kode)" jscpd --silent $SRC
fi

# --- 6. Ringkasan --------------------------------------------------------------
echo; echo "================ RINGKASAN ================"
echo "Log lengkap : $LOG"
if [ "$FAILS" -eq 0 ]; then
  echo "Hasil       : tidak ada FAIL. Periksa baris WARN/SKIPPED di atas; itu belum terverifikasi."
else
  echo "Hasil       : $FAILS langkah FAIL. Lihat baris [FAIL   ] di atas."
fi
echo "Ingat       : git status && git diff --stat sebelum commit. Jangan commit .env."
[ "$FAILS" -eq 0 ]
