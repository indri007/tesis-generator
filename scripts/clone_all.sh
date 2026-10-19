#!/usr/bin/env bash
# ============================================================================
# clone_all.sh : clone semua proyek dari daftar 50 sumber (yang bisa di-clone)
# untuk riset "clone CorelDRAW" (editor vektor, parser .cdr, engine SVG, dll.)
#
# Pemakaian:
#   chmod +x clone_all.sh
#   ./clone_all.sh                      # shallow clone (--depth 1), hemat ruang
#   FULL=1 ./clone_all.sh               # riwayat git lengkap (jauh lebih besar)
#   DEST=/data/refs ./clone_all.sh      # ganti folder tujuan (default ~/corel-clone-refs)
#   ONLY=02 ./clone_all.sh              # hanya kategori yang namanya diawali 02
#   WITH_HF=0 ./clone_all.sh            # lewati repo Hugging Face
#
# Aman dijalankan ulang: repo yang sudah ada dilewati; yang gagal dicatat di
# $DEST/_failed.txt. Butuh: git (dan curl + tar untuk crate cdrsdk).
# ============================================================================

DEST="${DEST:-$HOME/corel-clone-refs}"
DEPTH_OPT="--depth 1"
[ "${FULL:-0}" = "1" ] && DEPTH_OPT=""
ONLY="${ONLY:-}"
WITH_HF="${WITH_HF:-1}"

mkdir -p "$DEST" || exit 1
LOG="$DEST/_clone.log"; OK="$DEST/_ok.txt"; FAIL="$DEST/_failed.txt"
: > "$FAIL"; : > "$OK"
export GIT_TERMINAL_PROMPT=0

command -v git >/dev/null 2>&1 || { echo "git belum terpasang."; exit 1; }

want() { [ -z "$ONLY" ] || [[ "$1" == "$ONLY"* ]]; }

# clone <kategori> <folder> <url> [url-cadangan ...]
# Variabel LFS_SKIP=1 di depan pemanggilan = jangan unduh file LFS besar (hanya pointer).
clone() {
  local cat="$1" name="$2"; shift 2
  want "$cat" || return 0
  local target="$DEST/$cat/$name" url try
  if [ -d "$target/.git" ]; then
    echo "[SKIP ] $cat/$name (sudah ada)"; echo "$cat/$name (sudah ada)" >> "$OK"; return 0
  fi
  mkdir -p "$DEST/$cat"
  for url in "$@"; do
    for try in 1 2 3; do
      if [ "${LFS_SKIP:-0}" = "1" ]; then
        # shellcheck disable=SC2086
        env GIT_LFS_SKIP_SMUDGE=1 git clone $DEPTH_OPT "$url" "$target" >>"$LOG" 2>&1
      else
        # shellcheck disable=SC2086
        git clone $DEPTH_OPT "$url" "$target" >>"$LOG" 2>&1
      fi
      if [ $? -eq 0 ]; then
        echo "[ OK  ] $cat/$name  <- $url"; echo "$cat/$name $url" >> "$OK"; return 0
      fi
      rm -rf "$target"; sleep $((try * 2))
    done
  done
  echo "[FAIL ] $cat/$name  ($*)"; echo "$cat/$name $*" >> "$FAIL"; return 1
}

# fetch_crate <crate> <kategori>  : unduh source crate dari crates.io (tanpa git)
fetch_crate() {
  local crate="$1" cat="$2" target ver ua="clone_all.sh (riset pribadi)"
  want "$cat" || return 0
  target="$DEST/$cat/$crate"
  if [ -d "$target" ]; then echo "[SKIP ] $cat/$crate (sudah ada)"; return 0; fi
  ver=$(curl -fsSL -A "$ua" "https://crates.io/api/v1/crates/$crate" 2>>"$LOG" \
        | grep -o '"max_version":"[^"]*"' | head -1 | cut -d'"' -f4)
  if [ -z "$ver" ]; then echo "[FAIL ] $cat/$crate (versi crate tidak ditemukan)"; echo "$cat/$crate crates.io" >> "$FAIL"; return 1; fi
  mkdir -p "$target"
  if curl -fsSL -A "$ua" "https://crates.io/api/v1/crates/$crate/$ver/download" 2>>"$LOG" \
       | tar -xz -C "$target" --strip-components=1 2>>"$LOG"; then
    echo "[ OK  ] $cat/$crate v$ver  <- crates.io"; echo "$cat/$crate v$ver" >> "$OK"
  else
    rm -rf "$target"; echo "[FAIL ] $cat/$crate"; echo "$cat/$crate crates.io" >> "$FAIL"; return 1
  fi
}

