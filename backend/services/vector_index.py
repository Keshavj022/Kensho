"""The `menu_items` dish index (ChromaDB). Written by the menu pipeline, read by
dish search. Delegates to pgvector when DATABASE_URL is Postgres. Degrades to empty
results when embeddings/Chroma are unavailable."""
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


def _is_dimension_mismatch(err: Exception) -> bool:
    """True when a Chroma op failed because the collection's embedding dimension
    differs from the current provider's (e.g. after switching Gemini -> Azure)."""
    return "dimension" in str(err).lower()


def _reset_menu_collection():
    """Drop + recreate the menu_items collection (clears stale-dimension vectors)."""
    client = get_chroma_client()
    if client is None:
        return None
    try:
        client.delete_collection(MENU_COLLECTION)
        logger.warning("menu_items: reset collection (embedding dimension changed)")
    except Exception as e:
        logger.debug(f"menu_items reset: {e}")
    try:
        return client.get_or_create_collection(MENU_COLLECTION)
    except Exception as e:
        logger.warning(f"menu_items recreate failed: {e}")
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
    if settings.is_postgres:
        from . import vector_pgvector

        return vector_pgvector.add_items(restaurant_id, restaurant_name, items)
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
        try:
            collection.upsert(ids=ids, documents=docs, embeddings=vectors, metadatas=metadatas)
        except Exception as e:
            if not _is_dimension_mismatch(e):
                raise
            collection = _reset_menu_collection()
            if collection is None:
                return 0
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
    if settings.is_postgres:
        from . import vector_pgvector

        return vector_pgvector.search(query, max_results, restaurant_id)
    if not embeddings_available():
        return []
    collection = _get_collection(create=False)
    if collection is None:
        return []
    try:
        emb = get_embeddings()
        q_vec = emb.embed_query(query)
        where = {"restaurant_id": restaurant_id} if restaurant_id else None
        try:
            res = collection.query(
                query_embeddings=[q_vec],
                n_results=max(1, int(max_results)),
                where=where,
            )
        except Exception as e:
            if _is_dimension_mismatch(e):
                _reset_menu_collection()
                return []
            raise
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
    if settings.is_postgres:
        from . import vector_pgvector

        return vector_pgvector.count()
    collection = _get_collection(create=False)
    if collection is None:
        return 0
    try:
        return collection.count()
    except Exception:
        return 0


def _embedding_preflight() -> Optional[str]:
    """Confirm the active embedding provider actually answers. Returns an error
    hint string on failure, or None when embeddings work. We do this BEFORE touching
    the collection so a misconfigured provider can't wipe a working index."""
    from ..config import settings

    try:
        get_embeddings().embed_query("menu")
        return None
    except Exception as e:
        msg = str(e)
        if ("404" in msg or "not found" in msg.lower()) and settings.azure_embeddings_configured:
            return (
                f"Azure embedding deployment '{settings.AZURE_OPENAI_EMBEDDING_DEPLOYMENT}' was not found "
                f"at AZURE_OPENAI_ENDPOINT. Set AZURE_OPENAI_EMBEDDING_DEPLOYMENT to the name of an actual "
                f"embeddings deployment in your Azure resource, or set it to \"\" to use Gemini embeddings. "
                f"(Original error: {msg})"
            )
        return f"Embedding provider call failed: {msg}"


def reindex_from_cache() -> dict[str, Any]:
    """Re-embed every cached menu into menu_items with the CURRENT embedding provider.

    Run after switching embedding providers (e.g. Gemini -> Azure) to rebuild dish
    search in the new vector space. NON-DESTRUCTIVE on failure: a pre-flight check
    confirms embeddings work before any writes, and add_menu_items only resets the
    collection on a genuine dimension mismatch (when new vectors are in hand), so a
    bad provider config never wipes a working index.
    """
    if not embeddings_available():
        return {"status": "no_embeddings", "menus": 0, "items": 0}

    err = _embedding_preflight()
    if err:
        logger.warning(f"reindex aborted — {err}")
        return {"status": "embedding_error", "message": err, "menus": 0, "items": 0}

    if settings.is_postgres:
        from . import vector_pgvector

        vector_pgvector.reset()

    from ..db.database import SessionLocal
    from ..db.models import MenuCache

    menus, total = 0, 0
    try:
        with SessionLocal() as db:
            rows = db.query(MenuCache).all()
            for row in rows:
                mj = row.menu_json or {}
                items: list[dict[str, Any]] = []
                for sec in mj.get("sections", []):
                    items.extend(sec.get("items", []))
                n = add_menu_items(row.place_id, row.restaurant_name or mj.get("restaurant_name", ""), items)
                if n:
                    menus += 1
                    total += n
    except Exception as e:
        logger.warning(f"reindex_from_cache failed: {e}")
        return {"status": "error", "message": str(e), "menus": menus, "items": total}
    logger.info(f"Reindexed {total} items from {menus} cached menus into menu_items")
    return {"status": "ok", "menus": menus, "items": total}
