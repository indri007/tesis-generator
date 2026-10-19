import io
from typing import List, Optional, Tuple, Dict, Any
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np


def save_figure(fig: plt.Figure, fmt: str = "png", dpi: int = 300) -> io.BytesIO:
    """Save a matplotlib Figure to a BytesIO buffer in the given format (png or svg).

    Args:
        fig: The matplotlib Figure object.
        fmt: 'png' for Super HD raster or 'svg' for vector.
        dpi: Resolution for PNG export (default 300 DPI for thesis print).

    Returns:
        io.BytesIO buffer with the exported image data.
    """
    buf = io.BytesIO()
    if fmt == "svg":
        fig.savefig(buf, format="svg", bbox_inches="tight")
    else:
        fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf


def apply_thesis_style():
    """Fungsi untuk membuat semua plot di aplikasi terlihat seperti buatan manusia / Excel."""
    mpl.rcParams["font.family"] = "serif"
    mpl.rcParams["font.serif"] = ["Times New Roman", "DejaVu Serif", "serif"]
    mpl.rcParams["font.size"] = 11
    mpl.rcParams["axes.prop_cycle"] = mpl.cycler(color=["#5D729E", "#E8A87C", "#85CDCA", "#E27D60", "#C38D9E"])
    mpl.rcParams["axes.grid"] = True
    mpl.rcParams["grid.alpha"] = 0.3
    mpl.rcParams["grid.linestyle"] = "--"
    mpl.rcParams["axes.edgecolor"] = "#333333"
    mpl.rcParams["axes.linewidth"] = 1.0


def apply_spss_style(ax: Optional[plt.Axes] = None):
    """Menerapkan gaya SPSS klasik: latar belakang abu-abu terang (#F0F0F0) dengan gridline putih tebal."""
    apply_thesis_style()
    if ax is not None:
        ax.set_facecolor("#F0F0F0")
        ax.grid(True, color="white", linewidth=1.2, linestyle="-", alpha=1.0)
        ax.set_axisbelow(True)


def generate_excel_bar_chart(
    categories: Optional[List[str]] = None,
    values: Optional[List[float]] = None,
    title: str = "Distribusi Penerima Manfaat MBG (2025-2026)",
    ylabel: str = "Jumlah (Jiwa)",
    source_text: str = "Sumber: Diolah peneliti dari data primer (2026)",
    outlier_idx: Optional[int] = None,
    outlier_note: Optional[str] = None,
    figsize: Tuple[float, float] = (8.0, 5.0),
    export_fmt: str = "png",
) -> io.BytesIO:
    """Grafik Batang Gaya Excel: label angka di atas batang, border hitam, dan anotasi sumber."""
    apply_thesis_style()

    if categories is None:
        categories = ["Tahap 1", "Tahap 2", "Tahap 3", "Tahap 4", "Tahap 5"]
    if values is None:
        values = [15200, 31400, 48900, 64500, 81800]

    fig, ax = plt.subplots(figsize=figsize, dpi=300)
    bars = ax.bar(categories, values, color="#4C72B0", edgecolor="black", linewidth=1.0)

    # Tambahkan label angka tepat di atas batang (seperti Excel)
    ax.bar_label(bars, padding=4, fontsize=10, fmt="%d")

    # Sorotan outlier manual (kotak merah putus-putus) jika diminta
    if outlier_idx is not None and 0 <= outlier_idx < len(bars):
        b = bars[outlier_idx]
        rect = patches.Rectangle(
            (b.get_x() - 0.05, 0),
            b.get_width() + 0.1,
            b.get_height() * 1.08,
            linewidth=1.5,
            edgecolor="#EF4444",
            facecolor="none",
            linestyle="--",
        )
        ax.add_patch(rect)
        if outlier_note:
            ax.annotate(
                outlier_note,
                xy=(b.get_x() + b.get_width() / 2, b.get_height() * 1.09),
                xytext=(b.get_x() + b.get_width() / 2, b.get_height() * 1.22),
                arrowprops=dict(facecolor="#EF4444", edgecolor="#EF4444", arrowstyle="->", lw=1.2),
                fontsize=9,
                fontweight="bold",
                color="#DC2626",
                ha="center",
            )

    ax.set_ylabel(ylabel, fontweight="bold", labelpad=8)
    ax.set_title(title, fontweight="bold", pad=14, fontsize=12)

    # Anotasi sumber manusia di bawah grafik
    fig.text(0.12, 0.02, source_text, fontsize=9, style="italic", color="#4B5563")
    plt.tight_layout(rect=[0, 0.05, 1, 1])

    return save_figure(fig, fmt=export_fmt)


