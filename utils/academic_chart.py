import io
from typing import List, Optional, Tuple
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np


def apply_thesis_style():
    """Fungsi untuk membuat semua plot di aplikasi terlihat seperti buatan manusia/Excel."""
    mpl.rcParams["font.family"] = "serif"
    mpl.rcParams["font.serif"] = ["Times New Roman", "DejaVu Serif", "serif"]
    mpl.rcParams["axes.prop_cycle"] = mpl.cycler(color=["#5D729E", "#E8A87C", "#85CDCA", "#E27D60", "#C38D9E"])
    mpl.rcParams["axes.grid"] = True
    mpl.rcParams["grid.alpha"] = 0.3
    mpl.rcParams["axes.edgecolor"] = "#333333"


def apply_academic_chart_style():
    """Menerapkan konfigurasi tipografi dan visual standar tesis MIKOM 2026 (SPSS / Excel muted style)."""
    # 1. Gunakan Times New Roman (Standar Tesis)
    mpl.rcParams["font.family"] = "serif"
    mpl.rcParams["font.serif"] = ["Times New Roman", "DejaVu Serif", "serif"]
    mpl.rcParams["font.size"] = 11

    # 2. Tambahkan Gridline tipis (seperti Excel/SPSS)
    mpl.rcParams["axes.grid"] = True
    mpl.rcParams["grid.linestyle"] = "--"
    mpl.rcParams["grid.alpha"] = 0.6

    # 3. Beri Border hitam tegas (seperti grafik Word/Excel)
    mpl.rcParams["axes.edgecolor"] = "black"
    mpl.rcParams["axes.linewidth"] = 1.0

    # Palet warna akademis muted (tidak neon)
    colors = ["#4C72B0", "#DD8452", "#55A868", "#C44E52", "#8172B3"]
    return colors


def generate_excel_bar_chart(
    categories: Optional[List[str]] = None,
    values: Optional[List[float]] = None,
    title: str = "Distribusi Penerima Manfaat MBG (2025-2026)",
    ylabel: str = "Jumlah (Jiwa)",
    color: str = "#4C72B0",
    figsize: Tuple[float, float] = (8.0, 5.0),
) -> io.BytesIO:
    """Grafik Batang Gaya Excel / SPSS dengan label nilai di atas batang, border hitam, dan Times New Roman."""
    apply_academic_chart_style()

    if categories is None:
        categories = ["Tahap 1", "Tahap 2", "Tahap 3", "Tahap 4", "Tahap 5"]
    if values is None:
        values = [15000, 32000, 48000, 65000, 82000]

    fig, ax = plt.subplots(figsize=figsize, dpi=300)
    bars = ax.bar(categories, values, color=color, edgecolor="black", linewidth=1.0)

    # Tambahkan label angka di atas batang (seperti Excel)
    ax.bar_label(bars, padding=3, fontsize=10, fmt="%d")

    ax.set_ylabel(ylabel, fontweight="bold", labelpad=8)
    ax.set_title(title, fontweight="bold", pad=12, fontsize=12)
    plt.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=300)
    plt.close(fig)
    buf.seek(0)
    return buf


def generate_regression_plot(
    var_x_name: str,
    var_y_name: str,
    a_const: float = 2.5,
    b_coef: float = 0.4,
    p_val: float = 0.032,
    sample_n: int = 120,
    r_squared: float = 0.428,
) -> io.BytesIO:
    """Menghasilkan grafik regresi linier sederhana bergaya akademis publikasi jurnal / tesis."""
    colors = apply_academic_chart_style()

    np.random.seed(42)
    x = np.random.normal(loc=10.0, scale=2.5, size=sample_n)
    noise = np.random.normal(loc=0.0, scale=1.2, size=sample_n)
    y = a_const + (b_coef * x) + noise

    fig, ax = plt.subplots(figsize=(6.5, 4.2), dpi=300)

    # Titik scatter responden (muted blue)
    ax.scatter(x, y, color=colors[0], alpha=0.65, edgecolors="none", s=32, label="Data Responden (N=120)")

    # Garis regresi (muted orange/red)
    x_line = np.linspace(min(x), max(x), 100)
    y_line = a_const + b_coef * x_line
    formula_label = f"Model: Y = {a_const:.2f} + {b_coef:.2f}X\n(R² = {r_squared:.3f}, p = {p_val:.3f})"
    ax.plot(x_line, y_line, color=colors[3], linewidth=2.0, label=formula_label)

    # Label sumbu dan judul akademis
    ax.set_xlabel(f"Variabel Bebas (X): {var_x_name}", fontweight="bold", labelpad=8)
    ax.set_ylabel(f"Variabel Terikat (Y): {var_y_name}", fontweight="bold", labelpad=8)
    ax.set_title("Grafik 4.1 Estimasi Regresi Linier Sederhana", pad=12, fontweight="bold", fontsize=12)

    ax.legend(loc="upper left", framealpha=0.9, edgecolor="black", fontsize=10)
    plt.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=300)
    plt.close(fig)
    buf.seek(0)
    return buf
