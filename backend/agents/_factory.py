"""Builds a specialist agent, falling back to create_react_agent on older LangChain."""
from __future__ import annotations

from loguru import logger

RESPONSE_STYLE = (
    "\n\nVOICE & FORMAT:\n"
    "- Talk like a warm, knowledgeable local friend — natural first-person prose, concise, "
    "with a little personality. Open with a short human sentence, not a heading.\n"
    "- Do NOT use Markdown: no **bold**, no #headings, no '1.' numbered lists, no tables. "
    "If you mention a few options, give each its own short line (a plain dash is fine) with "
    "the name, rating, price, and ONE reason it fits — nothing more.\n"
    "- Quietly reflect what you know about the diner's taste; never restate their profile, "
    "never address them by name, and never say things like 'tailored to your preferences'.\n"
    "- When the user names a city or area, search and answer for exactly that place — never "
    "substitute their saved location or restaurants they've opened before.\n"
    "- End with one brief, natural follow-up offer (e.g. peek at a menu), not a sales pitch."
)


def make_agent(model, tools, system_prompt: str, name: str):
    try:
        from langchain.agents import create_agent

        return create_agent(model, tools=tools, system_prompt=system_prompt, name=name)
    except Exception as e:  # pragma: no cover
        logger.warning(f"create_agent unavailable ({e}); using create_react_agent")
        from langgraph.prebuilt import create_react_agent

        return create_react_agent(model, tools=tools, prompt=system_prompt, name=name)
