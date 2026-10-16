"""Vector Design Studio Package.

Provides a robust, scientific vector design and diagramming engine for AI Thesis Generator:
- Document Schema & Versioning (VectorProjectSchema, VectorLayer, VectorObject)
- W3C SVG Engine (SVGEngine)
- Scientific Diagram Templates (PRISMA 2020, Conceptual Framework, Methodology)
- High-Resolution Figure Bridge for DOCX / PDF injection (FigureBridge)
"""

from core.vector_studio.academic_templates import AcademicTemplateFactory
from core.vector_studio.document_schema import (
    FigureAttribution,
    Point,
    TypographyStyle,
    VectorLayer,
    VectorObject,
    VectorProjectSchema,
    VectorShapeType,
    VectorStyle,
)
from core.vector_studio.svg_engine import SVGEngine

__all__ = [
    "AcademicTemplateFactory",
    "FigureAttribution",
    "Point",
    "SVGEngine",
    "TypographyStyle",
    "VectorLayer",
    "VectorObject",
    "VectorProjectSchema",
    "VectorShapeType",
    "VectorStyle",
]
