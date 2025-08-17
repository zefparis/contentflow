# ---------- Stage 1: Build Frontend ----------
FROM node:18-bullseye AS frontend
WORKDIR /app

COPY package.json package-lock.json* vite.config.ts ./
COPY client ./client
COPY shared ./shared
COPY attached_assets ./attached_assets

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

# Copy frontend build → static dir
RUN mkdir -p app/static
COPY --from=frontend /app/dist/public/ ./app/static/

# Expose default port
ENV PORT=8000
EXPOSE 8000

# Healthcheck (shell for expansion OK)
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD sh -c 'curl -fsS http://localhost:${PORT:-8000}/healthz || exit 1'

# Start via wrapper (guarantees $PORT expansion)
RUN echo "IMAGE_BUILT_FROM_DOCKERFILE=1"
COPY start.sh /usr/local/bin/start.sh
RUN sed -i 's/\r$//' /usr/local/bin/start.sh && chmod +x /usr/local/bin/start.sh
CMD ["sh", "-c", "/usr/local/bin/start.sh"]
