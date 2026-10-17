# scripts/process_metadata.py
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

RAW_DIR = Path("data/raw")
PROCESSED_FILE = Path("data/processed/clean_references.jsonl")


def clean_html_tags(text: str) -> str:
    """Hapus tag HTML seperti <i>, <b>, dll."""
    return re.sub(r"<[^>]+>", "", text).strip()


def normalize_doi(doi: Optional[str]) -> Optional[str]:
    """Normalisasi format DOI ke format standar (10.xxxx/yyyy)."""
    if not doi:
        return None
    doi = doi.strip().lower()
    doi = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", doi)
    doi = re.sub(r"^doi:\s*", "", doi)
    return doi if "/" in doi else None


def format_author_list(raw_authors: List[Any]) -> List[str]:
    """Format daftar nama pengarang ke standar 'Belakang, Depan'."""
    formatted = []
    for author in raw_authors:
        if isinstance(author, dict):
            family = author.get("family", "") or author.get("last_name", "")
            given = author.get("given", "") or author.get("first_name", "")
            if family and given:
                formatted.append(f"{family}, {given}")
            elif family:
                formatted.append(family)
            elif author.get("name"):
                formatted.append(author["name"])
        elif isinstance(author, str) and author.strip():
            formatted.append(author.strip())
    return formatted


def extract_year(published: Any) -> Optional[int]:
    """Ekstraksi tahun terbit dari berbagai format metadata."""
    if not published:
        return None
    if isinstance(published, int):
        return published if 1900 <= published <= 2030 else None
    if isinstance(published, dict):
        date_parts = published.get("date-parts")
        if date_parts and isinstance(date_parts, list) and len(date_parts) > 0:
            first_part = date_parts[0]
            if isinstance(first_part, list) and len(first_part) > 0:
                try:
                    yr = int(first_part[0])
                    if 1900 <= yr <= 2030:
                        return yr
                except (ValueError, TypeError):
                    pass
    if isinstance(published, str):
        match = re.search(r"\b(19\d\d|20\d\d)\b", published)
        if match:
            return int(match.group(1))
    return None


def process_all_raw_metadata() -> Dict[str, int]:
    PROCESSED_FILE.parent.mkdir(parents=True, exist_ok=True)
    seen_dois = set()
    seen_titles = set()
    total_raw = 0
    unique_saved = 0

    raw_files = list(RAW_DIR.glob("*.jsonl"))
    if not raw_files:
        print(f"Tidak ada file .jsonl di {RAW_DIR}")
        return {"total_raw": 0, "unique_saved": 0}

    with PROCESSED_FILE.open("w", encoding="utf-8") as out_f:
        for fpath in raw_files:
            print(f"Memproses file: {fpath}")
            with fpath.open("r", encoding="utf-8") as in_f:
                for line in in_f:
                    line = line.strip()
                    if not line:
                        continue
                    total_raw += 1
                    try:
                        record = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    doi = normalize_doi(record.get("doi"))
                    title_raw = record.get("title")
                    title = ""
                    if isinstance(title_raw, list) and len(title_raw) > 0:
                        title = clean_html_tags(str(title_raw[0]))
                    elif isinstance(title_raw, str):
                        title = clean_html_tags(title_raw)

                    # Deduplikasi: periksa DOI atau judul
                    norm_title_key = re.sub(r"[^\w\s]", "", title.lower()).strip()
                    if doi and doi in seen_dois:
                        continue
                    if not doi and norm_title_key and norm_title_key in seen_titles:
                        continue

                    if doi:
                        seen_dois.add(doi)
                    if norm_title_key:
                        seen_titles.add(norm_title_key)

                    authors = format_author_list(record.get("authors", []))
                    year = extract_year(record.get("published") or record.get("year"))

                    journal_raw = record.get("journal")
                    journal = ""
                    if isinstance(journal_raw, list) and len(journal_raw) > 0:
                        journal = clean_html_tags(str(journal_raw[0]))
                    elif isinstance(journal_raw, str):
                        journal = clean_html_tags(journal_raw)

                    clean_record = {
                        "doi": doi,
                        "title": title,
                        "authors": authors,
                        "year": year,
                        "journal": journal,
                        "source": record.get("source", "Unknown"),
                        "url": record.get("url") or (f"https://doi.org/{doi}" if doi else ""),
                    }

                    out_f.write(json.dumps(clean_record, ensure_ascii=False) + "\n")
                    unique_saved += 1

    print("\n=== RINGKASAN PEMROSESAN METADATA ===")
    print(f"Total entri mentah dibaca : {total_raw}")
    print(f"Total unik tersimpan      : {unique_saved}")
    print(f"File output               : {PROCESSED_FILE}")
    return {"total_raw": total_raw, "unique_saved": unique_saved}


if __name__ == "__main__":
    process_all_raw_metadata()
