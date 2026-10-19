#!/usr/bin/env bash
# ==============================================================================
# BIT 18 — VOSVIEWER BIBLIOMETRIC MAPPING & SCIENCE VISUALIZATION CLONE
# Algoritma: Leiden VOS (Visualization of Similarities) & Association Strength
# Standar: MIKOM 2026 Academic Integrity & Scientometric Science Mapping
# ==============================================================================
set -euo pipefail

cd /Users/jevin/AI-Thesis-Generator || exit 1
mkdir -p workspace
OUT="workspace/BIT18_VOSVIEWER_BIBLIOMETRIC_CLONE.txt"
PY=".venv-test/bin/python3"

if [ ! -x "$PY" ]; then
  echo "ERROR: Virtualenv $PY tidak ditemukan."
  exit 1
fi

{
  echo "======================================================================"
  echo "BIT 18: VOSVIEWER BIBLIOMETRIC SCIENCE MAPPING & CLUSTER CLONE"
  date
  echo "======================================================================"

  echo
  echo "=== 1. STATUS REPOSITORY & ARSITEKTUR KLONING VOSVIEWER ==="
  git status -sb
  for f in \
    core/clones/vosviewer_bibliometrics.py \
    core/clones/__init__.py \
    tests/unit/test_vosviewer_bibliometrics.py
  do
    if [ -f "$f" ]; then
      echo "[OK] $f ($(wc -l < "$f") baris, SHA256: $(shasum -a 256 "$f" | cut -d' ' -f1))"
    else
      echo "[MISSING] $f"
      exit 1
    fi
  done

  echo
  echo "=== 2. EKSEKUSI PEMETAAN BIBLIOMETRIK & ALGORITMA VOS ==="
  "$PY" - << 'PY'
import json
from pathlib import Path
from core.clones.vosviewer_bibliometrics import VOSviewerClone

sample_corpus = [
    {
        "title": "Artificial Intelligence in Digital Journalism and Automated News Production",
        "keywords": ["Artificial Intelligence", "Digital Journalism", "News Automation"],
        "year": 2024,
        "citations": 42,
    },
    {
        "title": "Machine Learning and Natural Language Processing for Editorial Newsrooms",
        "keywords": ["Machine Learning", "Natural Language Processing", "Editorial Analytics"],
        "year": 2023,
        "citations": 28,
    },
    {
        "title": "Ethical Implications and Algorithmic Bias of AI-Generated Content in Journalism",
        "keywords": ["Artificial Intelligence", "Ethics", "Digital Journalism", "Generative AI"],
        "year": 2025,
        "citations": 19,
    },
    {
        "title": "Automated Fact-Checking Using Natural Language Processing and Knowledge Graphs",
        "keywords": ["Natural Language Processing", "Fact-Checking", "Machine Learning", "Verification"],
        "year": 2024,
        "citations": 35,
    },
    {
        "title": "Deep Learning Models for Automated Headline Generation and Sentiment Analysis",
        "keywords": ["Deep Learning", "Natural Language Processing", "News Automation"],
        "year": 2022,
        "citations": 51,
    },
]

vos = VOSviewerClone(min_cluster_size=1, resolution=1.0)
summary = vos.build_from_documents(sample_corpus, min_occurrences=1)

print("VOS Mapping Execution:")
print(f"  - Total Node Items (Terms) : {summary['total_items']}")
print(f"  - Total Network Links       : {summary['total_links']}")
print(f"  - Detected Modularity Clusters: {summary['total_clusters']}")
print(f"  - Max Association Strength  : {summary['max_link_strength']:.4f}")

# Export standard VOSviewer files
map_file = Path("workspace/vosviewer_map.txt")
net_file = Path("workspace/vosviewer_network.txt")
json_file = Path("workspace/vosviewer_online.json")

vos.export_vos_map(map_file)
vos.export_vos_network(net_file)
vos.export_vosviewer_online_json(json_file)

print(f"\n[OK] Standard VOSviewer Map File Exported     : {map_file} ({map_file.stat().st_size} bytes)")
print(f"[OK] Standard VOSviewer Network File Exported : {net_file} ({net_file.stat().st_size} bytes)")
print(f"[OK] VOSviewer Online JSON (app.vosviewer.com): {json_file} ({json_file.stat().st_size} bytes)")

print("\n=== 3. ASCII SCIENCE MAPPING & CLUSTER VISUALIZATION ===")
print(vos.generate_ascii_graph())
PY

  echo
  echo "=== 4. VERIFIKASI PYTEST UNIT REGRESSION SUITE ==="
  "$PY" -m pytest tests/unit/test_vosviewer_bibliometrics.py -q --tb=short
  echo "pytest_exit=$?"

  echo
  echo "=== RINGKASAN BIT 18 ==="
  echo "Status: SUKSES PENUH (VOSviewer Bibliometric Science Mapping Selesai)"
  echo "Format VOSviewer .map, .net, dan Online JSON siap diintegrasikan."
} > "$OUT" 2>&1

cat "$OUT"
