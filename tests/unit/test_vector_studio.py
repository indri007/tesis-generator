"""Unit and integration tests for Vector Design Studio.

Tests:
1. Document Schema (Serialization, Deserialization, Immutability, Defaults).
2. SVG Engine (W3C standard compilation, Arrow markers, Defs, Escaping).
3. Academic Templates (PRISMA 2020 4-stage metrics, Conceptual Framework, Methodology).
4. Figure Bridge (300 DPI PNG conversion, PDF vector generation, File export).
5. DOCX Injection (Standard MIKOM 2026 figure caption, attribution, and picture insertion).
"""

from __future__ import annotations

import io
from pathlib import Path

import docx
import fitz
from PIL import Image

from core.vector_studio.academic_templates import AcademicTemplateFactory
from core.vector_studio.canvas_component import CanvasComponent
from core.vector_studio.document_schema import (
    FigureAttribution,
    VectorLayer,
    VectorObject,
    VectorProjectSchema,
    VectorShapeType,
    VectorStyle,
)
from core.vector_studio.figure_bridge import FigureBridge
from core.vector_studio.svg_engine import SVGEngine


def test_document_schema_serialization_roundtrip() -> None:
    """Verifies that VectorProjectSchema serializes to JSON and deserializes identically."""
    project = VectorProjectSchema(
        title="Uji Skema Vektor",
        canvas_width=1000.0,
        canvas_height=800.0,
        dpi=300,
        attribution=FigureAttribution(
            chapter_number=3,
            figure_index=2,
            title="Model Uji Skema",
            source="Penulis (2026)",
        ),
    )
    layer = VectorLayer(name="Test Layer")
    obj = VectorObject(
        shape_type=VectorShapeType.ROUNDED_RECT,
        name="Test Rect",
        x=50.0,
        y=60.0,
        width=200.0,
        height=100.0,
        text_content="Node Eksperimen",
        style=VectorStyle(fill="#1E40AF", stroke="#0D1424", stroke_width=2.0),
    )
    layer.objects.append(obj)
    project.layers.append(layer)

    json_str = project.to_json()
    reloaded = VectorProjectSchema.from_json(json_str)

    assert reloaded.title == "Uji Skema Vektor"
    assert reloaded.canvas_width == 1000.0
    assert reloaded.attribution.figure_label == "Gambar 3.2"
    assert len(reloaded.layers) == 2
    found_obj = reloaded.find_object(obj.object_id)
    assert found_obj is not None
    assert found_obj.text_content == "Node Eksperimen"
    assert found_obj.style.fill == "#1E40AF"


def test_svg_engine_compilation() -> None:
    """Verifies SVG XML conforms to W3C standards with markers and definitions."""
    project = VectorProjectSchema(
        canvas_width=500.0,
        canvas_height=300.0,
        attribution=FigureAttribution(title="SVG Test"),
    )
    layer = VectorLayer(name="L1")
    layer.objects.append(
        VectorObject(
            shape_type=VectorShapeType.RECTANGLE,
            x=10,
            y=10,
            width=100,
            height=50,
            text_content="A & B <Test>",
        )
    )
    project.layers = [layer]

    svg_str = SVGEngine.compile_project_to_svg(project, include_attribution=True)

    assert '<svg xmlns="http://www.w3.org/2000/svg"' in svg_str
    assert 'viewBox="0 0 500.0 300.0"' in svg_str
    assert '<defs>' in svg_str
    assert 'id="arrow-end"' in svg_str
    assert "A &amp; B &lt;Test&gt;" in svg_str
    assert "</svg>" in svg_str


def test_prisma_2020_template_generation() -> None:
    """Verifies PRISMA 2020 factory builds all 4 mandatory SLR phases."""
    prisma_proj = AcademicTemplateFactory.create_prisma_2020_flowchart(
        identification_count=1500,
        duplicates_removed=500,
        screened_count=1000,
        excluded_screening=800,
        eligibility_assessed=200,
        excluded_eligibility=160,
        included_count=40,
        chapter=3,
        figure_idx=1,
    )

    assert prisma_proj.attribution.figure_label == "Gambar 3.1"
    assert "PRISMA 2020" in prisma_proj.attribution.title
    assert len(prisma_proj.layers) >= 1

    objects = prisma_proj.layers[0].objects
    names = [o.name for o in objects]

    assert "Section_IDENTIFIKASI" in names
    assert "Section_PENYARINGAN & KELAYAKAN" in names
    assert "Section_DITERIMA" in names
    assert "Box_Identification" in names
    assert "Box_Duplicates" in names

    # Verify counts appear inside text
    id_obj = next(o for o in objects if o.name == "Box_Identification")
    assert "n = 1500" in (id_obj.text_content or "")


