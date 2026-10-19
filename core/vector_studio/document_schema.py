"""Vector Design Studio Document Schema & Data Models.

Versioned, reproducible JSON document schema for editable academic vector projects.
Strictly separates canvas state, document schema, styling, and figure attribution.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class VectorShapeType(str, Enum):
    RECTANGLE = "rectangle"
    ROUNDED_RECT = "rounded_rectangle"
    ELLIPSE = "ellipse"
    CIRCLE = "circle"
    LINE = "line"
    BEZIER_PATH = "bezier_path"
    POLYGON = "polygon"
    TEXT = "text"
    GROUP = "group"
    CONNECTOR_ARROW = "connector_arrow"


class AlignmentType(str, Enum):
    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"
    TOP = "top"
    MIDDLE = "middle"
    BOTTOM = "bottom"


@dataclass
class Point:
    x: float
    y: float

    def to_dict(self) -> dict[str, float]:
        return {"x": self.x, "y": self.y}


@dataclass
class VectorStyle:
    fill: str = "#ffffff"
    stroke: str = "#0D1424"
    stroke_width: float = 1.5
    stroke_dasharray: str | None = None  # e.g., "5,5" for dashed
    opacity: float = 1.0
    fill_opacity: float = 1.0
    stroke_opacity: float = 1.0
    line_cap: str = "round"  # butt, round, square
    line_join: str = "round"  # miter, round, bevel
    has_shadow: bool = False
    shadow_color: str = "rgba(0, 0, 0, 0.15)"
    shadow_blur: float = 4.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class TypographyStyle:
    font_family: str = "Times New Roman"  # MIKOM 2026 standard
    font_size: float = 12.0
    font_weight: str = "normal"  # normal, bold
    font_style: str = "normal"  # normal, italic
    text_anchor: str = "middle"  # start, middle, end
    line_height: float = 1.4

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class VectorObject:
    object_id: str = field(default_factory=lambda: f"obj_{uuid.uuid4().hex[:8]}")
    shape_type: VectorShapeType = VectorShapeType.RECTANGLE
    name: str = "Object"
    x: float = 0.0
    y: float = 0.0
    width: float = 100.0
    height: float = 60.0
    rotation: float = 0.0  # degrees
    points: list[Point] = field(default_factory=list)
    path_data: str | None = None  # SVG path 'd' string
    text_content: str | None = None
    style: VectorStyle = field(default_factory=VectorStyle)
    typography: TypographyStyle = field(default_factory=TypographyStyle)
    is_locked: bool = False
    is_visible: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        res = asdict(self)
        res["shape_type"] = self.shape_type.value
        return res

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> VectorObject:
        d = dict(data)
        d["shape_type"] = VectorShapeType(d.get("shape_type", "rectangle"))
        if "style" in d and isinstance(d["style"], dict):
            d["style"] = VectorStyle(**d["style"])
        if "typography" in d and isinstance(d["typography"], dict):
            d["typography"] = TypographyStyle(**d["typography"])
        if "points" in d and isinstance(d["points"], list):
            d["points"] = [Point(**pt) if isinstance(pt, dict) else pt for pt in d["points"]]
        return cls(**d)


@dataclass
class VectorLayer:
    layer_id: str = field(default_factory=lambda: f"layer_{uuid.uuid4().hex[:6]}")
    name: str = "Layer 1"
    is_visible: bool = True
    is_locked: bool = False
    opacity: float = 1.0
    objects: list[VectorObject] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "layer_id": self.layer_id,
            "name": self.name,
            "is_visible": self.is_visible,
            "is_locked": self.is_locked,
            "opacity": self.opacity,
            "objects": [obj.to_dict() for obj in self.objects],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> VectorLayer:
        objs = [VectorObject.from_dict(o) for o in data.get("objects", [])]
        return cls(
            layer_id=data.get("layer_id", f"layer_{uuid.uuid4().hex[:6]}"),
            name=data.get("name", "Layer"),
            is_visible=data.get("is_visible", True),
            is_locked=data.get("is_locked", False),
            opacity=float(data.get("opacity", 1.0)),
            objects=objs,
        )


@dataclass
class FigureAttribution:
    """Pedoman Penulisan Tesis MIKOM 2026 Figure Standard."""

    chapter_number: int = 3
    figure_index: int = 1
    title: str = "Diagram Alur Penelitian"
    source: str = "Data diolah penulis (2026)"
    caption_notes: str | None = None

    @property
    def figure_label(self) -> str:
        return f"Gambar {self.chapter_number}.{self.figure_index}"

    @property
    def full_heading(self) -> str:
        return f"{self.figure_label}: {self.title}"

    @property
    def full_source_line(self) -> str:
        return f"Sumber: {self.source}"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class VectorProjectSchema:
    """Root project schema for saving, reopening, and versioning vector projects."""

    schema_version: str = "1.0.0"
    project_id: str = field(default_factory=lambda: f"proj_{uuid.uuid4().hex[:8]}")
    title: str = "Academic Thesis Figure"
    canvas_width: float = 800.0
    canvas_height: float = 600.0
    dpi: int = 300  # High-resolution standard
    background_color: str = "#ffffff"
    layers: list[VectorLayer] = field(default_factory=lambda: [VectorLayer()])
    attribution: FigureAttribution = field(default_factory=FigureAttribution)
    created_at: str = "2026-10-16T00:00:00Z"
    updated_at: str = "2026-10-16T00:00:00Z"
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "project_id": self.project_id,
            "title": self.title,
            "canvas_width": self.canvas_width,
            "canvas_height": self.canvas_height,
            "dpi": self.dpi,
            "background_color": self.background_color,
            "layers": [layer.to_dict() for layer in self.layers],
            "attribution": self.attribution.to_dict(),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "metadata": self.metadata,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_json(cls, json_str: str) -> VectorProjectSchema:
        data = json.loads(json_str)
        layers = [VectorLayer.from_dict(layer_dict) for layer_dict in data.get("layers", [])]
        attrib_data = data.get("attribution", {})
        attribution = FigureAttribution(**attrib_data) if attrib_data else FigureAttribution()
        return cls(
            schema_version=data.get("schema_version", "1.0.0"),
            project_id=data.get("project_id", f"proj_{uuid.uuid4().hex[:8]}"),
            title=data.get("title", "Academic Thesis Figure"),
            canvas_width=float(data.get("canvas_width", 800.0)),
            canvas_height=float(data.get("canvas_height", 600.0)),
            dpi=int(data.get("dpi", 300)),
            background_color=data.get("background_color", "#ffffff"),
            layers=layers,
            attribution=attribution,
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
            metadata=data.get("metadata", {}),
        )

    def find_object(self, object_id: str) -> VectorObject | None:
        for layer in self.layers:
            for obj in layer.objects:
                if obj.object_id == object_id:
                    return obj
        return None

    def add_object(self, obj: VectorObject, layer_index: int = 0) -> None:
        if not self.layers:
            self.layers.append(VectorLayer())
        idx = max(0, min(layer_index, len(self.layers) - 1))
        self.layers[idx].objects.append(obj)

    def remove_object(self, object_id: str) -> bool:
        """Removes an object by id across all layers."""
        for layer in self.layers:
            initial_len = len(layer.objects)
            layer.objects = [o for o in layer.objects if o.object_id != object_id]
            if len(layer.objects) < initial_len:
                return True
        return False

    def update_object(
        self,
        object_id: str,
        x: float | None = None,
        y: float | None = None,
        width: float | None = None,
        height: float | None = None,
        text_content: str | None = None,
        fill: str | None = None,
        stroke: str | None = None,
        stroke_width: float | None = None,
    ) -> bool:
        """Updates geometry, text, or style attributes of an object safely."""
        obj = self.find_object(object_id)
        if not obj:
            return False
        if x is not None:
            obj.x = float(x)
        if y is not None:
            obj.y = float(y)
        if width is not None and width > 0:
            obj.width = float(width)
        if height is not None and height > 0:
            obj.height = float(height)
        if text_content is not None:
            obj.text_content = text_content
        if fill is not None:
            obj.style.fill = fill
        if stroke is not None:
            obj.style.stroke = stroke
        if stroke_width is not None and stroke_width >= 0:
            obj.style.stroke_width = float(stroke_width)
        return True

    def all_objects(self) -> list[VectorObject]:
        """Returns flat list of all objects across visible layers."""
        objs: list[VectorObject] = []
        for layer in self.layers:
            objs.extend(layer.objects)
        return objs

    def to_doclaynet_elements(self, page_number: int = 1) -> list[Any]:
        """Converts vector project objects and attribution into DocLayNetElement representations.

        Uses lazy import of core.clones.doclaynet_layout to prevent circular dependencies.
        Maps:
        - Shapes with text / headers -> Section-Header / Text / Formula
        - Vector objects overall -> Picture / Section-Header / List-Item / Text
        - FigureAttribution heading -> Caption (bound to the overall figure)
        """
        from core.clones.doclaynet_layout import (
            BoundingBox,
            DocLayNetCategory,
            DocLayNetElement,
        )

        elements: list[DocLayNetElement] = []

        # 1. Whole Diagram Composite Bounding Box as a PICTURE element
        elements.append(
            DocLayNetElement(
                element_id=f"fig_{self.project_id}",
                category=DocLayNetCategory.PICTURE,
                bbox=BoundingBox(
                    x=0.0,
                    y=0.0,
                    width=float(self.canvas_width),
                    height=float(self.canvas_height),
                ),
                page_number=page_number,
                confidence=1.0,
                text_content=self.title,
                metadata={"title": self.title, "dpi": self.dpi},
            )
        )

        # 2. Figure Caption element from Attribution (MIKOM 2026 standard)
        if self.attribution:
            attrib = self.attribution
            # Placed standardly at bottom or top with standard height 20pt
            elements.append(
                DocLayNetElement(
                    element_id=f"cap_{self.project_id}",
                    category=DocLayNetCategory.CAPTION,
                    bbox=BoundingBox(
                        x=0.0,
                        y=float(self.canvas_height) + 12.0,  # 12pt spatial distance
                        width=float(self.canvas_width),
                        height=24.0,
                    ),
                    page_number=page_number,
                    confidence=1.0,
                    text_content=attrib.full_heading,
                    metadata={"source": attrib.source, "label": attrib.figure_label},
                )
            )

        # 3. Internal Vector Objects
        for layer in self.layers:
            if not layer.is_visible:
                continue
            for obj in layer.objects:
                if not obj.is_visible:
                    continue

                cat = DocLayNetCategory.TEXT
                text = (obj.text_content or "").strip()

                if obj.shape_type == VectorShapeType.TEXT:
                    if obj.typography.font_size >= 14.0 or (obj.typography.font_size >= 11.0 and obj.typography.font_weight == "bold"):
                        cat = DocLayNetCategory.SECTION_HEADER
                    else:
                        cat = DocLayNetCategory.TEXT
                elif obj.shape_type in (VectorShapeType.RECTANGLE, VectorShapeType.ROUNDED_RECT):
                    if text:
                        if text.lower().startswith(("gambar ", "tabel ")):
                            cat = DocLayNetCategory.CAPTION
                        elif text.startswith(("- ", "• ", "* ")):
                            cat = DocLayNetCategory.LIST_ITEM
                        elif "formula" in text.lower() or "\\begin" in text:
                            cat = DocLayNetCategory.FORMULA
                        elif obj.typography.font_weight == "bold" and len(text) < 80:
                            cat = DocLayNetCategory.SECTION_HEADER
                        else:
                            cat = DocLayNetCategory.TEXT
                    else:
                        # Empty rectangle / background card
                        cat = DocLayNetCategory.SECTION_HEADER if "section" in obj.name.lower() else DocLayNetCategory.TEXT

                elements.append(
                    DocLayNetElement(
                        element_id=obj.object_id,
                        category=cat,
                        bbox=BoundingBox(
                            x=float(obj.x),
                            y=float(obj.y),
                            width=float(obj.width),
                            height=float(obj.height),
                        ),
                        page_number=page_number,
                        confidence=1.0,
                        text_content=text,
                        metadata={
                            "layer": layer.name,
                            "shape": obj.shape_type.value,
                            "name": obj.name,
                        },
                    )
                )

        return elements

