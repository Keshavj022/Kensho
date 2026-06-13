"""LangGraph supervisor — the /chat entry point that routes to one of three
specialists. One compiled graph per LLM provider; conversation state is checkpointed
by thread_id."""
from __future__ import annotations

import ast
import json
import re
import sqlite3
from typing import Any, Optional
from urllib.parse import quote

from langchain_core.callbacks.base import BaseCallbackHandler
from loguru import logger

from ..config import settings
from ..services.llm import LLMNotConfiguredError, default_provider, get_chat_llm, providers_in_order
from ._factory import RESPONSE_STYLE

_checkpointer = None
_supervisors: dict[str, Any] = {}

SUPERVISOR_PROMPT = (
    "You are the Kensho supervisor coordinating three specialists:\n"
    "- restaurant_agent: restaurants, menus, dishes, food ordering (cart + handoff).\n"
    "- travel_agent: flights, hotels, and trip itineraries — metasearch only, no booking.\n"
    "- shopping_agent: product search across merchants.\n"
    "Classify the user's request and delegate to exactly ONE specialist. For ambiguous "
    "or multi-domain requests, choose the best-fit specialist. Do not answer domain "
    "questions yourself — always delegate.\n"
    "When you write the FINAL reply to the user, rephrase the specialist's findings in "
    "your own warm, natural voice using the VOICE & FORMAT rules below — do NOT pass "
    "through or re-introduce Markdown."
    + RESPONSE_STYLE
)


def get_checkpointer():
    """Postgres saver when DATABASE_URL is Postgres, else SQLite (with fallback)."""
    global _checkpointer
    if _checkpointer is not None:
        return _checkpointer

    if settings.is_postgres:
        try:
            from langgraph.checkpoint.postgres import PostgresSaver
            from psycopg_pool import ConnectionPool

            pool = ConnectionPool(
                conninfo=settings.pg_conninfo,
                max_size=5,
                kwargs={"autocommit": True, "prepare_threshold": 0},
            )
            saver = PostgresSaver(pool)
            saver.setup()
            _checkpointer = saver
            logger.info("LangGraph checkpointer ready (Postgres)")
            return _checkpointer
        except Exception as e:
            logger.warning(f"Postgres checkpointer unavailable ({e}); falling back to SQLite")

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


_MD_BOLD = re.compile(r"\*\*(.+?)\*\*", re.DOTALL)
_MD_BOLD_ALT = re.compile(r"__(.+?)__", re.DOTALL)
_MD_CODE = re.compile(r"`([^`]+)`")
_MD_HEADER = re.compile(r"(?m)^\s{0,3}#{1,6}\s+")


def _strip_markdown(text: str) -> str:
    """Strip bold/inline-code/heading markup so replies stay plain text."""
    if not text:
        return text
    text = _MD_BOLD.sub(r"\1", text)
    text = _MD_BOLD_ALT.sub(r"\1", text)
    text = _MD_CODE.sub(r"\1", text)
    text = _MD_HEADER.sub("", text)
    return text.strip()


def _content_to_text(content: Any) -> str:
    """Flatten a message's content (str or a list of content blocks) to plain text."""
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


class _ToolCapture(BaseCallbackHandler):
    """Records each tool's (name, output) so we can build in-app reference links."""

    def __init__(self) -> None:
        self.calls: list[tuple[Optional[str], Any]] = []
        self._names: dict[Any, Optional[str]] = {}

    def on_tool_start(self, serialized, input_str, *, run_id=None, **kwargs):  # noqa: ANN001
        try:
            self._names[run_id] = (serialized or {}).get("name")
        except Exception:
            pass

    def on_tool_end(self, output, *, run_id=None, **kwargs):  # noqa: ANN001
        try:
            self.calls.append((self._names.get(run_id), output))
        except Exception:
            pass


def _parse_tool_output(output: Any) -> Optional[dict]:
    content = getattr(output, "content", None)
    content = content if content is not None else output
    if isinstance(content, dict):
        return content
    if isinstance(content, str):
        s = content.strip()
        for parser in (json.loads, ast.literal_eval):
            try:
                v = parser(s)
                if isinstance(v, dict):
                    return v
            except Exception:
                continue
    return None


def _rest_link(rid: Any) -> str:
    return f"/restaurants/{quote(str(rid), safe='')}"


