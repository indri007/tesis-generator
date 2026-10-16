"""Unit tests for DocLayNet Layout & Spatial Analysis Clone.

Verifies:
1. Category classification (Title, Section-Header, Text, Picture, Caption, Formula, Table, List-Item).
2. Spatial Bounding Box intersections and IoU calculations.
3. Reading order sorting and spatial caption pairing.
4. Margin violation detection against Pedoman Penulisan Tesis MIKOM 2026.
"""

from __future__ import annotations

from core.clones.doclaynet_layout import (
    BoundingBox,
    DocLayNetCategory,
    DocLayNetClone,
    DocLayNetElement,
)


def test_doclaynet_category_classification() -> None:
    """Verifies that block classifications match DocLayNet scientific criteria."""
    assert DocLayNetClone.classify_text_block("Gambar 3.1: Diagram Alir") == DocLayNetCategory.CAPTION
    assert DocLayNetClone.classify_text_block("Tabel 4.2: Data Responden") == DocLayNetCategory.CAPTION
    assert DocLayNetClone.classify_text_block("BAB III: METODE PENELITIAN", font_size=16.0) == DocLayNetCategory.TITLE
    assert DocLayNetClone.classify_text_block("3.1 Pendekatan Penelitian", font_size=12.0, is_bold=True) == DocLayNetCategory.SECTION_HEADER
    assert DocLayNetClone.classify_text_block("- Sampel kuantitatif n = 100") == DocLayNetCategory.LIST_ITEM
    assert DocLayNetClone.classify_text_block("Penelitian ini menggunakan pendekatan kuantitatif empiris.") == DocLayNetCategory.TEXT


def test_bounding_box_geometry() -> None:
    """Verifies area, intersection, and IoU calculations."""
    box_a = BoundingBox(x=10, y=10, width=100, height=100)
    box_b = BoundingBox(x=60, y=60, width=100, height=100)
    box_c = BoundingBox(x=200, y=200, width=50, height=50)

    assert box_a.area == 10000.0
    assert box_a.intersects(box_b) is True
    assert box_a.intersects(box_c) is False
    assert 0.14 < box_a.intersection_over_union(box_b) < 0.16


def test_doclaynet_document_layout_analysis() -> None:
    """Verifies document layout segmentation, caption spatial pairing, and margin check."""
    elements = [
        # Page 1 Title
        DocLayNetElement(
            element_id="el_title",
            category=DocLayNetCategory.TITLE,
            bbox=BoundingBox(x=120, y=80, width=350, height=30),
            page_number=1,
            text_content="BAB III METODOLOGI PENELITIAN",
        ),
        # Page 1 Picture
        DocLayNetElement(
            element_id="el_pic",
            category=DocLayNetCategory.PICTURE,
            bbox=BoundingBox(x=120, y=150, width=350, height=200),
            page_number=1,
        ),
        # Page 1 Caption directly below Picture
        DocLayNetElement(
            element_id="el_cap",
            category=DocLayNetCategory.CAPTION,
            bbox=BoundingBox(x=120, y=360, width=350, height=20),
            page_number=1,
            text_content="Gambar 3.1: Diagram Alir Penelitian",
        ),
        # Page 1 Body text
        DocLayNetElement(
            element_id="el_txt",
            category=DocLayNetCategory.TEXT,
            bbox=BoundingBox(x=120, y=400, width=350, height=120),
            page_number=1,
            text_content="Tahap pelaksanaan riset diawali dengan...",
        ),
    ]

    report = DocLayNetClone.analyze_document_layout(elements)

    assert report.total_elements == 4
    assert report.category_counts[DocLayNetCategory.PICTURE.value] == 1
    assert report.category_counts[DocLayNetCategory.CAPTION.value] == 1
    assert len(report.figure_caption_pairs) == 1
    assert report.figure_caption_pairs[0]["picture_id"] == "el_pic"
    assert report.figure_caption_pairs[0]["caption_id"] == "el_cap"
    assert report.layout_score == 100.0
    assert len(report.formatting_warnings) == 0