def generate_spss_regression_chart(
    var_x: str = "Kualitas Konten Komunikasi Digital",
    var_y: str = "Loyalitas Audiens",
    a_const: float = 2.5,
    b_coef: float = 0.4,
    p_val: float = 0.032,
    sample_n: int = 120,
    source_text: str = "Sumber: Output Estimasi SPSS Model Regresi Linier (2026)",
    export_fmt: str = "png",
) -> io.BytesIO:
    """Grafik Sebar & Garis Regresi Gaya SPSS Klasik (#F0F0F0 background, white gridlines)."""
    fig, ax = plt.subplots(figsize=(7.5, 4.8), dpi=300)
    apply_spss_style(ax)

    np.random.seed(42)
    x = np.random.normal(loc=10.0, scale=2.5, size=sample_n)
    noise = np.random.normal(loc=0.0, scale=1.1, size=sample_n)
    y = a_const + (b_coef * x) + noise

    # Scatter data responden
    ax.scatter(x, y, color="#5D729E", alpha=0.75, edgecolors="black", linewidth=0.5, s=36, label=f"Responden (N={sample_n})")

    # Garis model regresi
    x_line = np.linspace(min(x), max(x), 100)
    y_line = a_const + (b_coef * x_line)
    ax.plot(x_line, y_line, color="#C44E52", linewidth=2.0, label=f"Fit Line: Y = {a_const:.2f} + {b_coef:.2f}X (p={p_val})")

    ax.set_xlabel(var_x, fontweight="bold", labelpad=8)
    ax.set_ylabel(var_y, fontweight="bold", labelpad=8)
    ax.set_title(f"Grafik 4.2 Scatter Plot & Garis Regresi: {var_x} vs {var_y}", fontweight="bold", pad=12, fontsize=12)

    # Legenda di luar data (bawah atau atas)
    ax.legend(loc="upper left", framealpha=0.95, edgecolor="black", facecolor="white", fontsize=9)

    fig.text(0.12, 0.02, source_text, fontsize=9, style="italic", color="#4B5563")
    plt.tight_layout(rect=[0, 0.05, 1, 1])

    return save_figure(fig, fmt=export_fmt)


def generate_vosviewer_sna_chart(
    nodes: Optional[List[Dict[str, Any]]] = None,
    edges: Optional[List[Tuple[str, str, float]]] = None,
    title: str = "Visualisasi Klaster Jaringan Komunikasi (Gaya VOSviewer)",
    source_text: str = "Sumber: Pemetaan Bibliometrik VOSviewer / Ekstraksi Korpus MIKOM 2026",
    export_fmt: str = "png",
) -> io.BytesIO:
    """Visualisasi Jaringan Gaya VOSviewer: latar putih bersih, lingkaran bergradasi, tautan lengkung tipis."""
    apply_thesis_style()

    fig, ax = plt.subplots(figsize=(8.0, 5.5), dpi=300)
    ax.set_facecolor("white")
    ax.grid(False)

    if nodes is None:
        nodes = [
            {"id": "Digital Marketing", "x": 0.2, "y": 0.6, "size": 950, "color": "#5D729E"},
            {"id": "Audience Loyalty", "x": 0.35, "y": 0.75, "size": 850, "color": "#5D729E"},
            {"id": "Media Richness", "x": 0.3, "y": 0.35, "size": 750, "color": "#55A868"},
            {"id": "Uses & Gratifications", "x": 0.65, "y": 0.45, "size": 900, "color": "#DD8452"},
            {"id": "Information Fatigue", "x": 0.75, "y": 0.7, "size": 650, "color": "#C44E52"},
            {"id": "Engagement Rate", "x": 0.5, "y": 0.8, "size": 800, "color": "#8172B3"},
        ]

    node_dict = {n["id"]: n for n in nodes}

    if edges is None:
        edges = [
            ("Digital Marketing", "Audience Loyalty", 2.0),
            ("Digital Marketing", "Media Richness", 1.5),
            ("Uses & Gratifications", "Audience Loyalty", 1.8),
            ("Information Fatigue", "Audience Loyalty", 1.2),
            ("Media Richness", "Engagement Rate", 1.6),
            ("Engagement Rate", "Audience Loyalty", 2.2),
        ]

    # Gambar tautan melengkung tipis (VOSviewer curved edges)
    for src, dst, weight in edges:
        if src in node_dict and dst in node_dict:
            n1 = node_dict[src]
            n2 = node_dict[dst]
            rad = 0.15 if (n1["x"] + n2["y"]) % 2 > 0 else -0.15
            conn = patches.ConnectionPatch(
                xyA=(n1["x"], n1["y"]),
                xyB=(n2["x"], n2["y"]),
                coordsA="data",
                coordsB="data",
                arrowstyle="-",
                color="#94A3B8",
                alpha=0.65,
                linewidth=weight,
                connectionstyle=f"arc3,rad={rad}",
            )
            ax.add_patch(conn)

    # Gambar node lingkaran dengan border tipis dan label rapi
    for n in nodes:
        ax.scatter(n["x"], n["y"], s=n["size"], color=n["color"], alpha=0.88, edgecolors="black", linewidth=0.8, zorder=3)
        ax.text(n["x"], n["y"] - 0.055, n["id"], fontsize=9.5, fontweight="bold", ha="center", va="top", zorder=4)

    ax.set_xlim(0.05, 0.95)
    ax.set_ylim(0.15, 0.95)
    ax.axis("off")
    ax.set_title(title, pad=16, fontweight="bold", fontsize=12)

    fig.text(0.10, 0.03, source_text, fontsize=9, style="italic", color="#4B5563")
    plt.tight_layout(rect=[0, 0.05, 1, 1])

    return save_figure(fig, fmt=export_fmt)


