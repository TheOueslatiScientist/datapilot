"""Étape 7 — découpage des documents (tools.chunk_text, chunk_markdown, load_corpus)."""
import pytest

from tools import chunk_text


def test_chunk_text_taille_et_chevauchement():
    text = " ".join(f"mot{i}" for i in range(300))
    chunks = chunk_text(text, chunk_size=200, overlap=50)
    assert len(chunks) > 1
    assert all(len(c) <= 200 for c in chunks)
    # Le début du chunk 2 reprend la fin du chunk 1 (chevauchement)
    assert chunks[1].split()[0] in chunks[0]


def test_chunk_text_overlap_invalide():
    with pytest.raises(ValueError):
        chunk_text("abc", chunk_size=100, overlap=100)


def test_corpus_charge():
    from pathlib import Path
    from tools import load_corpus
    chunks = load_corpus(Path(__file__).resolve().parents[1] / "data" / "docs")
    assert len(chunks) >= 20
    assert all(c.text.startswith("[") for c in chunks)          # préfixe [Titre — Section]
    assert {c.source for c in chunks} >= {"01_glossaire_kpi.md", "02_politique_retours.md"}
