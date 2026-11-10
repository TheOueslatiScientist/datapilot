"""Étape 6 — outil SQL (tools.validate_sql, format_results, SQLTool)."""
import pytest

from tools import SQLValidationError, format_results, validate_sql


@pytest.mark.parametrize("sql", [
    "SELECT * FROM clients",
    "select count(*) from commandes;",
    "WITH t AS (SELECT 1 AS x) SELECT x FROM t",
    "```sql\nSELECT 1\n```",
])
def test_requetes_autorisees(sql):
    assert validate_sql(sql).upper().startswith(("SELECT", "WITH"))


@pytest.mark.parametrize("sql", [
    "DELETE FROM clients",
    "DROP TABLE clients",
    "SELECT 1; DROP TABLE clients",
    "UPDATE clients SET segment = 'VIP'",
    "PRAGMA table_info(clients)",
    "",
])
def test_requetes_refusees(sql):
    with pytest.raises(SQLValidationError):
        validate_sql(sql)


def test_select_simple(sql_tool):
    out = sql_tool.run("SELECT COUNT(*) AS n FROM clients")
    assert "| n |" in out and "500" in out


def test_requete_parametree(sql_tool):
    out = sql_tool.run("SELECT COUNT(*) AS n FROM clients WHERE segment = ?", ["VIP"])
    assert "ligne(s)" in out


def test_ecriture_refusee(sql_tool):
    assert sql_tool.run("DELETE FROM clients").startswith("ERREUR")


def test_lecture_seule_meme_si_validation_contournee(sql_tool):
    # On appelle directement la connexion : SQLite refuse l'écriture (mode=ro)
    import sqlite3
    with pytest.raises(sqlite3.OperationalError):
        with sql_tool._connect() as conn:
            conn.execute("DELETE FROM clients")


def test_erreur_sql_renvoyee_en_texte(sql_tool):
    out = sql_tool.run("SELECT colonne_inexistante FROM clients")
    assert out.startswith("ERREUR SQL") and "no such column" in out


def test_troncature(sql_tool):
    out = sql_tool.run("SELECT client_id FROM clients")
    assert "tronqué" in out


def test_schema(sql_tool):
    schema = sql_tool.get_schema()
    for table in ["clients", "produits", "commandes", "lignes_commande", "retours"]:
        assert f"CREATE TABLE {table}" in schema


def test_format_results_vide():
    assert "aucun résultat" in format_results(["a"], [])