def generate_prisma_flowchart(
    identification_n: int = 480,
    screened_n: int = 340,
    excluded_n: int = 180,
    retrieved_n: int = 160,
    included_n: int = 45,
    title: str = "Bagan Alur Seleksi Literatur PRISMA 2020",
    source_text: str = "Sumber: Protokol Tinjauan Sistematis PRISMA 2020 (Diolah Peneliti, 2026)",
    export_fmt: str = "png",
) -> io.BytesIO:
    """Diagram Alur PRISMA: kotak sudut tegas, orthogonal routing, font Times New Roman, dan anotasi sumber."""
    apply_thesis_style()

    fig, ax = plt.subplots(figsize=(8.0, 7.2), dpi=300)
    ax.set_facecolor("white")
    ax.axis("off")

    # Kotak sudut tegas (Visio / Draw.io style)
    box_style = dict(boxstyle="square,pad=0.5", facecolor="#F8FAFC", edgecolor="black", linewidth=1.0)
    box_accent = dict(boxstyle="square,pad=0.5", facecolor="#E2E8F0", edgecolor="black", linewidth=1.0)

    # 1. Identifikasi
    ax.text(0.5, 0.88, f"Identifikasi Artikel melalui Basis Data:\nScopus & SINTA (n = {identification_n})", ha="center", va="center", bbox=box_style, fontsize=9.5)

    # Panah 1
    ax.annotate("", xy=(0.5, 0.74), xytext=(0.5, 0.82), arrowprops=dict(facecolor="black", edgecolor="black", arrowstyle="->", lw=1.2))

    # 2. Penyaringan
    ax.text(0.35, 0.68, f"Artikel Disaring Berdasarkan Judul/Abstrak\n(n = {screened_n})", ha="center", va="center", bbox=box_style, fontsize=9.5)

    # Cabang Dikeluarkan
    ax.annotate("", xy=(0.68, 0.68), xytext=(0.53, 0.68), arrowprops=dict(facecolor="black", edgecolor="black", arrowstyle="->", lw=1.2))
    ax.text(0.82, 0.68, f"Artikel Dikeluarkan\n(n = {excluded_n})", ha="center", va="center", bbox=box_accent, fontsize=9.0)

    # Panah 2
    ax.annotate("", xy=(0.35, 0.52), xytext=(0.35, 0.61), arrowprops=dict(facecolor="black", edgecolor="black", arrowstyle="->", lw=1.2))

    # 3. Kelayakan Naskah Penuh
    ax.text(0.35, 0.46, f"Naskah Lengkap Dinilai Kelayakannya\n(n = {retrieved_n})", ha="center", va="center", bbox=box_style, fontsize=9.5)

    # Cabang Eksklusi Kriteria
    ax.annotate("", xy=(0.68, 0.46), xytext=(0.53, 0.46), arrowprops=dict(facecolor="black", edgecolor="black", arrowstyle="->", lw=1.2))
    ax.text(0.82, 0.46, f"Eksklusi: Tidak Sesuai\nIndikator (n = {retrieved_n - included_n})", ha="center", va="center", bbox=box_accent, fontsize=9.0)

    # Panah 3
    ax.annotate("", xy=(0.35, 0.28), xytext=(0.35, 0.39), arrowprops=dict(facecolor="black", edgecolor="black", arrowstyle="->", lw=1.2))

    # 4. Sintesis Akhir
    ax.text(0.35, 0.22, f"Studi Disertakan dalam Sintesis\nKualitatif / Kuantitatif (n = {included_n})", ha="center", va="center", bbox=dict(boxstyle="square,pad=0.5", facecolor="#E0E7FF", edgecolor="black", linewidth=1.2), fontsize=10, fontweight="bold")

    ax.set_title(title, pad=14, fontweight="bold", fontsize=12)
    fig.text(0.08, 0.03, source_text, fontsize=9, style="italic", color="#4B5563")

    plt.tight_layout(rect=[0, 0.05, 1, 1])

    return save_figure(fig, fmt=export_fmt)
