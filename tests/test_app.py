from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_app_starts_without_exception():
    """Verifies that the Streamlit application starts and renders without exceptions."""
    app_path = Path(__file__).resolve().parent.parent / "app.py"
    at = AppTest.from_file(str(app_path)).run(timeout=10)
    assert not at.exception
    assert len(at.title) >= 1
    assert "TesisCheck" in at.title[0].value
