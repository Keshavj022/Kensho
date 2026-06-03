"""Milestone 1 — app boots and health endpoints report per-subsystem status."""
from __future__ import annotations


def test_root(client):
    r = client.get("/")
    assert r.status_code == 200
    body = r.json()
    assert body["name"] == "Kensho"
    assert set(body["domains"]) == {"restaurants", "travel", "shopping"}


def test_health_overall(client):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    # DB is the durable source of truth and must always be reachable.
    assert body["subsystems"]["db"] == "ok"
    # Optional subsystems are present in the snapshot regardless of config.
    for sub in ("kg", "rag", "llm"):
        assert sub in body["subsystems"]


def test_health_subsystem_endpoints(client):
    assert client.get("/health/db").json()["status"] == "ok"
    # Without keys these degrade but never error the request.
    for sub in ("kg", "rag", "llm"):
        r = client.get(f"/health/{sub}")
        assert r.status_code == 200
        assert "status" in r.json()


def test_tables_created():
    import sqlalchemy as sa

    from backend.db.database import engine

    tables = set(sa.inspect(engine).get_table_names())
    assert {"user_auth", "user_profiles", "menu_cache", "carts", "refresh_tokens"} <= tables
