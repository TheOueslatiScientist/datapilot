"""llm_client.py — Client LLM robuste en Python pur (bibliothèque requests)."""
from __future__ import annotations

import json
import logging
import time
from datetime import datetime
from pathlib import Path

import requests

logger = logging.getLogger("llm_client")


class LLMError(Exception):
    """Erreur définitive du client LLM (après épuisement des tentatives)."""


class LLMClient:
    RETRYABLE_STATUS = {408, 429, 500, 502, 503, 504}

    def __init__(self, model, base_url="http://localhost:11434", temperature=0.1,
                 timeout=120, max_retries=3, backoff_factor=1.0, num_ctx=8192,
                 log_file=None):
        self.model = model
        self.url = base_url.rstrip("/") + "/api/chat"
        self.base_url = base_url.rstrip("/")
        self.temperature = temperature
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.num_ctx = num_ctx
        self.log_file = Path(log_file) if log_file else None
        self.session = requests.Session()     # réutilise la connexion entre les appels

    def chat(self, messages: list[dict], json_mode: bool = False) -> str:
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": self.temperature, "num_ctx": self.num_ctx},
        }
        if json_mode:
            payload["format"] = "json"

        start = time.perf_counter()
        data = self._post_with_retry(payload)
        duration = time.perf_counter() - start

        try:
            answer = data["message"]["content"]
        except (KeyError, TypeError) as exc:
            raise LLMError(f"Réponse inattendue du serveur LLM : {data!r}") from exc

        self._log_exchange(messages, answer, duration, data)
        return answer

    def _post_with_retry(self, payload: dict) -> dict:
        last_error = None
        for attempt in range(1, self.max_retries + 1):
            try:
                response = self.session.post(self.url, json=payload, timeout=self.timeout)
                if response.status_code in self.RETRYABLE_STATUS:
                    raise requests.HTTPError(
                        f"{response.status_code} (réessayable)", response=response
                    )
                if response.status_code >= 400:
                    raise LLMError(
                        f"Erreur définitive {response.status_code} du serveur LLM : "
                        f"{response.text[:200]}"
                    )
                try:
                    return response.json()
                except ValueError as exc:
                    raise LLMError(f"Réponse non-JSON du serveur LLM : {exc}") from exc
            except (requests.ConnectionError, requests.Timeout, requests.HTTPError) as exc:
                last_error = exc
            if attempt < self.max_retries:
                wait = self.backoff_factor * 2 ** (attempt - 1)
                logger.warning(
                    "Tentative %d/%d échouée (%s), nouvelle tentative dans %.1fs",
                    attempt, self.max_retries, last_error, wait,
                )
                time.sleep(wait)
        raise LLMError(
            f"Le serveur LLM reste injoignable après {self.max_retries} tentatives "
            f"({last_error}). Vérifiez qu'Ollama est lancé (commande : ollama serve)."
        )

    def _log_exchange(self, messages, answer, duration, raw):
        if not self.log_file:
            return
        entry = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "model": self.model,
            "duration_s": round(duration, 3),
            "prompt_tokens": raw.get("prompt_eval_count"),
            "completion_tokens": raw.get("eval_count"),
            "messages": messages,
            "answer": answer,
        }
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def is_available(self) -> bool:
        try:
            r = self.session.get(f"{self.base_url}/api/tags", timeout=5)
            return r.ok
        except requests.RequestException:
            return False


class Conversation:
    """Mémoire conversationnelle sans framework : system prompt + fenêtre glissante."""

    def __init__(self, system_prompt: str, max_turns: int = 6) -> None:
        self.system_prompt = system_prompt
        self.max_turns = max_turns
        self.history: list[dict] = []

    def add_user(self, content: str) -> None:
        self.history.append({"role": "user", "content": content})

    def add_assistant(self, content: str) -> None:
        self.history.append({"role": "assistant", "content": content})

    def messages(self) -> list[dict]:
        window = self.history[-(2 * self.max_turns):]
        return [{"role": "system", "content": self.system_prompt}] + window

    def estimated_tokens(self) -> int:
        return sum(len(m["content"]) for m in self.messages()) // 4

    def reset(self) -> None:
        self.history = []
