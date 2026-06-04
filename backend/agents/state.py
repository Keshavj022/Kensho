"""
Shared graph state.

`create_supervisor` / `create_agent` manage their own message state, so this
TypedDict documents the extra context we thread through (user_id, thread_id) and
is available if we later hand-roll a StateGraph router.
"""
from __future__ import annotations

from typing import Annotated, Optional

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


class AgentState(TypedDict, total=False):
    messages: Annotated[list[AnyMessage], add_messages]
    user_id: Optional[str]
    thread_id: Optional[str]
