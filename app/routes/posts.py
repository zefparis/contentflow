from fastapi import APIRouter, Depends, HTTPException, Form
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import Post
from app.services.posts import queue_post_for_publishing, update_post_content

router = APIRouter()


@router.get("/posts")
async def list_posts(db: Session = Depends(get_db)):
    """List all posts"""
    posts = db.query(Post).order_by(Post.created_at.desc()).limit(100).all()
    return [
        {
            "id": post.id,
            "asset_id": post.asset_id,
            "platform": post.platform,
            "title": post.title,
            "status": post.status,
            "created_at": post.created_at.isoformat(),
            "posted_at": post.posted_at.isoformat() if post.posted_at else None
        }
        for post in posts
    ]


@router.post("/posts/{post_id}/queue")
async def queue_post(post_id: int, db: Session = Depends(get_db)):
    """Queue a post for publishing"""
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    success = queue_post_for_publishing(db, post)
    
    return {
        "success": success,
        "status": post.status,
        "message": f"Post {post_id} {'queued' if success else 'failed to queue'}"
    }


@router.post("/posts/{post_id}/update")
async def update_post(
    post_id: int,
    title: str = Form(...),
    description: str = Form(...),
    cta: str = Form(...),
    db: Session = Depends(get_db)
):
    """Update post content"""
    success = update_post_content(db, post_id, title, description, cta)
    
    if not success:
        raise HTTPException(status_code=404, detail="Post not found")
    
    return {
        "success": True,
        "message": f"Post {post_id} updated successfully"
    }
