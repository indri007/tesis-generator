#!/bin/bash
set -u
cd /Users/jevin/AI-Thesis-Generator || exit 1
mkdir -p workspace
OUT="workspace/BIT12_FIXTURE_FORENSICS.txt"

.venv-test/bin/python - <<'PY' > "$OUT" 2>&1
import io
import hashlib
import subprocess
import difflib
from pathlib import Path
from docx import Document

targets = [
    "TEST-006_citation_missing_bib.docx",
    "TEST-007_formula_error.docx",
    "TEST-008_stat_contradiction.docx",
    "TEST-009_sample_mismatch.docx",
    "TEST-010_journal.docx",
    "TEST-010_thesis.docx",
]

def sha(data):
    return hashlib.sha256(data).hexdigest()

def extract(data):
    doc = Document(io.BytesIO(data))
    lines = []
    for i, p in enumerate(doc.paragraphs):
        lines.append(f"P{i:03d} [{p.style.name}]: {p.text}")
    for ti, table in enumerate(doc.tables):
        for ri, row in enumerate(table.rows):
            cells = " | ".join(c.text.replace("\n", "\\n") for c in row.cells)
            lines.append(f"T{ti:02d}R{ri:03d}: {cells}")
    return lines, doc

root = Path("golden_dataset/documents")

for name in targets:
    path = root / name
    print("\n" + "=" * 80)
    print(name)
    print("=" * 80)

    if not path.exists():
        print("WORKING FILE MISSING")
        continue

    current = path.read_bytes()
    old_proc = subprocess.run(
        ["git", "show", f"HEAD:{path.as_posix()}"],
        capture_output=True, check=False
    )
    print("working_sha256:", sha(current))

    if old_proc.returncode != 0:
        print("BASELINE: tidak ada di HEAD")
        continue

    baseline = old_proc.stdout
    print("baseline_sha256:", sha(baseline))
    print("binary_identical:", current == baseline)

    try:
        old_lines, old_doc = extract(baseline)
        new_lines, new_doc = extract(current)
    except Exception as exc:
        print("DOCX parse error:", repr(exc))
        continue

    print("paragraphs baseline/current:",
          len(old_doc.paragraphs), "/", len(new_doc.paragraphs))
    print("tables baseline/current:",
          len(old_doc.tables), "/", len(new_doc.tables))
    print("sections baseline/current:",
          len(old_doc.sections), "/", len(new_doc.sections))

    for idx, (old_sec, new_sec) in enumerate(
        zip(old_doc.sections, new_doc.sections)
    ):
        print(
            f"section {idx}: "
            f"page size {old_sec.page_width}x{old_sec.page_height}"
            f" -> {new_sec.page_width}x{new_sec.page_height}; "
            f"margins L/R/T/B "
            f"{old_sec.left_margin}/{old_sec.right_margin}/"
            f"{old_sec.top_margin}/{old_sec.bottom_margin} -> "
            f"{new_sec.left_margin}/{new_sec.right_margin}/"
            f"{new_sec.top_margin}/{new_sec.bottom_margin}"
        )

    diff = list(difflib.unified_diff(
        old_lines, new_lines,
        fromfile="HEAD/" + name,
        tofile="WORKING/" + name,
        lineterm="",
        n=3
    ))
    if not diff:
        print("TEXT DIFF: tidak ada")
    else:
        print("TEXT DIFF:")
        for line in diff[:160]:
            print(line)
        if len(diff) > 160:
            print(f"... {len(diff)-160} baris diff lainnya disembunyikan")

print("\n" + "=" * 80)
print("AUDIT SELESAI — semua file hanya dibaca.")
print("Tidak ada restore, edit, staging, commit, push, atau deployment.")
PY

echo "Laporan: $OUT"
cat "$OUT"
