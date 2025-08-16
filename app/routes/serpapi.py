"""SerpAPI routes for content discovery."""

import json
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Dict, Any

from app.db import get_db
from app.models import Source
from app.providers import serpapi_provider as serp
from app.services.sources import ingest_dispatch_serp
from app.utils.logger import logger

router = APIRouter(prefix="/serpapi", tags=["serpapi"])


class SerpSourceCreate(BaseModel):
    kind: str  # serp_youtube, serp_news, serp_trends
    url: str  # query string
    params: Optional[Dict[str, Any]] = {}
    enabled: bool = True


@router.post("/search/youtube")
def search_youtube(query: str, max_results: int = 10):
    """Search YouTube videos via SerpAPI."""
    try:
        results = serp.youtube_search(query, max_results=max_results)
        return {"query": query, "results": results}
    except Exception as e:
        logger.error(f"YouTube search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search/news")
def search_news(query: str, max_results: int = 10):
    """Search Google News via SerpAPI."""
    try:
        results = serp.google_news(query, max_results=max_results)
        return {"query": query, "results": results}
    except Exception as e:
        logger.error(f"News search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trends/now")
def trends_now(category_id: Optional[int] = None):
    """Get trending topics from Google Trends via SerpAPI."""
    try:
        results = serp.trends_trending_now(category_id=category_id)
        return {"category_id": category_id, "trends": results}
    except Exception as e:
        logger.error(f"Trends search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sources")
def create_serp_source(source: SerpSourceCreate, db: Session = Depends(get_db)):
    """Create a new SerpAPI source."""
    try:
        if source.kind not in ["serp_youtube", "serp_news", "serp_trends"]:
            raise HTTPException(status_code=400, detail="Invalid kind")
        
        new_source = Source(
            kind=source.kind,
            url=source.url,
            params_json=json.dumps(source.params),
            enabled=source.enabled,
            language="fr"
        )
        
        db.add(new_source)
        db.commit()
        db.refresh(new_source)
        
        return {"message": "Source created", "source_id": new_source.id}
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating SerpAPI source: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ingest/{source_id}")
def trigger_serp_ingest(source_id: int, db: Session = Depends(get_db)):
    """Trigger SerpAPI ingestion for a specific source."""
    try:
        source = db.query(Source).filter(Source.id == source_id).first()
        if source is None:
            raise HTTPException(status_code=404, detail="Source not found")
        
        if not source.kind.startswith("serp_"):
            raise HTTPException(status_code=400, detail="Not a SerpAPI source")
        
        count = ingest_dispatch_serp(db, source)
        return {"message": f"Ingested {count} items", "source_id": source_id}
        
    except Exception as e:
        logger.error(f"Error triggering SerpAPI ingest: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
def serpapi_status():
    """Check SerpAPI provider status."""
    try:
        from app.providers.serpapi_provider import _enabled
        from app.config import settings
        
        return {
            "enabled": _enabled(),
            "api_key_configured": bool(settings.SERPAPI_KEY),
            "config": {
                "hl": settings.SERPAPI_HL,
                "gl": settings.SERPAPI_GL,
                "cache_ttl": settings.SERPAPI_CACHE_TTL,
                "max_results": settings.SERPAPI_MAX_RESULTS
            }
        }
    except Exception as e:
        logger.error(f"Error checking SerpAPI status: {e}")
        raise HTTPException(status_code=500, detail=str(e))