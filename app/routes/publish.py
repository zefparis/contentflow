from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Dict, Any
from app.db import get_db
from app.models import Post
from app.services.publish import do_publish, generate_shortlink

router = APIRouter()

@router.post("/publish/{post_id}")
async def publish_post(post_id: int, db: Session = Depends(get_db)):
    """Manually trigger publication of a specific post."""
    try:
        post = db.query(Post).filter(Post.id == post_id).first()
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        
        result = do_publish(post, db)
        return {"success": result["success"], "data": result}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/publish/status/{post_id}")
async def get_publish_status(post_id: int, db: Session = Depends(get_db)):
    """Get publication status for a post."""
    try:
        post = db.query(Post).filter(Post.id == post_id).first()
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        
        return {
            "success": True,
            "data": {
                "post_id": post.id,
                "status": post.status,
                "platform": post.platform,
                "metrics": post.metrics_json
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/publish/shortlink/{post_id}")
async def create_shortlink(post_id: int, base_url: str = "https://contentflow.app", db: Session = Depends(get_db)):
    """Generate a tracking shortlink for a post."""
    try:
        post = db.query(Post).filter(Post.id == post_id).first()
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        
        shortlink = generate_shortlink(post, base_url)
        db.commit()
        
        return {
            "success": True,
            "data": {
                "shortlink": shortlink,
                "post_id": post.id
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))