# CLAUDE.md — Kensho Backend (v2 rewrite)

## What this is

Kensho is an AI multi-agent platform spanning three domains: **restaurants/food**, **travel**, and **shopping**. This document is the authoritative build spec for a **full rewrite of the backend** that replaces the legacy **Azure AI Foundry** agents with a **LangChain 1.0 + LangGraph** multi-agent system. Build the backend to satisfy this spec.

You are working inside the existing repo. The current `backend/` is a FastAPI app built on Azure AI Foundry, Neo4j, and ChromaDB.

- **Preserve & adapt:** the Neo4j knowledge-graph logic (`services/knowledge_graph_service.py`), the ChromaDB RAG logic (`services/rag_service.py`), the JWT auth flow, the user/preference Pydantic models, and the project's graceful-degradation philosophy.
- **Replace:** the two Azure AI Foundry agents (`agents/*.py`) with LangGraph agents.
- **Remove:** all `azure-*` dependencies (`azure-ai-projects`, `azure-identity`, Azure Speech SDK, Azure Vision SDK), the in-memory `active_threads` dicts, the JSON-file auth store, and the broken itinerary service (it calls `async` methods synchronously).

## Locked technology decisions — do NOT substitute

- **Orchestration:** LangChain 1.0 + LangGraph. Use `create_agent` for the specialist agents and a LangGraph supervisor for routing. **Never** use the deprecated `AgentExecutor` / `initialize_agent`.
- **LLM:** Google Gemini via `langchain-google-genai`. Gemini is also the **menu OCR** engine (multimodal) — do not add a separate OCR library.
- **Tool backbone:** Google **Places API (New)** + **SerpApi** engines (Google Flights, Google Hotels, Google Maps + Google Maps Photos, Google Shopping) + **Tavily** web search.
- **Knowledge graph:** Neo4j (reuse). **Vector store / RAG:** ChromaDB (reuse).
- **Voice:** **ElevenLabs** for TTS and STT (Scribe). Fallback STT: `faster-whisper` (self-hosted, offline).
- **API:** FastAPI (async). **Relational persistence:** SQLAlchemy + SQLite (dev) / Postgres (prod). **Logging:** loguru.
- **Language:** Python 3.11+, Pydantic v2.

## Scope guardrails (important)

- **Travel is search-only metasearch (Skyscanner-style).** Return the cheapest option, the provider/app offering it, a deep link, and price context. **No booking, no payments.**
- **Food "ordering" is cart + handoff.** Build a cart from the structured menu, then hand off to Google's `order_online` deep link. **Do not** implement real order placement or payment (no public ordering API exists for arbitrary restaurants).
- **Every external integration is optional.** If an API key is missing, the corresponding tool returns a clear "not configured" result and the app still boots and serves other routes. **Never crash on a missing key.**

## Architecture

```
HTTP request
  └─> FastAPI route
        └─> LangGraph SUPERVISOR (Gemini router)  ──routes to one specialist──┐
                                                                              │
              ┌───────────────────────────────────────────────────────────────┘
              ▼
   ┌────────────────────┬─────────────────────┬──────────────────────┐
   │ restaurant_agent   │ travel_agent        │ shopping_agent       │
   │ (food + menus)     │ (flight/hotel meta) │ (product search)     │
   └─────────┬──────────┴──────────┬──────────┴──────────┬───────────┘
             ▼                     ▼                     ▼
         LangChain @tool functions (the backbone) call external APIs
         Google Places · SerpApi engines · Tavily · Neo4j · ChromaDB
```

- Each specialist is a `create_agent` ReAct agent given **only its own tools**.
- The **supervisor** is a LangGraph graph (use the `langgraph-supervisor` prebuilt `create_supervisor`, or a hand-rolled `StateGraph` with a Gemini router node + conditional edges). It classifies intent, dispatches to one specialist, and returns the result.
- **Conversation state** is persisted via a LangGraph **checkpointer** (`SqliteSaver` dev / `PostgresSaver` prod), keyed by `thread_id`. This replaces the legacy in-memory `active_threads`.
- Neo4j and ChromaDB are exposed to agents **as tools/retrievers**, not hand-wired into agent message-building.

