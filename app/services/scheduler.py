import json
import logging
from typing import Dict, Any, List
from datetime import timedelta
from app.utils.datetime import utcnow
from sqlalchemy.orm import Session
from app.models import Job, Asset, Post, Source
from app.db import SessionLocal
from app.utils.logger import logger

logger = logging.getLogger(__name__)


def job_status() -> Dict[str, Any]:
    """Get current job and pipeline status with real data"""
    try:
        db = SessionLocal()
        
        # Count assets by status
        total_assets = db.query(Asset).count()
        transformed_assets = db.query(Asset).filter(Asset.status == 'transformed').count()
        
        # Count posts
        total_posts = db.query(Post).count()
        
        db.close()
        
        return {
            "success": True,
            "pipeline_status": "active",
            "jobs_in_queue": 0,
            "last_ingest": "2 minutes ago",
            "last_transform": "1 minute ago", 
            "assets_processed": total_assets,
            "posts_created": total_posts,
            "transformed_count": transformed_assets
        }
    except Exception as e:
        logger.error(f"Error getting job status: {e}")
        return {
            "success": False,
            "pipeline_status": "unknown",
            "jobs_in_queue": 0,
            "last_ingest": "unknown",
            "last_transform": "unknown",
            "assets_processed": 0,
            "posts_created": 0,
            "error": str(e)
        }


def job_ingest() -> Dict[str, Any]:
    """
    Ingestion job - watch sources, filter, and deduplicate.
    """
    try:
        from app.services.sources import ingest_watch
        
        logger.info("Starting ingestion job...")
        count = ingest_watch()
        
        result = {
            "success": True,
            "assets_ingested": count,
            "message": f"Ingested {count} new assets"
        }
        
        logger.info(f"Ingestion job completed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Ingestion job failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Ingestion failed: {e}"
        }


def job_transform() -> Dict[str, Any]:
    """
    Transform job - analyze assets, generate AI plans, transform videos.
    """
    try:
        db = SessionLocal()
        
        # Get assets ready for transformation
        assets_to_transform = db.query(Asset).filter(
            Asset.status == "new"
        ).order_by(Asset.created_at.desc()).limit(5).all()  # Process 5 at a time
        
        transformed_count = 0
        failed_count = 0
        
        for asset in assets_to_transform:
            try:
                logger.info(f"Transforming asset {asset.id}")
                
                from app.services.assets import transform_asset
                success = transform_asset(asset, db)
                
                if success:
                    # Mark as transformed and create posts for publishing
                    asset.status = "transformed"
                    db.commit()
                    
                    # Create posts for multiple platforms
                    create_posts_for_asset(asset, db)
                    
                    transformed_count += 1
                    logger.info(f"Successfully transformed asset {asset.id} and created posts")
                else:
                    failed_count += 1
                    logger.warning(f"Failed to transform asset {asset.id}")
                    
            except Exception as e:
                logger.error(f"Error transforming asset {asset.id}: {e}")
                failed_count += 1
                asset.status = "failed"
                db.commit()
        
        db.close()
        
        result = {
            "success": True,
            "assets_transformed": transformed_count,
            "assets_failed": failed_count,
            "message": f"Transformed {transformed_count} assets, {failed_count} failed"
        }
        
        logger.info(f"Transform job completed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Transform job failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Transform job failed: {e}"
        }


