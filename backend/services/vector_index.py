"""
Gemini-embedded `menu_items` vector index (ChromaDB).

Single source of truth for the cross-restaurant dish-search collection. Written by
the menu pipeline (menu_service.embed) and read by rag_tools.search_dishes. All
embeddings use the one Gemini embedding space (settings.GEMINI_EMBEDDING_MODEL).

Fully graceful: if chromadb isn't installed or GEMINI_API_KEY is unset, reads
return empty and writes are skipped — never raises into a tool/agent.
"""
from __future__ import annotations

from typing import Any, Optional

from loguru import logger

from ..config import settings
from .llm import embeddings_available, get_embeddings

MENU_COLLECTION = "menu_items"

_client = None


def get_chroma_client():
    """Shared PersistentClient at settings.CHROMA_PATH, or None if unavailable.

    Reuses the RAG service's client if it already built one (chromadb refuses two
    clients on the same path with different settings), otherwise builds one with
    matching settings so the two share a single underlying instance.
    """
    global _client
    if _client is not None:
        return _client
    # Prefer an existing client to avoid the "instance already exists" conflict.
    try:
        from .rag_service import rag_service

        if getattr(rag_service, "chroma_client", None) is not None:
            _client = rag_service.chroma_client
            return _client
    except Exception:
        pass
    try:
        import chromadb
        from chromadb.config import Settings as ChromaSettings

        _client = chromadb.PersistentClient(
            path=settings.CHROMA_PATH,
            settings=ChromaSettings(anonymized_telemetry=False, allow_reset=True),
        )
    except Exception as e:
        logger.warning(f"ChromaDB unavailable: {e}")
        _client = None
    return _client


def _get_collection(create: bool = True):
    client = get_chroma_client()
    if client is None:
        return None
    try:
        if create:
            return client.get_or_create_collection(MENU_COLLECTION)
        return client.get_collection(MENU_COLLECTION)
    except Exception as e:
        logger.debug(f"menu_items collection: {e}")
        return None


def _item_text(item: dict[str, Any]) -> str:
    parts = [item.get("name") or ""]
    if item.get("description"):
        parts.append(item["description"])
    if item.get("section"):
        parts.append(f"({item['section']})")
    if item.get("dietary_flags"):
        parts.append(" ".join(item["dietary_flags"]))
    return " ".join(p for p in parts if p).strip()


def add_menu_items(restaurant_id: str, restaurant_name: str, items: list[dict[str, Any]]) -> int:
    """Embed + upsert menu items. Returns the count indexed (0 if degraded)."""
    if not items or not embeddings_available():
        return 0
    collection = _get_collection(create=True)
    if collection is None:
        return 0
    try:
        emb = get_embeddings()
        ids, docs, metadatas = [], [], []
        seen: set[str] = set()
        for it in items:
            text = _item_text(it)
            item_id = it.get("id")
            # Skip blanks and de-duplicate ids within the batch (chromadb upsert
            # rejects duplicate ids; collisions happen when two items share name+section).
            if not item_id or not text or item_id in seen:
                continue
            seen.add(item_id)
            ids.append(item_id)
            docs.append(text)
            metadatas.append(
                {
                    "restaurant_id": restaurant_id,
                    "restaurant_name": restaurant_name,
                    "name": it.get("name") or "",
                    "price": it.get("price") if it.get("price") is not None else -1,
                    "currency": it.get("currency") or "INR",
                    "section": it.get("section") or "",
                    "dietary_flags": ",".join(it.get("dietary_flags") or []),
                }
            )
        if not ids:
            return 0
        vectors = emb.embed_documents(docs)
        collection.upsert(ids=ids, documents=docs, embeddings=vectors, metadatas=metadatas)
        logger.info(f"Indexed {len(ids)} menu items for {restaurant_name} ({restaurant_id})")
        return len(ids)
    except Exception as e:
        logger.warning(f"add_menu_items failed for {restaurant_id}: {e}")
        return 0


def search_menu_items(
    query: str, max_results: int = 10, restaurant_id: Optional[str] = None
) -> list[dict[str, Any]]:
    """Semantic dish search across all indexed restaurants (or one restaurant)."""
    if not embeddings_available():
        return []
    collection = _get_collection(create=False)
    if collection is None:
        return []
    try:
        emb = get_embeddings()
        q_vec = emb.embed_query(query)
        where = {"restaurant_id": restaurant_id} if restaurant_id else None
        res = collection.query(
            query_embeddings=[q_vec],
            n_results=max(1, int(max_results)),
            where=where,
        )
        out: list[dict[str, Any]] = []
        ids = (res.get("ids") or [[]])[0]
        metas = (res.get("metadatas") or [[]])[0]
        dists = (res.get("distances") or [[]])[0]
        for i, _id in enumerate(ids):
            m = metas[i] if i < len(metas) else {}
            out.append(
                {
                    "id": _id,
                    "name": m.get("name"),
                    "restaurant_id": m.get("restaurant_id"),
                    "restaurant_name": m.get("restaurant_name"),
                    "price": None if m.get("price") in (None, -1) else m.get("price"),
                    "currency": m.get("currency"),
                    "section": m.get("section"),
                    "dietary_flags": (m.get("dietary_flags") or "").split(",") if m.get("dietary_flags") else [],
                    "score": round(1.0 - dists[i], 4) if i < len(dists) and dists[i] is not None else None,
                }
            )
        return out
    except Exception as e:
        logger.warning(f"search_menu_items failed: {e}")
        return []


def collection_count() -> int:
    collection = _get_collection(create=False)
    if collection is None:
        return 0
    try:
        return collection.count()
    except Exception:
        return 0
