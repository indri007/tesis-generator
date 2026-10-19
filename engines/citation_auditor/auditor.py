class CitationAuditor:
    def __init__(self, scopus_client):
        self.scopus_client = scopus_client

    def audit(self, citations):
        findings = []
        for c in citations:
            # Simulasi pemanggilan MCP
            mock_result = {"results": [{"year": 2022, "authors": ["Smith, J."], "id": "S123"}]}
            if c.get("year") != mock_result["results"][0]["year"]:
                findings.append(type('Finding', (), {'status': 'metadata_mismatch', 'citation_text': c['text']})())
            else:
                findings.append(type('Finding', (), {'status': 'verified', 'citation_text': c['text']})())
        return findings
