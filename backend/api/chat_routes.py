"""
Unified chat entry — runs the LangGraph supervisor.

POST /api/v1/chat  body: {message, user_id?, thread_id?}
                   -> {message, thread_id, ...}

thread_id maps to a checkpointer thread (conversation persistence). If the LLM is
not configured, returns a clear message instead of erroring (graceful degradation).
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter
from loguru import logger

from ..models.schemas import ChatRequest, ChatResponse
from ..services.llm import is_llm_available

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    thread_id = req.thread_id or f"thread_{uuid.uuid4().hex[:16]}"

    if not is_llm_available():
        return ChatResponse(
            message="The AI assistant is not configured. Set GEMINI_API_KEY to enable chat.",
            thread_id=thread_id,
        )

    # Personalize: prepend the diner profile so the model honors diet + allergies.
    message = req.message
    if req.user_id:
        try:
            from ..services.user_service import user_service

            summary = user_service.profile_summary(req.user_id)
            if summary:
                message = f"{summary}\n\nUser request: {req.message}"
        except Exception:
            pass

    try:
        from ..agents.supervisor import run_chat

        reply = await run_chat(message, thread_id=thread_id, user_id=req.user_id)
        return ChatResponse(message=reply, thread_id=thread_id)
    except Exception as e:
        logger.exception("chat failed")
        return ChatResponse(
            message=f"Sorry, the assistant hit an error: {e}",
            thread_id=thread_id,
        )
