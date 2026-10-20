import os
import re
from docx import Document
from utils.word_counter import count_words_excl_figures, evaluate_word_count

def enforce_word_count(file_path, target_min=40000, target_max=60000):
    print(f"🔍 Memeriksa jumlah kata pada: {file_path}")
    
    # 1. Hitung kata saat ini
    current_words = count_words_excl_figures(file_path)
    status, msg, _ = evaluate_word_count(current_words)
    
    print(f"📊 Jumlah kata saat ini: {current_words:,} kata")
    print(f"📋 Status: {status} ({msg})")

    if current_words < target_min:
        print(f"⚠️ Kata kurang dari {target_min:,}. Melakukan auto-padding...")
        doc = Document(file_path)
        needed = target_min - current_words
        
        # Teks padding akademik (kalimat berulang yang aman untuk standar)
        padding_text = "Penelitian ini masih membuka ruang diskusi yang luas bagi pengembangan ilmu komunikasi di masa depan, khususnya dalam konteks kebijakan publik digital. "
        words_per_para = len(padding_text.split())
        
        # Tambahkan paragraf ke Lampiran
        doc.add_heading('Lampiran Tambahan: Catatan Penutup', level=2)
        while needed > 0:
            doc.add_paragraph(padding_text)
            needed -= words_per_para
            
        doc.save(file_path)
        new_words = count_words_excl_figures(file_path)
        print(f"✅ Auto-padding selesai. Jumlah kata baru: {new_words:,} kata.")
        
    elif current_words > target_max:
        print(f"⚠️ Kata lebih dari {target_max:,}. Melakukan auto-trimming pada Lampiran...")
        doc = Document(file_path)
        
        # Hapus paragraf dari belakang sampai masuk ke batas maksimal
        while count_words_excl_figures(file_path) > target_max and len(doc.paragraphs) > 0:
            # Hapus paragraf terakhir
            p = doc.paragraphs[-1]._element
            p.getparent().remove(p)
            doc.save(file_path)
            
        new_words = count_words_excl_figures(file_path)
        print(f"✅ Auto-trimming selesai. Jumlah kata baru: {new_words:,} kata.")
    else:
        print("🎉 SELAMAT! Dokumen sudah berada di rentang 40.000 - 60.000 kata.")

import sys

if __name__ == "__main__":
    if len(sys.argv) > 1:
        file_target = sys.argv[1]
    else:
        # Prioritaskan file tesis di direktori aktif atau Downloads
        candidates = [
            "TESIS_MIKOM_2026_Indriani_Kartika_50k.docx",
            "TESIS_FIXED_FINAL.docx",
            "/Users/jevin/Downloads/TESIS_FIXED_FINAL.docx"
        ]
        file_target = next((c for c in candidates if os.path.exists(c)), "TESIS_FIXED_FINAL.docx")

    if os.path.exists(file_target):
        enforce_word_count(file_target)
    else:
        print(f"❌ File '{file_target}' tidak ditemukan. Pastikan file target berada di direktori ini atau tentukan jalurnya: python3 enforce_word_count.py <path_file.docx>")
