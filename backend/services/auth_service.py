"""JWT auth backed by SQLAlchemy. register_user creates the auth row + profile row
and bridges to Neo4j; refresh tokens are stored hashed."""
from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timedelta
from typing import Any, Optional

from jose import JWTError, jwt
from loguru import logger
from passlib.context import CryptContext
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError

from ..config import settings
from ..db.database import SessionLocal, session_scope
from ..db.models import RefreshToken, UserAuth, UserProfileRow

pwd_context = CryptContext(schemes=["pbkdf2_sha256", "bcrypt"], deprecated="auto")


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _auth_dict(row: UserAuth) -> dict[str, Any]:
    return {
        "user_id": row.user_id,
        "username": row.username,
        "email": row.email,
        "role": row.role,
        "is_active": row.is_active,
        "hashed_password": row.hashed_password,
    }


class AuthService:
    def hash_password(self, password: str) -> str:
        return pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    def create_access_token(self, data: dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        to_encode = data.copy()
        expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES))
        to_encode.update({"exp": expire, "type": "access", "jti": uuid.uuid4().hex})
        return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    def create_refresh_token(self, data: dict[str, Any]) -> str:
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire, "type": "refresh", "jti": uuid.uuid4().hex})
        return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    def verify_token(self, token: str, token_type: str = "access") -> Optional[dict[str, Any]]:
        try:
            payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
            if payload.get("type") != token_type:
                logger.warning(f"Token type mismatch: expected {token_type}, got {payload.get('type')}")
                return None
            return payload
        except JWTError as e:
            logger.warning(f"JWT verification failed: {e}")
            return None

    def _derive_username(self, db, email: str) -> str:
        """A stable, unique handle from the email local-part (no user-facing username)."""
        import re

        base = re.sub(r"[^a-z0-9_.]", "", email.split("@")[0].lower())[:40] or "user"
        cand, i = base, 1
        while db.execute(select(UserAuth).where(UserAuth.username == cand)).scalars().first():
            cand, i = f"{base}{i}", i + 1
        return cand

    def email_exists(self, email: str) -> bool:
        with SessionLocal() as db:
            return db.execute(select(UserAuth).where(UserAuth.email == email)).scalars().first() is not None

    def register_user(self, email: str, password: str, role: str = "user", user_id: Optional[str] = None) -> dict[str, Any]:
        """Atomically create the auth row + a durable default profile row (shared
        user_id), then bridge a Neo4j node. Email is the identity. Raises ValueError on duplicate."""
        new_id = user_id or f"user_{uuid.uuid4().hex[:12]}"
        try:
            with session_scope() as db:
                if db.execute(select(UserAuth).where(UserAuth.email == email)).scalars().first():
                    raise ValueError("Email already exists")
                username = self._derive_username(db, email)
                db.add(
                    UserAuth(
                        user_id=new_id,
                        username=username,
                        email=email,
                        hashed_password=self.hash_password(password),
                        role=role,
                        is_active=True,
                    )
                )
                db.add(
                    UserProfileRow(
                        user_id=new_id,
                        name="",
                        location="",
                        dietary_type="non-vegetarian",
                        dietary_restrictions=[],
                        dietary_goals=[],
                        food_preferences={},
                        cuisine_preferences={},
                    )
                )
        except IntegrityError:
            raise ValueError("Email already exists")

        try:
            from .knowledge_graph_service import knowledge_graph_service

            knowledge_graph_service.create_user(new_id, name=username, location="", dietary_type="non-vegetarian")
        except Exception as e:
            logger.warning(f"Neo4j node not created for {new_id}: {e}")

        logger.info(f"Registered {email} ({new_id}) — auth + profile + graph")
        return {"user_id": new_id, "username": username, "email": email, "role": role}

    def authenticate_user(self, username: str, password: str) -> Optional[dict[str, Any]]:
        with SessionLocal() as db:
            row = db.execute(
                select(UserAuth).where(or_(UserAuth.username == username, UserAuth.email == username))
            ).scalars().first()
        if not row:
            logger.warning(f"User not found: {username}")
            return None
        if not row.is_active:
            logger.warning(f"Inactive account: {username}")
            return None
        if not self.verify_password(password, row.hashed_password):
            logger.warning(f"Invalid password for: {username}")
            return None
        return {"user_id": row.user_id, "username": row.username, "email": row.email, "role": row.role}

    def create_tokens(self, user_data: dict[str, Any]) -> dict[str, str]:
        token_data = {
            "sub": user_data["user_id"],
            "username": user_data["username"],
            "email": user_data["email"],
            "role": user_data.get("role", "user"),
        }
        access_token = self.create_access_token(token_data)
        refresh_token = self.create_refresh_token(token_data)
        with session_scope() as db:
            db.add(
                RefreshToken(
                    user_id=user_data["user_id"],
                    token_hash=_hash_token(refresh_token),
                    expires_at=datetime.utcnow() + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS),
                )
            )
        return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

    def refresh_access_token(self, refresh_token: str) -> Optional[dict[str, str]]:
        payload = self.verify_token(refresh_token, token_type="refresh")
        if not payload:
            return None
        user_id = payload.get("sub")
        if not user_id:
            return None
        token_hash = _hash_token(refresh_token)
        with SessionLocal() as db:
            row = db.execute(
                select(RefreshToken).where(
                    RefreshToken.user_id == user_id, RefreshToken.token_hash == token_hash
                )
            ).scalars().first()
            if not row or row.expires_at < datetime.utcnow():
                logger.warning(f"Refresh token invalid/expired for {user_id}")
                return None
        access_token = self.create_access_token(
            {
                "sub": user_id,
                "username": payload.get("username"),
                "email": payload.get("email"),
                "role": payload.get("role", "user"),
            }
        )
        return {"access_token": access_token, "token_type": "bearer"}

    def revoke_refresh_token(self, user_id: str, refresh_token: str) -> bool:
        token_hash = _hash_token(refresh_token)
        with session_scope() as db:
            deleted = (
                db.query(RefreshToken)
                .filter_by(user_id=user_id, token_hash=token_hash)
                .delete(synchronize_session=False)
            )
        return bool(deleted)

    def revoke_all_tokens(self, user_id: str) -> bool:
        with session_scope() as db:
            if not db.get(UserAuth, user_id):
                return False
            db.query(RefreshToken).filter_by(user_id=user_id).delete(synchronize_session=False)
        return True

    def get_user_auth(self, user_id: str) -> Optional[dict[str, Any]]:
        with SessionLocal() as db:
            row = db.get(UserAuth, user_id)
            return _auth_dict(row) if row else None

    def change_password(self, user_id: str, current_password: str, new_password: str) -> bool:
        with session_scope() as db:
            row = db.get(UserAuth, user_id)
            if not row or not self.verify_password(current_password, row.hashed_password):
                return False
            row.hashed_password = self.hash_password(new_password)
            db.query(RefreshToken).filter_by(user_id=user_id).delete(synchronize_session=False)
        return True

    def list_users(self) -> list[dict[str, Any]]:
        with SessionLocal() as db:
            rows = db.execute(select(UserAuth)).scalars().all()
            return [
                {"user_id": r.user_id, "username": r.username, "email": r.email, "role": r.role, "is_active": r.is_active}
                for r in rows
            ]

    def update_user_role(self, user_id: str, role: str) -> bool:
        with session_scope() as db:
            row = db.get(UserAuth, user_id)
            if not row:
                return False
            row.role = role
        return True

    def deactivate_user(self, user_id: str) -> bool:
        with session_scope() as db:
            row = db.get(UserAuth, user_id)
            if not row:
                return False
            row.is_active = False
            db.query(RefreshToken).filter_by(user_id=user_id).delete(synchronize_session=False)
        return True

    def activate_user(self, user_id: str) -> bool:
        with session_scope() as db:
            row = db.get(UserAuth, user_id)
            if not row:
                return False
            row.is_active = True
        return True

    def delete_user(self, user_id: str) -> bool:
        with session_scope() as db:
            row = db.get(UserAuth, user_id)
            if not row:
                return False
            db.delete(row)  # cascades to profile + refresh tokens
        return True


auth_service = AuthService()
