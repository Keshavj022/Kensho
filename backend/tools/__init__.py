"""
Agent-facing tools (LangChain @tool functions).

Each tool's DOCSTRING is the description the LLM routes on — keep them precise.
Tools wrap external calls in try/except, cache expensive results, and degrade
gracefully (return a clear "not configured" result instead of raising) when an
API key is missing. Import specific tool modules directly.
"""
