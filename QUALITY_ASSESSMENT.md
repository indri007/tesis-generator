# TesisCheck MIKOM 2026 — Quality Assessment & Testing Plan

## Tujuan

Aplikasi Streamlit ini perlu diuji pada 4 lapisan:

1. **Code quality** — apakah kode bersih, konsisten, dan typed.
2. **Functional correctness** — apakah parser/auditor benar-benar menghasilkan temuan yang benar.
3. **UI/E2E quality** — apakah alur upload → audit → report bekerja di browser.
4. **Security/dependency quality** — apakah dependency memiliki vulnerability yang diketahui.

## Tool yang disarankan

### Wajib
- `pytest` — unit/integration tests.
- `streamlit.testing.v1.AppTest` — pengujian aplikasi Streamlit tanpa browser.
- `ruff` — lint + formatter.
- `mypy` — static type checking.
- `coverage` — code coverage.
- `bandit` — security linting untuk Python.
- `pip-audit` — audit dependency terhadap known vulnerabilities.

### Sangat disarankan
- `pytest-cov` — integrasi coverage dengan pytest.
- `Playwright + pytest-playwright` — end-to-end browser testing.
- `pre-commit` — menjalankan pemeriksaan sebelum commit.
- `hypothesis` — property-based testing untuk parser, angka, rumus, dan normalisasi.

## Instalasi dasar

```bash
python -m venv .venv

# macOS/Linux
source .venv/bin/activate

# Windows
# .venv\Scripts\activate

python -m pip install --upgrade pip

pip install streamlit pytest pytest-cov ruff mypy bandit pip-audit pre-commit
pip install hypothesis
pip install pytest-playwright
playwright install chromium
```

## Quality gate

Jalankan:

```bash
ruff check .
ruff format --check .
mypy .
bandit -r .
pip-audit
pytest -q
pytest --cov=. --cov-report=term-missing --cov-report=html
```

Untuk Streamlit AppTest:

```python
from streamlit.testing.v1 import AppTest

def test_app_starts():
    at = AppTest.from_file("app.py").run()
    assert not at.exception
```

## Target coverage

Target awal:
- Parser: >= 90%
- Rule engine: >= 90%
- Formula/statistics checker: >= 90%
- Citation/reference checker: >= 85%
- Journal-vs-thesis comparator: >= 80%
- UI: diuji dengan AppTest + smoke E2E

Jangan mengejar angka coverage semata. Temuan yang salah pada tesis lebih berbahaya daripada coverage yang rendah.

## Golden test set

Buat minimal 10 dokumen uji sintetis:

1. tesis valid
2. margin salah
3. font salah
4. BAB tidak lengkap
5. jumlah kata salah
6. citation tanpa reference
7. reference tanpa citation
8. variabel X1 berubah definisi
9. rumus dan hasil hitung tidak konsisten
10. jurnal berbeda dari tesis

Setiap dokumen harus mempunyai expected findings yang sudah ditentukan.

## Quality Assessment khusus domain tesis

Jangan hanya menilai kualitas software. Ukur juga:

- precision temuan
- recall temuan
- false positive rate
- false negative rate
- formula recalculation accuracy
- variable consistency accuracy
- citation/reference matching accuracy
- journal/thesis alignment accuracy

Contoh acceptance target MVP:

| Modul | Target |
|---|---:|
| Page limit | 100% |
| DOCX basic format | >= 95% |
| Structure detection | >= 95% |
| Citation/reference matching | >= 95% |
| Deterministic arithmetic | 100% |
| Variable consistency | >= 90% |
| Formula semantic audit | >= 85% |
| Journal/thesis alignment | >= 85% |

## Prinsip penting

Untuk aturan deterministik seperti margin, font, jumlah halaman, word count, numbering, dan aritmetika, jangan gunakan LLM sebagai sumber keputusan utama.

LLM digunakan untuk semantic analysis, contradiction detection, contextual formula interpretation, dan journal/thesis comparison.

Setiap finding wajib menyimpan:
- rule_id
- severity
- confidence
- page
- section
- evidence
- recommendation

Gunakan `UNVERIFIED` bila bukti tidak cukup.

## CI

Idealnya GitHub Actions menjalankan:

```text
ruff
mypy
bandit
pip-audit
pytest
coverage
Streamlit AppTest
```

Kemudian Playwright untuk smoke test deployment/staging.

