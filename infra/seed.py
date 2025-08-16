import asyncio
from sqlalchemy.orm import Session
from app.db import SessionLocal, engine, Base
from app.models import Source, Link
from app.utils.logger import logger


def create_seed_data():
    """Create initial seed data for ContentFlow"""
    
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        # Check if seed data already exists
        existing_sources = db.query(Source).count()
        if existing_sources > 0:
            logger.info("Seed data already exists, skipping...")
            return
        
        # Create sample sources
        sources = [
            Source(
                kind="rss",
                url="https://feeds.feedburner.com/TechCrunch",
                enabled=True
            ),
            Source(
                kind="rss", 
                url="https://www.theverge.com/rss/index.xml",
                enabled=True
            ),
            Source(
                kind="youtube_cc",
                url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                enabled=True
            ),
            Source(
                kind="stock",
                url="https://example.com/stock-content-api",
                enabled=True
            )
        ]
        
        for source in sources:
            db.add(source)
        
        # Create affiliate links
        links = [
            Link(
                affiliate_url="https://example.com/affiliate",
                utm="utm_source={platform}&utm_medium=social&utm_campaign=contentflow",
                platform_hint="instagram"
            ),
            Link(
                affiliate_url="https://example.com/affiliate-tiktok",
                utm="utm_source={platform}&utm_medium=video&utm_campaign=contentflow",
                platform_hint="tiktok"
            ),
            Link(
                affiliate_url="https://example.com/affiliate-youtube",
                utm="utm_source={platform}&utm_medium=video&utm_campaign=contentflow",
                platform_hint="youtube"
            )
        ]
        
        for link in links:
            db.add(link)
        
        db.commit()
        
        logger.info("Successfully created seed data:")
        logger.info(f"- {len(sources)} content sources")
        logger.info(f"- {len(links)} affiliate links")
        
    except Exception as e:
        logger.error(f"Error creating seed data: {e}")
        db.rollback()
        raise
    
    finally:
        db.close()


if __name__ == "__main__":
    logger.info("Starting ContentFlow seed process...")
    create_seed_data()
    logger.info("Seed process completed!")
