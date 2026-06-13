# Deploying Kensho (Hugging Face Spaces + Supabase)

One Docker image runs the FastAPI backend and serves the React SPA on the same
origin. State lives in Supabase: Postgres for the relational data **and** the
vector index (pgvector) **and** the LangGraph conversation memory — so the Space
itself is stateless and runs on the free tier.

## 1. Supabase (database + vectors)

1. Create a project at [supabase.com](https://supabase.com).
2. In the SQL editor, enable pgvector:
   ```sql
   create extension if not exists vector;
   ```
   (The app also creates it on first run, but enabling it up front avoids a
   permissions surprise.)
3. Copy the connection string (Project Settings → Database → Connection string →
   URI). Use the **session pooler** URI for serverless-friendly connections, e.g.
   `postgresql://postgres.xxxx:[PASSWORD]@aws-0-...pooler.supabase.com:5432/postgres`.

`DATABASE_URL` being a `postgres://` URL is the only switch needed — the app then
uses Postgres for tables, pgvector for dish search, and a Postgres checkpointer for
chat memory automatically.

## 2. Hugging Face Space

1. Create a new **Space** → SDK: **Docker** → blank.
2. Push this repo to the Space (or connect the GitHub repo). The `Dockerfile` at
   the root builds the SPA and runs the backend on port 7860.
3. The Space's `README.md` must start with the frontmatter in
   `deploy/huggingface-space-README.md` (`sdk: docker`, `app_port: 7860`).

## 3. Secrets (Space → Settings → Secrets)

Set these as Space secrets (never commit them):

```
DATABASE_URL=postgresql://...        # Supabase pooler URI
EMBEDDING_DIM=1536                   # 1536 for Azure text-embedding-3-small

JWT_SECRET_KEY=<long random string>  # generate: openssl rand -hex 32

AZURE_OPENAI_ENDPOINT=https://<resource>.openai.azure.com/
AZURE_OPENAI_API_KEY=...
AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini          # vision-capable, for chat + menu OCR
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-3-small

SERPAPI_API_KEY=...
TAVILY_API_KEY=...
ELEVENLABS_API_KEY=...

NEO4J_URI=neo4j+s://<id>.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=...

CORS_ORIGINS=https://<user>-<space>.hf.space
```

Everything except `DATABASE_URL` and `JWT_SECRET_KEY` is optional — missing keys
just disable that feature; the app still boots.

## 4. First run

- The Space builds, then boots. Health: `https://<user>-<space>.hf.space/health`.
- Open a few restaurants so menus extract, or call
  `POST /api/v1/azure/reindex-embeddings` to backfill dish search from cached menus.
- The free Space sleeps after ~48h idle and cold-starts on the next request.

## Other hosts

The same image runs on Render / Fly.io / Railway — they set `$PORT`, which the
container honours (falls back to 7860). Point `DATABASE_URL` at the same Supabase
project. For a fully managed split, host the SPA separately and set
`VITE_API_BASE_URL` at build time, with `CORS_ORIGINS` set to the SPA's URL.
