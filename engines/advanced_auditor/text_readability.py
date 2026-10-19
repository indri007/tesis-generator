import re
from docx import Document

class TextReadabilityAuditor:
    def __init__(self, max_words=150, max_sentences=6):
        self.max_words = max_words
        self.max_sentences = max_sentences

    def audit(self, docx_path):
        doc = Document(docx_path)
        findings = []
        
        for i, para in enumerate(doc.paragraphs):
            text = para.text.strip()
            # Abaikan paragraf pendek, heading, atau caption
            if len(text) < 100 or text.lower().startswith(('tabel', 'gambar', 'sumber')):
                continue
                
            word_count = len(text.split())
            # Split kalimat berdasarkan tanda titik, tanya, seru
            sentences = [s for s in re.split(r'[.!?]+', text) if s.strip()]
            sentence_count = len(sentences)

            if word_count > self.max_words or sentence_count > self.max_sentences:
                findings.append({
                    "type": "WALL_OF_TEXT",
                    "paragraph_index": i,
                    "word_count": word_count,
                    "sentence_count": sentence_count,
                    "snippet": text[:100] + "...",
                    "message": f"Paragraf terlalu panjang ({word_count} kata, {sentence_count} kalimat). Pecah menjadi 2-3 paragraf."
                })
        return findings
