"""OCR Engine for academic document processing with Tesseract and Poppler fallbacks."""

import logging
import shutil
from pathlib import Path
from typing import Any, Optional

from PIL import Image, ImageFilter, ImageOps

logger = logging.getLogger(__name__)

# Check system executable availability safely
TESSERACT_AVAILABLE = shutil.which("tesseract") is not None
POPPLER_AVAILABLE = shutil.which("pdftoppm") is not None


class OCREngine:
    """Provides OCR capabilities with preprocessing and non-blocking fallbacks."""

    def __init__(self, default_lang: str = "ind+eng"):
        self.default_lang = default_lang
        self.is_tesseract_installed = TESSERACT_AVAILABLE
        self.is_poppler_installed = POPPLER_AVAILABLE

    def check_system_readiness(self) -> dict[str, Any]:
        """Inspects local/cloud OCR binary and language model readiness."""
        available_langs = []
        if self.is_tesseract_installed:
            try:
                import pytesseract
                available_langs = pytesseract.get_languages(config="")
            except Exception as e:
                logger.warning("Could not query tesseract languages: %s", e)

        return {
            "tesseract_installed": self.is_tesseract_installed,
            "poppler_installed": self.is_poppler_installed,
            "available_languages": available_langs,
            "supports_indonesian": "ind" in available_langs,
            "supports_english": "eng" in available_langs,
        }

    def preprocess_image(self, img: Image.Image) -> Image.Image:
        """Applies grayscale, auto-contrast, and subtle sharpening for higher OCR accuracy."""
        # 1. Convert to Grayscale
        gray = img.convert("L")
        # 2. Auto-Contrast normalization
        contrasted = ImageOps.autocontrast(gray, cutoff=2)
        # 3. Subtle Sharpening filter to enhance font edges
        sharpened = contrasted.filter(ImageFilter.SHARPEN)
        return sharpened

    def run_ocr(self, image: Image.Image, lang: Optional[str] = None) -> str:
        """Runs OCR on a PIL Image object with graceful fallback if Tesseract is unavailable."""
        if not self.is_tesseract_installed:
            logger.info("Tesseract executable not found on system PATH. Skipping OCR.")
            return "[OCR tidak dapat dijalankan: tesseract-ocr belum terpasang di sistem]"

        try:
            import pytesseract
            target_lang = lang or self.default_lang
            readiness = self.check_system_readiness()
            # If Indonesian not installed, fallback to English or osd
            if "ind" not in readiness.get("available_languages", []) and "ind" in target_lang:
                target_lang = "eng" if "eng" in readiness.get("available_languages", []) else ""

            processed = self.preprocess_image(image)
            text = pytesseract.image_to_string(processed, lang=target_lang if target_lang else None)
            return text.strip()
        except Exception as e:
            logger.error("OCR execution failed: %s", e)
            return f"[Gagal menjalankan OCR: {e}]"

    def run_gemini_vision_ocr(self, image: Image.Image) -> str:
        """Ekstraksi teks dari gambar menggunakan Gemini Flash Multimodal Vision API."""
        import os
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            return ""

        try:
            import base64
            import io
            buf = io.BytesIO()
            image.save(buf, format="JPEG", quality=85)
            img_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")

            # Menggunakan litellm atau google-genai
            try:
                import litellm
                resp = litellm.completion(
                    model="gemini/gemini-1.5-flash",
                    api_key=api_key,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": "Transkripsikan seluruh teks yang ada pada halaman dokumen akademik ini secara akurat dan lengkap. Pertahankan tata letak dan struktur paragraf tanpa komentar tambahan.",
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"},
                                },
                            ],
                        }
                    ],
                    max_tokens=2048,
                )
                text = resp.choices[0].message.content
                return text.strip() if text else ""
            except Exception as e_llm:
                logger.warning("Gemini Vision OCR via litellm failed: %s", e_llm)
                return ""
        except Exception as e:
            logger.error("Error preparing image for Gemini Vision: %s", e)
            return ""

    def run_hybrid_ocr(self, image: Image.Image, lang: Optional[str] = None) -> str:
        """Strategi Hybrid OCR cerdas:
        1. Coba Tesseract OCR Lokal terlebih dahulu (cepat, gratis, hemat token).
        2. Jika teks lokal kurang dari 30 karakter atau Tesseract belum terpasang di OS,
           otomatis beralih (fallback) ke Gemini Multimodal Vision API.
        """
        # Step 1: Coba lokal Tesseract
        if self.is_tesseract_installed:
            local_text = self.run_ocr(image, lang=lang)
            if local_text and not local_text.startswith("[") and len(local_text.strip()) >= 30:
                return local_text

        # Step 2: Fallback ke Gemini Vision jika ada API key
        gemini_text = self.run_gemini_vision_ocr(image)
        if gemini_text and len(gemini_text.strip()) >= 20:
            return f"[Hasil Gemini Vision OCR]\n{gemini_text}"

        # Step 3: Jika keduanya gagal, kembalikan hasil lokal atau pesan informatif
        if self.is_tesseract_installed:
            return self.run_ocr(image, lang=lang)

        return "[OCR tidak dapat dijalankan: tesseract-ocr belum terpasang dan API Gemini tidak tersedia]"

    def run_pdf_ocr(self, pdf_path: str | Path, max_pages: int = 50, lang: Optional[str] = None) -> str:
        """Renders PDF pages to images via pdf2image/poppler and executes OCR."""
        if not self.is_poppler_installed:
            logger.info("Poppler (pdftoppm) not found on system PATH. Cannot render PDF to images.")
            return "[OCR PDF tidak dapat dijalankan: poppler-utils belum terpasang di sistem]"

        try:
            from pdf2image import convert_from_path
            pages = convert_from_path(str(pdf_path), first_page=1, last_page=max_pages)
            extracted_pages = []
            for idx, page in enumerate(pages, 1):
                page_text = self.run_hybrid_ocr(page, lang=lang)
                extracted_pages.append(f"--- Halaman {idx} (OCR) ---\n{page_text}")
            return "\n\n".join(extracted_pages)
        except Exception as e:
            logger.error("PDF OCR conversion failed: %s", e)
            return f"[Gagal memproses OCR PDF: {e}]"
