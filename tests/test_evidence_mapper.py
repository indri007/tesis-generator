from types import SimpleNamespace

from engines.evidence_mapper import (
    find_evidence_locations,
    map_finding_to_evidence,
    normalize_text,
)


def test_normalize_text():
    assert normalize_text("  BAB I\n   PENDAHULUAN ") == (
        "BAB I PENDAHULUAN"
    )


def test_find_evidence_with_page():
    document = SimpleNamespace(
        paragraphs=[
            SimpleNamespace(
                text="BAB I PENDAHULUAN",
                page=3,
                section="BAB I",
            )
        ]
    )
    results = find_evidence_locations(
        document, "BAB I PENDAHULUAN"
    )
    assert len(results) == 1
    assert results[0]["page"] == 3


def test_missing_evidence_is_unverified():
    document = SimpleNamespace(
        paragraphs=[
            SimpleNamespace(
                text="BAB I PENDAHULUAN",
                page=3,
                section="BAB I",
            )
        ]
    )
    finding = {
        "rule_id": "TEST-001",
        "status": "ERROR",
        "category": "Format",
        "description": "Uji bukti tidak ada",
        "evidence_query": "Teks Yang Tidak Ada",
        "recommendation": "Perbaiki",
        "source": {"title": "Pedoman MIKOM 2026", "page": 10, "verified": True}
    }
    result = map_finding_to_evidence(finding, document)
    assert result["mapping_status"] == "UNVERIFIED"
    assert result["evidence_verified"] is False
    assert result["page"] is None
