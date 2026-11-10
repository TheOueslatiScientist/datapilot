"""config.py — Paramètres centralisés du projet DataPilot."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent      # dossier qui contient ce fichier

# --- Moteur LLM (Ollama) ----------------------------------------------
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
LLM_MODEL = os.getenv("LLM_MODEL", "qwen2.5:7b")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.1"))
LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT", "240"))
LLM_NUM_CTX = int(os.getenv("LLM_NUM_CTX", "4096"))
LLM_KEEP_ALIVE = os.getenv("LLM_KEEP_ALIVE", "30m")

# --- Données ------------------------------------------------------------
DB_PATH = Path(os.getenv("DB_PATH", BASE_DIR / "data" / "ecommerce.db"))
DOCS_DIR = Path(os.getenv("DOCS_DIR", BASE_DIR / "data" / "docs"))

# --- Recherche documentaire (RAG) ---------------------------------------
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 100
TOP_K = 3

# --- Agent ----------------------------------------------------------------
MAX_STEPS = 5
MAX_HISTORY_TURNS = 6
SQL_MAX_ROWS = 50

# --- Journaux ---------------------------------------------------------
LOG_DIR = BASE_DIR / "logs"
