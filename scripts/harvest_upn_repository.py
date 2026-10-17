#!/usr/bin/env python3
"""Harvest public UPN repository metadata through OAI-PMH."""

import csv
import ssl
import certifi
import json
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

BASE = "https://repository.upnjatim.ac.id/cgi/oai2"
OUT = Path("data/upn_repository_clone")
PAGES = OUT / "pages"
JSONL = OUT / "records.jsonl"
CSVFILE = OUT / "records.csv"
CHECKPOINT = OUT / "checkpoint.json"
DELAY = 1.5
TIMEOUT = 60

OAI = "{http://www.openarchives.org/OAI/2.0/}"


def save_json(path, data):
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2),
                    encoding="utf-8")
    temp.replace(path)


def request(params, retries=5):
    query = urllib.parse.urlencode(params)
    url = BASE + "?" + query
    last_error = None

    for attempt in range(retries):
        try:
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "UPN-Repository-Metadata-Harvester/1.0",
                    "Accept": "application/xml,text/xml,*/*",
                },
            )
            context = ssl.create_default_context(cafile=certifi.where())
            with urllib.request.urlopen(
                req, timeout=TIMEOUT, context=context
            ) as response:
                return response.read()
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last_error = exc
            wait = min(5 * (attempt + 1), 30)
            print(f"Request gagal: {exc}. Coba lagi {wait} detik.")
            time.sleep(wait)

    raise RuntimeError(f"Gagal setelah {retries} percobaan: {last_error}")


def local_name(tag):
    return tag.rsplit("}", 1)[-1]


def identify_and_formats():
    for name, params in [
        ("identify.xml", {"verb": "Identify"}),
        ("metadata_formats.xml", {"verb": "ListMetadataFormats"}),
        ("sets.xml", {"verb": "ListSets"}),
    ]:
        try:
            content = request(params)
            ET.fromstring(content)  # Validate XML.
            (OUT / name).write_bytes(content)
            print(f"OK: {name}")
            time.sleep(DELAY)
        except Exception as exc:
            print(f"PERINGATAN: {name}: {exc}")


def read_records(root):
    container = root.find(OAI + "ListRecords")
    if container is None:
        error = root.find(OAI + "error")
        if error is not None:
            raise RuntimeError(
                f"OAI error {error.attrib}: {error.text}"
            )
        raise RuntimeError("Respons tidak memiliki ListRecords.")

    records = []
    for item in container.findall(OAI + "record"):
        header = item.find(OAI + "header")
        metadata = item.find(OAI + "metadata")

        if header is None:
            continue

        fields = {}
        if metadata is not None:
            for element in metadata.iter():
                if element is metadata:
                    continue
                if len(element) == 0 and element.text:
                    key = local_name(element.tag)
                    fields.setdefault(key, []).append(element.text.strip())

        records.append({
            "identifier": (
                header.findtext(OAI + "identifier") or ""
            ),
            "datestamp": header.findtext(OAI + "datestamp") or "",
            "sets": [
                e.text or "" for e in header.findall(OAI + "setSpec")
            ],
            "deleted": header.attrib.get("status") == "deleted",
            "metadata": fields,
            "raw_xml": ET.tostring(item, encoding="unicode"),
        })

    token_element = container.find(OAI + "resumptionToken")
    token = (
        token_element.text.strip()
        if token_element is not None and token_element.text
        else ""
    )
    return records, token


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    PAGES.mkdir(parents=True, exist_ok=True)

    identify_and_formats()

    state = json.loads(CHECKPOINT.read_text(encoding="utf-8")) \
        if CHECKPOINT.exists() else {
            "page": 0, "token": "", "done": False, "count": 0
        }

    if state.get("done"):
        print("Harvest sebelumnya sudah selesai.")
        print("Hapus checkpoint hanya jika memang ingin mulai ulang.")
        return

    page = int(state.get("page", 0))
    token = state.get("token", "")
    total = int(state.get("count", 0))

    while True:
        params = (
            {"verb": "ListRecords", "metadataPrefix": "oai_dc"}
            if not token else
            {"verb": "ListRecords", "resumptionToken": token}
        )

        content = request(params)
        root = ET.fromstring(content)

        page += 1
        page_file = PAGES / f"page_{page:06d}.xml"
        page_file.write_bytes(content)

        records, next_token = read_records(root)

        # Append harvested records to JSONL.
        with JSONL.open("a", encoding="utf-8") as f:
            for record in records:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")

        total += len(records)
        token = next_token

        state = {
            "page": page,
            "token": token,
            "done": not bool(token),
            "count": total,
        }
        save_json(CHECKPOINT, state)

        print(
            f"Halaman {page}: {len(records)} rekaman | "
            f"total sesi {total} | token berikutnya: "
            f"{'ada' if token else 'tidak ada'}"
        )

        if not token:
            break

        time.sleep(DELAY)

    print("Harvest metadata selesai.")
    print(f"XML mentah : {PAGES}")
    print(f"JSONL      : {JSONL}")
    print(f"Checkpoint : {CHECKPOINT}")
    print(f"Rekaman    : {total}")

    # Export a convenient CSV index.
    rows = []
    seen = set()
    with JSONL.open(encoding="utf-8") as f:
        for line in f:
            rec = json.loads(line)
            identifier = rec["identifier"]
            if identifier in seen:
                continue
            seen.add(identifier)
            md = rec["metadata"]

            def first(key):
                values = md.get(key, [])
                return " | ".join(values)

            rows.append({
                "identifier": identifier,
                "datestamp": rec["datestamp"],
                "title": first("title"),
                "creator": first("creator"),
                "date": first("date"),
                "type": first("type"),
                "subject": first("subject"),
                "description": first("description"),
                "publisher": first("publisher"),
                "language": first("language"),
                "relation": first("relation"),
                "rights": first("rights"),
                "identifier_metadata": first("identifier"),
                "deleted": rec["deleted"],
            })

    columns = list(rows[0].keys()) if rows else [
        "identifier", "datestamp", "title", "creator", "date",
        "type", "subject", "description", "publisher", "language",
        "relation", "rights", "identifier_metadata", "deleted"
    ]
    with CSVFILE.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)

    print(f"CSV index  : {CSVFILE} ({len(rows)} ID unik)")


if __name__ == "__main__":
    main()