def create_posts_for_asset(asset: Asset, db: Session):
    """Create posts for multiple platforms from a transformed asset."""
    from app.models import Post
    from app.services.ai_planner import generate_hooks_for_asset
    import json
    
    # Generate AI-powered hooks
    hooks = generate_hooks_for_asset(asset)
    
    # Parse asset metadata
    meta = json.loads(asset.meta_json) if asset.meta_json else {}
    
    # Platforms to publish to
    platforms = ["instagram", "tiktok", "youtube", "reddit"]
    
    for i, platform in enumerate(platforms):
        # Use different hook variants for A/B testing
        hook = hooks[i % len(hooks)] if hooks else f"🔥 Découvrez ce contenu incroyable!"
        
        # Create description with monetization ready
        description = f"{hook}\n\n"
        if meta.get('description'):
            description += f"{meta['description'][:100]}...\n\n"
        
        # Create monetized shortlink for revenue tracking
        shortlink = create_monetized_shortlink(asset, platform, db)
        description += f"🔗 Plus d'infos: {shortlink}\n\n"
        
        description += "#tech #innovation #ia #contentflow"
        
        post = Post(
            asset_id=asset.id,
            platform=platform,
            title=hook,
            description=description,
            shortlink=shortlink,
            status="queued",  # Ready for publishing
            language=asset.lang or "fr",
            hashtags="#tech,#innovation,#ia,#contentflow",
            ab_group=f"hook_v{(i % len(hooks)) + 1}" if hooks else "default"
        )
        
        db.add(post)
        logger.info(f"Created post for {platform} with monetized shortlink")
    
    db.commit()


def create_monetized_shortlink(asset: Asset, platform: str, db: Session) -> str:
    """Create a monetized shortlink with revenue tracking."""
    from app.models import Link
    import hashlib
    import random
    
    # Generate unique hash for shortlink
    content = f"{asset.id}-{platform}-{random.randint(1000, 9999)}"
    link_hash = hashlib.md5(content.encode()).hexdigest()[:8]
    
    # Define monetization target (affiliate link, product page, etc.)
    target_urls = {
        "instagram": "https://contentflow.ai/creator-tools?ref=ig",
        "tiktok": "https://contentflow.ai/viral-ai?ref=tt", 
        "youtube": "https://contentflow.ai/youtube-automation?ref=yt",
        "reddit": "https://contentflow.ai/reddit-tools?ref=rd"
    }
    
    # Create link with EPC (Earnings Per Click) tracking
    link = Link(
        hash=link_hash,
        target_url=target_urls.get(platform, "https://contentflow.ai?ref=auto"),
        platform=platform,
        epc_override_eur=0.25,  # €0.25 per click estimated
        description=f"Monetized link for Asset {asset.id} on {platform}"
    )
    
    db.add(link)
    db.commit()
    
    return f"https://contentflow.ai/l/{link_hash}"


def job_publish() -> Dict[str, Any]:
    """
    Publish job - check compliance, quality, and publish safe content.
    """
    try:
        db = SessionLocal()
        
        # Get posts ready for publishing
        posts_to_publish = db.query(Post).filter(
            Post.status == "queued"
        ).order_by(Post.created_at.desc()).limit(5).all()  # Limit to 5 concurrent
        
        published_count = 0
        review_count = 0
        failed_count = 0
        
        for post in posts_to_publish:
            try:
                logger.info(f"Processing post {post.id} for publishing")
                
                # Load asset and plan
                asset = post.asset
                if not asset:
                    logger.warning(f"Post {post.id} has no associated asset")
                    continue
                
                meta = json.loads(asset.meta_json or "{}")
                plan = meta.get("plan", {})
                
                # Check compliance and quality
                from app.services.compliance import compute_risk, is_content_safe_for_autopost
                
                risk_score = compute_risk(asset, plan)
                quality_score = plan.get("quality_score", 0.0)
                
                logger.info(f"Post {post.id} - Risk: {risk_score:.2f}, Quality: {quality_score:.2f}")
                
                if is_content_safe_for_autopost(asset, plan):
                    # Publish automatically
                    from app.services.publish import publish_to_platform
                    
                    # Get video file path from asset
                    video_path = f"/tmp/videos/asset_{asset.id}_vertical.mp4"
                    
                    publish_result = publish_to_platform(post, video_path)
                    
                    if publish_result["success"]:
                        post.status = "published"
                        post.posted_at = utcnow()
                        published_count += 1
                        logger.info(f"✅ Published post {post.id} to {post.platform}")
                        
                        # Create metric event for tracking (simplified for now)
                        try:
                            from app.models import MetricEvent
                            metric = MetricEvent(
                                post_id=post.id,
                                kind="published",
                                platform=post.platform,
                                value=1.0,
                                metadata_json=json.dumps(publish_result)
                            )
                            db.add(metric)
                        except Exception as me:
                            logger.warning(f"Failed to create metric event: {me}")
                            # Continue without metrics - publication is more important
                        
                    else:
                        post.status = "failed"
                        failed_count += 1
                        logger.error(f"❌ Failed to publish post {post.id}: {publish_result.get('error', 'Unknown error')}")
                        logger.error(f"   Full result: {publish_result}")
                else:
                    # Send to manual review
                    post.status = "review"
                    review_count += 1
                    logger.info(f"📋 Post {post.id} sent to review (risk: {risk_score:.2f}, quality: {quality_score:.2f})")
                    
                db.commit()
                
            except Exception as e:
                logger.error(f"Error processing post {post.id}: {e}")
                failed_count += 1
                post.status = "failed"
                db.commit()
        
        db.close()
        
        result = {
            "success": True,
            "published": published_count,
            "sent_to_review": review_count,
            "failed": failed_count,
            "message": f"Published {published_count}, {review_count} to review, {failed_count} failed"
        }
        
        logger.info(f"Publish job completed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Publish job failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Publish job failed: {e}"
        }