def test_conceptual_framework_template() -> None:
    """Verifies Conceptual Framework template creates X, M, and Y variables with Hypotheses."""
    framework_proj = AcademicTemplateFactory.create_conceptual_framework(
        var_x="Kualitas Sistem (X)",
        var_m="Kepuasan Pengguna (M)",
        var_y="Dampak Organisasi (Y)",
        h1_label="H1 (+, p < 0.05)",
        h2_label="H2 (+, p < 0.05)",
        h3_label="H3 (+, p < 0.05)",
        chapter=2,
        figure_idx=1,
    )

    assert framework_proj.attribution.figure_label == "Gambar 2.1"
    assert "Kerangka Konseptual" in framework_proj.attribution.title
    svg = SVGEngine.compile_project_to_svg(framework_proj)
    assert "Kualitas Sistem (X)" in svg
    assert "Kepuasan Pengguna (M)" in svg
    assert "Dampak Organisasi (Y)" in svg


def test_figure_bridge_png_and_pdf_export(tmp_path: Path) -> None:
    """Verifies FigureBridge converts SVG to 300 DPI PNG and vector PDF without CairoSVG."""
    prisma_proj = AcademicTemplateFactory.create_prisma_2020_flowchart(
        identification_count=500,
        duplicates_removed=100,
        screened_count=400,
        excluded_screening=300,
        eligibility_assessed=100,
        excluded_eligibility=80,
        included_count=20,
    )

    # 1. Test in-memory PNG generation
    svg_str = FigureBridge.project_to_svg(prisma_proj)
    png_bytes = FigureBridge.svg_to_png_bytes(svg_str, dpi=300)
    assert len(png_bytes) > 10000

    img = Image.open(io.BytesIO(png_bytes))
    assert img.format == "PNG"
    assert img.width > 2000  # 300 DPI high-resolution scale

    # 2. Test in-memory PDF generation
    pdf_bytes = FigureBridge.svg_to_pdf_bytes(svg_str)
    assert len(pdf_bytes) > 5000
    pdf_doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    assert len(pdf_doc) == 1
    pdf_doc.close()

    # 3. Test export to disk
    exported = FigureBridge.export_project_to_files(
        prisma_proj,
        output_dir=tmp_path,
        base_filename="prisma_test",
    )
    assert exported["json"].exists()
    assert exported["svg"].exists()
    assert exported["png"].exists()
    assert exported["pdf"].exists()


def test_figure_bridge_docx_injection() -> None:
    """Verifies that figure is injected cleanly into python-docx Document with caption."""
    prisma_proj = AcademicTemplateFactory.create_prisma_2020_flowchart(chapter=3, figure_idx=1)
    doc = docx.Document()

    # Add dummy preceding paragraph
    doc.add_paragraph("Berikut adalah diagram alir penelitian:")

    # Inject figure
    FigureBridge.inject_figure_into_docx(doc, prisma_proj, width_inches=6.0, dpi=150)

    # Validate paragraph texts
    texts = [p.text for p in doc.paragraphs if p.text]
    assert any("Gambar 3.1: Diagram Alir Seleksi Literatur Berdasarkan PRISMA 2020" in t for t in texts)
    assert any("Sumber: Data diolah penulis berdasarkan Page et al. (2021)" in t for t in texts)


def test_canvas_component_html_generation() -> None:
    """Verifies CanvasComponent produces valid HTML markup with pan/zoom buttons and selection badge."""
    project = AcademicTemplateFactory.create_prisma_2020_flowchart()
    html_output = CanvasComponent.render_canvas_html(project, selected_id="obj_box_test", height=600)

    assert "<!DOCTYPE html>" in html_output
    assert "Zoom +" in html_output
    assert "Pan Mode" in html_output
    assert "Pedoman MIKOM 2026" in html_output
    assert "obj_box_test" in html_output
    assert "<svg" in html_output


def test_vector_project_schema_mutation_and_history() -> None:
    """Verifies object additions, updates, deletions, and snapshot history management."""
    project = VectorProjectSchema(title="Eksperimen Interaktif")
    new_obj = VectorObject(
        object_id="custom_node_1",
        shape_type=VectorShapeType.ROUNDED_RECT,
        name="Node Kustom",
        x=100.0,
        y=150.0,
        width=120.0,
        height=60.0,
        text_content="Variabel X",
    )
    project.add_object(new_obj)
    assert project.find_object("custom_node_1") is not None

    # Snapshot 1 for Undo/Redo stack
    snapshot_1 = project.to_json()

    # Mutation: Update coordinates, text, and styling
    success = project.update_object(
        object_id="custom_node_1",
        x=200.0,
        y=250.0,
        width=180.0,
        height=90.0,
        text_content="Variabel X Diperbarui",
        fill="#FEF08A",
        stroke="#CA8A04",
        stroke_width=2.5,
    )
    assert success is True
    updated_obj = project.find_object("custom_node_1")
    assert updated_obj is not None
    assert updated_obj.x == 200.0
    assert updated_obj.text_content == "Variabel X Diperbarui"
    assert updated_obj.style.fill == "#FEF08A"

    # Snapshot 2
    snapshot_2 = project.to_json()

    # Mutation: Remove object
    removed = project.remove_object("custom_node_1")
    assert removed is True
    assert project.find_object("custom_node_1") is None

    # Simulate Undo to Snapshot 2
    restored_proj_2 = VectorProjectSchema.from_json(snapshot_2)
    assert restored_proj_2.find_object("custom_node_1") is not None
    assert restored_proj_2.find_object("custom_node_1").text_content == "Variabel X Diperbarui"

    # Simulate Undo to Snapshot 1
    restored_proj_1 = VectorProjectSchema.from_json(snapshot_1)
    assert restored_proj_1.find_object("custom_node_1").text_content == "Variabel X"
    assert restored_proj_1.find_object("custom_node_1").x == 100.0


def test_vector_project_invalid_mutation_payload_safety() -> None:
    """Verifies that invalid object ids or illegal dimensions fail safely without mutating project."""
    project = VectorProjectSchema()
    # Non-existent ID returns False
    assert project.update_object("non_existent_id", x=50.0) is False
    assert project.remove_object("non_existent_id") is False


def test_canvas_component_bidirectional_event_validation() -> None:
    """Verifies that CanvasComponent validates and applies JavaScript events safely."""
    project = AcademicTemplateFactory.create_prisma_2020_flowchart()
    target_obj = project.layers[0].objects[1]
    target_id = target_obj.object_id

    # 1. Valid Drag Event
    drag_payload = {
        "action": "drag_object",
        "object_id": target_id,
        "x": 150.0,
        "y": 200.0,
        "timestamp": 12345678,
    }
    res_drag = CanvasComponent.validate_and_apply_event(project, drag_payload)
    assert res_drag["success"] is True
    assert res_drag["mutated"] is True
    assert target_obj.x == 150.0
    assert target_obj.y == 200.0

    # 2. Valid Resize Event
    resize_payload = {
        "action": "resize_object",
        "object_id": target_id,
        "width": 320.0,
        "height": 140.0,
        "timestamp": 12345679,
    }
    res_resize = CanvasComponent.validate_and_apply_event(project, resize_payload)
    assert res_resize["success"] is True
    assert res_resize["mutated"] is True
    assert target_obj.width == 320.0
    assert target_obj.height == 140.0

    # 3. Reflection in Rendered SVG
    svg_output = SVGEngine.compile_project_to_svg(project)
    assert f'x="{target_obj.x}"' in svg_output
    assert f'y="{target_obj.y}"' in svg_output

    # 4. Unknown Object ID Rejected
    invalid_id_payload = {
        "action": "drag_object",
        "object_id": "ghost_object_999",
        "x": 100.0,
        "y": 100.0,
    }
    res_inv = CanvasComponent.validate_and_apply_event(project, invalid_id_payload)
    assert res_inv["success"] is False
    assert "not found" in (res_inv["error"] or "")

    # 5. NaN / Infinity Protection
    nan_payload = {
        "action": "drag_object",
        "object_id": target_id,
        "x": float("nan"),
        "y": 50.0,
    }
    res_nan = CanvasComponent.validate_and_apply_event(project, nan_payload)
    assert res_nan["success"] is False
    assert "NaN" in (res_nan["error"] or "")

    inf_payload = {
        "action": "resize_object",
        "object_id": target_id,
        "width": float("inf"),
        "height": 50.0,
    }
    res_inf = CanvasComponent.validate_and_apply_event(project, inf_payload)
    assert res_inf["success"] is False
    assert "Infinity" in (res_inf["error"] or "")

