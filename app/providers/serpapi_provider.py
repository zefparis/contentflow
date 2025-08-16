"""SerpAPI provider for content discovery and trends monitoring."""

import time
import os
from typing import Any, Dict, List, Optional
from functools import lru_cache

try:
    from serpapi import GoogleSearch
    SERPAPI_AVAILABLE = True
except ImportError:
    SERPAPI_AVAILABLE = False
    GoogleSearch = None

from app.config import settings


def _enabled() -> bool:
    """Check if SerpAPI is enabled and available."""
    return bool(settings.SERPAPI_KEY) and SERPAPI_AVAILABLE


def _run(engine: str, **kw) -> Dict[str, Any]:
    """Execute SerpAPI query with fallback."""
    if not _enabled():
        return {}
    
    try:
        params = {
            "engine": engine,
            "api_key": settings.SERPAPI_KEY,
            "hl": settings.SERPAPI_HL,
            "gl": settings.SERPAPI_GL,
        }
        params.update({k: v for k, v in kw.items() if v is not None})
        return GoogleSearch(params).get_dict()
    except Exception as e:
        print(f"SerpAPI error: {e}")
        return {}


# Cache for reducing API calls and costs
def _cache_key(engine: str, **kw) -> str:
    """Generate cache key for query."""
    return engine + "|" + "|".join(f"{k}={kw[k]}" for k in sorted(kw))


_cache: Dict[str, tuple[float, Dict[str, Any]]] = {}


def _cached(engine: str, ttl: int, **kw) -> Dict[str, Any]:
    """Execute cached SerpAPI query."""
    key = _cache_key(engine, **kw)
    now = time.time()
    
    # Check cache
    if key in _cache:
        ts, data = _cache[key]
        if now - ts < ttl:
            return data
    
    # Execute and cache
    data = _run(engine, **kw)
    _cache[key] = (now, data)
    return data


# High-level API functions
def youtube_search(q: str, max_results: int = None) -> List[Dict[str, Any]]:
    """Search YouTube videos via SerpAPI."""
    max_results = max_results or settings.SERPAPI_MAX_RESULTS
    d = _cached("youtube", settings.SERPAPI_CACHE_TTL, search_query=q)
    res = d.get("video_results") or d.get("items") or []
    return res[:max_results]


def youtube_video(video_id: str) -> Dict[str, Any]:
    """Get YouTube video details via SerpAPI."""
    return _cached("youtube_video", settings.SERPAPI_CACHE_TTL, v=video_id)


def google_news(q: str, max_results: int = None) -> List[Dict[str, Any]]:
    """Search Google News via SerpAPI."""
    max_results = max_results or settings.SERPAPI_MAX_RESULTS
    d = _cached("google_news", settings.SERPAPI_CACHE_TTL, q=q)
    return (d.get("news_results") or [])[:max_results]


def trends_trending_now(category_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """Get trending topics from Google Trends via SerpAPI."""
    kw = {}
    if category_id is not None:
        kw["category_id"] = category_id
    d = _cached("google_trends_trending_now", settings.SERPAPI_CACHE_TTL, **kw)
    return d.get("stories") or []