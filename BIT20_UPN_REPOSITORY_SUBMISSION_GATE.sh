#!/usr/bin/env bash
# ==============================================================================
# BIT20: UPN INSTITUTIONAL REPOSITORY COMPLIANCE & SUBMISSION GATE
# Target: https://repository.upnjatim.ac.id/view/divisions/comm/2026.html
# Division: comm (Magister Ilmu Komunikasi FISIP / FISIBPOL - UPN Veteran Jatim)
# Year: 2026 | System: EPrints 3.x Institutional Repository
# ==============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "======================================================================"
echo "    BIT20: UPN REPOSITORY COMPLIANCE & SUBMIT GATE (2026)"
echo "    Endpoint: https://repository.upnjatim.ac.id/view/divisions/comm/2026.html"
echo "    Timestamp: $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
echo "======================================================================"

# Determine Python runtime
if [ -f ".venv-test/bin/python3" ]; then
    PY=".venv-test/bin/python3"
elif [ -f "/Users/jevin/AI-Thesis-Generator/.venv-test/bin/python3" ]; then
    PY="/Users/jevin/AI-Thesis-Generator/.venv-test/bin/python3"
elif [ -f ".venv/bin/python3" ]; then
    PY=".venv/bin/python3"
else
    PY="python3"
fi

echo ""
echo "[1/5] REPOSITORY TAXONOMY SPECIFICATION & METADATA"
echo "----------------------------------------------------------------------"
$PY -c "
import json
with open('rules/upn_repository_rules.json', 'r') as f:
    r = json.load(f)
print(f'Repository Endpoint : {r[\"repository_endpoint\"]}')
print(f'Sistem Repositori   : {r[\"system\"]}')
print(f'Divisi / Prodi      : {r[\"division_code\"]} ({r[\"division_name\"]})')
print(f'Tahun Akademik      : {r[\"year\"]}')
print(f'Tipe Item / Jenjang : {r[\"thesis_type\"]} ({r[\"thesis_degree\"]})')
print(f'Batas Turnitin Max  : {r[\"submission_requirements\"][\"plagiarism_threshold_percent\"]}%')
print(f'Domain Email Wajib  : {r[\"submission_requirements\"][\"email_domain_requirement\"]}')
"

echo ""
echo "[2/5] PROTOKOL STANDAR PENAMAAN 10 BERKAS EPRINTS UPN VETERAN JATIM"
echo "----------------------------------------------------------------------"
$PY -c "
from engines.upn_repository_engine import UPNRepositoryEngine
engine = UPNRepositoryEngine()
manifest = engine.generate_file_manifest('22081010045')
print(f'| {\"Kode\":<12} | {\"Format Nama File\":<28} | {\"Akses\":<14} | {\"Tipe Dokumen\":<22} |')
print('|' + '-'*14 + '|' + '-'*30 + '|' + '-'*16 + '|' + '-'*24 + '|')
for m in manifest:
    print(f'| {m.code:<12} | {m.target_filename:<28} | {m.access_policy:<14} | {m.source_type:<22} |')
"

echo ""
echo "[3/5] SUBMISSION READINESS AUDIT GATE (SIMULASI KELAYAKAN UNGGAH)"
echo "----------------------------------------------------------------------"
$PY -c "
from engines.upn_repository_engine import UPNRepositoryEngine
engine = UPNRepositoryEngine()
sample_doc = {
    'title': 'Analisis Resepsi Komunikasi Digital Kebijakan MBG di Media Sosial',
    'chapters': {'BAB I': {}, 'BAB II': {}, 'BAB III': {}, 'BAB IV': {}, 'BAB V': {}},
    'has_abstract_id': True,
    'has_abstract_en': True
}
rep = engine.audit_submission_readiness(
    sample_doc,
    npm='22081010045',
    author_name='Indri Kartika',
    author_email='indri@upnjatim.ac.id',
    similarity_percent=14.5
)
print(f'Status Kesiapan    : {\"LULUS SIAP UNGGAH\" if rep.is_ready_for_submission else \"GAGAL\"}')
print(f'Indeks Kepatuhan   : {rep.compliance_score:.1f}%')
print(f'Hasil Uji Turnitin : {rep.similarity_status} ({rep.similarity_score}%)')
print('Rincian Verifikasi Kriteria Perpustakaan:')
for c in rep.checklist_results:
    print(f'  [{c[\"status\"]}] {c[\"label\"]}: {c[\"detail\"]}')
"

echo ""
echo "[4/5] VERIFIKASI UNIT TEST SUITE (tests/unit/test_upn_repository.py)"
echo "----------------------------------------------------------------------"
$PY -m pytest tests/unit/test_upn_repository.py -q

echo ""
echo "[5/5] SINKRONISASI ARTEFAK & EXPORT SUMMARY"
echo "----------------------------------------------------------------------"
echo "[✓] Aturan Repositori Terdaftar : rules/upn_repository_rules.json"
echo "[✓] Mesin Verifikasi EPrints   : engines/upn_repository_engine.py"
echo "[✓] Tab Dashboard Streamlit    : app.py (Tab 9: Repositori UPN 2026)"
echo "[✓] Unit Test Suite            : tests/unit/test_upn_repository.py"
echo ""
echo "======================================================================"
echo "    [SUCCESS] BIT20 UPN REPOSITORY GATE VERIFICATION COMPLETED"
echo "======================================================================"