### Target directory structure (guide, not gospel)

```
backend/
├── main.py                       # FastAPI app + lifespan (init DB, KG, Chroma, agents)
├── dependencies.py               # auth dependencies (reuse/adapt)
├── requirements.txt
├── config/
│   └── settings.py               # pydantic-settings; all env vars
├── db/
│   ├── database.py               # SQLAlchemy engine/session
│   └── models.py                 # ORM: users, user_profiles, menu_cache, carts
├── agents/
│   ├── supervisor.py             # LangGraph supervisor graph (entry point)
│   ├── restaurant_agent.py       # food/restaurant specialist
│   ├── travel_agent.py           # travel metasearch specialist
│   ├── shopping_agent.py         # shopping specialist
│   └── state.py                  # shared graph state (TypedDict: messages, user_id, ...)
├── tools/
│   ├── places_tools.py           # Google Places (New): search, details
│   ├── menu_tools.py             # menu cascade entrypoint (calls menu_service)
│   ├── serpapi_tools.py          # flights, hotels, shopping, maps photos
│   ├── search_tools.py           # Tavily web search
│   ├── kg_tools.py               # Neo4j prefs/recs/tracking tools
│   └── rag_tools.py              # Chroma retrievers (restaurant context, dish search)
├── services/
│   ├── llm.py                    # Gemini model factory (langchain-google-genai)
│   ├── ocr_service.py            # Gemini vision: menu image -> structured JSON
│   ├── menu_service.py           # menu pipeline orchestration + caching
│   ├── voice_service.py          # ElevenLabs STT/TTS (+ faster-whisper fallback)
│   ├── knowledge_graph_service.py# Neo4j (REUSE/adapt)
│   ├── rag_service.py            # Chroma (REUSE/adapt)
│   ├── auth_service.py           # JWT (reuse; move store JSON -> DB)
│   └── user_service.py           # profiles (move to DB; bridge to Neo4j)
├── models/                       # Pydantic v2 schemas
│   ├── chat.py  restaurant.py  menu.py  travel.py  shopping.py  voice.py  auth.py
└── api/
    ├── chat_routes.py            # unified agent entry (supervisor)
    ├── restaurant_routes.py  travel_routes.py  shopping_routes.py
    ├── menu_routes.py            # menu JSON + photo URLs for the website
    ├── voice_routes.py  auth_routes.py  kg_routes.py
    └── health_routes.py
scripts/
└── smoke_test.py                 # exercises every agent + the menu pipeline
.env.example
```

## Tools (the agent-facing backbone)

Every tool is a LangChain `@tool`. **The docstring is the description the LLM uses to decide when to call the tool — write each one precisely.** Tools return clean structured data (Pydantic models or dicts), wrap external calls in try/except, cache expensive results, and degrade gracefully.

