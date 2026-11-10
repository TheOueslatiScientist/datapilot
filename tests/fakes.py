"""
fakes.py — Doublures de test : permettent de tester chaque couche sans Ollama
et sans télécharger de modèle d'embedding.
"""
from __future__ import annotations

import hashlib
import re

import numpy as np


class FakeEmbedder:
    """Embedder « sac de mots » haché : rapide, déterministe, sans téléchargement.
    Même interface que SentenceTransformer.encode()."""

    def __init__(self, dim: int = 256) -> None:
        self.dim = dim

    def encode(self, texts, normalize_embeddings=True, convert_to_numpy=True):
        vectors = np.zeros((len(texts), self.dim), dtype="float32")
        for row, text in enumerate(texts):
            for word in re.findall(r"\w+", text.lower()):
                if len(word) < 3:
                    continue
                h = int(hashlib.md5(word.encode()).hexdigest(), 16)
                vectors[row, h % self.dim] += 1.0
        if normalize_embeddings:
            norms = np.linalg.norm(vectors, axis=1, keepdims=True)
            vectors = vectors / np.where(norms == 0, 1, norms)
        return vectors


class FakeLLM:
    """Faux LLM : renvoie des réponses écrites à l'avance, dans l'ordre."""

    def __init__(self, responses: list[str]) -> None:
        self.responses = list(responses)
        self.calls: list[list[dict]] = []

    def chat(self, messages, json_mode=False):
        self.calls.append([dict(m) for m in messages])
        if not self.responses:
            return '{"action": "final_answer", "input": "(plus de réponses scriptées)"}'
        return self.responses.pop(0)
