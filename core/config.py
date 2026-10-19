import os
from typing import Any, Dict
from dotenv import load_dotenv

load_dotenv()


def get_mcp_config() -> Dict[str, Any]:
    """Mengambil konfigurasi MCP dengan prioritas: Streamlit secrets > .env."""
    try:
        import streamlit as st
        # Cek apakah st.secrets tersedia dan dapat diakses
        scopus_k = st.secrets.get("SCOPUS_API_KEY") if hasattr(st, "secrets") else None
        scopus_u = st.secrets.get("SCOPUS_MCP_URL") if hasattr(st, "secrets") else None
        sinta_s = st.secrets.get("SINTA_MCP_SCRIPT") if hasattr(st, "secrets") else None

        return {
            "scopus_key": scopus_k or os.getenv("SCOPUS_API_KEY"),
            "scopus_url": scopus_u or os.getenv("SCOPUS_MCP_URL"),
            "sinta_script": sinta_s or os.getenv("SINTA_MCP_SCRIPT"),
        }
    except Exception:
        return {
            "scopus_key": os.getenv("SCOPUS_API_KEY"),
            "scopus_url": os.getenv("SCOPUS_MCP_URL"),
            "sinta_script": os.getenv("SINTA_MCP_SCRIPT"),
        }
