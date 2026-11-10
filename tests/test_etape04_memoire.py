"""Étape 4 — mémoire conversationnelle (llm_client.Conversation)."""
from llm_client import Conversation


def test_conversation_fenetre_glissante():
    conv = Conversation("SYS", max_turns=2)
    for i in range(5):
        conv.add_user(f"Q{i}")
        conv.add_assistant(f"R{i}")
    msgs = conv.messages()
    assert msgs[0] == {"role": "system", "content": "SYS"}
    assert [m["content"] for m in msgs[1:]] == ["Q3", "R3", "Q4", "R4"]
