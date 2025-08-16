"""
Buffer API routes for ContentFlow
Provides endpoints to manage Buffer integration and publishing
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import logging

from app.db import get_db
from app.models import Post
from app.services.buffer_integration import BufferAPI, test_buffer_connection

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/buffer", tags=["buffer"])

@router.get("/status")
async def get_buffer_status():
    """Check Buffer API connection and available profiles"""
    try:
        if not test_buffer_connection():
            return {
                "success": False,
                "connected": False,
                "error": "Buffer API not configured or connection failed"
            }
        
        buffer = BufferAPI()
        profiles = buffer.get_profiles()
        
        # Group profiles by platform
        platforms = {}
        for profile in profiles:
            platform = profile.get('service', 'unknown')
            if platform not in platforms:
                platforms[platform] = []
            platforms[platform].append({
                'id': profile.get('id'),
                'username': profile.get('username', ''),
                'formatted_username': profile.get('formatted_username', ''),
                'avatar': profile.get('avatar', ''),
                'timezone': profile.get('timezone', '')
            })
        
        return {
            "success": True,
            "connected": True,
            "total_profiles": len(profiles),
            "platforms": platforms,
            "supported_platforms": list(platforms.keys())
        }
        
    except Exception as e:
        logger.error(f"Buffer status check failed: {e}")
        return {
            "success": False,
            "connected": False,
            "error": str(e)
        }

@router.post("/publish/{post_id}")
async def publish_post_via_buffer(
    post_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Publish a specific post via Buffer API"""
    try:
        # Check if post exists
        post = db.query(Post).filter(Post.id == post_id).first()
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        
        # Check if already published
        if post.status == 'published':
            return {
                "success": False,
                "error": "Post already published"
            }
        
        # Publish via Buffer API
        buffer = BufferAPI()
        result = buffer.publish_post(post_id)
        
        if result['success']:
            return {
                "success": True,
                "message": f"Post {post_id} published to {post.platform} via Buffer",
                "buffer_id": result.get('buffer_id'),
                "platform": post.platform
            }
        else:
            return {
                "success": False,
                "error": result.get('error', 'Unknown Buffer API error')
            }
            
    except Exception as e:
        logger.error(f"Buffer publish failed for post {post_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/publish/batch")
async def publish_batch_via_buffer(
    post_ids: List[int],
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Publish multiple posts via Buffer API"""
    try:
        # Validate posts exist
        posts = db.query(Post).filter(Post.id.in_(post_ids)).all()
        if len(posts) != len(post_ids):
            found_ids = [p.id for p in posts]
            missing_ids = [pid for pid in post_ids if pid not in found_ids]
            raise HTTPException(
                status_code=404, 
                detail=f"Posts not found: {missing_ids}"
            )
        
        # Filter out already published posts
        publishable_posts = [p for p in posts if p.status != 'published']
        if not publishable_posts:
            return {
                "success": False,
                "error": "All posts are already published"
            }
        
        # Batch publish via Buffer
        buffer = BufferAPI()
        publishable_ids = [p.id for p in publishable_posts]
        result = buffer.batch_publish(publishable_ids)
        
        return {
            "success": True,
            "published": result['published'],
            "failed": result['failed'],
            "total_requested": len(post_ids),
            "already_published": len(posts) - len(publishable_posts),
            "results": result['results']
        }
        
    except Exception as e:
        logger.error(f"Buffer batch publish failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/{post_id}")
async def get_post_analytics(post_id: int, db: Session = Depends(get_db)):
    """Get Buffer analytics for a published post"""
    try:
        # Get post with Buffer metadata
        post = db.query(Post).filter(Post.id == post_id).first()
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        
        if post.status != 'published':
            return {
                "success": False,
                "error": "Post not published yet"
            }
        
        # Extract Buffer update ID from metadata
        import json
        metadata = json.loads(post.metadata_json or '{}')
        buffer_update_id = metadata.get('buffer_update_id')
        
        if not buffer_update_id:
            return {
                "success": False,
                "error": "No Buffer analytics available for this post"
            }
        
        # Get analytics from Buffer
        buffer = BufferAPI()
        analytics = buffer.get_post_analytics(buffer_update_id)
        
        return {
            "success": True,
            "post_id": post_id,
            "platform": post.platform,
            "analytics": analytics
        }
        
    except Exception as e:
        logger.error(f"Buffer analytics failed for post {post_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/profiles")
async def get_buffer_profiles():
    """Get all connected Buffer profiles with details"""
    try:
        buffer = BufferAPI()
        profiles = buffer.get_profiles()
        
        # Enhanced profile information
        enhanced_profiles = []
        for profile in profiles:
            enhanced_profiles.append({
                'id': profile.get('id'),
                'service': profile.get('service'),
                'username': profile.get('username'),
                'formatted_username': profile.get('formatted_username'),
                'avatar': profile.get('avatar'),
                'timezone': profile.get('timezone'),
                'schedules': profile.get('schedules', []),
                'supported_features': profile.get('supported_features', [])
            })
        
        return {
            "success": True,
            "profiles": enhanced_profiles,
            "total": len(profiles)
        }
        
    except Exception as e:
        logger.error(f"Failed to get Buffer profiles: {e}")
        return {
            "success": False,
            "error": str(e),
            "profiles": []
        }

@router.post("/test")
async def test_buffer_integration():
    """Test Buffer API integration and credentials"""
    try:
        # Test connection
        if not test_buffer_connection():
            return {
                "success": False,
                "message": "Buffer API connection failed",
                "suggestions": [
                    "Check BUFFER_ACCESS_TOKEN environment variable",
                    "Verify Buffer API credentials",
                    "Ensure Buffer app has necessary permissions"
                ]
            }
        
        # Test profile access
        buffer = BufferAPI()
        profiles = buffer.get_profiles()
        
        # Identify supported platforms
        supported_platforms = list(set([p.get('service') for p in profiles]))
        
        return {
            "success": True,
            "message": "Buffer API integration working correctly",
            "profiles_found": len(profiles),
            "supported_platforms": supported_platforms,
            "ready_for_publishing": len(profiles) > 0
        }
        
    except Exception as e:
        logger.error(f"Buffer test failed: {e}")
        return {
            "success": False,
            "message": "Buffer integration test failed",
            "error": str(e)
        }