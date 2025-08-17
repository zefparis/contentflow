# Multi-stage Dockerfile: build frontend, run FastAPI backend

# ---------- Stage 1: Frontend build ----------
FROM node:18-bullseye AS frontend
WORKDIR /app

# Copy only files needed to build the frontend via vite
COPY package.json package-lock.json* vite.config.ts ./
COPY client ./client
COPY shared ./shared
COPY attached_assets ./attached_assets

# Install deps and build only the Vite client
RUN npm ci --no-audit --no-fund \
 && npx vite build --config vite.config.ts

# ---------- Stage 2: Backend ----------
FROM python:3.12-slim AS backend
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
 && rm -rf /var/lib/apt/lists/*

# Python deps
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# App source
COPY app ./app
COPY server ./server
COPY utils ./utils
COPY shared ./shared
COPY app/templates ./app/templates

# Copy built frontend into FastAPI static dir
RUN mkdir -p app/static
COPY --from=frontend /app/dist/public/ ./app/static/

# Default env
ENV PORT=8000
EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD curl -fsS http://localhost:${PORT:-8000}/healthz || exit 1

# Start FastAPI (use shell so ${PORT} is expanded)
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