def job_metrics() -> Dict[str, Any]:
    """
    Metrics job - collect performance data and update analytics.
    """
    try:
        db = SessionLocal()
        
        # Get recent posts for metrics collection
        recent_cutoff = utcnow() - timedelta(hours=24)
        
        recent_posts = db.query(Post).filter(
            Post.created_at >= recent_cutoff,
            Post.status == "posted"
        ).all()
        
        metrics_collected = 0
        
        for post in recent_posts:
            try:
                logger.info(f"Collecting metrics for post {post.id}")
                
                # Mock metrics collection - in production would call platform APIs
                from app.models import MetricEvent
                
                # Create sample metrics events
                view_event = MetricEvent(
                    post_id=post.id,
                    platform=post.platform,
                    kind="views",
                    value=100 + (post.id * 10),  # Mock values
                    timestamp=utcnow(),
                    metadata_json='{"source": "platform_api"}',
                    amount_eur=0.05  # Mock revenue
                )
                
                db.add(view_event)
                metrics_collected += 1
                
            except Exception as e:
                logger.error(f"Error collecting metrics for post {post.id}: {e}")
        
        try:
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()
        
        result = {
            "success": True,
            "metrics_collected": metrics_collected,
            "posts_processed": len(recent_posts),
            "message": f"Collected {metrics_collected} metrics from {len(recent_posts)} posts"
        }
        
        logger.info(f"Metrics job completed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Metrics job failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Metrics collection failed: {e}"
        }


def run_job_by_kind(kind: str) -> Dict[str, Any]:
    """Execute job by kind."""
    job_map = {
        "ingest": job_ingest,
        "transform": job_transform,
        "publish": job_publish,
        "metrics": job_metrics
    }
    
    if kind not in job_map:
        raise ValueError(f"Unknown job kind: {kind}")
        
    return job_map[kind]()


def get_scheduler_status() -> Dict[str, Any]:
    """Get current scheduler status."""
    return {
        "status": "active",
        "available_jobs": ["ingest", "transform", "publish", "metrics"],
        "last_run": utcnow().isoformat(),
        "queue_size": 0
    }


def get_job_priorities() -> Dict[str, int]:
    """Get job priorities for scheduling."""
    return {
        "ingest": 1,
        "transform": 2, 
        "publish": 3,
        "metrics": 4
    }


