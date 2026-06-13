# Kensho · an atlas for taste

> **見性 (kenshō)** — *“seeing one's true nature.”* One AI assistant, three appetites. Ask in plain words and Kensho routes you to the right specialist — **restaurants & menus**, **travel**, or **shopping** — before you decide.

A full-stack, multi-agent AI platform. A LangGraph **supervisor** classifies what you want and hands off to a domain specialist; each specialist calls real tools (Maps, Flights, Hotels, Shopping, web search, menus) and answers in natural language — personalized to your taste.

<p>
<img alt="Python" src="https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white">
<img alt="FastAPI" src="https://img.shields.io/badge/FastAPI-async-009688?logo=fastapi&logoColor=white">
<img alt="LangGraph" src="https://img.shields.io/badge/LangChain-1.x%20%C2%B7%20LangGraph-1C3C3C">
<img alt="React" src="https://img.shields.io/badge/React-18%20%C2%B7%20Vite%20%C2%B7%20TS-61DAFB?logo=react&logoColor=white">
<img alt="Tailwind" src="https://img.shields.io/badge/Tailwind%20%C2%B7%20Framer%20Motion-38BDF8?logo=tailwindcss&logoColor=white">
</p>

---

## ✨ Features

### 🍜 Eat — restaurants & menus
- **AI restaurant discovery** — search by cuisine, dish, vibe, or “near me,” with ratings, price ranges, photos, and open-now status.
- **Menus read from photographs** *(the keystone)* — Kensho gathers a restaurant’s user-posted photos, figures out which ones are menu boards, and uses vision AI to extract a **structured, multilingual menu** (sections → items with price, description, dietary tags). English + Hindi/Bengali/regional scripts.
- **Cross-restaurant dish search** — “spicy paneer,” “cold brew,” “creamy pasta” — semantic search across every menu Kensho has read.
- **Voice & text ordering** — speak or type an order; it’s matched to real menu items, built into a cart, and handed off to the restaurant’s “order online” link.

### ✈️ Go — travel metasearch
- **Flight & hotel metasearch** — the cheapest option, *who* is offering it, a deep link, and price context (“below the typical range”).
- **AI trip planner** — a day-by-day itinerary for a destination, blending flights, stays, and activities to your pace and interests.

### 🛍️ Buy — shopping
- **Product search across merchants** — real prices, ratings, merchant, and a direct buy link, so you find the best deal fast.

### 🤖 Ask — the assistant
- **One conversation, three specialists** — a Gemini/GPT supervisor reads your intent and delegates to the restaurant, travel, or shopping expert, then replies in a warm, natural voice.
- **Talk to Kensho** — a fully voice-driven assistant: speak, get a spoken reply (STT → reasoning → TTS).

### 🎯 Personalized to you
- **Animated onboarding** captures a taste profile — name, location (one-tap geolocation), diet, allergies, health goals, favourite dishes, cuisines, and spice tolerance.
- **Personalized recommendations** — restaurants and dishes tuned to your profile and what you’ve searched and ordered.

> **By design:** travel is *search-only* (no booking, no payment) and food ordering is *cart + handoff* only. Every external integration is optional — a missing key disables just that tool; the app still boots and serves everything else.

---

## 🏗️ Architecture

```
                         HTTP request
                              │
                              ▼
                       FastAPI route
                              │
                              ▼
            ┌──────────────────────────────────────┐
            │   LangGraph SUPERVISOR (LLM router)   │
            │   classifies intent → one specialist  │
            └───────┬───────────┬───────────┬───────┘
                    ▼           ▼           ▼
          ┌──────────────┬──────────────┬──────────────┐
          │ restaurant_  │ travel_      │ shopping_    │
          │ agent        │ agent        │ agent        │
          │ food + menus │ flights/     │ products     │
          │              │ hotels/trips │              │
          └──────┬───────┴──────┬───────┴──────┬───────┘
                 ▼              ▼              ▼
        LangChain @tool functions (the backbone)
   ──────────────────────────────────────────────────────
   SerpApi  ·  Tavily  ·  Vision OCR  ·  Neo4j  ·  ChromaDB
   (maps · flights · hotels · shopping · photos · web · menus)
```

- **Each specialist is a `create_agent` ReAct agent** given *only* its own tools — no shared state, no cross-domain bleed.
- **The supervisor is a compiled LangGraph** that persists conversation state per `thread_id`, so multi-turn context survives across requests.
- **Provider-flexible AI** — the LLM layer is abstracted across **Azure OpenAI → Google Gemini → local Ollama**. If the primary provider is unconfigured or a call fails, the platform automatically falls through to the next — chat, agents, and menu OCR keep working.
- **Knowledge graph + vector search** — Neo4j models the diner ↔ preference ↔ restaurant graph; ChromaDB holds menu-item embeddings for semantic dish search.

### Request workflow

1. The browser calls a FastAPI route (e.g. `POST /api/v1/chat`).
2. The route prepends the diner’s taste profile and invokes the **supervisor**.
3. The supervisor classifies intent and delegates to one specialist.
4. The specialist runs a **ReAct loop** — calling tools (search a place, read a menu, find flights) until it can answer.
5. The reply is returned in natural language; tools cache expensive results so repeat requests are instant.

