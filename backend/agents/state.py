"""Shared graph state — the extra context (user_id, thread_id) threaded alongside
the message list."""
from __future__ import annotations

from typing import Annotated, Optional

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


class AgentState(TypedDict, total=False):
    messages: Annotated[list[AnyMessage], add_messages]
    user_id: Optional[str]
    thread_id: Optional[str]
