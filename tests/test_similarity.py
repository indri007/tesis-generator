"""Standard similarity interface tests."""

from src.similarity import similarity


def test_same_text():
    assert similarity("halo dunia", "halo dunia") > 0.99


def test_different_text():
    assert similarity("halo dunia", "kucing makan") < 0.5
