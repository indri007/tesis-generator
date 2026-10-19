"""scripts/fix_tesis_typos_metadata.py - Auto-Fix Typo, Metadata, DOI, and Table Repeat Header for Thesis."""
import os
import re
import sys
from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn


def replace_text_safely(paragraph, old_text, new_text):
    """Mengganti teks dengan mempertahankan format run (bold/italic/font) jika memungkinkan."""
    if old_text not in paragraph.text:
        return False
        
    replaced = False
    # Coba ganti di level run terlebih dahulu agar styling font/bold tidak hilang
    for r in paragraph.runs:
        if old_text in r.text:
            r.text = r.text.replace(old_text, new_text)
            replaced = True
            
    # Jika kata kunci terpecah di antara 2 run berbeda, lakukan fallback ke p.text
    if not replaced and old_text in paragraph.text:
        paragraph.text = paragraph.text.replace(old_text, new_text)
        replaced = True
        
    return replaced


def fix_typos_and_metadata(input_path: str, output_path: str):
    print(f"🚀 Memulai Auto-Fix Tesis: {input_path}")
    if not os.path.exists(input_path):
        print(f"❌ Berkas tidak ditemukan: {input_path}")
        return False

    doc = Document(input_path)

    # ─────────────────────────────────────────────
    # 1. KAMUS PERBAIKAN TEKS (Typo & Metadata)
    # ─────────────────────────────────────────────
    replacements = {
        # Typo Umum
        "Opin Public Daring": "Opini Publik Daring",
        "Ketiodaan": "Ketiadaan",
        "hutan hasil scraping": "cuitan hasil scraping",
        "memorialisasi slang": "menormalisasi slang",
        "diperlukankan": "diperlakukan",
        
        # Konsistensi Nama Penulis (Teks vs Daftar Pustaka)
        "Triningsih et al.": "Trinningsih et al.",
        "Fatkhurrohman et al.": "Fathkurrohman et al.",
        "Hasyim (2026)": "Hasvim (2026)",
        "Ihdahayuningsi h": "Ihdahayuningsih",
        
        # Perbaikan Nomor Halaman Manual "5.9" menjadi "59"
        " 5.9 \n": " 59 \n",
        " 5.9\n": " 59\n",
        " 5.9 ": " 59 ",
    }

    typo_count = 0
    # Lakukan penggantian di seluruh paragraf
    for p_idx, p in enumerate(doc.paragraphs):
        for old_text, new_text in replacements.items():
            if replace_text_safely(p, old_text, new_text):
                typo_count += 1
                print(f"✅ [Paragraf {p_idx+1}] Teks diperbaiki: '{old_text}' -> '{new_text}'")

    # Lakukan penggantian di dalam tabel
    table_cell_typos = 0
    for t_idx, table in enumerate(doc.tables):
        for r_idx, row in enumerate(table.rows):
            for c_idx, cell in enumerate(row.cells):
                for p in cell.paragraphs:
                    for old_text, new_text in replacements.items():
                        if replace_text_safely(p, old_text, new_text):
                            table_cell_typos += 1
                            print(f"✅ [Tabel {t_idx+1} R{r_idx+1}C{c_idx+1}] Teks diperbaiki: '{old_text}' -> '{new_text}'")

    # ─────────────────────────────────────────────
    # 2. PERBAIKAN DOI (Menghapus Spasi Terputus di Tabel)
    # ─────────────────────────────────────────────
    doi_fixed_count = 0
    doi_pattern = re.compile(r'(10\.\d{4,9}/[^\s]+)\s+([^\s]+)')
    for t_idx, table in enumerate(doc.tables):
        for r_idx, row in enumerate(table.rows):
            for c_idx, cell in enumerate(row.cells):
                if "10." in cell.text:
                    orig_text = cell.text
                    new_text = doi_pattern.sub(r'\1\2', orig_text)
                    if new_text != orig_text:
                        # Terapkan ke paragraf pertama cell
                        if cell.paragraphs:
                            cell.paragraphs[0].text = new_text
                            # Hapus paragraf berlebih di sel jika ada
                            for extra_p in cell.paragraphs[1:]:
                                extra_p.text = ""
                        else:
                            cell.text = new_text
                        doi_fixed_count += 1
                        print(f"✅ [Tabel {t_idx+1} DOI Dirapikan]: {new_text.strip()[:40]}...")

    # ─────────────────────────────────────────────
    # 3. PENGATURAN TABEL OTOMATIS (Repeat Header di Tiap Halaman Baru)
    # ─────────────────────────────────────────────
    header_repeat_count = 0
    for i, table in enumerate(doc.tables):
        # Jika tabel memiliki lebih dari 5 baris (seperti Tabel 4.1, Tabel Hasil Analisis, dll.)
        if len(table.rows) > 5:
            tr = table.rows[0]._tr
            trPr = tr.get_or_add_trPr()
            
            # Cek apakah sudah ada tblHeader
            if trPr.find(qn('w:tblHeader')) is None:
                tblHeader = OxmlElement('w:tblHeader')
                tblHeader.set(qn('w:val'), "true")
                trPr.append(tblHeader)
                header_repeat_count += 1
                print(f"✅ Tabel ke-{i+1} ({len(table.rows)} baris) diatur agar Header berulang otomatis di setiap halaman baru.")

            # Mencegah baris tabel terpotong terbelah canggung antar halaman (cantSplit)
            for row in table.rows:
                r_trPr = row._tr.get_or_add_trPr()
                if r_trPr.find(qn('w:cantSplit')) is None:
                    cantSplit = OxmlElement('w:cantSplit')
                    cantSplit.set(qn('w:val'), "true")
                    r_trPr.append(cantSplit)

    # Simpan dokumen output
    doc.save(output_path)
    print(f"\n🎉 Selesai! Berkas berhasil diperbaiki dan disimpan sebagai:\n   👉 {output_path}")
    print(f"📊 Ringkasan Eksekusi:")
    print(f"   - Typo/Metadata di Paragraf Diperbaiki: {typo_count}")
    print(f"   - Typo/Metadata di Sel Tabel Diperbaiki: {table_cell_typos}")
    print(f"   - DOI Rusak/Spasi Terputus Dirapikan   : {doi_fixed_count}")
    print(f"   - Tabel Panjang dengan Repeat Header  : {header_repeat_count}")
    print("\n⚠️ CATATAN MANUAL:")
    print("   1. Penomoran ganda di Bab V (Hal 154): Periksa nomor sub-bab manual.")
    print("   2. Paragraf panjang (Hal 132): Pisahkan menjadi 2 paragraf di Word.")
    print("   3. Gambar Dark Mode (Lampiran 5): Ganti dengan latar putih bersih untuk cetak formal.")
    return True


if __name__ == "__main__":
    default_input = "/Users/jevin/Downloads/revised_revised_revised_tesis2_revisi.docx"
    default_output = "/Users/jevin/Downloads/TESIS_FIXED_FINAL.docx"

    in_file = sys.argv[1] if len(sys.argv) > 1 else default_input
    out_file = sys.argv[2] if len(sys.argv) > 2 else default_output

    fix_typos_and_metadata(in_file, out_file)
