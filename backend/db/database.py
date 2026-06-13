"""SQLAlchemy engine / session factory. DATABASE_URL selects SQLite (dev) or
Postgres (prod)."""
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
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    return create_engine(url, connect_args=connect_args, pool_pre_ping=True, future=True)


engine = _make_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def init_db() -> None:
    """Create all tables. Idempotent; safe to call on every startup."""
    from . import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _auto_migrate_sqlite()
    logger.info(f"Relational DB ready ({settings.DATABASE_URL})")


def _auto_migrate_sqlite() -> None:
    """Dev convenience: add any newly-declared columns to existing SQLite tables
    (create_all never ALTERs). Only runs for SQLite; new columns must be nullable."""
    if not settings.DATABASE_URL.startswith("sqlite"):
        return
    from sqlalchemy import text

    try:
        with engine.begin() as conn:
            for table in Base.metadata.sorted_tables:
                rows = conn.execute(text(f"PRAGMA table_info('{table.name}')")).fetchall()
                if not rows:
                    continue  # table didn't exist; create_all already made it
                existing = {r[1] for r in rows}
                for col in table.columns:
                    if col.name not in existing:
                        coltype = col.type.compile(engine.dialect)
                        conn.execute(text(f'ALTER TABLE "{table.name}" ADD COLUMN "{col.name}" {coltype}'))
                        logger.info(f"DB migrate: added {table.name}.{col.name}")
    except Exception as e:  # pragma: no cover - best effort
        logger.warning(f"auto-migrate skipped: {e}")


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
