"""Voice routes — STT, TTS, voice ordering (audio → cart), and voice listing."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, File, Form, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel

from ..services import order_service
from ..services.voice_service import voice_service

router = APIRouter(prefix="/voice", tags=["voice"])


class TTSBody(BaseModel):
    text: str
    voice_id: Optional[str] = None


@router.post("/stt")
async def speech_to_text(file: UploadFile = File(...), language: Optional[str] = Form(None)) -> dict:
    audio = await file.read()
    return await run_in_threadpool(voice_service.transcribe, audio, language)


@router.post("/tts")
async def text_to_speech(body: TTSBody):
    res = await run_in_threadpool(voice_service.synthesize, body.text, body.voice_id)
    if res["status"] != "ok":
        return JSONResponse(res, status_code=200)
    return Response(content=res["audio"], media_type=res.get("mime", "audio/mpeg"))


@router.get("/voices")
async def list_voices() -> dict:
    return await run_in_threadpool(voice_service.list_voices)


@router.post("/order")
async def voice_order(
    place_id: str = Form(...),
    session_id: str = Form("anon"),
    text: Optional[str] = Form(None),
    language: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
) -> dict:
    audio = await file.read() if file is not None else None
    return await run_in_threadpool(
        order_service.process_voice_order, audio, text, place_id, session_id, language
    )


@router.get("/cart")
async def get_cart(place_id: str, session_id: str = "anon") -> dict:
    return await run_in_threadpool(order_service.get_cart, session_id, place_id)