- `places_tools.search_restaurants(query=None, location=None, lat=None, lng=None, radius=5000, cuisine=None, price_level=None, open_now=None, min_rating=None, dietary=None, max_results=20)` — Google **Places API (New)** Nearby/Text Search. **Always field-mask requests** (`X-Goog-FieldMask`) to control billing. Returns normalized restaurants: `id` (= place_id), `name`, `rating`, `price_level`, `location{lat,lng}`, `address`, `types`, `open_now`.
- `places_tools.get_restaurant_details(place_id)` — Place Details (New), field-masked.
- `menu_tools.get_menu(place_id)` — runs the menu cascade (see below). Cached.
- `serpapi_tools.search_flights(origin, destination, departure_date, return_date=None, adults=1, sort="price")` — engine `google_flights`, `sort=2` (price). Returns `best_flights` (sorted), the cheapest, and `price_insights` (`lowest_price`, `price_level`, `typical_price_range`). **Metasearch only.**
- `serpapi_tools.resolve_flight_booking_options(booking_token)` — second call that returns `booking_options` (each with `book_with` seller name + `price`); surface the cheapest seller + deep link as "book on X".
- `serpapi_tools.search_hotels(location, check_in, check_out, guests=1)` — `google_hotels` / `google_maps`. Returns each provider via `all_options` (`source`, `price`, `link`, `official_site`). **Metasearch only.**
- `serpapi_tools.search_products(query, max_results=20)` — `google_shopping`. Returns `title`, `price`, `source` (merchant), `link`, `rating`.
- `serpapi_tools.get_place_photos(place_id)` — `google_maps_photos` (used by the menu pipeline). Returns user-posted photo URLs (unlabeled).
- `search_tools.web_search(query)` — Tavily. For destinations, activities, "best dishes," and general lookups.
- `kg_tools.*` — Neo4j: `get_user_preferences(user_id)`, `track_interaction(...)`, `recommend_restaurants(user_id)` (delegate to the existing service).
- `rag_tools.*` — Chroma retrievers: restaurant context + `search_dishes(query)` over the menu-items collection.

## Menu pipeline (the keystone feature)

Goal: **automatically build a structured menu per restaurant, cached**, that powers (a) website display, (b) cross-restaurant dish search, and (c) voice ordering.

`menu_service.get_menu(place_id)` runs this cascade:

1. **Cache check** — look up `menu_cache` by `place_id`; return if fresh (e.g. `< 30 days`).
2. **Fetch photos** — `serpapi_tools.get_place_photos(place_id)` → user-posted photos (these are NOT labeled "menu").
3. **Classify** — Gemini vision flags which photos are menu images (the API won't tell you; this step is required).
4. **Extract** — `ocr_service.extract_menu(menu_photo_urls)`: Gemini reads the menu photo(s) and returns a structured `Menu` (sections → items with price, description, dietary flags). Gemini handles **multilingual** menus (English + Hindi/Bengali/regional scripts).
5. **Fallback** — if no usable menu photos, `web_search` for menu info and/or expose only the `order_online` link.
6. **Persist** — save the `Menu` to `menu_cache`; then **embed each item into Chroma** (collection `menu_items`) so dish search works across restaurants. Return the `Menu`.

`ocr_service.extract_menu(image_urls)` — downloads images, calls Gemini with a strict "return JSON only" instruction, validates the output against the Pydantic `Menu` model, and sets `source="ocr"` with a per-item `confidence`. Use a Gemini Flash model for cost; escalate to Gemini Pro for hard/low-quality menu photos.

### Menu schema (Pydantic + mirror in ORM)

```python
class MenuItem(BaseModel):
    id: str
    name: str
    description: str | None = None
    price: float | None = None
    currency: str = "INR"
    section: str | None = None
    dietary_flags: list[str] = []        # e.g. ["veg","vegan","contains_nuts"]
    spice_level: str | None = None
    image_url: str | None = None
    source: Literal["structured","ocr","web"] = "ocr"
    confidence: float = 1.0

class Menu(BaseModel):
    restaurant_id: str                    # = place_id
    restaurant_name: str
    currency: str = "INR"
    sections: list[dict]                  # [{ "name": str, "items": list[MenuItem] }]
    source: Literal["structured","ocr","web"]
    extracted_at: datetime
    raw_photo_urls: list[str] = []
    order_online_url: str | None = None   # Google food.google.com/chooseprovider link
```

## Travel metasearch

- `search_flights`: SerpApi `google_flights`, `sort=2`. Return the sorted `best_flights`, the cheapest, and `price_insights` so the agent can say e.g. "below the typical range." For a chosen flight, call `resolve_flight_booking_options(booking_token)` → `booking_options` → cheapest seller + deep link. (Two-call flow; cache by route + dates.)
- `search_hotels`: SerpApi → `all_options` → cheapest provider (`source`) + `price` + `link` + `official_site` flag.
- Normalize both into a consistent shape: `TravelOption{ type, title, price, currency, provider, deep_link, price_context }`. **No booking.**

## Voice (food ordering + assistant)

- **STT:** ElevenLabs Scribe. **TTS:** ElevenLabs. **Fallback STT:** `faster-whisper`.
- **Ordering flow:** audio → STT → text → **resolve against the restaurant's `Menu` item list** (constrained matching: fuzzy match + Gemini disambiguation, only ever map to existing `item_id`s) → update cart (session/DB) → TTS confirmation. **Checkout = return the `order_online` handoff link.**
- Keep `voice_service` vendor-swappable (interface + concrete impls) so providers can change without touching routes.

## Persistence

SQLAlchemy models (DATABASE_URL → SQLite dev / Postgres prod):

- `user_auth` — migrate the legacy JSON auth store here: `user_id, username, email, hashed_password, role, is_active, created_at, refresh_tokens`.
- `user_profiles` — profile + dietary + preferences. **Bridge to Neo4j on write:** registering a user must create the profile row **and** the Neo4j user node (the legacy code keeps auth users and profiles in separate, disconnected stores — fix this).
- `menu_cache` — `place_id, menu_json, source, extracted_at`.
- `carts` (optional) — `user_id|session_id, restaurant_id, items`.
- LangGraph **checkpointer** tables (SqliteSaver/PostgresSaver) for conversation state.

Neo4j (knowledge graph) and Chroma (vectors) remain separate from the relational DB.

## API surface (FastAPI, prefix `/api/v1`)

- `POST /chat` — unified entry; runs the supervisor. Body `{message, user_id?, thread_id?}` → `{message, thread_id, ...}`. `thread_id` maps to a checkpointer thread.
- Restaurant: `POST /restaurants/search`, `GET /restaurants/{place_id}`, `GET /restaurants/{place_id}/menu` (structured menu + photo URLs for the website), `POST /restaurants/dishes/search`.
- Travel: `POST /travel/flights/search`, `POST /travel/hotels/search` (metasearch responses).
- Shopping: `POST /shopping/search`.
- Voice: `POST /voice/stt`, `POST /voice/tts`, `POST /voice/order` (audio → cart), `GET /voice/voices`.
- Auth: `register`, `login`, `refresh`, `logout`, `me` (reuse, now DB-backed).
- Knowledge graph: preferences, recommendations, insights (reuse existing routes).
- Health: `GET /health` + per-subsystem checks (`/health/kg`, `/health/rag`, `/health/llm`).

## Configuration

`config/settings.py` via `pydantic-settings`. Ship a `.env.example`. Keys:

```
GEMINI_API_KEY=
GEMINI_MODEL=            # default to a current Gemini Flash model — VERIFY the current ID at ai.google.dev
SERPAPI_API_KEY=
GOOGLE_MAPS_API_KEY=     # Places API (New) enabled
TAVILY_API_KEY=
ELEVENLABS_API_KEY=
NEO4J_URI=
NEO4J_USERNAME=
NEO4J_PASSWORD=
CHROMA_PATH=./chroma_data
DATABASE_URL=sqlite:///./kensho.db
JWT_SECRET_KEY=
JWT_ALGORITHM=HS256
CORS_ORIGINS=http://localhost:5173
DEBUG=true
```

Never hardcode secrets or model IDs.

## Conventions

- Async FastAPI; type hints everywhere; Pydantic v2.
- Tools are `@tool` with precise docstrings; return structured data; try/except around all external calls; degrade gracefully.
- loguru for logging; format with ruff + black; tests with pytest.
- **Cache expensive external calls** (menu OCR, SerpApi travel/flights) aggressively.
- Keep agents thin — business logic lives in `tools/` and `services/`.

## Suggested package set (pin to current versions; verify names)

`fastapi`, `uvicorn[standard]`, `pydantic`, `pydantic-settings`, `langchain`, `langgraph`, `langgraph-supervisor`, `langchain-google-genai`, `langchain-tavily`, SerpApi Python SDK, `neo4j`, `chromadb`, `sqlalchemy`, `python-jose[cryptography]`, `passlib[bcrypt]`, `elevenlabs`, `faster-whisper`, `httpx`, `python-multipart`, `loguru`.

> Note: Places API (New) has no first-class Python SDK — call its REST endpoints with `httpx` and `X-Goog-FieldMask` headers (the old `googlemaps` package targets the legacy API). SerpApi is called via its SDK or `httpx` against `serpapi.com/search`.

## Build order (sequence the work like this)

1. **Scaffolding** — `requirements.txt`, `settings.py`, `db/` (engine/session/ORM), Pydantic models, FastAPI skeleton + `/health`, `.env.example`.
2. **LLM + skeleton graph** — `services/llm.py` (Gemini factory) + a minimal supervisor with one trivial tool, wired to `/chat`, to prove LangGraph works end-to-end.
3. **Tools** — places, serpapi (flights/hotels/shopping/photos), tavily, kg, rag. Each independently testable.
4. **Agents** — restaurant, travel, shopping specialists + supervisor routing; wire to `/chat` and the per-domain routes.
5. **Menu pipeline** — `ocr_service` → `menu_service` (cascade + cache) → menu routes → embed items into Chroma.
6. **Voice** — `voice_service` (ElevenLabs TTS/STT + faster-whisper fallback) → voice routes → ordering resolver + cart.
7. **Auth + persistence migration** — JSON → DB; bridge auth ↔ profile ↔ Neo4j.
8. **Tests + smoke test**.

## Testing

- pytest unit tests for tools/services with **external APIs mocked**.
- `scripts/smoke_test.py`: hits each agent path and runs the menu pipeline against ~10 real restaurants (mix of chains + independents, include a couple in Kolkata) and prints coverage — how many got structured vs OCR'd menus. This validates the riskiest feature before UI/voice depend on it.
- Per-subsystem health endpoints must pass.

## Definition of done

- App boots with any subset of keys configured (missing keys degrade gracefully).
- `POST /chat` routes through the supervisor to all three specialists correctly.
- The menu pipeline produces a validated structured `Menu` for a real `place_id`, caches it, and embeds items into Chroma.
- Flight/hotel search returns cheapest option + provider + deep link + price context (no booking).
- Voice STT→cart→TTS round-trips, with order items resolved to real menu `item_id`s.
- Auth works against the DB; registration creates both a profile row and a Neo4j node.
- All health checks pass.

## Do NOT

- Use `AgentExecutor` / `initialize_agent` (deprecated) — use `create_agent` / LangGraph `StateGraph`.
- Add any `azure-*` dependency; remove the legacy ones.
- Implement real booking or payment for flights, hotels, or food — search + metasearch + cart/handoff only.
- Re-OCR a menu on every request — always cache by `place_id`.
- Hardcode secrets or volatile model IDs — env-driven; **verify the current Gemini model ID, the latest LangGraph/LangChain `create_agent`/supervisor API, and the current ElevenLabs STT (Scribe) API against official docs before finalizing.**
- Request unmasked Google Places (New) fields — always field-mask.
- Block the whole app when one optional service is unconfigured.

## Reference: legacy code map

- **Adapt:** `services/knowledge_graph_service.py` (Neo4j), `services/rag_service.py` (Chroma), the auth flow, user/preference models.
- **Remove:** `agents/restaurant_agent.py` + `agents/travel_agent.py` (Azure), all `azure-*` deps, in-memory `active_threads`, the sync-calls-`async` itinerary bug, the JSON-file auth store.
