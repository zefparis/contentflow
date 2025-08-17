import json
from sqlalchemy.orm import Session
from app.models import Post, Link
from app.utils.logger import logger
from app.services.risk import calculate_risk_score
from app.utils.bandit import bandit
from app.utils.datetime import utcnow, iso_utc


def queue_post_for_publishing(db: Session, post: Post) -> bool:
    """Queue a post for publishing"""
    try:
        # Check compliance
        risk_score = calculate_risk_score(post)
        
        if risk_score >= 0.5:
            logger.warning(f"Post {post.id} has high risk score: {risk_score}")
            return False
        
        # Add affiliate link if needed
        link = db.query(Link).filter(
            Link.platform_hint == post.platform
        ).first()
        
        if link:
            # Generate UTM tracking
            utm_params = link.utm.format(platform=post.platform)
            post.shortlink = f"{link.affiliate_url}?{utm_params}"
        
        # Update status
        post.status = "queued"
        
        # Initialize metrics
        metrics = {
            "queued_at": iso_utc(),
            "risk_score": risk_score,
            "platform": post.platform
        }
        post.metrics_json = json.dumps(metrics)
        
        db.commit()
        
        logger.info(f"Queued post {post.id} for publishing")
        return True
        
    except Exception as e:
        logger.error(f"Failed to queue post {post.id}: {e}")
        return False


def update_post_content(db: Session, post_id: int, title: str, description: str, cta: str) -> bool:
    """Update post content"""
    try:
        post = db.query(Post).filter(Post.id == post_id).first()
        if not post:
            return False
        
        post.title = title
        post.description = description
        
        # Update metrics with CTA
        metrics = json.loads(post.metrics_json or "{}")
        metrics["cta"] = cta
        post.metrics_json = json.dumps(metrics)
        
        db.commit()
        
        logger.info(f"Updated content for post {post.id}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to update post {post_id}: {e}")
        return False
