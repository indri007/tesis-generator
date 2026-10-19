import csv
import json
import hashlib
import subprocess
from pathlib import Path
from collections import Counter
from urllib.parse import urlparse, unquote
from datetime import datetime, timezone

ROOT = Path("data/upn_repository_clone")
OUT = Path("reports")
OUT.mkdir(exist_ok=True)

def read_jsonl(path):
    rows, malformed = [], 0
    if not path.exists():
        return rows, malformed
    with path.open(encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                malformed += 1
    return rows, malformed

def sha256_file(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def write_csv(path, rows):
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    keys = list(dict.fromkeys(k for row in rows for k in row.keys()))
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

print("=" * 68)
print("BIT FINAL — AUDIT METADATA, DOWNLOAD, TEST, DAN GIT")
print("Waktu UTC:", datetime.now(timezone.utc).isoformat())
print("=" * 68)

# 1. Metadata
records, bad_lines = read_jsonl(ROOT / "records.jsonl")
ids = [str(r.get("identifier", "")) for r in records if r.get("identifier")]
id_counts = Counter(ids)
duplicate_ids = sorted(k for k, v in id_counts.items() if v > 1)

record_report = []
comm_records = []
all_urls = set()

for r in records:
    urls = r.get("document_urls", [])
    if isinstance(urls, str):
        urls = [urls]
    if not isinstance(urls, list):
        urls = []

    for u in urls:
        if isinstance(u, str) and u.startswith("https://"):
            all_urls.add(u)

    searchable = json.dumps(r, ensure_ascii=False).lower()
    if "komunikasi" in searchable or "social sciences" in searchable or '"h social sciences"' in searchable:
        comm_records.append({
            "identifier": r.get("identifier", ""),
            "title": r.get("title", ""),
            "date": r.get("date", ""),
            "authors": json.dumps(r.get("authors", r.get("creator", [])), ensure_ascii=False),
            "document_urls": json.dumps(urls, ensure_ascii=False),
        })

    record_report.append({
        "identifier": r.get("identifier", ""),
        "title": r.get("title", ""),
        "date": r.get("date", ""),
        "document_url_count": len(urls),
        "document_urls": json.dumps(urls, ensure_ascii=False),
    })

write_csv(OUT / "metadata_inventory.csv", record_report)
write_csv(OUT / "communication_candidates.csv", comm_records)

print("\n[1] METADATA")
print("Record valid:", len(records))
print("Baris JSON rusak:", bad_lines)
print("Identifier unik:", len(set(ids)))
print("Identifier duplikat:", len(duplicate_ids))
print("Kandidat URL HTTPS unik dari metadata:", len(all_urls))
print("Record relevan komunikasi / social sciences (indikatif):", len(comm_records))

# 2. Candidate URL CSV
candidate_path = ROOT / "document_url_candidates.csv"
candidate_rows = []
if candidate_path.exists():
    with candidate_path.open(encoding="utf-8-sig", newline="") as f:
        candidate_rows = list(csv.DictReader(f))
candidate_urls = {
    str(r.get("url", "")).strip()
    for r in candidate_rows
    if str(r.get("url", "")).strip()
}
print("\n[2] KANDIDAT DOKUMEN")
print("Baris kandidat CSV:", len(candidate_rows))
print("URL unik kandidat CSV:", len(candidate_urls))

# 3. Download manifest — historical counts and latest status per URL
manifest_path = ROOT / "download_manifest.jsonl"
manifest, manifest_bad = read_jsonl(manifest_path)
latest = {}
for row in manifest:
    url = row.get("url")
    if url:
        latest[url] = row

history_counts = Counter(str(r.get("status", "missing_status")) for r in manifest)
latest_counts = Counter(str(r.get("status", "missing_status")) for r in latest.values())
download_audit = []
valid_downloads = 0

for url, row in latest.items():
    raw_file = row.get("file")
    path = Path(raw_file) if raw_file else None

    if path and not path.is_absolute() and not path.exists():
        path = ROOT / path

    # Legacy manifest entries may not contain a filename.
    if not path or not path.is_file():
        name = unquote(Path(urlparse(url).path).name)
        prefix = hashlib.sha256(url.encode()).hexdigest()[:12]
        possible = list((ROOT / "public_files").glob(f"{prefix}_*"))
        if possible:
            path = possible[0]
        elif name:
            possible = list((ROOT / "public_files").glob(f"*_{name}"))
            path = possible[0] if possible else path

    status = str(row.get("status", "missing_status"))
    size = path.stat().st_size if path and path.is_file() else 0
    digest = ""
    integrity = "NOT_CHECKED"

    if status == "downloaded":
        if not path or not path.is_file():
            integrity = "FILE_MISSING"
        elif size <= 0:
            integrity = "EMPTY_FILE"
        else:
            digest = sha256_file(path)
            expected = row.get("sha256")
            integrity = "VALID" if not expected or digest == expected else "HASH_MISMATCH"
            if integrity == "VALID":
                valid_downloads += 1

    download_audit.append({
        "url": url,
        "latest_status": status,
        "file": str(path) if path else "",
        "bytes": size,
        "sha256_actual": digest,
        "sha256_manifest": row.get("sha256", ""),
        "integrity": integrity,
        "error": row.get("error", row.get("error_message", "")),
    })

write_csv(OUT / "download_integrity_audit.csv", download_audit)

print("\n[3] DOWNLOAD MANIFEST")
print("Total entri historis:", len(manifest))
print("Baris JSON manifest rusak:", manifest_bad)
print("URL unik dalam manifest:", len(latest))
print("Status historis:", dict(history_counts))
print("Status terbaru per URL:", dict(latest_counts))
print("Unduhan berstatus downloaded dan lolos pemeriksaan:", valid_downloads)
print("Rincian integritas: reports/download_integrity_audit.csv")

# 4. Actual files and incomplete transfers
public_dir = ROOT / "public_files"
files = [p for p in public_dir.rglob("*") if p.is_file()] if public_dir.exists() else []
partial = [p for p in files if p.name.endswith(".part")]
zero_byte = [p for p in files if p.stat().st_size == 0]
pdf_files = [p for p in files if p.suffix.lower() == ".pdf" and p.stat().st_size > 0]

file_inventory = []
for p in files:
    if p.name.endswith(".part"):
        state = "PARTIAL"
    elif p.stat().st_size == 0:
        state = "EMPTY"
    else:
        state = "PRESENT"
    file_inventory.append({
        "file": str(p),
        "bytes": p.stat().st_size,
        "state": state,
        "sha256": sha256_file(p) if state == "PRESENT" else "",
    })
write_csv(OUT / "local_file_inventory.csv", file_inventory)

print("\n[4] FILE LOKAL")
print("Jumlah file:", len(files))
print("PDF non-kosong:", len(pdf_files))
print("File .part:", len(partial))
print("File kosong:", len(zero_byte))

# 5. Checkpoint and XML page inventory
checkpoint_path = ROOT / "checkpoint.json"
checkpoint = {}
if checkpoint_path.exists():
    try:
        checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
    except Exception as e:
        checkpoint = {"checkpoint_parse_error": str(e)}

pages_dir = ROOT / "pages"
pages = sorted(p for p in pages_dir.glob("*.xml")) if pages_dir.exists() else []
page_inventory = [
    {"file": str(p), "bytes": p.stat().st_size}
    for p in pages
]
write_csv(OUT / "xml_page_inventory.csv", page_inventory)

print("\n[5] HARVEST CHECKPOINT")
print(json.dumps(checkpoint, ensure_ascii=False, indent=2))
print("Jumlah halaman XML:", len(pages))
print("Ukuran total XML (bytes):", sum(p.stat().st_size for p in pages))

# 6. Running process
try:
    proc = subprocess.run(
        ["pgrep", "-fl", "harvest_upn_repository.py"],
        capture_output=True, text=True, timeout=5
    )
    process_output = proc.stdout.strip()
except Exception as e:
    process_output = f"Process check unavailable: {e}"

print("\n[6] PROSES HARVESTER")
print(process_output or "Tidak ditemukan proses dengan nama tersebut.")

# 7. Git state; do not alter Git or manufacture CI status
try:
    branch = subprocess.run(
        ["git", "branch", "--show-current"],
        capture_output=True, text=True, timeout=5
    ).stdout.strip()
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        capture_output=True, text=True, timeout=5
    ).stdout.strip()
    git_status = subprocess.run(
        ["git", "status", "--short"],
        capture_output=True, text=True, timeout=5
    ).stdout.strip()
except Exception as e:
    branch, commit, git_status = "", "", str(e)

print("\n[7] GIT")
print("Branch:", branch)
print("HEAD:", commit)
print("Perubahan working tree:", git_status or "clean")

# 8. Save machine-readable final summary
summary = {
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "metadata": {
        "valid_records": len(records),
        "malformed_json_lines": bad_lines,
        "unique_identifiers": len(set(ids)),
        "duplicate_identifiers": len(duplicate_ids),
        "https_document_urls": len(all_urls),
        "communication_candidates_indicative": len(comm_records),
    },
    "candidates": {
        "csv_rows": len(candidate_rows),
        "unique_urls": len(candidate_urls),
    },
    "downloads": {
        "historical_manifest_entries": len(manifest),
        "manifest_malformed_lines": manifest_bad,
        "unique_urls": len(latest),
        "historical_status_counts": dict(history_counts),
        "latest_status_counts": dict(latest_counts),
        "valid_downloaded_files": valid_downloads,
        "partial_files": len(partial),
        "zero_byte_files": len(zero_byte),
        "nonempty_pdfs": len(pdf_files),
    },
    "harvest": {
        "checkpoint": checkpoint,
        "xml_page_count": len(pages),
        "xml_total_bytes": sum(p.stat().st_size for p in pages),
        "process_output": process_output,
    },
    "git": {"branch": branch, "head": commit, "status": git_status},
    "reports": [
        "reports/bit_final_summary.json",
        "reports/metadata_inventory.csv",
        "reports/communication_candidates.csv",
        "reports/download_integrity_audit.csv",
        "reports/local_file_inventory.csv",
        "reports/xml_page_inventory.csv",
    ],
}

(OUT / "bit_final_summary.json").write_text(
    json.dumps(summary, ensure_ascii=False, indent=2),
    encoding="utf-8"
)

print("\n[8] STATUS AUDIT")
if bad_lines or manifest_bad:
    verdict = "NEEDS_REVIEW: ditemukan baris JSON rusak"
elif duplicate_ids:
    verdict = "NEEDS_REVIEW: ada identifier duplikat"
elif partial or zero_byte:
    verdict = "NEEDS_REVIEW: ada file parsial/kosong"
elif latest_counts.get("failed", 0):
    verdict = "PARTIAL: masih ada unduhan gagal; bukan berarti metadata gagal"
else:
    verdict = "AUDIT DATA SELESAI: cek checkpoint/proses untuk memastikan harvest tuntas"

print(verdict)
print("\nLaporan dibuat di:", OUT.resolve())
print("Catatan: audit lokal ini tidak membuktikan seluruh repositori telah terambil.")
