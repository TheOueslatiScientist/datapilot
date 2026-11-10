"""Fixtures partagées. Les imports du projet sont faits DANS les fixtures :
les tests d'une étape peuvent tourner même si les fichiers des étapes suivantes n'existent pas encore."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
DB = ROOT / "data" / "ecommerce.db"


@pytest.fixture(scope="session")
def sql_tool():
    from tools import SQLTool
    if not DB.exists():
        import subprocess
        subprocess.run([sys.executable, str(ROOT / "data" / "create_db.py")], check=True)
    return SQLTool(DB)


@pytest.fixture(scope="session")
def doc_tool():
    from tests.fakes import FakeEmbedder
    from tools import DocSearchTool, load_corpus
    return DocSearchTool(load_corpus(ROOT / "data" / "docs"), FakeEmbedder(), top_k=3)
