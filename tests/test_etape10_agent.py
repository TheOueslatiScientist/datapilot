"""Étape 10 — la boucle de l'agent (agent.Agent) avec un faux LLM."""
from agent import Agent
from tests.fakes import FakeLLM


class EchoTool:
    def __init__(self):
        self.received = []

    def run(self, x, params=()):
        self.received.append((x, params))
        return f"résultat pour {x}"


def test_boucle_outil_puis_reponse(sql_tool):
    llm = FakeLLM([
        '{"thought": "je compte", "action": "query_database", "input": "SELECT COUNT(*) AS n FROM clients"}',
        '{"thought": "fini", "action": "final_answer", "input": "Il y a 500 clients."}',
    ])
    agent = Agent(llm, {"query_database": sql_tool}, "SYSTEM")
    resp = agent.ask("Combien de clients ?")
    assert resp.answer == "Il y a 500 clients."
    assert [s.kind for s in resp.steps] == ["tool", "final"]
    # Le 2e appel au LLM contient bien l'observation de l'outil
    assert "OBSERVATION (query_database)" in llm.calls[1][-1]["content"]
    assert "500" in llm.calls[1][-1]["content"]


def test_auto_correction_apres_erreur_format():
    llm = FakeLLM(["Le CA est élevé.", '{"action": "final_answer", "input": "ok"}'])
    resp = Agent(llm, {}, "SYSTEM").ask("CA ?")
    assert resp.answer == "ok" and resp.steps[0].kind == "error"


def test_max_steps_force_reponse():
    llm = FakeLLM(['{"action": "search_docs", "input": "x"}'] * 3 +
                  ['{"action": "final_answer", "input": "réponse forcée"}'])
    resp = Agent(llm, {"search_docs": EchoTool()}, "SYSTEM", max_steps=3).ask("?")
    assert resp.answer == "réponse forcée" and len(resp.steps) == 4


def test_memoire_conversationnelle():
    llm = FakeLLM(['{"action": "final_answer", "input": "R1"}',
                   '{"action": "final_answer", "input": "R2"}'])
    agent = Agent(llm, {}, "SYSTEM")
    agent.ask("Q1")
    agent.ask("Q2")
    contents = [m["content"] for m in llm.calls[1]]
    assert contents == ["SYSTEM", "Q1", "R1", "Q2"]
    agent.reset()
    assert agent.conversation.history == []


def test_llm_indisponible():
    from llm_client import LLMError

    class DownLLM:
        def chat(self, *a, **k):
            raise LLMError("connexion refusée")

    resp = Agent(DownLLM(), {}, "SYSTEM").ask("?")
    assert "indisponible" in resp.answer
