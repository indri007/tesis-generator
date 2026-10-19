"""Regression tests: benchmark generation must not overwrite fixtures."""
import hashlib
from pathlib import Path

from golden_dataset.generator import generate_golden_dataset


def test_generator_writes_to_requested_directory_and_preserves_fixtures(tmp_path):
    root = Path(__file__).resolve().parents[2]
    fixtures = root / "golden_dataset" / "documents"
    before = {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in fixtures.glob("*.docx")
    }

    output_dir = tmp_path / "generated_docs"
    output_dir.mkdir()
    generate_golden_dataset(output_dir=output_dir)

    generated = list(output_dir.glob("*.docx"))
    assert generated, "Generator tidak menghasilkan dokumen DOCX."

    after = {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in fixtures.glob("*.docx")
    }
    assert after == before, "Fixture DOCX sumber berubah saat generator berjalan."
