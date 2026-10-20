from docx import Document
import re
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

def replace_text_safely(paragraph, old_text, new_text):
    """Mengganti teks dengan mempertahankan formatting run (bold/italic) jika memungkinkan."""
    if old_text not in paragraph.text:
        return False
    replaced = False
    for r in paragraph.runs:
        if old_text in r.text:
            r.text = r.text.replace(old_text, new_text)
            replaced = True
    if not replaced and old_text in paragraph.text:
        paragraph.text = paragraph.text.replace(old_text, new_text)
        replaced = True
    return replaced

def fix_document(input_path, output_path):
    print(f"🚀 Memperbaiki dokumen: {input_path}")
    doc = Document(input_path)

    # 1. Perbaikan Typo & Metadata (Berdasarkan temuan audit)
    replacements = {
        "Opin Public Daring": "Opini Publik Daring",
        "Ketiodaan": "Ketiadaan",
        "hutan hasil scraping": "cuitan hasil scraping",
        "memorialisasi slang": "menormalisasi slang",
        "diperlukankan": "diperlakukan",
        "Triningsih et al.": "Trinningsih et al.",
        "Fatkhurrohman et al.": "Fathkurrohman et al.",
        "Hasyim (2026)": "Hasvim (2026)",
        "Ihdahayuningsi h": "Ihdahayuningsih",
        " 5.9 \n": " 59 \n" 
    }

    # Eksekusi penggantian teks di paragraf
    for p in doc.paragraphs:
        for old_text, new_text in replacements.items():
            if old_text in p.text:
                replace_text_safely(p, old_text, new_text)
                print(f"✅ Teks diperbaiki: '{old_text}' -> '{new_text}'")

    # Eksekusi penggantian teks di dalam tabel
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    for old_text, new_text in replacements.items():
                        if old_text in p.text:
                            replace_text_safely(p, old_text, new_text)

    # 2. Perbaikan DOI yang terputus spasi (di Tabel 4.1)
    doi_pattern = re.compile(r'(10\.\d{4,9}/[^\s]+)\s+([^\s]+)')
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                if "10." in cell.text:
                    new_text = doi_pattern.sub(r'\1\2', cell.text)
                    if new_text != cell.text:
                        for p in cell.paragraphs:
                            if "10." in p.text:
                                p.text = doi_pattern.sub(r'\1\2', p.text)

    # 3. Pengaturan Tabel (Repeat Header Row & CantSplit)
    for i, table in enumerate(doc.tables):
        if len(table.rows) > 5:
            tr = table.rows[0]._tr
            trPr = tr.get_or_add_trPr()
            if trPr.find(qn('w:tblHeader')) is None:
                tblHeader = OxmlElement('w:tblHeader')
                tblHeader.set(qn('w:val'), "true")
                trPr.append(tblHeader)
            # Cegah baris tabel terpotong terbelah canggung antar halaman
            for row in table.rows:
                r_trPr = row._tr.get_or_add_trPr()
                if r_trPr.find(qn('w:cantSplit')) is None:
                    cantSplit = OxmlElement('w:cantSplit')
                    cantSplit.set(qn('w:val'), "true")
                    r_trPr.append(cantSplit)
            print(f"✅ Tabel ke-{i+1} diatur agar Header berulang dan baris tidak terbelah di halaman baru.")

    doc.save(output_path)
    print(f"\n🎉 Selesai! File tersimpan sebagai: {output_path}")

if __name__ == "__main__":
    fix_document("TESIS_MIKOM_2026_Indriani_Kartika_50k.docx", "TESIS_FINAL_SIAP_SIDANG.docx")
