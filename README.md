# Kensho · an atlas for taste

> **見性 (kenshō)** — "seeing one's true nature." Kensho is an AI multi-agent platform that helps you **see what to eat, where to go, and what to buy** before you decide.

One assistant routes you to three specialists — **restaurants & menus**, **travel metasearch**, and **shopping** — built on **LangChain 1.0 + LangGraph**, **Google Gemini** (with an optional local **Ollama** fallback), **SerpApi**, **Neo4j**, **ChromaDB**, and **ElevenLabs**, behind an async **FastAPI** backend and a hand-crafted **React + Vite + Tailwind** frontend.

> The authoritative build spec lives in [`CLAUDE.md`](./CLAUDE.md).

---

## What it does

| Domain | What you get |
|---|---|
| 🍽️ **Eat** | Restaurant search (Google Maps via SerpApi), a **structured menu extracted from photos** by Gemini vision, cross-restaurant dish search, and **voice/text ordering** → cart → `order_online` handoff |
| ✈️ **Go** | Flight & hotel **metasearch** — the cheapest option, the provider offering it, a deep link, and price context — plus a day-by-day **trip planner** |
| 🛍️ **Buy** | Product search across merchants with real prices, ratings, and links |
| 🤖 **Ask** | A unified chat assistant — a Gemini **supervisor** classifies intent and hands off to the right specialist, personalized by your taste profile |

### Scope guardrails (by design)

- **Travel is search-only metasearch** (Skyscanner-style). No booking, no payments.
- **Food "ordering" is cart + handoff.** Build a cart from the menu, then hand off to Google's `order_online` deep link. No order placement, no payment.
- **Every external integration is optional.** A missing API key disables only that tool — the app still boots and serves every other route (graceful degradation).

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
         LangChain @tool functions (the backbone) call external APIs
   SerpApi (maps · flights · hotels · shopping · photos) · Tavily · Neo4j · Chroma
```

- Each specialist is a `create_agent` ReAct agent given **only its own tools**.
- The supervisor is a `langgraph-supervisor` graph compiled with a **SqliteSaver checkpointer** — conversation state is persisted by `thread_id`.
- **Gemini → Ollama fallback** is graph-level: one compiled supervisor per provider; if a Gemini call fails (or it's unconfigured), `run_chat` falls back to a local Ollama model.

### Tech (locked decisions — no substitutes)

- **Orchestration:** LangChain 1.x + LangGraph + `langgraph-supervisor` (no `AgentExecutor`/`initialize_agent`).
- **LLM:** Google Gemini via `langchain-google-genai` (also the **menu OCR** engine). Optional local fallback via `langchain-ollama`.
- **Tools:** SerpApi (`google_maps`, `google_flights`, `google_hotels`, `google_shopping`, `google_maps_photos`) called over `httpx`; **Tavily** web search.
- **Knowledge graph:** Neo4j. **Vectors / RAG:** ChromaDB with Gemini embeddings.
- **Voice:** ElevenLabs (Scribe STT + TTS); offline fallback `faster-whisper`.
- **Persistence:** SQLAlchemy + SQLite (dev) / Postgres (prod). **API:** async FastAPI. **Logging:** loguru. Python 3.11+, Pydantic v2.

---

## Repository layout

```
Kensho/
├── CLAUDE.md                     # authoritative build spec
├── .env.example                  # copy to .env
├── pytest.ini                    # test config (scoped to backend/tests)
├── scripts/
│   └── smoke_test.py             # exercises every agent + the menu pipeline live
├── backend/
│   ├── main.py                   # FastAPI app + lifespan
│   ├── config/settings.py        # pydantic-settings; every env var
│   ├── db/                       # SQLAlchemy engine + ORM (auth, profiles, menu_cache, carts)
│   ├── agents/                   # supervisor + restaurant/travel/shopping specialists
│   ├── tools/                    # @tool backbone: places, serpapi, search, kg, rag, menu, trip
│   ├── services/                 # llm, ocr, menu, voice, order, vector_index, location,
│   │                             #   airports, knowledge_graph, rag, auth, user
│   ├── models/                   # Pydantic v2 schemas (incl. menu.py keystone)
│   ├── api/                      # routes: chat, restaurants, menu, travel, shopping,
│   │                             #   voice, auth, knowledge_graph, location, health
│   └── tests/                    # pytest (external APIs mocked)
└── frontend/                     # React 18 + TS + Vite + Tailwind + framer-motion
    └── src/
        ├── pages/                # Home, Assistant, Restaurants, RestaurantDetail,
        │                         #   Travel, Shopping, Auth
        ├── components/           # Nav, Footer, Chat, AssistantDock, CartDrawer,
        │                         #   Onboarding (wizard), NearYou, RequireAuth, ui, fx
        ├── state/                # auth + cart contexts
        └── lib/                  # api client, types, session, geo, onboarding data
