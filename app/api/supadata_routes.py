"""
Routes API pour l'intégration Supadata AI
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import logging

from app.services.supadata_integration import supadata_client, supadata_optimizer
from app.services.contentflow_config import get_config

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/supadata", tags=["supadata"])


class ContentAnalysisRequest(BaseModel):
    title: str
    description: str
    platform: str
    niche: str
    hashtags: List[str] = []
    hook: Optional[str] = None
    cta: Optional[str] = None


class ContentOptimizationRequest(BaseModel):
    content: Dict[str, Any]
    goal: str = "engagement"  # engagement, conversion, reach


class EnhancePackRequest(BaseModel):
    niche: str
    platform: str


@router.post("/analyze/content")
async def analyze_content_performance(request: ContentAnalysisRequest):
    """
    Analyse la performance prédictive d'un contenu avec Supadata AI
    """
    try:
        content_data = {
            "title": request.title,
            "description": request.description,
            "platform": request.platform,
            "niche": request.niche,
            "hashtags": request.hashtags,
            "hook": request.hook,
            "cta": request.cta
        }
        
        result = await supadata_client.analyze_content_performance(content_data)
        
        if result["success"]:
            return {
                "success": True,
                "data": {
                    "performance_score": result["performance_score"],
                    "engagement_prediction": result["engagement_prediction"],
                    "optimization_suggestions": result["optimization_suggestions"],
                    "confidence": result["confidence"],
                    "best_posting_time": result["best_posting_time"],
                    "target_audience": result["target_audience"]
                }
            }
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        logger.error(f"Content analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/optimize/content")
async def optimize_content(request: ContentOptimizationRequest):
    """
    Optimise un contenu avec Supadata AI
    """
    try:
        result = await supadata_client.optimize_content(request.content, request.goal)
        
        if result["success"]:
            return {
                "success": True,
                "data": {
                    "optimized_title": result["optimized_title"],
                    "optimized_description": result["optimized_description"],
                    "optimized_hashtags": result["optimized_hashtags"],
                    "optimized_hook": result["optimized_hook"],
                    "optimized_cta": result["optimized_cta"],
                    "improvement_score": result["improvement_score"],
                    "changes_made": result["changes_made"]
                }
            }
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        logger.error(f"Content optimization error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analyze/audience/{niche}/{platform}")
async def analyze_audience_trends(niche: str, platform: str):
    """
    Analyse les tendances d'audience pour une niche et plateforme
    """
    try:
        result = await supadata_client.analyze_audience_trends(niche, platform)
        
        if result["success"]:
            return {
                "success": True,
                "data": {
                    "trending_topics": result["trending_topics"],
                    "optimal_posting_times": result["optimal_posting_times"],
                    "audience_demographics": result["audience_demographics"],
                    "content_preferences": result["content_preferences"],
                    "competitor_insights": result["competitor_insights"]
                }
            }
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        logger.error(f"Audience analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recommendations/{niche}/{platform}")
async def get_content_recommendations(niche: str, platform: str):
    """
    Obtient des recommandations de contenu basées sur Supadata AI
    """
    try:
        result = await supadata_client.get_content_recommendations(niche, platform)
        
        if result["success"]:
            return {
                "success": True,
                "data": {
                    "recommended_topics": result["recommended_topics"],
                    "recommended_hooks": result["recommended_hooks"],
                    "recommended_ctas": result["recommended_ctas"],
                    "trending_hashtags": result["trending_hashtags"],
                    "content_angles": result["content_angles"]
                }
            }
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        logger.error(f"Content recommendations error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/enhance/pack")
async def enhance_contentflow_pack(request: EnhancePackRequest):
    """
    Améliore le ContentFlow Pack avec Supadata AI
    """
    try:
        result = await supadata_optimizer.enhance_contentflow_pack(request.niche, request.platform)
        
        if result["success"]:
            return {
                "success": True,
                "data": {
                    "enhanced_hooks": result["enhanced_hooks"],
                    "enhanced_ctas": result["enhanced_ctas"],
                    "trending_hashtags": result["trending_hashtags"],
                    "optimal_posting_times": result["optimal_posting_times"],
                    "trending_topics": result["trending_topics"],
                    "audience_insights": result["audience_insights"]
                }
            }
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        logger.error(f"Pack enhancement error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/optimize/pre-publish")
async def optimize_before_publishing(post_data: Dict[str, Any]):
    """
    Optimise un post avant publication avec Supadata AI
    """
    try:
        result = await supadata_optimizer.optimize_post_before_publishing(post_data)
        
        if result["success"]:
            return {
                "success": True,
                "data": result
            }
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        logger.error(f"Pre-publishing optimization error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def supadata_status():
    """
    Vérifie le status de l'intégration Supadata
    """
    try:
        # Test simple de connexion
        test_content = {
            "title": "Test ContentFlow",
            "description": "Test integration",
            "platform": "youtube",
            "niche": "test"
        }
        
        result = await supadata_client.analyze_content_performance(test_content)
        
        return {
            "success": True,
            "data": {
                "status": "connected" if result["success"] else "error",
                "api_available": result["success"],
                "error": result.get("error") if not result["success"] else None,
                "features": [
                    "Content Performance Analysis",
                    "Content Optimization",
                    "Audience Trends Analysis", 
                    "Content Recommendations",
                    "ContentFlow Pack Enhancement",
                    "Pre-Publishing Optimization"
                ]
            }
        }
        
    except Exception as e:
        logger.error(f"Supadata status check error: {e}")
        return {
            "success": False,
            "data": {
                "status": "error",
                "error": str(e)
            }
        }


@router.get("/demo/{niche}")
async def demo_supadata_enhancement(niche: str):
    """
    Démonstration des capacités Supadata pour une niche
    """
    try:
        # Récupérer la config actuelle
        config = get_config()
        niche_config = config.get_niche_config(niche)
        
        if not niche_config:
            raise HTTPException(status_code=404, detail=f"Niche {niche} not found")
        
        # Analyser avec Supadata pour YouTube (plateforme principale)
        recommendations = await supadata_client.get_content_recommendations(niche, "youtube")
        audience_analysis = await supadata_client.analyze_audience_trends(niche, "youtube")
        
        # Test d'optimisation sur un hook existant
        existing_hook = niche_config.get("hooks", ["Test hook"])[0]
        test_content = {
            "title": existing_hook,
            "description": f"Contenu {niche} optimisé",
            "platform": "youtube",
            "niche": niche,
            "hook": existing_hook
        }
        
        optimization = await supadata_client.optimize_content(test_content, "conversion")
        
        return {
            "success": True,
            "data": {
                "niche": niche,
                "original_hooks": niche_config.get("hooks", [])[:3],
                "supadata_recommendations": recommendations.get("recommended_hooks", [])[:3] if recommendations["success"] else [],
                "trending_topics": audience_analysis.get("trending_topics", [])[:3] if audience_analysis["success"] else [],
                "optimization_demo": {
                    "original": existing_hook,
                    "optimized": optimization.get("optimized_hook") if optimization["success"] else None,
                    "improvement_score": optimization.get("improvement_score", 0) if optimization["success"] else 0
                },
                "audience_insights": audience_analysis.get("audience_demographics", {}) if audience_analysis["success"] else {}
            }
        }
        
    except Exception as e:
        logger.error(f"Supadata demo error: {e}")
        raise HTTPException(status_code=500, detail=str(e))