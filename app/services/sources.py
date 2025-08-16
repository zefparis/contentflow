import feedparser
import json
import logging
import re
import requests
from io import BytesIO
from PIL import Image
import imagehash
from sqlalchemy.orm import Session
from typing import List, Optional
from app.models import Source, Asset
from app.utils.logger import logger

logger = logging.getLogger(__name__)


def calculate_phash(image_url: str) -> Optional[str]:
    """Calculate perceptual hash of an image from URL."""
    try:
        response = requests.get(image_url, timeout=10, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        response.raise_for_status()
        
        image = Image.open(BytesIO(response.content))
        phash = str(imagehash.phash(image))
        return phash
        
    except Exception as e:
        logger.warning(f"Could not calculate phash for {image_url}: {e}")
        return None


def is_duplicate_phash(phash: str, db: Session, threshold: int = 5) -> bool:
    """Check if an asset with similar phash already exists."""
    if not phash:
        return False
        
    existing_assets = db.query(Asset).filter(Asset.phash.isnot(None)).all()
    
    for asset in existing_assets:
        try:
            existing_phash = imagehash.hex_to_hash(asset.phash)
            new_phash = imagehash.hex_to_hash(phash)
            
            # Calculate Hamming distance
            if abs(existing_phash - new_phash) <= threshold:
                logger.info(f"Duplicate detected: phash {phash} similar to existing {asset.phash}")
                return True
                
        except Exception as e:
            logger.warning(f"Error comparing phashes: {e}")
            continue
            
    return False


def extract_keywords(text: str) -> List[str]:
    """Extract keywords from text using simple regex patterns."""
    if not text:
        return []
        
    # Remove HTML tags and normalize
    text = re.sub(r'<[^>]+>', '', text.lower())
    
    # Extract meaningful words (longer than 3 chars, not common words)
    words = re.findall(r'\b[a-zA-Z]{4,}\b', text)
    
    # Filter out common stop words
    stop_words = {'this', 'that', 'with', 'have', 'will', 'from', 'they', 'been', 
                  'were', 'said', 'each', 'which', 'their', 'time', 'mais', 'pour', 
                  'dans', 'avec', 'être', 'avoir', 'fait', 'tout', 'dire', 'plus'}
    
    keywords = [w for w in words if w not in stop_words]
    
    # Return top 10 most relevant keywords
    return list(set(keywords))[:10]


def matches_filter(title: str, description: str, source: Source) -> bool:
    """Check if content matches source filter criteria."""
    text = f"{title} {description}".lower()
    
    # Check keywords filter
    if source.keywords:
        keywords = [k.strip().lower() for k in source.keywords.split(',')]
        if not any(keyword in text for keyword in keywords):
            return False
    
    # Check categories filter (simple regex matching)
    if source.categories:
        categories = [c.strip().lower() for c in source.categories.split(',')]
        if not any(category in text for category in categories):
            return False
    
    return True


def ingest_rss(source: Source, db: Session) -> int:
    """Ingest RSS feed with advanced filtering and deduplication."""
    try:
        feed = feedparser.parse(source.url)
        count = 0
        
        for entry in feed.entries[:20]:  # Process more entries for filtering
            title = entry.get("title", "")
            description = entry.get("description", "") or entry.get("summary", "")
            
            # Apply keyword/category filters
            if not matches_filter(title, description, source):
                logger.debug(f"Filtered out: {title}")
                continue
            
            # Check if we already have this by link
            existing = db.query(Asset).filter(
                Asset.source_id == source.id,
                Asset.meta_json.contains(f'"link":"{entry.link}"')
            ).first()
            
            if existing:
                continue
            
            # Calculate phash for thumbnail if available
            phash = None
            thumbnail_url = None
            
            # Try to find thumbnail in various RSS fields
            if hasattr(entry, 'media_thumbnail') and entry.media_thumbnail:
                thumbnail_url = entry.media_thumbnail[0]['url']
            elif hasattr(entry, 'enclosures') and entry.enclosures:
                for enclosure in entry.enclosures:
                    if 'image' in enclosure.get('type', ''):
                        thumbnail_url = enclosure.get('href')
                        break
            
            if thumbnail_url:
                phash = calculate_phash(thumbnail_url)
                
                # Check for duplicates using phash
                if phash and is_duplicate_phash(phash, db):
                    logger.info(f"Skipping duplicate content: {title}")
                    continue
            
            # Extract keywords from content
            keywords = extract_keywords(f"{title} {description}")
            
            # Create asset
            meta = {
                "title": title,
                "description": description,
                "link": entry.get("link", ""),
                "published": entry.get("published", ""),
                "summary": entry.get("summary", ""),
                "thumbnail": thumbnail_url
            }
            
            asset = Asset(
                source_id=source.id,
                status="new",
                meta_json=json.dumps(meta),
                lang=source.language or "fr",
                phash=phash,
                keywords=",".join(keywords) if keywords else None
            )
            
            db.add(asset)
            count += 1
            
        db.commit()
        logger.info(f"Ingested {count} new assets from RSS source {source.id}")
        return count
        
    except Exception as e:
        logger.error(f"Error ingesting RSS {source.url}: {e}")
        db.rollback()
        return 0


def ingest_youtube_cc(source: Source, db: Session) -> int:
    """Ingest YouTube closed captions (mock implementation)."""
    try:
        # Mock implementation - create sample assets if no API key
        import os
        if not os.getenv('YOUTUBE_API_KEY'):
            logger.info("Creating mock YouTube assets for demo")
            
            mock_videos = [
                {
                    "title": "Les dernières innovations en IA",
                    "description": "Découvrez les avancées récentes en intelligence artificielle",
                    "video_id": "mock_video_1",
                    "duration": 180
                },
                {
                    "title": "Guide complet du machine learning",
                    "description": "Tutoriel approfondi sur l'apprentissage automatique",
                    "video_id": "mock_video_2", 
                    "duration": 240
                }
            ]
            
            count = 0
            for video in mock_videos:
                # Check if already exists
                existing = db.query(Asset).filter(
                    Asset.source_id == source.id,
                    Asset.meta_json.contains(f'"video_id":"{video["video_id"]}"')
                ).first()
                
                if existing:
                    continue
                
                keywords = extract_keywords(f"{video['title']} {video['description']}")
                
                asset = Asset(
                    source_id=source.id,
                    status="new",
                    meta_json=json.dumps(video),
                    lang=source.language or "fr",
                    duration=video["duration"],
                    keywords=",".join(keywords) if keywords else None
                )
                
                db.add(asset)
                count += 1
            
            db.commit()
            logger.info(f"Created {count} mock YouTube assets")
            return count
        
        # Real YouTube API implementation would go here
        logger.info("YouTube API integration not implemented")
        return 0
        
    except Exception as e:
        logger.error(f"Error ingesting YouTube CC {source.url}: {e}")
        db.rollback()
        return 0


def ingest_stock(source: Source, db: Session) -> int:
    """Ingest from stock content API (stub implementation)."""
    logger.info(f"Stock content ingestion not implemented for {source.url}")
    return 0


def ingest_watch() -> int:
    """Continuous ingestion monitoring - scan all active sources."""
    from app.db import SessionLocal
    
    db = SessionLocal()
    total_ingested = 0
    
    try:
        # Get all enabled sources
        sources = db.query(Source).filter(Source.enabled == True).all()
        
        for source in sources:
            try:
                if source.kind == "rss":
                    count = ingest_rss(source, db)
                elif source.kind == "youtube_cc":
                    count = ingest_youtube_cc(source, db)
                elif source.kind == "stock":
                    count = ingest_stock(source, db)
                elif source.kind.startswith("serp_"):
                    count = ingest_dispatch_serp(db, source)
                else:
                    logger.warning(f"Unknown source kind: {source.kind}")
                    continue
                    
                total_ingested += count
                
            except Exception as e:
                logger.error(f"Error processing source {source.id}: {e}")
                continue
    
    finally:
        db.close()
    
    logger.info(f"Ingestion watch completed: {total_ingested} total assets")
    return total_ingested


# SerpAPI Integration for content discovery and trends monitoring

CC_HINTS = ("Creative Commons", "CC-BY", "CC BY", "CCBY", "creative commons")


def _maybe_cc_badge(item: dict) -> bool:
    """Check if video has Creative Commons indicators."""
    badges = item.get("badges") or []
    text = " ".join(badges) + " " + (item.get("title") or "")
    return any(k.lower() in text.lower() for k in CC_HINTS)


def ingest_serp_youtube(db: Session, src: Source, limit: int = 10) -> int:
    """Ingest YouTube videos via SerpAPI search."""
    try:
        from app.providers import serpapi_provider as serp
        from app.utils.dedupe import phash_from_url
        from app.config import settings
        
        q = (src.url or "").strip()
        if not q:
            return 0
        
        items = serp.youtube_search(q, max_results=limit)
        created = 0
        
        for it in items:
            vid = it.get("video_id") or it.get("id")
            if not vid:
                continue
                
            # Get thumbnail URL
            thumbs = it.get("thumbnails") or []
            thumb_url = None
            if thumbs and isinstance(thumbs[0], dict):
                thumb_url = thumbs[0].get("static") or thumbs[0].get("url")
            else:
                thumb_url = it.get("thumbnail")
            
            # Calculate perceptual hash for deduplication
            p = phash_from_url(thumb_url) if thumb_url else None

            # Check for duplicates using video ID
            video_url = f"https://www.youtube.com/watch?v={vid}"
            exists = db.query(Asset).filter(Asset.meta_json.contains(vid)).first()
            if exists:
                continue

            # Create asset metadata
            meta = {
                "source": "serpapi.youtube",
                "query": q,
                "title": it.get("title"),
                "channel": (it.get("channel", {}) or {}).get("name") or it.get("channel"),
                "video_id": vid,
                "url": video_url,
                "thumbnail": thumb_url,
                "published": it.get("published_date") or it.get("date"),
                "views": it.get("views"),
                "cc_hint": _maybe_cc_badge(it),
                "license": "unknown"
            }
            
            # Create asset
            a = Asset(
                source_id=src.id, 
                status="new", 
                meta_json=json.dumps(meta), 
                s3_key=None, 
                duration=None, 
                lang="fr"
            )
            if p:
                a.phash = p
            
            db.add(a)
            created += 1
        
        db.commit()
        logger.info(f"SerpAPI YouTube ingestion: {created} assets created for query '{q}'")
        return created
        
    except Exception as e:
        logger.error(f"Error in SerpAPI YouTube ingestion: {e}")
        return 0


def ingest_serp_news(db: Session, src: Source, limit: int = 10, spawn_youtube_sources: bool = True, max_spawn: int = 5) -> int:
    """Ingest news via SerpAPI and spawn YouTube search sources."""
    try:
        from app.providers import serpapi_provider as serp
        
        q = (src.url or "").strip()
        if not q:
            return 0
            
        rows = serp.google_news(q, max_results=limit)
        spawned = 0
        
        for r in rows:
            title = r.get("title") or ""
            if not title:
                continue
                
            if spawn_youtube_sources and spawned < max_spawn:
                # Create YouTube search source for this news topic
                exists = db.query(Source).filter_by(kind="serp_youtube", url=title).first()
                if not exists:
                    news_params = json.dumps({
                        "origin": "news", 
                        "news_url": r.get("link"),
                        "news_source": r.get("source")
                    })
                    
                    new_source = Source(
                        kind="serp_youtube", 
                        url=title, 
                        params_json=news_params, 
                        enabled=True,
                        language="fr"
                    )
                    db.add(new_source)
                    spawned += 1
        
        db.commit()
        logger.info(f"SerpAPI News ingestion: spawned {spawned} YouTube sources for query '{q}'")
        return spawned
        
    except Exception as e:
        logger.error(f"Error in SerpAPI News ingestion: {e}")
        return 0


def ingest_serp_trends(db: Session, src: Source, category_id: int = None, max_spawn: int = 5) -> int:
    """Ingest trending topics via SerpAPI and spawn YouTube search sources."""
    try:
        from app.providers import serpapi_provider as serp
        
        stories = serp.trends_trending_now(category_id=category_id)
        spawned = 0
        
        for s in stories:
            # Extract trending topic title
            title = s.get("title")
            if not title and s.get("entity_names"):
                title = ", ".join(s.get("entity_names", []))
            
            if not title:
                continue
                
            # Create YouTube search source for trending topic
            exists = db.query(Source).filter_by(kind="serp_youtube", url=title).first()
            if not exists and spawned < max_spawn:
                trends_params = json.dumps({
                    "origin": "trends",
                    "trend_rank": s.get("rank"),
                    "search_volume": s.get("search_volume")
                })
                
                new_source = Source(
                    kind="serp_youtube", 
                    url=title, 
                    params_json=trends_params, 
                    enabled=True,
                    language="fr"
                )
                db.add(new_source)
                spawned += 1
        
        db.commit()
        logger.info(f"SerpAPI Trends ingestion: spawned {spawned} YouTube sources")
        return spawned
        
    except Exception as e:
        logger.error(f"Error in SerpAPI Trends ingestion: {e}")
        return 0


def ingest_dispatch_serp(db: Session, src: Source) -> int:
    """Dispatch SerpAPI ingestion based on source kind."""
    try:
        from app.config import settings
        
        if src.kind == "serp_youtube":
            return ingest_serp_youtube(db, src, limit=settings.SERPAPI_MAX_RESULTS)
        elif src.kind == "serp_news":
            return ingest_serp_news(db, src)
        elif src.kind == "serp_trends":
            # Extract category from params
            cat = None
            try:
                p = json.loads(src.params_json or "{}")
                cat = p.get("category_id")
            except Exception:
                pass
            return ingest_serp_trends(db, src, category_id=cat)
        
        return 0
        
    except Exception as e:
        logger.error(f"Error in SerpAPI dispatch for source {src.id}: {e}")
        return 0
