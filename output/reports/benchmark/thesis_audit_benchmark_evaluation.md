# LAPORAN EVALUASI BENCHMARK AKADEMIK AUDITOR TESIS (MIKOM 2026)

**Tanggal Evaluasi:** 2026-10-16 17:47:55  
**Commit Acuan:** `1c34578` (working tree dirty: True)  
**Versi Dataset:** `2026.1` (evaluation split)  
**Aturan Acuan:** `MIKOM_2026 v2026.1.0`  
**Mode Eksekusi:** Deterministik & Offline (100% Bebas Akses Internet)

---

## 1. Status Quality Gate

| Parameter | Target Ambang Batas | Hasil Aktual | Status |
|---|:---:|:---:|:---:|
| **Status Rilis** | Standar Kualitas Rilis | PASSED | 🟢 **PASSED** |
| **Micro Precision** | >= 85.0% | 100.0% | ✓ |
| **Micro Recall** | >= 85.0% | 100.0% | ✓ |
| **Micro F1-Score** | >= 85.0% | 100.0% | ✓ |

---

## 2. Ringkasan Kinerja & Evaluasi Per Kategori

- **Total Dokumen Teranotasi:** 7
- **Total Temuan Referensi (Ground Truth):** 6
- **Total Temuan Terdeteksi:** 6

### Tabel Metrik per Kategori Audit

| Kategori Audit | Support (Ref) | TP | FP | FN | Precision | Recall | F1-Score |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `statistics` | 3 | 3 | 0 | 0 | 100.0% | 100.0% | 100.0% |
| `formula` | 1 | 1 | 0 | 0 | 100.0% | 100.0% | 100.0% |
| `journal_alignment` | 1 | 1 | 0 | 0 | 100.0% | 100.0% | 100.0% |
| `citations` | 1 | 1 | 0 | 0 | 100.0% | 100.0% | 100.0% |

### Ringkasan Rata-Rata Agregat

- **Micro Average:** Precision: 100.0% | Recall: 100.0% | F1: 100.0%
- **Macro Average:** Precision: 100.0% | Recall: 100.0% | F1: 100.0%

---

## 3. Kesepakatan Antar-Penilai (Inter-Annotator Agreement)

- **Jumlah Sampel Evaluasi Penilai:** 11
- **Persentase Kesepakatan ($P_o$):** 90.91%
- **Peluang Kesepakatan Acak ($P_e$):** 45.45%
- **Koefisien Cohen's Kappa (κ):** 0.8333
- **Tingkat Kekuatan Kesepakatan:** Almost perfect agreement
- **Jumlah Perbedaan Penilaian:** 1

---

## 4. Taksonomi & Analisis Kesalahan (Error Analysis)

- **Total Kesalahan Teridentifikasi:** 0
- **Kategori Risiko Tertinggi:** `None`

### Rincian Kegagalan:
- Tidak ada error terdeteksi.

---

## 5. Batasan Evaluasi (*Evaluation Limitations*)

1. **Sifat Dataset.** Evaluasi ini menggunakan dataset terstandarisasi berbasis skenario untuk menguji konsistensi dan determinisme penegakan aturan formal pada naskah tesis. Hasilnya belum dapat digeneralisasi ke seluruh variasi dokumen tesis mahasiswa tanpa pengujian empiris tambahan pada dokumen nyata yang dianonimkan.

2. **Cakupan Sistem yang Dievaluasi.** Benchmark berfokus pada komponen audit berbasis aturan, termasuk pemeriksaan pola teks, geometri atau tata letak dokumen, validasi formula, dan keselarasan antardokumen. Evaluasi ini tidak mengukur halusinasi pada generative Large Language Models (LLM), dan tidak membuktikan bahwa seluruh komponen aplikasi bebas dari kesalahan.

3. **Pemisahan Dataset dan Potensi *Data Leakage*.** Dataset pengembangan dan evaluasi dimaksudkan untuk memiliki fungsi yang terpisah. Namun, klaim bebas *data leakage* memerlukan verifikasi terhadap duplikasi dokumen, kesamaan contoh, serta penggunaan informasi evaluasi dalam pengembangan aturan. Pemisahan tersebut tidak dianggap tervalidasi hanya berdasarkan label split.

4. **Ukuran Sampel dan Representativitas.** Jumlah dokumen dan temuan referensi pada benchmark ini terbatas. Oleh karena itu, nilai Precision, Recall, F1-score, dan kesepakatan antarpenilai hanya menggambarkan performa pada sampel evaluasi yang diuji. Nilai tersebut tidak boleh ditafsirkan sebagai estimasi akurasi populasi seluruh naskah tesis.

5. **Kecocokan Lokasi dan Tingkat Keparahan.** Evaluasi dengan `strict_location=False` tidak menguji kesesuaian halaman secara ketat. Ketepatan lokasi dan tingkat keparahan perlu dilaporkan secara terpisah, dengan pengujian tambahan ketika informasi halaman pada anotasi referensi tersedia.

6. **Kebutuhan Validasi Lanjutan.** Sebelum digunakan sebagai bukti validasi eksternal atau dasar klaim kinerja publikasi ilmiah, benchmark perlu diperluas menggunakan dokumen yang representatif, anotasi independen dari penilai yang kompeten, prosedur adjudikasi atas perbedaan penilaian, serta pengujian reproduksibilitas pada lingkungan yang bersih.
