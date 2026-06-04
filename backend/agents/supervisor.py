"""
LangGraph supervisor (entry point for /chat).

Coordinates three specialists — restaurant_agent, travel_agent, shopping_agent —
each a create_agent ReAct agent given ONLY its own tools. The supervisor (LLM
router) classifies intent, delegates to one specialist, and returns the result.

LLM fallback is GRAPH-LEVEL: one compiled supervisor per provider (gemini/ollama).
run_chat tries Gemini first and falls back to a local Ollama model if the Gemini
call fails. Conversation state is persisted by a SqliteSaver keyed by thread_id.
"""
from __future__ import annotations

import sqlite3
from typing import Any, Optional

from loguru import logger

from ..config import settings
from ..services.llm import LLMNotConfiguredError, default_provider, get_chat_llm, providers_in_order

_checkpointer = None
_supervisors: dict[str, Any] = {}

SUPERVISOR_PROMPT = (
    "You are the Kensho supervisor coordinating three specialists:\n"
    "- restaurant_agent: restaurants, menus, dishes, food ordering (cart + handoff).\n"
    "- travel_agent: flights, hotels, and trip itineraries — metasearch only, no booking.\n"
    "- shopping_agent: product search across merchants.\n"
    "Classify the user's request and delegate to exactly ONE specialist, then return "
    "its answer. For ambiguous or multi-domain requests, choose the best-fit specialist. "
    "Do not answer domain questions yourself — always delegate."
)


def get_checkpointer():
    """Long-lived SqliteSaver (single connection, shared across the threadpool)."""
    global _checkpointer
    if _checkpointer is None:
        from langgraph.checkpoint.sqlite import SqliteSaver

        conn = sqlite3.connect(settings.CHECKPOINTER_DB_PATH, check_same_thread=False)
        _checkpointer = SqliteSaver(conn)
        try:
            _checkpointer.setup()
        except Exception as e:  # pragma: no cover - idempotent
            logger.debug(f"checkpointer.setup(): {e}")
        logger.info(f"LangGraph checkpointer ready ({settings.CHECKPOINTER_DB_PATH})")
    return _checkpointer


def build_supervisor(provider: str):
    """Construct + compile the supervisor over the three specialists for a provider."""
    from langgraph_supervisor import create_supervisor

    from .restaurant_agent import build_restaurant_agent
    from .shopping_agent import build_shopping_agent
    from .travel_agent import build_travel_agent

    model = get_chat_llm(provider)
    specialists = [
        build_restaurant_agent(model),
        build_travel_agent(model),
        build_shopping_agent(model),
    ]
    workflow = create_supervisor(
        agents=specialists,
        model=model,
        prompt=SUPERVISOR_PROMPT,
        output_mode="last_message",
        supervisor_name="supervisor",
    )
    graph = workflow.compile(checkpointer=get_checkpointer())
    logger.info(f"Supervisor compiled [{provider}] (restaurant_agent, travel_agent, shopping_agent)")
    return graph


def get_supervisor(provider: Optional[str] = None):
    """Lazily build + cache the compiled supervisor for a provider (default: first available)."""
    provider = provider or default_provider()
    if provider not in _supervisors:
        _supervisors[provider] = build_supervisor(provider)
    return _supervisors[provider]


def reset_supervisor() -> None:
    _supervisors.clear()


def _content_to_text(content: Any) -> str:
    """Flatten a message's content to plain text. Gemini 2.5 'thinking' returns a
    list of content blocks ([{type:'text', text:..., extras:{signature:...}}]); pull
    out the text parts and drop the thought-signature noise."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and block.get("text"):
                parts.append(block["text"])
        return "\n".join(p for p in parts if p).strip()
    return str(content) if content else ""


async def run_chat(message: str, thread_id: str, user_id: Optional[str] = None) -> str:
    """Invoke the supervisor for one turn; return the final assistant message.

    Tries Gemini first, then falls back to a local Ollama model if the Gemini call
    fails. The sync graph runs in a threadpool; the checkpointer persists per thread_id.
    """
    from fastapi.concurrency import run_in_threadpool

    providers = providers_in_order()
    if not providers:
        raise LLMNotConfiguredError("No LLM provider available")

    # recursion_limit bounds the ReAct loop so a failing tool can't spin forever.
    config = {"configurable": {"thread_id": thread_id}, "recursion_limit": 20}
    content = f"[user_id={user_id}] {message}" if user_id else message
    payload = {"messages": [{"role": "user", "content": content}]}

    last_err: Optional[Exception] = None
    for provider in providers:
        try:
            graph = get_supervisor(provider)
            state = await run_in_threadpool(graph.invoke, payload, config)
            messages = state.get("messages") if isinstance(state, dict) else None
            if not messages:
                return ""
            if provider != providers[0]:
                logger.info(f"chat answered via fallback provider: {provider}")
            return _content_to_text(getattr(messages[-1], "content", ""))
        except Exception as e:
            logger.warning(f"chat via {provider} failed: {e}")
            last_err = e
    raise last_err or LLMNotConfiguredError("No LLM provider available")
