from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from app.db import get_db
from app.models import Post, Asset
from app.services.performance_ai import (
    performance_ai,
    predict_post_performance,
    train_performance_models,
    get_ai_model_status
)

router = APIRouter()

@router.get("/ai/models/status")
async def ai_models_status():
    """Get status of all AI performance models."""
    try:
        status = get_ai_model_status()
        return {"success": True, "data": status}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ai/models/train")
async def train_ai_models(platform: Optional[str] = None):
    """Train AI performance models for all platforms or specific platform."""
    try:
        if platform:
            result = performance_ai.train_model(platform)
            return {"success": True, "data": {platform: result}}
        else:
            results = train_performance_models()
            return {"success": True, "data": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/ai/predict/{post_id}")
async def predict_performance(post_id: int, db: Session = Depends(get_db)):
    """Predict performance for a specific post."""
    try:
        post = db.query(Post).filter(Post.id == post_id).first()
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        
        asset = db.query(Asset).filter(Asset.id == post.asset_id).first()
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")
        
        prediction = predict_post_performance(post, asset)
        return {"success": True, "data": prediction}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ai/predict/draft")
async def predict_draft_performance(
    asset_id: int,
    platform: str,
    title: str,
    description: str = "",
    hashtags: str = "",
    language: str = "en",
    db: Session = Depends(get_db)
):
    """Predict performance for a draft post before creation."""
    try:
        asset = db.query(Asset).filter(Asset.id == asset_id).first()
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")
        
        # Create temporary post object for prediction
        temp_post = Post(
            asset_id=asset_id,
            platform=platform,
            title=title,
            description=description,
            hashtags=hashtags,
            language=language,
            status="draft"
        )
        
        prediction = predict_post_performance(temp_post, asset)
        return {"success": True, "data": prediction}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/ai/insights/platform/{platform}")
async def platform_insights(platform: str, db: Session = Depends(get_db)):
    """Get AI insights for a specific platform."""
    try:
        if platform not in performance_ai.models:
            return {
                "success": False,
                "error": f"No model available for {platform}",
                "suggestion": "Train model first with historical data"
            }
        
        model_data = performance_ai.models[platform]
        
        # Get recent posts for analysis
        recent_posts = db.query(Post).filter(
            Post.platform == platform,
            Post.status == "posted"
        ).order_by(Post.posted_at.desc()).limit(10).all()
        
        insights = {
            "model_info": {
                "type": model_data["model_type"],
                "accuracy": model_data["r2_score"],
                "training_samples": model_data["training_samples"],
                "last_trained": model_data["trained_at"].isoformat()
            },
            "recent_posts_count": len(recent_posts),
            "platform": platform
        }
        
        # Calculate average predictions for recent posts
        if recent_posts:
            predictions = []
            for post in recent_posts:
                asset = db.query(Asset).filter(Asset.id == post.asset_id).first()
                if asset:
                    pred = predict_post_performance(post, asset)
                    if pred["success"]:
                        predictions.append(pred["predicted_engagement"])
            
            if predictions:
                insights["average_predicted_engagement"] = sum(predictions) / len(predictions)
                insights["engagement_trend"] = "improving" if predictions[-1] > predictions[0] else "declining"
        
        return {"success": True, "data": insights}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/ai/recommendations/{asset_id}")
async def content_recommendations(asset_id: int, platform: str, db: Session = Depends(get_db)):
    """Get AI-powered content optimization recommendations."""
    try:
        asset = db.query(Asset).filter(Asset.id == asset_id).first()
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")
        
        # Get existing post or create template
        existing_post = db.query(Post).filter(
            Post.asset_id == asset_id,
            Post.platform == platform
        ).first()
        
        if existing_post:
            post = existing_post
        else:
            # Create template post for recommendations
            import json
            asset_meta = json.loads(asset.meta_json or "{}")
            plan = asset_meta.get("plan", {})
            
            post = Post(
                asset_id=asset_id,
                platform=platform,
                title=plan.get("title", f"Content from Asset {asset_id}"),
                description=plan.get("description", ""),
                hashtags=",".join(plan.get("hashtags", [])),
                language=asset.lang or "en",
                status="draft"
            )
        
        # Get AI prediction with recommendations
        prediction = predict_post_performance(post, asset)
        
        if not prediction["success"]:
            return prediction
        
        recommendations = {
            "current_prediction": {
                "engagement_rate": prediction["predicted_engagement"],
                "confidence": prediction["confidence"]
            },
            "optimizations": prediction["recommendations"],
            "model_info": prediction["model_info"]
        }
        
        # Add feature analysis
        features = performance_ai.extract_features(post, asset)
        recommendations["feature_analysis"] = {
            "title_length": features["title_length"],
            "description_length": features["description_length"],
            "hashtag_count": features["hashtag_count"],
            "quality_score": features["quality_score"],
            "optimal_posting_time": _get_optimal_posting_time(platform)
        }
        
        return {"success": True, "data": recommendations}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def _get_optimal_posting_time(platform: str) -> Dict[str, Any]:
    """Get optimal posting times for platform based on general best practices."""
    
    optimal_times = {
        "youtube": {"hours": [14, 15, 16, 20, 21], "days": [1, 2, 4]},  # Tue, Wed, Fri 2-4pm, 8-9pm
        "tiktok": {"hours": [6, 10, 19, 20], "days": [1, 2, 3, 4]},    # Tue-Fri 6am, 10am, 7-8pm
        "instagram": {"hours": [11, 13, 17], "days": [1, 2, 3, 4]},    # Tue-Fri 11am, 1pm, 5pm
        "reddit": {"hours": [7, 8, 9, 21, 22], "days": [0, 6]},       # Mon, Sun 7-9am, 9-10pm
        "pinterest": {"hours": [20, 21, 22], "days": [5, 6]}          # Sat, Sun 8-10pm
    }
    
    return optimal_times.get(platform, {"hours": [12, 18], "days": [1, 2, 3, 4, 5]})