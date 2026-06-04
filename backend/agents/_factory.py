"""Shared agent builder — prefers LangChain 1.x create_agent, falls back to
langgraph.prebuilt.create_react_agent (which uses `prompt=` not `system_prompt=`)."""
from __future__ import annotations

from loguru import logger


def make_agent(model, tools, system_prompt: str, name: str):
    try:
        from langchain.agents import create_agent

        return create_agent(model, tools=tools, system_prompt=system_prompt, name=name)
    except Exception as e:  # pragma: no cover - version fallback
        logger.warning(f"create_agent unavailable ({e}); using create_react_agent")
        from langgraph.prebuilt import create_react_agent

        return create_react_agent(model, tools=tools, prompt=system_prompt, name=name)
