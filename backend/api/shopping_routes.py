"""Shopping domain routes — product search (search-only)."""
from __future__ import annotations

from fastapi import APIRouter
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel

from ..tools import serpapi_tools

router = APIRouter(prefix="/shopping", tags=["shopping"])


class ProductSearchBody(BaseModel):
    query: str
    max_results: int = 20


@router.post("/search")
async def search_products(body: ProductSearchBody) -> dict:
    return await run_in_threadpool(serpapi_tools.search_products.invoke, body.model_dump())
