"""tools.py — Les outils de l'agent : SQL (partie 1) et recherche documentaire (parties
2 et 3)."""
from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path

import numpy as np

FORBIDDEN = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|REPLACE|TRUNCATE|ATTACH|DETACH|PRAGMA|"
    r"VACUUM|REINDEX)\b",
    re.IGNORECASE,
)


# --- Étape 6 : l'outil SQL sécurisé ----------------------------------------

class SQLValidationError(ValueError):
    """Requête refusée avant exécution."""


def validate_sql(sql: str) -> str:
    cleaned = sql.strip().rstrip(";").strip()
    cleaned = re.sub(r"^```(?:sql)?|```$", "", cleaned, flags=re.IGNORECASE).strip()
    if not cleaned:
        raise SQLValidationError("requête vide")
    if ";" in cleaned:
        raise SQLValidationError("plusieurs instructions ne sont pas autorisées")
    if not re.match(r"^(SELECT|WITH)\b", cleaned, re.IGNORECASE):
        raise SQLValidationError("seules les requêtes SELECT ou WITH sont autorisées")
    forbidden = FORBIDDEN.search(cleaned)
    if forbidden:
        raise SQLValidationError(f"mot-clé interdit : {forbidden.group(0)}")
    return cleaned


def format_results(columns: list[str], rows: list[tuple], truncated: bool = False) -> str:
    if not rows:
        return "0 ligne(s) : aucun résultat."
    header = "| " + " | ".join(columns) + " |"
    separator = "|" + "|".join("---" for _ in columns) + "|"
    lines = [header, separator]
    for row in rows:
        cells = []
        for value in row:
            if value is None:
                cells.append("NULL")
            elif isinstance(value, float):
                cells.append(f"{value:.2f}")
            else:
                cells.append(str(value))
        lines.append("| " + " | ".join(cells) + " |")
    table = "\n".join(lines)
    note = " (résultat tronqué)" if truncated else ""
    return f"{len(rows)} ligne(s){note} :\n{table}"


class SQLTool:
    name = "query_database"
    description = "Exécute UNE requête SQL SELECT (SQLite) sur la base e-commerce."

    def __init__(self, db_path, max_rows: int = 50) -> None:
        self.db_path = Path(db_path)
        if not self.db_path.exists():
            raise FileNotFoundError(
                f"Base introuvable : {self.db_path}. Lancez data/create_db.py."
            )
        self.max_rows = max_rows

    def _connect(self) -> sqlite3.Connection:
        uri = f"{self.db_path.resolve().as_uri()}?mode=ro"
        conn = sqlite3.connect(uri, uri=True)
        conn.execute("PRAGMA query_only = ON")
        return conn

    def run(self, sql: str, params=()) -> str:
        try:
            cleaned = validate_sql(sql)
        except SQLValidationError as exc:
            return f"ERREUR : requête refusée — {exc}"
        try:
            with self._connect() as conn:
                cursor = conn.execute(cleaned, params)
                columns = [d[0] for d in cursor.description] if cursor.description else []
                rows = cursor.fetchmany(self.max_rows + 1)
        except sqlite3.Error as exc:
            return f"ERREUR SQL : {exc}. Corrigez la requête et réessayez."
        truncated = len(rows) > self.max_rows
        if truncated:
            rows = rows[: self.max_rows]
        return format_results(columns, rows, truncated=truncated)

    def get_schema(self) -> str:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT sql FROM sqlite_master WHERE type = 'table' AND sql IS NOT NULL"
            ).fetchall()
        return "\n\n".join(r[0] for r in rows)


# --- Étape 7 : découper la documentation -----------------------------------

@dataclass
class Chunk:
    text: str
    source: str
    section: str


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 100) -> list[str]:
    if overlap >= chunk_size:
        raise ValueError("overlap doit être strictement inférieur à chunk_size")
    words = text.split()
    chunks: list[str] = []
    current = ""
    i = 0
    while i < len(words):
        word = words[i]
        candidate = f"{current} {word}".strip() if current else word
        if not current or len(candidate) <= chunk_size:
            current = candidate
            i += 1
        else:
            chunks.append(current)
            tail = current[-overlap:]
            current = tail.split(" ", 1)[1] if " " in tail else ""
    if current:
        chunks.append(current)
    return chunks


def chunk_markdown(text: str, source: str, chunk_size: int = 500,
                    overlap: int = 100) -> list[Chunk]:
    title_match = re.search(r"^#\s+(.+)$", text, flags=re.MULTILINE)
    title = title_match.group(1).strip() if title_match else source

    chunks: list[Chunk] = []
    for index, part in enumerate(re.split(r"^##\s+", text, flags=re.MULTILINE)):
        if index == 0:
            section = "Introduction"
            content = re.sub(r"^#\s+.+$", "", part, count=1, flags=re.MULTILINE).strip()
        else:
            heading, _, rest = part.partition("\n")
            section = heading.strip()
            content = rest.strip()
        if not content:
            continue
        for morceau in chunk_text(content, chunk_size, overlap):
            chunks.append(Chunk(text=f"[{title} — {section}] {morceau}",
                                 source=source, section=section))
    return chunks


def load_corpus(docs_dir, chunk_size: int = 500, overlap: int = 100) -> list[Chunk]:
    docs_dir = Path(docs_dir)
    files = sorted(docs_dir.glob("*.md"))
    if not files:
        raise FileNotFoundError(f"Aucun fichier .md trouvé dans {docs_dir}")
    chunks: list[Chunk] = []
    for file in files:
        text = file.read_text(encoding="utf-8")
        chunks.extend(chunk_markdown(text, file.name, chunk_size, overlap))
    return chunks


# --- Étape 8 : embeddings, FAISS et recherche documentaire -----------------

class DocSearchTool:
    name = "search_docs"
    description = ("Recherche dans la documentation métier (KPI, retours, segmentation, "
                    "données, livraison, reporting).")

    def __init__(self, chunks: list[Chunk], embedder, top_k: int = 3) -> None:
        import faiss  # import local : l'outil SQL reste utilisable sans FAISS

        self.chunks = chunks
        self.embedder = embedder
        self.top_k = top_k
        vectors = self._embed([c.text for c in chunks])
        self.index = faiss.IndexFlatIP(vectors.shape[1])
        self.index.add(vectors)

    def _embed(self, texts: list[str]) -> np.ndarray:
        vectors = self.embedder.encode(texts, normalize_embeddings=True,
                                        convert_to_numpy=True)
        return np.asarray(vectors, dtype="float32")

    def search(self, query: str, k: int | None = None) -> list[tuple[float, Chunk]]:
        k = min(k or self.top_k, len(self.chunks))
        query_vector = self._embed([query])
        scores, ids = self.index.search(query_vector, k)
        return [(float(score), self.chunks[idx])
                for score, idx in zip(scores[0], ids[0]) if idx != -1]

    def run(self, query: str) -> str:
        results = self.search(query)
        if not results:
            return "Aucun passage pertinent trouvé dans la documentation."
        passages = []
        for i, (score, chunk) in enumerate(results, start=1):
            passages.append(
                f"[Passage {i} — source : {chunk.source}, section « {chunk.section} », "
                f"score {score:.2f}]\n{chunk.text}"
            )
        return "\n\n".join(passages)


def load_embedder(model_name: str):
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(model_name)
