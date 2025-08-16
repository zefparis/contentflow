import json
import os
import re
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.models import Asset, Post
from utils.ffmpeg import make_vertical, create_demo_vertical_video
from app.utils.logger import logger


def analyze_asset(asset: Asset) -> Dict[str, Any]:
    """Analyze asset to extract duration, language, keywords."""
    try:
        meta = json.loads(asset.meta_json) if asset.meta_json else {}
        title = meta.get('title', '')
        description = meta.get('description', '')
        
        # Extract duration from metadata or estimate
        duration = meta.get('duration', asset.duration)
        if not duration:
            # Estimate based on content length
            content_length = len(title) + len(description)
            duration = max(15, min(60, content_length / 10))  # Rough estimate
        
        # Detect probable language
        text = f"{title} {description}".lower()
        lang = detect_language_simple(text)
        
        # Extract keywords using simple regex
        keywords = extract_keywords_simple(text)
        
        analysis = {
            'duration': duration,
            'language': lang,
            'keywords': keywords,
            'word_count': len(text.split()),
            'has_numbers': bool(re.search(r'\d+', text)),
            'has_urls': bool(re.search(r'http[s]?://', text))
        }
        
        logger.info(f"Analyzed asset {asset.id}: duration={duration}s, lang={lang}")
        return analysis
        
    except Exception as e:
        logger.error(f"Error analyzing asset {asset.id}: {e}")
        return {'duration': 30, 'language': 'fr', 'keywords': []}


def detect_language_simple(text: str) -> str:
    """Simple language detection based on keywords."""
    french_indicators = ['le', 'la', 'les', 'de', 'du', 'des', 'et', 'ou', 'est', 'sont', 
                        'avec', 'pour', 'dans', 'sur', 'par', 'cette', 'ces', 'nous', 'vous']
    english_indicators = ['the', 'and', 'or', 'is', 'are', 'with', 'for', 'in', 'on', 'by',
                         'this', 'these', 'we', 'you', 'that', 'have', 'has', 'will']
    
    words = text.lower().split()
    french_count = sum(1 for word in words if word in french_indicators)
    english_count = sum(1 for word in words if word in english_indicators)
    
    return 'fr' if french_count >= english_count else 'en'


def extract_keywords_simple(text: str) -> List[str]:
    """Extract keywords using simple pattern matching."""
    # Remove common words and extract meaningful terms
    words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
    
    # Tech-related keyword boost
    tech_keywords = ['tech', 'innovation', 'startup', 'digital', 'intelligence', 'artificielle',
                    'machine', 'learning', 'blockchain', 'crypto', 'fintech', 'saas', 'api']
    
    keywords = []
    for word in words:
        if word in tech_keywords:
            keywords.append(word)
        elif len(word) > 6 and words.count(word) == 1:  # Unique longer words
            keywords.append(word)
    
    return list(set(keywords))[:10]


def transform_asset(asset: Asset, db: Session) -> bool:
    """Transform asset using FFmpeg with vertical video output."""
    try:
        # Analyze asset first
        analysis = analyze_asset(asset)
        
        # Update asset with analysis
        if analysis.get('duration'):
            asset.duration = analysis['duration']
        if analysis.get('language'):
            asset.lang = analysis['language']
        if analysis.get('keywords'):
            asset.keywords = ','.join(analysis['keywords'])
        
        # Generate AI plan
        from app.services.ai_planner import generate_plan_heuristic
        plan = generate_plan_heuristic(asset)
        
        # Get input path - for demo, create a sample video
        meta = json.loads(asset.meta_json or "{}")
        input_path = meta.get("url", "")
        
        # Create output path
        output_filename = f"asset_{asset.id}_vertical.mp4"
        output_path = f"/tmp/{output_filename}"
        
        # Transform video to vertical format
        success = False
        if input_path and os.path.exists(input_path):
            success = make_vertical(input_path, plan, output_path)
        else:
            # Create demo video for testing
            logger.info(f"Creating demo video for asset {asset.id}")
            success = create_demo_vertical_video(output_path)
        
        if not success or not os.path.exists(output_path):
            logger.error(f"Video transformation failed for asset {asset.id}")
            asset.status = "failed"
            db.commit()
            return False
        
        # Set S3 key (simplified for demo)
        s3_key = f"assets/{asset.id}_{output_filename}"
        asset.s3_key = output_path  # Local path for development
        
        # Update asset status and metadata
        asset.status = "ready"
        meta.update({
            "processed": True,
            "plan": plan,
            "output_path": output_path,
            "analysis": analysis
        })
        asset.meta_json = json.dumps(meta)
        
        db.commit()
        logger.info(f"Successfully transformed asset {asset.id}")
        return True
        
    except Exception as e:
        logger.error(f"Asset transformation failed for {asset.id}: {e}")
        asset.status = "failed"
        db.commit()
        return False


def create_draft_post(db: Session, asset: Asset, plan: Dict[str, Any]):
    """Create a draft post from processed asset"""
    try:
        meta = json.loads(asset.meta_json or "{}")
        
        # Generate post content from plan
        overlays = plan.get('overlays', {})
        title = overlays.get('hook_text', meta.get('title', 'Amazing Content!'))
        description = meta.get('description', 'Check out this amazing content!')
        
        # Add hashtags to description
        hashtags = plan.get('hashtags', [])
        if hashtags:
            description += f"\n\n{' '.join(hashtags)}"
        
        # Add affiliate disclosure
        description += " #ad"
        
        # Select platform (for demo, default to Instagram)
        platform = "instagram"
        
        # Create post
        post = Post(
            asset_id=asset.id,
            platform=platform,
            title=title,
            description=description,
            language=plan.get('language', 'fr'),
            hashtags=','.join(hashtags) if hashtags else None,
            status="draft"
        )
        
        db.add(post)
        db.commit()
        
        logger.info(f"Created draft post {post.id} for asset {asset.id}")
        return post
        
    except Exception as e:
        logger.error(f"Failed to create draft post for asset {asset.id}: {e}")
        return None
