"""agent.py — Routing et boucle de l'agent DataPilot."""
from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field

from llm_client import Conversation, LLMError

logger = logging.getLogger("agent")

FINAL = "final_answer"


# --- Étape 9 : lire la décision du LLM et router ----------------------------

@dataclass
class Decision:
    action: str
    input: object
    thought: str = ""
    params: list = field(default_factory=list)


class ParseError(ValueError):
    pass


def parse_llm_output(raw: str) -> Decision:
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip(), flags=re.IGNORECASE)
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if not match:
            raise ParseError(f"Aucun objet JSON trouvé dans la réponse : {raw!r}")
        try:
            data = json.loads(match.group(0))
        except json.JSONDecodeError as exc:
            raise ParseError(f"JSON invalide : {exc}") from exc

    if not isinstance(data, dict) or "action" not in data:
        raise ParseError(f"Le JSON ne contient pas de clé 'action' : {data!r}")

    action = str(data["action"]).strip().lower()
    llm_input = data.get("input", data.get("action_input"))
    return Decision(
        action=action,
        input=llm_input,
        thought=str(data.get("thought", "")),
        params=data.get("params", []),
    )


@dataclass
class RouteResult:
    kind: str                      # "tool" | "final" | "error"
    content: str
    tool: str | None = None
    tool_input: object = None
    thought: str = ""


def route_query(llm_output: str, tools: dict) -> RouteResult:
    try:
        decision = parse_llm_output(llm_output)
    except ParseError:
        return RouteResult(
            kind="error",
            content=("Réponse illisible : répondez uniquement avec un objet JSON "
                     '{"thought": ..., "action": ..., "input": ...}.'),
        )

    if decision.action == FINAL:
        return RouteResult(kind="final", content=str(decision.input), thought=decision.thought)

    tool = tools.get(decision.action)
    if tool is None:
        return RouteResult(
            kind="error",
            content=f"Outil inconnu « {decision.action} ». Outils valides : "
                    f"{', '.join(tools) or 'aucun'}.",
            thought=decision.thought,
        )

    if decision.action == "query_database" and decision.params:
        content = tool.run(str(decision.input), decision.params)
    else:
        content = tool.run(str(decision.input))

    return RouteResult(kind="tool", content=content, tool=decision.action,
                        tool_input=decision.input, thought=decision.thought)


# --- Étape 10 : la boucle de l'agent ----------------------------------------

@dataclass
class AgentResponse:
    answer: str
    steps: list[RouteResult] = field(default_factory=list)


class Agent:
    def __init__(self, llm, tools: dict, system_prompt: str,
                 max_steps: int = 5, max_history_turns: int = 6) -> None:
        self.llm = llm
        self.tools = tools
        self.max_steps = max_steps
        self.conversation = Conversation(system_prompt, max_turns=max_history_turns)

    def ask(self, question: str) -> AgentResponse:
        self.conversation.add_user(question)
        scratchpad = self.conversation.messages()
        steps: list[RouteResult] = []
        answer = None
        try:
            for _ in range(self.max_steps):
                raw = self.llm.chat(scratchpad, json_mode=True)
                result = route_query(raw, self.tools)
                steps.append(result)
                if result.kind == "final":
                    answer = result.content
                    break
                scratchpad.append({"role": "assistant", "content": raw})
                if result.kind == "error":
                    observation = f"ERREUR DE FORMAT : {result.content}"
                else:
                    observation = f"OBSERVATION ({result.tool}) :\n{result.content}"
                scratchpad.append({"role": "user", "content": observation})

            if answer is None:
                scratchpad.append({
                    "role": "user",
                    "content": "Donnez votre réponse finale maintenant, au format JSON "
                                'avec "action": "final_answer".',
                })
                raw = self.llm.chat(scratchpad, json_mode=True)
                result = route_query(raw, self.tools)
                steps.append(result)
                answer = (result.content if result.kind == "final"
                          else "Je n'ai pas pu conclure dans le nombre d'étapes autorisé, "
                               "désolé.")
        except LLMError:
            answer = "Le service LLM est indisponible pour le moment, réessayez plus tard."

        self.conversation.add_assistant(answer)
        return AgentResponse(answer=answer, steps=steps)

    def reset(self) -> None:
        self.conversation.reset()


def build_agent():
    import config
    from llm_client import LLMClient
    from prompts import build_system_prompt
    from tools import DocSearchTool, SQLTool, load_corpus, load_embedder

    llm = LLMClient(config.LLM_MODEL, config.OLLAMA_URL, temperature=config.LLM_TEMPERATURE,
                     timeout=config.LLM_TIMEOUT, num_ctx=config.LLM_NUM_CTX,
                     log_file=config.LOG_DIR / "llm_exchanges.jsonl")
    sql_tool = SQLTool(config.DB_PATH, max_rows=config.SQL_MAX_ROWS)
    doc_tool = DocSearchTool(load_corpus(config.DOCS_DIR, config.CHUNK_SIZE,
                                         config.CHUNK_OVERLAP),
                              load_embedder(config.EMBEDDING_MODEL), top_k=config.TOP_K)
    tools = {sql_tool.name: sql_tool, doc_tool.name: doc_tool}
    system_prompt = build_system_prompt(sql_tool.get_schema())
    agent = Agent(llm, tools, system_prompt, max_steps=config.MAX_STEPS,
                  max_history_turns=config.MAX_HISTORY_TURNS)
    return agent, llm


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    agent, llm = build_agent()
    print("DataPilot — tapez 'quit' pour sortir, 'reset' pour vider la mémoire.")
    while True:
        question = input("\nVous > ").strip()
        if question.lower() == "quit":
            break
        if question.lower() == "reset":
            agent.reset()
            print("(mémoire vidée)")
            continue
        response = agent.ask(question)
        for step in response.steps:
            detail = step.tool or step.kind
            print(f"  [{step.kind}] {detail} : {str(step.content)[:80]}")
        print(f"DataPilot > {response.answer}")
