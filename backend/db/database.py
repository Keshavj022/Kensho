"""
SQLAlchemy engine / session factory.

DATABASE_URL drives the backend: sqlite:///./kensho.db for dev, a postgres://
URL for prod. The relational DB is the durable source of truth for auth users,
profiles, menu cache, and carts. Neo4j (graph) and Chroma (vectors) stay separate.
"""
from __future__ import annotations

from contextlib import contextmanager
from typing import Generator

from loguru import logger
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from ..config import settings


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


def _make_engine():
    url = settings.DATABASE_URL
    # SQLite needs check_same_thread=False to be usable across FastAPI's threadpool.
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    return create_engine(url, connect_args=connect_args, pool_pre_ping=True, future=True)


engine = _make_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def init_db() -> None:
    """Create all tables. Idempotent; safe to call on every startup."""
    # Import models so they register on Base.metadata before create_all.
    from . import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    logger.info(f"Relational DB ready ({settings.DATABASE_URL})")


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency yielding a session that is always closed."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """Context-managed session with commit/rollback, for use outside requests."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
