"""Étape 12 — interface Gradio (ui.py) avec un faux agent : aucun LLM requis."""
from types import SimpleNamespace

from ui import create_ui, message_text, steps_to_messages


class FakeAgent:
    def ask(self, q):
        step = SimpleNamespace(kind="tool", tool="query_database", tool_input="SELECT 1", content="1")
        return SimpleNamespace(answer=f"Réponse à : {q}", steps=[step])

    def reset(self):
        pass


def test_ui_se_construit():
    demo = create_ui(FakeAgent())
    assert demo is not None


def test_steps_to_messages():
    msgs = steps_to_messages(FakeAgent().ask("x").steps)
    assert msgs[0]["metadata"]["title"].startswith("🔧")


def test_message_text_formats_gradio():
    assert message_text("abc") == "abc"
    assert message_text([{"type": "text", "text": "abc"}]) == "abc"
