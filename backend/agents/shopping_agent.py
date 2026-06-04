"""Shopping specialist — product search across merchants (search-only)."""
from __future__ import annotations

from ..services.llm import get_llm
from ..tools.registry import shopping_tools
from ._factory import make_agent

NAME = "shopping_agent"

SYSTEM_PROMPT = (
    "You are Kensho's shopping specialist.\n"
    "- Use search_products to find products with prices, merchants (source), links, "
    "and ratings; sort by what the user cares about (price, rating).\n"
    "- Use web_search for buying guides, comparisons, and reviews.\n"
    "Search only — surface options with prices and links; never check out or take "
    "payment. Be concise and helpful."
)


def build_shopping_agent(model=None):
    return make_agent(model or get_llm(), tools=shopping_tools(), system_prompt=SYSTEM_PROMPT, name=NAME)