def _extract_references(calls: list[tuple[Optional[str], Any]]) -> list[dict[str, Any]]:
    """Build clickable in-app references from the tools the agent actually called."""
    refs: list[dict[str, Any]] = []
    seen: set[str] = set()

    def add(ref: dict[str, Any], key: str) -> None:
        if key and key not in seen:
            seen.add(key)
            refs.append(ref)

    for name, output in calls:
        data = _parse_tool_output(output)
        if not isinstance(data, dict):
            continue

        if name in ("search_restaurants", "get_restaurant_details"):
            items = data.get("restaurants")
            if items is None and data.get("id"):
                items = [data]
            for r in (items or [])[:6]:
                rid = r.get("id")
                if not rid:
                    continue
                bits = []
                if r.get("rating") is not None:
                    bits.append(f"★ {r.get('rating')}")
                if r.get("price_range"):
                    bits.append(str(r.get("price_range")))
                elif r.get("address"):
                    bits.append(str(r.get("address")))
                add(
                    {
                        "type": "restaurant",
                        "title": r.get("name") or "Restaurant",
                        "subtitle": " · ".join(bits[:2]),
                        "link": _rest_link(rid),
                        "external": False,
                        "image": r.get("thumbnail"),
                    },
                    f"r:{rid}",
                )
        elif name == "search_dishes":
            for d in (data.get("dishes") or [])[:6]:
                rid = d.get("restaurant_id")
                if not rid:
                    continue
                add(
                    {
                        "type": "dish",
                        "title": d.get("name") or "Dish",
                        "subtitle": d.get("restaurant_name") or "",
                        "link": _rest_link(rid),
                        "external": False,
                        "image": None,
                    },
                    f"d:{d.get('id') or d.get('name')}:{rid}",
                )
        elif name == "search_products":
            for p in (data.get("products") or [])[:6]:
                link = p.get("link")
                if not link:
                    continue
                price = p.get("price_label") or (f"₹{int(p['price'])}" if isinstance(p.get("price"), (int, float)) else None)
                bits = [b for b in (price, p.get("source")) if b]
                add(
                    {
                        "type": "product",
                        "title": p.get("title") or "Product",
                        "subtitle": " · ".join(str(b) for b in bits[:2]),
                        "link": link,
                        "external": True,
                        "image": p.get("thumbnail"),
                    },
                    f"p:{link}",
                )
        elif name == "search_hotels":
            for h in (data.get("hotels") or [])[:4]:
                cp = h.get("cheapest_provider") or {}
                link = cp.get("link") or h.get("link")
                if not link:
                    continue
                price = cp.get("price_per_night") or h.get("price_per_night")
                sub = (f"₹{int(price)}/night" if isinstance(price, (int, float)) else "")
                if cp.get("source"):
                    sub = (sub + f" · {cp['source']}").strip(" ·")
                add(
                    {
                        "type": "hotel",
                        "title": h.get("name") or "Hotel",
                        "subtitle": sub,
                        "link": link,
                        "external": True,
                        "image": None,
                    },
                    f"h:{h.get('name')}",
                )
    return refs[:8]


async def run_chat(message: str, thread_id: str, user_id: Optional[str] = None) -> dict[str, Any]:
    """Run the supervisor for one turn, trying each provider until one answers.
    Returns {message, references}."""
    from fastapi.concurrency import run_in_threadpool

    providers = providers_in_order()
    if not providers:
        raise LLMNotConfiguredError("No LLM provider available")

    content = f"[user_id={user_id}] {message}" if user_id else message
    payload = {"messages": [{"role": "user", "content": content}]}

    last_err: Optional[Exception] = None
    for provider in providers:
        capture = _ToolCapture()
        config = {
            "configurable": {"thread_id": thread_id},
            "recursion_limit": 20,
            "callbacks": [capture],
        }
        try:
            graph = get_supervisor(provider)
            state = await run_in_threadpool(graph.invoke, payload, config)
            messages = state.get("messages") if isinstance(state, dict) else None
            references = _extract_references(capture.calls)
            if not messages:
                return {"message": "", "references": references}
            if provider != providers[0]:
                logger.info(f"chat answered via fallback provider: {provider}")
            reply = _strip_markdown(_content_to_text(getattr(messages[-1], "content", "")))
            return {"message": reply, "references": references}
        except Exception as e:
            logger.warning(f"chat via {provider} failed: {e}")
            last_err = e
    raise last_err or LLMNotConfiguredError("No LLM provider available")
