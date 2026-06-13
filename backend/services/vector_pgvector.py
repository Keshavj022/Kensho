"""pgvector-backed dish index — the stateless alternative to ChromaDB, used when
DATABASE_URL is Postgres. Cosine search over a `menu_item_vectors` table. Mirrors
the vector_index surface and degrades to empty results on any failure."""
from __future__ import annotations

from typing import Any, Optional

from loguru import logger
from sqlalchemy import text

from ..config import settings
from ..db.database import engine
from .llm import embeddings_available, get_embeddings

_schema_ready = False


def available() -> bool:
    return settings.is_postgres


def _vec_literal(vec: list[float]) -> str:
    return "[" + ",".join(f"{x:.7f}" for x in vec) + "]"


def ensure_schema() -> bool:
    """Create the vector extension + table (+ HNSW index) once. Idempotent."""
    global _schema_ready
    if _schema_ready:
        return True
    if not available():
        return False
    dim = int(settings.EMBEDDING_DIM)
    try:
        with engine.begin() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            conn.execute(
                text(
                    f"""
                    CREATE TABLE IF NOT EXISTS menu_item_vectors (
                        id text PRIMARY KEY,
                        restaurant_id text,
                        restaurant_name text,
                        name text,
                        price double precision,
                        currency text,
                        section text,
                        dietary_flags text,
                        document text,
                        embedding vector({dim})
                    )
                    """
                )
            )
            conn.execute(text("CREATE INDEX IF NOT EXISTS menu_vec_rid ON menu_item_vectors (restaurant_id)"))
            if dim <= 2000:
                conn.execute(
                    text(
                        "CREATE INDEX IF NOT EXISTS menu_vec_hnsw ON menu_item_vectors "
                        "USING hnsw (embedding vector_cosine_ops)"
                    )
                )
        _schema_ready = True
        logger.info(f"pgvector menu_item_vectors ready (dim={dim})")
        return True
    except Exception as e:
        logger.warning(f"pgvector ensure_schema failed: {e}")
        return False


def _item_text(item: dict[str, Any]) -> str:
    parts = [item.get("name") or ""]
    if item.get("description"):
        parts.append(item["description"])
    if item.get("section"):
        parts.append(f"({item['section']})")
    if item.get("dietary_flags"):
        parts.append(" ".join(item["dietary_flags"]))
    return " ".join(p for p in parts if p).strip()


def add_items(restaurant_id: str, restaurant_name: str, items: list[dict[str, Any]]) -> int:
    if not items or not embeddings_available() or not ensure_schema():
        return 0
    try:
        emb = get_embeddings()
        rows, docs, seen = [], [], set()
        for it in items:
            item_id = it.get("id")
            doc = _item_text(it)
            if not item_id or not doc or item_id in seen:
                continue
            seen.add(item_id)
            docs.append(doc)
            rows.append(it)
        if not rows:
            return 0
        vectors = emb.embed_documents(docs)
        params = []
        for it, doc, vec in zip(rows, docs, vectors):
            params.append(
                {
                    "id": it["id"],
                    "rid": restaurant_id,
                    "rname": restaurant_name,
                    "name": it.get("name") or "",
                    "price": it.get("price"),
                    "currency": it.get("currency") or "INR",
                    "section": it.get("section") or "",
                    "flags": ",".join(it.get("dietary_flags") or []),
                    "document": doc,
                    "embedding": _vec_literal(vec),
                }
            )
        sql = text(
            """
            INSERT INTO menu_item_vectors
                (id, restaurant_id, restaurant_name, name, price, currency, section, dietary_flags, document, embedding)
            VALUES
                (:id, :rid, :rname, :name, :price, :currency, :section, :flags, :document, (:embedding)::vector)
            ON CONFLICT (id) DO UPDATE SET
                restaurant_id = EXCLUDED.restaurant_id,
                restaurant_name = EXCLUDED.restaurant_name,
                name = EXCLUDED.name,
                price = EXCLUDED.price,
                currency = EXCLUDED.currency,
                section = EXCLUDED.section,
                dietary_flags = EXCLUDED.dietary_flags,
                document = EXCLUDED.document,
                embedding = EXCLUDED.embedding
            """
        )
        with engine.begin() as conn:
            conn.execute(sql, params)
        logger.info(f"pgvector indexed {len(params)} items for {restaurant_name} ({restaurant_id})")
        return len(params)
    except Exception as e:
        logger.warning(f"pgvector add_items failed for {restaurant_id}: {e}")
        return 0


def search(query: str, max_results: int = 10, restaurant_id: Optional[str] = None) -> list[dict[str, Any]]:
    if not embeddings_available() or not ensure_schema():
        return []
    try:
        emb = get_embeddings()
        qvec = _vec_literal(emb.embed_query(query))
        where = "WHERE restaurant_id = :rid" if restaurant_id else ""
        sql = text(
            f"""
            SELECT id, name, restaurant_id, restaurant_name, price, currency, section, dietary_flags,
                   1 - (embedding <=> (:q)::vector) AS score
            FROM menu_item_vectors
            {where}
            ORDER BY embedding <=> (:q)::vector
            LIMIT :n
            """
        )
        params: dict[str, Any] = {"q": qvec, "n": max(1, int(max_results))}
        if restaurant_id:
            params["rid"] = restaurant_id
        with engine.connect() as conn:
            result = conn.execute(sql, params).mappings().all()
        out = []
        for r in result:
            flags = (r.get("dietary_flags") or "")
            out.append(
                {
                    "id": r["id"],
                    "name": r["name"],
                    "restaurant_id": r["restaurant_id"],
                    "restaurant_name": r["restaurant_name"],
                    "price": r["price"],
                    "currency": r["currency"],
                    "section": r["section"],
                    "dietary_flags": flags.split(",") if flags else [],
                    "score": round(float(r["score"]), 4) if r["score"] is not None else None,
                }
            )
        return out
    except Exception as e:
        logger.warning(f"pgvector search failed: {e}")
        return []


def count() -> int:
    if not ensure_schema():
        return 0
    try:
        with engine.connect() as conn:
            return int(conn.execute(text("SELECT count(*) FROM menu_item_vectors")).scalar() or 0)
    except Exception:
        return 0


def reset() -> None:
    if not available():
        return
    try:
        with engine.begin() as conn:
            conn.execute(text("TRUNCATE menu_item_vectors"))
    except Exception as e:
        logger.debug(f"pgvector reset: {e}")