# kaggle_ds <slug> <folder> : butuh CLI kaggle + ~/.kaggle/kaggle.json
kaggle_ds() {
  local slug="$1" cat="05-dataset-model" name="$2"
  want "$cat" || return 0
  if [ -d "$DEST/$cat/$name" ]; then echo "[SKIP ] $cat/$name (sudah ada)"; return 0; fi
  if command -v kaggle >/dev/null 2>&1 && [ -f "$HOME/.kaggle/kaggle.json" ]; then
    mkdir -p "$DEST/$cat/$name"
    if kaggle datasets download -d "$slug" -p "$DEST/$cat/$name" --unzip >>"$LOG" 2>&1; then
      echo "[ OK  ] $cat/$name  <- kaggle:$slug"; echo "$cat/$name kaggle:$slug" >> "$OK"
    else
      echo "[FAIL ] $cat/$name (kaggle:$slug)"; echo "$cat/$name kaggle:$slug" >> "$FAIL"
    fi
  else
    echo "[MANUAL] $cat/$name -> pip install kaggle; simpan token di ~/.kaggle/kaggle.json; lalu:"
    echo "         kaggle datasets download -d $slug -p \"$DEST/$cat/$name\" --unzip"
    echo "$cat/$name kaggle:$slug (perlu kaggle CLI + token)" >> "$FAIL"
  fi
}

echo "Tujuan : $DEST"
echo "Mode   : ${DEPTH_OPT:-riwayat penuh}"
echo

# ---------------------------------------------------------------------------
# 01 Editor & proyek open-source (No. 1-15)
# ---------------------------------------------------------------------------
C=01-editor
clone $C tracedraw      https://github.com/igtoth/tracedraw.git
clone $C sk1-wx         https://github.com/sk1-project/sk1-wx.git
clone $C Graphite       https://github.com/GraphiteEditor/Graphite.git
clone $C vectorcraft    https://github.com/storytold/vectorcraft.git
clone $C svgedit        https://github.com/SVG-Edit/svgedit.git
clone $C penpot         https://github.com/penpot/penpot.git
clone $C inkscape       https://github.com/inkscape/inkscape.git https://gitlab.com/inkscape/inkscape.git
clone $C Method-Draw    https://github.com/methodofaction/Method-Draw.git
clone $C calligra       https://github.com/KDE/calligra.git https://invent.kde.org/office/calligra.git
clone $C repath-studio  https://github.com/repath-studio/repath-studio.git
clone $C suika          https://github.com/F-star/suika.git
clone $C Vectora        https://github.com/wieslawsoltes/Vectora.git
clone $C dotloom        https://github.com/TNYCL/dotloom.git
clone $C galago         https://github.com/Its-Just-Nans/galago.git
clone $C lazpaint       https://github.com/bgrabitmap/lazpaint.git

# ---------------------------------------------------------------------------
# 02 Parser & konversi CDR (No. 16-22)
# ---------------------------------------------------------------------------
C=02-parser-cdr
clone $C libcdr         https://git.libreoffice.org/libcdr https://github.com/LibreOffice/libcdr.git   # No. 16 + 18
clone $C pylibcdr       https://github.com/mpds-io/pylibcdr.git                                        # No. 17
clone $C go-libcdr      https://github.com/nobbs/go-libcdr.git                                         # No. 20
fetch_crate cdrsdk $C                                                                                   # No. 19 (butuh CorelDRAW + COM di Windows untuk dijalankan)
# No. 21 (paket Debian) : sumbernya sama dengan libcdr; opsional, butuh deb-src aktif:
#   apt-get source libcdr
# No. 22 (FreshPorts)   : hanya paket port FreeBSD untuk libcdr, tidak perlu di-clone.

