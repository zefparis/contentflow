from __future__ import annotations

import os
import asyncio
import logging
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request as StarletteRequest
from starlette.responses import Response

# Internal imports
from app.config import settings
from app.db import init_db
from app.aiops.autopilot import ai_tick

# ------------------ Logging ------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("contentflow")

# ------------------ Lifespan ------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Booting ContentFlow…")

    # Init DB
    try:
        await init_db()
        logger.info("✅ DB init OK")
    except Exception as e:
        logger.exception(f"❌ DB init failed: {e}")

    # Autopilot scheduler
    app.state.autopilot_task = None
    try:
        if getattr(settings, "FEATURE_AUTOPILOT", False):
            interval_sec = max(60, int(settings.AI_TICK_INTERVAL_MIN) * 60)
            logger.info(f"▶️ Starting Autopilot every {interval_sec}s")

            async def _autopilot_loop():
                while True:
                    try:
                        res: dict[str, Any] = ai_tick(dry_run=settings.AI_DRY_RUN)
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
            logger.info("⚠️ Autopilot disabled (FEATURE_AUTOPILOT=False)")
    except Exception as e:
        logger.warning(f"Failed to start Autopilot scheduler: {e}")

    yield

    logger.info("🛑 Shutting down ContentFlow…")
    task = getattr(app.state, "autopilot_task", None)
    if task:
        task.cancel()
        try:
            await task
        except Exception:
            pass

# ------------------ App ------------------
app = FastAPI(
    title="ContentFlow",
    description="Automated Content Pipeline",
    version="1.0.0",
    lifespan=lifespan,
)

# ------------------ Health Endpoints (define early) ------------------
@app.get("/healthz", include_in_schema=False)
@app.head("/healthz", include_in_schema=False)
async def healthz():
    return {"ok": True}

@app.get("/health", include_in_schema=False)
async def health():
    return {"ok": True}

# ------------------ Middleware ------------------
# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=getattr(settings, "CORS_ORIGINS", ["*"]),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# SPA Fallback Middleware
class SPAFallbackMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.excluded_prefixes = [
            "/api", "/docs", "/redoc", "/openapi.json",
            "/static", "/assets", "/health", "/healthz", "/__feature_flags",
        ]
        candidates = [
            Path("app/static"),
            Path("client/dist/public"),
            Path("dist/public"),
            Path("dist"),
            Path("public"),
        ]
        self.candidates = [p for p in candidates if p.exists()]

    async def dispatch(self, request, call_next):
        path = request.url.path
        # Allow API and known prefixes
        if any(path.startswith(p) for p in self.excluded_prefixes):
            return await call_next(request)

        # Let the app respond first
        response = await call_next(request)
        if response.status_code != 404:
            return response

        # On 404, try static file by path
        rel = path.lstrip("/")
        for root in self.candidates:
            fp = root / rel
            if fp.is_file():
                return FileResponse(fp)

        # Fallback to SPA index.html
        for root in self.candidates:
            index = root / "index.html"
            if index.exists():
                return FileResponse(index)

        # If nothing found, return original 404
        return response

class LegacyRewriteMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: StarletteRequest, call_next):
        # Only handle HTTP (not websockets)
        if request.scope.get("type") != "http":
            return await call_next(request)

        path = request.url.path
        # legacy -> new routes
        if path.startswith("/partners/api/"):
            request.scope["path"] = path.replace("/partners/api", "/api", 1)
        elif path.startswith("/api/ai/orchestrator/"):
            request.scope["path"] = path.replace("/api/ai/orchestrator", "/api/ai", 1)

        # propagate and guarantee a Response
        resp = await call_next(request)
        if resp is None:
            return Response(status_code=404)
        return resp

# Order matters: legacy rewrite first, then SPA fallback
app.add_middleware(LegacyRewriteMiddleware)
app.add_middleware(SPAFallbackMiddleware)

# ------------------ Static Frontend (mount last) ------------------
for d in ["app/static", "client/dist/public", "dist/public", "dist", "public"]:
    if os.path.exists(d):
        app.mount("/", StaticFiles(directory=d, html=True), name="frontend")
        logger.info(f"📦 Mounted frontend from {d}")
        break

# ------------------ Legacy Rewrite (replaced by middleware class above) ------------------

# ------------------ Feature Flags Debug ------------------
@app.get("/__feature_flags", include_in_schema=False)
def feature_flags():
    return {
        "FEATURE_BYOP": settings.FEATURE_BYOP,
        "FEATURE_BYOP_PUBLISH": settings.FEATURE_BYOP_PUBLISH,
        "BYOP_PUBLISH_PLATFORMS": settings.BYOP_PUBLISH_PLATFORMS,
        "PUBLIC_BASE_URL": settings.PUBLIC_BASE_URL,
    }

# ------------------ Router Helper ------------------
def _include(module: str, **opts):
    try:
        mod = __import__(module, fromlist=["router"])
        app.include_router(mod.router, **opts)
        logger.info(f"✅ Mounted {module} {opts}")
    except Exception as e:
        logger.warning(f"⚠️ Skip {module}: {e}")

# Core Routers
for mod, opts in [
    ("app.routes.ui", {}),
    ("app.routes.sources", {"prefix": "/api"}),
    ("app.routes.assets", {"prefix": "/api"}),
    ("app.routes.posts", {"prefix": "/api"}),
    ("app.routes.jobs", {"prefix": "/api"}),
    ("app.routes.reports", {"prefix": "/api"}),
]:
    _include(mod, **opts)

# Extended Routers
for mod, opts in [
    ("app.routes.metrics", {"prefix": "/api", "tags": ["metrics"]}),
    ("app.routes.publish", {"prefix": "/api", "tags": ["publish"]}),
    ("app.routes.compliance", {"prefix": "/api", "tags": ["compliance"]}),
    ("app.routes.ai", {"prefix": "/api", "tags": ["ai"]}),
    ("app.routes.serpapi", {"prefix": "/api", "tags": ["serpapi"]}),
    ("app.routes.partner_auth", {"prefix": "/api/partner", "tags": ["partner_auth"]}),
    ("app.routes.byop_routes", {"prefix": "/api"}),
    ("app.routes.byop_publish", {"prefix": "/api"}),
    ("app.routes.ig_oauth", {"prefix": "/api"}),
    ("app.routes.ig_publish", {"prefix": "/api"}),
    ("app.routes.ai_orchestrator", {"prefix": "/api"}),
    ("app.api.supadata_routes", {"prefix": "/api"}),
    ("app.api.brevo_routes", {"prefix": "/api"}),
    # Stubs
    ("app.routes.stubs", {"prefix": "", "tags": ["stubs"]}),
    ("app.routes.byop_stub", {"prefix": "", "tags": ["byop"]}),
]:
    _include(mod, **opts)

# ------------------ Root fallback ------------------
@app.get("/", include_in_schema=False)
async def root():
    return HTMLResponse(
        "<!doctype html><meta charset='utf-8'>"
        "<title>ContentFlow API</title>"
        "<h1>ContentFlow API</h1>"
        "<ul><li><a href='/healthz'>/healthz</a></li>"
        "<li><a href='/docs'>/docs</a></li></ul>"
    )

# ------------------ Local Runner ------------------
if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", getattr(settings, "PORT", 8080)))
    reload = os.getenv("RELOAD", "0") == "1" or os.getenv("ENV", "").lower() in {"dev", "development", "local"}
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=reload)
