# Kensho — single image: builds the React SPA, then runs the FastAPI backend that
# serves both the API and the SPA on one port. Designed for Hugging Face Spaces
# (Docker SDK, port 7860) but also works on Render/Fly/Railway via $PORT.

# ---- 1. Build the frontend ----
FROM node:20-slim AS frontend
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
# Empty base URL -> the SPA calls the API at the same origin (/api/v1), no CORS.
ENV VITE_API_BASE_URL=""
RUN npm run build

# ---- 2. Python runtime ----
FROM python:3.11-slim AS runtime
WORKDIR /app
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    SERVE_FRONTEND=true

COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY backend/ ./backend/
COPY --from=frontend /app/frontend/dist ./frontend/dist

EXPOSE 7860
# Listen on $PORT when the host sets one (Render/Fly), else 7860 (Hugging Face Spaces).
CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-7860}"]
