"""utils/palette_generator.py - Academic color palette generator and Streamlit UI."""
import random
import streamlit as st


def generate_premium_palette():
    """Menghasilkan palet warna eksklusif yang aman untuk tesis."""
    # Daftar warna dasar (Navy, Emerald, Maroon, Charcoal, Slate)
    base_colors = ["#1D3557", "#2A9D8F", "#800E13", "#264653", "#4A4E69"]
    
    # Pilih satu warna dasar
    primary = random.choice(base_colors)
    
    # Buat warna turunannya
    if primary == "#1D3557":
        secondary = "#457B9D"
    elif primary == "#2A9D8F":
        secondary = "#E76F51"
    elif primary == "#800E13":
        secondary = "#A53860"
    elif primary == "#264653":
        secondary = "#2A9D8F"
    else:
        secondary = "#9A8C98"
        
    tertiary = "#F1FAEE"  # Off-white / Ivory neutral
    
    return {
        "Primary (Utama)": primary,
        "Secondary (Sekunder)": secondary,
        "Tertiary (Netral/Latar)": tertiary
    }


def show_palette_ui(key_prefix: str = "pal"):
    """Menampilkan palet warna di Streamlit."""
    st.markdown("##### 🎨 Palet Warna Eksklusif (Muted & Standar Tesis)")
    st.caption("Palet warna akademik terkalibrasi (*earth/muted tones*) tanpa efek neon atau kecurigaan AI.")
    
    if f"{key_prefix}_current" not in st.session_state:
        st.session_state[f"{key_prefix}_current"] = generate_premium_palette()
        
    col_ctrl, _ = st.columns([1, 2])
    with col_ctrl:
        if st.button("🎲 Buat Palet Warna Baru", key=f"{key_prefix}_refresh_btn"):
            st.session_state[f"{key_prefix}_current"] = generate_premium_palette()
            
    palette = st.session_state[f"{key_prefix}_current"]
    cols = st.columns(len(palette))
    for i, (name, hex_code) in enumerate(palette.items()):
        with cols[i]:
            st.markdown(f"**{name}**")
            st.color_picker(f"Hex {name}", hex_code, key=f"{key_prefix}_cp_{i}", disabled=True)
            st.code(hex_code, language="text")
