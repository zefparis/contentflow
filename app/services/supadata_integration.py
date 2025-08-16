"""
Intégration Supadata AI pour ContentFlow
Intelligence artificielle avancée pour l'analyse et l'optimisation de contenu
"""

import os
import httpx
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class SupadataClient:
    """Client pour l'API Supadata AI"""
    
    def __init__(self):
        self.api_key = os.getenv('SUPADATA_API_KEY')
        self.base_url = "https://api.supadata.ai/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def analyze_content_performance(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyse la performance prédictive d'un contenu
        """
        try:
            payload = {
                "content": {
                    "title": content.get("title", ""),
                    "description": content.get("description", ""),
                    "platform": content.get("platform", ""),
                    "niche": content.get("niche", ""),
                    "hashtags": content.get("hashtags", []),
                    "hook": content.get("hook", ""),
                    "cta": content.get("cta", "")
                },
                "analysis_type": "performance_prediction"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/analyze/content",
                    json=payload,
                    headers=self.headers,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return {
                        "success": True,
                        "performance_score": result.get("performance_score", 0),
                        "engagement_prediction": result.get("engagement_prediction", {}),
                        "optimization_suggestions": result.get("suggestions", []),
                        "confidence": result.get("confidence", 0),
                        "best_posting_time": result.get("best_posting_time"),
                        "target_audience": result.get("target_audience", {})
                    }
                else:
                    logger.error(f"Supadata API error: {response.status_code}")
                    return {"success": False, "error": f"API error: {response.status_code}"}
                    
        except Exception as e:
            logger.error(f"Supadata analysis error: {e}")
            return {"success": False, "error": str(e)}
    
    async def optimize_content(self, content: Dict[str, Any], goal: str = "engagement") -> Dict[str, Any]:
        """
        Optimise un contenu pour un objectif spécifique
        """
        try:
            payload = {
                "content": content,
                "optimization_goal": goal,  # engagement, conversion, reach
                "platform_specific": True
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/optimize/content",
                    json=payload,
                    headers=self.headers,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return {
                        "success": True,
                        "optimized_title": result.get("optimized_title"),
                        "optimized_description": result.get("optimized_description"),
                        "optimized_hashtags": result.get("optimized_hashtags", []),
                        "optimized_hook": result.get("optimized_hook"),
                        "optimized_cta": result.get("optimized_cta"),
                        "improvement_score": result.get("improvement_score", 0),
                        "changes_made": result.get("changes_made", [])
                    }
                else:
                    return {"success": False, "error": f"API error: {response.status_code}"}
                    
        except Exception as e:
            logger.error(f"Supadata optimization error: {e}")
            return {"success": False, "error": str(e)}
    
    async def analyze_audience_trends(self, niche: str, platform: str) -> Dict[str, Any]:
        """
        Analyse les tendances d'audience pour une niche et plateforme
        """
        try:
            payload = {
                "niche": niche,
                "platform": platform,
                "analysis_period": "30d",
                "include_predictions": True
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/analyze/audience",
                    json=payload,
                    headers=self.headers,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return {
                        "success": True,
                        "trending_topics": result.get("trending_topics", []),
                        "optimal_posting_times": result.get("optimal_posting_times", []),
                        "audience_demographics": result.get("demographics", {}),
                        "content_preferences": result.get("content_preferences", {}),
                        "competitor_insights": result.get("competitor_insights", [])
                    }
                else:
                    return {"success": False, "error": f"API error: {response.status_code}"}
                    
        except Exception as e:
            logger.error(f"Supadata audience analysis error: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_content_recommendations(self, niche: str, platform: str) -> Dict[str, Any]:
        """
        Obtient des recommandations de contenu basées sur l'IA
        """
        try:
            payload = {
                "niche": niche,
                "platform": platform,
                "content_type": "short_form_video",
                "optimization_target": "conversion"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/recommend/content",
                    json=payload,
                    headers=self.headers,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return {
                        "success": True,
                        "recommended_topics": result.get("topics", []),
                        "recommended_hooks": result.get("hooks", []),
                        "recommended_ctas": result.get("ctas", []),
                        "trending_hashtags": result.get("hashtags", []),
                        "content_angles": result.get("angles", [])
                    }
                else:
                    return {"success": False, "error": f"API error: {response.status_code}"}
                    
        except Exception as e:
            logger.error(f"Supadata recommendations error: {e}")
            return {"success": False, "error": str(e)}


class SupadataEnhancedOptimizer:
    """
    Optimiseur ContentFlow enrichi avec Supadata AI
    """
    
    def __init__(self):
        self.supadata = SupadataClient()
    
    async def enhance_contentflow_pack(self, niche: str, platform: str) -> Dict[str, Any]:
        """
        Améliore le ContentFlow Pack avec l'intelligence Supadata
        """
        try:
            # Analyser les tendances audience
            audience_analysis = await self.supadata.analyze_audience_trends(niche, platform)
            
            # Obtenir les recommandations
            recommendations = await self.supadata.get_content_recommendations(niche, platform)
            
            if audience_analysis["success"] and recommendations["success"]:
                return {
                    "success": True,
                    "enhanced_hooks": recommendations["recommended_hooks"],
                    "enhanced_ctas": recommendations["recommended_ctas"],
                    "trending_hashtags": recommendations["trending_hashtags"],
                    "optimal_posting_times": audience_analysis["optimal_posting_times"],
                    "trending_topics": audience_analysis["trending_topics"],
                    "audience_insights": audience_analysis["audience_demographics"]
                }
            else:
                return {"success": False, "error": "Failed to enhance pack"}
                
        except Exception as e:
            logger.error(f"Enhanced optimization error: {e}")
            return {"success": False, "error": str(e)}
    
    async def optimize_post_before_publishing(self, post_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Optimise un post avant publication avec Supadata AI
        """
        try:
            # Analyser la performance prédictive
            performance_analysis = await self.supadata.analyze_content_performance(post_data)
            
            if performance_analysis["success"]:
                # Si le score est faible, optimiser
                if performance_analysis["performance_score"] < 0.7:
                    optimization = await self.supadata.optimize_content(post_data, "conversion")
                    
                    if optimization["success"]:
                        return {
                            "success": True,
                            "should_optimize": True,
                            "original_score": performance_analysis["performance_score"],
                            "optimized_content": {
                                "title": optimization["optimized_title"],
                                "description": optimization["optimized_description"],
                                "hashtags": optimization["optimized_hashtags"],
                                "hook": optimization["optimized_hook"],
                                "cta": optimization["optimized_cta"]
                            },
                            "improvement_score": optimization["improvement_score"],
                            "best_posting_time": performance_analysis["best_posting_time"]
                        }
                
                return {
                    "success": True,
                    "should_optimize": False,
                    "score": performance_analysis["performance_score"],
                    "suggestions": performance_analysis["optimization_suggestions"]
                }
            else:
                return {"success": False, "error": performance_analysis["error"]}
                
        except Exception as e:
            logger.error(f"Pre-publishing optimization error: {e}")
            return {"success": False, "error": str(e)}


# Instance globale
supadata_client = SupadataClient()
supadata_optimizer = SupadataEnhancedOptimizer()