#!/usr/bin/env python3
import csv
import hashlib
import json
import os
import random
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
from pathlib import Path

ROOT = Path("data/upn_repository_clone")
CANDIDATES = ROOT / "document_url_candidates.csv"
OUT = ROOT / "public_files"
MANIFEST = ROOT / "download_manifest.jsonl"
ROBOTS_URL = "https://repository.upnjatim.ac.id/robots.txt"
HOST = "repository.upnjatim.ac.id"
MAX_BYTES = 100 * 1024 * 1024
DELAY_SECONDS = 3
MAX_ATTEMPTS = 4

EXTENSIONS = {
    ".pdf", ".jpg", ".jpeg", ".png", ".tif", ".tiff",
    ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    ".txt", ".csv", ".zip"
}

OUT.mkdir(parents=True, exist_ok=True)
ROOT.mkdir(parents=True, exist_ok=True)

try:
    import certifi
    SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    SSL_CONTEXT = ssl.create_default_context()

def log(message):
    print(message, flush=True)

def sha256_file(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def request(url):
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "UPNRepositoryMetadataResearch/1.0",
            "Accept": "application/pdf,image/*,application/octet-stream,*/*",
        },
    )
    return urllib.request.urlopen(
        req, timeout=45, context=SSL_CONTEXT
    )

def load_robots():
    rp = urllib.robotparser.RobotFileParser()
    rp.set_url(ROBOTS_URL)
    try:
        with request(ROBOTS_URL) as response:
            content = response.read(256 * 1024).decode(
                "utf-8", errors="replace"
            )
        rp.parse(content.splitlines())
        log("robots.txt berhasil dibaca.")
        return rp
    except Exception as exc:
        log(f"STOP: robots.txt tidak dapat diverifikasi: {exc}")
        raise SystemExit(2)

def valid_url(url):
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or parsed.hostname != HOST:
        return False
    if parsed.path.startswith("/cgi/"):
        return False
    if Path(urllib.parse.unquote(parsed.path)).suffix.lower() not in EXTENSIONS:
        return False
    return True

def read_manifest():
    downloaded = {}
    if not MANIFEST.exists():
        return downloaded
    with MANIFEST.open(encoding="utf-8") as f:
        for line in f:
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if row.get("status") == "downloaded" and row.get("url"):
                downloaded[row["url"]] = row
    return downloaded

def write_manifest(row):
    with MANIFEST.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
        f.flush()
        os.fsync(f.fileno())

if not CANDIDATES.exists():
    raise SystemExit(f"File kandidat tidak ditemukan: {CANDIDATES}")

with CANDIDATES.open(encoding="utf-8-sig", newline="") as f:
    candidates = list(csv.DictReader(f))

unique = {}
for row in candidates:
    url = (row.get("url") or "").strip()
    if valid_url(url):
        unique.setdefault(url, row)

robots = load_robots()
allowed = {
    url: row for url, row in unique.items()
    if robots.can_fetch("UPNRepositoryMetadataResearch/1.0", url)
}
blocked = len(unique) - len(allowed)
previous = read_manifest()
do_download = os.environ.get("UPN_DOWNLOAD") == "1"

log(f"Mode: {'DOWNLOAD' if do_download else 'DRY RUN'}")
log(f"URL kandidat unik berformat file: {len(unique)}")
log(f"Dilarang oleh robots.txt: {blocked}")
log(f"URL yang diizinkan robots.txt: {len(allowed)}")

if not do_download:
    for url in list(allowed)[:15]:
        log("DRY RUN " + url)
    log("Untuk mengunduh, jalankan: UPN_DOWNLOAD=1 python3 scripts/download_upn_public_files.py")
    raise SystemExit(0)

success = failed = skipped = 0

for index, (url, row) in enumerate(allowed.items(), 1):
    parsed = urllib.parse.urlparse(url)
    basename = Path(urllib.parse.unquote(parsed.path)).name
    prefix = hashlib.sha256(url.encode("utf-8")).hexdigest()[:12]
    target = OUT / f"{prefix}_{basename}"
    part = target.with_name(target.name + ".part")

    old = previous.get(url, {})
    if old and target.is_file() and target.stat().st_size > 0:
        try:
            digest = sha256_file(target)
            if not old.get("sha256") or digest == old["sha256"]:
                skipped += 1
                log(f"[{index}/{len(allowed)}] SKIP sudah ada: {basename}")
                continue
        except OSError:
            pass

    if not robots.can_fetch("UPNRepositoryMetadataResearch/1.0", url):
        write_manifest({"url": url, "title": row.get("title", ""),
                        "status": "blocked_by_robots"})
        skipped += 1
        continue

    if part.exists():
        part.unlink()

    error_message = ""
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            with request(url) as response:
                final_url = response.geturl()
                final = urllib.parse.urlparse(final_url)
                if final.scheme != "https" or final.hostname != HOST:
                    raise ValueError("Redirect keluar dari host repositori")

                content_type = response.headers.get("Content-Type", "").lower()
                if "text/html" in content_type:
                    raise ValueError("Server mengembalikan HTML, bukan dokumen")

                length = response.headers.get("Content-Length")
                if length and int(length) > MAX_BYTES:
                    raise ValueError("Ukuran file melebihi batas 100 MB")

                size = 0
                with part.open("wb") as out:
                    while True:
                        chunk = response.read(1024 * 256)
                        if not chunk:
                            break
                        size += len(chunk)
                        if size > MAX_BYTES:
                            raise ValueError("Ukuran file melebihi batas 100 MB")
                        out.write(chunk)

                if size == 0:
                    raise ValueError("File kosong")

            digest = sha256_file(part)
            part.replace(target)
            write_manifest({
                "url": url,
                "title": row.get("title", ""),
                "oai_identifier": row.get("oai_identifier", ""),
                "status": "downloaded",
                "file": str(target),
                "bytes": size,
                "sha256": digest,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            })
            previous[url] = {"status": "downloaded", "sha256": digest}
            success += 1
            log(f"[{index}/{len(allowed)}] OK {size:,} bytes: {basename}")
            error_message = ""
            break

        except (Exception, urllib.error.URLError) as exc:
            error_message = f"{type(exc).__name__}: {exc}"
            if part.exists():
                part.unlink()
            if attempt < MAX_ATTEMPTS:
                wait = min(30, 3 * (2 ** (attempt - 1))) + random.uniform(0, 1)
                log(f"RETRY {attempt}/{MAX_ATTEMPTS}: {basename}; tunggu {wait:.1f}s; {error_message}")
                time.sleep(wait)

    if error_message:
        failed += 1
        write_manifest({
            "url": url,
            "title": row.get("title", ""),
            "oai_identifier": row.get("oai_identifier", ""),
            "status": "failed",
            "error": error_message,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        })
        log(f"[{index}/{len(allowed)}] GAGAL: {url}: {error_message}")

    time.sleep(DELAY_SECONDS)

log("")
log("===== RINGKASAN BIT25 =====")
log(f"Berhasil diunduh sesi ini: {success}")
log(f"Gagal setelah retry: {failed}")
log(f"Dilewati: {skipped}")
log(f"Manifest: {MANIFEST}")
log(f"Folder file: {OUT}")
