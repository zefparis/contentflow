# app/main.py
from __future__ import annotations

import os
import asyncio
import logging
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.db import init_db
from app.utils.logger import logger
from app.aiops.autopilot import ai_tick


# ---------- Lifespan ----------
@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- startup ---
    logger.info("Booting ContentFlow…")
    try:
        await init_db()
        logger.info("DB init OK")
    except Exception as e:
        logger.exception(f"DB init failed: {e}")

    # Autopilot internal scheduler
    app.state.autopilot_task = None
    try:
        if getattr(settings, "FEATURE_AUTOPILOT", False):
            interval_sec = max(60, int(getattr(settings, "AI_TICK_INTERVAL_MIN", 10)) * 60)
            logger.info(f"Starting internal Autopilot scheduler (every {interval_sec}s) …")

            async def _autopilot_loop():
                while True:
                    try:
                        res = ai_tick(dry_run=getattr(settings, "AI_DRY_RUN", True))
                        status = "ok" if res.get("ok") else f"err:{res.get('reason') or res.get('error')}"
                        logger.info(
                            f"[Autopilot] tick={status} dry={res.get('dry_run')} "
                            f"actions={len(res.get('executed', []))}"
                        )
                        await asyncio.sleep(interval_sec)
                    except Exception as e:
                        logger.warning(f"[Autopilot] loop error: {e}")
                        await asyncio.sleep(60)

            app.state.autopilot_task = asyncio.create_task(_autopilot_loop())
        else:
            logger.info("Autopilot disabled by FEATURE_AUTOPILOT flag; scheduler not started.")
    except Exception as e:
        logger.warning(f"Failed to start internal Autopilot scheduler: {e}")

    yield

    # --- shutdown ---
    logger.info("ContentFlow shutdown complete.")
    task = getattr(app.state, "autopilot_task", None)
    if task:
        task.cancel()
        try:
            await task
        except Exception:
            pass


# ---------- FastAPI App ----------
app = FastAPI(
    title="ContentFlow",
    description="Automated Content Pipeline",
    version="1.0.0",
    lifespan=lifespan,
)


# ---------- Health endpoints ----------
@app.get("/healthz", include_in_schema=False)
@app.head("/healthz", include_in_schema=False)
async def _healthz():
    return {"ok": True}

@app.get("/health", include_in_schema=False)
async def _health():
    return {"ok": True}


# ---------- Legacy path rewrite ----------
@app.middleware("http")
async def _rewrite_legacy_paths(request, call_next):
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


# ---------- Router helper ----------
def _include(router, prefix: str | None = None, tags: list[str] | None = None):
    try:
        if prefix or tags:
            app.include_router(router, prefix=prefix or "", tags=tags)
        else:
            app.include_router(router)
    except Exception as e:
        logger.warning(f"Router include failed: {e}")


# ---------- Core Routers ----------
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


# ---------- Extended Routers ----------
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
    # APIs
    ("app.api.contentflow_routes",    {}),
    ("app.api.supadata_routes",       {"prefix": "/api"}),
    ("app.api.brevo_routes",          {"prefix": "/api"}),
    ("app.routes.ig_oauth",           {"prefix": "/api"}),
    ("app.routes.ig_publish",         {"prefix": "/api"}),
    ("app.routes.ai_orchestrator",    {"prefix": "/api"}),
    ("app.routes.partners_ui",        {}),
    # ✅ Correction: Partner Auth exposé sous /api/partner/*
    ("app.routes.partner_auth",       {"prefix": "/api/partner", "tags": ["partner_auth"]}),
    ("app.routes.partners_admin",     {}),
    ("app.routes.compat",             {}),
    
    # Stub endpoints for frontend compatibility
    ("app.routes.stubs",              {"prefix": "", "tags": ["stubs"]}),
    ("app.routes.byop_stub",          {"prefix": "", "tags": ["byop"]}),
]:
    try:
        modobj = __import__(mod, fromlist=["router"])
        _include(modobj.router, **opts)
        logger.info(f"Mounted {mod} with opts={opts}")
    except Exception as e:
        logger.warning(f"Skip {mod}: {e}")


# ---------- Static & SPA ----------
ROOT = Path(__file__).resolve().parents[1]
STATIC_DIR = ROOT / "app" / "static"

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

@app.middleware("http")
async def spa_fallback(request, call_next):
    response = await call_next(request)
    if response.status_code == 404 and not request.url.path.startswith("/api"):
        # Fallback vers index.html du SPA
        index_path = ROOT / "dist" / "public" / "index.html"
        if index_path.is_file():
            return FileResponse(index_path)
    return response

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
    import uvicorn
    port = int(os.getenv("PORT", getattr(settings, "PORT", 8080)))
    is_dev = os.getenv("RELOAD", "0") == "1" or os.getenv("ENV", "").lower() in {"dev", "development", "local"}
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=is_dev)
