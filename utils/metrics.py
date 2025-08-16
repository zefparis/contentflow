"""Enhanced metrics and revenue tracking with EPC support."""

import os
import csv
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.models import MetricEvent, Link, Post
from app.utils.logger import logger

def epc_for_link(link: Link) -> float:
    """Calculate EPC (Earnings Per Click) for a link."""
    if link.epc_override_eur is not None:
        return link.epc_override_eur
    
    # Use default EPC from environment
    return float(os.getenv("DEFAULT_EPC_EUR", "0.20"))

def compute_daily_revenue(db: Session, target_date: datetime = None) -> Dict[str, float]:
    """Compute daily revenue from metric events and EPC estimates."""
    if target_date is None:
        target_date = datetime.utcnow().date()
    
    start_time = datetime.combine(target_date, datetime.min.time())
    end_time = start_time + timedelta(days=1)
    
    # Get revenue from direct amounts (affiliate conversions)
    direct_revenue = db.execute(text("""
        SELECT platform, COALESCE(SUM(amount_eur), 0) as revenue
        FROM metric_events 
        WHERE timestamp >= :start_time 
        AND timestamp < :end_time 
        AND amount_eur > 0
        GROUP BY platform
    """), {"start_time": start_time, "end_time": end_time}).fetchall()
    
    # Get revenue from EPC estimates (clicks without conversion data)
    estimated_revenue = db.execute(text("""
        SELECT me.platform, COUNT(*) as clicks, AVG(COALESCE(l.epc_override_eur, :default_epc)) as avg_epc
        FROM metric_events me
        LEFT JOIN links l ON me.metadata->>'link_id' = CAST(l.id AS TEXT)
        WHERE me.timestamp >= :start_time 
        AND me.timestamp < :end_time 
        AND me.kind = 'click'
        AND (me.amount_eur = 0 OR me.amount_eur IS NULL)
        GROUP BY me.platform
    """), {
        "start_time": start_time, 
        "end_time": end_time,
        "default_epc": float(os.getenv("DEFAULT_EPC_EUR", "0.20"))
    }).fetchall()
    
    # Combine revenues
    platform_revenue = {}
    
    # Add direct revenue
    for row in direct_revenue:
        platform_revenue[row.platform] = float(row.revenue)
    
    # Add estimated revenue
    for row in estimated_revenue:
        estimated = float(row.clicks) * float(row.avg_epc)
        platform_revenue[row.platform] = platform_revenue.get(row.platform, 0) + estimated
    
    # Calculate total
    total_revenue = sum(platform_revenue.values())
    platform_revenue["total"] = total_revenue
    
    logger.info(f"Daily revenue for {target_date}: €{total_revenue:.2f}")
    return platform_revenue

