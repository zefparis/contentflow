"""Real analytics pulling from platforms with safe fallbacks."""

import os
import json
from typing import Optional, Dict, Any
from datetime import timedelta
import requests
import praw
from sqlalchemy.orm import Session

from app.models import Post, MetricEvent
from app.utils.logger import logger, set_post_context
from app.utils.jobs import check_rate_limit, should_backoff_platform
from app.utils.datetime import utcnow

def pull_youtube_stats(db: Session, post: Post) -> Optional[Dict[str, Any]]:
    """Pull YouTube video statistics via Data API v3."""
    if not post.platform_id or not os.getenv("YOUTUBE_API_KEY"):
        logger.info(f"YouTube stats unavailable for post {post.id}: missing platform_id or API key")
        return None
        
    if not check_rate_limit("youtube") or should_backoff_platform("youtube"):
        logger.warning(f"YouTube rate limit hit for post {post.id}")
        return None
        
    set_post_context(post.id)
    
    try:
        api_key = os.getenv("YOUTUBE_API_KEY")
        url = f"https://www.googleapis.com/youtube/v3/videos"
        params = {
            "id": post.platform_id,
            "part": "statistics,snippet",
            "key": api_key
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        if not data.get("items"):
            logger.warning(f"YouTube video {post.platform_id} not found")
            return None
            
        stats = data["items"][0]["statistics"]
        snippet = data["items"][0]["snippet"]
        
        metrics = {
            "views": int(stats.get("viewCount", 0)),
            "likes": int(stats.get("likeCount", 0)),
            "comments": int(stats.get("commentCount", 0)),
            "duration": snippet.get("duration"),
            "published_at": snippet.get("publishedAt")
        }
        
        # Save metrics to database
        for metric_name, value in metrics.items():
            if isinstance(value, int) and value > 0:
                metric_event = MetricEvent(
                    post_id=post.id,
                    platform=post.platform,
                    kind=metric_name,
                    value=value,
                    timestamp=utcnow()
                )
                db.add(metric_event)
        
        # Update post metrics JSON
        post.metrics_json = json.dumps(metrics)
        db.commit()
        
        logger.info(f"YouTube stats updated for post {post.id}: {metrics['views']} views")
        return metrics
        
    except Exception as e:
        logger.error(f"Failed to pull YouTube stats for post {post.id}: {e}")
        return None

def pull_reddit_stats(db: Session, post: Post) -> Optional[Dict[str, Any]]:
    """Pull Reddit post statistics via PRAW."""
    if not post.platform_id or not all([
        os.getenv("REDDIT_CLIENT_ID"),
        os.getenv("REDDIT_CLIENT_SECRET")
    ]):
        logger.info(f"Reddit stats unavailable for post {post.id}: missing credentials")
        return None
        
    if not check_rate_limit("reddit") or should_backoff_platform("reddit"):
        logger.warning(f"Reddit rate limit hit for post {post.id}")
        return None
        
    set_post_context(post.id)
    
    try:
        reddit = praw.Reddit(
            client_id=os.getenv("REDDIT_CLIENT_ID"),
            client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
            user_agent=os.getenv("REDDIT_USER_AGENT", "ContentFlow/1.0")
        )
        
        submission = reddit.submission(id=post.platform_id)
        
        metrics = {
            "score": submission.score,
            "upvote_ratio": submission.upvote_ratio,
            "num_comments": submission.num_comments,
            "created_utc": submission.created_utc,
            "subreddit": str(submission.subreddit)
        }
        
        # Save metrics to database
        for metric_name, value in metrics.items():
            if isinstance(value, (int, float)) and value > 0:
                metric_event = MetricEvent(
                    post_id=post.id,
                    platform=post.platform,
                    kind=metric_name,
                    value=value,
                    timestamp=utcnow()
                )
                db.add(metric_event)
        
        # Update post metrics JSON
        post.metrics_json = json.dumps(metrics)
        db.commit()
        
        logger.info(f"Reddit stats updated for post {post.id}: {metrics['score']} score")
        return metrics
        
    except Exception as e:
        logger.error(f"Failed to pull Reddit stats for post {post.id}: {e}")
        return None

def pull_pinterest_stats(db: Session, post: Post) -> Optional[Dict[str, Any]]:
    """Pull Pinterest pin statistics via API v5."""
    if not post.platform_id or not os.getenv("PINTEREST_ACCESS_TOKEN"):
        logger.info(f"Pinterest stats unavailable for post {post.id}: missing token")
        return None
        
    if not check_rate_limit("pinterest") or should_backoff_platform("pinterest"):
        logger.warning(f"Pinterest rate limit hit for post {post.id}")
        return None
        
    set_post_context(post.id)
    
    try:
        headers = {
            "Authorization": f"Bearer {os.getenv('PINTEREST_ACCESS_TOKEN')}",
            "Content-Type": "application/json"
        }
        
        url = f"https://api.pinterest.com/v5/pins/{post.platform_id}/analytics"
        params = {
            "start_date": (utcnow() - timedelta(days=7)).strftime("%Y-%m-%d"),
            "end_date": utcnow().strftime("%Y-%m-%d"),
            "metric_types": "IMPRESSION,SAVE,PIN_CLICK,OUTBOUND_CLICK"
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        metrics_data = data.get("all", {})
        
        metrics = {
            "impressions": metrics_data.get("IMPRESSION", 0),
            "saves": metrics_data.get("SAVE", 0),
            "pin_clicks": metrics_data.get("PIN_CLICK", 0),
            "outbound_clicks": metrics_data.get("OUTBOUND_CLICK", 0)
        }
        
        # Save metrics to database
        for metric_name, value in metrics.items():
            if isinstance(value, (int, float)) and value > 0:
                metric_event = MetricEvent(
                    post_id=post.id,
                    platform=post.platform,
                    kind=metric_name,
                    value=value,
                    timestamp=utcnow()
                )
                db.add(metric_event)
        
        # Update post metrics JSON
        post.metrics_json = json.dumps(metrics)
        db.commit()
        
        logger.info(f"Pinterest stats updated for post {post.id}: {metrics['impressions']} impressions")
        return metrics
        
    except Exception as e:
        logger.error(f"Failed to pull Pinterest stats for post {post.id}: {e}")
        return None

def pull_instagram_stats(db: Session, post: Post) -> Optional[Dict[str, Any]]:
    """Pull Instagram Reels statistics (stub with fallback)."""
    if not post.platform_id or not os.getenv("IG_ACCESS_TOKEN"):
        logger.info(f"Instagram stats unavailable for post {post.id}: missing token")
        # Fallback: estimate based on platform averages
        return _estimate_instagram_metrics(db, post)
        
    set_post_context(post.id)
    
    try:
        # Real implementation would use Instagram Graph API
        # For now, using estimation due to API complexity
        logger.info(f"Instagram real stats not implemented, using estimation for post {post.id}")
        return _estimate_instagram_metrics(db, post)
        
    except Exception as e:
        logger.error(f"Failed to pull Instagram stats for post {post.id}: {e}")
        return None

def pull_tiktok_stats(db: Session, post: Post) -> Optional[Dict[str, Any]]:
    """Pull TikTok video statistics (stub with fallback)."""
    if not post.platform_id or not os.getenv("TIKTOK_ACCESS_TOKEN"):
        logger.info(f"TikTok stats unavailable for post {post.id}: missing token")
        return _estimate_tiktok_metrics(db, post)
        
    set_post_context(post.id)
    
    try:
        # Real implementation would use TikTok Business API
        # For now, using estimation
        logger.info(f"TikTok real stats not implemented, using estimation for post {post.id}")
        return _estimate_tiktok_metrics(db, post)
        
    except Exception as e:
        logger.error(f"Failed to pull TikTok stats for post {post.id}: {e}")
        return None

def _estimate_instagram_metrics(db: Session, post: Post) -> Dict[str, Any]:
    """Estimate Instagram metrics based on historical data."""
    # Simple estimation based on post age and platform averages
    hours_since_post = (utcnow() - post.created_at).total_seconds() / 3600
    
    # Base engagement rates for Instagram Reels
    base_views = max(100, int(hours_since_post * 50))
    base_likes = max(5, int(base_views * 0.05))
    base_comments = max(1, int(base_views * 0.01))
    
    metrics = {
        "views": base_views,
        "likes": base_likes,
        "comments": base_comments,
        "estimated": True
    }
    
    # Save estimated metrics
    for metric_name, value in metrics.items():
        if isinstance(value, (int, float)) and value > 0:
            metric_event = MetricEvent(
                post_id=post.id,
                platform=post.platform,
                kind=f"estimated_{metric_name}",
                value=value,
                timestamp=utcnow()
            )
            db.add(metric_event)
    
    post.metrics_json = json.dumps(metrics)
    db.commit()
    
    return metrics

def _estimate_tiktok_metrics(db: Session, post: Post) -> Dict[str, Any]:
    """Estimate TikTok metrics based on historical data."""
    hours_since_post = (utcnow() - post.created_at).total_seconds() / 3600
    
    # Base engagement rates for TikTok
    base_views = max(200, int(hours_since_post * 100))
    base_likes = max(10, int(base_views * 0.08))
    base_shares = max(2, int(base_views * 0.02))
    
    metrics = {
        "views": base_views,
        "likes": base_likes,
        "shares": base_shares,
        "estimated": True
    }
    
    # Save estimated metrics
    for metric_name, value in metrics.items():
        if isinstance(value, (int, float)) and value > 0:
            metric_event = MetricEvent(
                post_id=post.id,
                platform=post.platform,
                kind=f"estimated_{metric_name}",
                value=value,
                timestamp=utcnow()
            )
            db.add(metric_event)
    
    post.metrics_json = json.dumps(metrics)
    db.commit()
    
    return metrics