```

---

## Getting started

### Prerequisites
- **Python 3.11+**
- **Node.js 18+**
- *(optional)* Neo4j, and an Ollama daemon for the LLM fallback

### 1. Backend

```bash
# from the repo root
python3 -m venv .venv
.venv/bin/pip install -r backend/requirements.txt

cp .env.example .env        # then fill in the keys you have (all optional — see below)

.venv/bin/python -m uvicorn backend.main:app --reload --port 8000
```

- API: `http://localhost:8000` · Docs: `http://localhost:8000/docs` · Health: `http://localhost:8000/health`

> Optional offline speech-to-text fallback (heavy — pulls ctranslate2):
> `.venv/bin/pip install "faster-whisper>=1.0.0"`

### 2. Frontend

```bash
cd frontend
npm install
npm run dev                 # → http://localhost:5173
```

The Vite dev server proxies `/api` and `/health` to `:8000`, so the frontend talks to your running backend automatically.

---

## Configuration

All settings are env-driven via `config/settings.py` (no hardcoded secrets or model IDs). Copy `.env.example` → `.env`. **Every key is optional** — a missing key disables only its tool.

```env
# LLM (Google Gemini)
GEMINI_API_KEY=
GEMINI_MODEL=gemini-2.5-flash          # default GA Flash; override if you want a newer one
GEMINI_PRO_MODEL=gemini-2.5-pro        # escalation model for hard menu OCR
GEMINI_EMBEDDING_MODEL=models/gemini-embedding-001

# Open-source LLM fallback (used when Gemini fails or is unset)
OLLAMA_ENABLED=false
OLLAMA_MODEL=llama3.1                   # must be tool-capable (llama3.1, qwen2.5, …)
OLLAMA_VISION_MODEL=llama3.2-vision     # menu-OCR fallback

# Tools — maps/flights/hotels/shopping/photos ALL run on SerpApi (no Google key needed)
SERPAPI_API_KEY=
TAVILY_API_KEY=                         # web search
SERPAPI_GL=in                           # locale: country (in = India)  →  INR prices
DEFAULT_CURRENCY=INR

# Voice (ElevenLabs)
ELEVENLABS_API_KEY=

# Knowledge graph (Neo4j) + vectors (Chroma) + relational DB
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=
CHROMA_PATH=./chroma_data
DATABASE_URL=sqlite:///./kensho.db

# Auth + app
JWT_SECRET_KEY=change-me-to-a-long-random-string
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
DEBUG=true
```

> **Localization:** results default to India (`gl=in`, INR). Change `SERPAPI_GL` / `DEFAULT_CURRENCY` for another market — no code change.

---

## The keystone: the menu pipeline

For any restaurant, `menu_service.get_menu(place_id)` runs a cached cascade:

1. **Cache** — return a fresh `menu_cache` row if `< 30 days` old.
2. **Photos** — fetch user-posted photos via SerpApi `google_maps_photos`.
3. **Classify** — Gemini vision flags which photos are actually menus.
4. **Extract** — Gemini reads the menu into a structured, multilingual `Menu` (sections → items with price, description, dietary flags). Flash by default; escalates to Pro for hard photos.
5. **Fallback** — no readable menu → web search / expose only the `order_online` link.
6. **Persist + embed** — save to `menu_cache` and embed each item into Chroma (`menu_items`) so **dish search works across restaurants**.

A live smoke test over ~10 real restaurants typically extracts structured menus for ~40% (the rest have no menu-board photos and fall back gracefully).

---

## Personalization & onboarding

Sign-up is an animated, multi-step **onboarding wizard** that captures a diner profile: name, DOB, gender, **location** (one-tap geolocation → reverse-geocoded, editable), **diet type**, **allergies**, **health goals**, **liked foods** (diet-aware) + favourite cuisines, and spice tolerance.

That profile is persisted to SQLite **and** bridged to Neo4j, then used everywhere:

