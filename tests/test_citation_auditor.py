# tests/test_citation_auditor.py
from unittest.mock import patch, MagicMock
from engines.citation_auditor import CitationAuditor


@patch("core.mcp_client.AcademicMCPClient.search_scopus")
def test_metadata_mismatch_detected(mock_search):
    mock_search.return_value = {"results": [{
        "year": 2022, "authors": ["Smith, J."], "id": "S123"
    }]}
    auditor = CitationAuditor(scopus_client=MagicMock())
    findings = auditor.audit([{
        "text": "(Smith, 2023)", "year": 2023,
        "authors": ["Smith"], "location": "hal.5"
    }])
    assert findings[0].status == "metadata_mismatch"
    assert "Tahun" in findings[0].details["mismatches"][0]
