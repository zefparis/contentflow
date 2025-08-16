from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import Source

router = APIRouter()


@router.get("/sources")
async def list_sources(db: Session = Depends(get_db)):
    """List all content sources"""
    sources = db.query(Source).all()
    return [
        {
            "id": source.id,
            "kind": source.kind,
            "url": source.url,
            "enabled": source.enabled,
            "created_at": source.created_at.isoformat()
        }
        for source in sources
    ]
