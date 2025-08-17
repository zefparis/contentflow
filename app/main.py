# app/main.py
from __future__ import annotations

import os
import asyncio
import logging
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from typing import Optional, Dict, Any

# Internal imports
from app.config import settings
from app.db import init_db
from app.aiops.autopilot import ai_tick
from app.routes import (
    ui,
    sources,
    assets,
    posts,
    jobs,
    reports,
    auth,
    posts,
    sources,
    assets,
    jobs,
    payments,
    partner_auth,
    byop,
    stubs,
    byop_stub
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS if hasattr(settings, 'CORS_ORIGINS') else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount built frontend if available (served as root)
frontend_dir_candidates = [
    "app/static",
    "client/dist/public",
    "dist/public",
    "dist",
    "public",
]
_static_root_mounted = False
for d in frontend_dir_candidates:
    if os.path.exists(d):
        # Serve SPA with index.html
        app.mount("/", StaticFiles(directory=d, html=True), name="static-root")
        _static_root_mounted = True
        logger.info(f"Mounted frontend static root at '{d}'")
        break

# Add SPA fallback middleware
class SPAFallbackMiddleware:
    def __init__(self, app):
        self.app = app
        self.static_dirs = [
            Path("app/static"),
            Path("client/dist/public"),
            Path("dist/public"),
            Path("dist"),
            Path("public"),
        ]
        self.excluded_prefixes = [
            "/api",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/static",
            "/assets"
        ]
        self.candidates = [Path(d) for d in self.static_dirs if Path(d).exists()]

    async def __call__(self, scope, receive, send):
        assert scope['type'] == 'http'
        request = Request(scope, receive)
        
        # Skip middleware for excluded paths
        if any(request.url.path.startswith(prefix) for prefix in self.excluded_prefixes):
            return await self.app(scope, receive, send)
        
        # Try to serve the requested file first
        try:
            response = await self.app(scope, receive, send)
            # If 404 and not an API request, try to serve index.html
            if hasattr(response, "status_code") and response.status_code == 404:
                path = request.url.path.lstrip('/')
                for candidate in self.candidates:
                    file_path = candidate / path
                    
                    # If it's a directory, try index.html
                    if file_path.is_dir() and (file_path / "index.html").exists():
                        return FileResponse(file_path / "index.html")
                    # If it's a file, serve it
                    elif file_path.is_file():
                        return FileResponse(file_path)
                    
                    # If we're at the root, try index.html
                    if not path and (candidate / "index.html").exists():
                        return FileResponse(candidate / "index.html")
            
            return response
        except Exception as e:
            # If any error occurs, try to serve index.html as a last resort
            for candidate in self.candidates:
                index_path = candidate / "index.html"
                if index_path.exists():
                    return FileResponse(index_path)
            raise  # Re-raise if no index.html is found

app.add_middleware(SPAFallbackMiddleware)

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
_mounted = False
try:
    from app.routes import ui, sources, assets, posts, jobs, reports
    _include(ui.router)
    _include(sources.router, prefix="/api")
    _include(assets.router,  prefix="/api")
    _include(posts.router,   prefix="/api")
    _include(jobs.router,    prefix="/api")
    _include(reports.router, prefix="/api")
    logger.info("Core routers mounted.")
    _mounted = True
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
        _mounted = True
    except Exception as e:
        logger.warning(f"Skip {mod}: {e}")

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