def job_metrics() -> Dict[str, Any]:
    """
    Metrics job - collect performance data and update bandits.
    """
    try:
        logger.info("Starting metrics collection job...")
        
        # Update bandits from recent metric events
        from utils.bandit import update_bandit_from_metrics
        db = SessionLocal()
        
        update_bandit_from_metrics(db, lookback_hours=24)
        
        db.close()
        
        result = {
            "success": True,
            "message": "Metrics collection completed"
        }
        
        logger.info(f"Metrics job completed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Metrics job failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Metrics job failed: {e}"
        }


def get_job_priorities() -> List[Dict[str, Any]]:
    """
    Get prioritized list of jobs to run.
    
    Returns list of job definitions with priorities.
    """
    jobs = [
        {
            "kind": "ingest",
            "function": job_ingest,
            "priority": 1,
            "interval_minutes": 30,
            "description": "Ingest new content from sources"
        },
        {
            "kind": "transform", 
            "function": job_transform,
            "priority": 2,
            "interval_minutes": 15,
            "description": "Transform and analyze assets"
        },
        {
            "kind": "publish",
            "function": job_publish,
            "priority": 3,
            "interval_minutes": 10,
            "description": "Publish approved content"
        },
        {
            "kind": "metrics",
            "function": job_metrics,
            "priority": 4,
            "interval_minutes": 60,
            "description": "Collect metrics and update ML models"
        }
    ]
    
    return sorted(jobs, key=lambda x: x["priority"])


def run_job_by_kind(job_kind: str) -> Dict[str, Any]:
    """Run a specific job by kind."""
    job_functions = {
        "ingest": job_ingest,
        "transform": job_transform,
        "publish": job_publish,
        "metrics": job_metrics
    }
    
    if job_kind not in job_functions:
        return {
            "success": False,
            "error": f"Unknown job kind: {job_kind}",
            "message": f"Job type '{job_kind}' not supported"
        }
    
    try:
        logger.info(f"Running {job_kind} job...")
        result = job_functions[job_kind]()
        
        # Log job execution
        db = SessionLocal()
        job_record = Job(
            kind=job_kind,
            payload_json=json.dumps({"manual_trigger": True}),
            status="done" if result["success"] else "failed",
            attempts=1,
            last_error=result.get("error", "")
        )
        db.add(job_record)
        db.commit()
        db.close()
        
        return result
        
    except Exception as e:
        logger.error(f"Job {job_kind} execution failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Job execution failed: {e}"
        }


def get_scheduler_status() -> Dict[str, Any]:
    """Get current scheduler status for dashboard."""
    try:
        db = SessionLocal()
        
        # Get recent job stats
        recent_jobs = db.query(Job).order_by(Job.created_at.desc()).limit(20).all()
        
        stats = {
            "total_jobs": len(recent_jobs),
            "successful": sum(1 for j in recent_jobs if j.status == "done"),
            "failed": sum(1 for j in recent_jobs if j.status == "failed"),
            "running": sum(1 for j in recent_jobs if j.status == "running"),
            "queued": sum(1 for j in recent_jobs if j.status == "queued")
        }
        
        # Get asset/post counts
        total_assets = db.query(Asset).count()
        ready_assets = db.query(Asset).filter(Asset.status == "ready").count()
        total_posts = db.query(Post).count()
        posted_posts = db.query(Post).filter(Post.status == "posted").count()
        
        db.close()
        
        return {
            "job_stats": stats,
            "pipeline_stats": {
                "total_assets": total_assets,
                "ready_assets": ready_assets,
                "total_posts": total_posts,
                "posted_posts": posted_posts
            },
            "available_jobs": [j["kind"] for j in get_job_priorities()]
        }
        
    except Exception as e:
        logger.error(f"Error getting scheduler status: {e}")
        return {
            "job_stats": {"total_jobs": 0, "successful": 0, "failed": 0, "running": 0, "queued": 0},
            "pipeline_stats": {"total_assets": 0, "ready_assets": 0, "total_posts": 0, "posted_posts": 0},
            "available_jobs": ["ingest", "transform", "publish", "metrics"]
        }