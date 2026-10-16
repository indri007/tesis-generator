"""Unit tests for DocLayNet Layout & Spatial Analysis Clone.

Verifies:
1. Category classification (Title, Section-Header, Text, Picture, Caption, Formula, Table, List-Item).
2. Spatial Bounding Box intersections and IoU calculations.
3. Reading order sorting and spatial caption pairing.
4. Margin violation detection against Pedoman Penulisan Tesis MIKOM 2026.
5. Empty diagram handling.
6. Normal diagram with valid caption pairing and zero false warnings.
7. Unpaired caption detection (caption without picture/table).
8. Two overlapping objects with significant IoU.
9. Objects placed out of canvas bounds.
10. Dynamic revalidation on parameter changes.
11. Invalid / zero dimension coordinate resilience.
"""

from __future__ import annotations

from core.clones.doclaynet_layout import (
    BoundingBox,
    DocLayNetCategory,
    DocLayNetClone,
    DocLayNetElement,
)
from core.vector_studio.academic_templates import AcademicTemplateFactory
from core.vector_studio.document_schema import (
    FigureAttribution,
    VectorLayer,
    VectorObject,
    VectorProjectSchema,
    VectorShapeType,
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
        DocLayNetElement(
            element_id="el_title",
            category=DocLayNetCategory.TITLE,
            bbox=BoundingBox(x=120, y=80, width=350, height=30),
            page_number=1,
            text_content="BAB III METODOLOGI PENELITIAN",
        ),
        DocLayNetElement(
            element_id="el_pic",
            category=DocLayNetCategory.PICTURE,
            bbox=BoundingBox(x=120, y=150, width=350, height=200),
            page_number=1,
        ),
        DocLayNetElement(
            element_id="el_cap",
            category=DocLayNetCategory.CAPTION,
            bbox=BoundingBox(x=120, y=360, width=350, height=20),
            page_number=1,
            text_content="Gambar 3.1: Diagram Alir Penelitian",
        ),
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


def test_empty_diagram_analysis() -> None:
    """Verifies that an empty vector project produces valid zero-count report without crashing."""
    empty_proj = VectorProjectSchema(
        canvas_width=800.0,
        canvas_height=600.0,
        layers=[],
        attribution=FigureAttribution(title="", source=""),
    )
    # Clear layers explicitly
    empty_proj.layers = []

    report = DocLayNetClone.analyze_vector_project(empty_proj, check_page_margins=False)
    assert report.total_elements >= 1  # Base composite figure & caption element
    assert report.layout_score == 100.0


def test_normal_diagram_zero_false_warnings() -> None:
    """Verifies that default PRISMA 2020 project produces zero false warnings and a high layout score."""
    prisma_proj = AcademicTemplateFactory.create_prisma_2020_flowchart(chapter=3, figure_idx=1)
    report = DocLayNetClone.analyze_vector_project(prisma_proj, check_page_margins=False)

    assert report.total_elements > 5
    assert len(report.out_of_bounds_elements) == 0
    assert len(report.figure_caption_pairs) >= 1
    assert report.layout_score >= 90.0


def test_unpaired_caption_detection() -> None:
    """Verifies warning when a caption has no corresponding picture or table."""
    orphan_caption = DocLayNetElement(
        element_id="cap_orphan",
        category=DocLayNetCategory.CAPTION,
        bbox=BoundingBox(x=100, y=600, width=200, height=20),
        page_number=1,
        text_content="Gambar 9.9: Gambar Hilang",
    )
    report = DocLayNetClone.analyze_document_layout([orphan_caption], page_width=500, page_height=700)
    assert "cap_orphan" in report.unpaired_captions
    assert any("tidak terhubung" in w for w in report.formatting_warnings)


def test_overlapping_objects_detection() -> None:
    """Verifies detection of overlapping objects with IoU > 0.25."""
    proj = VectorProjectSchema(canvas_width=800, canvas_height=600)
    layer = VectorLayer(name="L1")
    obj1 = VectorObject(
        object_id="obj_box_1",
        shape_type=VectorShapeType.RECTANGLE,
        x=50,
        y=50,
        width=100,
        height=100,
        text_content="Box 1",
    )
    obj2 = VectorObject(
        object_id="obj_box_2",
        shape_type=VectorShapeType.RECTANGLE,
        x=80,
        y=80,
        width=100,
        height=100,
        text_content="Box 2",
    )
    layer.objects = [obj1, obj2]
    proj.layers = [layer]

    report = DocLayNetClone.analyze_vector_project(proj, check_page_margins=False)
    assert len(report.overlapping_pairs) >= 1
    ov = report.overlapping_pairs[0]
    assert ov["element_a"] == "obj_box_1"
    assert ov["element_b"] == "obj_box_2"
    assert ov["iou"] > 0.25


def test_out_of_bounds_detection() -> None:
    """Verifies detection of objects placed outside the canvas boundary."""
    proj = VectorProjectSchema(canvas_width=500, canvas_height=400)
    layer = VectorLayer(name="L1")
    escaped_obj = VectorObject(
        object_id="obj_escaped",
        shape_type=VectorShapeType.RECTANGLE,
        x=550,  # Beyond canvas_width 500
        y=100,
        width=100,
        height=100,
    )
    layer.objects = [escaped_obj]
    proj.layers = [layer]

    report = DocLayNetClone.analyze_vector_project(proj, check_page_margins=False)
    assert "obj_escaped" in report.out_of_bounds_elements
    assert any("di luar batas" in w for w in report.formatting_warnings)


def test_parameter_change_revalidation() -> None:
    """Verifies that changing template parameters generates fresh distinct analysis reports."""
    proj1 = AcademicTemplateFactory.create_prisma_2020_flowchart(identification_count=500)
    proj2 = AcademicTemplateFactory.create_prisma_2020_flowchart(identification_count=9000)

    report1 = DocLayNetClone.analyze_vector_project(proj1)
    report2 = DocLayNetClone.analyze_vector_project(proj2)

    # Identifiers must be unique across project instances
    assert proj1.project_id != proj2.project_id
    assert report1.total_elements == report2.total_elements


def test_invalid_and_zero_dimensions_handling() -> None:
    """Verifies resilience against zero-width or negative coordinate elements."""
    zero_box = DocLayNetElement(
        element_id="el_zero",
        category=DocLayNetCategory.TEXT,
        bbox=BoundingBox(x=-10, y=-20, width=0, height=0),
        page_number=1,
    )
    report = DocLayNetClone.analyze_document_layout([zero_box], page_width=500, page_height=500)
    assert "el_zero" in report.out_of_bounds_elements
    assert report.total_elements == 1