def export_revenue_csv(db: Session, days: int = 30) -> str:
    """Export revenue data to CSV file."""
    start_date = datetime.utcnow().date() - timedelta(days=days)
    
    # Generate daily revenue data
    revenue_data = []
    current_date = start_date
    
    while current_date <= datetime.utcnow().date():
        daily_revenue = compute_daily_revenue(db, current_date)
        
        row = {
            "date": current_date.isoformat(),
            "total_revenue_eur": daily_revenue.get("total", 0),
            "youtube_revenue_eur": daily_revenue.get("youtube", 0),
            "reddit_revenue_eur": daily_revenue.get("reddit", 0),
            "pinterest_revenue_eur": daily_revenue.get("pinterest", 0),
            "instagram_revenue_eur": daily_revenue.get("instagram", 0),
            "tiktok_revenue_eur": daily_revenue.get("tiktok", 0),
        }
        revenue_data.append(row)
        current_date += timedelta(days=1)
    
    # Write to CSV
    filename = f"revenue_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
    filepath = f"/tmp/{filename}"
    
    with open(filepath, 'w', newline='') as csvfile:
        fieldnames = ["date", "total_revenue_eur", "youtube_revenue_eur", 
                     "reddit_revenue_eur", "pinterest_revenue_eur", 
                     "instagram_revenue_eur", "tiktok_revenue_eur"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for row in revenue_data:
            writer.writerow(row)
    
    logger.info(f"Revenue data exported to {filepath}")
    return filepath

def get_platform_performance(db: Session, days: int = 7) -> Dict[str, dict]:
    """Get performance metrics by platform."""
    start_time = datetime.utcnow() - timedelta(days=days)
    
    # Get aggregated metrics by platform
    results = db.execute(text("""
        SELECT 
            platform,
            SUM(CASE WHEN kind = 'click' THEN value ELSE 0 END) as total_clicks,
            SUM(CASE WHEN kind = 'view' THEN value ELSE 0 END) as total_views,
            SUM(CASE WHEN kind = 'like' THEN value ELSE 0 END) as total_likes,
            SUM(amount_eur) as total_revenue,
            COUNT(DISTINCT post_id) as active_posts
        FROM metric_events
        WHERE timestamp >= :start_time
        GROUP BY platform
    """), {"start_time": start_time}).fetchall()
    
    platform_stats = {}
    for row in results:
        ctr = (row.total_clicks / row.total_views * 100) if row.total_views > 0 else 0
        epc = (row.total_revenue / row.total_clicks) if row.total_clicks > 0 else 0
        
        platform_stats[row.platform] = {
            "clicks": int(row.total_clicks),
            "views": int(row.total_views),
            "likes": int(row.total_likes),
            "revenue_eur": float(row.total_revenue),
            "active_posts": int(row.active_posts),
            "ctr_percent": round(ctr, 2),
            "epc_eur": round(epc, 3)
        }
    
    return platform_stats

def get_top_performing_posts(db: Session, days: int = 7, limit: int = 10) -> List[dict]:
    """Get top performing posts by revenue."""
    start_time = datetime.utcnow() - timedelta(days=days)
    
    results = db.execute(text("""
        SELECT 
            p.id,
            p.title,
            p.platform,
            p.created_at,
            SUM(CASE WHEN me.kind = 'click' THEN me.value ELSE 0 END) as clicks,
            SUM(me.amount_eur) as revenue,
            COUNT(DISTINCT me.session_id) as unique_sessions
        FROM posts p
        LEFT JOIN metric_events me ON p.id = me.post_id
        WHERE me.timestamp >= :start_time OR me.timestamp IS NULL
        GROUP BY p.id, p.title, p.platform, p.created_at
        ORDER BY revenue DESC, clicks DESC
        LIMIT :limit
    """), {"start_time": start_time, "limit": limit}).fetchall()
    
    top_posts = []
    for row in results:
        post_data = {
            "id": row.id,
            "title": row.title[:100] + "..." if len(row.title) > 100 else row.title,
            "platform": row.platform,
            "created_at": row.created_at.isoformat(),
            "clicks": int(row.clicks),
            "revenue_eur": float(row.revenue),
            "unique_sessions": int(row.unique_sessions)
        }
        top_posts.append(post_data)
    
    return top_posts

def track_link_click(db: Session, link_id: int, session_id: str, platform: str, 
                    post_id: Optional[int] = None, user_agent: str = "", 
                    referer: str = "", ip: str = ""):
    """Track a link click with full context."""
    link = db.query(Link).filter(Link.id == link_id).first()
    if not link:
        logger.warning(f"Link {link_id} not found for click tracking")
        return
    
    # Calculate revenue
    revenue = epc_for_link(link)
    
    # Create metric event
    metric_event = MetricEvent(
        post_id=post_id,
        platform=platform,
        kind="click",
        value=1,
        session_id=session_id,
        amount_eur=revenue,
        timestamp=datetime.utcnow(),
        metadata={
            "link_id": link_id,
            "user_agent": user_agent,
            "referer": referer,
            "ip": ip
        }
    )
    
    db.add(metric_event)
    db.commit()
    
    logger.info(f"Link click tracked: link={link_id}, revenue=€{revenue:.3f}, session={session_id}")
    return metric_event