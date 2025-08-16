"""
ContentFlow Configuration Manager
Loads and manages niche-specific content strategies from contentflow_pack.json
"""

import json
import os
import random
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ContentFlowConfig:
    """Manages ContentFlow configuration for targeted niches"""
    
    def __init__(self, config_path: str = "contentflow_pack.json"):
        # Try multiple possible paths
        possible_paths = [
            config_path,
            f"/home/runner/workspace/{config_path}",
            f"../{config_path}",
            f"./{config_path}"
        ]
        
        self.config_path = None
        for path in possible_paths:
            if os.path.exists(path):
                self.config_path = path
                break
        
        if not self.config_path:
            logger.warning(f"Config file not found in any of: {possible_paths}")
            self.config_path = config_path
            
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file"""
        try:
            if self.config_path and os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    logger.info(f"Loaded ContentFlow config v{config.get('version', 'unknown')}")
                    return config
            else:
                logger.warning(f"Config file {self.config_path} not found, using defaults")
                return self._default_config()
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return self._default_config()
    
    def _default_config(self) -> Dict[str, Any]:
        """Fallback configuration"""
        return {
            "version": "default",
            "niches": {},
            "planner_policies": {
                "shorts_max_s": 30,
                "hook_max_s": 5,
                "title_max_chars": 70
            }
        }
    
    def get_niches(self) -> List[str]:
        """Get all available niches"""
        return list(self.config.get("niches", {}).keys())
    
    def get_niche_config(self, niche: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific niche"""
        return self.config.get("niches", {}).get(niche)
    
    def get_hook_for_niche(self, niche: str) -> str:
        """Get a random hook for the specified niche"""
        niche_config = self.get_niche_config(niche)
        if niche_config and "hooks" in niche_config:
            return random.choice(niche_config["hooks"])
        return "Découvrez cette astuce incroyable !"
    
    def get_title_for_niche(self, niche: str) -> str:
        """Get a random title for the specified niche"""
        niche_config = self.get_niche_config(niche)
        if niche_config and "titles" in niche_config:
            return random.choice(niche_config["titles"])
        return "Guide complet 2025"
    
    def get_hashtags_for_niche(self, niche: str, count: int = 5) -> List[str]:
        """Get hashtags for the specified niche"""
        niche_config = self.get_niche_config(niche)
        if niche_config and "hashtags" in niche_config:
            hashtags = niche_config["hashtags"]
            return random.sample(hashtags, min(count, len(hashtags)))
        return ["#ContentFlow", "#2025", "#Astuce"]
    
    def get_cta_for_niche(self, niche: str) -> str:
        """Get a random CTA for the specified niche"""
        niche_config = self.get_niche_config(niche)
        if niche_config and "ctas" in niche_config:
            return random.choice(niche_config["ctas"])
        return "En savoir plus ↓"
    
    def get_serpapi_queries(self, niche: str) -> Dict[str, Any]:
        """Get SerpAPI queries for the specified niche"""
        niche_config = self.get_niche_config(niche)
        if niche_config and "serpapi_queries" in niche_config:
            return niche_config["serpapi_queries"]
        return {
            "youtube_queries": [f"{niche} guide 2025"],
            "news_queries": [f"{niche} actualités"],
            "trends_category_id": 0
        }
    
    def get_ffmpeg_recipe(self, format_type: str = "shorts_9_16") -> Dict[str, Any]:
        """Get FFmpeg configuration for video processing"""
        return self.config.get("ffmpeg_recipes", {}).get(format_type, {})
    
    def get_scheduler_windows(self, platform: str) -> List[str]:
        """Get optimal posting windows for a platform"""
        return self.config.get("scheduler_windows", {}).get(platform, ["09:00-17:00"])
    
    def get_bandit_arms(self) -> List[Dict[str, str]]:
        """Get multi-armed bandit configuration"""
        return self.config.get("bandit_arms", [])
    
    def is_keyword_denied(self, keyword: str) -> bool:
        """Check if a keyword is in the denylist"""
        denylist = self.config.get("denylist_keywords", [])
        keyword_lower = keyword.lower()
        return any(denied.lower() in keyword_lower for denied in denylist)
    
    def get_planner_policies(self) -> Dict[str, Any]:
        """Get content planning policies"""
        return self.config.get("planner_policies", {})
    
    def generate_optimized_content(self, niche: str, platform: str) -> Dict[str, Any]:
        """Generate optimized content for a specific niche and platform"""
        try:
            niche_config = self.get_niche_config(niche)
            if not niche_config:
                logger.warning(f"Niche '{niche}' not found in config")
                niche = "ai_saas"  # Fallback to most profitable niche
                niche_config = self.get_niche_config(niche)
            
            # Generate content elements
            hook = self.get_hook_for_niche(niche)
            title = self.get_title_for_niche(niche)
            hashtags = self.get_hashtags_for_niche(niche, count=8)
            cta = self.get_cta_for_niche(niche)
            
            # Platform-specific optimizations
            if platform == "tiktok":
                hashtags = hashtags[:5]  # TikTok prefers fewer hashtags
                title = title[:60]  # Shorter titles work better
            elif platform == "youtube":
                hashtags = hashtags[:3]  # YouTube focuses on description
                title = title[:70]  # YouTube title limit
            elif platform == "instagram":
                hashtags = hashtags[:8]  # Instagram allows many hashtags
                
            return {
                "niche": niche,
                "platform": platform,
                "hook": hook,
                "title": title,
                "hashtags": hashtags,
                "cta": cta,
                "hashtag_string": " ".join(hashtags),
                "description": f"{title}\n\n{' '.join(hashtags)}\n\n{cta}",
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to generate content for {niche}/{platform}: {e}")
            return self._fallback_content(platform)
    
    def _fallback_content(self, platform: str) -> Dict[str, Any]:
        """Fallback content when niche config fails"""
        return {
            "niche": "general",
            "platform": platform,
            "hook": "Ne ratez pas cette astuce !",
            "title": "Guide essentiel 2025",
            "hashtags": ["#Guide", "#2025", "#Astuce"],
            "cta": "En savoir plus ↓",
            "hashtag_string": "#Guide #2025 #Astuce",
            "description": "Guide essentiel 2025\n\n#Guide #2025 #Astuce\n\nEn savoir plus ↓",
            "generated_at": datetime.now().isoformat()
        }
    
    def get_niche_metrics(self) -> Dict[str, Any]:
        """Get analytics about available niches"""
        niches = self.get_niches()
        metrics = {
            "total_niches": len(niches),
            "niches": []
        }
        
        for niche in niches:
            config = self.get_niche_config(niche)
            if config:
                metrics["niches"].append({
                    "name": niche,
                    "hooks_count": len(config.get("hooks", [])),
                    "titles_count": len(config.get("titles", [])),
                    "hashtags_count": len(config.get("hashtags", [])),
                    "ctas_count": len(config.get("ctas", [])),
                    "youtube_queries": len(config.get("serpapi_queries", {}).get("youtube_queries", [])),
                    "news_queries": len(config.get("serpapi_queries", {}).get("news_queries", []))
                })
        
        return metrics

# Global instance for easy access
contentflow_config = ContentFlowConfig()

def get_config() -> ContentFlowConfig:
    """Get the global ContentFlow configuration instance"""
    return contentflow_config

def reload_config() -> bool:
    """Reload configuration from file"""
    try:
        global contentflow_config
        contentflow_config = ContentFlowConfig()
        logger.info("ContentFlow configuration reloaded successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to reload configuration: {e}")
        return False

# Example usage
if __name__ == "__main__":
    config = get_config()
    
    print(f"Available niches: {config.get_niches()}")
    
    # Test content generation for each niche
    for niche in config.get_niches():
        for platform in ["youtube", "tiktok", "instagram"]:
            content = config.generate_optimized_content(niche, platform)
            print(f"\n{niche.upper()} on {platform.upper()}:")
            print(f"Hook: {content['hook']}")
            print(f"Title: {content['title']}")
            print(f"Hashtags: {content['hashtag_string']}")
            print(f"CTA: {content['cta']}")