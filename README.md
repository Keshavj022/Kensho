# Kensho · an atlas for taste

> **見性 (kenshō)** — "seeing one's true nature." One AI assistant that routes you to three specialists — **restaurants & menus**, **travel metasearch**, and **shopping** — before you decide.

Built on **LangChain 1.x + LangGraph**, **Google Gemini** (LLM + vision), **SerpApi**, **Neo4j**, **ChromaDB**, **ElevenLabs**, and **FastAPI**.

---

## Features

| Domain | Capability |
|---|---|
| **Eat** | Restaurant search via Google Maps · structured menus extracted from photos by Gemini vision · cross-restaurant dish search · voice/text ordering → cart → `order_online` handoff |
| **Go** | Flight & hotel metasearch — cheapest option, provider, deep link, and price context · day-by-day trip planner |
| **Buy** | Product search across merchants with real prices, ratings, and direct links |
| **Ask** | Unified chat assistant — Gemini supervisor classifies intent and dispatches to the right specialist, personalized by the user's taste profile |
| **Onboarding** | Animated multi-step wizard: name · DOB · geolocation (one-tap, reverse-geocoded) · diet type · allergies · health goals · liked foods · cuisines · spice tolerance — bridged to both SQLite and Neo4j |
| **Voice** | ElevenLabs Scribe STT → menu item resolution → TTS confirmation · offline `faster-whisper` fallback |
| **Demo mode** | Full-stack demo account (real JWT, pre-seeded taste profile) — no sign-up required |

**Scope guardrails (by design):** travel is search-only (no booking, no payment); food ordering is cart + `order_online` handoff only. Every external integration is optional — a missing API key disables only its tool; the app boots and serves all other routes.

---

## Architecture

```
HTTP request
  └─> FastAPI route
        └─> LangGraph SUPERVISOR (Gemini router)  ── routes to one specialist ──┐
                                                                                │
              ┌──────────────────────────────────────────────────────────────────┘
              ▼
   ┌────────────────────┬─────────────────────┬──────────────────────┐
   │ restaurant_agent   │ travel_agent        │ shopping_agent       │
   │ (food + menus)     │ (flight/hotel meta) │ (product search)     │
   └─────────┬──────────┴──────────┬──────────┴──────────┬───────────┘
             ▼                     ▼                      ▼
         LangChain @tool functions call external APIs
   SerpApi (maps · flights · hotels · shopping · photos) · Tavily · Neo4j · Chroma
```

- Each specialist is a **`create_agent` ReAct agent** given only its own tools — no shared state, no bleed-over.
- The supervisor is a **`langgraph-supervisor` compiled graph** with a **SqliteSaver checkpointer** — full conversation persistence keyed by `thread_id`.
- **Gemini → Ollama fallback** is graph-level: two compiled supervisors, one per provider. If a Gemini call fails or `GEMINI_API_KEY` is unset, `run_chat` automatically falls through to a local Ollama model.
- **Neo4j** stores the knowledge graph (user → preference → restaurant/cuisine/dish nodes); **ChromaDB** stores menu-item embeddings for cross-restaurant semantic dish search.

---

## The keystone: menu pipeline

`menu_service.get_menu(place_id)` runs a deterministic cascade that turns a `place_id` into a validated, cached, searchable structured menu:

