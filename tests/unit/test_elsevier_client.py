"""Unit tests for Elsevier ScienceDirect & Scopus integration module."""

from __future__ import annotations

import pytest
from core.integrations.elsevier_client import (
    ElsevierArticle,
    ElsevierClient,
    ElsevierSearchResult,
    normalize_doi,
    parse_elsevier_ris,
    parse_scopus_csv,
)


def test_normalize_doi():
    assert normalize_doi("https://doi.org/10.1016/j.tele.2023.102045") == "10.1016/j.tele.2023.102045"
    assert normalize_doi("doi: 10.1016/j.jenvman.2022.115012 ") == "10.1016/j.jenvman.2022.115012"
    assert normalize_doi("10.1016/S0140-6736(20)30183-5") == "10.1016/s0140-6736(20)30183-5"
    assert normalize_doi(None) is None
    assert normalize_doi("") is None


def test_parse_scopus_csv():
    scopus_csv = """Authors,Title,Year,Source title,Volume,Issue,Art. No.,Page start,Page end,Page count,Cited by,DOI,Link,Affiliations,Authors with affiliations,Abstract,Author Keywords,Index Keywords,Correspondence Address,Publisher,ISSN,ISBN,CODEN,PubMed ID,Language of Original Document,Abbreviated Source Title,Document Type,Publication Stage,Open Access,Source,EID
"Santoso B., Rahmawati A.","Artificial Intelligence in Journalism",2023,"Telematics and Informatics",80,,,102045,,,48,10.1016/j.tele.2023.102045,https://scopus.com,...,...,"Analyzing newsroom automation.",ai; journalism,,...,Elsevier,07365853,,,,English,Telem. Inf.,Article,Final,All Open Access,Scopus,2-s2.0-85150241092
"Smith J.","Environmental Framing",2022,"Journal of Environmental Management",312,,,,,,35,10.1016/j.jenvman.2022.115012,https://scopus.com,...,...,"Public perception framing.",framing,,...,Elsevier,03014797,,,,English,J. Env. Man.,Article,Final,,Scopus,2-s2.0-85128741291
"""
    res = parse_scopus_csv(scopus_csv, query="AI Journalism")
    assert res.total_results == 2
    assert res.q1_count >= 1
    assert res.open_access_count == 1
    assert res.articles[0].doi == "10.1016/j.tele.2023.102045"
    assert res.articles[0].cited_by_count == 48
    assert res.articles[0].quartile == "Q1"
    assert res.articles[1].cited_by_count == 35


def test_parse_elsevier_ris():
    ris_content = """TY  - JOUR
TI  - Machine Learning Approaches in Natural Language Processing for Academic Syntheses
AU  - Brown, T.
AU  - Davis, M.
JO  - Computer Science Review
PY  - 2024
VL  - 52
DO  - 10.1016/j.cosrev.2024.100612
AB  - Comprehensive survey on transformer-based language representations.
KW  - nlp
KW  - machine learning
ER  -
"""
    res = parse_elsevier_ris(ris_content, query="NLP")
    assert res.total_results == 1
    art = res.articles[0]
    assert art.title.startswith("Machine Learning Approaches")
    assert len(art.authors) == 2
    assert art.year == "2024"
    assert art.doi == "10.1016/j.cosrev.2024.100612"
    assert art.quartile == "Q1"


def test_elsevier_client_offline_search_and_doi_lookup():
    client = ElsevierClient()
    # Search query
    res = client.search_articles("journalism")
    assert res.total_results >= 1
    assert any("journalism" in a.title.lower() for a in res.articles)
    assert res.q1_count >= 1

    # Exact DOI lookup
    art = client.get_by_doi("10.1016/j.tele.2023.102045")
    assert art is not None
    assert art.journal == "Telematics and Informatics"
    assert art.quartile == "Q1"
    assert art.cited_by_count == 48

    # Non-existent DOI
    assert client.get_by_doi("10.9999/nonexistent.doi") is None