---

## 🔑 The keystone: the menu pipeline

Turning a restaurant into a structured, searchable menu is the hardest, most valuable part of the product. `get_menu(place_id)` runs a deterministic cascade:

1. **Cache check** — return a recently-extracted menu if one exists (no repeat OCR).
2. **Fetch photos** — pull user-posted photos for the place.
3. **Classify** — vision AI flags which photos are actual menu boards (the source never labels them).
4. **Extract** — read the menu image(s) into a structured `Menu` — sections, items, prices, descriptions, dietary tags — across multiple languages and scripts.
5. **Fallback** — no readable menu? Fall back to web search and surface the order link.
6. **Persist + embed** — cache the menu and embed every item so it becomes searchable across all restaurants.

This one pipeline powers menu display, cross-restaurant dish search, and voice ordering.

---

## 🧰 Tech stack

| Layer | Technology |
|---|---|
| **AI / orchestration** | LangChain 1.x · LangGraph · `langgraph-supervisor` · `create_agent` ReAct agents |
| **LLM / vision** | Azure OpenAI · Google Gemini · local Ollama — provider-abstracted with automatic fallback |
| **Tools** | SerpApi (`google_maps` · `google_flights` · `google_hotels` · `google_shopping` · `google_maps_photos`) · Tavily web search |
| **Knowledge graph** | Neo4j |
| **Vector search** | ChromaDB embeddings for cross-restaurant dish search |
| **Voice** | ElevenLabs (STT + TTS) · `faster-whisper` offline STT fallback |
| **Backend** | FastAPI (async) · Pydantic v2 · SQLAlchemy · loguru · Python 3.11+ |
| **Auth** | JWT (email-based) · hashed passwords · refresh tokens |
| **Frontend** | React 18 · TypeScript · Vite · Tailwind CSS · Framer Motion |

---

## 📁 Repository layout

```
Kensho/
├── backend/
│   ├── main.py                 # FastAPI app + lifespan
│   ├── config/settings.py      # all env vars (pydantic-settings)
│   ├── agents/                 # supervisor + restaurant / travel / shopping specialists
│   ├── tools/                  # @tool backbone (places, serpapi, search, kg, rag, menu)
│   ├── services/               # llm, ocr, menu, voice, order, auth, user, knowledge_graph …
│   ├── models/                 # Pydantic v2 schemas
│   ├── api/                    # route handlers
│   └── tests/                  # pytest (external APIs mocked)
└── frontend/                   # React 18 · TypeScript · Vite · Tailwind · Framer Motion
```

---

## 🚀 Getting started

### Prerequisites
- Python 3.11+
- Node.js 18+
- *(optional)* Neo4j, Ollama — everything degrades gracefully without them

### 1. Backend

```bash
python3 -m venv .venv
.venv/bin/pip install -r backend/requirements.txt

cp .env.example .env          # fill in the keys you have — all optional

.venv/bin/python -m uvicorn backend.main:app --reload --port 8000
```

- API docs → `http://localhost:8000/docs`
- Health → `http://localhost:8000/health`

### 2. Frontend

```bash
cd frontend
npm install
npm run dev                    # → http://localhost:5173
```

Vite proxies `/api` and `/health` to `:8000` automatically.

---

## ⚙️ Configuration

All settings are environment-driven (`pydantic-settings`). Copy `.env.example` → `.env` and add the keys you have — a missing key disables only its tool, never the app.

| Key | Enables |
|---|---|
| `AZURE_OPENAI_*` / `GEMINI_API_KEY` | the assistant, agents, and menu OCR |
| `SERPAPI_API_KEY` | restaurants, flights, hotels, shopping, photos |
| `TAVILY_API_KEY` | web search & trip-planner activities |
| `ELEVENLABS_API_KEY` | voice (STT + TTS) |
| `NEO4J_*` | the preference knowledge graph |
| `DATABASE_URL` · `JWT_SECRET_KEY` | persistence & auth |

---

## 🧪 Testing

```bash
# unit tests — external APIs mocked, no keys required
.venv/bin/python -m pytest -q

# frontend production build (strict tsc + vite)
cd frontend && npm run build
```

---

## 🔌 API surface (`/api/v1`)

| Area | Endpoints |
|---|---|
| **Chat** | `POST /chat` |
| **Restaurants** | `POST /restaurants/search` · `GET /restaurants/{id}` · `GET /restaurants/{id}/menu` · `POST /restaurants/dishes/search` |
| **Travel** | `POST /travel/flights/search` · `POST /travel/hotels/search` · `POST /travel/itinerary` |
| **Shopping** | `POST /shopping/search` |
| **Voice** | `POST /voice/stt` · `POST /voice/tts` · `POST /voice/order` · `GET /voice/voices` |
| **Auth** | `register` · `login` · `refresh` · `logout` · `me` · `profile` · `demo` |
| **Health** | `GET /health` (+ per-subsystem checks) |

---

<p align="center"><em>See what to eat, where to go, and what to buy — before you decide.</em></p>
<p align="center">LangChain · LangGraph · Azure OpenAI · Gemini · SerpApi · Neo4j · ChromaDB · ElevenLabs · FastAPI · React</p>
