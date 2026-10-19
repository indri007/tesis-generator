import os
from typing import Any, Dict, List, Optional
from docx import Document

from utils.word_counter import count_words_excl_figures, evaluate_word_count
from engines.advanced_auditor.text_readability import TextReadabilityAuditor
from engines.advanced_auditor.reference_integrity import ReferenceIntegrityAuditor
from engines.plagiarism_engine.orchestrator import PlagiarismOrchestrator


class MasterAuditor:
    """Master Auditor: Mengorkestrasi seluruh pipeline audit naskah tesis MIKOM 2026."""

    def __init__(self, reference_corpus: Optional[List[str]] = None):
        self.ref_corpus = reference_corpus or ["Media Richness Theory", "Makan Bergizi Gratis", "Analisis Sentimen"]
        self.readability = TextReadabilityAuditor()
        self.ref_integrity = ReferenceIntegrityAuditor()
        self.plagiarism = PlagiarismOrchestrator(self.ref_corpus)

    def run_full_audit(self, docx_path: str) -> Dict[str, Any]:
        """Menjalankan seluruh pipeline audit MIKOM 2026."""
        results = {
            "status": "success",
            "scores": {},
            "findings": {}
        }

        # 1. Audit Volume Kata (40k - 60k)
        try:
            word_count = count_words_excl_figures(docx_path)
            wc_status, wc_msg, _ = evaluate_word_count(word_count)
            results["findings"]["word_count"] = {
                "total": word_count,
                "status": wc_status,
                "message": wc_msg
            }
            results["scores"]["word_count"] = 100 if wc_status == "PASS" else 50
        except Exception as e:
            results["findings"]["word_count"] = {"status": "ERROR", "message": str(e)}

        # 2. Audit Readability (Wall of Text)
        wall_issues = self.readability.audit(docx_path)
        results["findings"]["readability"] = wall_issues
        results["scores"]["readability"] = max(0, 100 - (len(wall_issues) * 5))

        # 3. Audit Konsistensi Referensi (Typo Nama)
        ref_issues = self.ref_integrity.audit(docx_path)
        results["findings"]["reference_typos"] = ref_issues
        results["scores"]["references"] = max(0, 100 - (len(ref_issues) * 10))

        # 4. Audit Plagiarisme & AI (Ambil teks 10.000 karakter pertama untuk sampel)
        try:
            doc = Document(docx_path)
            sample_text = " ".join([p.text for p in doc.paragraphs if p.text.strip()])[:10000]
            plag_report = self.plagiarism.run(sample_text)

            plag_score = getattr(plag_report, "overall_plagiarism_score", None)
            if plag_score is None and isinstance(plag_report, dict):
                plag_score = plag_report.get("overall_plagiarism_score", 0.0)
            plag_score = plag_score if plag_score is not None else 0.0

            ai_score = getattr(plag_report, "overall_ai_score", None)
            if ai_score is None and isinstance(plag_report, dict):
                ai_score = plag_report.get("overall_ai_score", 0.0)
            ai_score = ai_score if ai_score is not None else 0.0

            if hasattr(plag_report, "__dict__"):
                results["findings"]["plagiarism"] = {
                    "overall_plagiarism_score": round(float(plag_score), 3),
                    "overall_ai_score": round(float(ai_score), 3),
                    "verdict": getattr(plag_report, "verdict", "clean"),
                    "findings": getattr(plag_report, "findings", []),
                    "details": getattr(plag_report, "details", {}),
                }
            elif isinstance(plag_report, dict):
                results["findings"]["plagiarism"] = plag_report
            else:
                results["findings"]["plagiarism"] = {
                    "overall_plagiarism_score": round(float(plag_score), 3),
                    "overall_ai_score": round(float(ai_score), 3),
                    "verdict": "clean",
                    "findings": [],
                }

            results["scores"]["plagiarism"] = int((1 - plag_score) * 100)
            results["scores"]["ai_detection"] = int((1 - ai_score) * 100)
        except Exception as e:
            results["findings"]["plagiarism"] = {
                "status": "ERROR",
                "message": str(e),
                "overall_plagiarism_score": 0.0,
                "overall_ai_score": 0.0
            }

        # 5. Hitung Skor Akhir (Overall)
        valid_scores = [v for v in results["scores"].values() if isinstance(v, (int, float))]
        results["scores"]["overall"] = sum(valid_scores) // len(valid_scores) if valid_scores else 0

        return results
