# ---- 1. Build the frontend ----
FROM node:20-slim AS frontend
WORKDIR /app/frontend

ENV NODE_ENV=development
COPY frontend/package*.json ./
RUN npm ci --include=dev
COPY frontend/ ./

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

CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-7860}"]
