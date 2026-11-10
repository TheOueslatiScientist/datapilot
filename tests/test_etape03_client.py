"""Étape 3 — client LLM (llm_client.LLMClient). Faux serveur HTTP local : aucun Ollama requis."""
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from llm_client import LLMClient, LLMError


class FakeOllama(BaseHTTPRequestHandler):
    script: list = []          # codes HTTP à renvoyer, dans l'ordre
    received: list = []

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        FakeOllama.received.append(body)
        status = FakeOllama.script.pop(0) if FakeOllama.script else 200
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        if status == 200:
            self.wfile.write(json.dumps({"message": {"role": "assistant", "content": "pong"},
                                         "eval_count": 3, "prompt_eval_count": 10}).encode())
        else:
            self.wfile.write(b'{"error": "boom"}')

    def log_message(self, *args):
        pass


@pytest.fixture
def server():
    httpd = HTTPServer(("127.0.0.1", 0), FakeOllama)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    FakeOllama.script, FakeOllama.received = [], []
    yield f"http://127.0.0.1:{httpd.server_port}"
    httpd.shutdown()


def make_client(url, tmp_path=None, **kw):
    return LLMClient(model="test", base_url=url, backoff_factor=0.01,
                     log_file=(tmp_path / "log.jsonl") if tmp_path else None, **kw)


def test_chat_ok_et_payload(server, tmp_path):
    client = make_client(server, tmp_path)
    assert client.chat([{"role": "user", "content": "ping"}], json_mode=True) == "pong"
    sent = FakeOllama.received[0]
    assert sent["stream"] is False and sent["format"] == "json" and sent["model"] == "test"
    log = (tmp_path / "log.jsonl").read_text(encoding="utf-8").strip().splitlines()
    assert json.loads(log[0])["answer"] == "pong"


def test_retry_sur_erreur_temporaire(server):
    FakeOllama.script = [503, 500]          # 2 échecs puis succès
    assert make_client(server, max_retries=3).chat([{"role": "user", "content": "x"}]) == "pong"
    assert len(FakeOllama.received) == 3


def test_pas_de_retry_sur_404(server):
    FakeOllama.script = [404]
    with pytest.raises(LLMError, match="404"):
        make_client(server).chat([{"role": "user", "content": "x"}])
    assert len(FakeOllama.received) == 1


def test_serveur_injoignable():
    client = LLMClient(model="m", base_url="http://127.0.0.1:9", max_retries=2,
                       backoff_factor=0.01, timeout=1)
    with pytest.raises(LLMError, match="ollama serve"):
        client.chat([{"role": "user", "content": "x"}])