# ---------------------------------------------------------------------------
# 03 Library & engine rendering SVG (No. 23-32)
# ---------------------------------------------------------------------------
C=03-render-svg
clone $C thorvg           https://github.com/thorvg/thorvg.git
clone $C tdewolff-canvas  https://github.com/tdewolff/canvas.git
clone $C two.js           https://github.com/jonobr1/two.js.git
clone $C svglab           https://github.com/reznakt/svglab.git
clone $C pave             https://github.com/baku89/pave.git
clone $C php-svg          https://codeberg.org/renfordt/php-svg.git
clone $C usvg             https://github.com/styluslabs/usvg.git
clone $C simple-svg       https://github.com/adishavit/simple-svg.git
clone $C GraphicsJS       https://github.com/AnyChart/GraphicsJS.git
clone $C vtracer          https://github.com/visioncortex/vtracer.git

# ---------------------------------------------------------------------------
# 04 API & layanan (No. 33-37)
# ---------------------------------------------------------------------------
C=04-api-layanan
clone $C svgl           https://github.com/pheralb/svgl.git
clone $C iconify        https://github.com/iconify/iconify.git
clone $C vectorforge    https://github.com/msitarzewski/vectorforge.git
clone $C grida-nothing  https://github.com/gridaco/nothing.git     # sesuai daftar (No. 36)
clone $C grida          https://github.com/gridaco/grida.git       # repo induk Grida Canvas (tambahan)
clone $C kotuku         https://github.com/kotuku-group/kotuku.git

# ---------------------------------------------------------------------------
# 05 Dataset & model AI (No. 38-43)
#   Repo Hugging Face di-clone TANPA file LFS (hanya pointer, ukuran kecil).
#   File aslinya (puluhan GB) diunduh terpisah, lihat catatan di bawah.
# ---------------------------------------------------------------------------
C=05-dataset-model
if [ "$WITH_HF" = "1" ]; then
  LFS_SKIP=1 clone $C text2svg-stack      https://huggingface.co/datasets/starvector/text2svg-stack
  LFS_SKIP=1 clone $C VectorEdits         https://huggingface.co/datasets/mikronai/VectorEdits
  LFS_SKIP=1 clone $C SVGThinker-7B       https://huggingface.co/Caffin/SVGThinker-7B
  LFS_SKIP=1 clone $C starvector-8b-im2svg https://huggingface.co/starvector/starvector-8b-im2svg
fi
kaggle_ds dushilong/svgdataset                       svgdataset-pixabay           # No. 39
kaggle_ds kaushikyh/svg-dataset-for-generative-llm   svg-icon-text2svg            # No. 41

# ---------------------------------------------------------------------------
# 06 Tool & utilitas (No. 44-47)
# ---------------------------------------------------------------------------
C=06-tools
clone $C scour      https://github.com/scour-project/scour.git
clone $C svgo       https://github.com/svg/svgo.git
clone $C oxvg       https://github.com/noahbald/oxvg.git           # repo asli (gwen-lg/oxvg hanya fork)
clone $C tiny-svg   https://github.com/hehehai/tiny-svg.git

# No. 48-50 (Inkscape Community, Graphic Design Stack Exchange, SVG Town Square)
# adalah forum, tidak bisa di-clone. Buka lewat browser.

echo
echo "================ RINGKASAN ================"
echo "Berhasil : $(grep -vc '^$' "$OK")   (daftar: $OK)"
if [ -s "$FAIL" ]; then
  echo "Gagal/manual : $(grep -vc '^$' "$FAIL")   (daftar: $FAIL)"; cat "$FAIL"
fi
echo "Ukuran total : $(du -sh "$DEST" 2>/dev/null | cut -f1)"
cat <<'EOF'

Catatan unduh file besar Hugging Face (opsional):
  pip install -U "huggingface_hub[cli]"
  huggingface-cli download starvector/text2svg-stack --repo-type dataset --local-dir <folder>
  huggingface-cli download starvector/starvector-8b-im2svg --local-dir <folder>   # model ~16 GB
  atau di dalam repo hasil clone:  git lfs install && git lfs pull

Jalankan ulang skrip ini kapan saja untuk mencoba lagi yang gagal.
EOF
