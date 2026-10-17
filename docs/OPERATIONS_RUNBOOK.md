# SRE Operations Runbook & Post-Deployment Validation

**Application:** TesisCheck MIKOM 2026 (AI-Thesis-Generator)
**Environment:** Local Workspace Runtime / Staging
**Service Type:** Streamlit Web Application (Port 8501) with Pure-Python Lexical Similarity & SQLite WAL
**Status:** OPERATIONALLY VERIFIED (Local Runtime) / NOT DEPLOYED (External Production)

---

## 1. Verifikasi Identitas & Status Deployment

| Parameter | Nilai Terverifikasi | Metode Verifikasi |
| :--- | :--- | :--- |
| **Git Branch** | `main` | `git status --short --branch` |
| **Active Commit** | `aa8bc2e` (atau commit HEAD terbaru) | `git log -1 --oneline` |
| **Python Runtime** | Python 3.11.15 (`.venv-test`) | `.venv-test/bin/python3 --version` |
| **Hosting Target** | Local Staging Server (`http://localhost:8501`) | Native Streamlit daemon |
| **Production Cloud** | Belum Terpasang (Tidak ada manifest AWS/GCP/Fly di repo) | Audit repository (`.github/workflows/ci.yml`) |

---

## 2. Prosedur Health Check

### A. HTTP Liveness & Readiness Endpoint
Streamlit menyediakan endpoint health check bawaan yang dapat dipantau oleh load balancer atau health monitor lokal:
```bash
curl -i -s http://localhost:8501/_stcore/health
```
**Ekspektasi Output:**
```http
HTTP/1.1 200 OK
content-type: text/plain

ok
```

### B. Health Check Komponen Internal (Engine & Database)
Jalankan verifikasi cepat untuk memastikan SQLite WAL mode dan Similarity Engine siap melayani naskah:
```bash
.venv-test/bin/python3 -c '
import urllib.request
from engines.similarity_auditor import run_similarity_analysis
from core.database.db_manager import DatabaseManager

# 1. Web Endpoint
with urllib.request.urlopen("http://localhost:8501/_stcore/health", timeout=3) as res:
    assert res.status == 200 and res.read().decode().strip() == "ok"

# 2. Similarity Engine
res = run_similarity_analysis("komunikasi massa", "komunikasi publik")
assert 0.0 <= res.cosine_similarity <= 1.0

# 3. Database SQLite WAL
db = DatabaseManager()
with db.get_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("PRAGMA journal_mode;")
    assert cursor.fetchone()[0].lower() == "wal"

print("✅ ALL HEALTH CHECKS OK")
'
```

---

## 3. Skrip Smoke Test End-to-End

Untuk memverifikasi seluruh alur operasional (Ekstraksi teks, Komputasi similarity, Ekspor ringkasan tanpa membocorkan naskah, dan Integrasi DB):
```bash
# Jalankan smoke test terotomatisasi
.venv-test/bin/pytest tests/unit/test_similarity_auditor.py -v
```

---

## 4. Lokasi Log & Aturan Redaksi Privasi

- **Lokasi Log Server:** Output standar konsol Streamlit atau file log task Antigravity IDE (`logs/` dan `.system_generated/tasks/`).
- **Aturan Redaksi Data (Privacy & Data Governance):**
  1. **Dilarang Mencatat Isi Naskah:** Log hanya boleh mencatat nama dokumen (`uploaded_filename`), ukuran berkas dalam byte, dan kode status (sukses/gagal). Isi teks naskah *tidak boleh* ditulis ke log.
  2. **Dilarang Mencatat Kredensial:** Parameter otentikasi atau variabel lingkungan tidak boleh dicetak.
  3. **Penghapusan File Sementara:** Berkas unggahan diproses di dalam `tempfile.TemporaryDirectory()` dan langsung dimusnahkan setelah ekstraksi teks selesai.

---

## 5. Diagnosis Masalah Umum (Troubleshooting)

### A. Port Conflict (Port 8501 Sedang Digunakan)
- **Gejala:** `OSError: [Errno 48] Address already in use` saat menjalankan `make run`.
- **Investigasi:**
  ```bash
  lsof -i :8501
  ```
- **Penanganan:**
  Jalankan aplikasi di port alternatif jika port 8501 digunakan oleh proses lain:
  ```bash
  .venv-test/bin/streamlit run app.py --server.port 8502
  ```

### B. Berkas Korup / Gagal Ekstraksi PDF/DOCX
- **Gejala:** Pesan UI `Gagal memproses Dokumen: ...`.
- **Penyebab:** Berkas dilindungi sandi, header berkas tidak valid, atau format biner korup.
- **Tindakan:** Pastikan berkas dapat dibuka di Microsoft Word / Adobe Reader lokal sebelum diunggah kembali.

---

## 6. Prosedur Respons Insiden (Incident Response Runbook)

| Tingkat Keparahan | Kriteria | Tindakan Segera |
| :--- | :--- | :--- |
| **SEV-1 (Kritis)** | Server down, kebocoran data draft antar-sesi, korupsi database SQLite. | 1. Hentikan proses Streamlit (`pkill -f streamlit`).<br>2. Periksa integritas file DB (`sqlite3 workspace/tesis_check.db "PRAGMA integrity_check;"`).<br>3. Restart aplikasi. |
| **SEV-2 (Tinggi)** | Fungsi ekspor PDF/DOCX gagal, atau parsing berkas memicu exception berulang. | 1. Periksa ketersediaan library `python-docx` / `fitz`.<br>2. Validasi ruang disk (`df -h`). |
| **SEV-3 (Rendah)** | Masalah visual CSS, kesalahan tampilan minor pada tab. | Jadwalkan perbaikan non-darurat pada jam kerja berikutnya. |

---

## 7. Prosedur Rollback Aman (Safe Rollback)

Jika versi terkini mengalami anomali dan memerlukan pengembalian versi:
1. **Dilarang Menggunakan `git reset --hard`** secara sembarangan agar tidak memusnahkan draf tesis atau modifikasi lokal yang sedang aktif.
2. **Identifikasi Commit Sehat Terakhir:**
   ```bash
   git log -n 5 --oneline
   ```
3. **Checkout/Revert Secara Terkontrol:**
   ```bash
   # Mengembalikan perubahan pada file tertentu tanpa merusak tree:
   git checkout <commit-hash> -- <file_path>
   ```
4. **Verifikasi Ulang Setelah Rollback:**
   ```bash
   make test && make lint
   ```

---

## 8. Keterbatasan Pemantauan (Known Monitoring Gaps)

- **Tidak Ada APM Cloud Eksternal:** Aplikasi secara sengaja tidak memasang agen APM SaaS (seperti Datadog atau New Relic) untuk menjamin naskah riset akademik tidak keluar dari perimeter lokal/institusi.
- **Metrik Beban:** Pengukuran performa saat ini berbasis proses lokal Python. Jika nantinya di-deploy ke cluster multi-user, reverse proxy (Nginx / Traefik) direkomendasikan untuk membatasi *rate limiting* dan *TLS termination*.
