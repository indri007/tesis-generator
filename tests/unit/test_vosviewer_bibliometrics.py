"""Unit tests for VOSviewer Bibliometric Mapping & Science Visualization Clone."""

import json
from pathlib import Path

import pytest

from core.clones.vosviewer_bibliometrics import VOSviewerClone


@pytest.fixture
def sample_academic_corpus():
    return [
        {
            "title": "Artificial Intelligence in Digital Journalism and Automated News Production",
            "keywords": ["Artificial Intelligence", "Digital Journalism", "News Automation"],
            "year": 2024,
            "citations": 25,
        },
        {
            "title": "Machine Learning and Natural Language Processing for Editorial Newsrooms",
            "keywords": ["Machine Learning", "Natural Language Processing", "Editorial Analytics"],
            "year": 2023,
            "citations": 18,
        },
        {
            "title": "Ethical Implications of AI-Generated Content in Modern Journalism",
            "keywords": ["Artificial Intelligence", "Ethics", "Digital Journalism", "Generative AI"],
            "year": 2025,
            "citations": 12,
        },
        {
            "title": "Automated Fact-Checking Using Natural Language Processing and Knowledge Graphs",
            "keywords": ["Natural Language Processing", "Fact-Checking", "Machine Learning"],
            "year": 2024,
            "citations": 30,
        },
    ]


@pytest.fixture
def sample_scopus_csv():
    return """Title,Year,Cited by,Author Keywords,Index Keywords
"AI in News Media",2024,15,"Artificial Intelligence; Media Studies","Journalism; Automation"
"Algorithmic News Desks",2023,20,"Machine Learning; News Automation","Algorithms; Journalism"
"Ethics in Generative Media",2025,8,"Ethics; Artificial Intelligence","AI Ethics; Social Media"
"""


def test_keyword_extraction_and_cleaning():
    clone = VOSviewerClone()
    clean = clone.clean_keyword("  Artificial-Intelligence!  ")
    assert clean == "artificial-intelligence"

    text = "Artificial intelligence enables automated news verification in modern media."
    terms = clone.extract_keywords_from_text(text)
    assert "artificial" in terms
    assert "intelligence" in terms
    assert "automated" in terms
    assert "artificial intelligence" in terms


def test_build_from_documents(sample_academic_corpus):
    clone = VOSviewerClone()
    summary = clone.build_from_documents(sample_academic_corpus, min_occurrences=1)

    assert summary["total_items"] > 0
    assert summary["total_links"] > 0
    assert summary["total_clusters"] >= 1
    assert "artificial intelligence" in clone.label_to_id

    # Check item attributes
    ai_id = clone.label_to_id["artificial intelligence"]
    ai_item = clone.items[ai_id]
    assert ai_item.occurrences >= 2
    assert ai_item.total_link_strength > 0
    assert 2023 <= ai_item.avg_pub_year <= 2025
    assert -5.0 <= ai_item.x <= 5.0
    assert -5.0 <= ai_item.y <= 5.0


def test_build_from_scopus_csv(sample_scopus_csv):
    clone = VOSviewerClone()
    summary = clone.build_from_scopus_csv(sample_scopus_csv, min_occurrences=1)

    assert summary["total_items"] >= 4
    assert summary["total_links"] >= 1
    assert "artificial intelligence" in clone.label_to_id


def test_vos_map_export(sample_academic_corpus, tmp_path: Path):
    clone = VOSviewerClone()
    clone.build_from_documents(sample_academic_corpus)

    map_path = tmp_path / "test_vos.map"
    content = clone.export_vos_map(map_path)

    assert map_path.exists()
    assert "id\tlabel\tx\ty\tcluster\tweight<Occurrences>" in content
    lines = content.strip().splitlines()
    assert len(lines) == len(clone.items) + 1  # header + items


def test_vos_network_export(sample_academic_corpus, tmp_path: Path):
    clone = VOSviewerClone()
    clone.build_from_documents(sample_academic_corpus)

    net_path = tmp_path / "test_vos.net"
    content = clone.export_vos_network(net_path)

    assert net_path.exists()
    assert "source\ttarget\tweight" in content
    lines = content.strip().splitlines()
    assert len(lines) == len(clone.links) + 1


def test_vosviewer_online_json_export(sample_academic_corpus, tmp_path: Path):
    clone = VOSviewerClone()
    clone.build_from_documents(sample_academic_corpus)

    json_path = tmp_path / "vosviewer_online.json"
    content = clone.export_vosviewer_online_json(json_path)

    data = json.loads(content)
    assert "network" in data
    assert "config" in data
    assert "items" in data["network"]
    assert "links" in data["network"]
    assert len(data["network"]["items"]) == len(clone.items)
    assert len(data["network"]["links"]) == len(clone.links)


def test_ascii_graph_generation(sample_academic_corpus):
    clone = VOSviewerClone()
    clone.build_from_documents(sample_academic_corpus)

    graph = clone.generate_ascii_graph()
    assert "VOSVIEWER BIBLIOMETRIC CO-OCCURRENCE MAP" in graph
    assert "Nodes (Items):" in graph
    assert "CLUSTER" in graph
