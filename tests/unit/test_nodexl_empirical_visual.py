"""Unit tests for NodeXL Pro Empirical Research Visualization & PRD Integration."""

from __future__ import annotations

from pathlib import Path

from core.integrations.thisiseconomy_bridge import ThisIsEconomyBridge

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
NODEXL_TOKEN = "c1d8d71236e1cae9628f0b5c7a55b581"
NODEXL_GALLERY_URL = f"https://www.nodexlgraphgallery.org/Pages/Cloud.aspx?token={NODEXL_TOKEN}"
NODEXL_LICENSE_ORDER = "14103"


def test_nodexl_visual_asset_file_integrity():
    """Verifies that the canonical NodeXL high-resolution image exists with valid PNG header."""
    asset_path = ROOT_DIR / "assets" / "images" / "16_nodexl_graph_visualization.png"
    assert asset_path.exists(), f"Asset not found at {asset_path}"
    assert asset_path.stat().st_size > 100_000, "Image file should be high-resolution (>100KB)"

    # Verify PNG magic number bytes
    with open(asset_path, "rb") as f:
        header = f.read(8)
    assert header == b"\x89PNG\r\n\x1a\n", "File is not a valid PNG image"


def test_prd_documents_contain_nodexl_specifications():
    """Verifies that PRD documents contain full NodeXL specifications, metrics, and links."""
    prd_paths = [
        ROOT_DIR / "docs" / "PRD_AI_THESIS_GENERATOR.md",
        ROOT_DIR / "docs" / "superpowers" / "specs" / "PRODUCT_REQUIREMENTS_DOCUMENT_PRD_2026.md",
    ]

    for p in prd_paths:
        assert p.exists(), f"PRD file missing: {p}"
        content = p.read_text(encoding="utf-8")
        assert NODEXL_TOKEN in content, f"NodeXL token missing in {p}"
        assert NODEXL_GALLERY_URL in content, f"Gallery URL missing in {p}"
        assert NODEXL_LICENSE_ORDER in content, f"License order missing in {p}"
        assert "971" in content, f"Node count 971 missing in {p}"
        assert "666" in content, f"Edge count 666 missing in {p}"
        assert "0.9837" in content, f"Modularity 0.9837 missing in {p}"
        assert "0.00071" in content, f"Graph density missing in {p}"
        assert "Group-in-a-Box" in content, f"GIB layout missing in {p}"


def test_app_ui_contains_nodexl_integration():
    """Verifies that web applications app.py and app/ui/app.py render NodeXL links."""
    app_root = (ROOT_DIR / "app.py").read_text(encoding="utf-8")
    assert NODEXL_TOKEN in app_root
    assert NODEXL_GALLERY_URL in app_root
    assert "16_nodexl_graph_visualization.png" in app_root

    app_ui = (ROOT_DIR / "app" / "ui" / "app.py").read_text(encoding="utf-8")
    assert NODEXL_TOKEN in app_ui
    assert NODEXL_GALLERY_URL in app_ui


def test_thisiseconomy_bridge_baseline_alignment():
    """Verifies that the ThisIsEconomyBridge incorporates the verified 971 nodes baseline."""
    bridge = ThisIsEconomyBridge()
    assert bridge.baseline.total_nodes == 971
