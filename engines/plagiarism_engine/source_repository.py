from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)

# Sample baseline corpus for academic thesis evaluation in Indonesian communication science
DEFAULT_ACADEMIC_CORPUS = [
    "Komunikasi massa adalah proses di mana organisasi media memproduksi dan mentransmisikan pesan kepada khalayak luas.",
    "Metode penelitian kualitatif berfokus pada pemahaman fenomena sosial dari perspektif partisipan melalui wawancara mendalam.",
    "Uji validitas dan reliabilitas instrumen dilakukan untuk memastikan kuesioner penelitian memiliki konsistensi internal.",
    "Analisis regresi linear berganda digunakan untuk menguji pengaruh variabel independen terhadap variabel dependen.",
    "Teori agenda setting menyatakan bahwa media massa memiliki kemampuan untuk mentransfer isu prioritas ke dalam agenda publik.",
    "Komunikasi organisasi mencakup struktur hierarkis, arus informasi vertikal dan horizontal, serta iklim komunikasi institusional.",
]


class SourceRepository:
    """Manajemen korpus pembanding dokumen akademik untuk audit plagiarisme."""

    def __init__(self, initial_corpus: Optional[List[str]] = None):
        self.corpus: List[str] = list(initial_corpus) if initial_corpus else list(DEFAULT_ACADEMIC_CORPUS)

    def add_document(self, text: str) -> None:
        """Menambahkan teks dokumen ke dalam korpus pembanding."""
        if text and text.strip():
            self.corpus.append(text.strip())

    def add_from_file(self, file_path: str | Path) -> None:
        """Membaca berkas teks dan menambahkannya ke korpus."""
        p = Path(file_path)
        if p.exists() and p.is_file():
            try:
                content = p.read_text(encoding="utf-8")
                self.add_document(content)
            except Exception as e:
                logger.warning("Gagal membaca dokumen sumber %s: %s", p, e)

    def load_from_directory(self, dir_path: str | Path) -> int:
        """Memuat semua berkas teks (.txt, .md) dari direktori."""
        d = Path(dir_path)
        count = 0
        if d.exists() and d.is_dir():
            for f in d.glob("*.*"):
                if f.suffix.lower() in [".txt", ".md"]:
                    self.add_from_file(f)
                    count += 1
        return count

    def get_all(self) -> List[str]:
        """Mengambil seluruh korpus pembanding."""
        return list(self.corpus)

    def clear(self) -> None:
        """Mengosongkan korpus pembanding."""
        self.corpus.clear()


def build_corpus_from_citations(
    scopus_client: Any,
    citations: list[dict[str, Any]],
    max_papers: int = 50,
) -> list[str]:
    """Ambil abstrak dari Scopus untuk setiap sitasi, jadikan korpus pembanding."""
    from core.mcp_client import run_async

    corpus = []
    for cite in citations[:max_papers]:
        doi = cite.get("doi")
        if not doi:
            continue
        try:
            detail = run_async(scopus_client.get_scopus_abstract(doi))
            abstract_data = detail.get("abstract")
            if isinstance(abstract_data, dict) and abstract_data.get("title"):
                corpus.append(abstract_data.get("title", ""))
            elif isinstance(abstract_data, str) and abstract_data:
                corpus.append(abstract_data)
        except Exception as e:
            logger.debug("Failed to retrieve Scopus abstract for DOI %s: %s", doi, e)
    return corpus
