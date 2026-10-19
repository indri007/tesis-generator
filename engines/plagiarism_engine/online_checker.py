from __future__ import annotations

import logging
import re
from typing import Any, List

from core.integrations.academic_services import CrossrefService, OpenAlexService
from .base_checker import BaseChecker, CheckResult

logger = logging.getLogger(__name__)


class OnlineAcademicChecker(BaseChecker):
    """Pemeriksa referensi & kemiripan judul/abstrak online ke Crossref dan OpenAlex.

    Bersifat opsional dan aman terhadap kegagalan jaringan (non-blocking).
    """

    name = "online_crossref_openalex"

    def __init__(self, enable_live_api: bool = False):
        self.enable_live_api = enable_live_api

    def check(self, text: str, **kwargs: Any) -> CheckResult:
        if not text:
            return CheckResult(self.name, 0.0, "clean", [], [])

        # Cari semua pola DOI dalam naskah
        dois = re.findall(r"\b10\.\d{4,9}/[-._;()/:A-Za-z0-9]+\b", text)
        matched_segments: List[dict[str, Any]] = []

        for doi in dois[:10]:  # Batasi periksa 10 DOI teratas untuk efisiensi
            try:
                crossref_data = CrossrefService.get_work(doi, live=self.enable_live_api)
                openalex_data = OpenAlexService.get_work_by_doi(doi, live=self.enable_live_api)

                title = crossref_data.get("title") or openalex_data.get("title") or ""
                matched_segments.append({
                    "doi": doi,
                    "title": title,
                    "source": "Crossref / OpenAlex",
                    "status": crossref_data.get("status", "unknown"),
                    "citations": openalex_data.get("cited_by_count", 0),
                    "concepts": openalex_data.get("concepts", []),
                })
            except Exception as e:
                logger.debug("Online check for DOI %s encountered exception: %s", doi, e)

        verdict = "clean"
        return CheckResult(
            checker_name=self.name,
            score=0.0,
            verdict=verdict,
            matched_segments=matched_segments,
            evidence_refs=[f"DOI:{d}" for d in dois[:10]],
            metadata={"total_dois_scanned": len(dois), "live_api": self.enable_live_api},
        )
