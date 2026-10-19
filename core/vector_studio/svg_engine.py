"""Vector Design Studio SVG Engine.

Compiles VectorProjectSchema into standards-compliant W3C SVG XML strings and files.
Supports defs, markers, arrowheads, Bézier curves, layer groupings, and safe parsing.
"""

from __future__ import annotations

import html
from pathlib import Path

from core.vector_studio.document_schema import (
    FigureAttribution,
    VectorObject,
    VectorProjectSchema,
    VectorShapeType,
)


class SVGEngine:
    """Compiles vector objects into clean, scalable W3C SVG strings."""

    @classmethod
    def compile_project_to_svg(
        cls,
        project: VectorProjectSchema,
        include_attribution: bool = False,
    ) -> str:
        """Converts an entire VectorProjectSchema into an SVG XML document."""
        w = project.canvas_width
        h = project.canvas_height

        svg_parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" '
            f'width="{w}" height="{h}" data-project-id="{project.project_id}">'
        ]

        # 1. Defs: Markers (Arrowheads) and Gradients
        svg_parts.append(cls._build_defs())

        # 2. Background
        if project.background_color and project.background_color.lower() != "transparent":
            svg_parts.append(
                f'  <rect width="{w}" height="{h}" fill="{project.background_color}" />'
            )

        # 3. Layers & Objects
        for layer in project.layers:
            if not layer.is_visible:
                continue
            layer_opacity = layer.opacity
            svg_parts.append(
                f'  <g id="{layer.layer_id}" data-layer-name="{html.escape(layer.name)}" '
                f'opacity="{layer_opacity}">'
            )
            for obj in layer.objects:
                if not obj.is_visible:
                    continue
                svg_parts.append(cls._render_object(obj))
            svg_parts.append("  </g>")

        # 4. Optional Figure Attribution (MIKOM 2026 Academic Standard)
        if include_attribution and project.attribution:
            svg_parts.append(cls._render_attribution(project.attribution, w, h))

        svg_parts.append("</svg>")
        return "\n".join(svg_parts)

    @staticmethod
    def _build_defs() -> str:
        return """  <defs>
    <!-- Academic Arrow Marker (Start) -->
    <marker id="arrow-start" viewBox="0 0 10 10" refX="5" refY="5"
            markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 10 0 L 0 5 L 10 10 z" fill="#142A4A" />
    </marker>
    <!-- Academic Arrow Marker (End) -->
    <marker id="arrow-end" viewBox="0 0 10 10" refX="5" refY="5"
            markerWidth="6" markerHeight="6" orient="auto">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="#142A4A" />
    </marker>
    <!-- Electric Cyan Arrow Marker (End) -->
    <marker id="arrow-cyan" viewBox="0 0 10 10" refX="5" refY="5"
            markerWidth="6" markerHeight="6" orient="auto">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="#58D8FF" />
    </marker>
    <!-- Box Shadow Filter -->
    <filter id="soft-shadow" x="-10%" y="-10%" width="130%" height="130%">
      <feDropShadow dx="0" dy="3" stdDeviation="4" flood-color="rgba(0,0,0,0.12)" />
    </filter>
  </defs>"""

    @classmethod
    def _render_object(cls, obj: VectorObject) -> str:
        s = obj.style
        ty = obj.typography
        stroke_attr = f'stroke="{s.stroke}" stroke-width="{s.stroke_width}"'
        if s.stroke_dasharray:
            stroke_attr += f' stroke-dasharray="{s.stroke_dasharray}"'
        fill_attr = f'fill="{s.fill}" fill-opacity="{s.fill_opacity}"'
        opacity_attr = f'opacity="{s.opacity}"'
        filter_attr = 'filter="url(#soft-shadow)"' if s.has_shadow else ''

        transform_attr = ""
        if obj.rotation != 0:
            cx = obj.x + obj.width / 2
            cy = obj.y + obj.height / 2
            transform_attr = f'transform="rotate({obj.rotation} {cx} {cy})"'

        t = obj.shape_type

        if t in (VectorShapeType.RECTANGLE, VectorShapeType.ROUNDED_RECT):
            rx = 8 if t == VectorShapeType.ROUNDED_RECT else 0
            rect_xml = (
                f'    <rect id="{obj.object_id}" x="{obj.x}" y="{obj.y}" '
                f'width="{obj.width}" height="{obj.height}" rx="{rx}" ry="{rx}" '
                f'{fill_attr} {stroke_attr} {opacity_attr} {filter_attr} {transform_attr} />'
            )
            # If rectangle has text content, render centered text inside it
            if obj.text_content:
                tx = obj.x + obj.width / 2
                ty_pos = obj.y + obj.height / 2 + ty.font_size * 0.35
                text_xml = (
                    f'    <text x="{tx}" y="{ty_pos}" text-anchor="{ty.text_anchor}" '
                    f'font-family="{ty.font_family}" font-size="{ty.font_size}" '
                    f'font-weight="{ty.font_weight}" font-style="{ty.font_style}" '
                    f'fill="{s.stroke}">{html.escape(obj.text_content)}</text>'
                )
                return f"{rect_xml}\n{text_xml}"
            return rect_xml

        if t in (VectorShapeType.ELLIPSE, VectorShapeType.CIRCLE):
            cx = obj.x + obj.width / 2
            cy = obj.y + obj.height / 2
            rx = obj.width / 2
            ry = obj.height / 2
            ellipse_xml = (
                f'    <ellipse id="{obj.object_id}" cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" '
                f'{fill_attr} {stroke_attr} {opacity_attr} {filter_attr} {transform_attr} />'
            )
            if obj.text_content:
                ty_pos = cy + ty.font_size * 0.35
                text_xml = (
                    f'    <text x="{cx}" y="{ty_pos}" text-anchor="{ty.text_anchor}" '
                    f'font-family="{ty.font_family}" font-size="{ty.font_size}" '
                    f'font-weight="{ty.font_weight}" fill="{s.stroke}">'
                    f'{html.escape(obj.text_content)}</text>'
                )
                return f"{ellipse_xml}\n{text_xml}"
            return ellipse_xml

        if t == VectorShapeType.LINE:
            x1, y1 = obj.x, obj.y
            x2, y2 = obj.x + obj.width, obj.y + obj.height
            if len(obj.points) >= 2:
                x1, y1 = obj.points[0].x, obj.points[0].y
                x2, y2 = obj.points[1].x, obj.points[1].y
            return (
                f'    <line id="{obj.object_id}" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
                f'{stroke_attr} {opacity_attr} stroke-linecap="{s.line_cap}" />'
            )

        if t == VectorShapeType.CONNECTOR_ARROW:
            x1, y1 = obj.x, obj.y
            x2, y2 = obj.x + obj.width, obj.y + obj.height
            if len(obj.points) >= 2:
                x1, y1 = obj.points[0].x, obj.points[0].y
                x2, y2 = obj.points[1].x, obj.points[1].y
            marker = 'marker-end="url(#arrow-cyan)"' if "#58" in s.stroke.lower() else 'marker-end="url(#arrow-end)"'
            line_xml = (
                f'    <line id="{obj.object_id}" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
                f'{stroke_attr} {opacity_attr} {marker} />'
            )
            if obj.text_content:
                mid_x = (x1 + x2) / 2
                mid_y = (y1 + y2) / 2 - 8
                text_xml = (
                    f'    <text x="{mid_x}" y="{mid_y}" text-anchor="middle" '
                    f'font-family="{ty.font_family}" font-size="{ty.font_size}" '
                    f'font-weight="bold" fill="{s.stroke}">{html.escape(obj.text_content)}</text>'
                )
                return f"{line_xml}\n{text_xml}"
            return line_xml

        if t == VectorShapeType.BEZIER_PATH:
            d = obj.path_data or ""
            if not d and len(obj.points) >= 3:
                # Construct quadratic Bézier
                d = f"M {obj.points[0].x} {obj.points[0].y} Q {obj.points[1].x} {obj.points[1].y} {obj.points[2].x} {obj.points[2].y}"
            return (
                f'    <path id="{obj.object_id}" d="{d}" {fill_attr} {stroke_attr} '
                f'{opacity_attr} stroke-linejoin="{s.line_join}" />'
            )

        if t == VectorShapeType.POLYGON:
            pts_str = " ".join(f"{p.x},{p.y}" for p in obj.points)
            return (
                f'    <polygon id="{obj.object_id}" points="{pts_str}" '
                f'{fill_attr} {stroke_attr} {opacity_attr} />'
            )

        if t == VectorShapeType.TEXT:
            return (
                f'    <text id="{obj.object_id}" x="{obj.x}" y="{obj.y}" '
                f'text-anchor="{ty.text_anchor}" font-family="{ty.font_family}" '
                f'font-size="{ty.font_size}" font-weight="{ty.font_weight}" '
                f'font-style="{ty.font_style}" fill="{s.fill}" {opacity_attr}>'
                f'{html.escape(obj.text_content or "")}</text>'
            )

        return f'    <!-- Unhandled shape: {t} -->'

    @staticmethod
    def _render_attribution(attrib: FigureAttribution, width: float, height: float) -> str:
        """Renders MIKOM 2026 standard figure numbering and source line."""
        title_y = 24
        source_y = height - 12
        return f"""  <!-- MIKOM 2026 Academic Figure Attribution -->
  <text x="{width / 2}" y="{title_y}" text-anchor="middle"
        font-family="Times New Roman" font-size="12" font-weight="bold" fill="#0D1424">
    {html.escape(attrib.full_heading)}
  </text>
  <text x="20" y="{source_y}" text-anchor="start"
        font-family="Times New Roman" font-size="10" font-style="italic" fill="#64748B">
    {html.escape(attrib.full_source_line)}
  </text>"""

    @classmethod
    def save_svg(cls, project: VectorProjectSchema, output_path: str | Path, include_attribution: bool = False) -> Path:
        p = Path(output_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        content = cls.compile_project_to_svg(project, include_attribution=include_attribution)
        p.write_text(content, encoding="utf-8")
        return p