- **Chat** injects a compact context separating **HARD constraints** (diet + allergies — *exclude even if a dish's ingredients are uncertain*) from **SOFT preferences** (likes, cuisines, goals, spice).
- **Restaurant search** defaults its diet filter and biases to your coordinates ("near you").
- **Travel** defaults the *From* airport to your **nearest airport** (curated dataset, haversine).
- The home page shows a **"Restaurants near you"** rail once you're signed in.

**Auth is email-based** (no username) and all app pages are **gated behind sign-in** (the landing page stays public).

---

## Voice & ordering

- **STT:** ElevenLabs Scribe → text (offline `faster-whisper` fallback). **TTS:** ElevenLabs.
- **Ordering:** audio/text → resolve against the restaurant's real `Menu` (Gemini disambiguation + fuzzy match, **only ever mapping to existing `item_id`s**) → update the cart → **checkout = the `order_online` handoff link**. No payment.

---

## API surface (prefix `/api/v1`)

| Area | Endpoints |
|---|---|
| **Chat** | `POST /chat` — `{message, user_id?, thread_id?}` → runs the supervisor |
| **Restaurants** | `POST /restaurants/search` · `GET /restaurants/{place_id}` · `GET /restaurants/{place_id}/menu` · `POST /restaurants/dishes/search` |
| **Travel** | `POST /travel/flights/search` · `POST /travel/hotels/search` · `POST /travel/itinerary` |
| **Shopping** | `POST /shopping/search` |
| **Voice** | `POST /voice/stt` · `POST /voice/tts` · `POST /voice/order` · `GET /voice/cart` · `GET /voice/voices` |
| **Auth** | `POST /auth/register` · `POST /auth/login` · `POST /auth/refresh` · `POST /auth/logout` · `GET /auth/me` · `GET /auth/check-email` · `GET\|PUT /auth/profile` · `POST /auth/change-password` · admin user routes |
| **Location** | `GET /location/reverse` · `GET /location/ip` · `GET /location/nearest-airport` |
| **Knowledge graph** | `/knowledge-graph/*` — preferences, recommendations, interactions, insights |
| **Health** | `GET /health` + `/health/{db,kg,rag,llm}` |

### Examples

**Register (email-based) & log in**
```http
POST /api/v1/auth/register        →   POST /api/v1/auth/login
{ "email": "you@example.com",          { "email": "you@example.com",
  "password": "secret123" }              "password": "secret123" }
# login → { access_token, refresh_token, token_type, expires_in }
# use:  Authorization: Bearer <access_token>
```

**Search restaurants (near coordinates)**
```http
POST /api/v1/restaurants/search
{ "query": "biryani", "location": "Kolkata", "lat": 22.57, "lng": 88.36,
  "radius": 6000, "cuisine": "mughlai", "dietary": "non-vegetarian", "max_results": 18 }
```

**Flights (metasearch, no booking)**
```http
POST /api/v1/travel/flights/search
{ "origin": "CCU", "destination": "DEL", "departure_date": "2026-07-20" }
# → { status, currency, cheapest, flights:[{price, airlines, stops, legs, booking_token}], price_insights }
```

**Chat (personalized when user_id is set)**
```http
POST /api/v1/chat
{ "message": "vegan dinner near me, then the cheapest flight home", "user_id": "user_…" }
```

---

## Testing

```bash
# unit tests — external APIs are mocked; deterministic regardless of your .env
.venv/bin/python -m pytest -q          # ~48 tests, runs in seconds

# live smoke test — menu-extraction coverage over ~10 real restaurants
# (needs GEMINI + SERPAPI keys in .env)
.venv/bin/python scripts/smoke_test.py

# frontend production build (strict tsc + vite)
cd frontend && npm run build
```

Per-subsystem health: `GET /health/db`, `/health/kg`, `/health/rag`, `/health/llm`.

---

## Frontend design — "Culinary Atlas"

A deliberately non-generic aesthetic: a warm paper-cream canvas with ink-black type, a vivid **tandoor-saffron** primary, and **pine** (travel) / **plum** (shopping) accents. Editorial/magazine layout with a film-grain overlay and **Fraunces** (display) + **Hanken Grotesk** (body) + **Space Mono** (labels/prices). Rich Motion choreography — staggered reveals, magnetic hovers, route transitions, a floating assistant dock, and an animated "taste passport" review at the end of onboarding.

Stack: React 18 · TypeScript · Vite 5 · Tailwind 3 · framer-motion · lucide-react.

---

## Do NOT

- Use `AgentExecutor` / `initialize_agent` (deprecated) — use `create_agent` / LangGraph.
- Add any `azure-*` dependency (the legacy Azure AI Foundry stack has been removed).
- Implement real booking or payment for flights, hotels, or food — search + metasearch + cart/handoff only.
- Re-OCR a menu on every request — always cache by `place_id`.
- Hardcode secrets or volatile model IDs — everything is env-driven.

---

## License

MIT.

---

*Kensho hands off — it never books or charges you. Built with LangChain · LangGraph · Gemini · SerpApi · Neo4j · ChromaDB · ElevenLabs · FastAPI · React.*
