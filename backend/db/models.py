"""ORM models: auth users, refresh tokens, profiles, menu cache, carts, activity."""
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
    dob: Mapped[str | None] = mapped_column(String(20), nullable=True)  # ISO date
    gender: Mapped[str | None] = mapped_column(String(24), nullable=True)
    location: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    lng: Mapped[float | None] = mapped_column(Float, nullable=True)
    dietary_type: Mapped[str] = mapped_column(String(40), default="non-vegetarian", nullable=False)
    spice_tolerance: Mapped[str | None] = mapped_column(String(20), nullable=True)
    onboarded: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    dietary_restrictions: Mapped[list] = mapped_column(JSON, default=list)  # allergies -> [{type,value}]
    dietary_goals: Mapped[list] = mapped_column(JSON, default=list)
    food_preferences: Mapped[dict] = mapped_column(JSON, default=dict)  # likes/dislikes -> {name:{preference,weight}}
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
    owner_key: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    restaurant_id: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    restaurant_name: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    items: Mapped[list] = mapped_column(JSON, default=list)  # [{item_id, name, qty, price, notes}]
    order_online_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)


class UserActivity(Base):
    """A single user signal — feeds the dashboard + recommendation engine.

    kind ∈ {search, view, dish_view, order}. The payload JSON keeps extra context
    (e.g. the restaurant rating, search filters, cart total) without schema churn.
    """

    __tablename__ = "user_activity"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    kind: Mapped[str] = mapped_column(String(24), index=True, nullable=False)
    query: Mapped[str | None] = mapped_column(String(255), nullable=True)
    restaurant_id: Mapped[str | None] = mapped_column(String(255), index=True, nullable=True)
    restaurant_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    cuisine: Mapped[str | None] = mapped_column(String(80), nullable=True)
    domain: Mapped[str] = mapped_column(String(24), default="restaurant", nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, index=True, nullable=False)
