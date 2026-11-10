# Kit de départ — DataPilot

Ce kit contient uniquement ce qui n'est pas l'objet du module :

- `data/` : la base SQLite `ecommerce.db` (ShopNova, ventes 2024-2025), son générateur `create_db.py` et les 6 documents métier ;
- `tests/` : un fichier de tests par étape (`test_etape03_client.py` … `test_etape12_interface.py`) et des doublures (`fakes.py`) ;
- `requirements.txt` ; `logs/` (vide).

Tout le reste (`config.py`, `llm_client.py`, `prompts.py`, `tools.py`, `agent.py`, `ui.py`, `evaluation.py`, `JOURNAL.md`),
c'est vous qui l'écrivez, en suivant le guide **Guide_projet_DataPilot.pdf**, étape par étape.

Les tests d'une étape ne passent qu'une fois l'étape réalisée : lancez seulement le fichier de l'étape en cours,
par exemple `pytest tests/test_etape06_sql.py -v`. À la fin du projet, `pytest -q` doit afficher 44 tests passés.
