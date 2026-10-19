#!/usr/bin/env bash
# ============================================================================
# re_cdr.sh : perkakas riset format berkas CorelDRAW (.cdr) untuk interoperabilitas,
# berbasis libcdr (parser open-source hasil analisis format, lisensi MPL 2.0).
# Pakailah pada berkas .cdr milik sendiri.
#
# Pemakaian:
#   ./re_cdr.sh deps            pasang dependensi build (Debian/Ubuntu)
#   ./re_cdr.sh build           build + install libcdr dari hasil clone_all.sh
#   ./re_cdr.sh pylibcdr        pasang binding Python (pylibcdr)
#   ./re_cdr.sh inspect F.cdr   struktur berkas: wadah (ZIP/RIFF), header, daftar chunk
#   ./re_cdr.sh convert F.cdr   keluarkan .xhtml (SVG per halaman), dump raw, dump teks
#
# Variabel: DEST (default ~/corel-clone-refs), PREFIX (default ~/.local)
# ============================================================================
set -e
DEST="${DEST:-$HOME/corel-clone-refs}"
PREFIX="${PREFIX:-$HOME/.local}"
LIBCDR="$DEST/02-parser-cdr/libcdr"
PYLIBCDR="$DEST/02-parser-cdr/pylibcdr"

export PATH="$PREFIX/bin:$PATH"
export PKG_CONFIG_PATH="$PREFIX/lib/pkgconfig:${PKG_CONFIG_PATH:-}"
export LD_LIBRARY_PATH="$PREFIX/lib:${LD_LIBRARY_PATH:-}"

cmd="${1:-help}"; f="${2:-}"

case "$cmd" in
  deps)
    sudo apt-get update
    sudo apt-get install -y build-essential automake libtool pkg-config cmake \
      libboost-all-dev libicu-dev liblcms2-dev librevenge-dev libcppunit-dev zlib1g-dev \
      python3-dev python3-pip cython3 unzip xxd binutils
    # opsional untuk analisis biner: sudo apt-get install -y binwalk
    ;;

  build)
    [ -d "$LIBCDR" ] || { echo "libcdr belum ada. Jalankan dulu: ./clone_all.sh"; exit 1; }
    # perlu clone dengan riwayat/tag jika ingin versi tertentu: FULL=1 ./clone_all.sh
    cd "$LIBCDR"
    ./autogen.sh
    ./configure --prefix="$PREFIX"          # tools (cdr2xhtml, cdr2raw, cdr2text, cmx2*) aktif secara default
    make -j"$(nproc 2>/dev/null || echo 2)"
    make install
    echo "Selesai. Tool ada di: $PREFIX/bin  (cdr2xhtml cdr2raw cdr2text cmx2xhtml cmx2raw cmx2text)"
    echo "Tambahkan ke shell:   export PATH=$PREFIX/bin:\$PATH LD_LIBRARY_PATH=$PREFIX/lib:\$LD_LIBRARY_PATH"
    ;;

  pylibcdr)
    [ -d "$PYLIBCDR" ] || { echo "pylibcdr belum ada. Jalankan dulu: ./clone_all.sh"; exit 1; }
    # butuh libcdr > v0.1.8 sudah ter-install (./re_cdr.sh build). Disarankan di dalam venv.
    python3 -m pip install "$PYLIBCDR"
    echo 'Uji:  python3 -c "from pylibcdr import CDRParser; p=CDRParser(\"file.cdr\"); print(p.xml[:500])"'
    ;;

  inspect)
    [ -f "$f" ] || { echo "Pakai: $0 inspect berkas.cdr"; exit 1; }
    echo "== file / ukuran";  file "$f"; ls -l "$f"
    echo "== 64 byte pertama"; xxd -l 64 "$f"
    echo "== string menarik (20 pertama, panjang >= 8)"; strings -n 8 "$f" | head -20 || true
    echo "== wadah"
    if unzip -tq "$f" >/dev/null 2>&1; then
      echo "ZIP (CorelDRAW X4 ke atas): isi arsip"; unzip -l "$f"
    else
      echo "Bukan ZIP: kemungkinan RIFF langsung (format lama)."
    fi
    echo "== struktur chunk RIFF"
    python3 - "$f" <<'PY'
import sys, struct, zipfile, io
data = open(sys.argv[1], 'rb').read()
if data[:2] == b'PK':
    z = zipfile.ZipFile(io.BytesIO(data))
    names = z.namelist()
    cand = [n for n in names if n.lower().endswith('riffdata.cdr')] or [n for n in names if n.lower().endswith('.cdr')]
    if not cand:
        print("Tidak ada riffData.cdr di dalam ZIP. Entri:", names[:30]); sys.exit()
    print("RIFF diambil dari entri ZIP:", cand[0])
    data = z.read(cand[0])
if data[:4] != b'RIFF':
    print("Bukan RIFF. 16 byte awal (hex):", data[:16].hex()); sys.exit()
lines = []
def walk(buf, off, end, depth):
    while off + 8 <= end and depth < 3 and len(lines) < 200:
        cc = buf[off:off+4]; sz = struct.unpack('<I', buf[off+4:off+8])[0]
        label = cc.decode('latin1')
        if cc in (b'RIFF', b'LIST') and off + 12 <= end:
            sub = buf[off+8:off+12].decode('latin1')
            lines.append('  ' * depth + f'{label} <{sub}> size={sz}')
            walk(buf, off + 12, min(off + 8 + sz, end), depth + 1)
        else:
            lines.append('  ' * depth + f'{label} size={sz}')
        off += 8 + sz + (sz & 1)
walk(data, 0, len(data), 0)
print("\n".join(lines))
if len(lines) >= 200: print("... (dipotong 200 baris)")
PY
    ;;

  convert)
    [ -f "$f" ] || { echo "Pakai: $0 convert berkas.cdr"; exit 1; }
    for t in cdr2xhtml cdr2raw cdr2text; do
      command -v "$t" >/dev/null 2>&1 || { echo "$t tidak ditemukan. Jalankan: ./re_cdr.sh build"; exit 1; }
    done
    base="${f%.*}"
    cdr2xhtml "$f" > "$base.xhtml"      # XHTML berisi SVG per halaman
    cdr2raw   "$f" > "$base.raw.txt"    # dump panggilan generator (urutan perintah gambar)
    cdr2text  "$f" > "$base.txt"        # teks yang ada di dokumen
    echo "Dihasilkan: $base.xhtml  $base.raw.txt  $base.txt"
    ;;

  *)
    sed -n '2,17p' "$0"
    ;;
esac
