"""Milestone 5 — menu pipeline: OCR extraction + cascade + caching (Gemini mocked)."""
from __future__ import annotations

from backend.config import settings
from backend.models.menu import Menu, MenuItem, make_item_id


class _Resp:
    def __init__(self, content):
        self.content = content


class _FakeModel:
    """Returns classify vs extract JSON based on the prompt text."""

    def invoke(self, messages):
        content = messages[0].content
        text = content[0]["text"] if isinstance(content, list) else content
        if "menu_indices" in text:
            return _Resp('{"menu_indices": [0]}')
        return _Resp(
            '{"currency":"INR","items":['
            '{"name":"Paneer Tikka","price":250,"section":"Starters","dietary_flags":["veg"],"confidence":0.9},'
            '{"name":"Chicken Biryani","price":320,"section":"Biryani","dietary_flags":["non_veg"]}'
            ']}'
        )


def _patch_gemini_vision(monkeypatch):
    from backend.services import ocr_service

    monkeypatch.setattr(settings, "GEMINI_API_KEY", "k")
    monkeypatch.setattr(ocr_service, "_download_image", lambda url, timeout=15.0: ("ZmFrZQ==", "image/jpeg"))
    monkeypatch.setattr(ocr_service, "invoke_with_fallback", lambda messages, **k: _FakeModel().invoke(messages))


def test_classify_menu_images(monkeypatch):
    from backend.services import ocr_service

    _patch_gemini_vision(monkeypatch)
    kept = ocr_service.classify_menu_images(["http://u1", "http://u2"])
    assert kept == ["http://u1"]  # index 0 only


def test_extract_menu_builds_structured_menu(monkeypatch):
    from backend.services import ocr_service

    _patch_gemini_vision(monkeypatch)
    menu = ocr_service.extract_menu("PID1", "Bhojohori Manna", ["http://menu1"])
    assert isinstance(menu, Menu)
    assert menu.source == "ocr"
    assert menu.item_count() == 2
    assert {s["name"] for s in menu.sections} == {"Starters", "Biryani"}
    item = menu.all_items()[0]
    assert item.id.startswith("item_")
    assert item.currency == "INR"


def test_add_menu_items_dedupes_ids(monkeypatch):
    from backend.services import vector_index

    captured = {}

    class _Coll:
        def upsert(self, ids, documents, embeddings, metadatas):
            captured["ids"] = ids

    class _Emb:
        def embed_documents(self, docs):
            return [[0.0] for _ in docs]

    monkeypatch.setattr(vector_index, "embeddings_available", lambda: True)
    monkeypatch.setattr(vector_index, "get_embeddings", lambda: _Emb())
    monkeypatch.setattr(vector_index, "_get_collection", lambda create=True: _Coll())

    items = [
        {"id": "dup", "name": "A", "price": 1},
        {"id": "dup", "name": "A duplicate id", "price": 2},
        {"id": "x", "name": "B", "price": 3},
    ]
    n = vector_index.add_menu_items("R1", "Resto", items)
    assert captured["ids"] == ["dup", "x"]  # duplicate id dropped
    assert n == 2


def test_menu_cascade_and_cache(monkeypatch):
    from backend.db.database import session_scope
    from backend.db.models import MenuCache
    from backend.services import menu_service, ocr_service
    from backend.tools import serpapi_tools

    with session_scope() as db:
        row = db.get(MenuCache, "PID_TEST")
        if row:
            db.delete(row)

    monkeypatch.setattr(settings, "GEMINI_API_KEY", "k")
    monkeypatch.setattr(settings, "SERPAPI_API_KEY", "k")

    class _FakeTool:
        def __init__(self, fn):
            self._fn = fn

        def invoke(self, payload):
            return self._fn(payload)

    monkeypatch.setattr(serpapi_tools, "get_place_photos", _FakeTool(lambda p: {"status": "ok", "photos": ["http://u1", "http://u2"]}))
    monkeypatch.setattr(menu_service, "_resolve_order_link", lambda pid: "http://order.google/x")
    monkeypatch.setattr(menu_service, "add_menu_items", lambda *a, **k: 0)  # skip real embeddings
    monkeypatch.setattr(ocr_service, "classify_menu_images", lambda urls, **k: urls[:1])

    def _fake_extract(rid, rname, urls, use_pro=False):
        items = [MenuItem(id=make_item_id(rid, "Starters", "Paneer Tikka"), name="Paneer Tikka", price=250, section="Starters", dietary_flags=["veg"])]
        return Menu(restaurant_id=rid, restaurant_name=rname, sections=[{"name": "Starters", "items": [i.model_dump() for i in items]}], source="ocr")

    monkeypatch.setattr(ocr_service, "extract_menu", _fake_extract)

    out = menu_service.get_menu("PID_TEST", "Test Resto")
    assert out["status"] == "ok"
    assert out["source"] == "ocr"
    assert out["cached"] is False
    assert out["order_online_url"] == "http://order.google/x"
    assert out["sections"][0]["items"][0]["name"] == "Paneer Tikka"

    out2 = menu_service.get_menu("PID_TEST")
    assert out2["cached"] is True
    assert out2["sections"][0]["items"][0]["name"] == "Paneer Tikka"
