#!/usr/bin/env python
"""
Kensho smoke test — exercises every agent path + the menu pipeline against real
restaurants and prints menu-extraction coverage (OCR vs web fallback).

Run from the repo root (after filling in .env):

    .venv/bin/python scripts/smoke_test.py

Degrades gracefully: with missing keys it reports "not configured" per section and
still completes. Requires GEMINI + SERPAPI + GOOGLE_MAPS keys for real menu coverage.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.config import settings  # noqa: E402

# Mix of chains + independents, including a couple in Kolkata.
RESTAURANTS = [
    {"name": "Bhojohori Manna", "location": "Kolkata"},
    {"name": "Peter Cat", "location": "Park Street, Kolkata"},
    {"name": "Arsalan Restaurant", "location": "Kolkata"},
    {"name": "Karim's", "location": "Jama Masjid, Delhi"},
    {"name": "Mavalli Tiffin Room MTR", "location": "Bangalore"},
    {"name": "Paragon Restaurant", "location": "Kozhikode"},
    {"name": "Britannia & Co", "location": "Mumbai"},
    {"name": "Domino's Pizza", "location": "Connaught Place, Delhi"},
    {"name": "Starbucks", "location": "Bandra, Mumbai"},
    {"name": "Truffles", "location": "Koramangala, Bangalore"},
]


def hr(title: str = "") -> None:
    print("\n" + "=" * 70)
    if title:
        print(title)
        print("=" * 70)


def config_status() -> None:
    hr("CONFIGURATION")
    flags = {
        "Gemini (LLM + OCR)": settings.gemini_configured,
        "Ollama fallback (open-source LLM)": settings.OLLAMA_ENABLED,
        "SerpApi (maps/flights/hotels/shopping/photos)": settings.serpapi_configured,
        "Tavily (web search)": settings.tavily_configured,
        "ElevenLabs (voice)": settings.elevenlabs_configured,
        "Neo4j (graph)": settings.neo4j_configured,
    }
    for k, v in flags.items():
        print(f"  [{'x' if v else ' '}] {k}")
    print(f"  Gemini model: {settings.GEMINI_MODEL} | Pro: {settings.GEMINI_PRO_MODEL}")


def menu_coverage() -> None:
    hr("MENU PIPELINE — coverage over real restaurants")
    from backend.services.menu_service import get_menu
    from backend.tools import places_tools

    if not settings.serpapi_configured:
        print("  SerpApi not configured — cannot resolve place_ids (google_maps). Skipping.")
        return

    cov = {"ocr": 0, "web": 0, "unresolved": 0}
    total_items = 0
    print(f"  {'Restaurant':<28}{'place_id':<24}{'source':<10}{'items':>6}")
    print("  " + "-" * 66)
    for r in RESTAURANTS:
        try:
            res = places_tools.search_restaurants.invoke(
                {"query": r["name"], "location": r["location"], "max_results": 1}
            )
            rows = res.get("restaurants", []) if res.get("status") == "ok" else []
            if not rows:
                cov["unresolved"] += 1
                print(f"  {r['name']:<28}{'(unresolved)':<24}{'-':<10}{'-':>6}")
                continue
            pid, rname = rows[0]["id"], rows[0]["name"]
            menu = get_menu(pid, rname)
            source = menu.get("source", "?")
            items = sum(len(s.get("items", [])) for s in menu.get("sections", []))
            total_items += items
            cov[source] = cov.get(source, 0) + 1
            print(f"  {(rname or r['name'])[:27]:<28}{pid[:22]:<24}{source:<10}{items:>6}")
        except Exception as e:
            cov["unresolved"] += 1
            print(f"  {r['name']:<28}ERROR: {str(e)[:30]}")

    n = len(RESTAURANTS)
    hr("COVERAGE SUMMARY")
    print(f"  Restaurants attempted : {n}")
    print(f"  Structured/OCR menus  : {cov.get('ocr', 0)}  ({100*cov.get('ocr',0)//n}%)")
    print(f"  Web-fallback only     : {cov.get('web', 0)}")
    print(f"  Unresolved/error      : {cov['unresolved']}")
    print(f"  Total menu items      : {total_items}")


def agent_checks() -> None:
    hr("AGENTS / TOOLS — quick live checks")

    # Supervisor chat (Gemini -> Ollama fallback handled inside run_chat)
    import asyncio

    from backend.services.llm import is_llm_available

    if is_llm_available():
        from backend.agents.supervisor import run_chat

        async def _ask(q, tid):
            return await asyncio.wait_for(run_chat(q, thread_id=tid), timeout=90)

        for i, q in enumerate(["Find me a good biryani place in Kolkata", "Cheapest flight CCU to DEL next month"]):
            try:
                reply = asyncio.run(_ask(q, f"smoke-{i}"))
                print(f"  chat> {q}\n    -> {reply[:200]}")
            except Exception as e:
                print(f"  chat> {q}\n    -> (slow/failed: {type(e).__name__}: {str(e)[:80]})")
    else:
        print("  chat: no LLM provider (set GEMINI_API_KEY or enable Ollama) — skipped")

    if settings.serpapi_configured:
        from backend.tools import serpapi_tools

        f = serpapi_tools.search_flights.invoke({"origin": "CCU", "destination": "DEL", "departure_date": "2026-07-20"})
        cheapest = f.get("cheapest") if f.get("status") == "ok" else None
        print(f"  flights CCU->DEL cheapest: {cheapest.get('price') if cheapest else f.get('status')}")
        s = serpapi_tools.search_products.invoke({"query": "noise cancelling headphones", "max_results": 3})
        print(f"  shopping results: {s.get('count') if s.get('status')=='ok' else s.get('status')}")
    else:
        print("  flights/shopping: SERPAPI not configured — skipped")


def main() -> None:
    print("Kensho backend smoke test")
    config_status()
    menu_coverage()
    agent_checks()
    hr("DONE")


if __name__ == "__main__":
    main()
