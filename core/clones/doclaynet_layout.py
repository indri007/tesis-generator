"""DocLayNet Academic Document Layout Analysis & Element Detection Clone.

A deterministic, high-performance layout detection module inspired by IBM's DocLayNet:
- Ground-truth academic document layout segmentation across standard scientific categories:
  1. Title
  2. Section-Header
  3. Paragraph / Text
  4. Table
  5. Picture / Figure
  6. Caption
  7. Formula / Equation
  8. List-Item
  9. Footnote
  10. Page-Header
  11. Page-Footer
- Bounding box collision, reading-order reconstruction, and compliance verification
  with academic thesis formatting standards (e.g. Pedoman MIKOM 2026).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class DocLayNetCategory(str, Enum):
    TITLE = "Title"
    SECTION_HEADER = "Section-Header"
    TEXT = "Text"
    TABLE = "Table"
    PICTURE = "Picture"
    CAPTION = "Caption"
    FORMULA = "Formula"
    LIST_ITEM = "List-Item"
    FOOTNOTE = "Footnote"
    PAGE_HEADER = "Page-Header"
    PAGE_FOOTER = "Page-Footer"


@dataclass
class BoundingBox:
    x: float
    y: float
    width: float
    height: float

    @property
    def x2(self) -> float:
        return self.x + self.width

    @property
    def y2(self) -> float:
        return self.y + self.height

    @property
    def area(self) -> float:
        return max(0.0, self.width) * max(0.0, self.height)

    def intersects(self, other: BoundingBox) -> bool:
        return not (self.x2 < other.x or self.x > other.x2 or self.y2 < other.y or self.y > other.y2)

    def intersection_over_union(self, other: BoundingBox) -> float:
        ix1 = max(self.x, other.x)
        iy1 = max(self.y, other.y)
        ix2 = min(self.x2, other.x2)
        iy2 = min(self.y2, other.y2)

        iw = max(0.0, ix2 - ix1)
        ih = max(0.0, iy2 - iy1)
        intersection = iw * ih

        union = self.area + other.area - intersection
        if union <= 0:
            return 0.0
        return intersection / union

    def to_dict(self) -> dict[str, float]:
        return {"x": self.x, "y": self.y, "width": self.width, "height": self.height}


@dataclass
class DocLayNetElement:
    element_id: str
    category: DocLayNetCategory
    bbox: BoundingBox
    page_number: int
    confidence: float = 1.0
    text_content: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        res = asdict(self)
        res["category"] = self.category.value
        return res


@dataclass
class LayoutAnalysisReport:
    total_elements: int
    category_counts: dict[str, int]
    elements_by_page: dict[int, list[DocLayNetElement]]
    figure_caption_pairs: list[dict[str, Any]]
    table_caption_pairs: list[dict[str, Any]]
    formatting_warnings: list[str]
    layout_score: float  # 0.0 - 100.0


class DocLayNetClone:
    """Document Layout Analysis engine conforming to DocLayNet taxonomy."""

    CATEGORIES = [c.value for c in DocLayNetCategory]

    @classmethod
    def classify_text_block(cls, text: str, font_size: float = 12.0, is_bold: bool = False) -> DocLayNetCategory:
        """Determines layout category from textual characteristics and typography."""
        stripped = text.strip()
        lower = stripped.lower()

        # Figure / Table Captions
        if lower.startswith(("gambar ", "figure ", "fig. ")) or lower.startswith(("tabel ", "table ")):
            return DocLayNetCategory.CAPTION

        # Formulas
        if lower.startswith(("\\begin{equation}", "$$", "formula", "persamaan ")):
            return DocLayNetCategory.FORMULA

        # Titles and Section Headers
        if font_size >= 14.0 or (font_size >= 12.0 and is_bold and len(stripped) < 120 and "\n" not in stripped):
            if lower.startswith(("bab ", "chapter ")) or font_size >= 16.0:
                return DocLayNetCategory.TITLE
            return DocLayNetCategory.SECTION_HEADER

        # List items
        if stripped.startswith(("- ", "• ", "* ", "1. ", "2. ", "a. ", "b. ")):
            return DocLayNetCategory.LIST_ITEM

        # Default standard body text
        return DocLayNetCategory.TEXT

    @classmethod
    def analyze_document_layout(
        cls,
        elements: list[DocLayNetElement],
        page_width: float = 595.0,  # A4 width in points
        page_height: float = 842.0,  # A4 height in points
        margin_left: float = 113.38,  # 4.0 cm = ~113.38 pt
        margin_right: float = 85.04,  # 3.0 cm = ~85.04 pt
    ) -> LayoutAnalysisReport:
        """Performs full DocLayNet layout segmentation, spatial linking, and thesis compliance checks."""
        category_counts: dict[str, int] = {c.value: 0 for c in DocLayNetCategory}
        elements_by_page: dict[int, list[DocLayNetElement]] = {}
        warnings: list[str] = []

        # Sort elements by page then reading order (top-to-bottom, left-to-right)
        sorted_elements = sorted(elements, key=lambda e: (e.page_number, e.bbox.y, e.bbox.x))

        for el in sorted_elements:
            cat_name = el.category.value
            category_counts[cat_name] = category_counts.get(cat_name, 0) + 1
            elements_by_page.setdefault(el.page_number, []).append(el)

            # Check Margin Violations
            if el.bbox.x < (margin_left - 10.0):
                warnings.append(
                    f"Halaman {el.page_number}: Elemen '{el.element_id}' ({cat_name}) melebihi batas margin kiri 4.0 cm."
                )
            if (el.bbox.x2) > (page_width - margin_right + 10.0):
                warnings.append(
                    f"Halaman {el.page_number}: Elemen '{el.element_id}' ({cat_name}) melebihi batas margin kanan 3.0 cm."
                )

        # Spatial Pairing: Match Pictures and Tables with their nearest Captions
        fig_caption_pairs: list[dict[str, Any]] = []
        table_caption_pairs: list[dict[str, Any]] = []

        for p_num, p_elements in elements_by_page.items():
            pictures = [e for e in p_elements if e.category == DocLayNetCategory.PICTURE]
            tables = [e for e in p_elements if e.category == DocLayNetCategory.TABLE]
            captions = [e for e in p_elements if e.category == DocLayNetCategory.CAPTION]

            for pic in pictures:
                # Find caption closest to picture (above or below within 60 points)
                closest_cap = None
                min_dist = float("inf")
                for cap in captions:
                    dist = abs(cap.bbox.y - pic.bbox.y2)  # below picture
                    if dist < min_dist and dist < 80.0:
                        min_dist = dist
                        closest_cap = cap
                if closest_cap:
                    fig_caption_pairs.append({
                        "picture_id": pic.element_id,
                        "caption_id": closest_cap.element_id,
                        "caption_text": closest_cap.text_content,
                        "distance_pt": round(min_dist, 2),
                    })
                else:
                    warnings.append(f"Halaman {p_num}: Gambar '{pic.element_id}' tidak memiliki keterangan caption di dekatnya.")

            for tbl in tables:
                # Tables in Indonesian thesis standards usually have captions above
                closest_cap = None
                min_dist = float("inf")
                for cap in captions:
                    dist = abs(tbl.bbox.y - cap.bbox.y2)  # above table
                    if dist < min_dist and dist < 60.0:
                        min_dist = dist
                        closest_cap = cap
                if closest_cap:
                    table_caption_pairs.append({
                        "table_id": tbl.element_id,
                        "caption_id": closest_cap.element_id,
                        "caption_text": closest_cap.text_content,
                    })

        # Calculate Compliance Score (100 - penalties)
        penalty = len(warnings) * 4.0
        score = max(0.0, min(100.0, 100.0 - penalty))

        return LayoutAnalysisReport(
            total_elements=len(sorted_elements),
            category_counts=category_counts,
            elements_by_page=elements_by_page,
            figure_caption_pairs=fig_caption_pairs,
            table_caption_pairs=table_caption_pairs,
            formatting_warnings=warnings,
            layout_score=round(score, 1),
        )
