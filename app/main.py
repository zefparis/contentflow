# app/main.py
from __future__ import annotations

import os
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.db import init_db
from app.utils.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- startup ---
    logger.info("Booting ContentFlow…")
    try:
        await init_db()
        logger.info("DB init OK")
    except Exception as e:
        logger.exception(f"DB init failed: {e}")
    yield
    # --- shutdown ---
    logger.info("ContentFlow shutdown complete.")


app = FastAPI(
    title="ContentFlow",
    description="Automated Content Pipeline",
    version="1.0.0",
    lifespan=lifespan,
)

# ---------- Health (Railway healthcheck) ----------
@app.get("/healthz", include_in_schema=False)
@app.head("/healthz", include_in_schema=False)
async def _healthz():
    return {"ok": True}

@app.get("/health", include_in_schema=False)
async def _health():
    return {"ok": True}

# ---------- Legacy path rewrite middleware ----------
@app.middleware("http")
async def _rewrite_legacy_paths(request, call_next):
    """Rewrite older frontend paths to current API structure.
    - /partners/api/* => /api/*
    - /api/ai/orchestrator/* => /api/ai/*
    """
    path = request.url.path
    if path.startswith("/partners/api/"):
        request.scope["path"] = path.replace("/partners/api", "/api", 1)
    elif path.startswith("/api/ai/orchestrator/"):
        request.scope["path"] = path.replace("/api/ai/orchestrator", "/api/ai", 1)
    return await call_next(request)

# ---------- Feature flags debug ----------
@app.get("/__feature_flags", include_in_schema=False)
def _feature_flags():
    return {
        "FEATURE_BYOP": getattr(settings, "FEATURE_BYOP", False),
        "FEATURE_BYOP_PUBLISH": getattr(settings, "FEATURE_BYOP_PUBLISH", False),
        "BYOP_PUBLISH_PLATFORMS": getattr(settings, "BYOP_PUBLISH_PLATFORMS", ""),
        "PUBLIC_BASE_URL": getattr(settings, "PUBLIC_BASE_URL", ""),
    }

# ---------- Core routers (safe include) ----------
def _include(router, prefix: str | None = None, tags: list[str] | None = None):
    try:
        if prefix or tags:
            app.include_router(router, prefix=prefix or "", tags=tags)
        else:
            app.include_router(router)
    except Exception as e:
        logger.warning(f"Router include failed: {e}")

# Core
try:
    from app.routes import ui, sources, assets, posts, jobs, reports
    _include(ui.router)
    _include(sources.router, prefix="/api")
    _include(assets.router,  prefix="/api")
    _include(posts.router,   prefix="/api")
    _include(jobs.router,    prefix="/api")
    _include(reports.router, prefix="/api")
    logger.info("Core routers mounted.")
except Exception as e:
    logger.exception(f"Core routers load error: {e}")

# Extended (mount ce qui existe, ne crashe rien)
for mod, opts in [
    ("app.routes.metrics",            {"prefix": "/api", "tags": ["metrics"]}),
    ("app.routes.publish",            {"prefix": "/api", "tags": ["publish"]}),
    ("app.routes.compliance",         {"prefix": "/api", "tags": ["compliance"]}),
    ("app.routes.ai",                 {"prefix": "/api", "tags": ["ai"]}),
    ("app.routes.serpapi",            {"prefix": "/api", "tags": ["serpapi"]}),
    ("app.routes.management",         {}),
    ("app.routes.admin_monitor",      {}),
    ("app.routes.assignment_routes",  {}),
    ("app.routes.partnership_routes", {}),
    ("app.routes.byop_routes",        {}),
    ("app.routes.byop_publish",       {}),
    # API/Providers
    ("app.api.contentflow_routes",    {}),
    ("app.api.supadata_routes",       {"prefix": "/api"}),
    ("app.api.brevo_routes",          {"prefix": "/api"}),
    ("app.routes.ig_oauth",           {"prefix": "/api"}),
    ("app.routes.ig_publish",         {"prefix": "/api"}),
    ("app.routes.ai_orchestrator",    {"prefix": "/api"}),
    ("app.routes.partners_ui",        {}),
    ("app.routes.partner_auth",       {}),
    ("app.routes.partners_admin",     {}),
    ("app.routes.compat",             {}),
]:
    try:
        modobj = __import__(mod, fromlist=["router"])
        _include(modobj.router, **opts)
        logger.info(f"Mounted {mod}")
    except Exception as e:
        logger.warning(f"Skip {mod}: {e}")

# ---------- Static & SPA (après les routes API) ----------
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pathlib import Path
import logging

ROOT = Path(__file__).resolve().parents[1]
STATIC_DIR = ROOT / "app" / "static"

# On tente dans cet ordre : client/dist (Vite client), dist/public (build root), dist (fallback)
CANDIDATES = [
    ROOT / "client" / "dist",
    ROOT / "dist" / "public",
    ROOT / "dist",
]

log = logging.getLogger("uvicorn")

if STATIC_DIR.is_dir():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

_mounted = False
for p in CANDIDATES:
    if p.is_dir():
        app.mount("/", StaticFiles(directory=str(p), html=True), name="spa")
        log.info(f"[STATIC] Serving SPA from {p}")
        _mounted = True
        break

@app.get("/__static_debug", include_in_schema=False)
def _static_debug():
    return {
        "root": str(ROOT),
        "static_dir": str(STATIC_DIR),
        "candidates": {str(p): p.is_dir() for p in CANDIDATES},
        "mounted": _mounted,
    }

if not _mounted:
    @app.get("/", include_in_schema=False)
    async def _root():
        return HTMLResponse(
            "<!doctype html><meta charset='utf-8'>"
            "<title>ContentFlow API</title>"
            "<h1>ContentFlow API</h1>"
            "<ul><li><a href='/healthz'>/healthz</a></li>"
            "<li><a href='/docs'>/docs</a></li>"
            "<li><a href='/__static_debug'>/__static_debug</a></li></ul>"
        )

# ---------- Local runner ----------
if __name__ == "__main__":
    # Utilisé seulement en local; en prod Railway lance via Procfile/Start Command.
    import uvicorn
    port = int(os.getenv("PORT", getattr(settings, "PORT", 8080)))
    is_dev = os.getenv("RELOAD", "0") == "1" or os.getenv("ENV", "").lower() in {"dev", "development", "local"}
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=is_dev)
