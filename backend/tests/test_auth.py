"""Milestone 7 — DB-backed auth + the dual-write (auth + profile + graph) fix."""
from __future__ import annotations

import uuid


def _u() -> str:
    return "u_" + uuid.uuid4().hex[:8]


def _email(name):
    return f"{name}@x.com"


def _register(client, name):
    return client.post("/api/v1/auth/register", json={"email": _email(name), "password": "secret123"})


def _login(client, name, password="secret123"):
    return client.post("/api/v1/auth/login", json={"email": _email(name), "password": password})


def test_register_creates_auth_and_profile_rows(client):
    """THE FIX: register must create BOTH the auth row and the profile row."""
    from backend.db.database import SessionLocal
    from backend.db.models import UserAuth, UserProfileRow

    name = _u()
    r = _register(client, name)
    assert r.status_code == 201
    uid = r.json()["user_id"]
    with SessionLocal() as db:
        auth = db.get(UserAuth, uid)
        profile = db.get(UserProfileRow, uid)
        assert auth is not None and profile is not None
        assert auth.user_id == profile.user_id  # shared user_id
        assert not auth.hashed_password.startswith("secret")  # hashed, not plaintext


def test_login_me_refresh_logout(client):
    name = _u()
    _register(client, name)
    login = _login(client, name).json()
    assert login["access_token"] and login["refresh_token"]

    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {login['access_token']}"})
    assert me.status_code == 200 and me.json()["email"] == _email(name)

    ref = client.post("/api/v1/auth/refresh", json={"refresh_token": login["refresh_token"]})
    assert ref.status_code == 200 and ref.json()["access_token"]

    client.post("/api/v1/auth/logout", headers={"Authorization": f"Bearer {login['access_token']}"})
    # After logout the refresh token is revoked.
    assert client.post("/api/v1/auth/refresh", json={"refresh_token": login["refresh_token"]}).status_code == 401


def test_duplicate_register_and_bad_password(client):
    name = _u()
    _register(client, name)
    dup = _register(client, name)  # same email -> duplicate
    assert dup.status_code == 400
    assert _login(client, name, "WRONG").status_code == 401


def test_check_email_availability(client):
    name = _u()
    assert client.get("/api/v1/auth/check-email", params={"email": _email(name)}).json()["available"] is True
    _register(client, name)
    assert client.get("/api/v1/auth/check-email", params={"email": _email(name)}).json()["available"] is False


def test_me_requires_auth(client):
    assert client.get("/api/v1/auth/me").status_code in (401, 403)


def test_profile_onboarding(client):
    name = _u()
    _register(client, name)
    login = _login(client, name).json()
    headers = {"Authorization": f"Bearer {login['access_token']}"}

    payload = {
        "name": "Aanya",
        "dob": "1996-04-10",
        "gender": "female",
        "dietary_type": "vegetarian",
        "spice_tolerance": "medium",
        "allergies": ["peanuts", "shellfish"],
        "goals": ["high-protein", "heart-healthy"],
        "likes": ["paneer", "dosa"],
        "dislikes": ["okra"],
        "cuisines": ["south indian", "bengali"],
    }
    put = client.put("/api/v1/auth/profile", json=payload, headers=headers).json()
    assert put["onboarded"] is True
    assert put["dietary_type"] == "vegetarian"
    assert set(put["allergies"]) == {"peanuts", "shellfish"}
    assert put["age"] is not None  # derived from DOB

    got = client.get("/api/v1/auth/profile", headers=headers).json()
    assert got["likes"] == ["paneer", "dosa"]
    assert got["dislikes"] == ["okra"]
    assert got["cuisines"] == ["south indian", "bengali"]

    from backend.services.user_service import user_service

    summary = user_service.profile_summary(put["user_id"]).lower()
    assert "peanuts" in summary and "vegetarian" in summary and "hard constraints" in summary


def test_profile_requires_auth(client):
    assert client.get("/api/v1/auth/profile").status_code in (401, 403)
