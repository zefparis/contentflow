import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn

from app.config import settings
from app.db import init_db
from app.routes import health, ui, sources, assets, posts, jobs, reports
# Additional routes for ContentFlow
try:
    from app.routes import metrics, publish, compliance, ai, serpapi
    EXTENDED_ROUTES = True
except ImportError:
    EXTENDED_ROUTES = False
# from app.services.scheduler import scheduler
from app.utils.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting ContentFlow application...")
    await init_db()
    # scheduler.start()
    logger.info("Application started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    # scheduler.shutdown()
    logger.info("Application shutdown complete")


app = FastAPI(
    title="ContentFlow",
    description="Automated Content Pipeline",
    version="1.0.0",
    lifespan=lifespan
)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Include routers
app.include_router(health.router, prefix="/api")
app.include_router(ui.router)
app.include_router(sources.router, prefix="/api")
app.include_router(assets.router, prefix="/api")
app.include_router(posts.router, prefix="/api")
app.include_router(jobs.router, prefix="/api")
app.include_router(reports.router, prefix="/api")

# Include additional ContentFlow routes if available
if EXTENDED_ROUTES:
    try:
        app.include_router(metrics.router, prefix="/api", tags=["metrics"])
        app.include_router(publish.router, prefix="/api", tags=["publish"]) 
        app.include_router(compliance.router, prefix="/api", tags=["compliance"])
        app.include_router(ai.router, prefix="/api", tags=["ai"])
        app.include_router(serpapi.router, prefix="/api", tags=["serpapi"])
        logger.info("Extended routes loaded successfully")
    except Exception as e:
        logger.warning(f"Some extended routes failed to load: {e}")

# Add new production management routes
try:
    from app.routes import management
    app.include_router(management.router)
    logger.info("Management routes loaded")
except ImportError:
    logger.warning("Management routes not available")

# Add admin monitoring routes
try:
    from app.routes import admin_monitor
    app.include_router(admin_monitor.router)
    logger.info("Admin monitoring routes loaded")
except ImportError:
    logger.warning("Admin monitoring routes not available")

# Add partner-specific routes
try:
    from app.routes import assignment_routes, partnership_routes, byop_routes
    app.include_router(assignment_routes.router)
    app.include_router(partnership_routes.router)  
    app.include_router(byop_routes.router)
    logger.info("Partner routes loaded")
except ImportError:
    logger.warning("Partner routes not available")

# Add BYOP publishing routes
try:
    from app.routes import byop_publish
    app.include_router(byop_publish.router)
    logger.info("BYOP publishing routes loaded")
except ImportError:
    logger.warning("BYOP publishing routes not available")

# Include ContentFlow and Supadata routers
try:
    from app.api.contentflow_routes import router as contentflow_router
    from app.api.supadata_routes import router as supadata_router
    from app.api.brevo_routes import router as brevo_router
    app.include_router(contentflow_router)
    app.include_router(supadata_router, prefix="/api")
    app.include_router(brevo_router, prefix="/api")
    
    # Instagram Graph API routes
    from app.routes.ig_oauth import router as ig_oauth_router
    from app.routes.ig_publish import router as ig_publish_router
    app.include_router(ig_oauth_router, prefix="/api")
    app.include_router(ig_publish_router, prefix="/api")
    
    # AI Orchestrator routes
    from app.routes.ai_orchestrator import router as ai_orchestrator_router
    app.include_router(ai_orchestrator_router, prefix="/api")
    
    # Partner UI routes
    from app.routes.partners_ui import router as partners_ui_router
    from app.routes.partner_auth import router as partner_auth_router
    from app.routes.partners_admin import router as partners_admin_router
    app.include_router(partners_ui_router)
    app.include_router(partner_auth_router)
    app.include_router(partners_admin_router)
    
    logger.info("ContentFlow, Supadata, Brevo, Instagram, AI Orchestrator and Partners system loaded")
except ImportError as e:
    logger.warning(f"ContentFlow/Supadata routes not available: {e}")


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=5000,
        reload=True
    )
