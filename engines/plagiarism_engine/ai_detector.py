from __future__ import annotations

import logging
import math
from typing import Any, List

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
    logger.info("transformers/torch not installed. AIDetector will use statistical linguistic burstiness fallback.")


class AIDetector(BaseChecker):
    """Mendeteksi potensi teks hasil generasi kecerdasan buatan (AI-generated)

    menggunakan metrik Perplexity dan Burstiness (variasi kompleksitas kalimat).
    """

    name = "ai_perplexity_burstiness"

    def __init__(self, use_neural_model: bool = True, originality_api_key: Optional[str] = None):
        import os
        self.tokenizer = None
        self.model = None
        self.use_neural = use_neural_model and TRANSFORMERS_AVAILABLE
        self.originality_api_key = originality_api_key or os.getenv("ORIGINALITY_API_KEY")

        if self.use_neural:
            try:
                # Gunakan model kecil agar cepat; GPT2 multilingual opsional
                self.tokenizer = GPT2TokenizerFast.from_pretrained("gpt2")
                self.model = GPT2LMHeadModel.from_pretrained("gpt2")
                self.model.eval()
            except Exception as e:
                logger.warning("Could not initialize GPT-2 model (%s). Using statistical fallback.", e)
                self.tokenizer = None
                self.model = None
                self.use_neural = False

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
        # Skala estimasi kemiripan perplexity sederhana [20.0, 120.0]
        return float(20.0 + (unique_ratio * 80.0))

    def _statistical_burstiness(self, sentences: List[str]) -> tuple[float, float]:
        """Fallback statistik linguistik berbasis variasi panjang kalimat (Copyleaks/Burstiness methodology)."""
        lengths = [len(s.split()) for s in sentences if s.strip()]
        if not lengths:
            return 50.0, 1.0

        mean_len = sum(lengths) / len(lengths)
        variance = sum((x - mean_len) ** 2 for x in lengths) / max(1, len(lengths))
        std_dev = math.sqrt(variance)
        burstiness = round(std_dev / max(1.0, mean_len), 3)

        # Rata-rata perplexity estimasi
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

        # Teks AI cenderung: perplexity rendah & burstiness rendah (keseragaman pola kalimat)
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