1. **Cache check** — return a fresh `menu_cache` row if `< 30 days` old (no repeat OCR).
2. **Photo fetch** — `serpapi / google_maps_photos` → user-posted photos (unlabeled).
3. **Classify** — Gemini vision flags which photos are menu boards (the API won't tell you; this step is required).
4. **Extract** — `ocr_service.extract_menu`: Gemini reads the menu photo(s) → structured `Menu` (sections → items with price, description, dietary flags). Flash model by default; escalates to Pro for low-quality photos. Handles multilingual menus (English + Hindi/Bengali/regional scripts).
5. **Fallback** — no readable photo → Tavily web search / expose only the `order_online` link.
6. **Persist + embed** — write to `menu_cache`, embed every item into Chroma (`menu_items`) so dish search works across restaurants.

---

## Personalization

The onboarding wizard captures a **diner profile** — location (geolocation → reverse-geocoded, editable), diet type, allergies, health goals, liked dishes, cuisines, spice tolerance — persisted to SQLite **and** bridged to Neo4j on write.

That profile is injected at every layer:

- **Chat** injects hard constraints (diet + allergies — *exclude even if uncertain*) and soft preferences (likes, cuisines, goals, spice) into the system prompt.
- **Restaurant search** defaults its diet filter and biases results to the user's coordinates.
- **Travel** defaults the *From* airport to the user's **nearest airport** (haversine over a curated IATA dataset).
- **Home** shows a "Restaurants near you" rail once authenticated.

---

## Voice & ordering

1. Audio → **ElevenLabs Scribe STT** (or `faster-whisper` offline) → text.
2. Text → **order resolver**: fuzzy-match + Gemini disambiguation, constrained to real `item_id`s from the restaurant's cached `Menu` — never fabricates items.
3. Cart updated → **ElevenLabs TTS** confirmation.
4. Checkout = `order_online` handoff link. No payment.

---

## Tech stack

| Layer | Technology |
|---|---|
| **LLM / vision** | Google Gemini via `langchain-google-genai` · optional local fallback via `langchain-ollama` |
| **Orchestration** | LangChain 1.x · LangGraph · `langgraph-supervisor` · `create_agent` ReAct (no `AgentExecutor`) |
| **Search tools** | SerpApi engines: `google_maps` · `google_flights` · `google_hotels` · `google_shopping` · `google_maps_photos` · Tavily web search |
| **Knowledge graph** | Neo4j (user · preference · restaurant nodes) |
| **Vector store** | ChromaDB with Gemini embeddings (`gemini-embedding-001`) |
| **Voice** | ElevenLabs Scribe STT + TTS · `faster-whisper` offline STT fallback |
| **API** | FastAPI (async) · Pydantic v2 · loguru |
| **Persistence** | SQLAlchemy + SQLite (dev) / Postgres (prod) · LangGraph `SqliteSaver` checkpointer |
| **Auth** | JWT (email-based) · passlib bcrypt · refresh tokens · SQLite-backed |
| **Language** | Python 3.11+ |

---

## Repository layout

```
Kensho/
├── .env.example
├── pytest.ini
├── tests/                            # legacy integration / smoke tests
├── scripts/
│   └── smoke_test.py                 # live menu-pipeline coverage test
├── backend/
│   ├── main.py                       # FastAPI app + lifespan (DB, KG, Chroma, agents)
│   ├── config/settings.py            # pydantic-settings; all env vars
│   ├── db/                           # SQLAlchemy engine + ORM (auth, profiles, menu_cache, carts)
│   ├── agents/
│   │   ├── supervisor.py             # LangGraph supervisor graph (entry point)
│   │   ├── restaurant_agent.py       # food / menu specialist
│   │   ├── travel_agent.py           # flight + hotel metasearch specialist
│   │   ├── shopping_agent.py         # product search specialist
│   │   └── state.py                  # shared TypedDict graph state
│   ├── tools/                        # @tool backbone (places, serpapi, search, kg, rag, menu, trip)
│   ├── services/                     # llm, ocr, menu, voice, order, auth, user,
│   │                                 #   knowledge_graph, rag, vector_index, location, airports
│   ├── models/                       # Pydantic v2 schemas
│   ├── api/                          # route handlers
│   └── tests/                        # pytest (external APIs mocked)
└── frontend/                         # React 18 · TypeScript · Vite · Tailwind · framer-motion
```

---

## Getting started

### Prerequisites

- Python 3.11+
- Node.js 18+
- *(optional)* Neo4j, Ollama

### Backend

```bash
python3 -m venv .venv
.venv/bin/pip install -r backend/requirements.txt

cp .env.example .env   # fill in the keys you have — all optional

.venv/bin/python -m uvicorn backend.main:app --reload --port 8000
```

- API docs: `http://localhost:8000/docs`
- Health: `http://localhost:8000/health`

### Frontend

```bash
cd frontend && npm install && npm run dev   # → http://localhost:5173
```

Vite proxies `/api` and `/health` to `:8000` automatically.

---

## API surface (`/api/v1`)

| Area | Endpoints |
|---|---|
| **Chat** | `POST /chat` — `{message, user_id?, thread_id?}` → supervisor |
| **Restaurants** | `POST /restaurants/search` · `GET /restaurants/{place_id}` · `GET /restaurants/{place_id}/menu` · `POST /restaurants/dishes/search` |
| **Travel** | `POST /travel/flights/search` · `POST /travel/hotels/search` · `POST /travel/itinerary` |
| **Shopping** | `POST /shopping/search` |
| **Voice** | `POST /voice/stt` · `POST /voice/tts` · `POST /voice/order` · `GET /voice/cart` · `GET /voice/voices` |
| **Auth** | `POST /auth/register` · `POST /auth/login` · `POST /auth/refresh` · `POST /auth/logout` · `GET /auth/me` · `PUT /auth/profile` · `POST /auth/demo` |
| **Location** | `GET /location/reverse` · `GET /location/ip` · `GET /location/nearest-airport` |
| **Knowledge graph** | `/knowledge-graph/*` — preferences · recommendations · interactions · insights |
| **Health** | `GET /health` · `/health/db` · `/health/kg` · `/health/rag` · `/health/llm` |

---

## Testing

```bash
# unit tests (all external APIs mocked — no keys required)
.venv/bin/python -m pytest -q

# live smoke test: menu-extraction coverage over ~10 real restaurants
# (requires GEMINI_API_KEY + SERPAPI_API_KEY)
.venv/bin/python scripts/smoke_test.py

# frontend production build (strict tsc + vite)
cd frontend && npm run build
```

---

## Configuration

All settings are env-driven via `pydantic-settings`. Copy `.env.example` → `.env`. Missing keys disable only their tool — the app never crashes on an unconfigured integration.

Key variables: `GEMINI_API_KEY`, `SERPAPI_API_KEY`, `GOOGLE_MAPS_API_KEY`, `TAVILY_API_KEY`, `ELEVENLABS_API_KEY`, `NEO4J_*`, `DATABASE_URL`, `JWT_SECRET_KEY`.

---

*Kensho hands off — it never books or charges you.*
*Built with LangChain · LangGraph · Gemini · SerpApi · Neo4j · ChromaDB · ElevenLabs · FastAPI · React.*
