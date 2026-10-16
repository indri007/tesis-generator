"""Bidirectional Interactive Vector Studio Component for Streamlit.

Provides real-time two-way communication between SVG canvas (JavaScript) and Python:
- Native Streamlit custom component declared via `st.components.v1.declare_component`.
- Handles visual drag, resize, and selection events via `Streamlit.setComponentValue()`.
- Validates all incoming payloads in Python (bounds, NaN/Infinity protection, object existence)
  before mutating VectorProjectSchema.
- Provides fallback to static HTML canvas rendering if custom component initialization is bypassed.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import streamlit.components.v1 as components

from core.vector_studio.document_schema import VectorProjectSchema
from core.vector_studio.svg_engine import SVGEngine

# Declare custom component with local static HTML bundle (Zero-npm, zero-CDN)
_FRONTEND_DIR = Path(__file__).parent / "frontend"
_vector_canvas_component = components.declare_component("vector_canvas_component", path=str(_FRONTEND_DIR))


class CanvasComponent:
    """Manages the bidirectional interactive vector canvas in Streamlit."""

    @classmethod
    def render_interactive_canvas(
        cls,
        project: VectorProjectSchema,
        selected_id: str | None = None,
        key: str = "vector_canvas_component",
    ) -> dict[str, Any] | None:
        """Renders bidirectional interactive canvas and returns JavaScript interaction event payload."""
        svg_content = SVGEngine.compile_project_to_svg(project, include_attribution=False)
        attrib = project.attribution

        component_value = _vector_canvas_component(
            svg_content=svg_content,
            title=attrib.full_heading if attrib else project.title,
            source=attrib.source if attrib else "",
            selected_id=selected_id or "",
            width=project.canvas_width,
            height=project.canvas_height,
            default=None,
            key=key,
        )
        return component_value

    @classmethod
    def render_canvas_html(
        cls,
        project: VectorProjectSchema,
        selected_id: str | None = None,
        height: int = 650,
    ) -> str:
        """Renders self-contained standalone HTML bundle for testing and offline fallback."""
        frontend_html = (_FRONTEND_DIR / "index.html").read_text(encoding="utf-8")
        svg_content = SVGEngine.compile_project_to_svg(project, include_attribution=False)
        attrib = project.attribution

        rendered = frontend_html.replace(
            '<div id="svgMount"></div>',
            f'<div id="svgMount">{svg_content}</div>',
        )
        if attrib:
            rendered = rendered.replace("Vector Canvas", attrib.full_heading)
            rendered = rendered.replace("Sumber: Standard MIKOM 2026", f"Sumber: {attrib.source}")
        if selected_id:
            rendered = rendered.replace('let activeSelectedId = null;', f'let activeSelectedId = "{selected_id}";')
        return rendered

    @classmethod
    def validate_and_apply_event(
        cls,
        project: VectorProjectSchema,
        event_payload: Any,
    ) -> dict[str, Any]:
        """Validates payload and mutates project safely in Python.

        Returns a dictionary:
        {
            "success": bool,
            "action": str,
            "object_id": str | None,
            "error": str | None,
            "mutated": bool,
        }
        """
        if not isinstance(event_payload, dict):
            return {"success": False, "action": "none", "object_id": None, "error": "Payload must be a dict", "mutated": False}

        action = event_payload.get("action")
        obj_id = event_payload.get("object_id")

        if not action or not isinstance(action, str):
            return {"success": False, "action": "unknown", "object_id": None, "error": "Missing action type", "mutated": False}

        if not obj_id or not isinstance(obj_id, str):
            return {"success": False, "action": action, "object_id": None, "error": "Missing object_id", "mutated": False}

        target_obj = project.find_object(obj_id)
        if not target_obj:
            return {"success": False, "action": action, "object_id": obj_id, "error": f"Object {obj_id} not found", "mutated": False}

        if action == "select_object":
            return {"success": True, "action": "select_object", "object_id": obj_id, "error": None, "mutated": False}

        if action == "drag_object":
            new_x = event_payload.get("x")
            new_y = event_payload.get("y")
            if not isinstance(new_x, (int, float)) or not isinstance(new_y, (int, float)):
                return {"success": False, "action": action, "object_id": obj_id, "error": "Coordinates must be numbers", "mutated": False}

            if math.isnan(new_x) or math.isinf(new_x) or math.isnan(new_y) or math.isinf(new_y):
                return {"success": False, "action": action, "object_id": obj_id, "error": "Coordinates cannot be NaN or Infinity", "mutated": False}

            # Constrain to reasonable canvas bounds
            bounded_x = max(-50.0, min(float(project.canvas_width) + 50.0, float(new_x)))
            bounded_y = max(-50.0, min(float(project.canvas_height) + 50.0, float(new_y)))

            target_obj.x = bounded_x
            target_obj.y = bounded_y
            return {"success": True, "action": "drag_object", "object_id": obj_id, "error": None, "mutated": True}

        if action == "resize_object":
            new_w = event_payload.get("width")
            new_h = event_payload.get("height")
            if not isinstance(new_w, (int, float)) or not isinstance(new_h, (int, float)):
                return {"success": False, "action": action, "object_id": obj_id, "error": "Dimensions must be numbers", "mutated": False}

            if math.isnan(new_w) or math.isinf(new_w) or math.isnan(new_h) or math.isinf(new_h):
                return {"success": False, "action": action, "object_id": obj_id, "error": "Dimensions cannot be NaN or Infinity", "mutated": False}

            # Minimum 15 pt, maximum 2x canvas size
            bounded_w = max(15.0, min(float(project.canvas_width) * 1.5, float(new_w)))
            bounded_h = max(15.0, min(float(project.canvas_height) * 1.5, float(new_h)))

            target_obj.width = bounded_w
            target_obj.height = bounded_h
            return {"success": True, "action": "resize_object", "object_id": obj_id, "error": None, "mutated": True}

        return {"success": False, "action": action, "object_id": obj_id, "error": f"Unsupported action {action}", "mutated": False}
