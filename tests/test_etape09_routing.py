"""Étape 9 — lecture de la décision du LLM et routing (agent.parse_llm_output, route_query)."""
import pytest

from agent import ParseError, parse_llm_output, route_query


class EchoTool:
    def __init__(self):
        self.received = []

    def run(self, x, params=()):
        self.received.append((x, params))
        return f"résultat pour {x}"


def test_parse_json_propre():
    d = parse_llm_output('{"thought": "t", "action": "search_docs", "input": "CA"}')
    assert d.action == "search_docs" and d.input == "CA"


def test_parse_json_avec_texte_autour():
    d = parse_llm_output('Voici : ```json\n{"action": "final_answer", "input": "ok"}\n``` merci')
    assert d.action == "final_answer"


def test_parse_cle_alternative():
    assert parse_llm_output('{"action": "x", "action_input": "y"}').input == "y"


def test_parse_invalide():
    with pytest.raises(ParseError):
        parse_llm_output("Je pense que le CA est de 10 000 €")


def test_route_vers_outil():
    tool = EchoTool()
    r = route_query('{"action": "search_docs", "input": "panier moyen"}', {"search_docs": tool})
    assert r.kind == "tool" and r.tool == "search_docs" and "panier moyen" in r.content


def test_route_final():
    r = route_query('{"action": "final_answer", "input": "Bonjour !"}', {})
    assert r.kind == "final" and r.content == "Bonjour !"


def test_route_outil_inconnu():
    r = route_query('{"action": "send_email", "input": "x"}', {"search_docs": EchoTool()})
    assert r.kind == "error" and "Outil inconnu" in r.content


def test_route_params_sql():
    tool = EchoTool()
    route_query('{"action": "query_database", "input": "SELECT ?", "params": [1]}',
                {"query_database": tool})
    assert tool.received == [("SELECT ?", [1])]
