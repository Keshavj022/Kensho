# Kensho — backend

The API and AI brains of Kensho. A FastAPI app where a LangGraph **supervisor** routes
each request to one of three specialist agents — **restaurant**, **travel**, **shopping** —
which call real tools (Maps, Flights, Hotels, Shopping, web search, menus) and answer in
natural language, personalized to the diner.

> For the product overview and architecture, see the [main README](../README.md). For
> hosting, see [`../docs/DEPLOY_HUGGINGFACE.md`](../docs/DEPLOY_HUGGINGFACE.md).

## Stack

- **FastAPI** (async) · **Pydantic v2** · **SQLAlchemy** · **loguru** · Python 3.11+
- **LangChain 1.x** · **LangGraph** · `langgraph-supervisor` · `create_agent` ReAct agents
- **LLM / vision:** Azure OpenAI · Google Gemini · local Ollama — provider-abstracted with automatic fallback
- **Tools:** SerpApi (maps · flights · hotels · shopping · photos) · Tavily web search
- **Data:** Neo4j (knowledge graph) · ChromaDB (dish embeddings) · SQLite / Postgres
- **Voice:** ElevenLabs (STT + TTS) · `faster-whisper` offline fallback

## Run it

From the **repo root** (the package is imported as `backend.main:app`):

```bash
python3 -m venv .venv
.venv/bin/pip install -r backend/requirements.txt

cp .env.example .env          # add the keys you have — all optional

.venv/bin/python -m uvicorn backend.main:app --reload --port 8000
```

- Interactive API docs → `http://localhost:8000/docs`
- Health → `http://localhost:8000/health`

Every external integration is optional: a missing key disables only its tool, and the app
still boots and serves every other route.

## Tests

```bash
.venv/bin/python -m pytest backend/tests -q   # external APIs mocked; no keys required
```

## Configuration

All settings are environment-driven (`pydantic-settings`); see [`config/settings.py`](config/settings.py)
and copy the repo-root [`.env.example`](../.env.example). The LLM provider is chosen
automatically — Azure OpenAI if configured, else Gemini, else Ollama.

## Structure

```
backend/
├── main.py            # FastAPI app + lifespan
├── config/            # settings (all env vars)
├── agents/            # supervisor + restaurant / travel / shopping specialists
├── tools/             # @tool backbone (places, serpapi, search, kg, rag, menu)
├── services/          # llm, ocr, menu, voice, order, auth, user, knowledge_graph, recommend…
├── models/            # Pydantic v2 schemas
├── api/               # route handlers
├── db/                # SQLAlchemy engine + ORM
└── tests/             # pytest
```
