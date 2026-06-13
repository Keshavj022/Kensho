"""POST /chat — runs the supervisor and returns {message, thread_id, references}."""
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

        result = await run_chat(message, thread_id=thread_id, user_id=req.user_id)
        return ChatResponse(
            message=result["message"],
            thread_id=thread_id,
            references=result.get("references") or None,
        )
    except Exception as e:
        logger.exception("chat failed")
        return ChatResponse(
            message=f"Sorry, the assistant hit an error: {e}",
            thread_id=thread_id,
        )
