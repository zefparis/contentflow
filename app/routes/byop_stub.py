from fastapi import APIRouter

router = APIRouter(tags=["byop"])

@router.get("/api/byop/config")
async def get_byop_config():
    return {
        "platforms": ["youtube", "pinterest", "reddit", "instagram"]
    }

@router.get("/api/byop/submissions")
async def get_byop_submissions():
    return []
