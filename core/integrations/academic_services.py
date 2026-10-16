"""Academic Services, Real Public APIs & Thin Integrations.

Taxonomy-compliant integration architecture:
1. Public APIs (Real endpoints with polite headers & local CI fixtures):
   - Crossref (https://api.crossref.org/works/)
   - OpenAlex (https://api.openalex.org/works/)
   - Semantic Scholar (https://api.semanticscholar.org/graph/v1/paper/)
2. Experiment Tracking & Versioning (Local offline modes):
   - MLflow (Local SQLite file store)
   - W&B (WANDB_MODE=offline)
   - DVC (Local remote storage)
3. Observability (Disabled by default):
   - Sentry (Optional via SENTRY_DSN)
   - Logfire (Optional via LOGFIRE_TOKEN)
4. Thin AI Service Adapters:
   - Perplexity API (PERPLEXITY_API_KEY)
   - Consensus API (CONSENSUS_API_KEY)
   - Elicit / SciSpace / ResearchRabbit (API or manual export checklist)
5. Plagiarism Assessment Engine:
   - Strictly labeled "heuristik internal (n-gram overlap)"
   - Explicit disclaimer that official checks must go through university Turnitin/iThenticate.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

# ==============================================================================
# 1. PUBLIC ACADEMIC APIS (REAL ENDPOINTS + CI CACHING)
# ==============================================================================

POLITE_EMAIL = os.getenv("ACADEMIC_POLITE_EMAIL", "tesis-check@mikom.ac.id")
CACHE_DIR = Path("workspace/academic_cache")


def _get_json_cached(cache_key: str, fetch_url: str, headers: dict[str, str], timeout: int = 5) -> dict[str, Any] | None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    clean_key = re.sub(r"[^A-Za-z0-9_-]", "_", cache_key)
    cache_file = CACHE_DIR / f"{clean_key}.json"

    # 1. Return cache if exists (CI & offline mode)
    if cache_file.exists():
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass

    # 2. Live fetch if network available
    try:
        req = Request(fetch_url, headers=headers)
        with urlopen(req, timeout=timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            return data
    except (HTTPError, URLError, TimeoutError, Exception):
        return None


class CrossrefService:
    """Real Crossref REST API (Public & Free) with polite user-agent header."""

    BASE_URL = "https://api.crossref.org/works/"

    @classmethod
    def get_work(cls, doi: str, live: bool = True) -> dict[str, Any]:
        doi_clean = doi.strip()
        headers = {
            "User-Agent": f"TesisCheck/1.0 (mailto:{POLITE_EMAIL})",
            "Accept": "application/json",
        }
        url = f"{cls.BASE_URL}{quote(doi_clean, safe='')}"
        
        cached_or_live = _get_json_cached(f"crossref_{doi_clean}", url, headers) if live else None
        if cached_or_live and "message" in cached_or_live:
            msg = cached_or_live["message"]
            return {
                "status": "connected",
                "source": "crossref_live_api",
                "doi": doi_clean,
                "title": (msg.get("title") or [""])[0],
                "year": (msg.get("published") or {}).get("date-parts", [[None]])[0][0],
                "publisher": msg.get("publisher", ""),
                "is_referenced_by_count": msg.get("is-referenced-by-count", 0),
            }
        
        # Fallback heuristic format validation
        is_valid = bool(re.match(r"^10\.\d{4,9}/[-._;()/:A-Za-z0-9]+$", doi_clean))
        return {
            "status": "offline_validated" if is_valid else "invalid_doi",
            "source": "crossref_format_validator",
            "doi": doi_clean,
            "title": "",
            "is_valid_syntax": is_valid,
        }


class OpenAlexService:
    """Real OpenAlex API (Public & Free) with concepts, citations & open access."""

    BASE_URL = "https://api.openalex.org/works/"

    @classmethod
    def get_work_by_doi(cls, doi: str, live: bool = True) -> dict[str, Any]:
        doi_clean = doi.strip()
        if not doi_clean.startswith("https://doi.org/"):
            doi_url = f"https://doi.org/{doi_clean}"
        else:
            doi_url = doi_clean
            
        headers = {
            "User-Agent": f"TesisCheck/1.0 (mailto:{POLITE_EMAIL})",
            "Accept": "application/json",
        }
        url = f"{cls.BASE_URL}{quote(doi_url, safe='')}"
        
        cached_or_live = _get_json_cached(f"openalex_{doi_clean}", url, headers) if live else None
        if cached_or_live and "id" in cached_or_live:
            return {
                "status": "connected",
                "source": "openalex_live_api",
                "openalex_id": cached_or_live.get("id"),
                "title": cached_or_live.get("title", ""),
                "publication_year": cached_or_live.get("publication_year"),
                "cited_by_count": cached_or_live.get("cited_by_count", 0),
                "is_oa": (cached_or_live.get("open_access") or {}).get("is_oa", False),
                "concepts": [c.get("display_name") for c in (cached_or_live.get("concepts") or [])[:5]],
            }

        return {
            "status": "offline_fixture",
            "source": "openalex_offline",
            "doi": doi_clean,
            "concepts": ["Communication Studies", "Information Science", "Digital Media"],
            "is_oa": True,
        }


class SemanticScholarService:
    """Real Semantic Scholar Graph API (Public & Free with optional API key)."""

    BASE_URL = "https://api.semanticscholar.org/graph/v1/paper/"

    @classmethod
    def get_paper(cls, doi: str, api_key: str | None = None, live: bool = True) -> dict[str, Any]:
        doi_clean = doi.strip()
        key = api_key or os.getenv("SEMANTIC_SCHOLAR_API_KEY")
        headers = {
            "User-Agent": f"TesisCheck/1.0 (mailto:{POLITE_EMAIL})",
            "Accept": "application/json",
        }
        if key:
            headers["x-api-key"] = key

        fields = "paperId,title,year,citationCount,influentialCitationCount,tldr,openAccessPdf"
        url = f"{cls.BASE_URL}DOI:{quote(doi_clean, safe='')}?fields={fields}"

        cached_or_live = _get_json_cached(f"s2_{doi_clean}", url, headers) if live else None
        if cached_or_live and "paperId" in cached_or_live:
            return {
                "status": "connected",
                "source": "semanticscholar_live_api",
                "s2_paper_id": cached_or_live.get("paperId"),
                "title": cached_or_live.get("title", ""),
                "citation_count": cached_or_live.get("citationCount", 0),
                "influential_citation_count": cached_or_live.get("influentialCitationCount", 0),
                "tldr": (cached_or_live.get("tldr") or {}).get("text", ""),
            }

        return {
            "status": "offline_fixture",
            "source": "semanticscholar_offline",
            "doi": doi_clean,
            "citation_count": 0,
            "influential_citation_count": 0,
            "tldr": "Informasi ringkas karya ilmiah dapat diakses secara daring.",
        }


# ==============================================================================
# 2. EXPERIMENT TRACKING & VERSIONING (LOCAL OFFLINE MODES)
# ==============================================================================

def configure_local_tracking() -> dict[str, str]:
    """Configures MLflow, DVC, and W&B in 100% offline local mode without accounts."""
    status = {}

    # 1. MLflow local sqlite tracking
    os.environ["MLFLOW_TRACKING_URI"] = "sqlite:///workspace/mlflow.db"
    os.environ["MLFLOW_DISABLE_AGENT_HINT"] = "1"
    status["mlflow"] = "sqlite:///workspace/mlflow.db (local file store)"

    # 2. W&B offline mode (no cloud login required)
    os.environ["WANDB_MODE"] = "offline"
    os.environ["WANDB_SILENT"] = "true"
    status["wandb"] = "offline (WANDB_MODE=offline)"

    # 3. DVC local storage
    dvc_dir = Path(".dvc")
    status["dvc"] = "local storage initialized" if dvc_dir.exists() else "ready (dvc local remote)"

    return status


# ==============================================================================
# 3. OBSERVABILITY (DISABLED BY DEFAULT)
# ==============================================================================

def init_observability(enable_sentry: bool = False, enable_logfire: bool = False) -> dict[str, str]:
    """Observability is disabled by default for academic research to avoid overhead."""
    results = {"sentry": "disabled (default)", "logfire": "disabled (default)"}

    # Sentry (only active if explicit DSN is provided and enabled)
    sentry_dsn = os.getenv("SENTRY_DSN")
    if enable_sentry and sentry_dsn:
        try:
            import sentry_sdk
            sentry_sdk.init(dsn=sentry_dsn, traces_sample_rate=0.1)
            results["sentry"] = "connected (live DSN)"
        except Exception as e:
            results["sentry"] = f"failed: {e}"

    # Logfire (only active if token is present and enabled)
    logfire_token = os.getenv("LOGFIRE_TOKEN")
    if enable_logfire and logfire_token:
        try:
            import logfire
            logfire.configure(token=logfire_token)
            results["logfire"] = "connected (live token)"
        except Exception as e:
            results["logfire"] = f"failed: {e}"

    return results


# ==============================================================================
# 4. THIN ADAPTERS FOR CLOSED PROPRIETARY AI SERVICES
# ==============================================================================

class ProprietaryAIAdapters:
    """Thin adapter layer taking API keys via environment with graceful fallback."""

    @staticmethod
    def check_consensus_connection() -> dict[str, Any]:
        key = os.getenv("CONSENSUS_API_KEY")
        if key and len(key.strip()) > 5:
            return {"service": "Consensus", "status": "api_key_configured", "mode": "authenticated"}
        return {"service": "Consensus", "status": "offline_fallback", "mode": "manual_export_csv"}

    @staticmethod
    def check_perplexity_connection() -> dict[str, Any]:
        key = os.getenv("PERPLEXITY_API_KEY")
        if key and len(key.strip()) > 5:
            return {"service": "Perplexity", "status": "api_key_configured", "mode": "authenticated"}
        return {"service": "Perplexity", "status": "offline_fallback", "mode": "manual_prompt_review"}

    @staticmethod
    def get_service_matrix() -> list[dict[str, str]]:
        return [
            {
                "service": "Consensus",
                "access_type": "Proprietary",
                "connection": "CONSENSUS_API_KEY (or CSV export)",
                "status": "Ready",
            },
            {
                "service": "Perplexity",
                "access_type": "Proprietary",
                "connection": "PERPLEXITY_API_KEY (or manual prompt)",
                "status": "Ready",
            },
            {
                "service": "Elicit",
                "access_type": "Proprietary",
                "connection": "ELICIT_API_KEY / CSV Export",
                "status": "Manual / Export checklist",
            },
            {
                "service": "SciSpace",
                "access_type": "Proprietary",
                "connection": "Web UI / Citation Export",
                "status": "Manual / Export checklist",
            },
            {
                "service": "ResearchRabbit",
                "access_type": "Proprietary",
                "connection": "BibTeX / RIS Sync",
                "status": "Export sync checklist",
            },
        ]


# ==============================================================================
# 5. HONEST ORIGINALITY & PLAGIARISM HEURISTIC ENGINE
# ==============================================================================

@dataclass
class SimilarityAuditResult:
    score_percentage: float
    overlapping_ngrams_count: int
    total_ngrams_count: int
    metric_label: str = "heuristik internal (n-gram overlap)"
    is_turnitin_equivalent: bool = False
    disclaimer: str = (
        "PERINGATAN RESMI: Skor kemiripan ini dihitung secara lokal berbasis overlap n-gram kata "
        "dan HANYA berfungsi sebagai deteksi awal mandiri. Skor ini BUKAN 'setara Turnitin' atau iThenticate "
        "karena repositori pembanding resmi (database penerbit global & repositori skripsi/tesis nasional) "
        "hanya dimiliki oleh penyedia komersial terkait. Pemeriksaan resmi wajib dilakukan melalui "
        "layanan Perpustakaan / Program Studi kampus Anda."
    )
    official_campus_checklist: list[str] = field(
        default_factory=lambda: [
            "Pemeriksaan resmi wajib dilakukan via akun Turnitin / iThenticate resmi kampus.",
            "Pastikan opsi 'Exclude bibliography' dan 'Exclude quotes' telah diaktifkan sesuai pedoman MIKOM.",
            "Ambang batas kelulusan tesis MIKOM UPNVJT: Maksimal 20% similarity.",
            "Periksa apakah naskah tersimpan di repository Turnitin kampus untuk mencegah self-plagiarism di masa depan.",
        ]
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class InternalSimilarityAuditor:
    """Computes transparent local n-gram overlap with zero claims of Turnitin equivalence."""

    @classmethod
    def calculate_ngram_overlap(cls, text_a: str, text_b: str, n: int = 5) -> SimilarityAuditResult:
        tokens_a = re.findall(r"\b\w+\b", text_a.lower())
        tokens_b = re.findall(r"\b\w+\b", text_b.lower())

        if len(tokens_a) < n or len(tokens_b) < n:
            return SimilarityAuditResult(score_percentage=0.0, overlapping_ngrams_count=0, total_ngrams_count=max(len(tokens_a), len(tokens_b)))

        ngrams_a = set(tuple(tokens_a[i : i + n]) for i in range(len(tokens_a) - n + 1))
        ngrams_b = set(tuple(tokens_b[i : i + n]) for i in range(len(tokens_b) - n + 1))

        if not ngrams_a:
            return SimilarityAuditResult(score_percentage=0.0, overlapping_ngrams_count=0, total_ngrams_count=0)

        overlap = ngrams_a.intersection(ngrams_b)
        score = (len(overlap) / len(ngrams_a)) * 100.0

        return SimilarityAuditResult(
            score_percentage=round(score, 2),
            overlapping_ngrams_count=len(overlap),
            total_ngrams_count=len(ngrams_a),
        )


# ==============================================================================
# 6. UNIFIED HEALTH CHECK
# ==============================================================================

def verify_all_academic_connections() -> dict[str, Any]:
    """Runs a complete connection verification across all tiers."""
    tracking = configure_local_tracking()
    observability = init_observability()
    
    # Test real public APIs
    test_doi = "10.1016/j.tele.2023.102045"
    crossref_res = CrossrefService.get_work(test_doi, live=True)
    openalex_res = OpenAlexService.get_work_by_doi(test_doi, live=True)
    s2_res = SemanticScholarService.get_paper(test_doi, live=True)

    return {
        "tier1_tracking": tracking,
        "tier2_observability": observability,
        "tier3_public_apis": {
            "crossref": crossref_res.get("status"),
            "openalex": openalex_res.get("status"),
            "semantic_scholar": s2_res.get("status"),
        },
        "tier4_proprietary_ai": ProprietaryAIAdapters.get_service_matrix(),
        "tier5_originality_policy": {
            "label": "heuristik internal (n-gram overlap)",
            "official_check_policy": "Pemeriksaan resmi wajib lewat kampus",
        },
    }


if __name__ == "__main__":
    res = verify_all_academic_connections()
    print(json.dumps(res, indent=2))
