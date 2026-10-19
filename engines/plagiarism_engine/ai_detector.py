from __future__ import annotations

import json
import logging
import math
import os
import ssl
import urllib.request
from typing import Any, List, Optional

from .base_checker import BaseChecker, CheckResult
from .preprocessing import split_into_sentences

logger = logging.getLogger(__name__)

# Check for PyTorch and Transformers
try:
    import numpy as np
    import torch
    from transformers import GPT2LMHeadModel, GPT2TokenizerFast
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logger.info("transformers/torch not installed. AIDetector will use ZeroGPT API / statistical linguistic fallback.")


class AIDetector(BaseChecker):
    """Mendeteksi potensi teks hasil generasi kecerdasan buatan (AI-generated)
    menggunakan ZeroGPT API resmi dan analisis linguistik Burstiness / Perplexity.
    """

    name = "ai_zerogpt_detector"

    def __init__(
        self,
        use_neural_model: bool = True,
        zerogpt_api_key: Optional[str] = None,
        originality_api_key: Optional[str] = None
    ):
        self.tokenizer = None
        self.model = None
        self.use_neural = use_neural_model and TRANSFORMERS_AVAILABLE
        self.originality_api_key = originality_api_key or os.getenv("ORIGINALITY_API_KEY")
        self.zerogpt_api_key = zerogpt_api_key or os.getenv("ZEROGPT_API_KEY", "a8f1a64f-00ac-426e-9c39-aa9b6b8d4c03")

        if self.use_neural:
            try:
                self.tokenizer = GPT2TokenizerFast.from_pretrained("gpt2")
                self.model = GPT2LMHeadModel.from_pretrained("gpt2")
                self.model.eval()
            except Exception as e:
                logger.warning("Could not initialize GPT-2 model (%s). Using ZeroGPT API / statistical fallback.", e)
                self.tokenizer = None
                self.model = None
                self.use_neural = False

    def _call_zerogpt_api(self, text: str) -> Optional[dict[str, Any]]:
        """Memanggil ZeroGPT API resmi untuk verifikasi deteksi AI naskah."""
        if not self.zerogpt_api_key:
            return None

        # ZeroGPT optimal pada cuplikan 100-300 kata
        words = text.split()
        sample_text = " ".join(words[:250]) if len(words) > 250 else text

        try:
            try:
                import certifi
                ctx = ssl.create_default_context(cafile=certifi.where())
            except Exception:
                ctx = ssl._create_unverified_context()

            req = urllib.request.Request(
                "https://api.zerogpt.com/api/detect/detectText",
                data=json.dumps({"input_text": sample_text}).encode("utf-8"),
                headers={
                    "ApiKey": self.zerogpt_api_key,
                    "Content-Type": "application/json",
                    "User-Agent": "Mozilla/5.0 (compatible; TesisCheck_MIKOM2026/1.0)",
                },
            )
            with urllib.request.urlopen(req, context=ctx, timeout=12) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                if data.get("success") and "data" in data:
                    return data["data"]
        except Exception as e:
            logger.debug("ZeroGPT API call skipped / offline: %s", e)
        return None

    def _perplexity(self, text: str) -> float:
        """Menghitung perplexity teks."""
        if self.use_neural and self.tokenizer and self.model:
            try:
                enc = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
                with torch.no_grad():
                    loss = self.model(**enc, labels=enc["input_ids"]).loss
                return float(torch.exp(loss))
            except Exception as e:
                logger.debug("Neural perplexity calculation failed: %s", e)

        # Fallback statistik: entropi variasi kata
        words = text.split()
        if not words:
            return 10.0
        unique_ratio = len(set(words)) / max(1, len(words))
        return float(20.0 + (unique_ratio * 80.0))

    def _statistical_burstiness(self, sentences: List[str]) -> tuple[float, float]:
        """Fallback statistik linguistik berbasis variasi panjang kalimat."""
        lengths = [len(s.split()) for s in sentences if s.strip()]
        if not lengths:
            return 50.0, 1.0

        mean_len = sum(lengths) / len(lengths)
        variance = sum((x - mean_len) ** 2 for x in lengths) / max(1, len(lengths))
        std_dev = math.sqrt(variance)
        burstiness = round(std_dev / max(1.0, mean_len), 3)

        avg_ppl = 35.0 if burstiness < 0.25 else 75.0 if burstiness > 0.6 else 55.0
        return avg_ppl, burstiness

    def check(self, text: str, **kwargs: Any) -> CheckResult:
        sentences = split_into_sentences(text)
        if len(sentences) < 3:
            return CheckResult(
                checker_name=self.name,
                score=0.0,
                verdict="clean",
                matched_segments=[],
                evidence_refs=[],
            )

        # 1. Coba ZeroGPT API terlebih dahulu jika terkonfigurasi
        zg_data = self._call_zerogpt_api(text)
        if zg_data is not None:
            fake_pct = float(zg_data.get("fakePercentage", 0.0))
            ai_score = round(fake_pct / 100.0, 3)
            verdict = "ai_generated" if ai_score >= 0.70 else "suspicious" if ai_score >= 0.35 else "clean"

            return CheckResult(
                checker_name="ZeroGPT Official API",
                score=ai_score,
                verdict=verdict,
                matched_segments=[{
                    "provider": "ZeroGPT",
                    "fake_percentage": f"{fake_pct:.1f}%",
                    "feedback": zg_data.get("feedback", "Verified via ZeroGPT API"),
                    "text_words": zg_data.get("textWords", len(text.split())),
                    "ai_words": zg_data.get("aiWords", 0),
                    "is_human": zg_data.get("isHuman", 100 - int(fake_pct)),
                }],
                evidence_refs=["ZeroGPT Authenticity Gate (Key: a8f1a64f...)"],
            )

        # 2. Fallback ke model neural / statistik burstiness
        if self.use_neural and self.model and self.tokenizer:
            try:
                import numpy as np
                ppls = [self._perplexity(s) for s in sentences]
                avg_ppl = float(np.mean(ppls))
                burstiness = float(np.std(ppls) / (avg_ppl + 1e-9))
            except Exception as e:
                logger.warning("Error calculating neural burstiness: %s. Using statistical fallback.", e)
                avg_ppl, burstiness = self._statistical_burstiness(sentences)
        else:
            avg_ppl, burstiness = self._statistical_burstiness(sentences)

        ai_score = max(0.0, 1.0 - (avg_ppl / 100.0)) * max(0.0, 1.0 - burstiness)
        ai_score = min(1.0, max(0.0, float(ai_score)))
        verdict = "ai_generated" if ai_score >= 0.7 else "clean"

        return CheckResult(
            checker_name=self.name,
            score=round(ai_score, 3),
            verdict=verdict,
            matched_segments=[{
                "avg_perplexity": round(avg_ppl, 2),
                "burstiness": round(burstiness, 3),
                "sentence_count": len(sentences),
            }],
            evidence_refs=[],
        )
