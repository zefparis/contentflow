import asyncio
from sqlalchemy.orm import Session
from app.db import SessionLocal
from app.models import Asset, Post
from app.services.assets import transform_asset
from app.services.posts import queue_post_for_publishing
from app.services.compliance import calculate_risk_score
from app.utils.logger import logger


async def autopilot_tick():
    """Execute one autopilot cycle: select assets → plan → transform → queue → publish"""
    db = SessionLocal()
    
    try:
        # 1. Select new assets for processing
        new_assets = db.query(Asset).filter(Asset.status == "new").limit(3).all()
        
        for asset in new_assets:
            logger.info(f"Autopilot processing asset {asset.id}")
            
            # 2. Transform asset
            transform_success = await transform_asset(db, asset)
            
            if transform_success and asset.status == "ready":
                # 3. Get associated draft posts
                draft_posts = db.query(Post).filter(
                    Post.asset_id == asset.id,
                    Post.status == "draft"
                ).all()
                
                for post in draft_posts:
                    # 4. Check compliance risk
                    risk_score = calculate_risk_score(post)
                    
                    if risk_score < 0.2:  # Only proceed with low-risk content
                        logger.info(f"Autopilot queuing post {post.id} (risk: {risk_score:.3f})")
                        
                        # 5. Queue for publishing
                        queue_success = queue_post_for_publishing(db, post)
                        
                        if queue_success:
                            logger.info(f"Autopilot successfully queued post {post.id}")
                        else:
                            logger.warning(f"Autopilot failed to queue post {post.id}")
                    else:
                        logger.warning(f"Autopilot skipping post {post.id} due to high risk: {risk_score:.3f}")
        
        logger.info(f"Autopilot cycle completed, processed {len(new_assets)} assets")
        
    except Exception as e:
        logger.error(f"Autopilot cycle failed: {e}")
    
    finally:
        db.close()


async def start_autopilot():
    """Start the autopilot worker"""
    logger.info("Starting autopilot worker...")
    
    while True:
        try:
            await autopilot_tick()
            await asyncio.sleep(300)  # Run every 5 minutes
        except Exception as e:
            logger.error(f"Autopilot error: {e}")
            await asyncio.sleep(60)  # Wait 1 minute on error


if __name__ == "__main__":
    asyncio.run(start_autopilot())
