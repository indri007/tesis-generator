from __future__ import annotations

import logging
import re
from typing import List

logger = logging.getLogger(__name__)

# Try loading Sastrawi for full morphological analysis; provide resilient pure-Python fallback
try:
    from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
    from Sastrawi.StopWordRemover.StopWordRemoverFactory import StopWordRemoverFactory

    _stemmer = StemmerFactory().create_stemmer()
    _stopword = StopWordRemoverFactory().create_stop_word_remover()
    SASTRAWI_AVAILABLE = True
except ImportError:
    SASTRAWI_AVAILABLE = False
    _stemmer = None
    _stopword = None
    logger.info("Sastrawi not installed. Using pure-Python Indonesian normalization fallback.")

# Common Indonesian stopwords for fallback
INDONESIAN_FALLBACK_STOPWORDS = {
    "yang", "di", "ke", "dari", "dan", "ini", "itu", "untuk", "pada", "adalah",
    "dengan", "sebagai", "oleh", "dalam", "atau", "juga", "akan", "telah", "dapat",
    "karena", "bagi", "secara", "tentang", "antara", "serta", "tersebut", "namun",
    "ia", "dia", "mereka", "kami", "kita", "bisa", "bahwa", "hanya", "sudah",
    "saat", "oleh", "pada", "atas", "bawah", "saja", "lebih", "sangat"
}


def normalize_text(text: str) -> str:
    """Membersihkan tanda baca dan menormalkan spasi teks."""
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)   # hapus tanda baca
    text = re.sub(r"\s+", " ", text).strip()
    return text


def preprocess_indonesian(text: str) -> str:
    """Preproses teks berbahasa Indonesia: normalisasi, stopword removal, dan stemming."""
    text = normalize_text(text)
    if not text:
        return ""

    if SASTRAWI_AVAILABLE and _stopword and _stemmer:
        text = _stopword.remove(text)
        return _stemmer.stem(text)

    # Fallback jika Sastrawi belum terpasang
    tokens = [w for w in text.split() if w not in INDONESIAN_FALLBACK_STOPWORDS]
    return " ".join(tokens)


def split_into_sentences(text: str) -> List[str]:
    """Membagi dokumen teks menjadi kalimat-kalimat terpisah."""
    if not text:
        return []
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
