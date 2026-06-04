"""Milestone 6 — voice STT/TTS graceful + constrained order resolution -> cart."""
from __future__ import annotations

from backend.services import order_service

ITEMS = [
    {"id": "item_aaa", "name": "Paneer Tikka", "price": 250, "section": "Starters"},
    {"id": "item_bbb", "name": "Chicken Biryani", "price": 320, "section": "Biryani"},
]


class _Resp:
    def __init__(self, content):
        self.content = content


def test_voice_routes_graceful(client):
    assert client.get("/api/v1/voice/voices").json()["status"] == "not_configured"
    assert client.post("/api/v1/voice/tts", json={"text": "hi"}).json()["status"] == "not_configured"
    assert client.post("/api/v1/voice/stt", files={"file": ("a.mp3", b"xx", "audio/mpeg")}).json()["status"] == "not_configured"
    assert client.post("/api/v1/voice/order", data={"place_id": "PID", "text": "biryani"}).json()["status"] == "no_menu"


def test_resolve_order_fuzzy_only_real_ids():
    res = order_service.resolve_order("a chicken biryani and paneer tikka please", ITEMS)
    assert sorted(r["item_id"] for r in res) == ["item_aaa", "item_bbb"]


def test_resolve_order_llm_rejects_invalid_ids(monkeypatch):
    # Includes a hallucinated id ("ghost") that must be dropped.
    json_out = '[{"item_id":"item_bbb","qty":2},{"item_id":"item_aaa","qty":1},{"item_id":"ghost","qty":1}]'
    monkeypatch.setattr(order_service, "is_llm_available", lambda: True)
    monkeypatch.setattr(order_service, "invoke_with_fallback", lambda prompt, **k: _Resp(json_out))
    res = order_service.resolve_order("two biryani one paneer", ITEMS)
    by_id = {r["item_id"]: r["qty"] for r in res}
    assert by_id == {"item_bbb": 2, "item_aaa": 1}  # ghost dropped


def test_process_voice_order_builds_cart(monkeypatch):
    owner = "test_session_voice"
    place = "PID_VOICE"

    # Clean any cart left from a previous run.
    from backend.db.database import session_scope
    from backend.db.models import Cart

    with session_scope() as db:
        for c in db.query(Cart).filter_by(owner_key=owner, restaurant_id=place).all():
            db.delete(c)

    monkeypatch.setattr(order_service, "_menu_items", lambda pid: (ITEMS, "http://order.google/x", "Test Resto"))
    monkeypatch.setattr(order_service, "is_llm_available", lambda: False)  # force fuzzy

    out = order_service.process_voice_order(None, "chicken biryani and paneer tikka", place, owner)
    assert out["status"] == "ok"
    assert out["order_online_url"] == "http://order.google/x"
    assert {m["item_id"] for m in out["matched"]} == {"item_aaa", "item_bbb"}
    assert out["cart"]["total"] == 570  # 250 + 320
    # Cart persists and is retrievable.
    cart = order_service.get_cart(owner, place)
    assert cart["status"] == "ok" and cart["total"] == 570
