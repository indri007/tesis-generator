"""utils/premium_plot.py - Academic chart generation with muted palette & clean spines."""
import io
import matplotlib.pyplot as plt

# Palet warna eksklusif (Muted/Earth Tones)
MUTED_PALETTE = ['#1D3557', '#457B9D', '#A8DADC', '#F1FAEE', '#E63946']


def create_premium_chart(
    x_data,
    y_data,
    title,
    xlabel,
    ylabel,
    annotation_text=None,
    export_fmt="png"
):
    """Membuat grafik dengan gaya akademik eksklusif menggunakan pure matplotlib.
    
    Format ekspor:
    - 'png': High-Resolution (300 DPI) siap cetak naskah
    - 'svg': Vektor murni scalable
    """
    plt.rcParams['font.family'] = 'serif'
    plt.rcParams['font.serif'] = ['Times New Roman']
    
    fig, ax = plt.subplots(figsize=(8, 5), facecolor='white')
    ax.set_facecolor('white')
    
    # Plot data dengan warna Muted
    ax.plot(x_data, y_data, color=MUTED_PALETTE[0], linewidth=2.5, marker='o', markersize=8)
    
    # Hapus garis grid yang tidak perlu (Chart Junk)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(axis='y', linestyle='--', alpha=0.5)
    
    # Beri judul dan label
    ax.set_title(title, fontsize=14, fontweight='bold', pad=15)
    ax.set_xlabel(xlabel, fontsize=12)
    ax.set_ylabel(ylabel, fontsize=12)
    
    # Tambahkan anotasi manusiawi (jika ada)
    if annotation_text and len(y_data) > 0:
        max_idx = y_data.index(max(y_data))
        ax.annotate(
            annotation_text,
            xy=(x_data[max_idx], y_data[max_idx]),
            xytext=(
                x_data[max_idx] - 0.5 if isinstance(x_data[max_idx], (int, float)) else max(0, max_idx - 1),
                y_data[max_idx] * 1.05
            ),
            arrowprops=dict(facecolor='black', arrowstyle='->', lw=1.5),
            fontsize=10,
            fontfamily='serif'
        )
    
    plt.tight_layout()
    
    buf = io.BytesIO()
    if export_fmt.lower() == "svg":
        fig.savefig(buf, format="svg", bbox_inches="tight")
    else:
        fig.savefig(buf, format="png", dpi=300, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf
