# scripts/collect_openalex.py
import json
import time
from pathlib import Path
import requests

OUT = Path("data/raw/openalex_metadata.jsonl")
OUT.parent.mkdir(parents=True, exist_ok=True)

QUERIES = [
    "communication studies",
    "social media communication",
    "political communication Indonesia",
    "interpersonal communication",
    "media literacy digital",
]

BASE_URL = "https://api.openalex.org/works"
HEADERS = {
    "User-Agent": (
        "TesisCheckMIKOM/1.0 "
        "(mailto:research-mikom@upnjatim.ac.id)"
    )
}


def main():
    count = 0
    with OUT.open("a", encoding="utf-8") as output:
        for query in QUERIES:
            params = {
                "search": query,
                "per-page": 50,
                "filter": "type:article",
            }
            try:
                print(f"Mengambil data OpenAlex untuk kueri: '{query}'...")
                response = requests.get(
                    BASE_URL,
                    params=params,
                    headers=HEADERS,
                    timeout=30,
                )
                response.raise_for_status()
                data = response.json()
                results = data.get("results", [])

                for item in results:
                    # Parse authors
                    authors = []
                    for authorship in item.get("authorships", []):
                        author_obj = authorship.get("author", {})
                        name = author_obj.get("display_name")
                        if name:
                            authors.append(name)

                    # Parse journal / source
                    journal = ""
                    primary_loc = item.get("primary_location") or {}
                    source_obj = primary_loc.get("source") or {}
                    if source_obj:
                        journal = source_obj.get("display_name", "")

                    record = {
                        "source": "OpenAlex",
                        "query": query,
                        "doi": item.get("doi"),
                        "title": item.get("title", ""),
                        "authors": authors,
                        "published": item.get("publication_year"),
                        "journal": journal,
                        "type": item.get("type"),
                        "url": item.get("doi") or item.get("id"),
                        "license_metadata": (
                            item.get("primary_location", {}) or {}
                        ).get("license"),
                        "cited_by_count": item.get("cited_by_count", 0),
                    }

                    output.write(json.dumps(record, ensure_ascii=False) + "\n")
                    count += 1

                print(f"  -> Sukses: {len(results)} entri diperoleh.")
            except Exception as e:
                print(f"  -> Error pada kueri '{query}': {e}")

            time.sleep(1)

    print(f"\nTotal entri OpenAlex berhasil dikumpulkan: {count}")
    print(f"Output: {OUT}")


if __name__ == "__main__":
    main()
