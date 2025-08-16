from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Dict, Any
from app.db import get_db
from app.models import Asset
from app.services.compliance import (
    compute_risk,
    get_compliance_summary,
    review_asset,
    is_content_safe_for_autopost
)
import json

router = APIRouter()

@router.get("/compliance/summary")
async def compliance_summary(db: Session = Depends(get_db)):
    """Get compliance gate summary."""
    try:
        summary = get_compliance_summary()
        return {"success": True, "data": summary}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/compliance/risk/{asset_id}")
async def check_asset_risk(asset_id: int, db: Session = Depends(get_db)):
    """Get risk score for a specific asset."""
    try:
        asset = db.query(Asset).filter(Asset.id == asset_id).first()
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")
        
        # Get plan from metadata
        meta = json.loads(asset.meta_json or "{}")
        plan = meta.get("plan", {})
        
        risk_score = compute_risk(asset, plan)
        is_safe = is_content_safe_for_autopost(asset, plan)
        
        return {
            "success": True,
            "data": {
                "asset_id": asset.id,
                "risk_score": risk_score,
                "is_safe_for_autopost": is_safe,
                "quality_score": plan.get("quality_score", 0.0)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/compliance/review/{asset_id}")
async def review_asset_endpoint(
    asset_id: int, 
    approved: bool, 
    reviewer_notes: str = "",
    db: Session = Depends(get_db)
):
    """Manually review an asset (approve/reject)."""
    try:
        success = review_asset(asset_id, approved, reviewer_notes)
        
        if success:
            return {
                "success": True,
                "message": f"Asset {asset_id} {'approved' if approved else 'rejected'}"
            }
        else:
            raise HTTPException(status_code=404, detail="Asset not found")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/compliance/queue")
async def get_review_queue(db: Session = Depends(get_db)):
    """Get assets waiting for manual review."""
    try:
        from app.models import Post
        
        # Get posts in review status
        review_posts = db.query(Post).filter(Post.status == "review").all()
        
        queue_data = []
        for post in review_posts:
            if post.asset:
                meta = json.loads(post.asset.meta_json or "{}")
                plan = meta.get("plan", {})
                
                queue_data.append({
                    "post_id": post.id,
                    "asset_id": post.asset.id,
                    "title": post.title,
                    "platform": post.platform,
                    "risk_score": compute_risk(post.asset, plan),
                    "quality_score": plan.get("quality_score", 0.0),
                    "created_at": post.created_at.isoformat() if post.created_at else None
                })
        
        return {
            "success": True,
            "data": {
                "queue_count": len(queue_data),
                "items": queue_data
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))