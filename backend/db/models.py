"""
ORM models — durable relational state.

- user_auth        : migrated from the legacy JSON auth store
- refresh_tokens   : hashed refresh tokens (server-side allowlist for revocation)
- user_profiles    : profile + dietary + preferences (1:1 with user_auth, shared user_id)
- menu_cache       : structured menus keyed by place_id (mirrors the Pydantic Menu)
- carts            : voice/ordering cart keyed by user_id OR session_id

Registration must write user_auth + user_profiles here AND a Neo4j node, all
sharing the same user_id (fixes the legacy 3-store disconnect).
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class UserAuth(Base):
    __tablename__ = "user_auth"

    user_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), default="user", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)

    profile: Mapped["UserProfileRow"] = relationship(
        back_populates="auth", uselist=False, cascade="all, delete-orphan"
    )
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        back_populates="auth", cascade="all, delete-orphan"
    )


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("user_auth.user_id", ondelete="CASCADE"), index=True
    )
    # Store a hash of the refresh token, never the token itself.
    token_hash: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)

    auth: Mapped["UserAuth"] = relationship(back_populates="refresh_tokens")


class UserProfileRow(Base):
    __tablename__ = "user_profiles"

    user_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("user_auth.user_id", ondelete="CASCADE"), primary_key=True
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    location: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    dietary_type: Mapped[str] = mapped_column(String(40), default="non-vegetarian", nullable=False)
    # Flexible JSON blobs mirror the Pydantic User model.
    dietary_restrictions: Mapped[list] = mapped_column(JSON, default=list)
    dietary_goals: Mapped[list] = mapped_column(JSON, default=list)
    food_preferences: Mapped[dict] = mapped_column(JSON, default=dict)
    cuisine_preferences: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)

    auth: Mapped["UserAuth"] = relationship(back_populates="profile")


class MenuCache(Base):
    __tablename__ = "menu_cache"

    place_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    restaurant_name: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    menu_json: Mapped[dict] = mapped_column(JSON, nullable=False)  # serialized Menu
    source: Mapped[str] = mapped_column(String(20), default="ocr", nullable=False)
    order_online_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    extracted_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)


class Cart(Base):
    __tablename__ = "carts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # owner_key holds a user_id (authenticated) or a session_id (anonymous).
    owner_key: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    restaurant_id: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    restaurant_name: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    items: Mapped[list] = mapped_column(JSON, default=list)  # [{item_id, name, qty, price, notes}]
    order_online_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)
