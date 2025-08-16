"""
ContentFlow Configuration API Routes
Provides endpoints to manage niche configurations and content generation
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
import logging

from app.services.contentflow_config import get_config, reload_config

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/contentflow", tags=["contentflow"])

@router.get("/niches")
async def get_available_niches():
    """Get all available content niches"""
    try:
        config = get_config()
        niches = config.get_niches()
        
        return {
            "success": True,
            "niches": niches,
            "total": len(niches)
        }
    except Exception as e:
        logger.error(f"Failed to get niches: {e}")
        return {
            "success": False,
            "error": str(e),
            "niches": []
        }

@router.get("/niches/{niche}")
async def get_niche_details(niche: str):
    """Get detailed configuration for a specific niche"""
    try:
        config = get_config()
        niche_config = config.get_niche_config(niche)
        
        if not niche_config:
            raise HTTPException(status_code=404, detail=f"Niche '{niche}' not found")
        
        return {
            "success": True,
            "niche": niche,
            "config": niche_config,
            "stats": {
                "hooks_count": len(niche_config.get("hooks", [])),
                "titles_count": len(niche_config.get("titles", [])),
                "hashtags_count": len(niche_config.get("hashtags", [])),
                "ctas_count": len(niche_config.get("ctas", []))
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get niche details for {niche}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate")
async def generate_optimized_content(
    niche: str = Query(..., description="Target niche"),
    platform: str = Query(..., description="Target platform"),
    count: int = Query(default=1, ge=1, le=10, description="Number of variants to generate")
):
    """Generate optimized content for a specific niche and platform"""
    try:
        config = get_config()
        
        # Validate niche exists
        if niche not in config.get_niches():
            raise HTTPException(status_code=404, detail=f"Niche '{niche}' not found")
        
        # Generate content variants
        variants = []
        for i in range(count):
            content = config.generate_optimized_content(niche, platform)
            variants.append(content)
        
        return {
            "success": True,
            "niche": niche,
            "platform": platform,
            "variants": variants,
            "count": len(variants)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate content for {niche}/{platform}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/serpapi/queries/{niche}")
async def get_serpapi_queries(niche: str):
    """Get SerpAPI queries for a specific niche"""
    try:
        config = get_config()
        
        if niche not in config.get_niches():
            raise HTTPException(status_code=404, detail=f"Niche '{niche}' not found")
        
        queries = config.get_serpapi_queries(niche)
        
        return {
            "success": True,
            "niche": niche,
            "queries": queries,
            "youtube_count": len(queries.get("youtube_queries", [])),
            "news_count": len(queries.get("news_queries", []))
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get SerpAPI queries for {niche}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics")
async def get_niche_metrics():
    """Get analytics and metrics about available niches"""
    try:
        config = get_config()
        metrics = config.get_niche_metrics()
        
        return {
            "success": True,
            "metrics": metrics
        }
        
    except Exception as e:
        logger.error(f"Failed to get niche metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/ffmpeg/{format_type}")
async def get_ffmpeg_recipe(format_type: str = "shorts_9_16"):
    """Get FFmpeg configuration for video processing"""
    try:
        config = get_config()
        recipe = config.get_ffmpeg_recipe(format_type)
        
        if not recipe:
            raise HTTPException(status_code=404, detail=f"FFmpeg recipe '{format_type}' not found")
        
        return {
            "success": True,
            "format_type": format_type,
            "recipe": recipe
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get FFmpeg recipe for {format_type}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/scheduler/{platform}")
async def get_posting_windows(platform: str):
    """Get optimal posting time windows for a platform"""
    try:
        config = get_config()
        windows = config.get_scheduler_windows(platform)
        
        return {
            "success": True,
            "platform": platform,
            "posting_windows": windows,
            "timezone": config.config.get("timezone", "UTC")
        }
        
    except Exception as e:
        logger.error(f"Failed to get posting windows for {platform}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/bandit/arms")
async def get_bandit_configuration():
    """Get multi-armed bandit configuration for A/B testing"""
    try:
        config = get_config()
        arms = config.get_bandit_arms()
        
        return {
            "success": True,
            "bandit_arms": arms,
            "total_arms": len(arms)
        }
        
    except Exception as e:
        logger.error(f"Failed to get bandit configuration: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reload")
async def reload_configuration():
    """Reload ContentFlow configuration from file"""
    try:
        success = reload_config()
        
        if success:
            config = get_config()
            return {
                "success": True,
                "message": "Configuration reloaded successfully",
                "version": config.config.get("version", "unknown"),
                "niches_count": len(config.get_niches())
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to reload configuration")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to reload configuration: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/policies")
async def get_planner_policies():
    """Get content planning policies and constraints"""
    try:
        config = get_config()
        policies = config.get_planner_policies()
        
        return {
            "success": True,
            "policies": policies
        }
        
    except Exception as e:
        logger.error(f"Failed to get planner policies: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/validate/keyword")
async def validate_keyword(keyword: str = Query(..., description="Keyword to validate")):
    """Check if a keyword is allowed (not in denylist)"""
    try:
        config = get_config()
        is_denied = config.is_keyword_denied(keyword)
        
        return {
            "success": True,
            "keyword": keyword,
            "is_allowed": not is_denied,
            "is_denied": is_denied
        }
        
    except Exception as e:
        logger.error(f"Failed to validate keyword '{keyword}': {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/test/{niche}")
async def test_niche_content_generation(niche: str):
    """Test content generation for all platforms in a niche"""
    try:
        config = get_config()
        
        if niche not in config.get_niches():
            raise HTTPException(status_code=404, detail=f"Niche '{niche}' not found")
        
        platforms = ["youtube", "tiktok", "instagram", "reddit", "pinterest"]
        results = {}
        
        for platform in platforms:
            try:
                content = config.generate_optimized_content(niche, platform)
                results[platform] = {
                    "success": True,
                    "content": content
                }
            except Exception as e:
                results[platform] = {
                    "success": False,
                    "error": str(e)
                }
        
        return {
            "success": True,
            "niche": niche,
            "test_results": results,
            "platforms_tested": len(platforms)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to test niche content generation for {niche}: {e}")
        raise HTTPException(status_code=500, detail=str(e))