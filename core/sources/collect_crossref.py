# scripts/collect_crossref.py
import json
import time
from pathlib import Path

import requests

OUT = Path("data/raw/crossref_metadata.jsonl")
OUT.parent.mkdir(parents=True, exist_ok=True)

QUERIES = [
    "communication studies",
    "media and communication",
    "social network analysis",
    "digital communication Indonesia",
    "public relations",
]

BASE_URL = "https://api.crossref.org/works"
HEADERS = {
    "User-Agent": (
        "TesisCheckMIKOM/0.1 "
        "(mailto:your-email@example.com)"
    )
}

def main() -> None:
    count = 0

    with OUT.open("a", encoding="utf-8") as output:
        for query in QUERIES:
            params = {
                "query.bibliographic": query,
                "rows": 100,
                "select": (
                    "DOI,title,author,published,"
                    "container-title,type,URL,license"
                ),
            }

            try:
                response = requests.get(
                    BASE_URL,
                    params=params,
                    headers=HEADERS,
                    timeout=30,
                )
                response.raise_for_status()

                items = response.json().get(
                    "message", {}
                ).get("items", [])

                for item in items:
                    record = {
                        "source": "Crossref",
                        "query": query,
                        "doi": item.get("DOI"),
                        "title": item.get("title", []),
                        "authors": item.get("author", []),
                        "published": item.get("published"),
                        "journal": item.get("container-title", []),
                        "type": item.get("type"),
                        "url": item.get("URL"),
                        "license_metadata": item.get("license", []),
                        "full_text_downloaded": False,
                    }
                    output.write(
                        json.dumps(record, ensure_ascii=False)
                        + "\n"
                    )
                    count += 1
            except Exception as e:
                print(f"Query {query} error: {e}")

            time.sleep(1)

    print(f"Records collected: {count}")
    print(f"Output: {OUT}")

if __name__ == "__main__":
    main()
