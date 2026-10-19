"""Academic Diagram Templates for Thesis Research.

Pre-engineered, editable templates complying with scientific reporting guidelines:
1. PRISMA 2020 Systematic Literature Review Flowchart (Page et al., 2021).
2. Conceptual Research Framework (Independent -> Mediating -> Dependent Variables with Hypotheses H1, H2, H3).
3. Thesis Methodology Workflow (5-Stage structured execution pipeline).
4. Social Network Analysis (SNA) / Bibliometric Topic Graph.
"""

from __future__ import annotations

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


class AcademicTemplateFactory:
    """Creates editable academic vector projects populated with scientific templates."""

    # ==========================================================================
    # 1. PRISMA 2020 FLOWCHART TEMPLATE
    # ==========================================================================
    @classmethod
    def create_prisma_2020_flowchart(
        cls,
        identification_count: int = 1250,
        duplicates_removed: int = 340,
        screened_count: int = 910,
        excluded_screening: int = 725,
        eligibility_assessed: int = 185,
        excluded_eligibility: int = 135,
        included_count: int = 50,
        chapter: int = 3,
        figure_idx: int = 1,
    ) -> VectorProjectSchema:
        """Constructs official PRISMA 2020 Flowchart as editable vector objects."""
        project = VectorProjectSchema(
            title="Diagram Alir Seleksi Literatur PRISMA 2020",
            canvas_width=900.0,
            canvas_height=750.0,
            attribution=FigureAttribution(
                chapter_number=chapter,
                figure_index=figure_idx,
                title="Diagram Alir Seleksi Literatur Berdasarkan PRISMA 2020",
                source="Data diolah penulis berdasarkan Page et al. (2021)",
            ),
        )
        layer = VectorLayer(name="PRISMA 2020 Diagram")

        # Color Tokens
        blue_fill = "#F0F7FF"
        blue_stroke = "#1E40AF"
        amber_fill = "#FFFBEB"
        amber_stroke = "#B45309"
        green_fill = "#ECFDF5"
        green_stroke = "#047857"
        section_fill = "#F8FAFC"
        section_stroke = "#94A3B8"

        # Section Backgrounds (Identification, Screening, Included)
        sections = [
            ("IDENTIFIKASI", 40, 60, 820, 160, section_fill, section_stroke),
            ("PENYARINGAN & KELAYAKAN", 40, 240, 820, 310, section_fill, section_stroke),
            ("DITERIMA", 40, 570, 820, 120, green_fill, green_stroke),
        ]
        for name, sx, sy, sw, sh, sfill, sstroke in sections:
            layer.objects.append(
                VectorObject(
                    shape_type=VectorShapeType.ROUNDED_RECT,
                    name=f"Section_{name}",
                    x=sx,
                    y=sy,
                    width=sw,
                    height=sh,
                    style=VectorStyle(fill=sfill, stroke=sstroke, stroke_width=1.0, stroke_dasharray="4,4"),
                    is_locked=True,
                )
            )
            # Section Header Tag
            layer.objects.append(
                VectorObject(
                    shape_type=VectorShapeType.TEXT,
                    name=f"Tag_{name}",
                    x=sx + 20,
                    y=sy + 24,
                    text_content=name,
                    typography=TypographyStyle(font_size=10, font_weight="bold", text_anchor="start"),
                    style=VectorStyle(fill=sstroke),
                )
            )

        # Stage 1: Identification Boxes
        # Database Records Box
        layer.objects.append(
            VectorObject(
                shape_type=VectorShapeType.ROUNDED_RECT,
                name="Box_Identification",
                x=80,
                y=95,
                width=320,
                height=90,
                text_content=f"Hasil pencarian basis data ilmiah\n(Scopus, WoS, Crossref, OpenAlex)\n(n = {identification_count})",
                style=VectorStyle(fill=blue_fill, stroke=blue_stroke, stroke_width=1.8, has_shadow=True),
                typography=TypographyStyle(font_size=11, font_weight="bold"),
            )
        )
        # Duplicate Removal Box
        layer.objects.append(
            VectorObject(
                shape_type=VectorShapeType.ROUNDED_RECT,
                name="Box_Duplicates",
                x=480,
                y=95,
                width=340,
                height=90,
                text_content=f"Duplikasi dihapus sebelum skrining:\n- Otomatis (Rayyan / DOI): n = {duplicates_removed}\n- Sisa catatan untuk skrining: n = {screened_count}",
                style=VectorStyle(fill=amber_fill, stroke=amber_stroke, stroke_width=1.5),
                typography=TypographyStyle(font_size=11),
            )
        )
        # Connector Identification -> Duplicate
        layer.objects.append(
            VectorObject(
                shape_type=VectorShapeType.CONNECTOR_ARROW,
                name="Arrow_Id_to_Dup",
                x=400,
                y=140,
                width=80,
                height=0,
                points=[Point(400, 140), Point(480, 140)],
                style=VectorStyle(stroke=blue_stroke, stroke_width=2.0),
            )
        )

        # Stage 2: Screening Boxes
        # Screening Title & Abstract Box
        layer.objects.append(
            VectorObject(
                shape_type=VectorShapeType.ROUNDED_RECT,
                name="Box_Screening",
                x=80,
                y=265,
                width=320,
                height=75,
                text_content=f"Catatan diskrining berdasarkan\njudul dan abstrak\n(n = {screened_count})",
                style=VectorStyle(fill=blue_fill, stroke=blue_stroke, stroke_width=1.8, has_shadow=True),
                typography=TypographyStyle(font_size=11, font_weight="bold"),
            )
        )
        # Excluded Screening Box
        layer.objects.append(
            VectorObject(
                shape_type=VectorShapeType.ROUNDED_RECT,
                name="Box_Excluded_Screening",
                x=480,
                y=265,
                width=340,
                height=75,
                text_content=f"Catatan dieksklusi:\n(Tidak relevan tema / Non-peer reviewed)\n(n = {excluded_screening})",
                style=VectorStyle(fill=amber_fill, stroke=amber_stroke, stroke_width=1.5),
                typography=TypographyStyle(font_size=11),
            )
        )
        # Connector Screening -> Excluded
        layer.objects.append(
            VectorObject(
                shape_type=VectorShapeType.CONNECTOR_ARROW,
                name="Arrow_Screen_to_Ex",
                x=400,
                y=302,
                width=80,
                height=0,
                points=[Point(400, 302), Point(480, 302)],
                style=VectorStyle(stroke=blue_stroke, stroke_width=2.0),
            )
        )

        # Stage 3: Eligibility Box
        layer.objects.append(
            VectorObject(
                shape_type=VectorShapeType.ROUNDED_RECT,
                name="Box_Eligibility",
                x=80,
                y=420,
                width=320,
                height=90,
                text_content=f"Laporan teks lengkap dinilai\nuntuk kelayakan empiris\n(n = {eligibility_assessed})",
                style=VectorStyle(fill=blue_fill, stroke=blue_stroke, stroke_width=1.8, has_shadow=True),
                typography=TypographyStyle(font_size=11, font_weight="bold"),
            )
        )
        # Excluded Eligibility Box with Specific Reasons
        layer.objects.append(
            VectorObject(
                shape_type=VectorShapeType.ROUNDED_RECT,
                name="Box_Excluded_Eligibility",
                x=480,
                y=420,
                width=340,
                height=90,
                text_content=f"Laporan teks lengkap dieksklusi (n = {excluded_eligibility}):\n- Sampel tidak representatif (n = 64)\n- Metodologi tidak terstandar (n = 41)\n- Data luaran tidak lengkap (n = 30)",
                style=VectorStyle(fill=amber_fill, stroke=amber_stroke, stroke_width=1.5),
                typography=TypographyStyle(font_size=10),
            )
        )
        # Connector Eligibility -> Excluded
        layer.objects.append(
            VectorObject(
                shape_type=VectorShapeType.CONNECTOR_ARROW,
                name="Arrow_Elig_to_Ex",
                x=400,
                y=465,
                width=80,
                height=0,
                points=[Point(400, 465), Point(480, 465)],
                style=VectorStyle(stroke=blue_stroke, stroke_width=2.0),
            )
        )

        # Stage 4: Included Box
        layer.objects.append(
            VectorObject(
                shape_type=VectorShapeType.ROUNDED_RECT,
                name="Box_Included",
                x=80,
                y=590,
                width=740,
                height=70,
                text_content=f"Studi akhir disertakan dalam sintesis kuantitatif dan kualitatif tesis\n(n = {included_count} artikel jurnal bereputasi Scopus Q1/Q2 & SINTA 1/2)",
                style=VectorStyle(fill=green_fill, stroke=green_stroke, stroke_width=2.2, has_shadow=True),
                typography=TypographyStyle(font_size=12, font_weight="bold"),
            )
        )

        # Vertical Flow Connectors (Id -> Screen -> Elig -> Inc)
        v_arrows = [
            ("V_Arrow_1", 240, 185, 240, 265),
            ("V_Arrow_2", 240, 340, 240, 420),
            ("V_Arrow_3", 240, 510, 240, 590),
        ]
        for aid, x1, y1, x2, y2 in v_arrows:
            layer.objects.append(
                VectorObject(
                    shape_type=VectorShapeType.CONNECTOR_ARROW,
                    name=aid,
                    x=x1,
                    y=y1,
                    width=x2 - x1,
                    height=y2 - y1,
                    points=[Point(x1, y1), Point(x2, y2)],
                    style=VectorStyle(stroke=blue_stroke, stroke_width=2.2),
                )
            )

        project.layers = [layer]
        return project

    # ==========================================================================
    # 2. CONCEPTUAL RESEARCH FRAMEWORK TEMPLATE
    # ==========================================================================
    @classmethod
    def create_conceptual_framework(
        cls,
        var_x: str = "Kualitas Konten Komunikasi Digital (X)",
        var_m: str = "Kepercayaan Merek / Brand Trust (M)",
        var_y: str = "Loyalitas Audiens (Y)",
        h1_label: str = "H1 (+, p < 0.05)",
        h2_label: str = "H2 (+, p < 0.05)",
        h3_label: str = "H3 (+, p < 0.05)",
        chapter: int = 2,
        figure_idx: int = 1,
    ) -> VectorProjectSchema:
        """Constructs quantitative research framework (X -> M -> Y) with hypothesis paths."""
        project = VectorProjectSchema(
            title="Model Kerangka Konseptual Penelitian",
            canvas_width=860.0,
            canvas_height=480.0,
            attribution=FigureAttribution(
                chapter_number=chapter,
                figure_index=figure_idx,
                title="Model Kerangka Konseptual dan Hipotesis Penelitian",
                source="Data diolah penulis berdasarkan teori integrasi komunikasi (2026)",
            ),
        )
        layer = VectorLayer(name="Kerangka Konseptual")

        # Nodes
        box_x = VectorObject(
            shape_type=VectorShapeType.ROUNDED_RECT,
            name="Node_Var_X",
            x=60,
            y=180,
            width=220,
            height=110,
            text_content=f"{var_x}\n\nIndikator:\n• Relevansi Informasi\n• Kredibilitas Sumber\n• Frekuensi Pesan",
            style=VectorStyle(fill="#F8FAFC", stroke="#1E293B", stroke_width=2.0, has_shadow=True),
            typography=TypographyStyle(font_size=11, font_weight="bold"),
        )
        box_m = VectorObject(
            shape_type=VectorShapeType.ROUNDED_RECT,
            name="Node_Var_M",
            x=320,
            y=60,
            width=220,
            height=110,
            text_content=f"{var_m}\n\nIndikator:\n• Keandalan Pesan\n• Integritas Platform\n• Persepsi Manfaat",
            style=VectorStyle(fill="#EFF6FF", stroke="#2563EB", stroke_width=2.0, has_shadow=True),
            typography=TypographyStyle(font_size=11, font_weight="bold"),
        )
        box_y = VectorObject(
            shape_type=VectorShapeType.ROUNDED_RECT,
            name="Node_Var_Y",
            x=580,
            y=180,
            width=220,
            height=110,
            text_content=f"{var_y}\n\nIndikator:\n• Retensi Penggunaan\n• Advokasi Rekomendasi\n• Resistensi Kompetitor",
            style=VectorStyle(fill="#F0FDF4", stroke="#16A34A", stroke_width=2.0, has_shadow=True),
            typography=TypographyStyle(font_size=11, font_weight="bold"),
        )
        layer.objects.extend([box_x, box_m, box_y])

        # Hypothesis Arrows
        # Path 1: X -> M (H1)
        layer.objects.append(
            VectorObject(
                shape_type=VectorShapeType.CONNECTOR_ARROW,
                name="Path_H1",
                x=180,
                y=180,
                width=140,
                height=-65,
                points=[Point(240, 180), Point(320, 120)],
                text_content=h1_label,
                style=VectorStyle(stroke="#2563EB", stroke_width=2.2),
                typography=TypographyStyle(font_size=10, font_weight="bold"),
            )
        )
        # Path 2: M -> Y (H2)
        layer.objects.append(
            VectorObject(
                shape_type=VectorShapeType.CONNECTOR_ARROW,
                name="Path_H2",
                x=540,
                y=120,
                width=80,
                height=60,
                points=[Point(540, 120), Point(620, 180)],
                text_content=h2_label,
                style=VectorStyle(stroke="#16A34A", stroke_width=2.2),
                typography=TypographyStyle(font_size=10, font_weight="bold"),
            )
        )
        # Path 3: Direct X -> Y (H3)
        layer.objects.append(
            VectorObject(
                shape_type=VectorShapeType.CONNECTOR_ARROW,
                name="Path_H3_Direct",
                x=280,
                y=235,
                width=300,
                height=0,
                points=[Point(280, 235), Point(580, 235)],
                text_content=h3_label,
                style=VectorStyle(stroke="#0F172A", stroke_width=2.5),
                typography=TypographyStyle(font_size=11, font_weight="bold"),
            )
        )

        project.layers = [layer]
        return project

    # ==========================================================================
    # 3. THESIS METHODOLOGY WORKFLOW TEMPLATE
    # ==========================================================================
    @classmethod
    def create_methodology_flowchart(
        cls,
        stages: list[dict[str, str]] | None = None,
        chapter: int = 3,
        figure_idx: int = 2,
    ) -> VectorProjectSchema:
        """Constructs 5-stage sequential thesis methodology diagram."""
        project = VectorProjectSchema(
            title="Diagram Alur Metodologi Penelitian",
            canvas_width=860.0,
            canvas_height=420.0,
            attribution=FigureAttribution(
                chapter_number=chapter,
                figure_index=figure_idx,
                title="Tahapan Prosedur Metodologi Penelitian",
                source="Buku Pedoman Penulisan Tesis MIKOM UPNVJT (2026)",
            ),
        )
        layer = VectorLayer(name="Alur Metodologi")

        default_stages = stages or [
            {"step": "Tahap 1", "title": "Studi Pendahuluan &\nRumusan Masalah", "desc": "Observasi empiris &\nanalisis kesenjangan riset"},
            {"step": "Tahap 2", "title": "Telaah Pustaka &\nPengembangan Instrumen", "desc": "Sintesis PRISMA &\nkuesioner skala Likert"},
            {"step": "Tahap 3", "title": "Pengumpulan Data\n(Survei Primer)", "desc": "Distribusi kuesioner ke\n120 responden terpilih"},
            {"step": "Tahap 4", "title": "Uji Kualitas Data &\nAnalisis Regresi", "desc": "Validitas, reliabilitas,\ndan estimasi model Y=a+bX"},
            {"step": "Tahap 5", "title": "Pembahasan &\nPenarikan Simpulan", "desc": "Uji hipotesis (p < 0.05) &\nrekomendasi manajerial"},
        ]

        card_width = 135
        card_height = 140
        gap = 25
        start_x = 45
        start_y = 120

        for i, s in enumerate(default_stages):
            cx = start_x + i * (card_width + gap)
            # Stage Card
            layer.objects.append(
                VectorObject(
                    shape_type=VectorShapeType.ROUNDED_RECT,
                    name=f"Card_{s['step']}",
                    x=cx,
                    y=start_y,
                    width=card_width,
                    height=card_height,
                    text_content=f"{s['step']}\n\n{s['title']}\n\n{s['desc']}",
                    style=VectorStyle(fill="#F8FAFC", stroke="#334155", stroke_width=1.5, has_shadow=True),
                    typography=TypographyStyle(font_size=10, font_weight="normal"),
                )
            )
            # Connecting Arrow (between cards)
            if i < len(default_stages) - 1:
                ax = cx + card_width
                layer.objects.append(
                    VectorObject(
                        shape_type=VectorShapeType.CONNECTOR_ARROW,
                        name=f"Arrow_{i+1}_to_{i+2}",
                        x=ax,
                        y=start_y + card_height / 2,
                        width=gap,
                        height=0,
                        points=[Point(ax, start_y + card_height / 2), Point(ax + gap, start_y + card_height / 2)],
                        style=VectorStyle(stroke="#2563EB", stroke_width=2.2),
                    )
                )

        project.layers = [layer]
        return project
