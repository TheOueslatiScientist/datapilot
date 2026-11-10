"""Étape 8 — recherche documentaire (tools.DocSearchTool) avec un faux embedder."""


def test_recherche_pertinente(doc_tool):
    results = doc_tool.search("délai de retour pour les clients VIP 60 jours")
    sources = [c.source for _, c in results]
    assert "02_politique_retours.md" in sources


def test_run_cite_les_sources(doc_tool):
    out = doc_tool.run("définition du panier moyen")
    assert "source :" in out and "Passage 1" in out
