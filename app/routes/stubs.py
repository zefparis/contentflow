from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(tags=["stubs"])

@router.get("/api/assets")
async def get_assets():
    return []

@router.get("/api/posts")
async def get_posts():
    return []

@router.get("/api/sources")
async def get_sources():
    return []

@router.get("/api/jobs")
def list_jobs():
    # Stub vide pour satisfaire frontend
    return []

@router.get("/api/jobs/status")
async def get_jobs_status():
    return {"status": "ok", "running": 0}

@router.get("/api/payments/calculate")
async def calculate_payment():
    return {"amount": 0}
